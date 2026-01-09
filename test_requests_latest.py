import os
import requests
import json
from dotenv import load_dotenv
import time

load_dotenv()
key = os.getenv("GEMINI_API_KEY", "")

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={key}"
headers = {'Content-Type': 'application/json'}
data = {"contents": [{"parts": [{"text": "Hello"}]}]}

print("Testing requests with gemini-flash-latest...")
try:
    response = requests.post(url, headers=headers, json=data, timeout=10)
    print(f"Status: {response.status_code}")
    print(response.json())
except Exception as e:
    print(f"Error: {e}")
