"""
OCR Analysis API Routes

Endpoints for image upload and text extraction.

Routes:
- POST /api/ocr/analyze - Upload image, get OCR results
- GET /api/ocr/health - Check OCR service status

Author: ClassSight Team
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
from models.schemas import OCRResponse, OCRHealthResponse, ErrorResponse, TextBlock
from services.ocr_service import OCRService
from services.ai_service import AIService
from config import settings
from utils.validators import InputValidator
from middleware.slowapi_config import limiter, HEALTH_LIMIT, ANALYSIS_LIMIT, DEFAULT_LIMIT
import os
import tempfile
from datetime import datetime

# Create router for OCR endpoints
router = APIRouter()

# Initialize services (singleton)
ocr_service = OCRService.get_instance()
ai_service = AIService.get_instance()

# Initialize input validator
validator = InputValidator()


@router.get(
    "/health",
    response_model=OCRHealthResponse,
    summary="Check OCR Service Health",
    description="Returns status of the OCR service and whether the model is loaded."
)
@limiter.limit(HEALTH_LIMIT if settings.RATE_LIMIT_ENABLED else "1000/minute")
async def health_check(request: Request):
    """
    Health check endpoint for OCR service.
    
    Returns:
        OCRHealthResponse with service status
    """
    return OCRHealthResponse(
        status="ready" if ocr_service.is_ready() else "initializing",
        model_loaded=ocr_service.is_ready(),
        language=settings.OCR_LANGUAGE
    )


@router.post(
    "/analyze",
    response_model=OCRResponse,
    summary="Analyze Image with OCR",
    description="Upload an image file and receive extracted text with confidence scores.",
    responses={
        200: {"description": "Successfully extracted text from image"},
        400: {"description": "Invalid file format or missing file"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "OCR processing error"}
    }
)
@limiter.limit(ANALYSIS_LIMIT if settings.RATE_LIMIT_ENABLED else "1000/minute")
async def analyze_image(
    request: Request,
    file: UploadFile = File(..., description="Image file (PNG, JPG, JPEG)")
):
    """
    Upload an image and extract text using OCR.
    
    Args:
        file: Uploaded image file
    
    Returns:
        OCRResponse with detected text and metadata
    
    Raises:
        HTTPException: If file is invalid or OCR fails
    """
    
    # ==================== Security Validation ====================
    
    # 1. Validate file upload (extension, MIME type)
    validator.validate_file_upload(file, max_size=settings.MAX_UPLOAD_SIZE)
    
    # 2. Read file content
    contents = await file.read()
    
    # 3. Validate file content (size, magic numbers)
    # This prevents file type spoofing by checking actual file bytes
    validator.validate_file_content(contents, max_size=settings.MAX_UPLOAD_SIZE)
    
    # 4. Sanitize filename to prevent path traversal
    safe_filename = validator.sanitize_filename(file.filename)
    
    # Reset file pointer for processing
    await file.seek(0)
    
    try:
        # Save uploaded file temporarily
        # EasyOCR works best with file paths
        file_ext = os.path.splitext(safe_filename)[1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name
        
        # Calculate image hash for caching
        image_hash = cache_service.get_image_hash(contents)
        
        # Check cache
        cached_result = cache_service.get_ocr_result(image_hash)
        if cached_result:
            print("🖼️ Image Cache Hit!")
            return OCRResponse(**cached_result)
        
        # Process with OCR service (run in threadpool to avoid blocking main loop)
        result = await run_in_threadpool(ocr_service.extract_text, temp_path)
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        # Get AI explanation if text was found
        explanation = None
        ai_model = None
        
        if result["combined_text"] and result["combined_text"].strip():
            try:
                # Sanitize OCR text before sending to AI (prevent prompt injection)
                sanitized_text = validator.sanitize_text(
                    result["combined_text"],
                    max_length=settings.MAX_TEXT_LENGTH,
                    strip_html=True
                )
                
                # Use "classroom" context by default for MVP
                # AWAIT the async AI call
                ai_result = await ai_service.explain_text(sanitized_text, context="classroom")
                if ai_result["success"]:
                    explanation = ai_result["explanation"]
                    ai_model = ai_result["model"]
            except Exception as e:
                # Don't fail the whole request if AI fails
                print(f"⚠️ AI explanation failed: {str(e)}")
        
        # Build response
        response_data = {
            "success": True,
            "combined_text": result["combined_text"],
            "confidence": result["confidence"],
            "blocks": [TextBlock(**block) for block in result["blocks"]],
            "explanation": explanation,
            "ai_model": ai_model,
            "processing_time": result["processing_time"],
            "timestamp": datetime.now()
        }
        
        # Cache the successful response
        cache_service.set_ocr_result(image_hash, response_data)
        
        return OCRResponse(**response_data)
    
    except Exception as e:
        # Clean up temp file if it exists
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        
        # Return error response
        raise HTTPException(
            status_code=500,
            detail=f"OCR processing failed: {str(e)}"
        )


@router.get(
    "/",
    summary="OCR Service Info",
    description="Returns basic information about the OCR service."
)
@limiter.limit(DEFAULT_LIMIT if settings.RATE_LIMIT_ENABLED else "1000/minute")
async def ocr_info(request: Request):
    """Default OCR endpoint with service information."""
    return {
        "service": "ClassSight OCR",
        "version": "0.1.0",
        "status": "active",
        "endpoints": {
            "health": "/api/ocr/health",
            "analyze": "/api/ocr/analyze"
        }
    }
