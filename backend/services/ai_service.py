"""
AI Service - Google Gemini Wrapper

This service provides educational explanations for OCR-detected text
using Google's Gemini API.

Key Design Decisions:
- Uses Gemini 1.5 Flash model (fast, free, excellent quality)
- Educational context optimized for classroom content
- Handles math, code, and general text
- Comprehensive error handling and retry logic

Author: ClassSight Team
"""

import google.generativeai as genai
import time
from typing import Dict, Optional
from config import settings


class AIService:
    """
    Wrapper around Google Gemini API for educational explanations.
    
    Usage:
        ai_service = AIService.get_instance()
        result = ai_service.explain_text("E = mc²")
    """
    
    _instance = None
    _model = None
    
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
        if AIService._model is None:
            print(f"Initializing Gemini AI with model: {settings.AI_MODEL}")
            
            # Configure Gemini API
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Initialize the model
            AIService._model = genai.GenerativeModel(
                model_name=settings.AI_MODEL,
                generation_config={
                    "temperature": settings.AI_TEMPERATURE,
                    "max_output_tokens": settings.AI_MAX_TOKENS,
                }
            )
            
            print("Gemini AI initialized successfully")
    
    def is_ready(self) -> bool:
        """Check if AI service is ready to generate explanations."""
        return AIService._model is not None
    
    def explain_text(self, text: str, context: str = "classroom") -> Dict:
        """
        Generate an educational explanation for the given text.
        
        Args:
            text: The OCR-detected text to explain (e.g., "x² + 5x + 6 = 0")
            context: Context hint ("classroom", "math", "code", etc.)
        
        Returns:
            dict containing:
                - explanation: The generated educational explanation
                - input_text: Original text that was explained
                - model: Model used for generation
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
                "processing_time": 0.0,
                "success": False
            }
        
        start_time = time.time()
        
        try:
            # Construct the prompt with educational context
            prompt = self._build_educational_prompt(text, context)
            
            # Generate explanation
            response = AIService._model.generate_content(prompt)
            
            # Extract the explanation text
            explanation = response.text if response.text else "Unable to generate explanation."
            
            processing_time = time.time() - start_time
            
            return {
                "explanation": explanation,
                "input_text": text,
                "model": settings.AI_MODEL,
                "processing_time": round(processing_time, 3),
                "success": True
            }
        
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"AI generation failed: {str(e)}"
            print(f"❌ {error_msg}")
            
            return {
                "explanation": f"Sorry, I couldn't generate an explanation. Error: {str(e)}",
                "input_text": text,
                "model": settings.AI_MODEL,
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
"""
        
        user_prompt = f"""The teacher has written or shown this content:

"{text}"

Please provide a clear educational explanation that would help students understand this content."""
        
        # Combine system context and user prompt
        full_prompt = f"{system_context}\n\n{user_prompt}"
        
        return full_prompt
    
    def batch_explain(self, texts: list) -> list:
        """
        Explain multiple pieces of text in batch.
        
        Args:
            texts: List of strings to explain
        
        Returns:
            List of explanation results (same format as explain_text)
        """
        results = []
        for text in texts:
            result = self.explain_text(text)
            results.append(result)
        return results
