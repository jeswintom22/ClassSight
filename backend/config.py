"""
Configuration Management for ClassSight

Loads environment variables and provides configuration settings
for the entire application.

Security Features:
- API key validation on startup
- CORS configuration
- Rate limiting settings
- File upload limits
- Input validation rules

Author: ClassSight Team
"""

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    
    # ==================== API Keys ====================
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # ==================== Server Configuration ====================
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # ==================== Security Settings ====================
    
    # CORS (Cross-Origin Resource Sharing)
    # For production: Set to your specific frontend domain(s)
    # Example: CORS_ORIGINS=https://classsight.com,https://app.classsight.com
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS", 
        "http://localhost:8000,http://localhost:3000,http://127.0.0.1:8000"
    ).split(",")
    
    # For development, you can allow all origins (NOT for production!)
    CORS_ALLOW_ALL: bool = os.getenv("CORS_ALLOW_ALL", "True").lower() == "true"
    
    # ==================== Rate Limiting ====================
    
    # Enable/disable rate limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    
    # Rate limit for health/info endpoints (requests per minute)
    RATE_LIMIT_HEALTH: str = os.getenv("RATE_LIMIT_HEALTH", "60/minute")
    
    # Rate limit for OCR analysis (resource-intensive)
    RATE_LIMIT_ANALYSIS: str = os.getenv("RATE_LIMIT_ANALYSIS", "10/minute")
    
    # Rate limit for general endpoints
    RATE_LIMIT_DEFAULT: str = os.getenv("RATE_LIMIT_DEFAULT", "30/minute")
    
    # ==================== File Upload Security ====================
    
    # Maximum file upload size (in bytes)
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", str(10 * 1024 * 1024)))  # 10 MB default
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS: List[str] = [".png", ".jpg", ".jpeg", ".bmp"]
    
    # Allowed MIME types
    ALLOWED_MIME_TYPES: List[str] = ["image/png", "image/jpeg", "image/jpg", "image/bmp"]
    
    # ==================== Input Validation ====================
    
    # Maximum text field length (characters)
    MAX_TEXT_LENGTH: int = int(os.getenv("MAX_TEXT_LENGTH", "50000"))
    
    # Maximum filename length
    MAX_FILENAME_LENGTH: int = 255
    
    # ==================== OCR Settings ====================
    OCR_LANGUAGE: str = os.getenv("OCR_LANGUAGE", "en")
    OCR_GPU: bool = os.getenv("OCR_GPU", "False").lower() == "true"
    
    # ==================== Frame Processing ====================
    FRAME_CAPTURE_INTERVAL: int = int(os.getenv("FRAME_CAPTURE_INTERVAL", "3"))
    
    # ==================== AI Settings (Gemini) ====================
    AI_MODEL: str = os.getenv("AI_MODEL", "gemini-flash-latest")  # Points to latest Flash model
    AI_MAX_TOKENS: int = int(os.getenv("AI_MAX_TOKENS", "1024"))
    AI_TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.7"))
    
    def validate(self) -> bool:
        """
        Validate that required settings are present and secure.
        
        Security checks:
        - API key is set and not a placeholder
        - File size limits are reasonable
        - Rate limiting is enabled in production
        
        Returns:
            True if all validations pass
        
        Raises:
            ValueError: If critical settings are missing or insecure
        """
        # Check API key
        if not self.GEMINI_API_KEY:
            raise ValueError(
                "❌ GEMINI_API_KEY not set in .env file. "
                "Get your API key from: https://aistudio.google.com/app/apikey"
            )
        
        # Check for placeholder/example API keys (common mistake)
        if self.GEMINI_API_KEY in ["your-api-key-here", "placeholder", "example"]:
            raise ValueError(
                "❌ GEMINI_API_KEY appears to be a placeholder. "
                "Please set a valid API key in .env file."
            )
        
        # Warn if API key looks suspicious (too short)
        if len(self.GEMINI_API_KEY) < 20:
            print("⚠️  Warning: GEMINI_API_KEY seems unusually short. Please verify it's correct.")
        
        # Security: Ensure rate limiting is enabled in production
        if not self.DEBUG and not self.RATE_LIMIT_ENABLED:
            print("⚠️  Warning: Rate limiting is disabled in production mode. This is not recommended!")
        
        # Validate file size limits (prevent memory issues)
        if self.MAX_UPLOAD_SIZE > 50 * 1024 * 1024:  # 50 MB
            print(f"⚠️  Warning: MAX_UPLOAD_SIZE is very large ({self.MAX_UPLOAD_SIZE / (1024*1024):.0f}MB). "
                  "This may cause memory issues.")
        
        print("✅ Configuration validated successfully")
        return True
    
    def get_cors_origins(self) -> List[str]:
        """
        Get CORS origins based on configuration.
        
        Returns:
            List of allowed origins, or ["*"] if CORS_ALLOW_ALL is True
        """
        if self.CORS_ALLOW_ALL:
            return ["*"]
        return self.CORS_ORIGINS

# Create global settings instance
settings = Settings()
