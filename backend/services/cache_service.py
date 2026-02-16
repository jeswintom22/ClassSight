"""
Cache Service for ClassSight

Implements caching strategies for OCR and AI results to improve performance.
Uses TTL (Time To Live) cache to store results for a limited time.

Key Features:
- Image hash based caching for duplicate frames
- Text hash based caching for AI explanations
- Thread-safe singleton implementation

Author: ClassSight Team
"""

import hashlib
from typing import Optional, Dict, Any
from cachetools import TTLCache
from config import settings
import time

class CacheService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheService, cls).__new__(cls)
            cls._instance.ocr_cache = TTLCache(maxsize=settings.CACHE_MAX_SIZE, ttl=settings.CACHE_TTL)
            cls._instance.ai_cache = TTLCache(maxsize=settings.CACHE_MAX_SIZE, ttl=settings.CACHE_TTL)
        return cls._instance

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def initialize(self):
        """Initialize or clear caches."""
        if not settings.CACHE_ENABLED:
            print("⚠️ Caching disabled by configuration")
            return
            
        print(f"✅ Cache Service initialized (TTL: {settings.CACHE_TTL}s, Max Size: {settings.CACHE_MAX_SIZE})")

    def get_image_hash(self, image_bytes: bytes) -> str:
        """Generate a SHA-256 hash for an image."""
        return hashlib.sha256(image_bytes).hexdigest()

    def get_text_hash(self, text: str) -> str:
        """Generate a SHA-256 hash for text content."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def get_ocr_result(self, image_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached OCR result."""
        if not settings.CACHE_ENABLED:
            return None
        return self.ocr_cache.get(image_hash)

    def set_ocr_result(self, image_hash: str, result: Dict[str, Any]):
        """Cache OCR result."""
        if not settings.CACHE_ENABLED:
            return
        self.ocr_cache[image_hash] = result

    def get_ai_explanation(self, text_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached AI explanation."""
        if not settings.CACHE_ENABLED:
            return None
        return self.ai_cache.get(text_hash)

    def set_ai_explanation(self, text_hash: str, result: Dict[str, Any]):
        """Cache AI explanation."""
        if not settings.CACHE_ENABLED:
            return
        self.ai_cache[text_hash] = result

    def clear_cache(self):
        """Clear all caches."""
        self.ocr_cache.clear()
        self.ai_cache.clear()
        print("🗑️ Cache cleared")
