"""Unit tests for Neo4j schema manager module."""

import pytest
from unittest.mock import Mock, MagicMock

from neo4j_graph_lib.schema_manager import SchemaManager


class TestSchemaManager:
    """Test cases for SchemaManager class."""
    
    @pytest.fixture
    def schema_manager(self, mock_connection):
        """Create SchemaManager instance with mock connection."""
        return SchemaManager(mock_connection)
    
    def test_init(self, mock_connection):
        """Test schema manager initialization."""
        manager = SchemaManager(mock_connection)
        assert manager.connection == mock_connection
    
    def test_create_unique_constraint(self, schema_manager, mock_connection):
        """Test creating unique constraint."""
        mock_summary = Mock()
        mock_connection.execute_write_query.return_value = mock_summary
        
        result = schema_manager.create_constraint("Person", "id", "UNIQUE")
        
        expected_query = "CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (n:Person) REQUIRE n.id IS UNIQUE"
        mock_connection.execute_write_query.assert_called_once_with(expected_query)
        assert result == mock_summary
    
    def test_create_node_key_constraint(self, schema_manager, mock_connection):
        """Test creating node key constraint."""
        mock_summary = Mock()
        mock_connection.execute_write_query.return_value = mock_summary
        
        result = schema_manager.create_constraint("Person", ["first_name", "last_name"], "NODE_KEY")
        
        expected_query = "CREATE CONSTRAINT person_first_name_last_name_node_key IF NOT EXISTS FOR (n:Person) REQUIRE (n.first_name, n.last_name) IS NODE KEY"
        mock_connection.execute_write_query.assert_called_once_with(expected_query)
        assert result == mock_summary
    
    def test_create_exists_constraint(self, schema_manager, mock_connection):
        """Test creating exists constraint."""
        mock_summary = Mock()
        mock_connection.execute_write_query.return_value = mock_summary
        
        result = schema_manager.create_constraint("Person", "name", "EXISTS")
        
        expected_query = "CREATE CONSTRAINT person_name_exists IF NOT EXISTS FOR (n:Person) REQUIRE n.name IS NOT NULL"
        mock_connection.execute_write_query.assert_called_once_with(expected_query)
        assert result == mock_summary
    
    def test_create_constraint_invalid_type(self, schema_manager):
        """Test creating constraint with invalid type."""
        with pytest.raises(ValueError, match="Unsupported constraint type"):
            schema_manager.create_constraint("Person", "id", "INVALID")
    
    def test_drop_constraint(self, schema_manager, mock_connection):
        """Test dropping constraint."""
        mock_summary = Mock()
        mock_connection.execute_write_query.return_value = mock_summary
        
        result = schema_manager.drop_constraint("person_id_unique")
        
        expected_query = "DROP CONSTRAINT person_id_unique IF EXISTS"
        mock_connection.execute_write_query.assert_called_once_with(expected_query)
        assert result == mock_summary
    
    def test_create_index_single_property(self, schema_manager, mock_connection):
        """Test creating index on single property."""
        mock_summary = Mock()
        mock_connection.execute_write_query.return_value = mock_summary
        
        result = schema_manager.create_index("Person", ["name"])
        
        expected_query = "CREATE INDEX person_name_index IF NOT EXISTS FOR (n:Person) ON (n.name)"
        mock_connection.execute_write_query.assert_called_once_with(expected_query)
        assert result == mock_summary
    
    def test_create_index_multiple_properties(self, schema_manager, mock_connection):
        """Test creating composite index on multiple properties."""
        mock_summary = Mock()
        mock_connection.execute_write_query.return_value = mock_summary
        
        result = schema_manager.create_index("Person", ["first_name", "last_name"])
        
        expected_query = "CREATE INDEX person_first_name_last_name_index IF NOT EXISTS FOR (n:Person) ON (n.first_name, n.last_name)"
        mock_connection.execute_write_query.assert_called_once_with(expected_query)
        assert result == mock_summary
    
    def test_create_index_with_custom_name(self, schema_manager, mock_connection):
        """Test creating index with custom name."""
        mock_summary = Mock()
        mock_connection.execute_write_query.return_value = mock_summary
        
        result = schema_manager.create_index("Person", ["email"], index_name="email_lookup")
        
        expected_query = "CREATE INDEX email_lookup IF NOT EXISTS FOR (n:Person) ON (n.email)"
        mock_connection.execute_write_query.assert_called_once_with(expected_query)
        assert result == mock_summary
    
    def test_drop_index(self, schema_manager, mock_connection):
        """Test dropping index."""
        mock_summary = Mock()
        mock_connection.execute_write_query.return_value = mock_summary
        
        result = schema_manager.drop_index("person_name_index")
        
        expected_query = "DROP INDEX person_name_index IF EXISTS"
        mock_connection.execute_write_query.assert_called_once_with(expected_query)
        assert result == mock_summary
    
    def test_list_constraints(self, schema_manager, mock_connection):
        """Test listing constraints."""
        mock_constraints = [
            {"name": "person_id_unique", "type": "UNIQUENESS", "entityType": "NODE"},
            {"name": "company_name_exists", "type": "NODE_PROPERTY_EXISTENCE", "entityType": "NODE"}
        ]
        mock_connection.execute_read_query.return_value = mock_constraints
        
        result = schema_manager.list_constraints()
        
        expected_query = "SHOW CONSTRAINTS"
        mock_connection.execute_read_query.assert_called_once_with(expected_query)
        assert result == mock_constraints
    
    def test_list_indexes(self, schema_manager, mock_connection):
        """Test listing indexes."""
        mock_indexes = [
            {"name": "person_name_index", "state": "ONLINE", "type": "BTREE"},
            {"name": "company_industry_index", "state": "ONLINE", "type": "BTREE"}
        ]
        mock_connection.execute_read_query.return_value = mock_indexes
        
        result = schema_manager.list_indexes()
        
        expected_query = "SHOW INDEXES"
        mock_connection.execute_read_query.assert_called_once_with(expected_query)
        assert result == mock_indexes
    
    def test_get_schema_info(self, schema_manager, mock_connection):
        """Test getting schema information."""
        mock_labels = [{"label": "Person"}, {"label": "Company"}]
        mock_rel_types = [{"relationshipType": "WORKS_FOR"}, {"relationshipType": "OWNS"}]
        mock_properties = [{"propertyName": "name"}, {"propertyName": "age"}]
        
        mock_connection.execute_read_query.side_effect = [
            mock_labels,
            mock_rel_types,
            mock_properties
        ]
        
        result = schema_manager.get_schema_info()
        
        expected_calls = [
            "CALL db.labels()",
            "CALL db.relationshipTypes()",
            "CALL db.propertyKeys()"
        ]
        
        assert mock_connection.execute_read_query.call_count == 3
        for i, call in enumerate(mock_connection.execute_read_query.call_args_list):
            assert call[0][0] == expected_calls[i]
        
        expected_result = {
            "labels": ["Person", "Company"],
            "relationship_types": ["WORKS_FOR", "OWNS"],
            "properties": ["name", "age"]
        }
        assert result == expected_result
    
    def test_create_node_label(self, schema_manager, mock_connection):
        """Test creating node label (implicit through node creation)."""
        mock_summary = Mock()
        mock_connection.execute_write_query.return_value = mock_summary
        
        result = schema_manager.create_node_label("NewLabel")
        
        expected_query = "CREATE (n:NewLabel {_temp: true}) DELETE n"
        mock_connection.execute_write_query.assert_called_once_with(expected_query)
        assert result == mock_summary
    
    def test_create_relationship_type(self, schema_manager, mock_connection):
        """Test creating relationship type (implicit through relationship creation)."""
        mock_summary = Mock()
        mock_connection.execute_write_query.return_value = mock_summary
        
        result = schema_manager.create_relationship_type("NEW_RELATIONSHIP")
        
        expected_query = "CREATE (a:_TempNode)-[r:NEW_RELATIONSHIP]->(b:_TempNode) DELETE a, r, b"
        mock_connection.execute_write_query.assert_called_once_with(expected_query)
        assert result == mock_summary
    
    def test_validate_schema_valid(self, schema_manager, mock_connection):
        """Test schema validation with valid schema."""
        mock_constraints = [{"name": "person_id_unique"}]
        mock_indexes = [{"name": "person_name_index", "state": "ONLINE"}]
        
        mock_connection.execute_read_query.side_effect = [mock_constraints, mock_indexes]
        
        result = schema_manager.validate_schema()
        
        assert result["valid"] is True
        assert result["constraints_count"] == 1
        assert result["indexes_count"] == 1
        assert len(result["issues"]) == 0
    
    def test_validate_schema_with_failed_indexes(self, schema_manager, mock_connection):
        """Test schema validation with failed indexes."""
        mock_constraints = [{"name": "person_id_unique"}]
        mock_indexes = [
            {"name": "person_name_index", "state": "ONLINE"},
            {"name": "failed_index", "state": "FAILED"}
        ]
        
        mock_connection.execute_read_query.side_effect = [mock_constraints, mock_indexes]
        
        result = schema_manager.validate_schema()
        
        assert result["valid"] is False
        assert result["constraints_count"] == 1
        assert result["indexes_count"] == 2
        assert len(result["issues"]) == 1
        assert "failed_index" in result["issues"][0]