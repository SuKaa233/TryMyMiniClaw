from langchain_community.tools.file_management.read import ReadFileTool
from langchain_community.tools.file_management.list_dir import ListDirectoryTool
from langchain_community.tools.file_management.write import WriteFileTool
from langchain_core.callbacks import CallbackManagerForToolRun
from typing import Optional
import os

class SafeReadFileTool(ReadFileTool):
    def _run(self, file_path: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            # Check for absolute path override first
            if os.path.isabs(file_path) and os.path.exists(file_path):
                 # Try to read directly if it exists, bypassing root check for this safe tool version
                 try:
                     with open(file_path, "r", encoding="utf-8") as f:
                         return f.read()
                 except Exception:
                     pass # Fallback to standard logic

            # Try default implementation (usually utf-8)
            result = super()._run(file_path, run_manager=run_manager)
            # Check if the result indicates an encoding error (some versions return string instead of raising)
            if isinstance(result, str) and "codec can't decode byte" in result:
                raise UnicodeDecodeError("utf-8", b"", 0, 0, "Fake exception to trigger fallback")
            return result
        except Exception as e:
            # If default utf-8 fails, try to handle it manually
            error_str = str(e)
            if "codec can't decode byte" in error_str or "UnicodeDecodeError" in error_str:
                 try:
                     root = self.root_dir
                     if os.path.isabs(file_path):
                         full_path = file_path
                     else:
                         full_path = os.path.join(root, file_path)
                     
                     if not os.path.exists(full_path):
                         return f"Error: File not found {file_path}"
                         
                     # Try GBK (common for Chinese Windows)
                     try:
                         with open(full_path, "r", encoding="gbk") as f:
                             return f.read()
                     except UnicodeDecodeError:
                         pass
                         
                     # Try Latin-1
                     try:
                         with open(full_path, "r", encoding="latin-1") as f:
                             return f.read()
                     except UnicodeDecodeError:
                         pass
                         
                     # Fallback to replace
                     with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                         return f.read()
                 except Exception as e2:
                     return f"Error reading file with fallback encoding: {e2}"
            return f"Error: {e}"

class SafeListDirectoryTool(ListDirectoryTool):
    def _run(self, dir_path: str = ".", run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            # Allow absolute paths even if outside root_dir
            if os.path.isabs(dir_path) and os.path.exists(dir_path):
                return "\n".join(os.listdir(dir_path))
            
            return super()._run(dir_path, run_manager=run_manager)
        except Exception as e:
            return f"Error listing directory: {e}"

class SafeWriteFileTool(WriteFileTool):
    def _run(self, file_path: str, text: str, append: bool = False, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            # Check for absolute path override
            if os.path.isabs(file_path):
                # Ensure directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                mode = "a" if append else "w"
                with open(file_path, mode, encoding="utf-8") as f:
                    f.write(text)
                return f"File written successfully to {file_path}"
            
            return super()._run(file_path, text, append=append, run_manager=run_manager)
        except Exception as e:
            return f"Error writing file: {e}"

def get_read_file_tool(root_dir: str = "."):
    abs_root = os.path.abspath(root_dir)
    return SafeReadFileTool(root_dir=abs_root)

def get_list_directory_tool(root_dir: str = "."):
    abs_root = os.path.abspath(root_dir)
    return SafeListDirectoryTool(root_dir=abs_root)

def get_write_file_tool(root_dir: str = "."):
    abs_root = os.path.abspath(root_dir)
    return SafeWriteFileTool(root_dir=abs_root)
