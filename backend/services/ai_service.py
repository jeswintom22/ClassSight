"""
AI Service - Provider-Agnostic LLM Wrapper

This service provides educational explanations for OCR-detected text
using any OpenAI-compatible chat completions endpoint (xAI Grok, OpenAI,
Groq, OpenRouter, DeepSeek, self-hosted, etc.).

Key Design Decisions:
- Provider configured purely via env: AI_API_KEY + AI_BASE_URL + AI_MODEL
- AI_PROVIDER env var overrides auto-detection from the base URL domain
- Educational context optimized for classroom content
- Handles math, code, and general text
- Configurable retry-with-backoff for transient failures
- Comprehensive error handling

Author: ClassSight Team
"""

import openai
from openai import AsyncOpenAI
import asyncio
import random
import time
from typing import Dict
from config import settings


class AIService:
    """
    Wrapper around any OpenAI-compatible LLM API for educational explanations.

    Usage:
        ai_service = AIService.get_instance()
        result = ai_service.explain_text("E = mc²")
    """

    _instance = None
    _client = None

    def __new__(cls):
        """Singleton pattern: only one instance of AIService exists."""
        if cls._instance is None:
            cls._instance = super(AIService, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls):
        """Get or create the AI service instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initialize AI service (only runs once due to singleton)."""
        self.provider = settings.resolve_provider()

        if AIService._client is None:
            print(
                f"[AI] Initializing provider='{self.provider}' "
                f"model='{settings.AI_MODEL}' base_url='{settings.AI_BASE_URL}'"
            )

            # The OpenAI SDK speaks to any OpenAI-compatible endpoint via base_url
            AIService._client = AsyncOpenAI(
                api_key=settings.AI_API_KEY,
                base_url=settings.AI_BASE_URL,
            )

            print("[AI] Initialized successfully")

    def is_ready(self) -> bool:
        """Check if AI service is ready to generate explanations."""
        return AIService._client is not None

    def _is_retryable(self, exc: Exception) -> bool:
        """
        Return True for transient failures worth retrying (429, 5xx, timeouts).

        Non-retryable errors (auth, invalid request, etc.) return False so the
        caller fails fast instead of wasting retries.
        """
        if isinstance(exc, (openai.APITimeoutError, openai.APIConnectionError)):
            return True
        if isinstance(exc, openai.RateLimitError):  # HTTP 429
            return True
        if isinstance(exc, openai.APIStatusError) and exc.status_code >= 500:
            return True
        return False

    async def _generate(self, prompt: str) -> str:
        """
        Call the chat completions endpoint with retry-with-backoff.

        Args:
            prompt: The prompt to send to the model

        Returns:
            The generated explanation text

        Raises:
            Exception: If generation fails after exhausting retries
        """
        max_attempts = max(1, settings.AI_RETRIES + 1)

        for attempt in range(1, max_attempts + 1):
            try:
                response = await AIService._client.chat.completions.create(
                    model=settings.AI_MODEL,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=settings.AI_MAX_TOKENS,
                    temperature=settings.AI_TEMPERATURE,
                )
                return response.choices[0].message.content if response.choices else "Unable to generate explanation."
            except Exception as e:
                if attempt < max_attempts and self._is_retryable(e):
                    delay = (2 ** (attempt - 1)) + random.uniform(0, 0.5)
                    print(
                        f"[AI] Attempt {attempt}/{max_attempts} failed "
                        f"({type(e).__name__}). Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    raise

    async def explain_text(self, text: str, context: str = "classroom") -> Dict:
        """
        Generate an educational explanation for the given text (Async).

        Args:
            text: The OCR-detected text to explain (e.g., "x² + 5x + 6 = 0")
            context: Context hint ("classroom", "math", "code", etc.)

        Returns:
            dict containing:
                - explanation: The generated educational explanation
                - input_text: Original text that was explained
                - model: Model used for generation
                - ai_provider: Provider id used for generation (openai, xai, ...)
                - processing_time: Time taken in seconds
                - success: Whether explanation was successful

        Raises:
            RuntimeError: If AI service not initialized
            Exception: If generation fails
        """
        if not self.is_ready():
            raise RuntimeError("AI service not initialized")

        if not text or not text.strip():
            return {
                "explanation": "No text provided to explain.",
                "input_text": text,
                "model": settings.AI_MODEL,
                "ai_provider": self.provider,
                "processing_time": 0.0,
                "success": False
            }

        # Check cache first
        from services.cache_service import CacheService
        cache_service = CacheService.get_instance()
        text_hash = cache_service.get_text_hash(text)
        cached_result = cache_service.get_ai_explanation(text_hash)

        if cached_result:
            print("[AI] Cache Hit!")
            return cached_result

        start_time = time.time()

        try:
            # Construct the prompt with educational context
            prompt = self._build_educational_prompt(text, context)

            # Generate explanation (ASYNC, with retry-with-backoff)
            explanation = await self._generate(prompt)

            processing_time = time.time() - start_time

            result = {
                "explanation": explanation,
                "input_text": text,
                "model": settings.AI_MODEL,
                "ai_provider": self.provider,
                "processing_time": round(processing_time, 3),
                "success": True
            }

            # Cache the result
            cache_service.set_ai_explanation(text_hash, result)

            return result

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"AI generation failed: {str(e)}"
            print(f"[ERROR] {error_msg}")

            return {
                "explanation": f"Sorry, I couldn't generate an explanation. Error: {str(e)}",
                "input_text": text,
                "model": settings.AI_MODEL,
                "ai_provider": self.provider,
                "processing_time": round(processing_time, 3),
                "success": False,
                "error": str(e)
            }

    def _build_educational_prompt(self, text: str, context: str) -> str:
        """
        Build an optimized prompt for educational explanations.

        Args:
            text: The text to explain
            context: Context hint for better explanations

        Returns:
            Formatted prompt string
        """
        system_context = """You are an intelligent teaching assistant helping students understand classroom content in real-time.
Your role is to provide clear, concise, and educational explanations.

Guidelines:
- If it's a mathematical equation or problem, explain the concept and show how to solve it step-by-step
- If it's code, explain what it does and the programming concepts involved
- If it's a formula or theory, explain the meaning and real-world applications
- If it's general text, summarize key points and clarify any complex terms
- Keep explanations student-friendly and engaging
- Use examples when helpful
- Be concise but thorough (2-4 sentences for simple content, more for complex topics)
- Keep explanations under 150 words.
"""

        user_prompt = f"""The teacher has written or shown this content:

"{text}"

Please provide a clear educational explanation that would help students understand this content."""

        # Combine system context and user prompt
        full_prompt = f"{system_context}\n\n{user_prompt}"

        return full_prompt

    async def batch_explain(self, texts: list) -> list:
        """
        Explain multiple pieces of text in batch.

        Args:
            texts: List of strings to explain

        Returns:
            List of explanation results (same format as explain_text)
        """
        results = []
        for text in texts:
            result = await self.explain_text(text)
            results.append(result)
        return results
