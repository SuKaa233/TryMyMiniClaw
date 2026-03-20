from langchain_core.tools import tool
from typing import Optional, List, Dict, Any
import json
from backend.ontology.service import ontology_service
from backend.ontology.mysql_sync import mysql_syncer

@tool
def import_mysql_to_neo4j() -> str:
    """
    Connect to a user's MySQL database (using env credentials), read its tables, rows, and foreign key relationships, 
    and automatically sync/import them into the Neo4j ontology graph database.
    Call this tool when the user asks to sync, import, or read from their MySQL database into the graph.
    """
    try:
        stats = mysql_syncer.sync()
        return json.dumps({
            "status": "success",
            "message": "MySQL to Neo4j sync completed successfully.",
            "stats": stats
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to sync MySQL to Neo4j: {str(e)}",
            "instruction": "Please ensure MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, and MYSQL_DATABASE are correctly set in the .env file."
        }, ensure_ascii=False, indent=2)

@tool
def propose_create_project(name: str, description: str = "", budget: float = 0.0, status: str = "Active"):
    """
    Propose creating a new Project. Returns a UI form definition for the user to confirm.
    Use this when the user wants to create a project.
    """
    return json.dumps({
        "ui_type": "form",
        "form_type": "project",
        "initial_data": {
            "name": name,
            "description": description,
            "budget": budget,
            "status": status
        }
    })

@tool
def propose_create_team(name: str, description: str = ""):
    """
    Propose creating a new Team. Returns a UI form definition.
    """
    return json.dumps({
        "ui_type": "form",
        "form_type": "team",
        "initial_data": {
            "name": name,
            "description": description
        }
    })

@tool
def propose_create_developer(name: str, role: str, skills: str = "", experience_years: int = 0):
    """
    Propose creating a new Developer.
    skills should be a comma-separated string.
    """
    return json.dumps({
        "ui_type": "form",
        "form_type": "developer",
        "initial_data": {
            "name": name,
            "role": role,
            "skills": [s.strip() for s in skills.split(",") if s.strip()],
            "experience_years": experience_years
        }
    })

@tool
def propose_create_requirement(name: str, description: str = "", priority: str = "Medium"):
    """
    Propose creating a new Requirement.
    """
    return json.dumps({
        "ui_type": "form",
        "form_type": "requirement",
        "initial_data": {
            "name": name,
            "description": description,
            "priority": priority
        }
    })

@tool
def propose_create_task(name: str, description: str = "", estimated_hours: float = 0.0, priority: str = "Medium"):
    """
    Propose creating a new Task.
    """
    return json.dumps({
        "ui_type": "form",
        "form_type": "task",
        "initial_data": {
            "name": name,
            "description": description,
            "estimated_hours": estimated_hours,
            "priority": priority
        }
    })

@tool
def get_graph_schema() -> str:
    """
    Get the schema of the graph database, including node labels and relationship types.
    Use this to understand the structure of the data in the database.
    """
    # This is a simplified schema retrieval.
    # In a real scenario, we might query db.schema.visualization() or similar.
    # But for now, we return the static schema we defined.
    return """
    Nodes:
    - Project (id, name, description, budget, status, start_date, end_date)
    - Team (id, name, description, lead_id)
    - Developer (id, name, role, skills, experience_years)
    - Requirement (id, name, description, priority, status, deadline)
    - Task (id, name, description, estimated_hours, priority, status, assignee_id, requirement_id)

    Relationships:
    - Project -[HAS_TEAM]-> Team
    - Team -[HAS_DEVELOPER]-> Developer
    - Project -[HAS_REQUIREMENT]-> Requirement
    - Task -[OF]-> Requirement
    - Task -[ASSIGNED_TO]-> Developer
    """

@tool
def search_knowledge_graph(query: str) -> str:
    """
    Search the knowledge graph for entities and their relationships.
    Returns a list of matching entities with their context.
    """
    try:
        results = ontology_service.semantic_search(query, limit=5)
        return json.dumps(results, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error searching graph: {str(e)}"

@tool
def list_entities(entity_type: str, limit: int = 10) -> str:
    """
    List entities of a specific type (Project, Team, Developer, Requirement, Task).
    Returns a UI table definition.
    Use this when the user asks to "list", "show", or "get" all entities of a certain type.
    """
    # Map input type to label
    type_map = {
        "project": "Project",
        "team": "Team",
        "developer": "Developer",
        "requirement": "Requirement",
        "task": "Task"
    }
    label = type_map.get(entity_type.lower())
    if not label:
        return json.dumps({"error": f"Unknown entity type: {entity_type}"})

    # Fetch data directly using service (we need to add a list method or use search)
    # For simplicity, we'll use a Cypher query here or add a method to service.
    # Let's use a direct Cypher query via service's db connector for now to avoid modifying service too much
    # Or better, use get_entity but we need 'get_all'.
    
    # Let's just query via the service's db driver if possible, or add a helper.
    # Accessing db directly here is a bit hacky but works for tool.
    from backend.ontology.connector import db
    
    query = f"MATCH (n:{label}) RETURN n LIMIT $limit"
    data = []
    
    try:
        if db.driver:
            from backend.ontology.service import _normalize_neo4j_value
            with db.driver.session() as session:
                result = session.run(query, limit=limit)
                for record in result:
                    node = dict(record["n"])
                    data.append(_normalize_neo4j_value(node))
    except Exception as e:
        return json.dumps({"error": str(e)})

    # Return UI definition
    return json.dumps({
        "ui_type": "table",
        "form_type": entity_type, # Align with ui logic key
        "data": data
    })

ontology_tools = [
    propose_create_project,
    propose_create_team,
    propose_create_developer,
    propose_create_requirement,
    propose_create_task,
    get_graph_schema,
    search_knowledge_graph,
    list_entities,
    import_mysql_to_neo4j
]
