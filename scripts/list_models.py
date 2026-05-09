import google.generativeai as genai
import os
from app.config import get_settings

settings = get_settings()
api_keys = settings.get_gemini_keys()

if api_keys:
    genai.configure(api_key=api_keys[0])
    print("Listing models...")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
    except Exception as e:
        print(f"Error: {e}")
else:
    print("No API keys found.")
