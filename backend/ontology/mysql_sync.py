import os
import pymysql
import uuid
import logging
from backend.ontology.connector import db

logger = logging.getLogger(__name__)

class MySQLToNeo4jSyncer:
    def __init__(self):
        self.host = os.getenv("MYSQL_HOST", "127.0.0.1")
        self.port = int(os.getenv("MYSQL_PORT", 3306))
        self.user = os.getenv("MYSQL_USER", "root")
        self.password = os.getenv("MYSQL_PASSWORD", "")
        self.database = os.getenv("MYSQL_DATABASE", "")
        
    def _get_mysql_connection(self):
        if not self.database:
            raise ValueError("MYSQL_DATABASE is not set in environment variables. Please set it in .env file.")
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            cursorclass=pymysql.cursors.DictCursor
        )

    def sync(self):
        if not db.driver:
            raise Exception("Neo4j database connection not available.")

        stats = {
            "tables_processed": 0,
            "nodes_created": 0,
            "relationships_created": 0
        }

        try:
            conn = self._get_mysql_connection()
        except Exception as e:
            logger.error(f"Failed to connect to MySQL: {e}")
            raise Exception(f"Failed to connect to MySQL: {e}")

        try:
            with conn.cursor() as cursor:
                # 1. Get all tables
                cursor.execute("SHOW TABLES")
                tables = [list(row.values())[0] for row in cursor.fetchall()]
                
                # 2. Get Primary Keys for all tables
                cursor.execute("""
                    SELECT TABLE_NAME, COLUMN_NAME
                    FROM information_schema.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = %s AND CONSTRAINT_NAME = 'PRIMARY'
                """, (self.database,))
                pks = {row['TABLE_NAME']: row['COLUMN_NAME'] for row in cursor.fetchall()}
                
                # 3. Process each table to create nodes
                for table in tables:
                    pk_col = pks.get(table, 'id') # fallback to 'id'
                    
                    cursor.execute(f"SELECT * FROM `{table}`")
                    rows = cursor.fetchall()
                    
                    if not rows:
                        continue
                        
                    stats["tables_processed"] += 1
                    
                    # Convert table name to TitleCase for Label (e.g. user -> User, task_list -> TaskList)
                    label = "".join(word.capitalize() for word in table.split("_"))
                    
                    with db.driver.session() as session:
                        for row in rows:
                            # Generate a unique string ID for Neo4j based on MySQL PK
                            row_pk_val = row.get(pk_col)
                            if row_pk_val is None:
                                mysql_id = f"{table}_{uuid.uuid4()}"
                            else:
                                mysql_id = f"{table}_{row_pk_val}"
                                
                            # Convert datetime/decimals to string for Neo4j compatibility
                            clean_row = {}
                            for k, v in row.items():
                                if v is not None:
                                    clean_row[k] = str(v)
                                    
                            # Create or Merge Node
                            query = (
                                f"MERGE (n:{label} {{_mysql_id: $mysql_id}}) "
                                "ON CREATE SET n += $props, n.id = $uuid, n._source = 'mysql' "
                                "ON MATCH SET n += $props "
                                "RETURN id(n)"
                            )
                            
                            session.run(query, mysql_id=mysql_id, props=clean_row, uuid=str(uuid.uuid4()))
                            stats["nodes_created"] += 1

                # 4. Get Foreign Keys and create relationships
                cursor.execute("""
                    SELECT 
                        TABLE_NAME, COLUMN_NAME, 
                        REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                    FROM information_schema.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = %s 
                      AND REFERENCED_TABLE_NAME IS NOT NULL
                """, (self.database,))
                fks = cursor.fetchall()
                
                with db.driver.session() as session:
                    for fk in fks:
                        source_table = fk['TABLE_NAME']
                        source_col = fk['COLUMN_NAME']
                        target_table = fk['REFERENCED_TABLE_NAME']
                        target_col = fk['REFERENCED_COLUMN_NAME']
                        
                        source_label = "".join(word.capitalize() for word in source_table.split("_"))
                        target_label = "".join(word.capitalize() for word in target_table.split("_"))
                        
                        rel_type = f"RELATES_TO_{target_table.upper()}"
                        
                        # Fix: Cast both properties to string before comparing, since we saved MySQL values as strings in Neo4j properties
                        rel_query = f"""
                        MATCH (a:{source_label}), (b:{target_label})
                        WHERE toString(a.{source_col}) = toString(b.{target_col})
                        MERGE (a)-[r:{rel_type}]->(b)
                        RETURN count(r) as rel_count
                        """
                        try:
                            result = session.run(rel_query)
                            record = result.single()
                            if record:
                                stats["relationships_created"] += record["rel_count"]
                        except Exception as e:
                            logger.error(f"Error creating relationships for {source_table}.{source_col}: {e}")

        finally:
            conn.close()
            
        return stats

mysql_syncer = MySQLToNeo4jSyncer()
