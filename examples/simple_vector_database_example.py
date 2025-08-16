#!/usr/bin/env python3
"""
Simple Vector Database Example (Lightweight Version)

This example demonstrates vector database operations using only basic dependencies:
- numpy for vector operations
- sklearn for TF-IDF vectorization and similarity calculations

No heavy ML models required - perfect for quick testing and understanding concepts.

Requirements:
    pip install numpy scikit-learn
"""

import numpy as np
import json
import os
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import hashlib


@dataclass
class SimpleDocument:
    """Represents a document with its metadata and content."""
    id: str
    content: str
    metadata: Dict[str, Any]
    vector: Optional[np.ndarray] = None


class SimpleVectorEmbedder:
    """Simple text vectorization using TF-IDF."""
    
    def __init__(self, max_features: int = 1000):
        """
        Initialize the embedder.
        
        Args:
            max_features: Maximum number of features for TF-IDF
        """
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            stop_words='english',
            lowercase=True,
            ngram_range=(1, 2)  # Include both unigrams and bigrams
        )
        self.is_fitted = False
    
    def fit_and_transform(self, texts: List[str]) -> np.ndarray:
        """
        Fit the vectorizer on texts and transform them to vectors.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            numpy array of embeddings
        """
        print(f"Fitting TF-IDF vectorizer on {len(texts)} texts...")
        vectors = self.vectorizer.fit_transform(texts).toarray()
        self.is_fitted = True
        print(f"Generated embeddings with shape: {vectors.shape}")
        return vectors
    
    def transform(self, texts: List[str]) -> np.ndarray:
        """
        Transform texts to vectors using fitted vectorizer.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            numpy array of embeddings
        """
        if not self.is_fitted:
            raise ValueError("Vectorizer must be fitted first. Use fit_and_transform().")
        
        return self.vectorizer.transform(texts).toarray()
    
    def transform_single(self, text: str) -> np.ndarray:
        """
        Transform a single text to vector.
        
        Args:
            text: Text string to embed
            
        Returns:
            numpy array embedding vector
        """
        return self.transform([text])[0]


class SimpleVectorDatabase:
    """Simple in-memory vector database with similarity search."""
    
    def __init__(self):
        """Initialize the vector database."""
        self.documents: List[SimpleDocument] = []
        self.vectors: Optional[np.ndarray] = None
        self.embedder: Optional[SimpleVectorEmbedder] = None
    
    def add_documents(self, documents: List[SimpleDocument], embedder: SimpleVectorEmbedder):
        """
        Add documents to the database and generate their embeddings.
        
        Args:
            documents: List of SimpleDocument objects
            embedder: Fitted embedder to use for vectorization
        """
        print(f"Adding {len(documents)} documents to vector database...")
        
        # Extract texts and generate embeddings
        texts = [doc.content for doc in documents]
        
        if not embedder.is_fitted:
            # Fit embedder on all texts
            vectors = embedder.fit_and_transform(texts)
        else:
            # Use pre-fitted embedder
            vectors = embedder.transform(texts)
        
        # Assign vectors to documents
        for doc, vector in zip(documents, vectors):
            doc.vector = vector
        
        # Store documents and vectors
        self.documents.extend(documents)
        self.embedder = embedder
        
        if self.vectors is None:
            self.vectors = vectors
        else:
            self.vectors = np.vstack([self.vectors, vectors])
        
        print(f"Database now contains {len(self.documents)} documents")
    
    def similarity_search(self, query: str, k: int = 5) -> List[Tuple[SimpleDocument, float]]:
        """
        Search for similar documents using cosine similarity.
        
        Args:
            query: Query text
            k: Number of top results to return
            
        Returns:
            List of tuples (document, similarity_score)
        """
        if len(self.documents) == 0:
            return []
        
        if self.embedder is None:
            raise ValueError("No embedder available. Add documents first.")
        
        print(f"Searching for: '{query}'")
        
        # Generate query vector
        query_vector = self.embedder.transform_single(query)
        query_vector = query_vector.reshape(1, -1)
        
        # Calculate similarities
        similarities = cosine_similarity(query_vector, self.vectors)[0]
        
        # Get top k results
        top_indices = np.argsort(similarities)[::-1][:k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:  # Only include positive similarities
                results.append((self.documents[idx], similarities[idx]))
        
        return results
    
    def get_document_by_id(self, doc_id: str) -> Optional[SimpleDocument]:
        """Retrieve a document by its ID."""
        for doc in self.documents:
            if doc.id == doc_id:
                return doc
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        if len(self.documents) == 0:
            return {"total_documents": 0}
        
        return {
            "total_documents": len(self.documents),
            "vector_dimension": self.vectors.shape[1] if self.vectors is not None else 0,
            "categories": list(set(doc.metadata.get("category", "unknown") for doc in self.documents)),
            "average_content_length": np.mean([len(doc.content) for doc in self.documents])
        }
    
    def save_to_file(self, filepath: str):
        """Save database to JSON file."""
        data = {
            "documents": [
                {
                    "id": doc.id,
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "vector": doc.vector.tolist() if doc.vector is not None else None
                }
                for doc in self.documents
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Database saved to {filepath}")


def create_sample_tech_documents() -> List[SimpleDocument]:
    """Create sample technology-related documents."""
    sample_data = [
        {
            "content": "Python is a high-level programming language known for its simplicity and readability. It's widely used in web development, data science, and machine learning.",
            "category": "programming",
            "topic": "python"
        },
        {
            "content": "Machine learning algorithms can automatically learn patterns from data without being explicitly programmed. Popular algorithms include linear regression, decision trees, and neural networks.",
            "category": "ai",
            "topic": "machine_learning"
        },
        {
            "content": "Databases are organized collections of data that can be easily accessed, managed, and updated. SQL databases use structured query language for data manipulation.",
            "category": "database",
            "topic": "sql"
        },
        {
            "content": "Web development involves creating websites and web applications using technologies like HTML, CSS, JavaScript, and various frameworks like React or Django.",
            "category": "web",
            "topic": "frontend"
        },
        {
            "content": "Cloud computing provides on-demand access to computing resources over the internet. Major providers include AWS, Google Cloud, and Microsoft Azure.",
            "category": "cloud",
            "topic": "infrastructure"
        },
        {
            "content": "Data science combines statistics, programming, and domain expertise to extract insights from data. It involves data collection, cleaning, analysis, and visualization.",
            "category": "data",
            "topic": "analytics"
        },
        {
            "content": "Cybersecurity protects digital systems, networks, and data from malicious attacks. It includes practices like encryption, access control, and threat monitoring.",
            "category": "security",
            "topic": "protection"
        },
        {
            "content": "Artificial intelligence enables machines to perform tasks that typically require human intelligence, such as visual perception, speech recognition, and decision-making.",
            "category": "ai",
            "topic": "general_ai"
        },
        {
            "content": "Version control systems like Git help developers track changes in code, collaborate with teams, and manage different versions of software projects.",
            "category": "tools",
            "topic": "git"
        },
        {
            "content": "API (Application Programming Interface) allows different software applications to communicate with each other. REST APIs are commonly used for web services.",
            "category": "web",
            "topic": "api"
        }
    ]
    
    documents = []
    for i, data in enumerate(sample_data):
        # Generate a simple hash-based ID
        doc_id = hashlib.md5(data["content"].encode()).hexdigest()[:8]
        
        doc = SimpleDocument(
            id=f"doc_{doc_id}",
            content=data["content"],
            metadata={
                "category": data["category"],
                "topic": data["topic"],
                "length": len(data["content"]),
                "index": i
            }
        )
        documents.append(doc)
    
    return documents


def demonstrate_simple_vector_operations():
    """Demonstrate the simple vector database operations."""
    print("=" * 70)
    print("SIMPLE VECTOR DATABASE DEMONSTRATION")
    print("=" * 70)
    
    # Step 1: Create and prepare data
    print("\n1. DATA PREPARATION")
    print("-" * 30)
    
    documents = create_sample_tech_documents()
    print(f"Created {len(documents)} sample documents")
    
    # Display sample documents
    print("\nSample documents:")
    for i, doc in enumerate(documents[:3]):
        print(f"  {i+1}. [{doc.metadata['category']}] {doc.content[:60]}...")
    
    # Step 2: Initialize database and embedder
    print("\n2. VECTORIZATION AND STORAGE")
    print("-" * 30)
    
    embedder = SimpleVectorEmbedder(max_features=500)
    vector_db = SimpleVectorDatabase()
    
    # Add documents to database (this will generate embeddings)
    vector_db.add_documents(documents, embedder)
    
    # Display database statistics
    stats = vector_db.get_statistics()
    print(f"\nDatabase Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Step 3: Perform similarity searches
    print("\n3. SIMILARITY SEARCH DEMONSTRATIONS")
    print("-" * 30)
    
    # Define test queries
    test_queries = [
        "programming languages for beginners",
        "machine learning and artificial intelligence",
        "web development frameworks",
        "data analysis and statistics",
        "computer security and protection"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nQuery {i}: '{query}'")
        print("-" * 50)
        
        results = vector_db.similarity_search(query, k=3)
        
        if results:
            for j, (doc, score) in enumerate(results, 1):
                print(f"  {j}. [Score: {score:.4f}] [{doc.metadata['category']}]")
                print(f"     {doc.content[:80]}...")
                print(f"     ID: {doc.id}")
        else:
            print("  No relevant results found.")
    
    # Step 4: Advanced operations
    print("\n4. ADVANCED OPERATIONS")
    print("-" * 30)
    
    # Category-based analysis
    print("\nDocuments by category:")
    categories = {}
    for doc in documents:
        cat = doc.metadata['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(doc)
    
    for category, docs in categories.items():
        print(f"  {category}: {len(docs)} documents")
    
    # Find similar documents to a specific document
    print("\nFinding documents similar to the first document:")
    first_doc = documents[0]
    print(f"Reference: {first_doc.content[:60]}...")
    
    similar_results = vector_db.similarity_search(first_doc.content, k=4)
    for i, (doc, score) in enumerate(similar_results[1:], 1):  # Skip the first (identical) result
        print(f"  {i}. [Score: {score:.4f}] {doc.content[:60]}...")
    
    # Save database
    db_file = "simple_vector_db.json"
    vector_db.save_to_file(db_file)
    
    # Cleanup
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"\nCleaned up temporary file: {db_file}")
    
    print("\n" + "=" * 70)
    print("SIMPLE VECTOR DATABASE DEMONSTRATION COMPLETED!")
    print("=" * 70)


def interactive_search_demo(vector_db: SimpleVectorDatabase):
    """Interactive search demonstration."""
    print("\n" + "=" * 50)
    print("INTERACTIVE SEARCH DEMO")
    print("=" * 50)
    print("Enter your search queries (type 'quit' to exit):")
    
    while True:
        try:
            query = input("\nSearch query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            results = vector_db.similarity_search(query, k=3)
            
            if results:
                print(f"\nTop {len(results)} results for '{query}':")
                for i, (doc, score) in enumerate(results, 1):
                    print(f"\n  {i}. [Score: {score:.4f}] [{doc.metadata['category']}]")
                    print(f"     {doc.content}")
            else:
                print("No relevant results found.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("\nInteractive demo ended.")


if __name__ == "__main__":
    try:
        # Run the main demonstration
        demonstrate_simple_vector_operations()
        
        # Uncomment the following lines for interactive demo
        # print("\n" + "="*50)
        # print("Setting up interactive demo...")
        # documents = create_sample_tech_documents()
        # embedder = SimpleVectorEmbedder(max_features=500)
        # vector_db = SimpleVectorDatabase()
        # vector_db.add_documents(documents, embedder)
        # interactive_search_demo(vector_db)
        
    except ImportError as e:
        print(f"Missing required dependencies: {e}")
        print("\nPlease install required packages:")
        print("pip install numpy scikit-learn")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()