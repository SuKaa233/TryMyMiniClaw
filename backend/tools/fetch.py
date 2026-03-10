from langchain_community.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field
from langchain_core.callbacks import CallbackManagerForToolRun
import requests
from bs4 import BeautifulSoup
import markdownify
import os
import mimetypes

class FetchUrlInput(BaseModel):
    url: str = Field(description="The URL to fetch content from")

class FetchUrlTool(BaseTool):
    name: str = "fetch_url"
    description: str = "Fetches the content of a URL. If it's a webpage, returns it as Markdown. If it's a file (PDF, image, etc.), downloads it to the Downloads folder."
    args_schema: Type[BaseModel] = FetchUrlInput

    def _run(self, url: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": "https://www.bilibili.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        }
        
        try:
            # 1. Head request to check content type
            try:
                head = requests.head(url, headers=headers, allow_redirects=True, timeout=10)
                content_type = head.headers.get("Content-Type", "").lower()
            except:
                # Fallback to GET if HEAD fails
                content_type = "text/html"

            # 2. If it's a web page, fetch and convert to Markdown
            if "text/html" in content_type or "text/plain" in content_type or "application/json" in content_type:
                response = requests.get(url, headers=headers, timeout=20)
                response.raise_for_status()
                response.encoding = response.apparent_encoding # Fix encoding issues
                
                # If it's JSON, return it directly
                if "application/json" in content_type:
                    return response.text
                
                # Use markdownify for better conversion
                md_content = markdownify.markdownify(response.text, heading_style="ATX")
                return md_content[:10000] # Limit length to prevent context overflow

            # 3. If it's a binary file, download it
            else:
                response = requests.get(url, headers=headers, stream=True, timeout=60)
                response.raise_for_status()
                
                # Determine filename
                filename = os.path.basename(url.split("?")[0])
                if not filename:
                    ext = mimetypes.guess_extension(content_type) or ".bin"
                    filename = f"downloaded_file{ext}"
                
                # Save to Downloads folder
                download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
                os.makedirs(download_dir, exist_ok=True)
                file_path = os.path.join(download_dir, filename)
                
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                return f"File downloaded successfully to: {file_path}"

        except Exception as e:
            return f"Error fetching URL: {str(e)}"

def get_fetch_tool():
    return FetchUrlTool()
