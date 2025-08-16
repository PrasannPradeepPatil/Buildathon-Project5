
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from backend.neo4j_store import Neo4jStore
from backend.nlp import embed_text

class RetrievalService:
    def __init__(self, neo4j_store: Neo4jStore):
        self.store = neo4j_store
    
    def search_chunks(self, query: str, k: int = 10, alpha: float = 0.7) -> List[Dict[str, Any]]:
        """Search chunks using hybrid semantic + keyword approach."""
        # Embed the query
        query_vector = embed_text(query)
        
        # Perform hybrid search
        results = self.store.hybrid_search(query, query_vector, k, alpha)
        
        # Normalize scores
        if results:
            max_score = max(result['combined_score'] for result in results)
            if max_score > 0:
                for result in results:
                    result['normalized_score'] = result['combined_score'] / max_score
        
        return results
    
    def expand_context(self, chunk_results: List[Dict[str, Any]], hops: int = 1) -> Dict[str, Any]:
        """Expand context by including related concepts."""
        chunk_ids = [result['chunk_id'] for result in chunk_results]
        neighborhood = self.store.expand_neighborhood(chunk_ids, hops)
        
        return {
            'chunks': chunk_results,
            'concepts': neighborhood.get('concepts', []),
            'relationships': neighborhood.get('relationships', [])
        }
    
    def select_best_snippets(self, chunks: List[Dict[str, Any]], max_snippets: int = 5) -> List[str]:
        """Select best snippets using MMR (Maximal Marginal Relevance) approach."""
        if not chunks:
            return []
        
        # Simple implementation: take top scored unique chunks
        seen_texts = set()
        snippets = []
        
        for chunk in chunks:
            text = chunk['text'].strip()
            if text not in seen_texts and len(text) > 20:  # Avoid very short snippets
                snippets.append(text)
                seen_texts.add(text)
                
                if len(snippets) >= max_snippets:
                    break
        
        return snippets
    
    def dedupe_by_document(self, chunks: List[Dict[str, Any]], max_per_doc: int = 3) -> List[Dict[str, Any]]:
        """Limit chunks per document for diversity."""
        doc_counts = {}
        filtered_chunks = []
        
        for chunk in chunks:
            doc_id = chunk.get('doc_id', '')
            count = doc_counts.get(doc_id, 0)
            
            if count < max_per_doc:
                filtered_chunks.append(chunk)
                doc_counts[doc_id] = count + 1
        
        return filtered_chunks
