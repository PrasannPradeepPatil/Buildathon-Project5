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
    logger.info(f"📤 Upload request received: filename={file.filename}, size={file.size}")
    
    if not file.filename.lower().endswith('.txt'):
        logger.error(f"❌ Invalid file type: {file.filename}")
        raise HTTPException(status_code=400, detail="Only .txt files are supported")

    # Read file content for logging
    content = await file.read()
    logger.info(f"📄 File content length: {len(content)} bytes")
    
    # Simulate processing time
    time.sleep(1)

    logger.info(f"✅ Upload successful: {file.filename}")
    return JSONResponse(content={
        "status": "success",
        "filename": file.filename,
        "chunks_created": 15,
        "concepts_extracted": 8
    })

@app.post("/ingest/url")
async def ingest_url(request: UrlIngestRequest):
    """URL ingestion endpoint."""
    logger.info(f"🌐 URL ingestion request: {request.url}")
    
    # Simulate processing time
    time.sleep(2)

    logger.info(f"✅ URL ingestion successful: {request.url}")
    return JSONResponse(content={
        "status": "success",
        "chunks_created": 25,
        "concepts_extracted": 12
    })

@app.get("/graph")
async def get_graph():
    """Return graph data for visualization."""
    logger.info(f"📊 Graph data requested - returning {len(mock_nodes)} nodes and {len(mock_edges)} edges")
    
    return JSONResponse(content={
        "nodes": mock_nodes,
        "edges": mock_edges
    })

@app.get("/node/{node_id}")
async def get_node_details(node_id: str):
    """Return mock node details."""
    try:
        logger.info(f"🔍 Node details requested: node_id={node_id}")
        node = next((n for n in mock_nodes if str(n["id"]) == str(node_id)), None)

        if not node:
            logger.warning(f"❌ Node not found: {node_id}")
            raise HTTPException(status_code=404, detail="Node not found")

        logger.info(f"✅ Node details found: {node['label']}")
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
        logger.error(f"❌ Error getting node details for {node_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/search")
async def search(q: str = Query(...), k: int = Query(10)):
    """Mock search endpoint."""
    logger.info(f"🔍 Search request: query='{q}', k={k}")
    
    results = [
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
    
    logger.info(f"✅ Search completed: found {len(results)} results")
    return JSONResponse(content={
        "query": q,
        "results": results
    })

@app.post("/qa")
async def ask_question(request: QARequest):
    """Mock Q&A endpoint."""
    try:
        question = request.question
        logger.info(f"🤖 Q&A request: '{question}'")

        # Generate a mock answer based on the question
        answer = f"This is a mock answer to your question: '{question}'. In a real implementation, this would be generated using the knowledge graph and retrieved documents to provide accurate, contextual responses."

        # Determine relevant nodes based on question content
        relevant_nodes = []
        question_lower = question.lower()

        # Simple keyword matching to determine relevant nodes
        node_keywords = {
            "Machine Learning": ["machine", "learning", "ml", "model", "algorithm"],
            "Neural Networks": ["neural", "network", "neuron", "deep"],
            "Deep Learning": ["deep", "learning", "neural", "cnn", "rnn"],
            "Python": ["python", "programming", "code", "script"],
            "Programming": ["programming", "code", "software", "development"],
            "Data Science": ["data", "science", "analysis", "statistics"],
            "Statistics": ["statistics", "statistical", "probability", "math"],
            "Algorithms": ["algorithm", "sorting", "complexity", "optimization"]
        }

        for node_label, keywords in node_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                relevant_nodes.append(node_label)

        # Fallback to default nodes if no matches
        if not relevant_nodes:
            relevant_nodes = ["Machine Learning", "Python", "Data Science"]

        logger.info(f"📝 Generated answer with {len(relevant_nodes)} relevant nodes: {relevant_nodes}")

        response_data = {
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
            "nodes_used": relevant_nodes
        }
        
        logger.info(f"✅ Q&A response ready: {len(response_data['sources'])} sources")
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"❌ Error in Q&A endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

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