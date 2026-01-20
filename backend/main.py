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
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="ClassSight API",
    description="AI-powered classroom content capture and explanation system",
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

# Root endpoint - Health check
@app.get("/")
async def root():
    """
    Health check endpoint.
    Returns API status and version.
    """
    return {
        "message": "ClassSight API Running",
        "version": "0.1.0",
        "status": "healthy"
    }

# Additional route imports will go here
# from routes import video, analysis

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
