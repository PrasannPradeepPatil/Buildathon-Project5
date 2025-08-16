# Neo4j Graph Library Examples

This directory contains example scripts demonstrating how to use the neo4j-graph-lib library.

## Prerequisites

Before running the examples, make sure you have:

1. **Neo4j Database**: A running Neo4j instance (local or remote)
2. **Python Dependencies**: Install the library and its dependencies
3. **Environment Variables**: Set up your Neo4j connection details

### Installation

```bash
# Install the library in development mode
pip install -e .

# Or install from requirements
pip install -r requirements.txt
```

### Environment Setup

Set the following environment variables or modify the connection details in the examples:

```bash
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="your_password"
```

## Examples

### 1. Basic Usage (`basic_usage.py`)

Demonstrates fundamental operations:
- Database connection and testing
- Schema management (constraints and indexes)
- Basic CRUD operations (Create, Read, Update, Delete)
- Simple queries and data retrieval

**Run:**
```bash
python examples/basic_usage.py
```

**What it covers:**
- Creating nodes and relationships
- Setting up constraints and indexes
- Finding nodes by properties
- Updating node properties
- Basic graph statistics

### 2. Advanced Usage (`advanced_usage.py`)

Demonstrates advanced features:
- Batch operations for performance
- Complex graph queries and traversals
- Path finding algorithms
- Pattern matching
- Graph analytics and insights

**Run:**
```bash
python examples/advanced_usage.py
```

**What it covers:**
- Batch node and relationship creation
- Multi-hop graph traversal
- Shortest path finding
- Subgraph extraction
- Aggregation queries
- Network analysis
- Collaboration patterns

## Sample Data

The examples use a sample dataset representing:
- **Persons**: Employees with skills and demographics
- **Companies**: Organizations of different sizes and industries
- **Projects**: Work projects with budgets and status
- **Skills**: Technical skills with categories

**Relationships:**
- `WORKS_FOR`: Person to Company employment
- `ASSIGNED_TO`: Person to Project assignments
- `OWNS`: Company to Project ownership
- `HAS_SKILL`: Person to Skill proficiency
- `COLLABORATES_WITH`: Person to Person collaboration

## Expected Output

### Basic Usage Output
```
Testing connection...
✓ Connected to Neo4j successfully!

=== Schema Management ===
Creating constraints...
Creating indexes...
Constraints: 2
Indexes: 2

=== CRUD Operations ===
Creating nodes...
Created person: {'id': 'p001', 'name': 'Alice Johnson', ...}
...
```

### Advanced Usage Output
```
✓ Connected to Neo4j successfully!

Setting up sample data...
Created 5 persons, 3 companies, 3 projects
Created 15 relationships

=== Advanced Queries ===
1. Path Finding:
Shortest path from Alice to AI Platform: 2 paths found
...
```

## Troubleshooting

### Connection Issues
- Ensure Neo4j is running and accessible
- Check your connection URI, username, and password
- Verify network connectivity and firewall settings

### Permission Issues
- Make sure your Neo4j user has appropriate permissions
- Check if constraints can be created (requires admin privileges)

### Data Issues
- The examples clear existing data for clean demonstrations
- Use a test database to avoid affecting production data

## Customization

You can modify the examples to:
- Use your own data models
- Connect to different Neo4j instances
- Add custom queries and analytics
- Integrate with your application logic

## Next Steps

After running the examples:
1. Explore the library's API documentation
2. Adapt the patterns to your use case
3. Build your own graph applications
4. Contribute improvements and additional examples

## Support

For questions and issues:
- Check the main README.md for library documentation
- Review the source code in `neo4j_graph_lib/`
- Open issues on the project repository