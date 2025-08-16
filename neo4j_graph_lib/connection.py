"""Neo4j Database Connection Module

Provides connection management for Neo4j database operations.
"""

from typing import Optional, Dict, Any, List
from neo4j import GraphDatabase, Driver, Session, Result
import logging


class Neo4jConnection:
    """Manages Neo4j database connections and provides session handling."""
    
    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        """Initialize Neo4j connection.
        
        Args:
            uri: Neo4j database URI (e.g., "bolt://localhost:7687")
            username: Database username
            password: Database password
            database: Database name (default: "neo4j")
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self._driver: Optional[Driver] = None
        self.logger = logging.getLogger(__name__)
        
        # Initialize connection
        self._connect()
    
    def _connect(self) -> None:
        """Establish connection to Neo4j database."""
        try:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            # Test connection
            self._driver.verify_connectivity()
            self.logger.info(f"Successfully connected to Neo4j at {self.uri}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Neo4j: {e}")
            raise ConnectionError(f"Could not connect to Neo4j database: {e}")
    
    def get_session(self) -> Session:
        """Get a new database session.
        
        Returns:
            Neo4j session object
        """
        if not self._driver:
            raise RuntimeError("Database connection not established")
        
        return self._driver.session(database=self.database)
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results.
        
        Args:
            query: Cypher query string
            parameters: Query parameters (optional)
        
        Returns:
            List of result records as dictionaries
        """
        if parameters is None:
            parameters = {}
        
        with self.get_session() as session:
            try:
                result = session.run(query, parameters)
                return [record.data() for record in result]
            except Exception as e:
                self.logger.error(f"Query execution failed: {e}")
                self.logger.error(f"Query: {query}")
                self.logger.error(f"Parameters: {parameters}")
                raise
    
    def execute_write_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a write query in a transaction.
        
        Args:
            query: Cypher query string
            parameters: Query parameters (optional)
        
        Returns:
            List of result records as dictionaries
        """
        if parameters is None:
            parameters = {}
        
        def _execute_write(tx):
            result = tx.run(query, parameters)
            return [record.data() for record in result]
        
        with self.get_session() as session:
            try:
                return session.execute_write(_execute_write)
            except Exception as e:
                self.logger.error(f"Write query execution failed: {e}")
                self.logger.error(f"Query: {query}")
                self.logger.error(f"Parameters: {parameters}")
                raise
    
    def execute_read_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a read query.
        
        Args:
            query: Cypher query string
            parameters: Query parameters (optional)
        
        Returns:
            List of result records as dictionaries
        """
        if parameters is None:
            parameters = {}
        
        def _execute_read(tx):
            result = tx.run(query, parameters)
            return [record.data() for record in result]
        
        with self.get_session() as session:
            try:
                return session.execute_read(_execute_read)
            except Exception as e:
                self.logger.error(f"Read query execution failed: {e}")
                self.logger.error(f"Query: {query}")
                self.logger.error(f"Parameters: {parameters}")
                raise
    
    def test_connection(self) -> bool:
        """Test database connectivity.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            if self._driver:
                self._driver.verify_connectivity()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    def close(self) -> None:
        """Close the database connection."""
        if self._driver:
            self._driver.close()
            self._driver = None
            self.logger.info("Neo4j connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()