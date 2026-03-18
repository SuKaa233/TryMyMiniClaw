from neo4j import GraphDatabase
from backend.ontology.config import settings
import logging

logger = logging.getLogger(__name__)

class Neo4jConnector:
    def __init__(self):
        self.driver = None
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI, 
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            self.verify_connection()
        except Exception as e:
            logger.error(f"Failed to create Neo4j driver: {e}")

    def close(self):
        if self.driver:
            self.driver.close()

    def verify_connection(self):
        if self.driver:
            try:
                self.driver.verify_connectivity()
                logger.info("Connected to Neo4j database.")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                self.driver = None # Disable driver if connection fails
                # We might want to raise here depending on how critical this is
                # raise e 

    def init_schema(self):
        """
        Initialize the database schema with constraints and indexes.
        """
        if not self.driver:
            logger.error("Driver not initialized, skipping schema initialization.")
            return

        constraints = [
            "CREATE CONSTRAINT project_id_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT team_id_unique IF NOT EXISTS FOR (t:Team) REQUIRE t.id IS UNIQUE",
            "CREATE CONSTRAINT developer_id_unique IF NOT EXISTS FOR (d:Developer) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT requirement_id_unique IF NOT EXISTS FOR (r:Requirement) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT task_id_unique IF NOT EXISTS FOR (t:Task) REQUIRE t.id IS UNIQUE",
        ]

        indexes = [
            "CREATE FULLTEXT INDEX project_search IF NOT EXISTS FOR (n:Project) ON EACH [n.name, n.description]",
            "CREATE FULLTEXT INDEX team_search IF NOT EXISTS FOR (n:Team) ON EACH [n.name, n.description]",
            "CREATE FULLTEXT INDEX developer_search IF NOT EXISTS FOR (n:Developer) ON EACH [n.name, n.role, n.skills]",
            "CREATE FULLTEXT INDEX requirement_search IF NOT EXISTS FOR (n:Requirement) ON EACH [n.title, n.description]",
            "CREATE FULLTEXT INDEX task_search IF NOT EXISTS FOR (n:Task) ON EACH [n.name, n.description]",
        ]

        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"Constraint created: {constraint}")
                except Exception as e:
                    logger.warning(f"Failed to create constraint: {e}")
            
            for index in indexes:
                try:
                    session.run(index)
                    logger.info(f"Index created: {index}")
                except Exception as e:
                    logger.warning(f"Failed to create index: {e}")

db = Neo4jConnector()
