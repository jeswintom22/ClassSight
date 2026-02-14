"""
Input Validation and Sanitization Utilities

Provides comprehensive validation and sanitization for all user inputs
following OWASP best practices.

Key Features:
- File validation (type, size, content)
- Text sanitization (XSS prevention)
- Path traversal prevention
- Size limit enforcement
- Magic number verification

Author: ClassSight Security Team
"""

import magic
import bleach
import re
import os
from typing import Optional, List, Dict, Any
from fastapi import UploadFile, HTTPException


# Allowed file types for upload (MIME types)
ALLOWED_IMAGE_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/bmp"
}

# Magic number signatures for image validation
# Prevents file extension spoofing
IMAGE_MAGIC_NUMBERS = {
    b'\x89PNG\r\n\x1a\n': 'image/png',
    b'\xFF\xD8\xFF': 'image/jpeg',
    b'BM': 'image/bmp'
}

# File size limits (in bytes)
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_TEXT_LENGTH = 50000  # 50K characters for text fields

# Dangerous file extensions to reject
FORBIDDEN_EXTENSIONS = {
    '.exe', '.bat', '.cmd', '.sh', '.ps1', '.vbs', '.js', '.jar',
    '.scr', '.msi', '.app', '.deb', '.rpm', '.dmg', '.pkg'
}


class InputValidator:
    """Comprehensive input validation and sanitization."""
    
    @staticmethod
    def validate_file_upload(file: UploadFile, max_size: int = MAX_IMAGE_SIZE) -> Dict[str, Any]:
        """
        Validate uploaded file for security threats.
        
        Checks:
        - File extension against forbidden list
        - File size limits
        - MIME type validation
        - Magic number verification (prevents spoofing)
        
        Args:
            file: FastAPI UploadFile object
            max_size: Maximum allowed file size in bytes
        
        Returns:
            Dict with validation results
        
        Raises:
            HTTPException: If file fails validation
        """
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # 1. Check file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext in FORBIDDEN_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Forbidden file type: {file_ext}"
            )
        
        # 2. Validate allowed image extensions
        allowed_exts = ['.png', '.jpg', '.jpeg', '.bmp']
        if file_ext not in allowed_exts:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file extension: {file_ext}. Allowed: {', '.join(allowed_exts)}"
            )
        
        # 3. Validate MIME type from content-type header
        content_type = file.content_type
        if content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid content type: {content_type}. Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}"
            )
        
        return {
            "valid": True,
            "filename": file.filename,
            "extension": file_ext,
            "content_type": content_type
        }
    
    @staticmethod
    def validate_file_content(file_bytes: bytes, max_size: int = MAX_IMAGE_SIZE) -> Dict[str, Any]:
        """
        Validate file content using magic numbers.
        
        Prevents file type spoofing by checking actual file content,
        not just the extension.
        
        Args:
            file_bytes: Raw file bytes
            max_size: Maximum allowed size
        
        Returns:
            Dict with validation results
        
        Raises:
            HTTPException: If content is invalid
        """
        # 1. Check file size
        file_size = len(file_bytes)
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {file_size / (1024*1024):.2f}MB. Maximum: {max_size / (1024*1024):.0f}MB"
            )
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        # 2. Verify magic numbers (file signature)
        detected_type = None
        for magic_bytes, mime_type in IMAGE_MAGIC_NUMBERS.items():
            if file_bytes.startswith(magic_bytes):
                detected_type = mime_type
                break
        
        if not detected_type:
            # Fallback to python-magic for more comprehensive detection
            try:
                detected_type = magic.from_buffer(file_bytes, mime=True)
            except Exception:
                detected_type = None
        
        if detected_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file content. Expected image, detected: {detected_type or 'unknown'}"
            )
        
        return {
            "valid": True,
            "size": file_size,
            "detected_type": detected_type
        }
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = MAX_TEXT_LENGTH, strip_html: bool = True) -> str:
        """
        Sanitize text input to prevent XSS and injection attacks.
        
        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length
            strip_html: Whether to strip all HTML tags
        
        Returns:
            Sanitized text
        
        Raises:
            HTTPException: If text exceeds max length
        """
        if not text:
            return ""
        
        # 1. Length validation
        if len(text) > max_length:
            raise HTTPException(
                status_code=400,
                detail=f"Text too long: {len(text)} characters. Maximum: {max_length}"
            )
        
        # 2. Remove HTML tags to prevent XSS
        if strip_html:
            # Use bleach to strip all HTML
            text = bleach.clean(text, tags=[], strip=True)
        
        # 3. Normalize whitespace
        text = " ".join(text.split())
        
        return text
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal attacks.
        
        Removes:
        - Path separators (/, \\)
        - Parent directory references (..)
        - Special characters
        
        Args:
            filename: Original filename
        
        Returns:
            Sanitized filename
        """
        if not filename:
            return "unnamed_file"
        
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove dangerous characters
        # Allow only alphanumeric, dash, underscore, dot
        filename = re.sub(r'[^a-zA-Z0-9\-_\.]', '_', filename)
        
        # Remove leading dots (hidden files)
        filename = filename.lstrip('.')
        
        # Ensure not empty after sanitization
        if not filename:
            filename = "unnamed_file"
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext
        
        return filename
    
    @staticmethod
    def validate_positive_number(value: Any, field_name: str = "value") -> float:
        """
        Validate that a value is a positive number.
        
        Args:
            value: Value to validate
            field_name: Name of the field (for error messages)
        
        Returns:
            Validated number
        
        Raises:
            HTTPException: If invalid
        """
        try:
            num = float(value)
            if num <= 0:
                raise ValueError("Must be positive")
            return num
        except (ValueError, TypeError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid {field_name}: must be a positive number"
            )
