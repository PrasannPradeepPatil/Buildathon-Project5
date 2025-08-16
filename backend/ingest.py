
import os
import hashlib
from typing import Optional, Dict, Any
import requests
from urllib.parse import urljoin, urlparse
import trafilatura
from backend.config import DATA_BUDGET_MB, URL_TIMEOUT, MAX_URL_SIZE_MB
from backend.neo4j_store import Neo4jStore
from backend.nlp import chunk_text, embed_chunks, extract_concepts, compute_cooccurrence_pairs

class DocumentProcessor:
    """Document processor for handling file uploads and URL ingestion."""
    
    def __init__(self, neo4j_store: Neo4jStore):
        self.store = neo4j_store
        self.ingestion_service = IngestionService(neo4j_store)
    
    async def process_document(self, content: str, filename: str) -> dict:
        """Process a document from string content."""
        try:
            # Convert string to bytes for compatibility
            content_bytes = content.encode('utf-8')
            result = self.ingestion_service.ingest_file("", content_bytes, filename)
            return {
                "status": "success",
                "filename": filename,
                "chunks_created": result.get('chunks_created', 0),
                "concepts_extracted": result.get('concepts_extracted', 0),
                "doc_id": result.get('doc_id', ''),
                "bytes_ingested": result.get('bytes_ingested', 0)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "filename": filename
            }
    
    async def process_url(self, url: str) -> dict:
        """Process a document from URL."""
        try:
            result = self.ingestion_service.ingest_url(url)
            return {
                "status": "success",
                "url": url,
                "chunks_created": result.get('chunks_created', 0),
                "concepts_extracted": result.get('concepts_extracted', 0),
                "doc_id": result.get('doc_id', ''),
                "bytes_ingested": result.get('bytes_ingested', 0)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "url": url
            }

class IngestionService:
    def __init__(self, neo4j_store: Neo4jStore):
        self.store = neo4j_store
    
    def check_budget(self, additional_bytes: int) -> bool:
        """Check if adding bytes would exceed budget."""
        stats = self.store.stats()
        current_bytes = stats.get('total_bytes', 0)
        budget_bytes = DATA_BUDGET_MB * 1024 * 1024
        
        return (current_bytes + additional_bytes) <= budget_bytes
    
    def ingest_file(self, file_path: str, content: bytes, filename: str) -> Dict[str, Any]:
        """Ingest a text file."""
        file_size = len(content)
        
        if not self.check_budget(file_size):
            raise ValueError(f"File would exceed {DATA_BUDGET_MB}MB budget")
        
        try:
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            raise ValueError("File must be UTF-8 encoded text")
        
        # Generate document ID
        doc_id = hashlib.md5(f"file:{filename}".encode()).hexdigest()
        
        # Store document
        self.store.upsert_document(
            doc_id=doc_id,
            doc_type='file',
            name=filename,
            bytes_size=file_size
        )
        
        # Process content
        result = self._process_content(text_content, doc_id)
        result['doc_id'] = doc_id
        result['bytes_ingested'] = file_size
        
        return result
    
    def ingest_url(self, url: str) -> Dict[str, Any]:
        """Ingest content from a URL."""
        # Validate URL
        parsed = urlparse(url)
        if parsed.scheme not in ['http', 'https']:
            raise ValueError("Only HTTP/HTTPS URLs are supported")
        
        # Check robots.txt (basic implementation)
        robots_url = urljoin(url, '/robots.txt')
        try:
            robots_response = requests.get(robots_url, timeout=5)
            if robots_response.status_code == 200:
                robots_content = robots_response.text.lower()
                if 'user-agent: *' in robots_content and 'disallow: /' in robots_content:
                    raise ValueError("URL disallowed by robots.txt")
        except:
            pass  # Continue if robots.txt check fails
        
        # Fetch content
        try:
            response = requests.get(url, timeout=URL_TIMEOUT)
            response.raise_for_status()
            
            content_length = len(response.content)
            max_bytes = MAX_URL_SIZE_MB * 1024 * 1024
            
            if content_length > max_bytes:
                raise ValueError(f"URL content exceeds {MAX_URL_SIZE_MB}MB limit")
            
            if not self.check_budget(content_length):
                raise ValueError(f"URL would exceed {DATA_BUDGET_MB}MB budget")
            
            # Extract text content
            text_content = trafilatura.extract(response.content, include_links=False, include_images=False)
            
            if not text_content:
                raise ValueError("Could not extract text from URL")
            
        except requests.RequestException as e:
            raise ValueError(f"Failed to fetch URL: {str(e)}")
        
        # Generate document ID
        doc_id = hashlib.md5(f"url:{url}".encode()).hexdigest()
        
        # Store document
        self.store.upsert_document(
            doc_id=doc_id,
            doc_type='url',
            name=url,
            url=url,
            bytes_size=content_length
        )
        
        # Process content
        result = self._process_content(text_content, doc_id)
        result['doc_id'] = doc_id
        result['url'] = url
        result['bytes_ingested'] = content_length
        
        return result
    
    def _process_content(self, text: str, doc_id: str) -> Dict[str, Any]:
        """Process text content: chunk, embed, extract concepts."""
        # Chunk text
        chunks = chunk_text(text)
        chunks = embed_chunks(chunks)
        
        # Store chunks
        for chunk in chunks:
            chunk_id = f"{doc_id}_{chunk['id']}"
            self.store.upsert_chunk_with_embedding(
                chunk_id=chunk_id,
                text=chunk['text'],
                start=chunk['start'],
                end=chunk['end'],
                doc_id=doc_id,
                embedding=chunk['embedding']
            )
        
        # Extract concepts from all chunks
        all_concepts = []
        chunk_concepts = []
        
        for chunk in chunks:
            concepts = extract_concepts(chunk['text'])
            chunk_concepts.append([c['label'] for c in concepts])
            all_concepts.extend(concepts)
        
        # Store unique concepts
        unique_concepts = {}
        for concept in all_concepts:
            label = concept['label']
            if label in unique_concepts:
                unique_concepts[label]['freq'] += 1
            else:
                unique_concepts[label] = concept
                unique_concepts[label]['freq'] = 1
        
        for concept in unique_concepts.values():
            concept_id = hashlib.md5(concept['label'].encode()).hexdigest()
            self.store.upsert_concept(
                concept_id=concept_id,
                label=concept['label'],
                lemma=concept['lemma'],
                freq=concept['freq']
            )
        
        # Link chunks to concepts
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_{chunk['id']}"
            for concept_label in chunk_concepts[i]:
                self.store.link_mentions(chunk_id, concept_label)
        
        # Compute co-occurrences
        cooccurrence_count = 0
        for concepts_in_chunk in chunk_concepts:
            if len(concepts_in_chunk) > 1:
                pairs = compute_cooccurrence_pairs(concepts_in_chunk)
                for concept1, concept2, weight in pairs:
                    self.store.bump_cooccurrence(concept1, concept2, weight)
                    cooccurrence_count += 1
        
        return {
            'chunks_created': len(chunks),
            'concepts_extracted': len(unique_concepts),
            'cooccurrences_created': cooccurrence_count
        }
