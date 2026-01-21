"""
Configuration Management for ClassSight

Loads environment variables and provides configuration settings
for the entire application.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # OCR Settings
    OCR_LANGUAGE: str = os.getenv("OCR_LANGUAGE", "en")
    OCR_GPU: bool = os.getenv("OCR_GPU", "False").lower() == "true"
    
    # Frame Processing
    FRAME_CAPTURE_INTERVAL: int = int(os.getenv("FRAME_CAPTURE_INTERVAL", "3"))
    
    # AI Settings (Gemini)
    AI_MODEL: str = os.getenv("AI_MODEL", "gemini-flash-latest")  # Points to latest Flash model
    AI_MAX_TOKENS: int = int(os.getenv("AI_MAX_TOKENS", "1024"))
    AI_TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.7"))
    
    def validate(self):
        """Validate that required settings are present."""
        if not self.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set in .env file")
        return True

# Create global settings instance
settings = Settings()
