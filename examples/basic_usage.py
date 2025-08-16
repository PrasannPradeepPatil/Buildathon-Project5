#!/usr/bin/env python3
"""
Basic usage example for neo4j-graph-lib.

This example demonstrates:
1. Connecting to Neo4j database
2. Creating schema (constraints and indexes)
3. Basic CRUD operations
4. Simple queries
"""

import os
from dotenv import load_dotenv
from neo4j_graph_lib import Neo4jGraphLib


def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Database connection configuration
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not all([uri, username, password]):
        print("Error: Please set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD in .env file")
        return
    
    # Initialize the library
    graph_lib = Neo4jGraphLib(uri=uri, username=username, password=password)
    
    try:
        # Test connection
        print("Testing connection...")
        if graph_lib.connection.test_connection():
            print("✓ Connected to Neo4j successfully!")
        else:
            print("✗ Failed to connect to Neo4j")
            return
        
        # Schema Management Example
        print("\n=== Schema Management ===")
        
        # Import schema classes
        from neo4j_graph_lib.schema_manager import NodeSchema, ConstraintType, IndexType
        
        # Create Person node schema
        print("Creating Person schema...")
        person_schema = NodeSchema(
            label="Person",
            properties={"id": "string", "name": "string", "age": "integer"},
            constraints=[
                {"type": ConstraintType.UNIQUE.value, "properties": ["id"]}
            ],
            indexes=[
                {"type": IndexType.BTREE.value, "properties": ["name"]}
            ]
        )
        graph_lib.schema.create_node_schema(person_schema)
        
        # Create Company node schema
        print("Creating Company schema...")
        company_schema = NodeSchema(
            label="Company",
            properties={"id": "string", "name": "string", "industry": "string"},
            constraints=[
                {"type": ConstraintType.UNIQUE.value, "properties": ["id"]}
            ],
            indexes=[
                {"type": IndexType.BTREE.value, "properties": ["name"]}
            ]
        )
        graph_lib.schema.create_node_schema(company_schema)
        
        # List constraints and indexes
        constraints = graph_lib.schema.get_constraints()
        indexes = graph_lib.schema.get_indexes()
        print(f"Constraints: {len(constraints)}")
        print(f"Indexes: {len(indexes)}")
        
        # CRUD Operations Example
        print("\n=== CRUD Operations ===")
        
        # Create nodes
        print("Creating nodes...")
        person_data = {
            "id": "p001",
            "name": "Alice Johnson",
            "age": 30,
            "email": "alice@example.com"
        }
        person_node_id = graph_lib.crud.create_node("Person", person_data)
        print(f"Created person with ID: {person_node_id}")
        
        company_data = {
            "id": "c001",
            "name": "Tech Corp",
            "industry": "Technology",
            "founded": 2010
        }
        company_node_id = graph_lib.crud.create_node("Company", company_data)
        print(f"Created company with ID: {company_node_id}")
        
        # Create relationship
        print("Creating relationship...")
        relationship_id = graph_lib.crud.create_relationship(
            person_node_id, company_node_id,
            "WORKS_FOR",
            {"position": "Software Engineer", "since": 2020}
        )
        print(f"Created relationship with ID: {relationship_id}")
        
        # Read operations
        print("\nReading data...")
        
        # Find node by properties
        found_persons = graph_lib.crud.get_nodes_by_properties("Person", {"name": "Alice Johnson"})
        print(f"Found persons: {len(found_persons)}")
        if found_persons:
            print(f"First person: {found_persons[0].properties}")
        
        # Get all nodes of a label
        all_persons = graph_lib.crud.get_nodes_by_label("Person")
        print(f"All persons: {len(all_persons)}")
        
        # Update operations
        print("\nUpdating data...")
        update_success = graph_lib.crud.update_node(
            person_node_id, 
            {"age": 31, "city": "San Francisco"}
        )
        print(f"Update successful: {update_success}")
        
        # Query Engine Example
        print("\n=== Query Engine ===")
        
        # Find neighbors
        neighbors = graph_lib.query.get_neighbors(person_node_id, depth=1, relationship_types=["WORKS_FOR"])
        print(f"Person's neighbors: {len(neighbors)}")
        if neighbors:
            print(f"First neighbor: {neighbors[0].properties}")
        
        # Search nodes
        search_results = graph_lib.query.search_nodes(
            {"age": 30}, 
            labels=["Person"]
        )
        print(f"Search results: {len(search_results)}")
        if search_results:
            print(f"First result: {search_results[0].properties}")
        
        # Get graph statistics
        stats = graph_lib.query.get_graph_statistics()
        print(f"Graph statistics: {stats}")
        
        # Custom Cypher query
        print("\nCustom query...")
        custom_result = graph_lib.connection.execute_read_query(
            "MATCH (p:Person)-[r:WORKS_FOR]->(c:Company) RETURN p.name, r.position, c.name"
        )
        print(f"Custom query result: {custom_result}")
        
        print("\n✓ Basic usage example completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Close connection
        graph_lib.connection.close()
        print("Connection closed.")


if __name__ == "__main__":
    main()