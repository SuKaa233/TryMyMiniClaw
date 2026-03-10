from langchain_community.tools import BaseTool
from typing import Optional, Type, List
from pydantic import BaseModel, Field
from playwright.sync_api import sync_playwright
from langchain_core.callbacks import CallbackManagerForToolRun
import json

class GetBilibiliRankingInput(BaseModel):
    category: str = Field(description="The category of ranking to fetch (default: 'all'). Options: all, origin, bangumi, cinema, rookie", default="all")

class GetBilibiliRankingTool(BaseTool):
    name: str = "get_bilibili_ranking"
    description: str = "Fetches the current top 10 popular videos from Bilibili using a real browser to bypass anti-scraping."
    args_schema: Type[BaseModel] = GetBilibiliRankingInput

    def _run(self, category: str = "all", run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        url_map = {
            "all": "https://www.bilibili.com/v/popular/rank/all/",
            "origin": "https://www.bilibili.com/v/popular/rank/origin",
            "bangumi": "https://www.bilibili.com/v/popular/rank/bangumi",
            "cinema": "https://www.bilibili.com/v/popular/rank/cinema",
            "rookie": "https://www.bilibili.com/v/popular/rank/rookie"
        }
        
        url = url_map.get(category, url_map["all"])
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080}
                )
                page = context.new_page()
                
                # print(f"Navigating to {url}...")
                page.goto(url, timeout=60000)
                
                try:
                    page.wait_for_selector(".rank-list", timeout=15000)
                except:
                    return f"Error: Timeout waiting for rank list at {url}"

                # Extract items
                # We use evaluate to run JS in the browser context for better performance and stability
                results = page.evaluate("""
                    () => {
                        const items = document.querySelectorAll('.rank-item');
                        const data = [];
                        for (let i = 0; i < Math.min(items.length, 10); i++) {
                            const item = items[i];
                            const titleEl = item.querySelector('.title');
                            const viewEl = item.querySelector('.detail-state .data-box'); // View count usually first
                            const authorEl = item.querySelector('.up-name');
                            const linkEl = item.querySelector('a.title');
                            
                            data.push({
                                rank: i + 1,
                                title: titleEl ? titleEl.innerText.trim() : 'Unknown',
                                author: authorEl ? authorEl.innerText.trim() : 'Unknown',
                                view_count: viewEl ? viewEl.innerText.trim() : '0',
                                link: linkEl ? linkEl.href : ''
                            });
                        }
                        return data;
                    }
                """)
                
                browser.close()
                return json.dumps(results, ensure_ascii=False, indent=2)
                
        except Exception as e:
            return f"Error fetching Bilibili ranking: {str(e)}"

def get_bilibili_tools() -> List[BaseTool]:
    return [GetBilibiliRankingTool()]
