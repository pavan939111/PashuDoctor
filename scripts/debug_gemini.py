import os
import sys
sys.path.append(os.path.join(os.getcwd(), "backend"))
import google.generativeai as genai
from app.config import get_settings

settings = get_settings()
api_keys = settings.get_gemini_keys()

if not api_keys:
    print("No API keys found.")
else:
    genai.configure(api_key=api_keys[0])
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
    except Exception as e:
        print(f"Error: {e}")
