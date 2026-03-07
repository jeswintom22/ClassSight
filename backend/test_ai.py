"""
AI Service Test Script

Tests Google Gemini AI on sample educational content to verify
functionality before integrating with the OCR pipeline.

Usage:
    python test_ai.py

Author: ClassSight Team
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ai_service import AIService
from config import settings


def test_ai_service():
    """Test AI service on various educational content types."""
    
    print("=" * 70)
    print("ClassSight AI Service Test Script")
    print("=" * 70)
    print(f"Model: {settings.AI_MODEL}")
    print(f"Temperature: {settings.AI_TEMPERATURE}")
    print(f"Max Tokens: {settings.AI_MAX_TOKENS}")
    print("=" * 70)
    print()
    
    # Initialize AI service
    print("Initializing AI service...")
    ai_service = AIService.get_instance()
    
    if not ai_service.is_ready():
        print("ERROR: AI service failed to initialize")
        print("   Check your GEMINI_API_KEY in .env file")
        return
    
    print("AI service ready\n")
    
    # Test cases representing different classroom scenarios
    test_cases = [
        {
            "name": "Mathematical Equation",
            "text": "Solve: x² + 5x + 6 = 0",
            "context": "math"
        },
        {
            "name": "Physics Formula",
            "text": "E = mc²",
            "context": "classroom"
        },
        {
            "name": "Python Code",
            "text": "def factorial(n):\n    if n == 0:\n        return 1\n    return n * factorial(n-1)",
            "context": "code"
        },
        {
            "name": "General Instruction",
            "text": "Photosynthesis is the process by which plants convert light energy into chemical energy",
            "context": "classroom"
        },
        {
            "name": "Chemistry Equation",
            "text": "2H₂ + O₂ → 2H₂O",
            "context": "classroom"
        }
    ]
    
    total_tests = len(test_cases)
    passed_tests = 0
    total_time = 0.0
    
    for i, test_case in enumerate(test_cases, 1):
        print("-" * 70)
        print(f"Test {i}/{total_tests}: {test_case['name']}")
        print("-" * 70)
        print(f"Input Text:")
        print(f"   {test_case['text'][:100]}{'...' if len(test_case['text']) > 100 else ''}")
        print()
        
        try:
            # Get explanation from AI
            result = ai_service.explain_text(
                text=test_case['text'],
                context=test_case['context']
            )
            
            # Display results
            if result['success']:
                print(f"Explanation Generated:")
                print(f"   {'-' * 65}")
                
                # Print explanation with proper wrapping
                explanation = result['explanation']
                for line in explanation.split('\n'):
                    if line.strip():
                        # Wrap long lines
                        words = line.split()
                        current_line = "   "
                        for word in words:
                            if len(current_line) + len(word) + 1 <= 70:
                                current_line += word + " "
                            else:
                                print(current_line)
                                current_line = "   " + word + " "
                        if current_line.strip():
                            print(current_line)
                
                print(f"   {'-' * 65}")
                print(f"   Processing Time: {result['processing_time']:.3f}s")
                print(f"   Model: {result['model']}")
                
                passed_tests += 1
                total_time += result['processing_time']
            else:
                print(f"FAILED")
                if 'error' in result:
                    print(f"   Error: {result['error']}")
        
        except Exception as e:
            print(f"ERROR: {str(e)}")
        
        print()
    
    # Summary
    print("=" * 70)
    print(f"Test Summary: {passed_tests}/{total_tests} tests passed")
    if passed_tests > 0:
        avg_time = total_time / passed_tests
        print(f"Average Response Time: {avg_time:.3f}s")
    print("=" * 70)
    
    if passed_tests == total_tests:
        print("All tests passed! AI service is working correctly.")
    elif passed_tests > 0:
        print("Some tests failed. Check API key and network connection.")
    else:
        print("All tests failed. Verify GEMINI_API_KEY in .env file.")
        print("   Get your free API key at: https://aistudio.google.com/app/apikey")


if __name__ == "__main__":
    test_ai_service()
