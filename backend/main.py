"""
ClassSight Backend - Main Application Entry Point

This is the FastAPI application that orchestrates:
- Video frame processing
- OCR text extraction
- AI-powered explanations

Author: ClassSight Team
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from config import settings
from routes import analysis
import uvicorn
import os

# Initialize FastAPI app
app = FastAPI(
    title="ClassSight API",
    description="Backend for ClassSight AI Classroom Assistant",
    version="0.1.0"
)

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Mock Data (for images)
app.mount("/mock_data", StaticFiles(directory="../mock_data"), name="mock_data")

# API Health Endpoint (must be before static files mount)
@app.get("/api/health")
async def api_health():
    """
    API health check endpoint.
    Returns API status and version.
    """
    return {
        "message": "ClassSight API Running",
        "version": "0.1.0",
        "status": "healthy"
    }

# Mount API Routes
app.include_router(analysis.router, prefix="/api/ocr", tags=["OCR"])

# Mount Frontend (Static Files) - This MUST be last
# Note: This checks for the frontend folder relative to main.py
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    # Run the server
    # Access at: http://localhost:8000
    # Docs at: http://localhost:8000/docs
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload on code changes during development
    )
