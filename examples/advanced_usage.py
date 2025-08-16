#!/usr/bin/env python3
"""
Advanced usage example for neo4j-graph-lib.

This example demonstrates:
1. Batch operations
2. Complex graph queries
3. Path finding
4. Graph traversal
5. Pattern matching
6. Aggregation queries
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from neo4j_graph_lib import Neo4jGraphLib

# Load environment variables from .env file
load_dotenv()


def setup_sample_data(graph_lib: Neo4jGraphLib) -> None:
    """Set up sample data for advanced examples."""
    print("Setting up sample data...")
    
    # Create multiple persons
    persons = [
        {"id": "p001", "name": "Alice Johnson", "age": 30, "city": "San Francisco", "skills": ["Python", "Neo4j"]},
        {"id": "p002", "name": "Bob Smith", "age": 28, "city": "New York", "skills": ["Java", "Spring"]},
        {"id": "p003", "name": "Carol Davis", "age": 35, "city": "London", "skills": ["JavaScript", "React"]},
        {"id": "p004", "name": "David Wilson", "age": 32, "city": "Berlin", "skills": ["Python", "Django"]},
        {"id": "p005", "name": "Eva Brown", "age": 29, "city": "Tokyo", "skills": ["Go", "Kubernetes"]},
    ]
    
    # Create multiple companies
    companies = [
        {"id": "c001", "name": "Tech Corp", "industry": "Technology", "size": "Large"},
        {"id": "c002", "name": "StartupXYZ", "industry": "FinTech", "size": "Small"},
        {"id": "c003", "name": "Global Solutions", "industry": "Consulting", "size": "Medium"},
    ]
    
    # Create projects
    projects = [
        {"id": "pr001", "name": "AI Platform", "status": "Active", "budget": 500000},
        {"id": "pr002", "name": "Mobile App", "status": "Completed", "budget": 200000},
        {"id": "pr003", "name": "Data Pipeline", "status": "Planning", "budget": 300000},
    ]
    
    # Create nodes individually
    print("Creating persons...")
    for person in persons:
        graph_lib.crud.create_node("Person", person)
    
    print("Creating companies...")
    for company in companies:
        graph_lib.crud.create_node("Company", company)
    
    print("Creating projects...")
    for project in projects:
        graph_lib.crud.create_node("Project", project)
    
    # Create relationships
    relationships = [
        # Work relationships
        ("p001", "c001", "WORKS_FOR", {"position": "Senior Developer", "since": 2020}),
        ("p002", "c002", "WORKS_FOR", {"position": "Lead Developer", "since": 2021}),
        ("p003", "c001", "WORKS_FOR", {"position": "Frontend Developer", "since": 2019}),
        ("p004", "c003", "WORKS_FOR", {"position": "Backend Developer", "since": 2022}),
        ("p005", "c002", "WORKS_FOR", {"position": "DevOps Engineer", "since": 2021}),
        
        # Project assignments
        ("p001", "pr001", "ASSIGNED_TO", {"role": "Tech Lead", "allocation": 0.8}),
        ("p003", "pr001", "ASSIGNED_TO", {"role": "Frontend Lead", "allocation": 0.6}),
        ("p002", "pr002", "ASSIGNED_TO", {"role": "Project Manager", "allocation": 1.0}),
        ("p004", "pr003", "ASSIGNED_TO", {"role": "Architect", "allocation": 0.5}),
        
        # Company-project relationships
        ("c001", "pr001", "OWNS", {"investment": 500000}),
        ("c002", "pr002", "OWNS", {"investment": 200000}),
        ("c003", "pr003", "OWNS", {"investment": 300000}),
        
        # Friendship/collaboration relationships
        ("p001", "p003", "COLLABORATES_WITH", {"projects": ["pr001"]}),
        ("p002", "p005", "COLLABORATES_WITH", {"projects": ["pr002"]}),
    ]
    
    # Create relationships using node IDs
    print("Creating relationships...")
    for start_id, end_id, rel_type, properties in relationships:
        # Find start node - need to determine label based on ID prefix
        start_label = "Person" if start_id.startswith("p") else ("Company" if start_id.startswith("c") else "Project")
        end_label = "Person" if end_id.startswith("p") else ("Company" if end_id.startswith("c") else "Project")
        
        start_nodes = graph_lib.crud.get_nodes_by_properties(start_label, {"id": start_id})
        end_nodes = graph_lib.crud.get_nodes_by_properties(end_label, {"id": end_id})
        
        if start_nodes and end_nodes:
            start_node_id = start_nodes[0].id
            end_node_id = end_nodes[0].id
            graph_lib.crud.create_relationship(start_node_id, end_node_id, rel_type, properties)
        else:
            print(f"Warning: Could not find nodes for relationship {start_id} -> {end_id}")
    
    print(f"Created {len(persons)} persons, {len(companies)} companies, {len(projects)} projects")
    print(f"Created {len(relationships)} relationships")


def demonstrate_advanced_queries(graph_lib: Neo4jGraphLib) -> None:
    """Demonstrate advanced query capabilities."""
    print("\n=== Advanced Queries ===")
    
    # 1. Path finding (need to get actual node IDs first)
    print("\n1. Path Finding:")
    alice_nodes = graph_lib.crud.get_nodes_by_properties("Person", {"id": "p001"})
    project_nodes = graph_lib.crud.get_nodes_by_properties("Project", {"id": "pr001"})
    
    if alice_nodes and project_nodes:
        from neo4j_graph_lib.query_engine import PathType
        paths = graph_lib.query.find_path(
            alice_nodes[0].id, 
            project_nodes[0].id, 
            path_type=PathType.SHORTEST,
            max_depth=3
        )
        print(f"Shortest path from Alice to AI Platform: {len(paths)} paths found")
    
    # 2. Multi-hop traversal
    print("\n2. Multi-hop Traversal:")
    if alice_nodes:
        neighbors = graph_lib.query.get_neighbors(
            alice_nodes[0].id,
            depth=2,
            relationship_types=["WORKS_FOR", "OWNS"]
        )
        print(f"2-hop traversal from Alice: {len(neighbors)} nodes reached")
    
    # 3. Pattern matching using direct Cypher
    print("\n3. Pattern Matching:")
    pattern_query = "MATCH (p:Person)-[:WORKS_FOR]->(c:Company)-[:OWNS]->(pr:Project) RETURN p, c, pr"
    patterns = graph_lib.connection.execute_read_query(pattern_query)
    print(f"Person->Company->Project patterns: {len(patterns)}")
    
    # 4. Subgraph extraction
    print("\n4. Subgraph Extraction:")
    # Get actual node IDs for subgraph
    company_nodes = graph_lib.crud.get_nodes_by_properties("Company", {"id": "c001"})
    if alice_nodes and company_nodes and project_nodes:
        # Use direct Cypher for subgraph extraction
        subgraph_query = """
        MATCH (n) WHERE id(n) IN [$alice_id, $company_id, $project_id]
        OPTIONAL MATCH (n)-[r]-(m) WHERE id(m) IN [$alice_id, $company_id, $project_id]
        RETURN n, r, m
        """
        subgraph_result = graph_lib.connection.execute_read_query(subgraph_query, {
            "alice_id": alice_nodes[0].id,
            "company_id": company_nodes[0].id,
            "project_id": project_nodes[0].id
        })
        print(f"Subgraph query returned {len(subgraph_result)} records")
    
    # 5. Aggregation queries
    print("\n5. Aggregation Queries:")
    
    # Average age by company
    avg_age_query = """
    MATCH (p:Person)-[:WORKS_FOR]->(c:Company)
    RETURN c.name as company, avg(p.age) as avg_age, count(p) as employee_count
    ORDER BY avg_age DESC
    """
    avg_ages = graph_lib.connection.execute_read_query(avg_age_query)
    print("Average age by company:")
    for record in avg_ages:
        print(f"  {record['company']}: {record['avg_age']:.1f} years ({record['employee_count']} employees)")
    
    # Project budget analysis
    budget_query = """
    MATCH (c:Company)-[:OWNS]->(pr:Project)
    RETURN c.name as company, sum(pr.budget) as total_budget, count(pr) as project_count
    ORDER BY total_budget DESC
    """
    budgets = graph_lib.connection.execute_read_query(budget_query)
    print("\nProject budgets by company:")
    for record in budgets:
        print(f"  {record['company']}: ${record['total_budget']:,} ({record['project_count']} projects)")


def demonstrate_batch_operations(graph_lib: Neo4jGraphLib) -> None:
    """Demonstrate batch operations for performance."""
    print("\n=== Batch Operations ===")
    
    # Individual update example
    print("\n1. Individual Updates:")
    updates = [
        {"id": "p001", "properties": {"last_login": "2024-01-15", "status": "active"}},
        {"id": "p002", "properties": {"last_login": "2024-01-14", "status": "active"}},
        {"id": "p003", "properties": {"last_login": "2024-01-13", "status": "inactive"}},
    ]
    
    updated_count = 0
    for update in updates:
        person_nodes = graph_lib.crud.get_nodes_by_properties("Person", {"id": update["id"]})
        if person_nodes:
            success = graph_lib.crud.update_node(person_nodes[0].id, update["properties"])
            if success:
                updated_count += 1
    print(f"Updated {updated_count} person nodes")
    
    # Batch relationship creation
    print("\n2. Batch Relationship Creation:")
    skill_relationships = [
        ("p001", "skill_python", "HAS_SKILL", {"level": "expert", "years": 5}),
        ("p001", "skill_neo4j", "HAS_SKILL", {"level": "intermediate", "years": 2}),
        ("p002", "skill_java", "HAS_SKILL", {"level": "expert", "years": 6}),
        ("p003", "skill_javascript", "HAS_SKILL", {"level": "expert", "years": 4}),
    ]
    
    # First create skill nodes
    skills = [
        {"id": "skill_python", "name": "Python", "category": "Programming"},
        {"id": "skill_neo4j", "name": "Neo4j", "category": "Database"},
        {"id": "skill_java", "name": "Java", "category": "Programming"},
        {"id": "skill_javascript", "name": "JavaScript", "category": "Programming"},
    ]
    for skill in skills:
        graph_lib.crud.create_node("Skill", skill)
    
    # Create relationships individually
    rel_count = 0
    for person_id, skill_id, rel_type, properties in skill_relationships:
        person_nodes = graph_lib.crud.get_nodes_by_properties("Person", {"id": person_id})
        skill_nodes = graph_lib.crud.get_nodes_by_properties("Skill", {"id": skill_id})
        
        if person_nodes and skill_nodes:
            rel_id = graph_lib.crud.create_relationship(
                person_nodes[0].id, skill_nodes[0].id, rel_type, properties
            )
            if rel_id:
                rel_count += 1
    print(f"Created {rel_count} skill relationships")


def demonstrate_complex_analytics(graph_lib: Neo4jGraphLib) -> None:
    """Demonstrate complex analytics and insights."""
    print("\n=== Complex Analytics ===")
    
    # 1. Network analysis
    print("\n1. Network Analysis:")
    
    # Find most connected persons
    centrality_query = """
    MATCH (p:Person)
    OPTIONAL MATCH (p)-[r]-()
    RETURN p.name as person, count(r) as connections
    ORDER BY connections DESC
    LIMIT 5
    """
    centrality = graph_lib.connection.execute_read_query(centrality_query)
    print("Most connected persons:")
    for record in centrality:
        print(f"  {record['person']}: {record['connections']} connections")
    
    # 2. Skill analysis
    print("\n2. Skill Analysis:")
    skill_demand_query = """
    MATCH (p:Person)-[:HAS_SKILL]->(s:Skill)
    RETURN s.name as skill, s.category as category, count(p) as person_count
    ORDER BY person_count DESC
    """
    skill_demand = graph_lib.connection.execute_read_query(skill_demand_query)
    print("Skill demand:")
    for record in skill_demand:
        print(f"  {record['skill']} ({record['category']}): {record['person_count']} people")
    
    # 3. Project collaboration network
    print("\n3. Project Collaboration:")
    collaboration_query = """
    MATCH (p1:Person)-[:ASSIGNED_TO]->(pr:Project)<-[:ASSIGNED_TO]-(p2:Person)
    WHERE p1.id < p2.id
    RETURN p1.name as person1, p2.name as person2, pr.name as project
    """
    collaborations = graph_lib.connection.execute_read_query(collaboration_query)
    print("Project collaborations:")
    for record in collaborations:
        print(f"  {record['person1']} & {record['person2']} on {record['project']}")


def main():
    # Database connection configuration
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    
    # Check if all required environment variables are set
    if not all([uri, username, password]):
        print("Error: Please set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD environment variables")
        print("You can create a .env file with these values")
        return
    
    # Initialize the library
    graph_lib = Neo4jGraphLib(uri=uri, username=username, password=password)
    
    try:
        # Test connection
        if not graph_lib.connection.test_connection():
            print("✗ Failed to connect to Neo4j")
            return
        
        print("✓ Connected to Neo4j successfully!")
        
        # Clear existing data for clean demo
        print("\nClearing existing data...")
        graph_lib.connection.execute_write_query("MATCH (n) DETACH DELETE n")
        
        # Set up schema
        print("Setting up schema...")
        from neo4j_graph_lib.schema_manager import NodeSchema, ConstraintType
        
        # Create schemas for each node type
        person_schema = NodeSchema(
            label="Person",
            properties={"id": "string", "name": "string", "age": "integer", "city": "string"},
            constraints=[{"property": "id", "type": ConstraintType.UNIQUE}]
        )
        company_schema = NodeSchema(
            label="Company",
            properties={"id": "string", "name": "string", "industry": "string", "size": "string"},
            constraints=[{"property": "id", "type": ConstraintType.UNIQUE}]
        )
        project_schema = NodeSchema(
            label="Project",
            properties={"id": "string", "name": "string", "status": "string", "budget": "integer"},
            constraints=[{"property": "id", "type": ConstraintType.UNIQUE}]
        )
        skill_schema = NodeSchema(
            label="Skill",
            properties={"id": "string", "name": "string", "category": "string"},
            constraints=[{"property": "id", "type": ConstraintType.UNIQUE}]
        )
        
        # Apply schemas
        graph_lib.schema.create_node_schema(person_schema)
        graph_lib.schema.create_node_schema(company_schema)
        graph_lib.schema.create_node_schema(project_schema)
        graph_lib.schema.create_node_schema(skill_schema)
        
        # Set up sample data
        setup_sample_data(graph_lib)
        
        # Run demonstrations
        demonstrate_advanced_queries(graph_lib)
        demonstrate_batch_operations(graph_lib)
        demonstrate_complex_analytics(graph_lib)
        
        # Final statistics
        print("\n=== Final Statistics ===")
        stats = graph_lib.query.get_graph_statistics()
        print(f"Total nodes: {stats.get('node_count', 0)}")
        print(f"Total relationships: {stats.get('relationship_count', 0)}")
        print(f"Node labels: {', '.join(stats.get('labels', []))}")
        print(f"Relationship types: {', '.join(stats.get('relationship_types', []))}")
        
        print("\n✓ Advanced usage example completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close connection
        graph_lib.connection.close()
        print("Connection closed.")


if __name__ == "__main__":
    main()
