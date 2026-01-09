import requests
import json

# Test news analysis
print("Testing news analysis...")
try:
    response = requests.post(
        "http://127.0.0.1:5001/analyze",
        json={
            "text": "Scientists have discovered a new breakthrough in cancer treatment using immunotherapy.",
            "type": "news"
        }
    )
    print(f"News analysis status: {response.status_code}")
    print(f"News analysis result: {response.json()}")
except Exception as e:
    print(f"Error in news analysis: {e}")

print("\n" + "="*50 + "\n")

# Test privacy analysis
print("Testing privacy analysis...")
try:
    response = requests.post(
        "http://127.0.0.1:5001/analyze",
        json={
            "text": "My name is John Doe and my email is john.doe@example.com",
            "type": "privacy"
        }
    )
    print(f"Privacy analysis status: {response.status_code}")
    print(f"Privacy analysis result: {response.json()}")
except Exception as e:
    print(f"Error in privacy analysis: {e}")

print("\n" + "="*50 + "\n")

# Test deepfake analysis (without image data for now)
print("Testing deepfake analysis...")
try:
    response = requests.post(
        "http://127.0.0.1:5001/analyze",
        json={
            "text": "sample_image.jpg",
            "type": "deepfake"
        }
    )
    print(f"Deepfake analysis status: {response.status_code}")
    print(f"Deepfake analysis result: {response.json()}")
except Exception as e:
    print(f"Error in deepfake analysis: {e}")