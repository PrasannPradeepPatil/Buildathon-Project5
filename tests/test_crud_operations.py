"""Unit tests for Neo4j CRUD operations module."""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, List, Any

from neo4j_graph_lib.crud_operations import CRUDOperations


class TestCRUDOperations:
    """Test cases for CRUDOperations class."""
    
    @pytest.fixture
    def crud_ops(self, mock_connection):
        """Create CRUDOperations instance with mock connection."""
        return CRUDOperations(mock_connection)
    
    def test_init(self, mock_connection):
        """Test CRUD operations initialization."""
        crud = CRUDOperations(mock_connection)
        assert crud.connection == mock_connection
    
    def test_create_node(self, crud_ops, mock_connection):
        """Test creating a single node."""
        mock_record = Mock()
        mock_record.get.return_value = {"id": 1, "name": "John", "age": 30}
        mock_connection.execute_write_query.return_value = [mock_record]
        
        properties = {"name": "John", "age": 30}
        result = crud_ops.create_node("Person", properties)
        
        expected_query = "CREATE (n:Person $properties) RETURN n"
        mock_connection.execute_write_query.assert_called_once_with(
            expected_query, {"properties": properties}
        )
        assert result == {"id": 1, "name": "John", "age": 30}
    
    def test_create_node_no_result(self, crud_ops, mock_connection):
        """Test creating node with no result returned."""
        mock_connection.execute_write_query.return_value = []
        
        result = crud_ops.create_node("Person", {"name": "John"})
        
        assert result is None
    
    def test_create_nodes_batch(self, crud_ops, mock_connection):
        """Test creating multiple nodes in batch."""
        mock_records = [
            Mock(),
            Mock()
        ]
        mock_records[0].get.return_value = {"id": 1, "name": "John"}
        mock_records[1].get.return_value = {"id": 2, "name": "Jane"}
        mock_connection.execute_write_query.return_value = mock_records
        
        nodes_data = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25}
        ]
        result = crud_ops.create_nodes_batch("Person", nodes_data)
        
        expected_query = "UNWIND $nodes_data AS nodeData CREATE (n:Person) SET n = nodeData RETURN n"
        mock_connection.execute_write_query.assert_called_once_with(
            expected_query, {"nodes_data": nodes_data}
        )
        assert len(result) == 2
        assert result[0] == {"id": 1, "name": "John"}
        assert result[1] == {"id": 2, "name": "Jane"}
    
    def test_get_node_by_id(self, crud_ops, mock_connection):
        """Test getting node by ID."""
        mock_record = Mock()
        mock_record.get.return_value = {"id": 1, "name": "John"}
        mock_connection.execute_read_query.return_value = [mock_record]
        
        result = crud_ops.get_node_by_id(1)
        
        expected_query = "MATCH (n) WHERE id(n) = $node_id RETURN n"
        mock_connection.execute_read_query.assert_called_once_with(
            expected_query, {"node_id": 1}
        )
        assert result == {"id": 1, "name": "John"}
    
    def test_get_node_by_id_not_found(self, crud_ops, mock_connection):
        """Test getting node by ID when not found."""
        mock_connection.execute_read_query.return_value = []
        
        result = crud_ops.get_node_by_id(999)
        
        assert result is None
    
    def test_get_nodes_by_label(self, crud_ops, mock_connection):
        """Test getting nodes by label."""
        mock_records = [Mock(), Mock()]
        mock_records[0].get.return_value = {"id": 1, "name": "John"}
        mock_records[1].get.return_value = {"id": 2, "name": "Jane"}
        mock_connection.execute_read_query.return_value = mock_records
        
        result = crud_ops.get_nodes_by_label("Person")
        
        expected_query = "MATCH (n:Person) RETURN n LIMIT $limit"
        mock_connection.execute_read_query.assert_called_once_with(
            expected_query, {"limit": 100}
        )
        assert len(result) == 2
    
    def test_get_nodes_by_properties(self, crud_ops, mock_connection):
        """Test getting nodes by properties."""
        mock_record = Mock()
        mock_record.get.return_value = {"id": 1, "name": "John", "age": 30}
        mock_connection.execute_read_query.return_value = [mock_record]
        
        properties = {"name": "John", "age": 30}
        result = crud_ops.get_nodes_by_properties("Person", properties)
        
        expected_query = "MATCH (n:Person) WHERE n.name = $name AND n.age = $age RETURN n LIMIT $limit"
        expected_params = {"name": "John", "age": 30, "limit": 100}
        mock_connection.execute_read_query.assert_called_once_with(
            expected_query, expected_params
        )
        assert len(result) == 1
    
    def test_update_node(self, crud_ops, mock_connection):
        """Test updating a node."""
        mock_record = Mock()
        mock_record.get.return_value = {"id": 1, "name": "John Updated", "age": 31}
        mock_connection.execute_write_query.return_value = [mock_record]
        
        updates = {"name": "John Updated", "age": 31}
        result = crud_ops.update_node(1, updates)
        
        expected_query = "MATCH (n) WHERE id(n) = $node_id SET n += $updates RETURN n"
        mock_connection.execute_write_query.assert_called_once_with(
            expected_query, {"node_id": 1, "updates": updates}
        )
        assert result == {"id": 1, "name": "John Updated", "age": 31}
    
    def test_update_nodes_by_properties(self, crud_ops, mock_connection):
        """Test updating multiple nodes by properties."""
        mock_summary = Mock()
        mock_summary.counters.properties_set = 2
        mock_connection.execute_write_query.return_value = mock_summary
        
        filter_props = {"department": "Engineering"}
        updates = {"salary_updated": True}
        result = crud_ops.update_nodes_by_properties("Employee", filter_props, updates)
        
        expected_query = "MATCH (n:Employee) WHERE n.department = $department SET n += $updates"
        expected_params = {"department": "Engineering", "updates": updates}
        mock_connection.execute_write_query.assert_called_once_with(
            expected_query, expected_params
        )
        assert result == mock_summary
    
    def test_delete_node(self, crud_ops, mock_connection):
        """Test deleting a node."""
        mock_summary = Mock()
        mock_summary.counters.nodes_deleted = 1
        mock_connection.execute_write_query.return_value = mock_summary
        
        result = crud_ops.delete_node(1)
        
        expected_query = "MATCH (n) WHERE id(n) = $node_id DETACH DELETE n"
        mock_connection.execute_write_query.assert_called_once_with(
            expected_query, {"node_id": 1}
        )
        assert result == mock_summary
    
    def test_delete_nodes_by_properties(self, crud_ops, mock_connection):
        """Test deleting nodes by properties."""
        mock_summary = Mock()
        mock_summary.counters.nodes_deleted = 3
        mock_connection.execute_write_query.return_value = mock_summary
        
        properties = {"status": "inactive"}
        result = crud_ops.delete_nodes_by_properties("User", properties)
        
        expected_query = "MATCH (n:User) WHERE n.status = $status DETACH DELETE n"
        mock_connection.execute_write_query.assert_called_once_with(
            expected_query, {"status": "inactive"}
        )
        assert result == mock_summary
    
    def test_create_relationship(self, crud_ops, mock_connection):
        """Test creating a relationship."""
        mock_record = Mock()
        mock_record.get.return_value = {"type": "KNOWS", "since": "2023"}
        mock_connection.execute_write_query.return_value = [mock_record]
        
        properties = {"since": "2023"}
        result = crud_ops.create_relationship(1, 2, "KNOWS", properties)
        
        expected_query = (
            "MATCH (a), (b) WHERE id(a) = $start_id AND id(b) = $end_id "
            "CREATE (a)-[r:KNOWS $properties]->(b) RETURN r"
        )
        expected_params = {"start_id": 1, "end_id": 2, "properties": properties}
        mock_connection.execute_write_query.assert_called_once_with(
            expected_query, expected_params
        )
        assert result == {"type": "KNOWS", "since": "2023"}
    
    def test_create_relationships_batch(self, crud_ops, mock_connection):
        """Test creating multiple relationships in batch."""
        mock_records = [Mock(), Mock()]
        mock_records[0].get.return_value = {"type": "KNOWS"}
        mock_records[1].get.return_value = {"type": "WORKS_WITH"}
        mock_connection.execute_write_query.return_value = mock_records
        
        relationships_data = [
            {"start_id": 1, "end_id": 2, "type": "KNOWS", "properties": {"since": "2023"}},
            {"start_id": 1, "end_id": 3, "type": "WORKS_WITH", "properties": {}}
        ]
        result = crud_ops.create_relationships_batch(relationships_data)
        
        expected_query = (
            "UNWIND $relationships_data AS relData "
            "MATCH (a), (b) WHERE id(a) = relData.start_id AND id(b) = relData.end_id "
            "CALL apoc.create.relationship(a, relData.type, relData.properties, b) YIELD rel "
            "RETURN rel"
        )
        mock_connection.execute_write_query.assert_called_once_with(
            expected_query, {"relationships_data": relationships_data}
        )
        assert len(result) == 2
    
    def test_get_relationship_by_id(self, crud_ops, mock_connection):
        """Test getting relationship by ID."""
        mock_record = Mock()
        mock_record.get.return_value = {"id": 1, "type": "KNOWS"}
        mock_connection.execute_read_query.return_value = [mock_record]
        
        result = crud_ops.get_relationship_by_id(1)
        
        expected_query = "MATCH ()-[r]-() WHERE id(r) = $rel_id RETURN r"
        mock_connection.execute_read_query.assert_called_once_with(
            expected_query, {"rel_id": 1}
        )
        assert result == {"id": 1, "type": "KNOWS"}
    
    def test_get_relationships_by_type(self, crud_ops, mock_connection):
        """Test getting relationships by type."""
        mock_records = [Mock(), Mock()]
        mock_records[0].get.return_value = {"type": "KNOWS"}
        mock_records[1].get.return_value = {"type": "KNOWS"}
        mock_connection.execute_read_query.return_value = mock_records
        
        result = crud_ops.get_relationships_by_type("KNOWS")
        
        expected_query = "MATCH ()-[r:KNOWS]-() RETURN r LIMIT $limit"
        mock_connection.execute_read_query.assert_called_once_with(
            expected_query, {"limit": 100}
        )
        assert len(result) == 2
    
    def test_get_node_relationships(self, crud_ops, mock_connection):
        """Test getting node relationships."""
        mock_records = [Mock()]
        mock_records[0].get.return_value = {"type": "KNOWS"}
        mock_connection.execute_read_query.return_value = mock_records
        
        result = crud_ops.get_node_relationships(1)
        
        expected_query = "MATCH (n)-[r]-(m) WHERE id(n) = $node_id RETURN r LIMIT $limit"
        mock_connection.execute_read_query.assert_called_once_with(
            expected_query, {"node_id": 1, "limit": 100}
        )
        assert len(result) == 1
    
    def test_get_node_relationships_outgoing(self, crud_ops, mock_connection):
        """Test getting outgoing node relationships."""
        mock_records = [Mock()]
        mock_records[0].get.return_value = {"type": "KNOWS"}
        mock_connection.execute_read_query.return_value = mock_records
        
        result = crud_ops.get_node_relationships(1, direction="outgoing")
        
        expected_query = "MATCH (n)-[r]->(m) WHERE id(n) = $node_id RETURN r LIMIT $limit"
        mock_connection.execute_read_query.assert_called_once_with(
            expected_query, {"node_id": 1, "limit": 100}
        )
        assert len(result) == 1
    
    def test_update_relationship(self, crud_ops, mock_connection):
        """Test updating a relationship."""
        mock_record = Mock()
        mock_record.get.return_value = {"id": 1, "type": "KNOWS", "strength": "strong"}
        mock_connection.execute_write_query.return_value = [mock_record]
        
        updates = {"strength": "strong"}
        result = crud_ops.update_relationship(1, updates)
        
        expected_query = "MATCH ()-[r]-() WHERE id(r) = $rel_id SET r += $updates RETURN r"
        mock_connection.execute_write_query.assert_called_once_with(
            expected_query, {"rel_id": 1, "updates": updates}
        )
        assert result == {"id": 1, "type": "KNOWS", "strength": "strong"}
    
    def test_delete_relationship(self, crud_ops, mock_connection):
        """Test deleting a relationship."""
        mock_summary = Mock()
        mock_summary.counters.relationships_deleted = 1
        mock_connection.execute_write_query.return_value = mock_summary
        
        result = crud_ops.delete_relationship(1)
        
        expected_query = "MATCH ()-[r]-() WHERE id(r) = $rel_id DELETE r"
        mock_connection.execute_write_query.assert_called_once_with(
            expected_query, {"rel_id": 1}
        )
        assert result == mock_summary
    
    def test_delete_relationships_by_type(self, crud_ops, mock_connection):
        """Test deleting relationships by type."""
        mock_summary = Mock()
        mock_summary.counters.relationships_deleted = 5
        mock_connection.execute_write_query.return_value = mock_summary
        
        result = crud_ops.delete_relationships_by_type("TEMP_RELATION")
        
        expected_query = "MATCH ()-[r:TEMP_RELATION]-() DELETE r"
        mock_connection.execute_write_query.assert_called_once_with(expected_query)
        assert result == mock_summary