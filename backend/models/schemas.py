"""
Pydantic Data Models (Schemas) for ClassSight API

These models provide:
- Type validation for requests and responses
- Automatic API documentation
- Serialization/deserialization

Author: ClassSight Team
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional
from datetime import datetime


class TextBlock(BaseModel):
    """
    Represents a single detected text block with metadata.
    
    EasyOCR returns multiple detections per image.
    Each detection includes the text, confidence score, and bounding box coordinates.
    """
    # Pydantic v2 configuration
    model_config = ConfigDict(
        extra='forbid',  # Reject unexpected fields (security best practice)
        str_strip_whitespace=True,  # Auto-strip whitespace
        validate_assignment=True  # Validate on assignment
    )
    
    text: str = Field(
        ...,
        description="Detected text content",
        min_length=0,
        max_length=10000  # Prevent extremely long text blocks
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1)"
    )
    bounding_box: Optional[List[List[float]]] = Field(
        None, 
        description="Corner coordinates [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]",
        max_length=4  # Should be exactly 4 corners
    )
    
    @field_validator('bounding_box')
    @classmethod
    def validate_bounding_box(cls, v):
        """Validate bounding box structure."""
        if v is not None:
            if len(v) != 4:
                raise ValueError('Bounding box must have exactly 4 corners')
            for corner in v:
                if len(corner) != 2:
                    raise ValueError('Each corner must have exactly 2 coordinates (x, y)')
        return v


class OCRResponse(BaseModel):
    """
    Response model for OCR analysis endpoint.
    
    Contains all detected text, combined text, and metadata about the processing.
    """
    # Pydantic v2 configuration
    model_config = ConfigDict(
        extra='forbid',  # Reject unexpected fields
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    success: bool = Field(..., description="Whether OCR processing succeeded")
    combined_text: str = Field(
        ...,
        description="All detected text combined with newlines",
        max_length=50000  # Prevent excessively large responses
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Average confidence across all detections"
    )
    blocks: List[TextBlock] = Field(
        default_factory=list,
        description="Individual text detections",
        max_length=1000  # Prevent DoS via excessive blocks
    )
    processing_time: float = Field(
        ...,
        ge=0.0,
        description="Time taken to process (seconds)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When analysis was performed"
    )
    
    # AI Explanation Response
    explanation: Optional[str] = Field(
        None,
        description="AI-generated educational explanation",
        max_length=10000  # Reasonable limit for explanations
    )
    ai_model: Optional[str] = Field(
        None,
        description="AI model used for explanation",
        max_length=100
    )


class OCRHealthResponse(BaseModel):
    """Health check response for OCR service."""
    model_config = ConfigDict(extra='forbid')
    
    status: str = Field(
        ...,
        description="Service status: 'ready' or 'initializing'",
        pattern="^(ready|initializing)$"  # Only allow these values
    )
    model_loaded: bool = Field(..., description="Whether EasyOCR model is loaded")
    language: str = Field(
        ...,
        description="Current OCR language setting",
        max_length=10
    )


class ErrorResponse(BaseModel):
    """Standard error response format."""
    model_config = ConfigDict(extra='forbid')
    
    success: bool = False
    error: str = Field(
        ...,
        description="Error message",
        max_length=500
    )
    detail: Optional[str] = Field(
        None,
        description="Detailed error information",
        max_length=1000
    )
