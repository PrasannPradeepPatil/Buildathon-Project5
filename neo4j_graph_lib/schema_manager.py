"""Schema Management Module

Provides functionality for creating and managing Neo4j database schemas,
including node labels, relationship types, constraints, and indexes.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging

from .connection import Neo4jConnection


class ConstraintType(Enum):
    """Types of constraints supported by Neo4j."""
    UNIQUE = "UNIQUE"
    NODE_KEY = "NODE_KEY"
    EXISTS = "EXISTS"


class IndexType(Enum):
    """Types of indexes supported by Neo4j."""
    BTREE = "BTREE"
    TEXT = "TEXT"
    POINT = "POINT"
    RANGE = "RANGE"


@dataclass
class NodeSchema:
    """Represents a node schema definition."""
    label: str
    properties: Dict[str, str]  # property_name: property_type
    constraints: List[Dict[str, Any]] = None
    indexes: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.constraints is None:
            self.constraints = []
        if self.indexes is None:
            self.indexes = []


@dataclass
class RelationshipSchema:
    """Represents a relationship schema definition."""
    type: str
    from_label: str
    to_label: str
    properties: Dict[str, str] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


class SchemaManager:
    """Manages Neo4j database schema operations."""
    
    def __init__(self, connection: Neo4jConnection):
        """Initialize schema manager.
        
        Args:
            connection: Neo4j database connection
        """
        self.connection = connection
        self.logger = logging.getLogger(__name__)
    
    def create_node_schema(self, schema: NodeSchema) -> bool:
        """Create a node schema with constraints and indexes.
        
        Args:
            schema: Node schema definition
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create constraints
            for constraint in schema.constraints:
                self._create_constraint(schema.label, constraint)
            
            # Create indexes
            for index in schema.indexes:
                self._create_index(schema.label, index)
            
            self.logger.info(f"Successfully created schema for node label: {schema.label}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to create node schema for {schema.label}: {e}")
            return False
    
    def create_relationship_schema(self, schema: RelationshipSchema) -> bool:
        """Create a relationship schema.
        
        Args:
            schema: Relationship schema definition
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # For now, we just log the relationship schema creation
            # Neo4j doesn't require explicit relationship schema creation
            self.logger.info(
                f"Relationship schema registered: {schema.from_label} -[:{schema.type}]-> {schema.to_label}"
            )
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to create relationship schema: {e}")
            return False
    
    def _create_constraint(self, label: str, constraint: Dict[str, Any]) -> None:
        """Create a constraint on a node label.
        
        Args:
            label: Node label
            constraint: Constraint definition
        """
        constraint_type = constraint.get("type")
        properties = constraint.get("properties", [])
        
        if not properties:
            raise ValueError("Constraint must specify properties")
        
        if constraint_type == ConstraintType.UNIQUE.value:
            props_str = ", ".join([f"n.{prop}" for prop in properties])
            query = f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE ({props_str}) IS UNIQUE"
        
        elif constraint_type == ConstraintType.NODE_KEY.value:
            props_str = ", ".join([f"n.{prop}" for prop in properties])
            query = f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE ({props_str}) IS NODE KEY"
        
        elif constraint_type == ConstraintType.EXISTS.value:
            # For EXISTS constraints, create one for each property
            for prop in properties:
                query = f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.{prop} IS NOT NULL"
                self.connection.execute_query(query)
            return
        
        else:
            raise ValueError(f"Unsupported constraint type: {constraint_type}")
        
        self.connection.execute_query(query)
        self.logger.info(f"Created {constraint_type} constraint on {label}({', '.join(properties)})")
    
    def _create_index(self, label: str, index: Dict[str, Any]) -> None:
        """Create an index on a node label.
        
        Args:
            label: Node label
            index: Index definition
        """
        index_type = index.get("type", IndexType.BTREE.value)
        properties = index.get("properties", [])
        name = index.get("name")
        
        if not properties:
            raise ValueError("Index must specify properties")
        
        props_str = ", ".join([f"n.{prop}" for prop in properties])
        
        if name:
            query = f"CREATE INDEX {name} IF NOT EXISTS FOR (n:{label}) ON ({props_str})"
        else:
            query = f"CREATE INDEX IF NOT EXISTS FOR (n:{label}) ON ({props_str})"
        
        self.connection.execute_query(query)
        self.logger.info(f"Created {index_type} index on {label}({', '.join(properties)})")
    
    def get_constraints(self) -> List[Dict[str, Any]]:
        """Get all constraints in the database.
        
        Returns:
            List of constraint information
        """
        query = "SHOW CONSTRAINTS"
        return self.connection.execute_read_query(query)
    
    def get_indexes(self) -> List[Dict[str, Any]]:
        """Get all indexes in the database.
        
        Returns:
            List of index information
        """
        query = "SHOW INDEXES"
        return self.connection.execute_read_query(query)
    
    def get_node_labels(self) -> List[str]:
        """Get all node labels in the database.
        
        Returns:
            List of node labels
        """
        query = "CALL db.labels()"
        result = self.connection.execute_read_query(query)
        return [record["label"] for record in result]
    
    def get_relationship_types(self) -> List[str]:
        """Get all relationship types in the database.
        
        Returns:
            List of relationship types
        """
        query = "CALL db.relationshipTypes()"
        result = self.connection.execute_read_query(query)
        return [record["relationshipType"] for record in result]
    
    def drop_constraint(self, constraint_name: str) -> bool:
        """Drop a constraint by name.
        
        Args:
            constraint_name: Name of the constraint to drop
        
        Returns:
            True if successful, False otherwise
        """
        try:
            query = f"DROP CONSTRAINT {constraint_name} IF EXISTS"
            self.connection.execute_query(query)
            self.logger.info(f"Dropped constraint: {constraint_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to drop constraint {constraint_name}: {e}")
            return False
    
    def drop_index(self, index_name: str) -> bool:
        """Drop an index by name.
        
        Args:
            index_name: Name of the index to drop
        
        Returns:
            True if successful, False otherwise
        """
        try:
            query = f"DROP INDEX {index_name} IF EXISTS"
            self.connection.execute_query(query)
            self.logger.info(f"Dropped index: {index_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to drop index {index_name}: {e}")
            return False
    
    def validate_schema(self, schemas: List[Union[NodeSchema, RelationshipSchema]]) -> Dict[str, Any]:
        """Validate schema definitions.
        
        Args:
            schemas: List of schema definitions to validate
        
        Returns:
            Validation results
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        node_labels = set()
        relationship_types = set()
        
        for schema in schemas:
            if isinstance(schema, NodeSchema):
                if schema.label in node_labels:
                    validation_results["errors"].append(
                        f"Duplicate node label: {schema.label}"
                    )
                    validation_results["valid"] = False
                node_labels.add(schema.label)
                
            elif isinstance(schema, RelationshipSchema):
                rel_key = f"{schema.from_label}-[:{schema.type}]->{schema.to_label}"
                if rel_key in relationship_types:
                    validation_results["warnings"].append(
                        f"Duplicate relationship definition: {rel_key}"
                    )
                relationship_types.add(rel_key)
        
        return validation_results
