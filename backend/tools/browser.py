from langchain_community.tools import BaseTool
from typing import Optional, Type, List
from pydantic import BaseModel, Field
from playwright.sync_api import sync_playwright
from langchain_core.callbacks import CallbackManagerForToolRun
import time
import os
import threading
import queue
import json

class ThreadedBrowserManager:
    _instance = None
    
    def __init__(self):
        self.cmd_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ThreadedBrowserManager()
        return cls._instance

    def _worker_loop(self):
        p = None
        browser = None
        context = None
        page = None

        def ensure_browser():
            nonlocal p, browser, context, page
            if page is not None:
                try:
                    if not page.is_closed():
                        return None
                except Exception:
                    pass
            try:
                if p is None:
                    p = sync_playwright().start()
                if browser is None:
                    browser = p.chromium.launch(headless=False)
                if context is None:
                    context = browser.new_context(
                        viewport={"width": 1280, "height": 720},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    )
                page = context.new_page()
                return None
            except Exception as e:
                return f"Error: 浏览器启动失败: {e}"

        while True:
            cmd, args, kwargs = self.cmd_queue.get()
            if cmd == "stop":
                try:
                    if browser is not None:
                        browser.close()
                except Exception:
                    pass
                try:
                    if p is not None:
                        p.stop()
                except Exception:
                    pass
                self.result_queue.put("stopped")
                break

            init_err = ensure_browser()
            if init_err:
                self.result_queue.put(init_err)
                continue
                    
            try:
                res = ""
                if cmd == "goto":
                    url = args[0]
                    try:
                        page.goto(url, timeout=60000)
                        page.wait_for_load_state("domcontentloaded", timeout=60000)
                        res = f"Opened {url}. Page title: {page.title()}"
                    except Exception as e:
                        res = f"Opened {url}, but wait timed out or failed: {e}"
                
                elif cmd == "click":
                    selector = args[0]
                    try:
                        page.wait_for_selector(selector, state="visible", timeout=10000)
                        page.click(selector)
                        res = f"Clicked element: {selector}"
                    except Exception as e:
                        res = f"Error clicking {selector}: {e}"

                elif cmd == "click_text":
                    text = args[0]
                    try:
                        locator = page.get_by_text(text, exact=False).first
                        locator.wait_for(state="visible", timeout=15000)
                        locator.click()
                        res = f"Clicked text: {text}"
                    except Exception as e:
                        res = f"Error clicking text '{text}': {e}"

                elif cmd == "click_role":
                    role, name = args
                    try:
                        locator = page.get_by_role(role, name=name).first
                        locator.wait_for(state="visible", timeout=15000)
                        locator.click()
                        res = f"Clicked role={role} name={name}"
                    except Exception as e:
                        res = f"Error clicking role={role} name={name}: {e}"

                elif cmd == "smart_click":
                    desc = args[0]
                    try:
                        clicked = False
                        # Try multiple strategies
                        strategies = [
                            lambda: page.get_by_role("button", name=desc).first,
                            lambda: page.get_by_role("link", name=desc).first,
                            lambda: page.get_by_text(desc, exact=True).first, # Try exact match first
                            lambda: page.get_by_text(desc, exact=False).first,
                            lambda: page.get_by_label(desc).first,
                            lambda: page.get_by_title(desc).first,
                            lambda: page.locator(f"button:has-text('{desc}')").first,
                            lambda: page.locator(f"a:has-text('{desc}')").first,
                            # Common patterns for buttons
                            lambda: page.locator(f"[aria-label*='{desc}']").first,
                            lambda: page.locator(f"[title*='{desc}']").first
                        ]
                        
                        for strategy in strategies:
                            try:
                                loc = strategy()
                                if loc.is_visible(timeout=500): # Short timeout for check
                                    loc.click()
                                    self.result_queue.put(f"Clicked element matching '{desc}'")
                                    clicked = True
                                    break
                            except:
                                continue
                        
                        if not clicked:
                            # Fallback: try to find any visible element containing the text
                            # This is a bit risky but useful for "smart" behavior
                            try:
                                loc = page.locator(f"text={desc}").first
                                if loc.is_visible(timeout=1000):
                                    loc.click()
                                    self.result_queue.put(f"Clicked text '{desc}' (fallback)")
                                    clicked = True
                            except: pass

                        if not clicked:
                            res = f"Could not find clickable element matching '{desc}'. I tried roles, text, labels, and titles."
                        else:
                            continue # Result already put
                    except Exception as e:
                        res = f"Error in smart click for '{desc}': {e}"

                elif cmd == "type":
                    selector, text = args
                    try:
                        page.wait_for_selector(selector, state="visible", timeout=10000)
                        page.fill(selector, text)
                        res = f"Typed '{text}' into {selector}"
                    except Exception as e:
                        res = f"Error typing into {selector}: {e}"

                elif cmd == "smart_type":
                    desc, text = args
                    try:
                        typed = False
                        strategies = [
                            lambda: page.get_by_placeholder(desc).first,
                            lambda: page.get_by_label(desc).first,
                            lambda: page.get_by_role("textbox", name=desc).first,
                            lambda: page.get_by_role("searchbox", name=desc).first,
                            # Generic selectors for common inputs
                            lambda: page.locator(f"input[name*='{desc}']").first,
                            lambda: page.locator(f"input[id*='{desc}']").first,
                            lambda: page.locator(f"input[placeholder*='{desc}']").first,
                            lambda: page.locator(f"textarea[name*='{desc}']").first,
                            lambda: page.locator(f"textarea[placeholder*='{desc}']").first,
                            # Fallback for search
                            lambda: page.locator("input[type='search']").first if "search" in desc.lower() or "搜索" in desc else None,
                            lambda: page.locator("input[type='text']").first # Last resort: first text input? Maybe too aggressive.
                        ]

                        for strategy in strategies:
                            try:
                                loc = strategy()
                                if loc and loc.is_visible(timeout=500):
                                    loc.fill(text)
                                    # Trigger events that might be needed
                                    loc.dispatch_event("input")
                                    loc.dispatch_event("change")
                                    self.result_queue.put(f"Typed '{text}' into field matching '{desc}'")
                                    typed = True
                                    break
                            except:
                                continue
                        
                        if not typed:
                             # Special case: if desc is "search" or "搜索", try to find ANY search input
                            if "search" in desc.lower() or "搜索" in desc:
                                try:
                                    loc = page.locator("input[type='search'], input[name='q'], input[name='wd'], input[name='query']").first
                                    if loc.is_visible(timeout=1000):
                                        loc.fill(text)
                                        self.result_queue.put(f"Typed '{text}' into detected search box")
                                        typed = True
                                except: pass

                        if not typed:
                            res = f"Could not find input field matching '{desc}'"
                        else:
                            continue
                    except Exception as e:
                        res = f"Error in smart type for '{desc}': {e}"
                
                elif cmd == "press_key":
                    key = args[0]
                    try:
                        page.keyboard.press(key)
                        res = f"Pressed key: {key}"
                    except Exception as e:
                        res = f"Error pressing key {key}: {e}"

                elif cmd == "scroll":
                    direction = args[0]
                    try:
                        if direction == "down":
                            page.evaluate("window.scrollBy(0, 500)")
                        elif direction == "up":
                            page.evaluate("window.scrollBy(0, -500)")
                        elif direction == "bottom":
                            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        elif direction == "top":
                            page.evaluate("window.scrollTo(0, 0)")
                        res = f"Scrolled {direction}"
                    except Exception as e:
                        res = f"Error scrolling: {e}"

                elif cmd == "screenshot":
                    filename = args[0]
                    try:
                        download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
                        os.makedirs(download_dir, exist_ok=True)
                        path = os.path.join(download_dir, filename)
                        page.screenshot(path=path)
                        res = f"Screenshot saved to {path}"
                    except Exception as e:
                        res = f"Error taking screenshot: {e}"

                elif cmd == "page_info":
                    try:
                        res = json.dumps({"url": page.url, "title": page.title()}, ensure_ascii=False)
                    except Exception as e:
                        res = f"Error getting page info: {e}"

                elif cmd == "a11y_snapshot":
                    try:
                        snap = page.accessibility.snapshot()
                        res = json.dumps(snap, ensure_ascii=False)
                        if len(res) > 15000:
                            res = res[:15000]
                    except Exception as e:
                        res = f"Error getting accessibility snapshot: {e}"

                else:
                    res = "Unknown command"

                self.result_queue.put(res)
                    
            except Exception as e:
                self.result_queue.put(f"Error executing command {cmd}: {e}")

    def execute(self, cmd, *args, **kwargs):
        if not self.worker_thread.is_alive():
            # Restart if died
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            # Give it a sec to init
            time.sleep(2)
            
        self.cmd_queue.put((cmd, args, kwargs))
        # Add a timeout to get() to prevent infinite hang if worker dies
        try:
            return self.result_queue.get(timeout=180)
        except queue.Empty:
            return "Error: 浏览器操作超时（可能页面加载太慢或浏览器未启动）。"

def get_browser_manager() -> ThreadedBrowserManager:
    return ThreadedBrowserManager.get_instance()

# --- Tools ---

class BrowserOpenInput(BaseModel):
    url: str = Field(description="The URL to open")

class BrowserOpenTool(BaseTool):
    name: str = "browser_open"
    description: str = "Opens a URL in a visible browser window. Use this to start browsing or navigate to a new page."
    args_schema: Type[BaseModel] = BrowserOpenInput

    def _run(self, url: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return get_browser_manager().execute("goto", url)

class BrowserClickInput(BaseModel):
    selector: str = Field(description="The CSS selector of the element to click (e.g. '#submit-button', '.video-title')")

class BrowserClickTool(BaseTool):
    name: str = "browser_click"
    description: str = "Clicks an element on the current page using a CSS selector."
    args_schema: Type[BaseModel] = BrowserClickInput

    def _run(self, selector: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return get_browser_manager().execute("click", selector)

class BrowserClickTextInput(BaseModel):
    text: str = Field(description="Text to find on the page and click (partial match)")

class BrowserClickTextTool(BaseTool):
    name: str = "browser_click_text"
    description: str = "Finds a visible element by text (partial match) and clicks it. Useful when you don't know CSS selectors."
    args_schema: Type[BaseModel] = BrowserClickTextInput

    def _run(self, text: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return get_browser_manager().execute("click_text", text)

class BrowserClickRoleInput(BaseModel):
    role: str = Field(description="ARIA role, e.g. 'button', 'link'")
    name: str = Field(description="Accessible name of the element")

class BrowserClickRoleTool(BaseTool):
    name: str = "browser_click_role"
    description: str = "Clicks an element by ARIA role and accessible name. Useful for buttons like '点赞'."
    args_schema: Type[BaseModel] = BrowserClickRoleInput

    def _run(self, role: str, name: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return get_browser_manager().execute("click_role", role, name)

class BrowserSmartClickInput(BaseModel):
    description: str = Field(description="Description of the element to click (e.g. 'search', 'like', 'submit')")

class BrowserSmartClickTool(BaseTool):
    name: str = "browser_smart_click"
    description: str = "Intelligently finds and clicks an element based on a description. Tries role, text, label, and title."
    args_schema: Type[BaseModel] = BrowserSmartClickInput

    def _run(self, description: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return get_browser_manager().execute("smart_click", description)

class BrowserTypeInput(BaseModel):
    selector: str = Field(description="The CSS selector of the input field")
    text: str = Field(description="The text to type")

class BrowserTypeTool(BaseTool):
    name: str = "browser_type"
    description: str = "Types text into an input field using a CSS selector."
    args_schema: Type[BaseModel] = BrowserTypeInput

    def _run(self, selector: str, text: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return get_browser_manager().execute("type", selector, text)

class BrowserSmartTypeInput(BaseModel):
    description: str = Field(description="Description of the input field (e.g. 'search', 'username', 'comment')")
    text: str = Field(description="The text to type")

class BrowserSmartTypeTool(BaseTool):
    name: str = "browser_smart_type"
    description: str = "Intelligently finds an input field based on description and types text. Tries placeholder, label, and role."
    args_schema: Type[BaseModel] = BrowserSmartTypeInput

    def _run(self, description: str, text: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return get_browser_manager().execute("smart_type", description, text)

class BrowserPressKeyInput(BaseModel):
    key: str = Field(description="Key to press (e.g. 'Enter', 'Escape', 'Tab')")

class BrowserPressKeyTool(BaseTool):
    name: str = "browser_press_key"
    description: str = "Presses a keyboard key. Useful for submitting forms (Enter) or closing modals (Escape)."
    args_schema: Type[BaseModel] = BrowserPressKeyInput

    def _run(self, key: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return get_browser_manager().execute("press_key", key)

class BrowserScrollInput(BaseModel):
    direction: str = Field(description="Direction to scroll: 'down', 'up', 'bottom', 'top'")

class BrowserScrollTool(BaseTool):
    name: str = "browser_scroll"
    description: str = "Scrolls the current page."
    args_schema: Type[BaseModel] = BrowserScrollInput

    def _run(self, direction: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return get_browser_manager().execute("scroll", direction)

class BrowserScreenshotInput(BaseModel):
    filename: str = Field(description="Filename for the screenshot (e.g. 'page.png')")

class BrowserScreenshotTool(BaseTool):
    name: str = "browser_screenshot"
    description: str = "Takes a screenshot of the current page and saves it to Downloads."
    args_schema: Type[BaseModel] = BrowserScreenshotInput

    def _run(self, filename: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return get_browser_manager().execute("screenshot", filename)

class BrowserPageInfoInput(BaseModel):
    pass

class BrowserPageInfoTool(BaseTool):
    name: str = "browser_page_info"
    description: str = "Returns current page URL and title as JSON."
    args_schema: Type[BaseModel] = BrowserPageInfoInput

    def _run(self, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return get_browser_manager().execute("page_info")

class BrowserA11ySnapshotInput(BaseModel):
    pass

class BrowserA11ySnapshotTool(BaseTool):
    name: str = "browser_a11y_snapshot"
    description: str = "Returns a JSON accessibility snapshot of the current page (may be truncated)."
    args_schema: Type[BaseModel] = BrowserA11ySnapshotInput

    def _run(self, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return get_browser_manager().execute("a11y_snapshot")

def get_browser_tools() -> List[BaseTool]:
    return [
        BrowserOpenTool(),
        BrowserClickTool(),
        BrowserClickTextTool(),
        BrowserClickRoleTool(),
        BrowserSmartClickTool(),
        BrowserTypeTool(),
        BrowserSmartTypeTool(),
        BrowserPressKeyTool(),
        BrowserScrollTool(),
        BrowserScreenshotTool(),
        BrowserPageInfoTool(),
        BrowserA11ySnapshotTool()
    ]
