# Universal Knowledge-Graph Builder

Convert a small document archive into an interactive knowledge graph with natural-language Q&A over the graph. Built with Neo4j for graph storage and semantic vector retrieval.

## Features

- **Document Ingestion**: Upload TXT files and ingest URLs (≤100MB total)
- **Neo4j Graph Storage**: Semantic graph with concepts, chunks, and co-occurrence relationships
- **Vector Search**: Native Neo4j vector indexes with hybrid keyword fallback
- **Natural Language Q&A**: Answer questions with citations and concept highlighting
- **Interactive UI**: React-based graph visualization with Cytoscape.js
- **Community Detection**: Automatic concept clustering for better organization
- **Real-time Updates**: Live graph updates as new content is ingested

## Quick Setup

### 1. Neo4j AuraDB Setup
1. Go to [Neo4j AuraDB](https://console.neo4j.io/) and create a free account
2. Create a new database instance
3. Copy the connection URI, username, and password

### 2. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your Neo4j credentials
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 4. Run the Application
```bash
python run.py
```

The application will be available at `http://localhost:5000`

## API Usage

The application exposes a FastAPI REST API:

### Upload Documents
```bash
curl -X POST -F "file=@document.txt" http://localhost:5000/ingest/upload
```

### Ingest URLs
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/article"}' \
  http://localhost:5000/ingest/url
```

### Get Graph Data
```bash
curl http://localhost:5000/graph
```

### Ask Questions
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"question":"What are the main topics?"}' \
  http://localhost:5000/qa
```

### Search Content
```bash
curl "http://localhost:5000/search?q=machine learning&k=10"
```

## API Endpoints

### Neo4jGraphLib

Main library class that provides unified access to all functionality.

```python
lib = Neo4jGraphLib(uri, user, password, database="neo4j")
```

**Properties:**
- `connection`: Neo4jConnection instance
- `schema`: SchemaManager instance
- `crud`: CRUDOperations instance
- `query`: QueryEngine instance

### Connection Management

```python
from neo4j_graph_lib import Neo4jConnection

conn = Neo4jConnection(uri, user, password)
with conn.get_session() as session:
    result = session.run("MATCH (n) RETURN count(n)")
```

### Schema Management

```python
# Create constraints
lib.schema.create_unique_constraint("Person", "email")
lib.schema.create_node_key_constraint("Product", ["sku", "version"])
lib.schema.create_exists_constraint("Order", "created_at")

# Create indexes
lib.schema.create_index("Person", "name")
lib.schema.create_index("Product", ["category", "price"], "product_category_price_idx")

# List constraints and indexes
constraints = lib.schema.list_constraints()
indexes = lib.schema.list_indexes()
```

### CRUD Operations

```python
# Create nodes
node_id = lib.crud.create_node("Person", {"name": "Bob", "age": 30})

# Create multiple nodes
node_ids = lib.crud.create_nodes("Product", [
    {"name": "Laptop", "price": 999},
    {"name": "Mouse", "price": 25}
])

# Read nodes
node = lib.crud.get_node_by_id(node_id)
nodes = lib.crud.get_nodes_by_label("Person")
filtered = lib.crud.get_nodes_by_properties("Product", {"price": 999})

# Update nodes
lib.crud.update_node(node_id, {"age": 31})

# Delete nodes
lib.crud.delete_node(node_id)

# Relationships
rel_id = lib.crud.create_relationship(person_id, product_id, "PURCHASED", {"date": "2023-12-01"})
relationships = lib.crud.get_relationships_by_type("PURCHASED")
lib.crud.delete_relationship(rel_id)
```

### Query Engine

```python
# Path finding
path = lib.query.find_shortest_path(start_id, end_id, "KNOWS")
all_paths = lib.query.find_all_paths(start_id, end_id, "KNOWS", max_depth=3)

# Graph traversal
neighbors = lib.query.get_node_neighbors(node_id, "FRIENDS", direction="both")
traversal = lib.query.traverse_graph(start_id, "FOLLOWS", max_depth=2, algorithm="bfs")

# Search and filtering
results = lib.query.search_nodes_by_property("Person", "name", "Alice", exact=False)
subgraph = lib.query.get_subgraph([node1_id, node2_id], include_relationships=True)

# Analytics
stats = lib.query.get_graph_statistics()
aggregated = lib.query.aggregate_by_property("Person", "age", "avg")

# Pattern matching
patterns = lib.query.find_patterns("(p:Person)-[:WORKS_FOR]->(c:Company)")

# Recommendations
recommendations = lib.query.recommend_nodes(node_id, "SIMILAR_TO", limit=5)

# Custom queries
result = lib.query.execute_read_query(
    "MATCH (p:Person) WHERE p.age > $age RETURN p",
    {"age": 25}
)
```

## Examples

See the `examples/` directory for comprehensive usage examples:

- `basic_usage.py`: Basic operations and getting started
- `advanced_usage.py`: Complex queries, batch operations, and analytics

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=neo4j_graph_lib

# Run specific test categories
pytest -m unit
pytest -m integration
```

### Code Quality

```bash
# Format code
black neo4j_graph_lib/
isort neo4j_graph_lib/

# Lint code
flake8 neo4j_graph_lib/
mypy neo4j_graph_lib/
```

## Configuration

### Environment Variables

```bash
# Neo4j connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j

# Testing
NEO4J_TEST_URI=bolt://localhost:7687
NEO4J_TEST_USER=neo4j
NEO4J_TEST_PASSWORD=test_password
```

### Connection Options

```python
lib = Neo4jGraphLib(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password",
    database="neo4j",
    max_connection_lifetime=3600,
    max_connection_pool_size=50,
    connection_acquisition_timeout=60
)
```

## Error Handling

The library provides comprehensive error handling:

```python
from neo4j_graph_lib.exceptions import (
    Neo4jConnectionError,
    SchemaError,
    CRUDError,
    QueryError
)

try:
    lib.crud.create_node("Person", {"email": "duplicate@example.com"})
except CRUDError as e:
    print(f"CRUD operation failed: {e}")
```

## Performance Tips

1. **Use batch operations** for creating multiple nodes/relationships
2. **Create appropriate indexes** for frequently queried properties
3. **Use parameterized queries** to avoid query plan cache pollution
4. **Limit result sets** with appropriate WHERE clauses and LIMIT statements
5. **Use connection pooling** for high-throughput applications

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Vector Database Examples

This project includes comprehensive vector database implementations that demonstrate:

### 🚀 Quick Start

```bash
# Install basic dependencies
pip install numpy scikit-learn

# Run the interactive demo
python examples/vector_demo.py --interactive

# Or run the quick demo
python examples/vector_demo.py
```

### 📚 Available Examples

1. **Simple Vector Database** (`simple_vector_database_example.py`)
   - Lightweight implementation using TF-IDF vectorization
   - In-memory storage with JSON persistence
   - Perfect for learning and small datasets
   - Dependencies: `numpy`, `scikit-learn`

2. **Advanced Vector Database** (`vector_database_example.py`)
   - Production-ready implementation with SentenceTransformers
   - FAISS integration for efficient similarity search
   - Multiple embedding methods support
   - Dependencies: `sentence-transformers`, `faiss-cpu`

3. **Interactive Demo** (`vector_demo.py`)
   - Hands-on demonstration with custom data
   - Add documents and perform searches
   - Real-time similarity search testing

### 🎯 Key Features Demonstrated

- **Vectorization**: Convert text to numerical embeddings
- **Storage**: Efficient vector storage with metadata
- **Retrieval**: Similarity search using cosine similarity
- **Persistence**: Save/load vector databases
- **Scalability**: Handle large document collections

### 📖 Documentation

See [`examples/VECTOR_DATABASE_GUIDE.md`](examples/VECTOR_DATABASE_GUIDE.md) for:
- Comprehensive concepts explanation
- Implementation details
- Performance optimization tips
- Production deployment guidance

## Support

For issues and questions:
- Create an issue on GitHub
- Check the examples directory
- Review the test files for usage patterns

## Changelog

### v1.0.0
- Initial release
- Core functionality for schema management, CRUD operations, and queries
- Comprehensive test suite
- Documentation and examples