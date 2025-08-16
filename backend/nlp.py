
import re
import spacy
from typing import List, Dict, Tuple, Any
from sentence_transformers import SentenceTransformer
import numpy as np
from backend.config import EMBED_MODEL, CHUNK_SIZE, CHUNK_OVERLAP

# Load models
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Please install spacy English model: python -m spacy download en_core_web_sm")
    nlp = None

embed_model = SentenceTransformer(EMBED_MODEL)

def clean_text(text: str) -> str:
    """Clean text by removing control characters and normalizing whitespace."""
    # Remove control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[Dict[str, Any]]:
    """Chunk text with overlap."""
    text = clean_text(text)
    chunks = []
    start = 0
    chunk_id = 0
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_text = text[start:end]
        
        chunks.append({
            'id': chunk_id,
            'text': chunk_text,
            'start': start,
            'end': end
        })
        
        if end >= len(text):
            break
            
        start = end - overlap
        chunk_id += 1
    
    return chunks

def embed_text(text: str) -> List[float]:
    """Generate embedding for text."""
    embedding = embed_model.encode(text, convert_to_tensor=False)
    return embedding.tolist()

def embed_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Add embeddings to chunks."""
    texts = [chunk['text'] for chunk in chunks]
    embeddings = embed_model.encode(texts, convert_to_tensor=False)
    
    for i, chunk in enumerate(chunks):
        chunk['embedding'] = embeddings[i].tolist()
    
    return chunks

def extract_concepts(text: str, max_tokens: int = 5) -> List[Dict[str, Any]]:
    """Extract concepts (noun chunks and proper nouns) from text."""
    if not nlp:
        return []
    
    doc = nlp(text)
    concepts = []
    seen_concepts = set()
    
    # Extract noun chunks
    for chunk in doc.noun_chunks:
        if len(chunk.text.split()) <= max_tokens:
            normalized = chunk.text.lower().strip()
            lemmatized = ' '.join([token.lemma_.lower() for token in chunk])
            
            if normalized not in seen_concepts and len(normalized) > 2:
                concepts.append({
                    'label': normalized,
                    'lemma': lemmatized,
                    'type': 'noun_chunk'
                })
                seen_concepts.add(normalized)
    
    # Extract proper nouns
    for ent in doc.ents:
        if ent.label_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT', 'EVENT']:
            normalized = ent.text.lower().strip()
            if normalized not in seen_concepts and len(normalized) > 2:
                concepts.append({
                    'label': normalized,
                    'lemma': normalized,
                    'type': 'named_entity'
                })
                seen_concepts.add(normalized)
    
    return concepts

def compute_cooccurrence_pairs(concepts: List[str], window_size: int = 5) -> List[Tuple[str, str, float]]:
    """Compute co-occurrence pairs within a sliding window."""
    pairs = []
    
    for i in range(len(concepts)):
        for j in range(i + 1, min(i + window_size, len(concepts))):
            concept1 = concepts[i]
            concept2 = concepts[j]
            
            if concept1 != concept2:
                # Simple PMI-like weight (can be enhanced)
                weight = 1.0 / (abs(j - i))
                pairs.append((concept1, concept2, weight))
    
    return pairs
