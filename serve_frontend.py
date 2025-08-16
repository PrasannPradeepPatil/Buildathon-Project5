
#!/usr/bin/env python3
"""
Unified server that serves frontend and uses real backend implementation.
"""

import logging
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import real backend modules
try:
    from backend.config import get_settings
    from backend.ingest import DocumentProcessor
    from backend.qa import QAEngine
    from backend.graph_ops import GraphOperations
    from backend.neo4j_store import Neo4jStore
    BACKEND_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Backend modules not available: {e}")
    BACKEND_AVAILABLE = False
    
    # Create dummy classes as fallbacks
    class DocumentProcessor:
        def __init__(self, *args, **kwargs):
            pass
        async def process_document(self, *args, **kwargs):
            return {}
        async def process_url(self, *args, **kwargs):
            return {}
    
    class QAEngine:
        def __init__(self, *args, **kwargs):
            pass
        async def answer_question(self, *args, **kwargs):
            return {}
        async def search(self, *args, **kwargs):
            return {}
    
    class GraphOperations:
        def __init__(self, *args, **kwargs):
            pass
        async def get_visualization_data(self, *args, **kwargs):
            return {}
        async def get_node_details(self, *args, **kwargs):
            return {}
    
    class Neo4jStore:
        def __init__(self, *args, **kwargs):
            pass
        async def get_statistics(self, *args, **kwargs):
            return {}
    
    def get_settings():
        return {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Universal Knowledge-Graph Builder")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class UrlIngestRequest(BaseModel):
    url: str

class QARequest(BaseModel):
    question: str
    k: Optional[int] = 10

# Frontend directory
FRONTEND_DIR = Path(__file__).parent / "frontend"

# Global variables for services
document_processor: Optional[DocumentProcessor] = None
qa_engine: Optional[QAEngine] = None
graph_ops: Optional[GraphOperations] = None
neo4j_store: Optional[Neo4jStore] = None
backend_initialized = False

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global document_processor, qa_engine, graph_ops, neo4j_store, backend_initialized
    
    logger.info("🚀 Starting unified frontend and backend server...")
    logger.info(f"📁 Frontend directory: {FRONTEND_DIR}")
    
    if BACKEND_AVAILABLE:
        try:
            # Get settings
            settings = get_settings()
            logger.info(f"📋 Loaded settings")
            
            # Initialize Neo4j store
            logger.info("🔗 Initializing Neo4j connection...")
            neo4j_store = Neo4jStore()
            
            # Initialize graph operations
            logger.info("📊 Initializing graph operations...")
            graph_ops = GraphOperations(neo4j_store)
            
            # Initialize document processor
            logger.info("📄 Initializing document processor...")
            document_processor = DocumentProcessor(neo4j_store)
            
            # Initialize QA engine
            logger.info("🤖 Initializing QA engine...")
            qa_engine = QAEngine(neo4j_store, graph_ops)
            
            backend_initialized = True
            logger.info("✅ Real backend services initialized successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize real backend services: {e}")
            logger.warning("⚠️ Falling back to mock mode...")
            backend_initialized = False
    else:
        logger.warning("⚠️ Backend modules not available, using mock mode...")
        backend_initialized = False

@app.post("/ingest/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process a document."""
    logger.info(f"📤 Upload request received: filename={file.filename}, size={file.size}")
    
    if not file.filename.lower().endswith('.txt'):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")
    
    try:
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        logger.info(f"📄 File content length: {len(content_str)} bytes")
        
        if backend_initialized and document_processor:
            # Use real document processor
            logger.info("🔄 Processing with real backend...")
            result = await document_processor.process_document(content_str, file.filename)
            logger.info(f"✅ Real processing complete: {result}")
            return JSONResponse(content=result)
        else:
            # Fallback to mock processing
            logger.warning("⚠️ Using mock processing (real backend not available)")
            time.sleep(1)  # Simulate processing time
            
            result = {
                "status": "success",
                "filename": file.filename,
                "chunks_created": 15,
                "concepts_extracted": 8,
                "note": "Mock processing - real backend not available"
            }
            logger.info(f"✅ Mock upload successful: {file.filename}")
            return JSONResponse(content=result)
            
    except Exception as e:
        logger.error(f"❌ Upload processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/ingest/url")
async def ingest_url(request: UrlIngestRequest):
    """Ingest content from a URL."""
    logger.info(f"🌐 URL ingestion request: {request.url}")
    
    try:
        if backend_initialized and document_processor:
            # Use real document processor
            logger.info("🔄 Processing URL with real backend...")
            result = await document_processor.process_url(request.url)
            logger.info(f"✅ Real URL processing complete: {result}")
            return JSONResponse(content=result)
        else:
            # Fallback to mock processing
            logger.warning("⚠️ Using mock URL processing (real backend not available)")
            time.sleep(2)  # Simulate processing time
            
            return JSONResponse(content={
                "status": "success",
                "url": request.url,
                "chunks_created": 25,
                "concepts_extracted": 12,
                "note": "Mock processing - real backend not available"
            })
            
    except Exception as e:
        logger.error(f"❌ URL processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"URL processing failed: {str(e)}")

@app.get("/graph")
async def get_graph():
    """Return graph data for visualization."""
    logger.info("📊 Graph data requested")
    
    try:
        if backend_initialized and graph_ops:
            # Use real graph operations
            logger.info("🔄 Fetching real graph data...")
            graph_data = await graph_ops.get_visualization_data()
            logger.info(f"📊 Real graph data: {len(graph_data.get('nodes', []))} nodes, {len(graph_data.get('edges', []))} edges")
            return JSONResponse(content=graph_data)
        else:
            # Fallback to mock data
            logger.warning("⚠️ Using mock graph data (real backend not available)")
            
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
            
            logger.info(f"📊 Mock graph data returned - {len(mock_nodes)} nodes and {len(mock_edges)} edges")
            return JSONResponse(content={
                "nodes": mock_nodes,
                "edges": mock_edges,
                "note": "Mock data - real backend not available"
            })
            
    except Exception as e:
        logger.error(f"❌ Failed to get graph data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve graph data")

@app.post("/qa")
async def ask_question(request: QARequest):
    """Answer questions using the knowledge graph."""
    logger.info(f"🤖 Q&A request: '{request.question}'")
    
    try:
        if backend_initialized and qa_engine:
            # Use real QA engine
            logger.info("🔄 Processing with real QA engine...")
            result = await qa_engine.answer_question(request.question, k=request.k)
            logger.info(f"✅ Real Q&A response generated")
            return JSONResponse(content=result)
        else:
            # Fallback to mock answer
            logger.warning("⚠️ Using mock Q&A (real backend not available)")
            question = request.question
            
            # Generate a mock answer based on the question
            answer = f"This is a mock answer to your question: '{question}'. The real backend is not available, so this is a simulated response. In a real implementation, this would use the knowledge graph and retrieved documents."
            
            # Determine relevant nodes based on question content
            relevant_nodes = []
            question_lower = question.lower()
            if "machine" in question_lower or "ml" in question_lower:
                relevant_nodes.append("Machine Learning")
            if "python" in question_lower or "programming" in question_lower:
                relevant_nodes.append("Python")
            if "data" in question_lower:
                relevant_nodes.append("Data Science")
            if "neural" in question_lower or "deep" in question_lower:
                relevant_nodes.append("Neural Networks")
            
            if not relevant_nodes:
                relevant_nodes = ["Data Science"]  # Default fallback
            
            result = {
                "answer": answer,
                "sources": [
                    {
                        "snippet": f"Mock snippet 1 that helps answer the question about {question[:20]}...",
                        "score": 0.92,
                        "docId": "doc_1",
                        "doc_name": "Sample Document 1",
                        "url": "https://example.com/doc1"
                    },
                    {
                        "snippet": f"Mock snippet 2 providing additional context for {question[:20]}...",
                        "score": 0.85,
                        "docId": "doc_2", 
                        "doc_name": "Sample Document 2",
                        "url": "https://example.com/doc2"
                    }
                ],
                "nodes_used": relevant_nodes,
                "note": "Mock response - real backend not available"
            }
            
            logger.info(f"📝 Generated mock answer with {len(relevant_nodes)} relevant nodes: {relevant_nodes}")
            logger.info(f"✅ Mock Q&A response ready: {len(result['sources'])} sources")
            return JSONResponse(content=result)
            
    except Exception as e:
        logger.error(f"❌ Q&A processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Q&A failed: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Return system statistics."""
    logger.info("📈 Stats requested")
    
    try:
        if backend_initialized and neo4j_store:
            # Use real statistics
            logger.info("🔄 Fetching real statistics...")
            stats = await neo4j_store.get_statistics()
            logger.info(f"📊 Real stats retrieved")
            return JSONResponse(content=stats)
        else:
            # Fallback to mock statistics
            logger.warning("⚠️ Using mock statistics (real backend not available)")
            return JSONResponse(content={
                "docs": 5,
                "chunks": 47,
                "concepts": 8,
                "edges": 8,
                "total_bytes": 52428800,  # ~50MB
                "budget_mb": 100,
                "used_mb": 50.0,
                "remaining_mb": 50.0,
                "note": "Mock data - real backend not available"
            })
            
    except Exception as e:
        logger.error(f"❌ Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

@app.get("/node/{node_id}")
async def get_node_details(node_id: str):
    """Return detailed information about a specific node."""
    logger.info(f"🔍 Node details requested: node_id={node_id}")
    
    try:
        if backend_initialized and graph_ops:
            # Use real node details
            logger.info("🔄 Fetching real node details...")
            node_info = await graph_ops.get_node_details(node_id)
            logger.info(f"📊 Real node details retrieved for {node_id}")
            return JSONResponse(content=node_info)
        else:
            # Fallback to mock node details
            logger.warning("⚠️ Using mock node details (real backend not available)")
            
            # Mock data based on node_id
            mock_node_info = {
                "id": node_id,
                "label": f"Node {node_id}",
                "freq": 10,
                "community": 0,
                "snippets": [
                    {
                        "text": f"This is a mock snippet for node {node_id}. It contains relevant information about this concept and its usage in the knowledge base.",
                        "doc_name": "Sample Document 1"
                    },
                    {
                        "text": f"Another mock snippet related to node {node_id}. This provides additional context and examples.",
                        "doc_name": "Sample Document 2"
                    }
                ],
                "note": "Mock data - real backend not available"
            }
            return JSONResponse(content=mock_node_info)
            
    except Exception as e:
        logger.error(f"❌ Failed to get node details: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve node details")

@app.get("/search")
async def search(q: str = Query(...), k: int = Query(10)):
    """Search for relevant content."""
    logger.info(f"🔍 Search request: query='{q}', k={k}")
    
    try:
        if backend_initialized and qa_engine:
            # Use real search
            logger.info("🔄 Performing real search...")
            results = await qa_engine.search(q, k=k)
            logger.info(f"✅ Real search completed: found {len(results.get('results', []))} results")
            return JSONResponse(content=results)
        else:
            # Fallback to mock search
            logger.warning("⚠️ Using mock search (real backend not available)")
            
            results = [
                {
                    "chunk_id": "chunk_1",
                    "text": f"This is a mock search result for '{q}'. It contains relevant information that matches your query.",
                    "doc_id": "doc_1",
                    "score": 0.95
                },
                {
                    "chunk_id": "chunk_2", 
                    "text": f"Another mock search result related to '{q}'. This chunk provides additional context and information.",
                    "doc_id": "doc_2",
                    "score": 0.87
                }
            ]
            
            logger.info(f"✅ Mock search completed: found {len(results)} results")
            return JSONResponse(content={
                "query": q,
                "results": results,
                "note": "Mock data - real backend not available"
            })
            
    except Exception as e:
        logger.error(f"❌ Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# Frontend serving
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the main index.html file."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(), status_code=200)
    else:
        raise HTTPException(status_code=404, detail="Frontend not found")

# Mount static files if directory exists
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    print("Starting unified server on port 5000")
    print(f"Frontend directory: {FRONTEND_DIR}")
    uvicorn.run(app, host="0.0.0.0", port=5000)
