
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import logging

from backend.neo4j_store import Neo4jStore
from backend.ingest import IngestionService
from backend.retrieval import RetrievalService
from backend.qa import QAService
from backend.graph_ops import GraphOperations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
neo4j_store = Neo4jStore()
ingest_service = IngestionService(neo4j_store)
retrieval_service = RetrievalService(neo4j_store)
qa_service = QAService(retrieval_service)
graph_ops = GraphOperations(neo4j_store)

# Create FastAPI app
app = FastAPI(
    title="Universal Knowledge-Graph Builder",
    description="Convert documents into an interactive knowledge graph with Q&A",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
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

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Universal Knowledge-Graph Builder...")
    try:
        # Compute communities on startup (async)
        asyncio.create_task(compute_communities_async())
    except Exception as e:
        logger.error(f"Startup error: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    neo4j_store.close()

async def compute_communities_async():
    """Compute communities asynchronously."""
    try:
        await asyncio.sleep(5)  # Wait a bit for initial data
        graph_ops.compute_communities()
        logger.info("Communities computed successfully")
    except Exception as e:
        logger.error(f"Community computation failed: {e}")

@app.post("/ingest/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and ingest a text file."""
    try:
        # Validate file type
        if not file.filename.lower().endswith('.txt'):
            raise HTTPException(status_code=400, detail="Only .txt files are supported")
        
        # Read file content
        content = await file.read()
        
        # Ingest the file
        result = ingest_service.ingest_file(file.filename, content, file.filename)
        
        return JSONResponse(content={
            "status": "success",
            "filename": file.filename,
            **result
        })
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/ingest/url")
async def ingest_url(request: UrlIngestRequest):
    """Ingest content from a URL."""
    try:
        result = ingest_service.ingest_url(request.url)
        
        return JSONResponse(content={
            "status": "success",
            **result
        })
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"URL ingestion error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/graph")
async def get_graph():
    """Get the concept graph for visualization."""
    try:
        graph_data = neo4j_store.get_graph()
        return JSONResponse(content=graph_data)
    except Exception as e:
        logger.error(f"Graph retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/node/{node_id}")
async def get_node_details(node_id: str):
    """Get detailed information about a concept node."""
    try:
        node_data = neo4j_store.get_node(node_id)
        
        if not node_data:
            raise HTTPException(status_code=404, detail="Node not found")
        
        return JSONResponse(content=node_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Node retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/search")
async def search(q: str = Query(...), k: int = Query(10)):
    """Search for relevant chunks and concepts."""
    try:
        results = retrieval_service.search_chunks(q, k)
        
        return JSONResponse(content={
            "query": q,
            "results": results
        })
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/qa")
async def ask_question(request: QARequest):
    """Answer a natural language question."""
    try:
        answer_data = qa_service.answer_question(request.question, request.k)
        
        # Add document metadata to sources
        for source in answer_data.get('sources', []):
            doc_data = neo4j_store.get_document_metadata(source['docId'])
            if doc_data:
                source['url'] = doc_data.get('url')
                source['doc_name'] = doc_data.get('name')
        
        return JSONResponse(content=answer_data)
    except Exception as e:
        logger.error(f"QA error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/stats")
async def get_stats():
    """Get database statistics."""
    try:
        stats = neo4j_store.stats()
        
        # Add budget information
        budget_bytes = 100 * 1024 * 1024  # 100MB
        stats['budget_mb'] = 100
        stats['used_mb'] = round(stats.get('total_bytes', 0) / (1024 * 1024), 2)
        stats['remaining_mb'] = round((budget_bytes - stats.get('total_bytes', 0)) / (1024 * 1024), 2)
        
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
