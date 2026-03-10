import asyncio
import threading
import time
from typing import Any, List, Optional
from pydantic import create_model, BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool
from mcp import ClientSession
from mcp.client.sse import sse_client
from langchain_core.callbacks import CallbackManagerForToolRun

# URL from user
MCP_SSE_URL = "https://web-mcp.koyeb.app/sse/97fdaddc-2008-43ed-9c44-0c79e1ecd8c7"

class MCPClientManager:
    _instance = None
    
    def __init__(self, url: str):
        self.url = url
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self.session: Optional[ClientSession] = None
        self._ready = threading.Event()
        
        # Initialize connection in the loop
        asyncio.run_coroutine_threadsafe(self._connect(), self.loop)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = MCPClientManager(MCP_SSE_URL)
        return cls._instance

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _connect(self):
        """Maintains the SSE connection"""
        while True:
            try:
                # print(f"Connecting to MCP SSE: {self.url}")
                async with sse_client(self.url) as (read_stream, write_stream):
                    async with ClientSession(read_stream, write_stream) as session:
                        self.session = session
                        await session.initialize()
                        self._ready.set()
                        # print("MCP Connected and Initialized")
                        
                        # Keep session alive
                        await asyncio.Future() 
            except Exception as e:
                print(f"MCP Connection Error: {e}")
                self._ready.clear()
                self.session = None
                await asyncio.sleep(5) # Retry delay

    def get_tools_sync(self) -> List[Any]:
        """Fetch tools list synchronously"""
        # Wait for connection
        start_time = time.time()
        while not self._ready.is_set():
            if time.time() - start_time > 10:
                print("Timeout waiting for MCP connection")
                return []
            time.sleep(0.1)
            
        future = asyncio.run_coroutine_threadsafe(self._list_tools(), self.loop)
        try:
            return future.result(timeout=10)
        except Exception as e:
            print(f"Error fetching tools: {e}")
            return []

    async def _list_tools(self):
        if not self.session:
            raise Exception("No active MCP session")
        return await self.session.list_tools()

    def call_tool_sync(self, name: str, arguments: dict) -> Any:
        """Call tool synchronously"""
        if not self._ready.is_set():
             return "Error: MCP connection not ready"
             
        future = asyncio.run_coroutine_threadsafe(self._call_tool(name, arguments), self.loop)
        try:
            return future.result(timeout=60)
        except Exception as e:
            return f"Error calling tool {name}: {e}"

    async def _call_tool(self, name: str, arguments: dict):
        if not self.session:
            raise Exception("No active MCP session")
        result = await self.session.call_tool(name, arguments)
        return result

class CheckMCPStatusInput(BaseModel):
    pass

class CheckMCPStatusTool(BaseTool):
    name: str = "check_mcp_status"
    description: str = "Checks if the MCP server is connected and returns the list of available tools."
    args_schema: Type[BaseModel] = CheckMCPStatusInput

    def _run(self, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        manager = MCPClientManager.get_instance()
        if not manager._ready.is_set():
            return "MCP Status: Disconnected. Remote server is not reachable."
        
        # Try to list tools to verify connection
        try:
            future = asyncio.run_coroutine_threadsafe(manager._list_tools(), manager.loop)
            tools_data = future.result(timeout=5)
            tool_names = [t.name for t in tools_data.tools]
            return f"MCP Status: Connected.\nAvailable Tools: {', '.join(tool_names)}"
        except Exception as e:
            return f"MCP Status: Connected but failed to list tools. Error: {e}"

def create_mcp_tools() -> List[BaseTool]:
    manager = MCPClientManager.get_instance()
    
    # Try to fetch tools
    mcp_tools_data = manager.get_tools_sync()
    langchain_tools = []
    
    if hasattr(mcp_tools_data, 'tools'):
        for tool in mcp_tools_data.tools:
            # Create Pydantic model for args
            fields = {}
            if tool.inputSchema and 'properties' in tool.inputSchema:
                for prop_name, prop_def in tool.inputSchema['properties'].items():
                    t = str
                    prop_type = prop_def.get('type')
                    if prop_type == 'number' or prop_type == 'integer':
                        t = float
                    elif prop_type == 'boolean':
                        t = bool
                    elif prop_type == 'array':
                        t = list
                    
                    # Check if required
                    is_required = prop_name in tool.inputSchema.get('required', [])
                    default = ... if is_required else None
                    fields[prop_name] = (t, default)
            
            # Create dynamic model
            # Ensure model name is unique and valid
            safe_name = tool.name.replace("-", "_") + "_Args"
            ArgsModel = create_model(safe_name, **fields)
            
            # Closure for run function
            def make_run_func(t_name):
                def _run(**kwargs):
                    result = manager.call_tool_sync(t_name, kwargs)
                    # Result is CallToolResult
                    if hasattr(result, 'content'):
                        text_content = []
                        for item in result.content:
                            if item.type == 'text':
                                text_content.append(item.text)
                            elif item.type == 'image':
                                text_content.append(f"[Image: {item.mimeType}]")
                        return "\n".join(text_content)
                    return str(result)
                return _run

            lc_tool = StructuredTool.from_function(
                func=make_run_func(tool.name),
                name=f"mcp_{tool.name.replace('-', '_')}", # Prefix to avoid conflicts
                description=tool.description or f"MCP Tool: {tool.name}",
                args_schema=ArgsModel
            )
            langchain_tools.append(lc_tool)
            
    # Add the status check tool
    langchain_tools.append(CheckMCPStatusTool())
            
    return langchain_tools
