"""
Pydantic Data Models (Schemas) for ClassSight API

These models provide:
- Type validation for requests and responses
- Automatic API documentation
- Serialization/deserialization

Author: ClassSight Team
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class TextBlock(BaseModel):
    """
    Represents a single detected text block with metadata.
    
    EasyOCR returns multiple detections per image.
    Each detection includes the text, confidence score, and bounding box coordinates.
    """
    text: str = Field(..., description="Detected text content")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    bounding_box: Optional[List[List[float]]] = Field(
        None, 
        description="Corner coordinates [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]"
    )


class OCRResponse(BaseModel):
    """
    Response model for OCR analysis endpoint.
    
    Contains all detected text, combined text, and metadata about the processing.
    """
    success: bool = Field(..., description="Whether OCR processing succeeded")
    combined_text: str = Field(..., description="All detected text combined with newlines")
    confidence: float = Field(..., description="Average confidence across all detections")
    blocks: List[TextBlock] = Field(default_factory=list, description="Individual text detections")
    processing_time: float = Field(..., description="Time taken to process (seconds)")
    timestamp: datetime = Field(default_factory=datetime.now, description="When analysis was performed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "combined_text": "x² + 5x + 6 = 0",
                "confidence": 0.92,
                "blocks": [
                    {
                        "text": "x² + 5x + 6 = 0",
                        "confidence": 0.92,
                        "bounding_box": [[10, 10], [200, 10], [200, 50], [10, 50]]
                    }
                ],
                "processing_time": 0.45,
                "timestamp": "2026-01-21T06:00:00"
            }
        }


class OCRHealthResponse(BaseModel):
    """Health check response for OCR service."""
    status: str = Field(..., description="Service status: 'ready' or 'initializing'")
    model_loaded: bool = Field(..., description="Whether EasyOCR model is loaded")
    language: str = Field(..., description="Current OCR language setting")


class ErrorResponse(BaseModel):
    """Standard error response format."""
    success: bool = False
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
