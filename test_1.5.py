import os
from dotenv import load_dotenv
import google.genai as genai

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

client = genai.Client(api_key=GEMINI_API_KEY)

print("Trying gemini-1.5-flash...")
try:
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents="Hello, identify yourself."
    )
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
