import requests
import time

# Wait a moment for the server to be ready
time.sleep(2)

try:
    r = requests.post('http://127.0.0.1:5000/analyze', json={'text': 'This is a test'})
    print("Status Code:", r.status_code)
    print("Response:", r.json())
except Exception as e:
    print(f"Error: {e}")