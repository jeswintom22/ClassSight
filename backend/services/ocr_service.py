"""
OCR Service - EasyOCR Wrapper

This service provides text extraction from images using EasyOCR.

Key Design Decisions:
- Singleton pattern: EasyOCR reader is expensive to initialize (~3-5 seconds)
- Only initialized once and reused across all requests
- GPU disabled by default for compatibility (can enable in .env)

Author: ClassSight Team
"""

import easyocr
import time
from typing import List, Tuple
from PIL import Image
import numpy as np
from config import settings


class OCRService:
    """
    Wrapper around EasyOCR for text extraction from images.
    
    Usage:
        ocr_service = OCRService.get_instance()
        result = ocr_service.extract_text("path/to/image.png")
    """
    
    _instance = None
    _reader = None
    
    def __new__(cls):
        """Singleton pattern: only one instance of OCRService exists."""
        if cls._instance is None:
            cls._instance = super(OCRService, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        """Get or create the OCR service instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Initialize OCR service (only runs once due to singleton)."""
        if OCRService._reader is None:
            print(f"🔄 Initializing EasyOCR with language: {settings.OCR_LANGUAGE}")
            print(f"   GPU enabled: {settings.OCR_GPU}")
            
            try:
                # Initialize EasyOCR reader
                # This downloads models on first run (~500MB)
                OCRService._reader = easyocr.Reader(
                    [settings.OCR_LANGUAGE],  # Languages to detect (default: English)
                    gpu=settings.OCR_GPU       # Use GPU if available (default: False)
                )
                print("✅ EasyOCR model loaded successfully")
            except Exception as e:
                print(f"❌ Failed to load EasyOCR model: {e}")
                OCRService._reader = None
    
    def is_ready(self) -> bool:
        """Check if OCR service is ready to process images."""
        return OCRService._reader is not None
    
    def extract_text(self, image_path: str) -> dict:
        """
        Extract text from an image file.
        
        Args:
            image_path: Path to the image file (PNG, JPG, etc.)
        
        Returns:
            dict containing:
                - combined_text: All detected text joined with newlines
                - confidence: Average confidence score
                - blocks: List of individual text detections
                - processing_time: Time taken in seconds
        
        Raises:
            FileNotFoundError: If image file doesn't exist
            Exception: If OCR processing fails
        """
        if not self.is_ready():
            raise RuntimeError("OCR service not initialized")
        
        start_time = time.time()
        
        try:
            # Preprocess image (resize if too large)
            image_np = self._preprocess_image(image_path)
            
            # Read and process the image
            # EasyOCR accepts: file path, numpy array, or PIL Image
            results = OCRService._reader.readtext(image_np)
            
            # EasyOCR returns: List of (bounding_box, text, confidence)
            # Example: [([[10, 10], [100, 10], [100, 50], [10, 50]], 'Hello', 0.95), ...]
            
            blocks = []
            all_text = []
            confidences = []
            
            for detection in results:
                bounding_box, text, confidence = detection
                
                blocks.append({
                    "text": text,
                    "confidence": float(confidence),
                    "bounding_box": [[int(p) for p in point] for point in bounding_box]  # Ensure native ints
                })
                
                all_text.append(text)
                confidences.append(confidence)
            
            # Calculate average confidence
            avg_confidence = float(sum(confidences) / len(confidences)) if confidences else 0.0
            
            # Combine all text with newlines
            combined_text = "\n".join(all_text)
            
            processing_time = time.time() - start_time
            
            return {
                "combined_text": combined_text,
                "confidence": round(avg_confidence, 3),
                "blocks": blocks,
                "processing_time": round(processing_time, 3)
            }
        
        except FileNotFoundError:
            raise FileNotFoundError(f"Image not found: {image_path}")
        except Exception as e:
            raise Exception(f"OCR processing failed: {str(e)}")
    
    def extract_text_from_bytes(self, image_bytes: bytes) -> dict:
        """
        Extract text from image bytes (useful for uploaded files).
        
        Args:
            image_bytes: Raw image data as bytes
        
        Returns:
            Same format as extract_text()
        """
        if not self.is_ready():
            raise RuntimeError("OCR service not initialized")
        
        start_time = time.time()
        
        try:
            print(f"🔍 OCR Processing: Received {len(image_bytes)} bytes")
            
            # Preprocess image bytes (resize/convert)
            image_np = self._preprocess_image(io.BytesIO(image_bytes))
            print(f"   Image shape: {image_np.shape}")
            
            # Process with EasyOCR
            results = OCRService._reader.readtext(image_np)
            print(f"   OCR raw results: {len(results)} blocks detected")
            
            blocks = []
            all_text = []
            confidences = []
            
            for detection in results:
                bounding_box, text, confidence = detection
                # print(f"   - Detected: '{text}' ({confidence:.2f})") # Verbose logging
                
                # Ensure bounding box is a list of lists of native ints (not numpy ints)
                safe_box = [[int(coord) for coord in point] for point in bounding_box]
                
                blocks.append({
                    "text": text,
                    "confidence": float(confidence),
                    "bounding_box": safe_box
                })
                
                all_text.append(text)
                confidences.append(confidence)
            
            avg_confidence = float(sum(confidences) / len(confidences)) if confidences else 0.0
            combined_text = "\n".join(all_text)
            processing_time = time.time() - start_time
            
            print(f"✅ OCR Complete: {len(all_text)} lines, Avg Conf: {avg_confidence:.2f}, Time: {processing_time:.2f}s")
            
            return {
                "combined_text": combined_text,
                "confidence": round(avg_confidence, 3),
                "blocks": blocks,
                "processing_time": round(processing_time, 3)
            }
        
        except Exception as e:
            raise Exception(f"OCR processing failed: {str(e)}")



    def _preprocess_image(self, image_source) -> np.ndarray:
        """
        Preprocess image for better performance:
        - Resize if too large (max 1024px width/height)
        - Convert to grayscale if needed (skip for now as EasyOCR handles color)
        """
        try:
            if isinstance(image_source, str):
                img = Image.open(image_source)
            elif isinstance(image_source, np.ndarray):
                return image_source # Already numpy array
            else:
                # Assume bytes or stream
                 img = Image.open(image_source)

            # Max dimension
            MAX_DIM = 1024
            if img.width > MAX_DIM or img.height > MAX_DIM:
                img.thumbnail((MAX_DIM, MAX_DIM), Image.Resampling.LANCZOS)
            
            return np.array(img)
            
        except Exception as e:
            print(f"⚠️ Image preprocessing failed: {e}")
            # Fallback to loading directly
            if isinstance(image_source, str):
                 return np.array(Image.open(image_source))
            return np.array(image_source)

# Import io for bytes processing
import io

