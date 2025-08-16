"""Unit tests for Neo4j query engine module."""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, List, Any

from neo4j_graph_lib.query_engine import QueryEngine


class TestQueryEngine:
    """Test cases for QueryEngine class."""
    
    @pytest.fixture
    def query_engine(self, mock_connection):
        """Create QueryEngine instance with mock connection."""
        return QueryEngine(mock_connection)
    
    def test_init(self, mock_connection):
        """Test query engine initialization."""
        engine = QueryEngine(mock_connection)
        assert engine.connection == mock_connection
    
    def test_execute_cypher(self, query_engine, mock_connection):
        """Test executing custom Cypher query."""
        mock_records = [Mock(), Mock()]
        mock_records[0].data.return_value = {"name": "John", "age": 30}
        mock_records[1].data.return_value = {"name": "Jane", "age": 25}
        mock_connection.execute_read_query.return_value = mock_records
        
        query = "MATCH (n:Person) RETURN n.name as name, n.age as age"
        params = {"min_age": 18}
        result = query_engine.execute_cypher(query, params)
        
        mock_connection.execute_read_query.assert_called_once_with(query, params)
        assert len(result) == 2
        assert result[0] == {"name": "John", "age": 30}
        assert result[1] == {"name": "Jane", "age": 25}
    
    def test_execute_cypher_write(self, query_engine, mock_connection):
        """Test executing write Cypher query."""
        mock_summary = Mock()
        mock_summary.counters.nodes_created = 1
        mock_connection.execute_write_query.return_value = mock_summary
        
        query = "CREATE (n:Person {name: $name}) RETURN n"
        params = {"name": "John"}
        result = query_engine.execute_cypher(query, params, write=True)
        
        mock_connection.execute_write_query.assert_called_once_with(query, params)
        assert result == mock_summary
    
    def test_find_shortest_path(self, query_engine, mock_connection):
        """Test finding shortest path between nodes."""
        mock_record = Mock()
        mock_path_data = {
            "path": ["Person:1", "KNOWS", "Person:2", "WORKS_WITH", "Person:3"],
            "length": 2
        }
        mock_record.data.return_value = mock_path_data
        mock_connection.execute_read_query.return_value = [mock_record]
        
        result = query_engine.find_shortest_path(1, 3)
        
        expected_query = (
            "MATCH (start), (end) WHERE id(start) = $start_id AND id(end) = $end_id "
            "MATCH path = shortestPath((start)-[*]-(end)) "
            "RETURN path, length(path) as length"
        )
        mock_connection.execute_read_query.assert_called_once_with(
            expected_query, {"start_id": 1, "end_id": 3}
        )
        assert result == mock_path_data
    
    def test_find_shortest_path_with_relationship_type(self, query_engine, mock_connection):
        """Test finding shortest path with specific relationship type."""
        mock_record = Mock()
        mock_path_data = {"path": ["Person:1", "KNOWS", "Person:2"], "length": 1}
        mock_record.data.return_value = mock_path_data
        mock_connection.execute_read_query.return_value = [mock_record]
        
        result = query_engine.find_shortest_path(1, 2, relationship_type="KNOWS")
        
        expected_query = (
            "MATCH (start), (end) WHERE id(start) = $start_id AND id(end) = $end_id "
            "MATCH path = shortestPath((start)-[:KNOWS*]-(end)) "
            "RETURN path, length(path) as length"
        )
        mock_connection.execute_read_query.assert_called_once_with(
            expected_query, {"start_id": 1, "end_id": 2}
        )
        assert result == mock_path_data
    
    def test_find_shortest_path_no_path(self, query_engine, mock_connection):
        """Test finding shortest path when no path exists."""
        mock_connection.execute_read_query.return_value = []
        
        result = query_engine.find_shortest_path(1, 999)
        
        assert result is None
    
    def test_find_all_paths(self, query_engine, mock_connection):
        """Test finding all paths between nodes."""
        mock_records = [Mock(), Mock()]
        mock_records[0].data.return_value = {"path": ["Person:1", "KNOWS", "Person:2"], "length": 1}
        mock_records[1].data.return_value = {"path": ["Person:1", "WORKS_WITH", "Person:3", "KNOWS", "Person:2"], "length": 2}
        mock_connection.execute_read_query.return_value = mock_records
        
        result = query_engine.find_all_paths(1, 2, max_depth=3)
        
        expected_query = (
            "MATCH (start), (end) WHERE id(start) = $start_id AND id(end) = $end_id "
            "MATCH path = (start)-[*1..3]-(end) "
            "RETURN path, length(path) as length LIMIT $limit"
        )
        mock_connection.execute_read_query.assert_called_once_with(
            expected_query, {"start_id": 1, "end_id": 2, "limit": 100}
        )
        assert len(result) == 2
    
    def test_get_neighbors(self, query_engine, mock_connection):
        """Test getting node neighbors."""
        mock_records = [Mock(), Mock()]
        mock_records[0].get.return_value = {"id": 2, "name": "Jane"}
        mock_records[1].get.return_value = {"id": 3, "name": "Bob"}
        mock_connection.execute_read_query.return_value = mock_records
        
        result = query_engine.get_neighbors(1)
        
        expected_query = "MATCH (n)-[]-(neighbor) WHERE id(n) = $node_id RETURN DISTINCT neighbor LIMIT $limit"
        mock_connection.execute_read_query.assert_called_once_with(
            expected_query, {"node_id": 1, "limit": 100}
        )
        assert len(result) == 2
    
    def test_get_neighbors_with_depth(self, query_engine, mock_connection):
        """Test getting node neighbors with specific depth."""
        mock_records = [Mock()]
        mock_records[0].get.return_value = {"id": 4, "name": "Alice"}
        mock_connection.execute_read_query.return_value = mock_records
        
        result = query_engine.get_neighbors(1, depth=2)
        
        expected_query = "MATCH (n)-[*2]-(neighbor) WHERE id(n) = $node_id RETURN DISTINCT neighbor LIMIT $limit"
        mock_connection.execute_read_query.assert_called_once_with(
            expected_query, {"node_id": 1, "limit": 100}
        )
        assert len(result) == 1
    
    def test_traverse_graph_bfs(self, query_engine, mock_connection):
        """Test breadth-first graph traversal."""
        mock_records = [Mock(), Mock(), Mock()]
        mock_records[0].data.return_value = {"node": {"id": 1}, "depth": 0}
        mock_records[1].data.return_value = {"node": {"id": 2}, "depth": 1}
        mock_records[2].data.return_value = {"node": {"id": 3}, "depth": 1}
        mock_connection.execute_read_query.return_value = mock_records
        
        result = query_engine.traverse_graph(1, max_depth=2, algorithm="bfs")
        
        expected_query = (
            "MATCH path = (start)-[*0..2]-(node) WHERE id(start) = $start_id "
            "RETURN DISTINCT node, length(path) as depth ORDER BY depth LIMIT $limit"
        )
        mock_connection.execute_read_query.assert_called_once_with(
            expected_query, {"start_id": 1, "limit": 1000}
        )
        assert len(result) == 3
    
    def test_traverse_graph_dfs(self, query_engine, mock_connection):
        """Test depth-first graph traversal."""
        mock_records = [Mock(), Mock()]
        mock_records[0].data.return_value = {"node": {"id": 1}, "depth": 0}
        mock_records[1].data.return_value = {"node": {"id": 2}, "depth": 2}
        mock_connection.execute_read_query.return_value = mock_records
        
        result = query_engine.traverse_graph(1, max_depth=2, algorithm="dfs")
        
        expected_query = (
            "MATCH path = (start)-[*0..2]-(node) WHERE id(start) = $start_id "
            "RETURN DISTINCT node, length(path) as depth ORDER BY depth DESC LIMIT $limit"
        )
        mock_connection.execute_read_query.assert_called_once_with(
            expected_query, {"start_id": 1, "limit": 1000}
        )
        assert len(result) == 2
    
    def test_search_nodes_by_property(self, query_engine, mock_connection):
        """Test searching nodes by property value."""
        mock_records = [Mock(), Mock()]
        mock_records[0].get.return_value = {"id": 1, "name": "John Smith"}
        mock_records[1].get.return_value = {"id": 2, "name": "Jane Smith"}
        mock_connection.execute_read_query.return_value = mock_records
        
        result = query_engine.search_nodes_by_property("Person", "name", "Smith")
        
        expected_query = "MATCH (n:Person) WHERE n.name CONTAINS $value RETURN n LIMIT $limit"
        mock_connection.execute_read_query.assert_called_once_with(
            expected_query, {"value": "Smith", "limit": 100}
        )
        assert len(result) == 2
    
    def test_search_nodes_by_property_exact_match(self, query_engine, mock_connection):
        """Test searching nodes by exact property match."""
        mock_records = [Mock()]
        mock_records[0].get.return_value = {"id": 1, "name": "John"}
        mock_connection.execute_read_query.return_value = mock_records
        
        result = query_engine.search_nodes_by_property("Person", "name", "John", exact_match=True)
        
        expected_query = "MATCH (n:Person) WHERE n.name = $value RETURN n LIMIT $limit"
        mock_connection.execute_read_query.assert_called_once_with(
            expected_query, {"value": "John", "limit": 100}
        )
        assert len(result) == 1
    
    def test_get_subgraph(self, query_engine, mock_connection):
        """Test getting subgraph around nodes."""
        mock_records = [Mock(), Mock()]
        mock_records[0].data.return_value = {
            "nodes": [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}],
            "relationships": [{"id": 1, "type": "KNOWS"}]
        }
        mock_records[1].data.return_value = {
            "nodes": [{"id": 3, "name": "Bob"}],
            "relationships": [{"id": 2, "type": "WORKS_WITH"}]
        }
        mock_connection.execute_read_query.return_value = mock_records
        
        result = query_engine.get_subgraph([1, 2], depth=1)
        
        expected_query = (
            "MATCH (n)-[r*0..1]-(m) WHERE id(n) IN $node_ids "
            "RETURN collect(DISTINCT n) + collect(DISTINCT m) as nodes, "
            "collect(DISTINCT r) as relationships"
        )
        mock_connection.execute_read_query.assert_called_once_with(
            expected_query, {"node_ids": [1, 2]}
        )
        assert len(result) == 2
    
    def test_aggregate_by_property(self, query_engine, mock_connection):
        """Test aggregating nodes by property."""
        mock_records = [Mock(), Mock()]
        mock_records[0].data.return_value = {"department": "Engineering", "count": 10, "avg_salary": 75000}
        mock_records[1].data.return_value = {"department": "Marketing", "count": 5, "avg_salary": 65000}
        mock_connection.execute_read_query.return_value = mock_records
        
        result = query_engine.aggregate_by_property("Employee", "department", ["count(*)", "avg(salary)"])
        
        expected_query = (
            "MATCH (n:Employee) "
            "RETURN n.department as department, count(*) as count_all, avg(n.salary) as avg_salary "
            "ORDER BY department"
        )
        mock_connection.execute_read_query.assert_called_once_with(expected_query)
        assert len(result) == 2
    
    def test_get_graph_statistics(self, query_engine, mock_connection):
        """Test getting graph statistics."""
        mock_records = [
            Mock(),  # node count
            Mock(),  # relationship count
            Mock(),  # labels
            Mock()   # relationship types
        ]
        mock_records[0].data.return_value = {"node_count": 100}
        mock_records[1].data.return_value = {"relationship_count": 150}
        mock_records[2].data.return_value = {"labels": ["Person", "Company"]}
        mock_records[3].data.return_value = {"relationship_types": ["WORKS_FOR", "KNOWS"]}
        
        mock_connection.execute_read_query.side_effect = [
            [mock_records[0]],
            [mock_records[1]],
            [mock_records[2]],
            [mock_records[3]]
        ]
        
        result = query_engine.get_graph_statistics()
        
        expected_calls = [
            "MATCH (n) RETURN count(n) as node_count",
            "MATCH ()-[r]-() RETURN count(r) as relationship_count",
            "CALL db.labels() YIELD label RETURN collect(label) as labels",
            "CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) as relationship_types"
        ]
        
        assert mock_connection.execute_read_query.call_count == 4
        for i, call in enumerate(mock_connection.execute_read_query.call_args_list):
            assert call[0][0] == expected_calls[i]
        
        expected_result = {
            "node_count": 100,
            "relationship_count": 150,
            "labels": ["Person", "Company"],
            "relationship_types": ["WORKS_FOR", "KNOWS"]
        }
        assert result == expected_result
    
    def test_find_patterns(self, query_engine, mock_connection):
        """Test finding graph patterns."""
        mock_records = [Mock(), Mock()]
        mock_records[0].data.return_value = {"a": {"id": 1}, "b": {"id": 2}, "c": {"id": 3}}
        mock_records[1].data.return_value = {"a": {"id": 4}, "b": {"id": 5}, "c": {"id": 6}}
        mock_connection.execute_read_query.return_value = mock_records
        
        pattern = "(a:Person)-[:KNOWS]->(b:Person)-[:WORKS_FOR]->(c:Company)"
        result = query_engine.find_patterns(pattern)
        
        expected_query = f"MATCH {pattern} RETURN a, b, c LIMIT $limit"
        mock_connection.execute_read_query.assert_called_once_with(
            expected_query, {"limit": 100}
        )
        assert len(result) == 2
    
    def test_recommend_nodes(self, query_engine, mock_connection):
        """Test node recommendations based on connections."""
        mock_records = [Mock(), Mock()]
        mock_records[0].data.return_value = {"recommended": {"id": 5, "name": "Alice"}, "score": 3}
        mock_records[1].data.return_value = {"recommended": {"id": 6, "name": "Bob"}, "score": 2}
        mock_connection.execute_read_query.return_value = mock_records
        
        result = query_engine.recommend_nodes(1, "Person")
        
        expected_query = (
            "MATCH (target)-[:KNOWS]-(connected)-[:KNOWS]-(recommended:Person) "
            "WHERE id(target) = $node_id AND id(recommended) <> $node_id "
            "AND NOT (target)-[:KNOWS]-(recommended) "
            "RETURN recommended, count(*) as score "
            "ORDER BY score DESC LIMIT $limit"
        )
        mock_connection.execute_read_query.assert_called_once_with(
            expected_query, {"node_id": 1, "limit": 10}
        )
        assert len(result) == 2
        assert result[0]["score"] == 3
    
    def test_recommend_nodes_custom_relationship(self, query_engine, mock_connection):
        """Test node recommendations with custom relationship type."""
        mock_records = [Mock()]
        mock_records[0].data.return_value = {"recommended": {"id": 7, "name": "Charlie"}, "score": 1}
        mock_connection.execute_read_query.return_value = mock_records
        
        result = query_engine.recommend_nodes(1, "Person", relationship_type="WORKS_WITH")
        
        expected_query = (
            "MATCH (target)-[:WORKS_WITH]-(connected)-[:WORKS_WITH]-(recommended:Person) "
            "WHERE id(target) = $node_id AND id(recommended) <> $node_id "
            "AND NOT (target)-[:WORKS_WITH]-(recommended) "
            "RETURN recommended, count(*) as score "
            "ORDER BY score DESC LIMIT $limit"
        )
        mock_connection.execute_read_query.assert_called_once_with(
            expected_query, {"node_id": 1, "limit": 10}
        )
        assert len(result) == 1