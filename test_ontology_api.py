import requests
import json
import time

BASE_URL = "http://localhost:8002/api/v1/ontology"

def test_ontology():
    print("Testing Ontology API...")
    
    # 1. Create Project
    project_data = {
        "name": "Project Alpha",
        "description": "A top secret AI project",
        "budget": 100000.0,
        "status": "Active"
    }
    try:
        res = requests.post(f"{BASE_URL}/projects", json=project_data)
        if res.status_code == 200:
            project = res.json()
            print(f"Project Created: {project['id']}")
        else:
            print(f"Failed to create project: {res.text}")
            return
    except Exception as e:
        print(f"Error connecting to backend: {e}")
        return

    project_id = project["id"]

    # 2. Create Team
    team_data = {
        "name": "Alpha Team",
        "description": "Core development team"
    }
    res = requests.post(f"{BASE_URL}/teams", json=team_data)
    team = res.json()
    print(f"Team Created: {team['id']}")
    team_id = team["id"]

    # 3. Create Developer
    dev_data = {
        "name": "Alice",
        "role": "Backend Engineer",
        "skills": ["Python", "Neo4j"],
        "experience_years": 5
    }
    res = requests.post(f"{BASE_URL}/developers", json=dev_data)
    dev = res.json()
    print(f"Developer Created: {dev['id']}")
    dev_id = dev["id"]

    # 4. Create Requirement
    req_data = {
        "name": "Implement Graph Database",
        "description": "Store data in Neo4j",
        "priority": "High"
    }
    res = requests.post(f"{BASE_URL}/requirements", json=req_data)
    req = res.json()
    print(f"Requirement Created: {req['id']}")
    req_id = req["id"]

    # 5. Create Task
    task_data = {
        "name": "Setup Neo4j",
        "description": "Install and configure Neo4j instance",
        "estimated_hours": 4.0,
        "status": "In Progress"
    }
    res = requests.post(f"{BASE_URL}/tasks", json=task_data)
    task = res.json()
    print(f"Task Created: {task['id']}")
    task_id = task["id"]

    # 6. Create Relations
    relations = [
        {"source_id": project_id, "target_id": team_id, "relation_type": "HAS_TEAM"},
        {"source_id": team_id, "target_id": dev_id, "relation_type": "HAS_DEVELOPER"},
        {"source_id": project_id, "target_id": req_id, "relation_type": "HAS_REQUIREMENT"},
        {"source_id": task_id, "target_id": req_id, "relation_type": "OF"},
        {"source_id": task_id, "target_id": dev_id, "relation_type": "ASSIGNED_TO"}
    ]

    for rel in relations:
        res = requests.post(f"{BASE_URL}/relations", json=rel)
        if res.status_code == 200:
            print(f"Relation Created: {rel['relation_type']}")
        else:
            print(f"Failed to create relation: {res.text}")

    # 7. Semantic Search
    print("\nTesting Semantic Search...")
    time.sleep(1) # Allow index to update
    query = "Graph Database"
    res = requests.get(f"{BASE_URL}/search", params={"q": query})
    if res.status_code == 200:
        results = res.json()
        print(f"Found {len(results)} results for '{query}'")
        for r in results:
            print(f"- {r.get('name')} ({r.get('_type')}) Score: {r.get('_score')}")
            if r.get("_context"):
                print(f"  Context: {len(r['_context'])} related items")
    else:
        print(f"Search failed: {res.text}")

if __name__ == "__main__":
    test_ontology()
