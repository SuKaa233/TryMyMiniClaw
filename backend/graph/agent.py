from typing import TypedDict, List, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
import os
import json

# 导入工具
from backend.tools import get_core_tools
from backend.tools.rag import get_rag_tool

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

def get_system_prompt() -> str:
    prompt_parts = []

    files = [
        "backend/workspace/SKILLS_SNAPSHOT.md",
        "backend/workspace/SOUL.md",
        "backend/workspace/IDENTITY.md",
        "backend/workspace/USER.md",
        "backend/workspace/AGENTS.md",
        "backend/memory/MEMORY.md"
    ]

    if not os.path.exists("backend/workspace/SKILLS_SNAPSHOT.md"):
        # 确保目录存在
        os.makedirs("backend/workspace", exist_ok=True)
        with open("backend/workspace/SKILLS_SNAPSHOT.md", "w", encoding="utf-8") as f:
            f.write("<available_skills>\n</available_skills>")

    for file_path in files:
        full_path = os.path.join(os.getcwd(), file_path)
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
                prompt_parts.append(content)

    return "\n\n".join(prompt_parts)

def sanitize_messages(messages: List[BaseMessage]) -> List[BaseMessage]:
    """
    确保每个 ToolMessage 在前面的 AIMessage 中都有对应的工具调用。
    如果没有，丢弃该 ToolMessage 以防止 'tool_call_id not found' 错误。
    """
    sanitized = []
    # 我们需要向前/向后查看，所以通过索引迭代或跟踪预期的工具调用
    
    i = 0
    while i < len(messages):
        msg = messages[i]
        
        if isinstance(msg, ToolMessage):
            # 检查前一条消息是否为带有此 tool_call_id 的 AIMessage
            # 或者它是否属于以 AIMessage 开头的一系列 ToolMessage
            is_valid = False
            last_msg_info = "None"
            
            # 向后搜索最近的 AIMessage
            # (跳过中间的其他 ToolMessage)
            found_ai_msg = None
            if sanitized:
                for j in range(len(sanitized) - 1, -1, -1):
                    m = sanitized[j]
                    if isinstance(m, AIMessage):
                        found_ai_msg = m
                        break
                    elif isinstance(m, ToolMessage):
                        continue # 跳过其他工具消息
                    else:
                        break # 在 User/System 消息处停止
            
            if found_ai_msg:
                last_msg_info = f"AIMessage tool_calls={len(found_ai_msg.tool_calls)}"
                if found_ai_msg.tool_calls:
                    for tc in found_ai_msg.tool_calls:
                        if tc.get("id") == msg.tool_call_id:
                            is_valid = True
                            break
            
            if is_valid:
                sanitized.append(msg)
            else:
                print(f"警告：丢弃孤立的 ToolMessage，ID 为 {msg.tool_call_id}。前一个 AIMessage 信息：{last_msg_info}")
        else:
            sanitized.append(msg)
        i += 1
            
    return sanitized

def create_graph():
    # 工具
    tools = get_core_tools(os.getcwd())
    tools.append(get_rag_tool())

    # 模型
    model_name = os.getenv("MODEL_NAME", "moonshot-v1-8k")
    base_url = os.getenv("OPENAI_API_BASE", "https://api.moonshot.cn/v1")
    api_key = os.getenv("OPENAI_API_KEY")

    model = ChatOpenAI(
        model_name=model_name,
        temperature=0,
        base_url=base_url,
        api_key=api_key
    )

    # 绑定工具（原生函数调用）
    # Kimi/Moonshot 支持 OpenAI 兼容的工具调用
    model = model.bind_tools(tools)

    # 节点
    def agent_node(state: AgentState):
        messages = state["messages"]

        # 注入系统提示词
        system_prompt = get_system_prompt()
        
        # 过滤掉旧的系统消息以避免重复/混淆
        filtered_messages = [m for m in messages if not isinstance(m, SystemMessage)]
        
        # 清理消息以防止 400 错误
        sanitized_messages = sanitize_messages(filtered_messages)

        # 预置当前系统提示词
        final_messages = [SystemMessage(content=system_prompt)] + sanitized_messages

        try:
            response = model.invoke(final_messages)
            return {"messages": [response]}
        except Exception as e:
            return {"messages": [AIMessage(content=f"Error invoking model: {str(e)}")]}

    # 定义图
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))

    workflow.set_entry_point("agent")

    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        # 如果模型调用了工具，它会返回带有 tool_calls 的消息
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")

    return workflow.compile()
