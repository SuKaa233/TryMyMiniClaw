from typing import List, Optional, Dict, Any
from backend.ontology.connector import db
from backend.ontology.models import (
    OntologyInstance, SemanticRelation,
    Project, Team, Developer, Requirement, Task,
    EntityCreate, RelationCreate
)
from neo4j.exceptions import ConstraintError
from neo4j.time import DateTime, Date, Time
import logging

logger = logging.getLogger(__name__)

def _normalize_neo4j_value(value: Any) -> Any:
    """
    Recursively convert Neo4j types to Python native types (mostly ISO strings for dates).
    """
    if isinstance(value, (DateTime, Date, Time)):
        return value.iso_format()
    if isinstance(value, dict):
        return {k: _normalize_neo4j_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_neo4j_value(v) for v in value]
    return value

class OntologyService:
    def __init__(self):
        self.db = db

    def create_entity(self, label: str, entity: EntityCreate) -> Dict[str, Any]:
        """
        Create a new entity node in the graph with the given label.
        """
        if not self.db.driver:
            raise Exception("Neo4j database connection not available. Please ensure Neo4j is running.")
            
        query = (
            f"CREATE (n:{label} {{id: $id, name: $name, description: $description, created_at: datetime()}}) "
            "SET n += $properties "
            "RETURN n"
        )
        # Generate ID if not present (handled by Pydantic usually, but we need it for Cypher)
        import uuid
        entity_id = str(uuid.uuid4())
        
        params = {
            "id": entity_id,
            "name": entity.name,
            "description": entity.description,
            "properties": entity.properties
        }

        try:
            with self.db.driver.session() as session:
                result = session.run(query, params)
                record = result.single()
                if record:
                    node = record["n"]
                    return _normalize_neo4j_value(dict(node))
        except Exception as e:
            logger.error(f"Error creating entity {label}: {e}")
            raise e
        return None

    def get_entity(self, label: str, entity_id: str) -> Optional[Dict[str, Any]]:
        if not self.db.driver:
            raise Exception("Neo4j database connection not available. Please ensure Neo4j is running.")
        query = f"MATCH (n:{label} {{id: $id}}) RETURN n"
        with self.db.driver.session() as session:
            result = session.run(query, id=entity_id)
            record = result.single()
            if record:
                return _normalize_neo4j_value(dict(record["n"]))
        return None
    
    def update_entity(self, label: str, entity_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        query = (
            f"MATCH (n:{label} {{id: $id}}) "
            "SET n += $updates, n.updated_at = datetime() "
            "RETURN n"
        )
        with self.db.driver.session() as session:
            result = session.run(query, id=entity_id, updates=updates)
            record = result.single()
            if record:
                return _normalize_neo4j_value(dict(record["n"]))
        return None

    def delete_entity(self, label: str, entity_id: str) -> bool:
        query = f"MATCH (n:{label} {{id: $id}}) DETACH DELETE n"
        with self.db.driver.session() as session:
            session.run(query, id=entity_id)
            return True # Simplified

    def create_relation(self, relation: RelationCreate) -> Dict[str, Any]:
        if not self.db.driver:
            raise Exception("Neo4j database connection not available. Please ensure Neo4j is running.")
        query = (
            "MATCH (a), (b) "
            "WHERE a.id = $source_id AND b.id = $target_id "
            f"MERGE (a)-[r:{relation.relation_type}]->(b) "
            "SET r += $properties "
            "RETURN r"
        )
        params = {
            "source_id": relation.source_id,
            "target_id": relation.target_id,
            "properties": relation.properties
        }
        with self.db.driver.session() as session:
            result = session.run(query, params)
            record = result.single()
            if record:
                # Neo4j relationship object to dict is a bit different
                rel = record["r"]
                return _normalize_neo4j_value({
                    "id": rel.id,
                    "start_node": rel.start_node.id, # Internal ID
                    "end_node": rel.end_node.id,     # Internal ID
                    "type": rel.type,
                    "properties": dict(rel)
                })
        return None

    def semantic_search(self, query_text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform a fulltext search on nodes and return matching nodes with their context.
        Context includes directly connected nodes.
        """
        if not self.db.driver:
            raise Exception("Neo4j database connection not available. Please ensure Neo4j is running.")
            
        # Try a more general search if specific fulltext indexes fail or are empty
        # This is a fallback to allow searching properties directly using CONTAINS
        # if the fulltext index doesn't return results (e.g. index not yet populated or query issue)
        
        # Standard Fulltext Search Query
        cypher_query = """
        CALL {
            CALL db.index.fulltext.queryNodes("project_search", $query) YIELD node, score RETURN node, score, "Project" as type
            UNION
            CALL db.index.fulltext.queryNodes("team_search", $query) YIELD node, score RETURN node, score, "Team" as type
            UNION
            CALL db.index.fulltext.queryNodes("developer_search", $query) YIELD node, score RETURN node, score, "Developer" as type
            UNION
            CALL db.index.fulltext.queryNodes("requirement_search", $query) YIELD node, score RETURN node, score, "Requirement" as type
            UNION
            CALL db.index.fulltext.queryNodes("task_search", $query) YIELD node, score RETURN node, score, "Task" as type
        }
        WITH node, score, type
        ORDER BY score DESC
        LIMIT $limit
        
        // Fetch context: 1-hop relationships
        OPTIONAL MATCH (node)-[r]-(related)
        RETURN node, type, score, collect({rel: type(r), node: related}) as context
        """
        
        try:
            with self.db.driver.session() as session:
                result = session.run(cypher_query, query=query_text, limit=limit)
                results = []
                for record in result:
                    node_data = dict(record["node"])
                    node_data["_type"] = record["type"]
                    node_data["_score"] = record["score"]
                    
                    context_data = []
                    for item in record["context"]:
                        if item["node"]:
                            ctx_node = dict(item["node"])
                            ctx_node["_labels"] = list(item["node"].labels)
                            context_data.append({
                                "relationship": item["rel"],
                                "node": ctx_node
                            })
                    
                    node_data["_context"] = context_data
                    results.append(_normalize_neo4j_value(node_data))
                
                if results:
                    return results
        except Exception as e:
            logger.warning(f"Fulltext search failed or returned empty, trying fallback: {e}")
            # We don't raise here, we fall through to the fallback query

        # Fallback: Simple property search using CONTAINS (case-insensitive usually requires lower(), but let's keep simple)
        # Note: This is slower but works without indexes
        fallback_query = """
        MATCH (n)
        WHERE (n:Project OR n:Team OR n:Developer OR n:Requirement OR n:Task)
          AND (toLower(n.name) CONTAINS toLower($q) OR toLower(n.description) CONTAINS toLower($q))
        RETURN n as node, 1.0 as score, labels(n)[0] as type
        LIMIT $limit
        """
        
        with self.db.driver.session() as session:
            # Fix: avoid conflicting 'query' param name if neo4j driver complains
            result = session.run(fallback_query, q=query_text, limit=limit)
            results = []
            for record in result:
                node_data = dict(record["node"])
                node_data["_type"] = record["type"]
                node_data["_score"] = record["score"]
                
                # Fetch context separately for fallback results
                context_query = "MATCH (n)-[r]-(related) WHERE id(n) = $node_id RETURN type(r) as rel, related"
                ctx_result = session.run(context_query, node_id=record["node"].id)
                context_data = []
                for ctx_record in ctx_result:
                    ctx_node = dict(ctx_record["related"])
                    ctx_node["_labels"] = list(ctx_record["related"].labels)
                    context_data.append({
                        "relationship": ctx_record["rel"],
                        "node": ctx_node
                    })

                node_data["_context"] = context_data
                results.append(_normalize_neo4j_value(node_data))
            return results

    def get_all_graph_data(self) -> Dict[str, Any]:
        """
        Fetch all nodes and relationships from the database to build a complete context.
        """
        if not self.db.driver:
            raise Exception("Neo4j database connection not available.")

        # Query to get all nodes and their labels
        nodes_query = "MATCH (n) RETURN n, labels(n) as labels"
        # Query to get all relationships
        rels_query = "MATCH (a)-[r]->(b) RETURN r, a.id as source_id, b.id as target_id, type(r) as type"

        graph_data = {"nodes": [], "relationships": []}

        with self.db.driver.session() as session:
            # Fetch Nodes
            result = session.run(nodes_query)
            for record in result:
                node = dict(record["n"])
                labels = record["labels"]
                # Filter for our known labels if necessary, or keep all
                node["_labels"] = labels
                graph_data["nodes"].append(_normalize_neo4j_value(node))

            # Fetch Relationships
            result = session.run(rels_query)
            for record in result:
                rel = {
                    "source": record["source_id"],
                    "target": record["target_id"],
                    "type": record["type"],
                    "properties": dict(record["r"])
                }
                graph_data["relationships"].append(_normalize_neo4j_value(rel))
        
        return graph_data

ontology_service = OntologyService()
