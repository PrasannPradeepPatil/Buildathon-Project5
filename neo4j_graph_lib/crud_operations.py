"""CRUD Operations Module

Provides Create, Read, Update, Delete operations for Neo4j nodes and relationships.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import logging

from .connection import Neo4jConnection


@dataclass
class Node:
    """Represents a Neo4j node."""
    labels: List[str]
    properties: Dict[str, Any]
    id: Optional[int] = None


@dataclass
class Relationship:
    """Represents a Neo4j relationship."""
    type: str
    properties: Dict[str, Any]
    from_node_id: Optional[int] = None
    to_node_id: Optional[int] = None
    id: Optional[int] = None


class CRUDOperations:
    """Handles CRUD operations for Neo4j database."""
    
    def __init__(self, connection: Neo4jConnection):
        """Initialize CRUD operations.
        
        Args:
            connection: Neo4j database connection
        """
        self.connection = connection
        self.logger = logging.getLogger(__name__)
    
    # Node Operations
    
    def create_node(self, labels: Union[str, List[str]], properties: Dict[str, Any]) -> Optional[int]:
        """Create a new node.
        
        Args:
            labels: Node label(s)
            properties: Node properties
        
        Returns:
            Node ID if successful, None otherwise
        """
        try:
            if isinstance(labels, str):
                labels = [labels]
            
            labels_str = ":".join(labels)
            
            # Build properties string
            props_str = ", ".join([f"{key}: ${key}" for key in properties.keys()])
            
            query = f"CREATE (n:{labels_str} {{{props_str}}}) RETURN id(n) as node_id"
            
            result = self.connection.execute_write_query(query, properties)
            
            if result:
                node_id = result[0]["node_id"]
                self.logger.info(f"Created node with ID: {node_id}")
                return node_id
            
            return None
        
        except Exception as e:
            self.logger.error(f"Failed to create node: {e}")
            return None
    
    def get_node_by_id(self, node_id: int) -> Optional[Node]:
        """Get a node by its ID.
        
        Args:
            node_id: Node ID
        
        Returns:
            Node object if found, None otherwise
        """
        try:
            query = "MATCH (n) WHERE id(n) = $node_id RETURN n, labels(n) as labels"
            result = self.connection.execute_read_query(query, {"node_id": node_id})
            
            if result:
                record = result[0]
                return Node(
                    id=node_id,
                    labels=record["labels"],
                    properties=dict(record["n"])
                )
            
            return None
        
        except Exception as e:
            self.logger.error(f"Failed to get node by ID {node_id}: {e}")
            return None
    
    def get_nodes_by_label(self, label: str, limit: Optional[int] = None) -> List[Node]:
        """Get nodes by label.
        
        Args:
            label: Node label
            limit: Maximum number of nodes to return
        
        Returns:
            List of Node objects
        """
        try:
            query = f"MATCH (n:{label}) RETURN n, id(n) as node_id, labels(n) as labels"
            
            if limit:
                query += f" LIMIT {limit}"
            
            result = self.connection.execute_read_query(query)
            
            nodes = []
            for record in result:
                nodes.append(Node(
                    id=record["node_id"],
                    labels=record["labels"],
                    properties=dict(record["n"])
                ))
            
            return nodes
        
        except Exception as e:
            self.logger.error(f"Failed to get nodes by label {label}: {e}")
            return []
    
    def get_nodes_by_properties(self, label: str, properties: Dict[str, Any], 
                               limit: Optional[int] = None) -> List[Node]:
        """Get nodes by label and properties.
        
        Args:
            label: Node label
            properties: Properties to match
            limit: Maximum number of nodes to return
        
        Returns:
            List of Node objects
        """
        try:
            # Build WHERE clause
            where_conditions = [f"n.{key} = ${key}" for key in properties.keys()]
            where_clause = " AND ".join(where_conditions)
            
            query = f"MATCH (n:{label}) WHERE {where_clause} RETURN n, id(n) as node_id, labels(n) as labels"
            
            if limit:
                query += f" LIMIT {limit}"
            
            result = self.connection.execute_read_query(query, properties)
            
            nodes = []
            for record in result:
                nodes.append(Node(
                    id=record["node_id"],
                    labels=record["labels"],
                    properties=dict(record["n"])
                ))
            
            return nodes
        
        except Exception as e:
            self.logger.error(f"Failed to get nodes by properties: {e}")
            return []
    
    def update_node(self, node_id: int, properties: Dict[str, Any]) -> bool:
        """Update a node's properties.
        
        Args:
            node_id: Node ID
            properties: Properties to update
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build SET clause
            set_clauses = [f"n.{key} = ${key}" for key in properties.keys()]
            set_clause = ", ".join(set_clauses)
            
            query = f"MATCH (n) WHERE id(n) = $node_id SET {set_clause} RETURN n"
            
            params = {"node_id": node_id, **properties}
            result = self.connection.execute_write_query(query, params)
            
            if result:
                self.logger.info(f"Updated node {node_id}")
                return True
            
            return False
        
        except Exception as e:
            self.logger.error(f"Failed to update node {node_id}: {e}")
            return False
    
    def delete_node(self, node_id: int, detach: bool = True) -> bool:
        """Delete a node.
        
        Args:
            node_id: Node ID
            detach: Whether to detach relationships before deleting
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if detach:
                query = "MATCH (n) WHERE id(n) = $node_id DETACH DELETE n"
            else:
                query = "MATCH (n) WHERE id(n) = $node_id DELETE n"
            
            self.connection.execute_write_query(query, {"node_id": node_id})
            self.logger.info(f"Deleted node {node_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to delete node {node_id}: {e}")
            return False
    
    # Relationship Operations
    
    def create_relationship(self, from_node_id: int, to_node_id: int, 
                          relationship_type: str, properties: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """Create a relationship between two nodes.
        
        Args:
            from_node_id: Source node ID
            to_node_id: Target node ID
            relationship_type: Relationship type
            properties: Relationship properties
        
        Returns:
            Relationship ID if successful, None otherwise
        """
        try:
            if properties is None:
                properties = {}
            
            if properties:
                props_str = ", ".join([f"{key}: ${key}" for key in properties.keys()])
                query = f"""MATCH (a), (b) 
                           WHERE id(a) = $from_node_id AND id(b) = $to_node_id 
                           CREATE (a)-[r:{relationship_type} {{{props_str}}}]->(b) 
                           RETURN id(r) as rel_id"""
            else:
                query = f"""MATCH (a), (b) 
                           WHERE id(a) = $from_node_id AND id(b) = $to_node_id 
                           CREATE (a)-[r:{relationship_type}]->(b) 
                           RETURN id(r) as rel_id"""
            
            params = {
                "from_node_id": from_node_id,
                "to_node_id": to_node_id,
                **properties
            }
            
            result = self.connection.execute_write_query(query, params)
            
            if result:
                rel_id = result[0]["rel_id"]
                self.logger.info(f"Created relationship with ID: {rel_id}")
                return rel_id
            
            return None
        
        except Exception as e:
            self.logger.error(f"Failed to create relationship: {e}")
            return None
    
    def get_relationship_by_id(self, rel_id: int) -> Optional[Relationship]:
        """Get a relationship by its ID.
        
        Args:
            rel_id: Relationship ID
        
        Returns:
            Relationship object if found, None otherwise
        """
        try:
            query = """MATCH (a)-[r]->(b) 
                      WHERE id(r) = $rel_id 
                      RETURN r, type(r) as rel_type, id(a) as from_id, id(b) as to_id"""
            
            result = self.connection.execute_read_query(query, {"rel_id": rel_id})
            
            if result:
                record = result[0]
                return Relationship(
                    id=rel_id,
                    type=record["rel_type"],
                    properties=dict(record["r"]),
                    from_node_id=record["from_id"],
                    to_node_id=record["to_id"]
                )
            
            return None
        
        except Exception as e:
            self.logger.error(f"Failed to get relationship by ID {rel_id}: {e}")
            return None
    
    def get_node_relationships(self, node_id: int, direction: str = "both") -> List[Relationship]:
        """Get all relationships for a node.
        
        Args:
            node_id: Node ID
            direction: Relationship direction ("incoming", "outgoing", "both")
        
        Returns:
            List of Relationship objects
        """
        try:
            if direction == "outgoing":
                query = """MATCH (n)-[r]->(m) 
                          WHERE id(n) = $node_id 
                          RETURN r, id(r) as rel_id, type(r) as rel_type, 
                                 id(n) as from_id, id(m) as to_id"""
            elif direction == "incoming":
                query = """MATCH (m)-[r]->(n) 
                          WHERE id(n) = $node_id 
                          RETURN r, id(r) as rel_id, type(r) as rel_type, 
                                 id(m) as from_id, id(n) as to_id"""
            else:  # both
                query = """MATCH (n)-[r]-(m) 
                          WHERE id(n) = $node_id 
                          RETURN r, id(r) as rel_id, type(r) as rel_type, 
                                 id(startNode(r)) as from_id, id(endNode(r)) as to_id"""
            
            result = self.connection.execute_read_query(query, {"node_id": node_id})
            
            relationships = []
            for record in result:
                relationships.append(Relationship(
                    id=record["rel_id"],
                    type=record["rel_type"],
                    properties=dict(record["r"]),
                    from_node_id=record["from_id"],
                    to_node_id=record["to_id"]
                ))
            
            return relationships
        
        except Exception as e:
            self.logger.error(f"Failed to get relationships for node {node_id}: {e}")
            return []
    
    def update_relationship(self, rel_id: int, properties: Dict[str, Any]) -> bool:
        """Update a relationship's properties.
        
        Args:
            rel_id: Relationship ID
            properties: Properties to update
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build SET clause
            set_clauses = [f"r.{key} = ${key}" for key in properties.keys()]
            set_clause = ", ".join(set_clauses)
            
            query = f"MATCH ()-[r]-() WHERE id(r) = $rel_id SET {set_clause} RETURN r"
            
            params = {"rel_id": rel_id, **properties}
            result = self.connection.execute_write_query(query, params)
            
            if result:
                self.logger.info(f"Updated relationship {rel_id}")
                return True
            
            return False
        
        except Exception as e:
            self.logger.error(f"Failed to update relationship {rel_id}: {e}")
            return False
    
    def delete_relationship(self, rel_id: int) -> bool:
        """Delete a relationship.
        
        Args:
            rel_id: Relationship ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            query = "MATCH ()-[r]-() WHERE id(r) = $rel_id DELETE r"
            self.connection.execute_write_query(query, {"rel_id": rel_id})
            self.logger.info(f"Deleted relationship {rel_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to delete relationship {rel_id}: {e}")
            return False
    
    # Batch Operations
    
    def create_nodes_batch(self, nodes_data: List[Dict[str, Any]]) -> List[int]:
        """Create multiple nodes in a batch.
        
        Args:
            nodes_data: List of node data dictionaries with 'labels' and 'properties' keys
        
        Returns:
            List of created node IDs
        """
        try:
            node_ids = []
            
            for node_data in nodes_data:
                labels = node_data.get("labels", [])
                properties = node_data.get("properties", {})
                
                node_id = self.create_node(labels, properties)
                if node_id:
                    node_ids.append(node_id)
            
            self.logger.info(f"Created {len(node_ids)} nodes in batch")
            return node_ids
        
        except Exception as e:
            self.logger.error(f"Failed to create nodes in batch: {e}")
            return []
    
    def delete_nodes_by_label(self, label: str, detach: bool = True) -> int:
        """Delete all nodes with a specific label.
        
        Args:
            label: Node label
            detach: Whether to detach relationships before deleting
        
        Returns:
            Number of deleted nodes
        """
        try:
            if detach:
                query = f"MATCH (n:{label}) DETACH DELETE n RETURN count(n) as deleted_count"
            else:
                query = f"MATCH (n:{label}) DELETE n RETURN count(n) as deleted_count"
            
            result = self.connection.execute_write_query(query)
            
            if result:
                deleted_count = result[0]["deleted_count"]
                self.logger.info(f"Deleted {deleted_count} nodes with label {label}")
                return deleted_count
            
            return 0
        
        except Exception as e:
            self.logger.error(f"Failed to delete nodes by label {label}: {e}")
            return 0
