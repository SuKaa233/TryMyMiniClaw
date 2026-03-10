from .terminal import get_terminal_tool
from .python_repl import get_python_repl_tool
from .fetch import get_fetch_tool
from .files import get_read_file_tool, get_list_directory_tool, get_write_file_tool
from .browser import get_browser_tools
from .bilibili import get_bilibili_tools
from .mcp import create_mcp_tools

def get_core_tools(root_dir: str = "."):
    tools = [
        get_terminal_tool(root_dir),
        get_python_repl_tool(),
        get_fetch_tool(),
        get_read_file_tool(root_dir),
        get_list_directory_tool(root_dir),
        get_write_file_tool(root_dir),
    ]
    # Add browser tools
    tools.extend(get_browser_tools())
    # Add bilibili tools
    tools.extend(get_bilibili_tools())
    
    # Add MCP tools
    try:
        # print("Loading MCP tools...")
        mcp_tools = create_mcp_tools()
        tools.extend(mcp_tools)
        # print(f"Loaded {len(mcp_tools)} MCP tools")
    except Exception as e:
        print(f"Warning: Failed to load MCP tools: {e}")
        
    return tools
