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

# Friendly display names for known OpenAI-compatible providers (UI badge)
PROVIDER_DISPLAY_NAMES = {
    "openai": "OpenAI",
    "xai": "xAI",
    "groq": "Groq",
    "openrouter": "OpenRouter",
    "deepseek": "DeepSeek",
    "together": "Together",
    "mistral": "Mistral",
    "custom": "Custom",
}

class Settings:
    """Application settings loaded from environment variables."""
    
    # ==================== API Keys ====================
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    
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
    
    # ==================== AI Settings (any OpenAI-compatible provider) ====================
    # Generic keys: point AI_BASE_URL at any OpenAI-compatible /chat/completions endpoint.
    AI_BASE_URL: str = os.getenv("AI_BASE_URL", "")
    AI_MODEL: str = os.getenv("AI_MODEL", "")  # Required - no default
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "")  # Optional override (openai|xai|groq|...)
    AI_MAX_TOKENS: int = int(os.getenv("AI_MAX_TOKENS", "1024"))
    AI_TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.7"))
    AI_RETRIES: int = max(0, min(int(os.getenv("AI_RETRIES", "2")), 10))  # Clamped 0-10

    # ==================== Caching Settings ====================
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "True").lower() == "true"
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes
    CACHE_MAX_SIZE: int = int(os.getenv("CACHE_MAX_SIZE", "1000"))

    # ==================== WebSocket Settings ====================
    WS_HEARTBEAT_INTERVAL: int = int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))
    # Optional shared secret; when set, clients must connect with ?token=<WS_AUTH_TOKEN>
    WS_AUTH_TOKEN: str = os.getenv("WS_AUTH_TOKEN", "")
    WS_MAX_CONNECTIONS_PER_IP: int = int(os.getenv("WS_MAX_CONNECTIONS_PER_IP", "3"))
    # Minimum seconds between frames on one connection (frontend captures every >= 3s)
    WS_MIN_FRAME_INTERVAL: float = float(os.getenv("WS_MIN_FRAME_INTERVAL", "1.0"))
    WS_MAX_FRAMES_PER_MINUTE: int = int(os.getenv("WS_MAX_FRAMES_PER_MINUTE", "30"))

    # ==================== Auto-Capture Settings ====================
    AUTO_CAPTURE_INTERVAL: int = int(os.getenv("AUTO_CAPTURE_INTERVAL", "5"))
    
    # ==================== AI Provider Resolution ====================

    def resolve_provider(self) -> str:
        """
        Resolve the active AI provider id.
        
        Priority:
        1. AI_PROVIDER env var (explicit override) wins
        2. Auto-detect from known domain fragments in AI_BASE_URL
        3. Fall back to 'custom'
        
        Returns:
            Provider id string (openai, xai, groq, openrouter, deepseek,
            together, mistral, custom)
        """
        if self.AI_PROVIDER:
            return self.AI_PROVIDER.strip().lower()
        
        base_url = self.AI_BASE_URL.lower()
        if "api.openai.com" in base_url:
            return "openai"
        if "api.x.ai" in base_url:
            return "xai"
        if "api.groq.com" in base_url:
            return "groq"
        if "openrouter.ai" in base_url:
            return "openrouter"
        if "api.deepseek.com" in base_url:
            return "deepseek"
        if "api.together.xyz" in base_url:
            return "together"
        if "api.mistral.ai" in base_url:
            return "mistral"
        return "custom"

    def provider_display_name(self) -> str:
        """Get the friendly display name for the active provider (for UI badges)."""
        return PROVIDER_DISPLAY_NAMES.get(self.resolve_provider(), "Custom")

    def ai_config_complete(self) -> bool:
        """Whether all required AI config (key, base URL, model) is present."""
        return bool(self.AI_API_KEY and self.AI_BASE_URL and self.AI_MODEL)

    def validate(self) -> bool:
        """
        Validate that required settings are present and secure.
        
        Security checks:
        - AI API key, base URL, and model are set and not placeholders
        - File size limits are reasonable
        - Rate limiting is enabled in production
        
        Returns:
            True if all validations pass
        
        Raises:
            ValueError: If critical settings are missing or insecure
        """
        # Check AI API key
        if not self.AI_API_KEY:
            raise ValueError(
                "❌ AI_API_KEY not set in .env file. "
                "Get an API key from your AI provider "
                "(e.g. https://console.x.ai or https://platform.openai.com)."
            )
        
        # Check AI base URL
        if not self.AI_BASE_URL:
            raise ValueError(
                "❌ AI_BASE_URL not set in .env file. "
                "e.g. https://api.x.ai/v1 or https://api.openai.com/v1"
            )
        
        # Check AI model (required - no default)
        if not self.AI_MODEL:
            raise ValueError(
                "❌ AI_MODEL not set in .env file. "
                "e.g. grok-3, gpt-4o-mini, llama-3.3-70b-versatile"
            )
        
        # Legacy GROK_API_KEY migration hint
        if os.getenv("GROK_API_KEY"):
            raise ValueError(
                "❌ GROK_API_KEY is no longer supported. "
                "Set AI_API_KEY, AI_BASE_URL (e.g. https://api.x.ai/v1) "
                "and AI_MODEL instead."
            )
        
        # Check for placeholder/example API keys (common mistake)
        if self.AI_API_KEY in ["your-api-key-here", "your-xai-api-key-here", "placeholder", "example"]:
            raise ValueError(
                "❌ AI_API_KEY appears to be a placeholder. "
                "Please set a valid API key in .env file."
            )
        
        # Warn if API key looks suspicious (too short)
        if len(self.AI_API_KEY) < 20:
            print("⚠️  Warning: AI_API_KEY seems unusually short. Please verify it's correct.")
        
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
