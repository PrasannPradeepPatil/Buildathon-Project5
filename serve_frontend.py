
#!/usr/bin/env python3
"""
Unified server that serves both the frontend and backend API
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import logging
import time
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Universal Knowledge-Graph Builder",
    description="Unified frontend and backend server",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class UrlIngestRequest(BaseModel):
    url: str

class QARequest(BaseModel):
    question: str
    k: Optional[int] = 10

# Mock data
mock_nodes = [
    {"id": "1", "label": "Machine Learning", "weight": 15, "community": 0},
    {"id": "2", "label": "Neural Networks", "weight": 12, "community": 0},
    {"id": "3", "label": "Deep Learning", "weight": 10, "community": 0},
    {"id": "4", "label": "Python", "weight": 20, "community": 1},
    {"id": "5", "label": "Programming", "weight": 18, "community": 1},
    {"id": "6", "label": "Data Science", "weight": 14, "community": 2},
    {"id": "7", "label": "Statistics", "weight": 8, "community": 2},
    {"id": "8", "label": "Algorithms", "weight": 11, "community": 0},
]

mock_edges = [
    {"source": "1", "target": "2", "weight": 5},
    {"source": "1", "target": "3", "weight": 8},
    {"source": "2", "target": "3", "weight": 7},
    {"source": "1", "target": "8", "weight": 4},
    {"source": "4", "target": "5", "weight": 6},
    {"source": "1", "target": "6", "weight": 3},
    {"source": "6", "target": "7", "weight": 5},
    {"source": "4", "target": "6", "weight": 4},
]

# Frontend directory
FRONTEND_DIR = Path(__file__).parent / "frontend"

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting unified frontend and backend server...")

# API Endpoints
@app.post("/ingest/upload")
async def upload_file(file: UploadFile = File(...)):
    """File upload endpoint."""
    if not file.filename.lower().endswith('.txt'):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")
    
    # Simulate processing time
    time.sleep(1)
    
    return JSONResponse(content={
        "status": "success",
        "filename": file.filename,
        "chunks_created": 15,
        "concepts_extracted": 8
    })

@app.post("/ingest/url")
async def ingest_url(request: UrlIngestRequest):
    """URL ingestion endpoint."""
    # Simulate processing time
    time.sleep(2)
    
    return JSONResponse(content={
        "status": "success",
        "chunks_created": 25,
        "concepts_extracted": 12
    })

@app.get("/graph")
async def get_graph():
    """Return mock graph data."""
    try:
        # Ensure all nodes have required properties
        safe_nodes = []
        for node in mock_nodes:
            safe_node = {
                "id": str(node.get("id", "")),
                "label": str(node.get("label", "Unknown")),
                "weight": int(node.get("weight", 1)),
                "community": int(node.get("community", 0))
            }
            safe_nodes.append(safe_node)
        
        # Ensure all edges have required properties
        safe_edges = []
        for edge in mock_edges:
            safe_edge = {
                "source": str(edge.get("source", "")),
                "target": str(edge.get("target", "")),
                "weight": int(edge.get("weight", 1))
            }
            safe_edges.append(safe_edge)
        
        return JSONResponse(content={
            "nodes": safe_nodes,
            "edges": safe_edges
        })
    except Exception as e:
        logger.error(f"Error getting graph data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/node/{node_id}")
async def get_node_details(node_id: str):
    """Return mock node details."""
    try:
        node = next((n for n in mock_nodes if str(n["id"]) == str(node_id)), None)
        
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        
        return JSONResponse(content={
            "id": str(node["id"]),
            "label": str(node["label"]),
            "freq": int(node.get("weight", 1)),
            "community": int(node.get("community", 0)),
            "snippets": [
                {
                    "text": f"This is a sample snippet about {node['label']} from document 1. It contains relevant information that helps understand the concept better.",
                    "doc_name": "sample_document_1.txt"
                },
                {
                    "text": f"Another example snippet discussing {node['label']} in more detail. This comes from a different source document.",
                    "doc_name": "sample_document_2.txt"
                },
                {
                    "text": f"A third snippet that mentions {node['label']} in the context of related topics and applications.",
                    "doc_name": "sample_document_3.txt"
                }
            ]
        })
    except Exception as e:
        logger.error(f"Error getting node details for {node_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/search")
async def search(q: str = Query(...), k: int = Query(10)):
    """Mock search endpoint."""
    return JSONResponse(content={
        "query": q,
        "results": [
            {
                "chunk_id": "chunk_1",
                "text": f"This is a sample search result for '{q}'. It contains relevant information that matches your query.",
                "doc_id": "doc_1",
                "score": 0.95
            },
            {
                "chunk_id": "chunk_2", 
                "text": f"Another search result related to '{q}'. This chunk provides additional context and information.",
                "doc_id": "doc_2",
                "score": 0.87
            }
        ]
    })

@app.post("/qa")
async def ask_question(request: QARequest):
    """Mock Q&A endpoint."""
    question = request.question
    
    # Generate a mock answer based on the question
    answer = f"This is a mock answer to your question: '{question}'. In a real implementation, this would be generated using the knowledge graph and retrieved documents to provide accurate, contextual responses."
    
    return JSONResponse(content={
        "answer": answer,
        "sources": [
            {
                "snippet": f"Relevant snippet 1 that helps answer the question about {question[:20]}...",
                "score": 0.92,
                "docId": "doc_1",
                "doc_name": "Sample Document 1",
                "url": "https://example.com/doc1"
            },
            {
                "snippet": f"Relevant snippet 2 providing additional context for {question[:20]}...",
                "score": 0.85,
                "docId": "doc_2", 
                "doc_name": "Sample Document 2",
                "url": "https://example.com/doc2"
            }
        ],
        "nodes_used": ["Machine Learning", "Python", "Data Science"]
    })

@app.get("/stats")
async def get_stats():
    """Return mock statistics."""
    try:
        return JSONResponse(content={
            "docs": 5,
            "chunks": 47,
            "concepts": 8,
            "edges": 8,
            "total_bytes": 52428800,  # ~50MB
            "budget_mb": 100,
            "used_mb": 50.0,
            "remaining_mb": 50.0
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "mode": "unified"}

# Frontend routes
@app.get("/")
async def serve_index():
    """Serve the main HTML page."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    else:
        raise HTTPException(status_code=404, detail="Frontend not found")

# Mount static files for any additional assets
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

if __name__ == "__main__":
    import uvicorn
    PORT = 5000
    print(f"Starting unified server on port {PORT}")
    print(f"Frontend directory: {FRONTEND_DIR}")
    
    if not FRONTEND_DIR.exists():
        print(f"Warning: Frontend directory {FRONTEND_DIR} does not exist!")
    
    uvicorn.run(app, host="0.0.0.0", port=PORT)
