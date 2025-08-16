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
from neo4j_graph_lib import Neo4jGraphLib


def main():
    # Database connection configuration
    # You can set these as environment variables or pass directly
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    
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
        
        # Create constraints
        print("Creating constraints...")
        graph_lib.schema.create_constraint("Person", "id", "UNIQUE")
        graph_lib.schema.create_constraint("Company", "id", "UNIQUE")
        
        # Create indexes
        print("Creating indexes...")
        graph_lib.schema.create_index("Person", ["name"])
        graph_lib.schema.create_index("Company", ["name"])
        
        # List constraints and indexes
        constraints = graph_lib.schema.list_constraints()
        indexes = graph_lib.schema.list_indexes()
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
        person_node = graph_lib.crud.create_node("Person", person_data)
        print(f"Created person: {person_node}")
        
        company_data = {
            "id": "c001",
            "name": "Tech Corp",
            "industry": "Technology",
            "founded": 2010
        }
        company_node = graph_lib.crud.create_node("Company", company_data)
        print(f"Created company: {company_node}")
        
        # Create relationship
        print("Creating relationship...")
        relationship = graph_lib.crud.create_relationship(
            person_node["id"], company_node["id"],
            "WORKS_FOR",
            {"position": "Software Engineer", "since": 2020}
        )
        print(f"Created relationship: {relationship}")
        
        # Read operations
        print("\nReading data...")
        
        # Find node by property
        found_person = graph_lib.crud.find_node_by_property("Person", "name", "Alice Johnson")
        print(f"Found person: {found_person}")
        
        # Get all nodes of a label
        all_persons = graph_lib.crud.get_nodes_by_label("Person")
        print(f"All persons: {len(all_persons)}")
        
        # Update operations
        print("\nUpdating data...")
        updated_person = graph_lib.crud.update_node(
            person_node["id"], 
            {"age": 31, "city": "San Francisco"}
        )
        print(f"Updated person: {updated_person}")
        
        # Query Engine Example
        print("\n=== Query Engine ===")
        
        # Find neighbors
        neighbors = graph_lib.query.find_neighbors(person_node["id"], "WORKS_FOR")
        print(f"Person's neighbors: {neighbors}")
        
        # Search nodes
        search_results = graph_lib.query.search_nodes(
            "Person", 
            {"age": {"$gte": 25}}
        )
        print(f"Search results: {search_results}")
        
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