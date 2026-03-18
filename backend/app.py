import sys
import os
import warnings

# Suppress Pydantic V1 warnings from LangChain
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_core")
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import uvicorn
from dotenv import load_dotenv

from graph.agent import create_graph
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

# Import routers
from backend.api.v1.endpoints import generation, ppt_generation, rag, ontology

# Load environment variables
load_dotenv()

app = FastAPI(title="Mini-OpenClaw Backend", version="1.0.0")

# Mount Static Files
static_dir = os.path.join(os.getcwd(), "backend", "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include Routers
app.include_router(generation.router, prefix="/api/v1", tags=["generation"])
app.include_router(ppt_generation.router, prefix="/api/v1", tags=["ppt_generation"])
app.include_router(rag.router, prefix="/api/v1/rag", tags=["rag"])
app.include_router(ontology.router, prefix="/api/v1/ontology", tags=["ontology"])

# Initialize Agent Graph
agent_graph = create_graph()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Models
class ChatRequest(BaseModel):
    message: str
    session_id: str
    stream: bool = True

class FileRequest(BaseModel):
    path: str
    content: Optional[str] = None

def refresh_skills_snapshot():
    """
    Scans the backend/skills directory for SKILL.md files and aggregates them into
    backend/workspace/SKILLS_SNAPSHOT.md. This allows the agent to 'learn' skills
    dynamically at startup.
    """
    skills_dir = os.path.join(os.getcwd(), "backend/skills")
    snapshot_path = os.path.join(os.getcwd(), "backend/workspace/SKILLS_SNAPSHOT.md")
    
    # Ensure workspace directory exists
    os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
    
    aggregated_content = ["<available_skills>"]
    
    if os.path.exists(skills_dir):
        for item in os.listdir(skills_dir):
            item_path = os.path.join(skills_dir, item)
            if os.path.isdir(item_path):
                skill_md = os.path.join(item_path, "SKILL.md")
                if os.path.exists(skill_md):
                    try:
                        with open(skill_md, "r", encoding="utf-8") as f:
                            content = f.read()
                            # Wrap each skill in a tag for clarity, or just append
                            # Adding some separation and context
                            aggregated_content.append(f"\n<!-- Skill: {item} -->\n{content}\n")
                    except Exception as e:
                        print(f"Error reading skill {item}: {e}")
    
    aggregated_content.append("</available_skills>")
    
    try:
        with open(snapshot_path, "w", encoding="utf-8") as f:
            f.write("\n".join(aggregated_content))
        print(f"Successfully refreshed skills snapshot at {snapshot_path}")
    except Exception as e:
        print(f"Error writing skills snapshot: {e}")

from backend.services.session import load_session_messages, save_session_messages, serialize_message

# Startup Event
@app.on_event("startup")
async def startup_event():
    refresh_skills_snapshot()

# Routes
@app.get("/")
async def root():
    return {"message": "Mini-OpenClaw Backend is running"}

@app.get("/api/skills")
async def get_skills():
    skills = []
    
    # 1. Scan backend/skills
    skills_dir = os.path.join(os.getcwd(), "backend/skills")
    if os.path.exists(skills_dir):
        for item in os.listdir(skills_dir):
            item_path = os.path.join(skills_dir, item)
            if os.path.isdir(item_path):
                skill_md = os.path.join(item_path, "SKILL.md")
                if os.path.exists(skill_md):
                    skills.append(f"backend/skills/{item}/SKILL.md")

    # 2. Add SKILLS_SNAPSHOT.md
    if os.path.exists(os.path.join(os.getcwd(), "backend/workspace/SKILLS_SNAPSHOT.md")):
        skills.append("backend/workspace/SKILLS_SNAPSHOT.md")
        
    return skills

@app.get("/api/sessions/{session_id}")
async def get_session_history(session_id: str):
    messages = load_session_messages(session_id)
    # Convert to simple format for frontend
    history = []
    for msg in messages:
        serialized = serialize_message(msg)
        if serialized:
            history.append(serialized)
    return history

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    session_file = os.path.join(os.getcwd(), f"backend/sessions/{session_id}.json")
    if os.path.exists(session_file):
        try:
            os.remove(session_file)
            return {"message": "Session deleted successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.post("/api/chat")
async def chat(request: ChatRequest):
    print(f"Received chat request: {request.message} (Session: {request.session_id})")
    
    messages = load_session_messages(request.session_id)
    initial_len = len(messages)
    
    # Construct input message
    input_message = HumanMessage(content=request.message)
    messages.append(input_message)
    
    # Run the graph
    try:
        final_state = await agent_graph.ainvoke({"messages": messages})
        
        # Get all new messages (including the user input we just added? No, let's return from user input onwards)
        # Actually, user input is already displayed on frontend optimistically.
        # We want everything AFTER the user input.
        # The messages list in final_state includes all history.
        # initial_len was history size.
        # messages list passed to ainvoke had size initial_len + 1 (user input).
        # So new messages generated by agent are from index (initial_len + 1) onwards.
        
        new_messages_objects = final_state["messages"][initial_len+1:]
        new_messages = []
        for msg in new_messages_objects:
            serialized = serialize_message(msg)
            if serialized:
                new_messages.append(serialized)
        
        # Save history
        save_session_messages(request.session_id, final_state["messages"])
        
        return {"new_messages": new_messages}
    except Exception as e:
        print(f"Error executing graph: {e}")
        import traceback
        traceback.print_exc()
        # Save what we have so far? No, maybe not if it crashed.
        # But if it's a tool error, we might want to save it.
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files")
async def read_file_content(path: str):
    # Security check: ensure path is within project root
    if ".." in path or path.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    full_path = os.path.join(os.getcwd(), path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/files")
async def write_file_content(request: FileRequest):
    if not request.content:
        raise HTTPException(status_code=400, detail="Content is required")
    
    # Security check
    if ".." in request.path or request.path.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid path")
        
    full_path = os.path.join(os.getcwd(), request.path)
    
    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(request.content)
        return {"message": "File saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions")
async def get_sessions():
    sessions_dir = os.path.join(os.getcwd(), "backend/sessions")
    if not os.path.exists(sessions_dir):
        return []
    
    files = os.listdir(sessions_dir)
    sessions = [f.replace(".json", "") for f in files if f.endswith(".json")]
    # Sort sessions by creation time (optional, but good for UX)
    sessions.sort(key=lambda s: os.path.getmtime(os.path.join(sessions_dir, f"{s}.json")), reverse=True)
    return sessions

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8002, reload=True)
