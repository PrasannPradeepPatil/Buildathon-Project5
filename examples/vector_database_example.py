#!/usr/bin/env python3
"""
Comprehensive Vector Database Example

This example demonstrates the complete process of:
1. Vectorization: Converting raw data into numerical vector embeddings
2. Storage: Inserting vector embeddings into a vector database
3. Retrieval: Performing similarity searches to retrieve relevant data

Requirements:
    pip install numpy scikit-learn sentence-transformers faiss-cpu
"""

import numpy as np
import json
import os
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import faiss


@dataclass
class Document:
    """Represents a document with its metadata and content."""
    id: str
    content: str
    metadata: Dict[str, Any]
    vector: Optional[np.ndarray] = None


class VectorEmbedder:
    """Handles the vectorization of different types of data."""
    
    def __init__(self, method: str = "sentence_transformer"):
        """
        Initialize the embedder with the specified method.
        
        Args:
            method: Embedding method ('sentence_transformer', 'tfidf', 'custom')
        """
        self.method = method
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the embedding model based on the selected method."""
        if self.method == "sentence_transformer":
            # Using a pre-trained sentence transformer model
            print("Loading SentenceTransformer model...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            print("Model loaded successfully!")
        elif self.method == "tfidf":
            # Using TF-IDF vectorization
            self.model = TfidfVectorizer(max_features=1000, stop_words='english')
        else:
            raise ValueError(f"Unsupported embedding method: {self.method}")
    
    def embed_text(self, texts: List[str]) -> np.ndarray:
        """
        Convert text data into vector embeddings.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            numpy array of embeddings with shape (n_texts, embedding_dim)
        """
        print(f"Embedding {len(texts)} texts using {self.method}...")
        
        if self.method == "sentence_transformer":
            # Generate embeddings using sentence transformer
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            
        elif self.method == "tfidf":
            # Generate TF-IDF vectors
            embeddings = self.model.fit_transform(texts).toarray()
            
        print(f"Generated embeddings with shape: {embeddings.shape}")
        return embeddings
    
    def embed_single_text(self, text: str) -> np.ndarray:
        """
        Embed a single text string.
        
        Args:
            text: Text string to embed
            
        Returns:
            numpy array embedding vector
        """
        if self.method == "sentence_transformer":
            return self.model.encode([text], convert_to_numpy=True)[0]
        elif self.method == "tfidf":
            # For TF-IDF, we need to transform using the fitted model
            return self.model.transform([text]).toarray()[0]


class VectorDatabase:
    """Simple vector database implementation with similarity search capabilities."""
    
    def __init__(self, dimension: int, use_faiss: bool = True):
        """
        Initialize the vector database.
        
        Args:
            dimension: Dimension of the vector embeddings
            use_faiss: Whether to use FAISS for efficient similarity search
        """
        self.dimension = dimension
        self.use_faiss = use_faiss
        self.documents: List[Document] = []
        self.vectors: Optional[np.ndarray] = None
        
        if use_faiss:
            # Initialize FAISS index for efficient similarity search
            self.index = faiss.IndexFlatIP(dimension)  # Inner product (cosine similarity)
            print(f"Initialized FAISS index with dimension {dimension}")
        else:
            self.index = None
    
    def add_documents(self, documents: List[Document]):
        """
        Add documents with their vector embeddings to the database.
        
        Args:
            documents: List of Document objects with embeddings
        """
        print(f"Adding {len(documents)} documents to vector database...")
        
        # Store documents
        self.documents.extend(documents)
        
        # Extract vectors
        new_vectors = np.array([doc.vector for doc in documents])
        
        if self.vectors is None:
            self.vectors = new_vectors
        else:
            self.vectors = np.vstack([self.vectors, new_vectors])
        
        if self.use_faiss:
            # Normalize vectors for cosine similarity
            normalized_vectors = new_vectors / np.linalg.norm(new_vectors, axis=1, keepdims=True)
            self.index.add(normalized_vectors.astype('float32'))
        
        print(f"Database now contains {len(self.documents)} documents")
    
    def similarity_search(self, query_vector: np.ndarray, k: int = 5) -> List[Tuple[Document, float]]:
        """
        Perform similarity search to find the most relevant documents.
        
        Args:
            query_vector: Query vector to search for
            k: Number of top results to return
            
        Returns:
            List of tuples (document, similarity_score)
        """
        if len(self.documents) == 0:
            return []
        
        print(f"Performing similarity search for top {k} results...")
        
        if self.use_faiss:
            # Use FAISS for efficient search
            query_normalized = query_vector / np.linalg.norm(query_vector)
            query_normalized = query_normalized.reshape(1, -1).astype('float32')
            
            scores, indices = self.index.search(query_normalized, k)
            
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(self.documents):  # Valid index
                    results.append((self.documents[idx], float(score)))
            
        else:
            # Use sklearn cosine similarity
            query_vector = query_vector.reshape(1, -1)
            similarities = cosine_similarity(query_vector, self.vectors)[0]
            
            # Get top k indices
            top_indices = np.argsort(similarities)[::-1][:k]
            
            results = []
            for idx in top_indices:
                results.append((self.documents[idx], similarities[idx]))
        
        return results
    
    def save_to_disk(self, filepath: str):
        """Save the vector database to disk."""
        data = {
            'documents': [
                {
                    'id': doc.id,
                    'content': doc.content,
                    'metadata': doc.metadata,
                    'vector': doc.vector.tolist()
                }
                for doc in self.documents
            ],
            'dimension': self.dimension
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Vector database saved to {filepath}")
    
    def load_from_disk(self, filepath: str):
        """Load the vector database from disk."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        documents = []
        for doc_data in data['documents']:
            doc = Document(
                id=doc_data['id'],
                content=doc_data['content'],
                metadata=doc_data['metadata'],
                vector=np.array(doc_data['vector'])
            )
            documents.append(doc)
        
        self.documents = documents
        self.vectors = np.array([doc.vector for doc in documents])
        
        if self.use_faiss:
            # Rebuild FAISS index
            normalized_vectors = self.vectors / np.linalg.norm(self.vectors, axis=1, keepdims=True)
            self.index.add(normalized_vectors.astype('float32'))
        
        print(f"Vector database loaded from {filepath} with {len(self.documents)} documents")


def create_sample_documents() -> List[Document]:
    """Create sample documents for demonstration."""
    sample_texts = [
        "Machine learning is a subset of artificial intelligence that focuses on algorithms.",
        "Deep learning uses neural networks with multiple layers to learn complex patterns.",
        "Natural language processing enables computers to understand human language.",
        "Computer vision allows machines to interpret and analyze visual information.",
        "Data science combines statistics, programming, and domain expertise.",
        "Python is a popular programming language for data analysis and machine learning.",
        "Databases store and organize large amounts of structured information.",
        "Cloud computing provides on-demand access to computing resources.",
        "Cybersecurity protects digital systems from malicious attacks.",
        "Web development involves creating websites and web applications."
    ]
    
    documents = []
    for i, text in enumerate(sample_texts):
        doc = Document(
            id=f"doc_{i+1}",
            content=text,
            metadata={
                "category": "technology",
                "length": len(text),
                "created_at": "2024-01-01"
            }
        )
        documents.append(doc)
    
    return documents


def demonstrate_vector_operations():
    """Comprehensive demonstration of vector database operations."""
    print("=" * 60)
    print("VECTOR DATABASE DEMONSTRATION")
    print("=" * 60)
    
    # Step 1: Vectorization
    print("\n1. VECTORIZATION PHASE")
    print("-" * 30)
    
    # Create sample documents
    documents = create_sample_documents()
    print(f"Created {len(documents)} sample documents")
    
    # Initialize embedder
    embedder = VectorEmbedder(method="sentence_transformer")
    
    # Generate embeddings for all documents
    texts = [doc.content for doc in documents]
    embeddings = embedder.embed_text(texts)
    
    # Assign embeddings to documents
    for doc, embedding in zip(documents, embeddings):
        doc.vector = embedding
    
    print(f"Generated embeddings with dimension: {embeddings.shape[1]}")
    
    # Step 2: Storage
    print("\n2. STORAGE PHASE")
    print("-" * 30)
    
    # Initialize vector database
    vector_db = VectorDatabase(dimension=embeddings.shape[1], use_faiss=True)
    
    # Add documents to database
    vector_db.add_documents(documents)
    
    # Save to disk (optional)
    db_filepath = "vector_database.json"
    vector_db.save_to_disk(db_filepath)
    
    # Step 3: Retrieval
    print("\n3. RETRIEVAL PHASE")
    print("-" * 30)
    
    # Example queries
    queries = [
        "What is artificial intelligence and machine learning?",
        "How do neural networks work in deep learning?",
        "Programming languages for data analysis",
        "Security in computer systems"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\nQuery {i}: '{query}'")
        print("-" * 40)
        
        # Generate query embedding
        query_vector = embedder.embed_single_text(query)
        
        # Perform similarity search
        results = vector_db.similarity_search(query_vector, k=3)
        
        # Display results
        for j, (doc, score) in enumerate(results, 1):
            print(f"  {j}. [Score: {score:.4f}] {doc.content[:80]}...")
            print(f"     ID: {doc.id}, Category: {doc.metadata['category']}")
    
    # Step 4: Advanced Operations
    print("\n4. ADVANCED OPERATIONS")
    print("-" * 30)
    
    # Demonstrate loading from disk
    print("\nLoading database from disk...")
    new_db = VectorDatabase(dimension=embeddings.shape[1], use_faiss=True)
    new_db.load_from_disk(db_filepath)
    
    # Test loaded database
    test_query = "machine learning algorithms"
    test_vector = embedder.embed_single_text(test_query)
    test_results = new_db.similarity_search(test_vector, k=2)
    
    print(f"\nTest query on loaded database: '{test_query}'")
    for i, (doc, score) in enumerate(test_results, 1):
        print(f"  {i}. [Score: {score:.4f}] {doc.content}")
    
    # Cleanup
    if os.path.exists(db_filepath):
        os.remove(db_filepath)
        print(f"\nCleaned up temporary file: {db_filepath}")
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)


def demonstrate_different_embedding_methods():
    """Demonstrate different embedding methods."""
    print("\n" + "=" * 60)
    print("COMPARING DIFFERENT EMBEDDING METHODS")
    print("=" * 60)
    
    # Sample texts
    texts = [
        "Machine learning is transforming technology.",
        "Deep learning uses neural networks effectively.",
        "Natural language processing understands text."
    ]
    
    # Test different embedding methods
    methods = ["sentence_transformer", "tfidf"]
    
    for method in methods:
        print(f"\nTesting {method.upper()} method:")
        print("-" * 40)
        
        try:
            embedder = VectorEmbedder(method=method)
            embeddings = embedder.embed_text(texts)
            
            print(f"Embedding shape: {embeddings.shape}")
            print(f"Sample embedding (first 5 dimensions): {embeddings[0][:5]}")
            
            # Calculate similarity between first two texts
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            print(f"Similarity between text 1 and 2: {similarity:.4f}")
            
        except Exception as e:
            print(f"Error with {method}: {e}")


if __name__ == "__main__":
    try:
        # Main demonstration
        demonstrate_vector_operations()
        
        # Additional demonstrations
        demonstrate_different_embedding_methods()
        
    except ImportError as e:
        print(f"Missing required dependencies: {e}")
        print("\nPlease install required packages:")
        print("pip install numpy scikit-learn sentence-transformers faiss-cpu")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()