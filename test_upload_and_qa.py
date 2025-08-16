
#!/usr/bin/env python3
"""
Test script to upload a dummy text file and ask questions.
This script tests the complete workflow of the knowledge graph application.
"""

import requests
import time
import json
from pathlib import Path

# Configuration
API_BASE = "http://localhost:5000"
TEST_FILE_NAME = "test_document.txt"

# Sample content for testing
SAMPLE_CONTENT = """
Machine Learning and Artificial Intelligence

Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed. It has revolutionized many industries including healthcare, finance, and technology.

Key Concepts in Machine Learning:

1. Supervised Learning: This approach uses labeled training data to learn a mapping from inputs to outputs. Common algorithms include linear regression, decision trees, and neural networks.

2. Unsupervised Learning: This method finds hidden patterns in data without labeled examples. Clustering and dimensionality reduction are popular techniques.

3. Deep Learning: A subset of machine learning that uses neural networks with multiple layers. It has achieved remarkable success in image recognition, natural language processing, and game playing.

Programming Languages for ML:

Python is the most popular programming language for machine learning due to its extensive libraries like scikit-learn, TensorFlow, and PyTorch. R is also widely used for statistical analysis and data visualization.

Applications:
- Healthcare: Medical image analysis, drug discovery
- Finance: Fraud detection, algorithmic trading
- Technology: Recommendation systems, search engines
- Transportation: Autonomous vehicles, route optimization

The field continues to evolve rapidly with new techniques and applications emerging regularly. Understanding the fundamentals is crucial for anyone looking to work in this exciting domain.
"""

# Test questions to ask
TEST_QUESTIONS = [
    "What is machine learning?",
    "What programming languages are used for machine learning?",
    "What are the main types of machine learning?",
    "What are some applications of machine learning in healthcare?",
    "How does deep learning relate to machine learning?"
]

def create_test_file():
    """Create a test text file with sample content."""
    test_file_path = Path(TEST_FILE_NAME)
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(SAMPLE_CONTENT)
    print(f"✓ Created test file: {TEST_FILE_NAME}")
    return test_file_path

def upload_file(file_path):
    """Upload the test file to the application."""
    print(f"\n📤 Uploading {file_path.name}...")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'text/plain')}
            response = requests.post(f"{API_BASE}/ingest/upload", files=files, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Upload successful!")
            print(f"  - Chunks created: {result.get('chunks_created', 'N/A')}")
            print(f"  - Concepts extracted: {result.get('concepts_extracted', 'N/A')}")
            return True
        else:
            print(f"✗ Upload failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Upload error: {e}")
        return False

def check_stats():
    """Check application statistics."""
    print(f"\n📊 Checking application stats...")
    
    try:
        response = requests.get(f"{API_BASE}/stats", timeout=10)
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✓ Stats retrieved:")
            print(f"  - Documents: {stats.get('docs', 'N/A')}")
            print(f"  - Chunks: {stats.get('chunks', 'N/A')}")
            print(f"  - Concepts: {stats.get('concepts', 'N/A')}")
            print(f"  - Edges: {stats.get('edges', 'N/A')}")
            print(f"  - Used space: {stats.get('used_mb', 'N/A')}MB / {stats.get('budget_mb', 'N/A')}MB")
            return True
        else:
            print(f"✗ Stats check failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Stats error: {e}")
        return False

def check_graph():
    """Check if graph data is available."""
    print(f"\n🔗 Checking graph data...")
    
    try:
        response = requests.get(f"{API_BASE}/graph", timeout=10)
        
        if response.status_code == 200:
            graph_data = response.json()
            nodes = graph_data.get('nodes', [])
            edges = graph_data.get('edges', [])
            print(f"✓ Graph data retrieved:")
            print(f"  - Nodes: {len(nodes)}")
            print(f"  - Edges: {len(edges)}")
            
            if nodes:
                print(f"  - Sample nodes: {[node.get('label', 'N/A') for node in nodes[:3]]}")
            return True
        else:
            print(f"✗ Graph check failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Graph error: {e}")
        return False

def ask_question(question):
    """Ask a question to the Q&A system."""
    print(f"\n❓ Asking: '{question}'")
    
    try:
        payload = {"question": question}
        response = requests.post(
            f"{API_BASE}/qa", 
            json=payload, 
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get('answer', 'No answer provided')
            sources = result.get('sources', [])
            nodes_used = result.get('nodes_used', [])
            
            print(f"✓ Answer received:")
            print(f"  Answer: {answer}")
            print(f"  Sources: {len(sources)} documents referenced")
            print(f"  Nodes used: {nodes_used}")
            return True
        else:
            print(f"✗ Question failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Question error: {e}")
        return False

def test_search(query):
    """Test the search functionality."""
    print(f"\n🔍 Searching for: '{query}'")
    
    try:
        params = {"q": query, "k": 5}
        response = requests.get(f"{API_BASE}/search", params=params, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            results = result.get('results', [])
            print(f"✓ Search results:")
            print(f"  - Found {len(results)} results")
            for i, res in enumerate(results[:2]):
                print(f"  - Result {i+1}: {res.get('text', '')[:100]}...")
            return True
        else:
            print(f"✗ Search failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Search error: {e}")
        return False

def main():
    """Run the complete test suite."""
    print("🧪 Starting Knowledge Graph Application Test")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code != 200:
            print("✗ Server health check failed. Make sure the application is running on port 5000.")
            return
    except requests.exceptions.RequestException:
        print("✗ Cannot connect to server. Make sure the application is running on port 5000.")
        return
    
    print("✓ Server is running")
    
    # Create and upload test file
    test_file_path = create_test_file()
    
    if not upload_file(test_file_path):
        print("✗ Test failed at upload stage")
        return
    
    # Wait a moment for processing
    print("\n⏳ Waiting for processing...")
    time.sleep(2)
    
    # Check stats
    check_stats()
    
    # Check graph
    check_graph()
    
    # Test search
    test_search("machine learning")
    
    # Ask test questions
    print("\n" + "=" * 50)
    print("🤖 Testing Q&A System")
    print("=" * 50)
    
    successful_questions = 0
    for question in TEST_QUESTIONS:
        if ask_question(question):
            successful_questions += 1
        time.sleep(1)  # Brief pause between questions
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary")
    print("=" * 50)
    print(f"✓ File upload: {'Success' if Path(TEST_FILE_NAME).exists() else 'Failed'}")
    print(f"✓ Q&A questions answered: {successful_questions}/{len(TEST_QUESTIONS)}")
    
    # Cleanup
    if test_file_path.exists():
        test_file_path.unlink()
        print(f"✓ Cleaned up test file: {TEST_FILE_NAME}")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    main()
