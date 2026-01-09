import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
headers = {'Content-Type': 'application/json'}
data = {
    "contents": [{
        "parts": [{"text": "Hello, are you working?"}]
    }]
}

print(f"Requesting Gemini API via direct HTTP...")
try:
    response = requests.post(url, headers=headers, json=data, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
