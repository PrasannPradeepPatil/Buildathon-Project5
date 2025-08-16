"""Neo4j Graph Database Library

A Python library for Neo4j graph database operations including schema management,
CRUD operations, and advanced query functionality.
"""

from .connection import Neo4jConnection
from .schema_manager import SchemaManager
from .crud_operations import CRUDOperations
from .query_engine import QueryEngine

__version__ = "0.1.0"
__author__ = "Neo4j Graph Library Team"
__email__ = "contact@neo4j-graph-lib.com"

__all__ = [
    "Neo4jConnection",
    "SchemaManager",
    "CRUDOperations",
    "QueryEngine",
]


class Neo4jGraphLib:
    """Main class for Neo4j Graph Database Library.
    
    This class provides a unified interface to all library functionality.
    """
    
    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        """Initialize the Neo4j Graph Library.
        
        Args:
            uri: Neo4j database URI
            username: Database username
            password: Database password
            database: Database name (default: "neo4j")
        """
        self.connection = Neo4jConnection(uri, username, password, database)
        self.schema = SchemaManager(self.connection)
        self.crud = CRUDOperations(self.connection)
        self.query = QueryEngine(self.connection)
    
    def close(self):
        """Close the database connection."""
        self.connection.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()