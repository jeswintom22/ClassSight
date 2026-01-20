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
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # OCR Settings
    OCR_LANGUAGE: str = os.getenv("OCR_LANGUAGE", "en")
    OCR_GPU: bool = os.getenv("OCR_GPU", "False").lower() == "true"
    
    # Frame Processing
    FRAME_CAPTURE_INTERVAL: int = int(os.getenv("FRAME_CAPTURE_INTERVAL", "3"))
    
    def validate(self):
        """Validate that required settings are present."""
        if not self.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set in .env file")
        return True

# Create global settings instance
settings = Settings()
