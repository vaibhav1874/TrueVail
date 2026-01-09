import os
import requests
import json
from dotenv import load_dotenv
import time

print("1. Loading env...")
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
print(f"2. Key found: {bool(GEMINI_API_KEY)}")

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
headers = {'Content-Type': 'application/json'}
data = {
    "contents": [{
        "parts": [{"text": "Hello"}]
    }]
}

print("3. Sending request...")
try:
    start = time.time()
    # Use verify=False as a last resort check
    response = requests.post(url, headers=headers, json=data, timeout=15)
    end = time.time()
    print(f"4. Received response in {end-start:.2f}s")
    print(f"Status: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
