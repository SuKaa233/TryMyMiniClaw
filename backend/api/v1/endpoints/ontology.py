from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.ontology.models import (
    Project, Team, Developer, Requirement, Task,
    SemanticRelation, EntityCreate, RelationCreate
)
from backend.ontology.service import ontology_service
from backend.ontology.connector import db
from backend.ontology.agent import ontology_graph
from backend.services.session import load_session_messages, save_session_messages, serialize_message
from langchain_core.messages import HumanMessage, SystemMessage

router = APIRouter()

class OntologyChatRequest(BaseModel):
    message: str
    session_id: str

# --- Helper to create entity ---
def _create_node(label: str, data: EntityCreate):
    try:
        # Convert Pydantic model to dict, excluding None and extra properties logic
        result = ontology_service.create_entity(label, data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.on_event("startup")
async def startup_event():
    # Ensure schema is initialized
    db.init_schema()

@router.post("/chat")
async def chat(request: OntologyChatRequest):
    messages = load_session_messages(request.session_id)
    initial_len = len(messages)
    
    # Check if this is a new session or if we need to inject full context
    if initial_len == 0:
        # Inject full graph data into the system prompt for the first message
        try:
            full_graph = ontology_service.get_all_graph_data()
            graph_context = (
                "Here is the COMPLETE current state of the database. "
                "You MUST use this information to answer user questions accurately. "
                "Do NOT guess or hallucinate. If information is not in this context, say you don't know.\n\n"
                f"Nodes: {len(full_graph['nodes'])}\n"
                f"Relationships: {len(full_graph['relationships'])}\n\n"
                "Details:\n"
                f"{str(full_graph)}" 
            )
            # We will prepend this to the system prompt in the agent, 
            # or we can add it as a SystemMessage here.
            # Since the agent adds its own SystemPrompt, let's add this as a high-priority SystemMessage.
            messages.append(SystemMessage(content=graph_context))
        except Exception as e:
            print(f"Failed to load graph context: {e}")

    # Construct input message
    input_message = HumanMessage(content=request.message)
    messages.append(input_message)
    
    try:
        final_state = await ontology_graph.ainvoke({"messages": messages})
        
        # Get all new messages
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
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# --- Project Endpoints ---

@router.post("/projects", response_model=Dict[str, Any])
async def create_project(project: Project):
    # Extract specific fields and put them into properties for Cypher
    # We exclude base fields that are handled explicitly in create_entity (name, description, id)
    # and created_at/updated_at which are handled by DB or base model
    props = project.dict(exclude={"name", "description", "id", "created_at", "updated_at", "properties"})
    # If the model has a 'properties' field (from OntologyInstance), merge it?
    # Actually, Project model defines specific fields. 
    # Any extra properties in 'properties' dict should also be included.
    if project.properties:
        props.update(project.properties)

    data = EntityCreate(
        name=project.name,
        description=project.description,
        properties=props
    )
    return _create_node("Project", data)

@router.get("/projects/{project_id}", response_model=Dict[str, Any])
async def get_project(project_id: str):
    result = ontology_service.get_entity("Project", project_id)
    if not result:
        raise HTTPException(status_code=404, detail="Project not found")
    return result

# --- Team Endpoints ---

@router.post("/teams", response_model=Dict[str, Any])
async def create_team(team: Team):
    props = team.dict(exclude={"name", "description", "id", "created_at", "updated_at", "properties"})
    if team.properties:
        props.update(team.properties)
        
    data = EntityCreate(
        name=team.name,
        description=team.description,
        properties=props
    )
    return _create_node("Team", data)

@router.get("/teams/{team_id}", response_model=Dict[str, Any])
async def get_team(team_id: str):
    result = ontology_service.get_entity("Team", team_id)
    if not result:
        raise HTTPException(status_code=404, detail="Team not found")
    return result

# --- Developer Endpoints ---

@router.post("/developers", response_model=Dict[str, Any])
async def create_developer(developer: Developer):
    props = developer.dict(exclude={"name", "description", "id", "created_at", "updated_at", "properties"})
    if developer.properties:
        props.update(developer.properties)

    data = EntityCreate(
        name=developer.name,
        description=developer.description,
        properties=props
    )
    return _create_node("Developer", data)

@router.get("/developers/{developer_id}", response_model=Dict[str, Any])
async def get_developer(developer_id: str):
    result = ontology_service.get_entity("Developer", developer_id)
    if not result:
        raise HTTPException(status_code=404, detail="Developer not found")
    return result

# --- Requirement Endpoints ---

@router.post("/requirements", response_model=Dict[str, Any])
async def create_requirement(requirement: Requirement):
    props = requirement.dict(exclude={"name", "description", "id", "created_at", "updated_at", "properties"})
    if requirement.properties:
        props.update(requirement.properties)

    data = EntityCreate(
        name=requirement.name,
        description=requirement.description,
        properties=props
    )
    return _create_node("Requirement", data)

@router.get("/requirements/{requirement_id}", response_model=Dict[str, Any])
async def get_requirement(requirement_id: str):
    result = ontology_service.get_entity("Requirement", requirement_id)
    if not result:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return result

# --- Task Endpoints ---

@router.post("/tasks", response_model=Dict[str, Any])
async def create_task(task: Task):
    props = task.dict(exclude={"name", "description", "id", "created_at", "updated_at", "properties"})
    if task.properties:
        props.update(task.properties)

    data = EntityCreate(
        name=task.name,
        description=task.description,
        properties=props
    )
    return _create_node("Task", data)

@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
async def get_task(task_id: str):
    result = ontology_service.get_entity("Task", task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return result

# --- Relationship Endpoints ---

@router.post("/relations", response_model=Dict[str, Any])
async def create_relation(relation: RelationCreate):
    try:
        result = ontology_service.create_relation(relation)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Semantic Search ---

@router.get("/search", response_model=List[Dict[str, Any]])
async def semantic_search(q: str = Query(..., min_length=1), limit: int = 10):
    try:
        results = ontology_service.semantic_search(q, limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
