
import google.generativeai as genai
import os
import sys
from dotenv import load_dotenv

# Force UTF-8 for output
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key found: {'Yes' if api_key else 'No'}")
print(f"Key preview: {api_key[:5]}..." if api_key else "None")

genai.configure(api_key=api_key)

models_to_test = [
    "gemini-1.5-flash",
    "gemini-2.0-flash",
    "gemini-pro",
    "gemini-1.5-pro",
    "models/gemini-1.5-flash"
]

print("\n--- Listing Available Models ---")
try:
    for m in genai.list_models():
        print(f"Found: {m.name}")
except Exception as e:
    print(f"List models failed: {e}")

print("\n--- Testing Generation ---")
for model_name in models_to_test:
    print(f"\nTesting model: {model_name}")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say 'Hello' if this works.")
        print(f"✅ SUCCESS! Response: {response.text}")
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
