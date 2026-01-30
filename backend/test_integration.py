"""
Integration Test for ClassSight
Tests the entire pipeline: Server -> OCR -> AI
"""

import requests
import time
import os

# Configuration
BASE_URL = "http://localhost:8000"
TEST_IMAGE_PATH = "../mock_data/sample_frames/math_equation.png"

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_server_health():
    """Test if the server is running"""
    print_section("TEST 1: Server Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"✅ Server Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Server not responding: {e}")
        return False

def test_ocr_health():
    """Test OCR service health"""
    print_section("TEST 2: OCR Service Health")
    
    try:
        response = requests.get(f"{BASE_URL}/api/ocr/health")
        data = response.json()
        print(f"✅ OCR Status: {data['status']}")
        print(f"Model Loaded: {data['model_loaded']}")
        print(f"Language: {data['language']}")
        return data['model_loaded']
    except Exception as e:
        print(f"❌ OCR service error: {e}")
        return False

def test_ocr_analysis():
    """Test OCR + AI analysis with a real image"""
    print_section("TEST 3: End-to-End OCR + AI Analysis")
    
    # Check if test image exists
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"❌ Test image not found: {TEST_IMAGE_PATH}")
        return False
    
    try:
        # Prepare the file
        with open(TEST_IMAGE_PATH, 'rb') as image_file:
            files = {'file': ('math_equation.png', image_file, 'image/png')}
            
            print(f"📤 Uploading: {TEST_IMAGE_PATH}")
            print("⏳ Processing (OCR + AI)...\n")
            
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/api/ocr/analyze", files=files)
            elapsed = time.time() - start_time
            
            if response.status_code != 200:
                print(f"❌ Request failed with status {response.status_code}")
                print(response.text)
                return False
            
            data = response.json()
            
            # Display results
            print(f"⏱️  Total Processing Time: {elapsed:.2f}s")
            print(f"\n📝 OCR Results:")
            print(f"   Success: {data['success']}")
            print(f"   Confidence: {data['confidence']*100:.1f}%")
            print(f"   Detected Text:\n")
            print(f"   {'-'*50}")
            print(f"   {data['combined_text']}")
            print(f"   {'-'*50}")
            
            if data.get('explanation'):
                print(f"\n🤖 AI Explanation ({data.get('ai_model', 'Unknown')}):")
                print(f"   {'-'*50}")
                print(f"   {data['explanation']}")
                print(f"   {'-'*50}")
            else:
                print("\n⚠️  No AI explanation generated")
            
            print(f"\n✅ End-to-End Test Passed!")
            return True
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("  CLASSSIGHT INTEGRATION TEST SUITE")
    print("="*60)
    
    # Track results
    results = {
        "Server Health": False,
        "OCR Health": False,
        "End-to-End Analysis": False
    }
    
    # Run tests
    results["Server Health"] = test_server_health()
    
    if results["Server Health"]:
        results["OCR Health"] = test_ocr_health()
        
        if results["OCR Health"]:
            results["End-to-End Analysis"] = test_ocr_analysis()
    
    # Summary
    print_section("TEST SUMMARY")
    for test, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test:30s} {status}")
    
    all_passed = all(results.values())
    print(f"\n{'='*60}")
    if all_passed:
        print(f"  🎉 ALL TESTS PASSED - ClassSight MVP is working!")
    else:
        print(f"  ⚠️  SOME TESTS FAILED - Please review errors above")
    print(f"{'='*60}\n")
    
    return all_passed

if __name__ == "__main__":
    main()
