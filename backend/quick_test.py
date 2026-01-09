#!/usr/bin/env python
import requests
import json

tests = [
    {'text': 'Breaking: unbelievable event just happened!!!', 'type': 'news'},
    {'text': 'The user email is test@example.com and phone 555-1234', 'type': 'privacy'},
    {'text': 'suspected_deepfake_video_ai_generated.mp4', 'type': 'deepfake'},
]

for test in tests:
    print(f"REQUEST: {test}")
    try:
        r = requests.post('http://127.0.0.1:5001/analyze', json=test, timeout=15)
        print(f"STATUS: {r.status_code}")
        print(json.dumps(r.json(), indent=2))
    except Exception as e:
        print(f"ERROR: {e}")
    print("-" * 60)
