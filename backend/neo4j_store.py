
from typing import List, Dict, Any, Optional, Tuple
import logging
from neo4j import GraphDatabase, Driver
from backend.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

logger = logging.getLogger(__name__)

class Neo4jStore:
    def __init__(self):
        self.driver: Driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
        self.bootstrap_schema()
    
    def close(self):
        if self.driver:
            self.driver.close()
    
    def bootstrap_schema(self):
        """Create constraints and indexes idempotently."""
        with self.driver.session() as session:
            try:
                # Uniqueness constraints
                session.run("CREATE CONSTRAINT doc_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE")
                session.run("CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE")
                session.run("CREATE CONSTRAINT concept_label IF NOT EXISTS FOR (k:Concept) REQUIRE k.label IS UNIQUE")
                
                # Fulltext index for keyword search (check if exists first)
                result = session.run("SHOW INDEXES YIELD name WHERE name = 'chunk_text_idx'")
                if not list(result):
                    session.run("CALL db.index.fulltext.createNodeIndex('chunk_text_idx', ['Chunk'], ['text'])")
                
                # Vector indexes for semantic search (check if exists first)
                result = session.run("SHOW INDEXES YIELD name WHERE name = 'chunk_embedding_idx'")
                if not list(result):
                    session.run("""
                        CREATE VECTOR INDEX chunk_embedding_idx 
                        FOR (c:Chunk) ON (c.embedding) 
                        OPTIONS { 
                            indexConfig: { 
                                'vector.dimensions': 384, 
                                'vector.similarity_function': 'cosine' 
                            } 
                        }
                    """)
                
                logger.info("Schema bootstrap completed successfully")
            except Exception as e:
                logger.error(f"Error during schema bootstrap: {e}")
                raise
    
    def upsert_document(self, doc_id: str, doc_type: str, name: str, 
                       url: Optional[str] = None, bytes_size: int = 0) -> bool:
        """Upsert a document node."""
        with self.driver.session() as session:
            result = session.run("""
                MERGE (d:Document {id: $doc_id})
                SET d.type = $doc_type,
                    d.name = $name,
                    d.url = $url,
                    d.bytes = $bytes_size,
                    d.createdAt = datetime()
                RETURN d
            """, doc_id=doc_id, doc_type=doc_type, name=name, url=url, bytes_size=bytes_size)
            return len(list(result)) > 0
    
    def upsert_chunk_with_embedding(self, chunk_id: str, text: str, start: int, 
                                   end: int, doc_id: str, embedding: List[float]) -> bool:
        """Upsert a chunk with its embedding vector."""
        with self.driver.session() as session:
            result = session.run("""
                MERGE (c:Chunk {id: $chunk_id})
                SET c.text = $text,
                    c.start = $start,
                    c.end = $end,
                    c.docId = $doc_id,
                    c.embedding = $embedding
                WITH c
                MATCH (d:Document {id: $doc_id})
                MERGE (d)-[:HAS_CHUNK]->(c)
                RETURN c
            """, chunk_id=chunk_id, text=text, start=start, end=end, 
                 doc_id=doc_id, embedding=embedding)
            return len(list(result)) > 0
    
    def upsert_concept(self, concept_id: str, label: str, lemma: str, freq: int = 1,
                      embedding: Optional[List[float]] = None) -> bool:
        """Upsert a concept node."""
        with self.driver.session() as session:
            result = session.run("""
                MERGE (k:Concept {label: $label})
                SET k.id = $concept_id,
                    k.lemma = $lemma,
                    k.freq = COALESCE(k.freq, 0) + $freq,
                    k.embedding = $embedding
                RETURN k
            """, concept_id=concept_id, label=label, lemma=lemma, freq=freq, embedding=embedding)
            return len(list(result)) > 0
    
    def link_mentions(self, chunk_id: str, concept_label: str) -> bool:
        """Link a chunk to a concept via MENTIONS relationship."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Chunk {id: $chunk_id})
                MATCH (k:Concept {label: $concept_label})
                MERGE (c)-[:MENTIONS]->(k)
                RETURN c, k
            """, chunk_id=chunk_id, concept_label=concept_label)
            return len(list(result)) > 0
    
    def bump_cooccurrence(self, concept1_label: str, concept2_label: str, weight: float = 1.0) -> bool:
        """Create or increment co-occurrence relationship between concepts."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (k1:Concept {label: $label1})
                MATCH (k2:Concept {label: $label2})
                WHERE k1 <> k2
                MERGE (k1)-[r:CO_OCCURS]-(k2)
                SET r.weight = COALESCE(r.weight, 0) + $weight
                RETURN r
            """, label1=concept1_label, label2=concept2_label, weight=weight)
            return len(list(result)) > 0
    
    def vector_search_chunks(self, query_vector: List[float], k: int = 10) -> List[Dict[str, Any]]:
        """Search for similar chunks using vector index."""
        with self.driver.session() as session:
            result = session.run("""
                CALL db.index.vector.queryNodes('chunk_embedding_idx', $k, $qvec)
                YIELD node, score
                RETURN node.id as chunk_id, node.text as text, node.docId as doc_id, score
                ORDER BY score DESC
            """, k=k, qvec=query_vector)
            return [dict(record) for record in result]
    
    def hybrid_search(self, query: str, query_vector: List[float], k: int = 10, alpha: float = 0.7) -> List[Dict[str, Any]]:
        """Hybrid search combining vector and keyword search."""
        # Get vector results
        vector_results = self.vector_search_chunks(query_vector, k)
        
        # Get keyword results
        with self.driver.session() as session:
            keyword_result = session.run("""
                CALL db.index.fulltext.queryNodes('chunk_text_idx', $query)
                YIELD node, score
                RETURN node.id as chunk_id, node.text as text, node.docId as doc_id, score as kw_score
                ORDER BY score DESC
                LIMIT $k
            """, query=query, k=k)
            keyword_results = [dict(record) for record in keyword_result]
        
        # Combine scores (simple implementation)
        combined_results = {}
        for result in vector_results:
            chunk_id = result['chunk_id']
            combined_results[chunk_id] = {
                **result,
                'vector_score': result['score'],
                'kw_score': 0.0,
                'combined_score': alpha * result['score']
            }
        
        for result in keyword_results:
            chunk_id = result['chunk_id']
            if chunk_id in combined_results:
                combined_results[chunk_id]['kw_score'] = result['kw_score']
                combined_results[chunk_id]['combined_score'] += (1 - alpha) * result['kw_score']
            else:
                combined_results[chunk_id] = {
                    **result,
                    'vector_score': 0.0,
                    'kw_score': result['kw_score'],
                    'combined_score': (1 - alpha) * result['kw_score']
                }
        
        return sorted(combined_results.values(), key=lambda x: x['combined_score'], reverse=True)[:k]
    
    def expand_neighborhood(self, chunk_ids: List[str], hops: int = 1) -> Dict[str, Any]:
        """Expand concept neighborhood from given chunks."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Chunk)-[:MENTIONS]->(k:Concept)
                WHERE c.id IN $chunk_ids
                WITH COLLECT(DISTINCT k) as seed_concepts
                UNWIND seed_concepts as k
                OPTIONAL MATCH (k)-[r:CO_OCCURS]-(k2:Concept)
                RETURN COLLECT(DISTINCT {id: k.id, label: k.label, freq: k.freq, community: k.community}) as concepts,
                       COLLECT(DISTINCT {source: k.label, target: k2.label, weight: r.weight}) as relationships
            """, chunk_ids=chunk_ids)
            
            record = result.single()
            if record:
                return {
                    'concepts': record['concepts'],
                    'relationships': record['relationships']
                }
            return {'concepts': [], 'relationships': []}
    
    def get_graph(self) -> Dict[str, Any]:
        """Get the complete concept graph for visualization."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (k:Concept)
                OPTIONAL MATCH (k)-[e:CO_OCCURS]->(k2:Concept)
                RETURN COLLECT(DISTINCT {id: k.id, label: k.label, weight: k.freq, community: COALESCE(k.community, 0)}) as nodes,
                       COLLECT(DISTINCT {source: k.id, target: k2.id, weight: e.weight}) as edges
            """)
            
            record = result.single()
            if record:
                return {
                    'nodes': record['nodes'],
                    'edges': [edge for edge in record['edges'] if edge['target'] is not None]
                }
            return {'nodes': [], 'edges': []}
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a concept node."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (k:Concept {id: $node_id})
                OPTIONAL MATCH (c:Chunk)-[:MENTIONS]->(k)
                OPTIONAL MATCH (c)<-[:HAS_CHUNK]-(d:Document)
                RETURN k,
                       COLLECT(DISTINCT {text: c.text, doc_name: d.name, doc_url: d.url}) as snippets
            """, node_id=node_id)
            
            record = result.single()
            if record:
                concept = record['k']
                return {
                    'id': concept['id'],
                    'label': concept['label'],
                    'lemma': concept['lemma'],
                    'freq': concept['freq'],
                    'community': concept.get('community', 0),
                    'snippets': record['snippets'][:5]  # Top 5 snippets
                }
            return None
    
    def get_document_metadata(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document metadata by ID."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (d:Document {id: $doc_id})
                RETURN d.name as name, d.url as url, d.type as type
            """, doc_id=doc_id)
            
            record = result.single()
            if record:
                return dict(record)
            return None
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics (async version)."""
        return self.stats()
    
    def stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (d:Document) WITH COUNT(d) as docs, SUM(d.bytes) as total_bytes
                MATCH (c:Chunk) WITH docs, total_bytes, COUNT(c) as chunks
                MATCH (k:Concept) WITH docs, total_bytes, chunks, COUNT(k) as concepts
                MATCH ()-[r:CO_OCCURS]-() WITH docs, total_bytes, chunks, concepts, COUNT(r)/2 as edges
                RETURN docs, chunks, concepts, edges, total_bytes
            """)
            
            record = result.single()
            if record:
                return dict(record)
            return {'docs': 0, 'chunks': 0, 'concepts': 0, 'edges': 0, 'total_bytes': 0}
