"""Query Engine Module

Provides advanced query and retrieval operations for Neo4j database,
including path finding, graph traversal, and complex queries.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from .connection import Neo4jConnection
from .crud_operations import Node, Relationship


class PathType(Enum):
    """Types of paths for path finding algorithms."""
    SHORTEST = "shortestPath"
    ALL_SHORTEST = "allShortestPaths"
    ALL_PATHS = "allPaths"


@dataclass
class QueryResult:
    """Represents a query result with metadata."""
    data: List[Dict[str, Any]]
    execution_time: Optional[float] = None
    total_records: Optional[int] = None
    query: Optional[str] = None


@dataclass
class Path:
    """Represents a path between nodes."""
    nodes: List[Node]
    relationships: List[Relationship]
    length: int
    cost: Optional[float] = None


class QueryEngine:
    """Handles advanced query operations for Neo4j database."""
    
    def __init__(self, connection: Neo4jConnection):
        """Initialize query engine.
        
        Args:
            connection: Neo4j database connection
        """
        self.connection = connection
        self.logger = logging.getLogger(__name__)
    
    def execute_cypher(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Execute a custom Cypher query.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
        
        Returns:
            QueryResult object
        """
        try:
            if parameters is None:
                parameters = {}
            
            result = self.connection.execute_read_query(query, parameters)
            
            return QueryResult(
                data=result,
                total_records=len(result),
                query=query
            )
        
        except Exception as e:
            self.logger.error(f"Failed to execute Cypher query: {e}")
            return QueryResult(data=[], total_records=0, query=query)
    
    def find_path(self, from_node_id: int, to_node_id: int, 
                  path_type: PathType = PathType.SHORTEST,
                  max_depth: Optional[int] = None,
                  relationship_types: Optional[List[str]] = None) -> List[Path]:
        """Find paths between two nodes.
        
        Args:
            from_node_id: Source node ID
            to_node_id: Target node ID
            path_type: Type of path to find
            max_depth: Maximum path depth
            relationship_types: Allowed relationship types
        
        Returns:
            List of Path objects
        """
        try:
            # Build relationship type filter
            rel_filter = ""
            if relationship_types:
                rel_types = "|".join(relationship_types)
                rel_filter = f":{rel_types}"
            
            # Build depth filter
            depth_filter = ""
            if max_depth:
                depth_filter = f"*1..{max_depth}"
            
            if path_type == PathType.SHORTEST:
                query = f"""MATCH p = shortestPath((start)-[{rel_filter}{depth_filter}]-(end))
                           WHERE id(start) = $from_id AND id(end) = $to_id
                           RETURN p, length(p) as path_length"""
            
            elif path_type == PathType.ALL_SHORTEST:
                query = f"""MATCH p = allShortestPaths((start)-[{rel_filter}{depth_filter}]-(end))
                           WHERE id(start) = $from_id AND id(end) = $to_id
                           RETURN p, length(p) as path_length"""
            
            else:  # ALL_PATHS
                query = f"""MATCH p = (start)-[{rel_filter}{depth_filter}]-(end)
                           WHERE id(start) = $from_id AND id(end) = $to_id
                           RETURN p, length(p) as path_length
                           ORDER BY path_length"""
            
            result = self.connection.execute_read_query(query, {
                "from_id": from_node_id,
                "to_id": to_node_id
            })
            
            paths = []
            for record in result:
                path_data = record["p"]
                path_length = record["path_length"]
                
                # Extract nodes and relationships from path
                nodes = []
                relationships = []
                
                # This is a simplified extraction - in practice, you'd need to
                # properly parse the Neo4j path object
                paths.append(Path(
                    nodes=nodes,
                    relationships=relationships,
                    length=path_length
                ))
            
            return paths
        
        except Exception as e:
            self.logger.error(f"Failed to find path: {e}")
            return []
    
    def get_neighbors(self, node_id: int, depth: int = 1, 
                     relationship_types: Optional[List[str]] = None,
                     direction: str = "both") -> List[Node]:
        """Get neighboring nodes at a specific depth.
        
        Args:
            node_id: Source node ID
            depth: Traversal depth
            relationship_types: Allowed relationship types
            direction: Traversal direction ("incoming", "outgoing", "both")
        
        Returns:
            List of neighboring nodes
        """
        try:
            # Build relationship type filter
            rel_filter = ""
            if relationship_types:
                rel_types = "|".join(relationship_types)
                rel_filter = f":{rel_types}"
            
            # Build direction pattern
            if direction == "outgoing":
                pattern = f"-[{rel_filter}*{depth}]->"
            elif direction == "incoming":
                pattern = f"<-[{rel_filter}*{depth}]-"
            else:  # both
                pattern = f"-[{rel_filter}*{depth}]-"
            
            query = f"""MATCH (start){pattern}(neighbor)
                       WHERE id(start) = $node_id
                       RETURN DISTINCT neighbor, id(neighbor) as neighbor_id, labels(neighbor) as labels"""
            
            result = self.connection.execute_read_query(query, {"node_id": node_id})
            
            neighbors = []
            for record in result:
                neighbors.append(Node(
                    id=record["neighbor_id"],
                    labels=record["labels"],
                    properties=dict(record["neighbor"])
                ))
            
            return neighbors
        
        except Exception as e:
            self.logger.error(f"Failed to get neighbors: {e}")
            return []
    
    def search_nodes(self, search_criteria: Dict[str, Any], 
                    labels: Optional[List[str]] = None,
                    fuzzy: bool = False,
                    limit: Optional[int] = None) -> List[Node]:
        """Search nodes based on criteria.
        
        Args:
            search_criteria: Search criteria (property: value pairs)
            labels: Node labels to search within
            fuzzy: Whether to use fuzzy matching
            limit: Maximum number of results
        
        Returns:
            List of matching nodes
        """
        try:
            # Build label filter
            label_filter = ""
            if labels:
                label_filter = ":".join(labels)
                label_filter = f":{label_filter}"
            
            # Build WHERE conditions
            where_conditions = []
            params = {}
            
            for key, value in search_criteria.items():
                if fuzzy and isinstance(value, str):
                    where_conditions.append(f"toLower(n.{key}) CONTAINS toLower(${key})")
                    params[key] = value
                else:
                    where_conditions.append(f"n.{key} = ${key}")
                    params[key] = value
            
            where_clause = " AND ".join(where_conditions)
            
            query = f"MATCH (n{label_filter}) WHERE {where_clause} RETURN n, id(n) as node_id, labels(n) as labels"
            
            if limit:
                query += f" LIMIT {limit}"
            
            result = self.connection.execute_read_query(query, params)
            
            nodes = []
            for record in result:
                nodes.append(Node(
                    id=record["node_id"],
                    labels=record["labels"],
                    properties=dict(record["n"])
                ))
            
            return nodes
        
        except Exception as e:
            self.logger.error(f"Failed to search nodes: {e}")
            return []
    
    def get_subgraph(self, center_node_id: int, radius: int = 2,
                    relationship_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get a subgraph around a center node.
        
        Args:
            center_node_id: Center node ID
            radius: Subgraph radius
            relationship_types: Allowed relationship types
        
        Returns:
            Dictionary containing nodes and relationships
        """
        try:
            # Build relationship type filter
            rel_filter = ""
            if relationship_types:
                rel_types = "|".join(relationship_types)
                rel_filter = f":{rel_types}"
            
            query = f"""MATCH (center)-[r{rel_filter}*1..{radius}]-(node)
                       WHERE id(center) = $center_id
                       RETURN DISTINCT center, node, r,
                              id(center) as center_id, id(node) as node_id,
                              labels(center) as center_labels, labels(node) as node_labels"""
            
            result = self.connection.execute_read_query(query, {"center_id": center_node_id})
            
            nodes = {}
            relationships = []
            
            # Add center node
            if result:
                center_record = result[0]
                nodes[center_node_id] = Node(
                    id=center_node_id,
                    labels=center_record["center_labels"],
                    properties=dict(center_record["center"])
                )
            
            # Process results
            for record in result:
                node_id = record["node_id"]
                if node_id not in nodes:
                    nodes[node_id] = Node(
                        id=node_id,
                        labels=record["node_labels"],
                        properties=dict(record["node"])
                    )
            
            return {
                "nodes": list(nodes.values()),
                "relationships": relationships,
                "center_node_id": center_node_id
            }
        
        except Exception as e:
            self.logger.error(f"Failed to get subgraph: {e}")
            return {"nodes": [], "relationships": [], "center_node_id": center_node_id}
    
    def aggregate_query(self, aggregation_type: str, property_name: str,
                       label: Optional[str] = None,
                       filters: Optional[Dict[str, Any]] = None) -> Optional[Union[int, float]]:
        """Perform aggregation queries.
        
        Args:
            aggregation_type: Type of aggregation ("count", "sum", "avg", "min", "max")
            property_name: Property to aggregate on
            label: Node label to filter by
            filters: Additional filters
        
        Returns:
            Aggregation result
        """
        try:
            # Build label filter
            label_filter = f":{label}" if label else ""
            
            # Build WHERE clause
            where_conditions = []
            params = {}
            
            if filters:
                for key, value in filters.items():
                    where_conditions.append(f"n.{key} = ${key}")
                    params[key] = value
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # Build aggregation function
            if aggregation_type.lower() == "count":
                agg_func = "count(n)"
            else:
                agg_func = f"{aggregation_type.lower()}(n.{property_name})"
            
            query = f"MATCH (n{label_filter}) {where_clause} RETURN {agg_func} as result"
            
            result = self.connection.execute_read_query(query, params)
            
            if result:
                return result[0]["result"]
            
            return None
        
        except Exception as e:
            self.logger.error(f"Failed to perform aggregation query: {e}")
            return None
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get basic graph statistics.
        
        Returns:
            Dictionary containing graph statistics
        """
        try:
            stats = {}
            
            # Node count
            node_count_result = self.connection.execute_read_query("MATCH (n) RETURN count(n) as node_count")
            stats["node_count"] = node_count_result[0]["node_count"] if node_count_result else 0
            
            # Relationship count
            rel_count_result = self.connection.execute_read_query("MATCH ()-[r]->() RETURN count(r) as rel_count")
            stats["relationship_count"] = rel_count_result[0]["rel_count"] if rel_count_result else 0
            
            # Label distribution
            label_result = self.connection.execute_read_query(
                "MATCH (n) RETURN labels(n) as labels, count(n) as count"
            )
            stats["label_distribution"] = {str(record["labels"]): record["count"] for record in label_result}
            
            # Relationship type distribution
            rel_type_result = self.connection.execute_read_query(
                "MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as count"
            )
            stats["relationship_type_distribution"] = {record["rel_type"]: record["count"] for record in rel_type_result}
            
            return stats
        
        except Exception as e:
            self.logger.error(f"Failed to get graph statistics: {e}")
            return {}
    
    def find_patterns(self, pattern: str, parameters: Optional[Dict[str, Any]] = None,
                     limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Find graph patterns using Cypher pattern matching.
        
        Args:
            pattern: Cypher pattern string
            parameters: Pattern parameters
            limit: Maximum number of results
        
        Returns:
            List of pattern matches
        """
        try:
            if parameters is None:
                parameters = {}
            
            query = f"MATCH {pattern} RETURN *"
            
            if limit:
                query += f" LIMIT {limit}"
            
            result = self.connection.execute_read_query(query, parameters)
            return result
        
        except Exception as e:
            self.logger.error(f"Failed to find patterns: {e}")
            return []
    
    def recommend_nodes(self, node_id: int, recommendation_type: str = "collaborative",
                       limit: int = 10) -> List[Tuple[Node, float]]:
        """Get node recommendations based on graph structure.
        
        Args:
            node_id: Source node ID
            recommendation_type: Type of recommendation algorithm
            limit: Maximum number of recommendations
        
        Returns:
            List of (Node, score) tuples
        """
        try:
            if recommendation_type == "collaborative":
                # Find nodes connected to similar nodes
                query = f"""MATCH (source)-[:SIMILAR_TO|:CONNECTED_TO]-(intermediate)-[:SIMILAR_TO|:CONNECTED_TO]-(recommendation)
                           WHERE id(source) = $node_id AND id(recommendation) <> $node_id
                           AND NOT (source)-[:SIMILAR_TO|:CONNECTED_TO]-(recommendation)
                           RETURN recommendation, id(recommendation) as rec_id, labels(recommendation) as labels,
                                  count(*) as score
                           ORDER BY score DESC
                           LIMIT {limit}"""
            
            elif recommendation_type == "content":
                # Find nodes with similar properties
                query = f"""MATCH (source), (recommendation)
                           WHERE id(source) = $node_id AND id(recommendation) <> $node_id
                           AND any(label IN labels(source) WHERE label IN labels(recommendation))
                           RETURN recommendation, id(recommendation) as rec_id, labels(recommendation) as labels,
                                  1.0 as score
                           LIMIT {limit}"""
            
            else:
                raise ValueError(f"Unsupported recommendation type: {recommendation_type}")
            
            result = self.connection.execute_read_query(query, {"node_id": node_id})
            
            recommendations = []
            for record in result:
                node = Node(
                    id=record["rec_id"],
                    labels=record["labels"],
                    properties=dict(record["recommendation"])
                )
                score = float(record["score"])
                recommendations.append((node, score))
            
            return recommendations
        
        except Exception as e:
            self.logger.error(f"Failed to get recommendations: {e}")
            return []