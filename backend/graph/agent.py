from typing import TypedDict, List, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
import os
import json

# Import tools
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
        # Ensure directory exists
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
    Ensure that every ToolMessage has a corresponding tool call in the preceding AIMessage.
    If not, drop the ToolMessage to prevent 'tool_call_id not found' errors.
    """
    sanitized = []
    # We need to look ahead/behind, so iterate by index or keep track of expected tool calls
    
    i = 0
    while i < len(messages):
        msg = messages[i]
        
        if isinstance(msg, ToolMessage):
            # Check if previous message was AIMessage with this tool_call_id
            # Or if it's part of a sequence of ToolMessages preceded by an AIMessage
            is_valid = False
            last_msg_info = "None"
            
            # Search backwards for the most recent AIMessage
            # (Skipping other ToolMessages in between)
            found_ai_msg = None
            if sanitized:
                for j in range(len(sanitized) - 1, -1, -1):
                    m = sanitized[j]
                    if isinstance(m, AIMessage):
                        found_ai_msg = m
                        break
                    elif isinstance(m, ToolMessage):
                        continue # Skip other tool messages
                    else:
                        break # Stop at User/System message
            
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
                print(f"Warning: Dropping orphaned ToolMessage with id {msg.tool_call_id}. Previous AIMessage info: {last_msg_info}")
        else:
            sanitized.append(msg)
        i += 1
            
    return sanitized

def create_graph():
    # Tools
    tools = get_core_tools(os.getcwd())
    tools.append(get_rag_tool())

    # Model
    model_name = os.getenv("MODEL_NAME", "moonshot-v1-8k")
    base_url = os.getenv("OPENAI_API_BASE", "https://api.moonshot.cn/v1")
    api_key = os.getenv("OPENAI_API_KEY")

    model = ChatOpenAI(
        model_name=model_name,
        temperature=0,
        base_url=base_url,
        api_key=api_key
    )

    # Bind tools (Native Function Calling)
    # Kimi/Moonshot supports OpenAI compatible tool calling
    model = model.bind_tools(tools)

    # Nodes
    def agent_node(state: AgentState):
        messages = state["messages"]

        # Inject System Prompt
        system_prompt = get_system_prompt()
        
        # Filter out old system messages to avoid duplicates/confusion
        filtered_messages = [m for m in messages if not isinstance(m, SystemMessage)]
        
        # Sanitize messages to prevent 400 errors
        sanitized_messages = sanitize_messages(filtered_messages)

        # Prepend current system prompt
        final_messages = [SystemMessage(content=system_prompt)] + sanitized_messages

        try:
            response = model.invoke(final_messages)
            return {"messages": [response]}
        except Exception as e:
            return {"messages": [AIMessage(content=f"Error invoking model: {str(e)}")]}

    # Define Graph
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))

    workflow.set_entry_point("agent")

    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        # If the model called a tool, it returns a message with tool_calls
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")

    return workflow.compile()
