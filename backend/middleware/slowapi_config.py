"""
Rate Limiting Middleware using SlowAPI

Implements IP-based and user-based rate limiting following OWASP best practices.

Key Features:
- Per-IP rate limiting to prevent DDoS attacks
- Configurable limits per endpoint type
- Graceful 429 responses with Retry-After headers
- Request tracking and logging

Author: ClassSight Security Team
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import time


def get_identifier(request: Request) -> str:
    """
    Get a unique identifier for rate limiting.
    
    Priority:
    1. User ID (if authenticated) - for future user-based limiting
    2. IP address (current implementation)
    
    Args:
        request: FastAPI request object
    
    Returns:
        Unique identifier string for rate limiting
    """
    # For future: Check if user is authenticated
    # user_id = request.state.user_id if hasattr(request.state, 'user_id') else None
    # if user_id:
    #     return f"user:{user_id}"
    
    try:
        # Default to IP-based limiting
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Use the first IP in the chain (client IP)
            ip = forwarded.split(",")[0].strip()
        else:
            # Fallback to remote address
            ip = get_remote_address(request)
            
        # Fallback if IP is still None (e.g. test client)
        if not ip:
            ip = "127.0.0.1"
            
        return f"ip:{ip}"
    except Exception as e:
        # Fallback for safety
        print(f"⚠️ Rate limiting error: {str(e)}")
        return "ip:unknown"


# Initialize limiter with custom key function
limiter = Limiter(
    key_func=get_identifier,
    default_limits=["30/minute"],  # Default: 30 requests per minute
    headers_enabled=True,           # Include rate limit headers in response
    storage_uri="memory://",        # In-memory storage (for production, use Redis)
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.
    
    Returns a 429 Too Many Requests response with:
    - Clear error message
    - Retry-After header
    - Rate limit information
    
    Args:
        request: FastAPI request object
        exc: RateLimitExceeded exception
    
    Returns:
        JSONResponse with 429 status code
    """
    # Parse the retry time from the exception
    retry_after = int(exc.detail.split("after ")[1].split(" ")[0]) if "after" in exc.detail else 60
    
    response = JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": "Rate limit exceeded",
            "detail": "Too many requests. Please try again later.",
            "retry_after_seconds": retry_after,
            "limit": str(exc.detail) if hasattr(exc, 'detail') else "Rate limit exceeded"
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": request.headers.get("X-RateLimit-Limit", "Unknown"),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(int(time.time()) + retry_after)
        }
    )
    
    return response


# Rate limit configurations for different endpoint types
# OWASP recommended limits based on resource intensity

# Health/info endpoints: High limit (non-resource intensive)
HEALTH_LIMIT = "60/minute"

# Analysis endpoints: Low limit (resource-intensive: OCR + AI)
ANALYSIS_LIMIT = "10/minute"

# Upload endpoints: Medium limit
UPLOAD_LIMIT = "20/minute"

# Default for general endpoints
DEFAULT_LIMIT = "30/minute"
