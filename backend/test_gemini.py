#!/usr/bin/env python
import requests
import json

# Test news text analysis
print("Testing news text analysis...")
response = requests.post(
    'http://127.0.0.1:5001/analyze',
    json={'text': 'Breaking news: Scientists discover new cure for disease!', 'type': 'news'},
    timeout=20
)
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))
print("\n" + "="*60 + "\n")

# Test privacy analysis
print("Testing privacy analysis...")
response = requests.post(
    'http://127.0.0.1:5001/analyze',
    json={'text': 'My email is john@example.com and phone is 555-1234', 'type': 'privacy'},
    timeout=20
)
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))
