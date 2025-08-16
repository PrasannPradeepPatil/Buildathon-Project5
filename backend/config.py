
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

# OpenAI Configuration (optional)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Embedding Configuration
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBED_DIM = int(os.getenv("EMBED_DIM", "384"))

# Data Budget
DATA_BUDGET_MB = int(os.getenv("DATA_BUDGET_MB", "100"))

# Other constants
CHUNK_SIZE = 700
CHUNK_OVERLAP = 100
URL_TIMEOUT = 30
MAX_URL_SIZE_MB = 5

def get_settings():
    """Get application settings."""
    return {
        "neo4j_uri": NEO4J_URI,
        "neo4j_username": NEO4J_USERNAME,
        "neo4j_password": NEO4J_PASSWORD,
        "openai_api_key": OPENAI_API_KEY,
        "embed_model": EMBED_MODEL,
        "embed_dim": EMBED_DIM,
        "data_budget_mb": DATA_BUDGET_MB,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "url_timeout": URL_TIMEOUT,
        "max_url_size_mb": MAX_URL_SIZE_MB
    }
