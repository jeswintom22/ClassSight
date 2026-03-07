"""
OCR Service Test Script

Tests EasyOCR on sample images to verify functionality
before integrating with the API.

Usage:
    python test_ocr.py

Author: ClassSight Team
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ocr_service import OCRService
from config import settings

def test_ocr_on_samples():
    """Test OCR on all sample images in mock_data/sample_frames/"""
    
    print("=" * 60)
    print("ClassSight OCR Test Script")
    print("=" * 60)
    print(f"OCR Language: {settings.OCR_LANGUAGE}")
    print(f"GPU Enabled: {settings.OCR_GPU}")
    print("=" * 60)
    print()
    
    # Initialize OCR service
    print("🔄 Initializing OCR service...")
    ocr_service = OCRService.get_instance()
    
    if not ocr_service.is_ready():
        print("❌ ERROR: OCR service failed to initialize")
        return
    
    print("✅ OCR service ready\n")
    
    # Path to sample images
    samples_dir = Path(__file__).parent.parent / "mock_data" / "sample_frames"
    
    if not samples_dir.exists():
        print(f"❌ ERROR: Sample directory not found: {samples_dir}")
        return
    
    # Get all image files
    image_files = list(samples_dir.glob("*.png")) + list(samples_dir.glob("*.jpg"))
    
    if not image_files:
        print(f"❌ No image files found in: {samples_dir}")
        return
    
    print(f"Found {len(image_files)} test image(s)\n")
    
    # Test each image
    total_tests = len(image_files)
    passed_tests = 0
    
    for image_path in sorted(image_files):
        print("-" * 60)
        print(f"📸 Testing: {image_path.name}")
        print("-" * 60)
        
        try:
            # Run OCR
            result = ocr_service.extract_text(str(image_path))
            
            # Display results
            print(f"   Detected Text:")
            print(f"   {'-' * 55}")
            if result["combined_text"]:
                for line in result["combined_text"].split("\n"):
                    print(f"   {line}")
            else:
                print("   (No text detected)")
            print(f"   {'-' * 55}")
            
            print(f"   Average Confidence: {result['confidence']:.2%}")
            print(f"   Processing Time: {result['processing_time']:.3f}s")
            print(f"   Text Blocks Found: {len(result['blocks'])}")
            
            # Individual blocks (if there are multiple)
            if len(result['blocks']) > 1:
                print(f"\n   Individual Detections:")
                for i, block in enumerate(result['blocks'], 1):
                    print(f"     {i}. \"{block['text']}\" (confidence: {block['confidence']:.2%})")
            
            # Success indicator
            if result['combined_text']:
                print(f"\n   ✅ PASS - Text extracted successfully")
                passed_tests += 1
            else:
                print(f"\n   ⚠️  WARNING - No text detected")
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
        
        print()
    
    # Summary
    print("=" * 60)
    print(f"Test Summary: {passed_tests}/{total_tests} tests passed")
    print("=" * 60)
    
    if passed_tests == total_tests:
        print("🎉 All tests passed!")
    elif passed_tests > 0:
        print("⚠️  Some tests failed or returned no text")
    else:
        print("❌ All tests failed")


if __name__ == "__main__":
    test_ocr_on_samples()
