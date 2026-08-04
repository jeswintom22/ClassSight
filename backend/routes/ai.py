"""
AI Provider Info Routes

Exposes the currently configured AI provider (any OpenAI-compatible endpoint)
for health checks and debugging.

Routes:
- GET /api/ai/info - Return active AI provider, model, and endpoint

Author: ClassSight Team
"""

from fastapi import APIRouter, Request, Response
from models.schemas import AIInfoResponse
from config import settings
from middleware.slowapi_config import limiter, DEFAULT_LIMIT

# Create router for AI endpoints
router = APIRouter()


@router.get(
    "/info",
    response_model=AIInfoResponse,
    summary="Get Active AI Provider Info",
    description="Returns the currently configured AI provider, model, and endpoint.",
    responses={
        200: {"description": "AI provider configuration"},
        429: {"description": "Rate limit exceeded"}
    }
)
@limiter.limit(DEFAULT_LIMIT if settings.RATE_LIMIT_ENABLED else "1000/minute")
async def ai_info(request: Request, response: Response):
    """
    Return the currently configured AI provider configuration.

    Args:
        request: FastAPI request (used by rate limiter)
        response: FastAPI response (required by slowapi to inject rate-limit headers)

    Returns:
        AIInfoResponse with provider id, display name, model, base URL,
        retry count, and whether the config is complete.
    """
    return AIInfoResponse(
        provider=settings.resolve_provider(),
        provider_name=settings.provider_display_name(),
        model=settings.AI_MODEL,
        base_url=settings.AI_BASE_URL,
        retries=settings.AI_RETRIES,
        configured=settings.ai_config_complete(),
    )
