
import asyncio
import sys
import os

# 添加 backend 目录到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), 'backend')))

from tools.mcp import MCPClientManager

async def check_mcp():
    print("Checking MCP connection...")
    try:
        manager = MCPClientManager.get_instance()
        # 给一点时间连接
        await asyncio.sleep(5)
        
        print("Fetching tools...")
        tools = await manager._list_tools()
        
        if tools:
            print(f"Successfully connected! Found {len(tools.tools)} tools:")
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")
        else:
            print("Connected but no tools found.")
            
    except Exception as e:
        print(f"Failed to connect or fetch tools: {e}")

if __name__ == "__main__":
    asyncio.run(check_mcp())
