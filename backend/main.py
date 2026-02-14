"""
ClassSight Backend - Main Application Entry Point

This is the FastAPI application that orchestrates:
- Video frame processing
- OCR text extraction
- AI-powered explanations

Security Features:
- Rate limiting (IP-based)
- Security headers middleware
- CORS restrictions
- Input validation
- API key validation

Author: ClassSight Team
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from slowapi.errors import RateLimitExceeded
from config import settings
from routes import analysis
from middleware.slowapi_config import limiter, rate_limit_exceeded_handler
from middleware.security_headers import SecurityHeadersMiddleware
import uvicorn
import os

# Initialize FastAPI app
app = FastAPI(
    title="ClassSight API",
    description="Backend for ClassSight AI Classroom Assistant",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,  # Disable docs in production
    redoc_url="/redoc" if settings.DEBUG else None
)

# ==================== Security Middleware ====================

# 1. Rate Limiting (SlowAPI)
if settings.RATE_LIMIT_ENABLED:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    print("✅ Rate limiting enabled")
else:
    print("⚠️  Rate limiting disabled")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    error_msg = traceback.format_exc()
    print(f"❌ Unhandled Exception:\n{error_msg}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)}
    )

# 2. Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)
print("✅ Security headers middleware enabled")

# 3. CORS Middleware
# NOTE: Order matters! This should be added after other middleware
cors_origins = settings.get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)
if cors_origins == ["*"]:
    print("⚠️  CORS: Allowing ALL origins (development mode)")
else:
    print(f"✅ CORS: Restricted to {len(cors_origins)} origin(s)")

# ==================== Startup Event ====================

@app.on_event("startup")
async def startup_event():
    """
    Run validation and initialization on application startup.
    
    This ensures all required configuration is present before
    the application starts accepting requests.
    """
    print("\n" + "="*60)
    print("🚀 ClassSight API Starting Up")
    print("="*60)
    
    # Validate configuration (includes API key check)
    try:
        settings.validate()
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}\n")
        raise
    
    # Print security configuration
    print(f"\n🔒 Security Configuration:")
    print(f"   - Rate Limiting: {'Enabled' if settings.RATE_LIMIT_ENABLED else 'Disabled'}")
    print(f"   - Max Upload Size: {settings.MAX_UPLOAD_SIZE / (1024*1024):.1f} MB")
    print(f"   - CORS Origins: {cors_origins[:3]}{'...' if len(cors_origins) > 3 else ''}")
    print(f"   - Debug Mode: {settings.DEBUG}")
    
    print("\n✅ Startup complete - Ready to accept requests")
    print("="*60 + "\n")

# ==================== Static File Mounts ====================

# Mount Mock Data (for images)
mock_data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mock_data")
if os.path.exists(mock_data_path):
    app.mount("/mock_data", StaticFiles(directory=mock_data_path), name="mock_data")

# ==================== API Routes ====================

# Health Endpoint (with rate limiting)
@app.get("/api/health")
# @limiter.limit(settings.RATE_LIMIT_HEALTH if settings.RATE_LIMIT_ENABLED else "1000/minute")
async def api_health(request: Request):
    """
    API health check endpoint.
    Returns API status and version.
    
    Rate limit: 60 requests/minute
    """
    return {
        "message": "ClassSight API Running",
        "version": "0.1.0",
        "status": "healthy",
        "security": {
            "rate_limiting": settings.RATE_LIMIT_ENABLED,
            "cors_restricted": cors_origins != ["*"]
        }
    }

# Include OCR routes
app.include_router(analysis.router, prefix="/api/ocr", tags=["OCR"])

# ==================== Frontend Static Files ====================

# Mount Frontend (Static Files) - This MUST be last
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

# ==================== Main Entry Point ====================

if __name__ == "__main__":
    # Run the server
    # Access at: http://localhost:8000
    # Docs at: http://localhost:8000/docs
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG  # Auto-reload only in debug mode
    )
