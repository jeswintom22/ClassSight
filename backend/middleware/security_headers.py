"""
Security Headers Middleware

Adds OWASP-recommended security headers to all responses.

Security Headers:
- Content-Security-Policy (CSP)
- X-Frame-Options (Clickjacking protection)
- X-Content-Type-Options (MIME sniffing prevention)
- Strict-Transport-Security (HTTPS enforcement)
- Permissions-Policy (Feature restrictions)
- X-XSS-Protection (Legacy XSS protection)

Author: ClassSight Security Team
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all HTTP responses.
    
    Follows OWASP security best practices for web applications.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and add security headers to response.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
        
        Returns:
            Response with added security headers
        """
        response = await call_next(request)
        
        # Content Security Policy (CSP)
        # Prevents XSS attacks by controlling resource loading
        # Note: Adjusted for development; tighten in production
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "img-src 'self' data: blob:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # X-Frame-Options: Prevent clickjacking attacks
        # DENY: Page cannot be displayed in a frame
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options: Prevent MIME sniffing
        # Force browser to respect declared content-type
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Strict-Transport-Security (HSTS)
        # Force HTTPS for 1 year (31536000 seconds)
        # Only enable in production with HTTPS
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Permissions-Policy (formerly Feature-Policy)
        # Restrict browser features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(self), "  # Allow camera for video capture
            "payment=(), "
            "usb=()"
        )
        
        # X-XSS-Protection (legacy, but still supported by some browsers)
        # Modern browsers rely on CSP, but this provides backward compatibility
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy: Control referrer information
        # no-referrer-when-downgrade: Default, send referrer to same security level
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
