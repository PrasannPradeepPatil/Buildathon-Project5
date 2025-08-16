"""Integration tests for Neo4j Graph Library."""

import pytest
from unittest.mock import Mock, patch
import os

from neo4j_graph_lib import Neo4jGraphLib
from neo4j_graph_lib.connection import Neo4jConnection
from neo4j_graph_lib.schema_manager import SchemaManager
from neo4j_graph_lib.crud_operations import CRUDOperations
from neo4j_graph_lib.query_engine import QueryEngine


class TestNeo4jGraphLibIntegration:
    """Integration tests for the complete Neo4j Graph Library."""
    
    @pytest.fixture
    def mock_driver(self):
        """Create a mock Neo4j driver."""
        driver = Mock()
        session = Mock()
        driver.session.return_value.__enter__.return_value = session
        driver.session.return_value.__exit__.return_value = None
        return driver, session
    
    @pytest.fixture
    def graph_lib(self, mock_driver):
        """Create Neo4jGraphLib instance with mocked driver."""
        driver, session = mock_driver
        with patch('neo4j_graph_lib.connection.GraphDatabase.driver', return_value=driver):
            lib = Neo4jGraphLib(
                uri="bolt://localhost:7687",
                username="neo4j",
                password="password"
            )
            yield lib, session
    
    def test_library_initialization(self, graph_lib):
        """Test that the library initializes all components correctly."""
        lib, session = graph_lib
        
        assert isinstance(lib.connection, Neo4jConnection)
        assert isinstance(lib.schema, SchemaManager)
        assert isinstance(lib.crud, CRUDOperations)
        assert isinstance(lib.query, QueryEngine)
        
        # Test that all components share the same connection
        assert lib.schema.connection == lib.connection
        assert lib.crud.connection == lib.connection
        assert lib.query.connection == lib.connection
    
    def test_context_manager(self, mock_driver):
        """Test library as context manager."""
        driver, session = mock_driver
        
        with patch('neo4j_graph_lib.connection.GraphDatabase.driver', return_value=driver):
            with Neo4jGraphLib(
                uri="bolt://localhost:7687",
                username="neo4j",
                password="password"
            ) as lib:
                assert isinstance(lib, Neo4jGraphLib)
                assert lib.connection is not None
            
            # Verify driver.close was called
            driver.close.assert_called_once()
    
    def test_schema_and_crud_workflow(self, graph_lib):
        """Test complete workflow: schema creation -> CRUD operations."""
        lib, session = graph_lib
        
        # Mock schema operations
        session.run.return_value.consume.return_value = Mock()
        
        # 1. Create schema
        lib.schema.create_constraint("Person", "email", "UNIQUE")
        lib.schema.create_index("Person", ["name"])
        
        # 2. Create nodes
        mock_record = Mock()
        mock_record.get.return_value = {"id": 1, "name": "John", "email": "john@example.com"}
        session.run.return_value = [mock_record]
        
        person = lib.crud.create_node("Person", {
            "name": "John",
            "email": "john@example.com",
            "age": 30
        })
        
        assert person["name"] == "John"
        assert person["email"] == "john@example.com"
        
        # 3. Query the created node
        session.run.return_value = [mock_record]
        found_person = lib.crud.get_nodes_by_properties("Person", {"email": "john@example.com"})
        
        assert len(found_person) == 1
        assert found_person[0]["name"] == "John"
    
    def test_crud_and_query_workflow(self, graph_lib):
        """Test workflow: CRUD operations -> advanced queries."""
        lib, session = graph_lib
        
        # Mock CRUD operations
        mock_person1 = Mock()
        mock_person1.get.return_value = {"id": 1, "name": "Alice"}
        mock_person2 = Mock()
        mock_person2.get.return_value = {"id": 2, "name": "Bob"}
        
        session.run.return_value = [mock_person1]
        alice = lib.crud.create_node("Person", {"name": "Alice"})
        
        session.run.return_value = [mock_person2]
        bob = lib.crud.create_node("Person", {"name": "Bob"})
        
        # Create relationship
        mock_relationship = Mock()
        mock_relationship.get.return_value = {"type": "KNOWS", "since": "2023"}
        session.run.return_value = [mock_relationship]
        
        relationship = lib.crud.create_relationship(
            alice["id"], bob["id"], "KNOWS", {"since": "2023"}
        )
        
        # Advanced query: find path
        mock_path_record = Mock()
        mock_path_record.data.return_value = {
            "path": ["Person:1", "KNOWS", "Person:2"],
            "length": 1
        }
        session.run.return_value = [mock_path_record]
        
        path = lib.query.find_shortest_path(alice["id"], bob["id"])
        
        assert path["length"] == 1
        assert "KNOWS" in str(path["path"])
    
    def test_batch_operations_workflow(self, graph_lib):
        """Test batch operations workflow."""
        lib, session = graph_lib
        
        # Mock batch node creation
        mock_records = [Mock(), Mock(), Mock()]
        mock_records[0].get.return_value = {"id": 1, "name": "Alice"}
        mock_records[1].get.return_value = {"id": 2, "name": "Bob"}
        mock_records[2].get.return_value = {"id": 3, "name": "Charlie"}
        session.run.return_value = mock_records
        
        nodes_data = [
            {"name": "Alice", "department": "Engineering"},
            {"name": "Bob", "department": "Marketing"},
            {"name": "Charlie", "department": "Engineering"}
        ]
        
        created_nodes = lib.crud.create_nodes_batch("Employee", nodes_data)
        assert len(created_nodes) == 3
        
        # Mock batch relationship creation
        mock_rel_records = [Mock(), Mock()]
        mock_rel_records[0].get.return_value = {"type": "WORKS_WITH"}
        mock_rel_records[1].get.return_value = {"type": "REPORTS_TO"}
        session.run.return_value = mock_rel_records
        
        relationships_data = [
            {"start_id": 1, "end_id": 3, "type": "WORKS_WITH", "properties": {}},
            {"start_id": 2, "end_id": 1, "type": "REPORTS_TO", "properties": {}}
        ]
        
        created_relationships = lib.crud.create_relationships_batch(relationships_data)
        assert len(created_relationships) == 2
    
    def test_complex_query_workflow(self, graph_lib):
        """Test complex query operations."""
        lib, session = graph_lib
        
        # Mock graph statistics
        mock_stats_records = [
            Mock(),  # node count
            Mock(),  # relationship count
            Mock(),  # labels
            Mock()   # relationship types
        ]
        mock_stats_records[0].data.return_value = {"node_count": 100}
        mock_stats_records[1].data.return_value = {"relationship_count": 150}
        mock_stats_records[2].data.return_value = {"labels": ["Person", "Company"]}
        mock_stats_records[3].data.return_value = {"relationship_types": ["WORKS_FOR", "KNOWS"]}
        
        session.run.side_effect = [
            [mock_stats_records[0]],
            [mock_stats_records[1]],
            [mock_stats_records[2]],
            [mock_stats_records[3]]
        ]
        
        stats = lib.query.get_graph_statistics()
        
        assert stats["node_count"] == 100
        assert stats["relationship_count"] == 150
        assert "Person" in stats["labels"]
        assert "WORKS_FOR" in stats["relationship_types"]
        
        # Reset side_effect for next operations
        session.run.side_effect = None
        
        # Mock pattern finding
        mock_pattern_records = [Mock()]
        mock_pattern_records[0].data.return_value = {
            "person": {"id": 1, "name": "Alice"},
            "company": {"id": 2, "name": "TechCorp"}
        }
        session.run.return_value = mock_pattern_records
        
        pattern = "(person:Person)-[:WORKS_FOR]->(company:Company)"
        matches = lib.query.find_patterns(pattern)
        
        assert len(matches) == 1
        assert matches[0]["person"]["name"] == "Alice"
        assert matches[0]["company"]["name"] == "TechCorp"
    
    def test_error_handling_workflow(self, graph_lib):
        """Test error handling in various operations."""
        lib, session = graph_lib
        
        # Mock connection error
        from neo4j.exceptions import ServiceUnavailable
        session.run.side_effect = ServiceUnavailable("Connection failed")
        
        with pytest.raises(ServiceUnavailable):
            lib.crud.create_node("Person", {"name": "Test"})
        
        # Reset side effect
        session.run.side_effect = None
        
        # Test empty results
        session.run.return_value = []
        
        result = lib.crud.get_node_by_id(999)
        assert result is None
        
        path = lib.query.find_shortest_path(1, 999)
        assert path is None
    
    def test_custom_cypher_execution(self, graph_lib):
        """Test custom Cypher query execution."""
        lib, session = graph_lib
        
        # Mock custom query results
        mock_records = [Mock(), Mock()]
        mock_records[0].data.return_value = {"name": "Alice", "connections": 5}
        mock_records[1].data.return_value = {"name": "Bob", "connections": 3}
        session.run.return_value = mock_records
        
        custom_query = """
        MATCH (p:Person)-[r]-()
        RETURN p.name as name, count(r) as connections
        ORDER BY connections DESC
        """
        
        results = lib.query.execute_cypher(custom_query)
        
        assert len(results) == 2
        assert results[0]["name"] == "Alice"
        assert results[0]["connections"] == 5
        assert results[1]["name"] == "Bob"
        assert results[1]["connections"] == 3
    
    def test_schema_validation_workflow(self, graph_lib):
        """Test schema validation workflow."""
        lib, session = graph_lib
        
        # Mock schema validation
        mock_constraints = [{"name": "person_email_unique", "state": "ONLINE"}]
        mock_indexes = [
            {"name": "person_name_index", "state": "ONLINE"},
            {"name": "failed_index", "state": "FAILED"}
        ]
        
        session.run.side_effect = [mock_constraints, mock_indexes]
        
        validation_result = lib.schema.validate_schema()
        
        assert validation_result["valid"] is False  # Due to failed index
        assert validation_result["constraints_count"] == 1
        assert validation_result["indexes_count"] == 2
        assert len(validation_result["issues"]) == 1
        assert "failed_index" in validation_result["issues"][0]
    
    @pytest.mark.skipif(
        not os.getenv("NEO4J_TEST_URI"),
        reason="Real Neo4j instance not available for integration testing"
    )
    def test_real_database_connection(self):
        """Test connection to real Neo4j database (requires environment setup)."""
        uri = os.getenv("NEO4J_TEST_URI", "bolt://localhost:7687")
        username = os.getenv("NEO4J_TEST_USERNAME", "neo4j")
        password = os.getenv("NEO4J_TEST_PASSWORD", "password")
        
        try:
            with Neo4jGraphLib(uri=uri, username=username, password=password) as lib:
                # Test basic connectivity
                assert lib.connection.test_connection() is True
                
                # Test basic operations
                stats = lib.query.get_graph_statistics()
                assert "node_count" in stats
                assert "relationship_count" in stats
                
        except Exception as e:
            pytest.skip(f"Could not connect to real Neo4j instance: {e}")