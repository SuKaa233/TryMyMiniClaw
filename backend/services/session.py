import os
import json
from typing import List, Any
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

def load_session_messages(session_id: str):
    session_file = os.path.join(os.getcwd(), f"backend/sessions/{session_id}.json")
    messages = []
    
    if os.path.exists(session_file):
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # Convert JSON to LangChain messages
                for msg in data:
                    msg_type = msg.get("type")
                    if msg_type == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg_type == "assistant":
                        # Restore tool_calls if present
                        tool_calls = msg.get("tool_calls")
                        # Pydantic validation: tool_calls must be a list if provided
                        if tool_calls is None:
                            tool_calls = []
                        messages.append(AIMessage(content=msg.get("content", "") or "", tool_calls=tool_calls))
                    elif msg_type == "tool":
                        # Restore tool message with tool_call_id
                        tool_call_id = msg.get("tool_call_id")
                        if tool_call_id:
                            messages.append(ToolMessage(content=msg["content"], tool_call_id=tool_call_id, name=msg.get("name")))
        except Exception as e:
            print(f"Error loading session: {e}")
            messages = []
            
    return messages

def save_session_messages(session_id: str, messages: List[Any]):
    session_file = os.path.join(os.getcwd(), f"backend/sessions/{session_id}.json")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(session_file), exist_ok=True)
    
    def message_to_dict(msg):
        """Convert a LangChain message to a dict for JSON serialization"""
        if isinstance(msg, HumanMessage):
            return {"type": "user", "content": msg.content}
        elif isinstance(msg, AIMessage):
            entry = {"type": "assistant", "content": msg.content}
            # Always save tool_calls if present
            if msg.tool_calls:
                entry["tool_calls"] = msg.tool_calls
            return entry
        elif isinstance(msg, ToolMessage):
            return {"type": "tool", "content": msg.content, "tool_call_id": msg.tool_call_id, "name": msg.name}
        return None
    
    # Convert all messages to dicts
    new_history = []
    for msg in messages:
        msg_dict = message_to_dict(msg)
        if msg_dict:
            new_history.append(msg_dict)
            
    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(new_history, f, ensure_ascii=False, indent=2)

def serialize_message(msg):
    if isinstance(msg, HumanMessage):
        return {"role": "user", "content": msg.content}
    elif isinstance(msg, AIMessage):
        return {
            "role": "assistant", 
            "content": msg.content, 
            "tool_calls": msg.tool_calls if hasattr(msg, "tool_calls") else []
        }
    elif isinstance(msg, ToolMessage):
        return {
            "role": "tool", 
            "content": msg.content, 
            "tool_call_id": msg.tool_call_id,
            "name": msg.name
        }
    return None
