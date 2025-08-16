
#!/usr/bin/env python3
"""
Universal Knowledge-Graph Builder
Run script for the FastAPI application
"""

import uvicorn
from backend.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
