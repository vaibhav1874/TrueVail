#!/usr/bin/env python
import os
from dotenv import load_dotenv
import google.genai as genai

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

print(f"API Key exists: {bool(GEMINI_API_KEY)}")
print(f"google.genai attributes: {dir(genai)}")

# Check what's available
print(f"\nClient: {genai.Client if hasattr(genai, 'Client') else 'N/A'}")
print(f"GenerativeModel: {genai.GenerativeModel if hasattr(genai, 'GenerativeModel') else 'N/A'}")

# Try with Client
if hasattr(genai, 'Client'):
    print("\nTrying with genai.Client...")
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        print(f"Client created: {client}")
    except Exception as e:
        print(f"Error: {e}")
