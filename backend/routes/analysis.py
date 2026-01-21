"""
OCR Analysis API Routes

Endpoints for image upload and text extraction.

Routes:
- POST /api/ocr/analyze - Upload image, get OCR results
- GET /api/ocr/health - Check OCR service status

Author: ClassSight Team
"""

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from models.schemas import OCRResponse, OCRHealthResponse, ErrorResponse, TextBlock
from services.ocr_service import OCRService
from services.ai_service import AIService
from config import settings
import os
import tempfile
from datetime import datetime

# Create router for OCR endpoints
router = APIRouter()

# Initialize services (singleton)
ocr_service = OCRService.get_instance()
ai_service = AIService.get_instance()


@router.get(
    "/health",
    response_model=OCRHealthResponse,
    summary="Check OCR Service Health",
    description="Returns status of the OCR service and whether the model is loaded."
)
async def health_check():
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
        500: {"description": "OCR processing error"}
    }
)
async def analyze_image(
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
    
    # Validate file is provided
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    # Validate file type
    allowed_extensions = [".png", ".jpg", ".jpeg", ".bmp"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (max 10MB)
    # Read file content
    contents = await file.read()
    file_size_mb = len(contents) / (1024 * 1024)
    
    if file_size_mb > 10:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {file_size_mb:.2f}MB. Maximum: 10MB"
        )
    
    # Reset file pointer for processing
    await file.seek(0)
    
    try:
        # Save uploaded file temporarily
        # EasyOCR works best with file paths
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name
        
        # Process with OCR service
        result = ocr_service.extract_text(temp_path)
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        # Get AI explanation if text was found
        explanation = None
        ai_model = None
        
        if result["combined_text"] and result["combined_text"].strip():
            try:
                # Use "classroom" context by default for MVP
                ai_result = ai_service.explain_text(result["combined_text"], context="classroom")
                if ai_result["success"]:
                    explanation = ai_result["explanation"]
                    ai_model = ai_result["model"]
            except Exception as e:
                # Don't fail the whole request if AI fails
                print(f"⚠️ AI explanation failed: {str(e)}")
        
        # Build response
        response = OCRResponse(
            success=True,
            combined_text=result["combined_text"],
            confidence=result["confidence"],
            blocks=[TextBlock(**block) for block in result["blocks"]],
            explanation=explanation,
            ai_model=ai_model,
            processing_time=result["processing_time"],
            timestamp=datetime.now()
        )
        
        return response
    
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
async def ocr_info():
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
