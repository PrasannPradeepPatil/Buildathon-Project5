"""Unit tests for Neo4j connection module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

from neo4j_graph_lib.connection import Neo4jConnection


class TestNeo4jConnection:
    """Test cases for Neo4jConnection class."""
    
    def test_init(self):
        """Test connection initialization."""
        connection = Neo4jConnection(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password"
        )
        
        assert connection.uri == "bolt://localhost:7687"
        assert connection.username == "neo4j"
        assert connection.password == "password"
        assert connection._driver is None
    
    @patch('neo4j_graph_lib.connection.GraphDatabase.driver')
    def test_connect_success(self, mock_driver_factory):
        """Test successful connection."""
        mock_driver = Mock()
        mock_driver_factory.return_value = mock_driver
        
        connection = Neo4jConnection("bolt://localhost:7687", "neo4j", "password")
        connection.connect()
        
        mock_driver_factory.assert_called_once_with(
            "bolt://localhost:7687",
            auth=("neo4j", "password")
        )
        assert connection._driver == mock_driver
    
    @patch('neo4j_graph_lib.connection.GraphDatabase.driver')
    def test_connect_service_unavailable(self, mock_driver_factory):
        """Test connection failure due to service unavailable."""
        mock_driver_factory.side_effect = ServiceUnavailable("Service unavailable")
        
        connection = Neo4jConnection("bolt://localhost:7687", "neo4j", "password")
        
        with pytest.raises(ServiceUnavailable):
            connection.connect()
    
    @patch('neo4j_graph_lib.connection.GraphDatabase.driver')
    def test_connect_auth_error(self, mock_driver_factory):
        """Test connection failure due to authentication error."""
        mock_driver_factory.side_effect = AuthError("Authentication failed")
        
        connection = Neo4jConnection("bolt://localhost:7687", "neo4j", "password")
        
        with pytest.raises(AuthError):
            connection.connect()
    
    def test_get_session_without_connection(self):
        """Test getting session without establishing connection first."""
        connection = Neo4jConnection("bolt://localhost:7687", "neo4j", "password")
        
        with pytest.raises(RuntimeError, match="Not connected to Neo4j"):
            connection.get_session()
    
    @patch('neo4j_graph_lib.connection.GraphDatabase.driver')
    def test_get_session_success(self, mock_driver_factory):
        """Test successful session creation."""
        mock_driver = Mock()
        mock_session = Mock()
        mock_driver.session.return_value = mock_session
        mock_driver_factory.return_value = mock_driver
        
        connection = Neo4jConnection("bolt://localhost:7687", "neo4j", "password")
        connection.connect()
        
        session = connection.get_session()
        
        mock_driver.session.assert_called_once()
        assert session == mock_session
    
    @patch('neo4j_graph_lib.connection.GraphDatabase.driver')
    def test_execute_read_query(self, mock_driver_factory):
        """Test executing read query."""
        mock_driver = Mock()
        mock_session = Mock()
        mock_result = Mock()
        mock_records = [{'name': 'Alice'}, {'name': 'Bob'}]
        
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        mock_session.run.return_value = mock_result
        mock_result.data.return_value = mock_records
        mock_driver_factory.return_value = mock_driver
        
        connection = Neo4jConnection("bolt://localhost:7687", "neo4j", "password")
        connection.connect()
        
        result = connection.execute_read_query(
            "MATCH (n:Person) RETURN n.name as name",
            {"limit": 10}
        )
        
        mock_session.run.assert_called_once_with(
            "MATCH (n:Person) RETURN n.name as name",
            {"limit": 10}
        )
        assert result == mock_records
    
    @patch('neo4j_graph_lib.connection.GraphDatabase.driver')
    def test_execute_write_query(self, mock_driver_factory):
        """Test executing write query."""
        mock_driver = Mock()
        mock_session = Mock()
        mock_result = Mock()
        mock_summary = Mock()
        mock_summary.counters.nodes_created = 1
        
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        mock_session.run.return_value = mock_result
        mock_result.consume.return_value = mock_summary
        mock_driver_factory.return_value = mock_driver
        
        connection = Neo4jConnection("bolt://localhost:7687", "neo4j", "password")
        connection.connect()
        
        result = connection.execute_write_query(
            "CREATE (n:Person {name: $name}) RETURN n",
            {"name": "Alice"}
        )
        
        mock_session.run.assert_called_once_with(
            "CREATE (n:Person {name: $name}) RETURN n",
            {"name": "Alice"}
        )
        assert result == mock_summary
    
    @patch('neo4j_graph_lib.connection.GraphDatabase.driver')
    def test_test_connection_success(self, mock_driver_factory):
        """Test successful connection test."""
        mock_driver = Mock()
        mock_session = Mock()
        mock_result = Mock()
        mock_result.single.return_value = {"result": 1}
        
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        mock_session.run.return_value = mock_result
        mock_driver_factory.return_value = mock_driver
        
        connection = Neo4jConnection("bolt://localhost:7687", "neo4j", "password")
        
        result = connection.test_connection()
        
        assert result is True
        mock_session.run.assert_called_once_with("RETURN 1 as result")
    
    @patch('neo4j_graph_lib.connection.GraphDatabase.driver')
    def test_test_connection_failure(self, mock_driver_factory):
        """Test connection test failure."""
        mock_driver_factory.side_effect = ServiceUnavailable("Service unavailable")
        
        connection = Neo4jConnection("bolt://localhost:7687", "neo4j", "password")
        
        result = connection.test_connection()
        
        assert result is False
    
    @patch('neo4j_graph_lib.connection.GraphDatabase.driver')
    def test_close_connection(self, mock_driver_factory):
        """Test closing connection."""
        mock_driver = Mock()
        mock_driver_factory.return_value = mock_driver
        
        connection = Neo4jConnection("bolt://localhost:7687", "neo4j", "password")
        connection.connect()
        connection.close()
        
        mock_driver.close.assert_called_once()
        assert connection._driver is None
    
    def test_close_without_connection(self):
        """Test closing connection when not connected."""
        connection = Neo4jConnection("bolt://localhost:7687", "neo4j", "password")
        
        # Should not raise an exception
        connection.close()
        assert connection._driver is None
    
    @patch('neo4j_graph_lib.connection.GraphDatabase.driver')
    def test_context_manager(self, mock_driver_factory):
        """Test using connection as context manager."""
        mock_driver = Mock()
        mock_driver_factory.return_value = mock_driver
        
        with Neo4jConnection("bolt://localhost:7687", "neo4j", "password") as connection:
            assert connection._driver == mock_driver
        
        mock_driver.close.assert_called_once()
    
    @patch('neo4j_graph_lib.connection.GraphDatabase.driver')
    def test_execute_query_without_connection(self, mock_driver_factory):
        """Test executing query without establishing connection."""
        connection = Neo4jConnection("bolt://localhost:7687", "neo4j", "password")
        
        with pytest.raises(RuntimeError, match="Not connected to Neo4j"):
            connection.execute_read_query("RETURN 1")
        
        with pytest.raises(RuntimeError, match="Not connected to Neo4j"):
            connection.execute_write_query("CREATE (n:Test)")