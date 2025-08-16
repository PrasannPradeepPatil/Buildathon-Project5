#!/usr/bin/env python3
"""
Quick Vector Database Demo

A simple interactive demo to test vector database functionality with custom data.
This script allows users to:
1. Add their own documents
2. Perform similarity searches
3. See how vector databases work in practice

Requirements: pip install numpy scikit-learn
"""

import sys
import os

# Add the examples directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_vector_database_example import (
    SimpleDocument, SimpleVectorEmbedder, SimpleVectorDatabase
)
import hashlib
from typing import List


def create_document_from_text(text: str, category: str = "user") -> SimpleDocument:
    """Create a SimpleDocument from text input."""
    doc_id = hashlib.md5(text.encode()).hexdigest()[:8]
    return SimpleDocument(
        id=f"user_{doc_id}",
        content=text.strip(),
        metadata={
            "category": category,
            "length": len(text),
            "source": "user_input"
        }
    )


def load_sample_data() -> List[SimpleDocument]:
    """Load some sample documents for demonstration."""
    sample_texts = [
        "Python is a versatile programming language used for web development, data science, and automation.",
        "Machine learning algorithms can learn patterns from data to make predictions and decisions.",
        "Web development involves creating websites using HTML, CSS, JavaScript, and backend technologies.",
        "Data analysis helps organizations make informed decisions by examining patterns in their data.",
        "Cloud computing provides scalable and flexible computing resources over the internet.",
        "Artificial intelligence is transforming industries by automating complex tasks and decision-making.",
        "Database management systems store and organize data for efficient retrieval and manipulation.",
        "Software engineering practices ensure code quality, maintainability, and team collaboration."
    ]
    
    documents = []
    for i, text in enumerate(sample_texts):
        doc = create_document_from_text(text, "sample")
        doc.id = f"sample_{i+1}"
        documents.append(doc)
    
    return documents


def interactive_demo():
    """Run an interactive vector database demo."""
    print("=" * 60)
    print("INTERACTIVE VECTOR DATABASE DEMO")
    print("=" * 60)
    print("This demo shows how vector databases work with similarity search.")
    print("You can add your own documents and search through them!\n")
    
    # Initialize the vector database
    embedder = SimpleVectorEmbedder(max_features=300)
    vector_db = SimpleVectorDatabase()
    
    # Load sample data
    print("Loading sample documents...")
    sample_docs = load_sample_data()
    vector_db.add_documents(sample_docs, embedder)
    
    print(f"Loaded {len(sample_docs)} sample documents.")
    print("\nSample documents:")
    for i, doc in enumerate(sample_docs[:3], 1):
        print(f"  {i}. [{doc.metadata['category']}] {doc.content[:60]}...")
    print("  ... and more\n")
    
    while True:
        print("-" * 60)
        print("Options:")
        print("1. Search documents")
        print("2. Add new document")
        print("3. Show database statistics")
        print("4. List all documents")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            search_documents(vector_db)
        elif choice == '2':
            add_new_document(vector_db, embedder)
        elif choice == '3':
            show_statistics(vector_db)
        elif choice == '4':
            list_all_documents(vector_db)
        elif choice == '5':
            print("\nThank you for trying the vector database demo!")
            break
        else:
            print("Invalid choice. Please enter 1-5.")


def search_documents(vector_db: SimpleVectorDatabase):
    """Search for similar documents."""
    print("\n" + "=" * 40)
    print("DOCUMENT SEARCH")
    print("=" * 40)
    
    query = input("Enter your search query: ").strip()
    if not query:
        print("Empty query. Returning to main menu.")
        return
    
    try:
        k = int(input("Number of results to show (default 5): ") or "5")
        k = max(1, min(k, len(vector_db.documents)))  # Clamp between 1 and total docs
    except ValueError:
        k = 5
    
    print(f"\nSearching for: '{query}'")
    print("-" * 40)
    
    results = vector_db.similarity_search(query, k=k)
    
    if results:
        print(f"Found {len(results)} results:\n")
        for i, (doc, score) in enumerate(results, 1):
            print(f"{i}. [Score: {score:.4f}] [{doc.metadata['category']}]")
            print(f"   {doc.content}")
            print(f"   ID: {doc.id}\n")
    else:
        print("No relevant results found.")
    
    input("Press Enter to continue...")


def add_new_document(vector_db: SimpleVectorDatabase, embedder: SimpleVectorEmbedder):
    """Add a new document to the database."""
    print("\n" + "=" * 40)
    print("ADD NEW DOCUMENT")
    print("=" * 40)
    
    content = input("Enter document content: ").strip()
    if not content:
        print("Empty content. Returning to main menu.")
        return
    
    category = input("Enter category (optional): ").strip() or "user"
    
    # Create new document
    new_doc = create_document_from_text(content, category)
    
    # Add to database
    try:
        vector_db.add_documents([new_doc], embedder)
        print(f"\nDocument added successfully!")
        print(f"ID: {new_doc.id}")
        print(f"Category: {new_doc.metadata['category']}")
        print(f"Length: {new_doc.metadata['length']} characters")
    except Exception as e:
        print(f"Error adding document: {e}")
    
    input("Press Enter to continue...")


def show_statistics(vector_db: SimpleVectorDatabase):
    """Show database statistics."""
    print("\n" + "=" * 40)
    print("DATABASE STATISTICS")
    print("=" * 40)
    
    stats = vector_db.get_statistics()
    
    for key, value in stats.items():
        if key == "categories" and isinstance(value, list):
            print(f"{key.replace('_', ' ').title()}: {', '.join(value)}")
        elif key == "average_content_length":
            print(f"{key.replace('_', ' ').title()}: {value:.1f} characters")
        else:
            print(f"{key.replace('_', ' ').title()}: {value}")
    
    # Category breakdown
    if len(vector_db.documents) > 0:
        print("\nDocuments by category:")
        categories = {}
        for doc in vector_db.documents:
            cat = doc.metadata.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        for category, count in sorted(categories.items()):
            print(f"  {category}: {count} documents")
    
    input("\nPress Enter to continue...")


def list_all_documents(vector_db: SimpleVectorDatabase):
    """List all documents in the database."""
    print("\n" + "=" * 40)
    print("ALL DOCUMENTS")
    print("=" * 40)
    
    if not vector_db.documents:
        print("No documents in the database.")
        input("Press Enter to continue...")
        return
    
    print(f"Total documents: {len(vector_db.documents)}\n")
    
    for i, doc in enumerate(vector_db.documents, 1):
        print(f"{i}. [{doc.metadata['category']}] {doc.id}")
        print(f"   {doc.content[:80]}{'...' if len(doc.content) > 80 else ''}")
        print(f"   Length: {doc.metadata['length']} chars\n")
        
        # Pause every 10 documents
        if i % 10 == 0 and i < len(vector_db.documents):
            cont = input(f"Showing {i}/{len(vector_db.documents)} documents. Continue? (y/n): ")
            if cont.lower().startswith('n'):
                break
            print()
    
    input("Press Enter to continue...")


def quick_demo():
    """Run a quick non-interactive demo."""
    print("=" * 60)
    print("QUICK VECTOR DATABASE DEMO")
    print("=" * 60)
    
    # Setup
    embedder = SimpleVectorEmbedder(max_features=200)
    vector_db = SimpleVectorDatabase()
    
    # Load sample data
    documents = load_sample_data()
    vector_db.add_documents(documents, embedder)
    
    print(f"\nLoaded {len(documents)} sample documents.")
    
    # Demo searches
    demo_queries = [
        "programming and software development",
        "artificial intelligence and machine learning",
        "web technologies and internet",
        "data processing and analysis"
    ]
    
    print("\nDemo searches:")
    print("-" * 40)
    
    for query in demo_queries:
        print(f"\nQuery: '{query}'")
        results = vector_db.similarity_search(query, k=2)
        
        for i, (doc, score) in enumerate(results, 1):
            print(f"  {i}. [Score: {score:.3f}] {doc.content[:60]}...")
    
    print("\n" + "=" * 60)
    print("Quick demo completed!")
    print("Run with --interactive for the full interactive experience.")
    print("=" * 60)


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1] in ['--interactive', '-i']:
            interactive_demo()
        else:
            quick_demo()
            
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user. Goodbye!")
    except ImportError as e:
        print(f"Missing required dependencies: {e}")
        print("\nPlease install required packages:")
        print("pip install numpy scikit-learn")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()