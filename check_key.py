import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEY", "")
print(f"Key Found: {bool(key)}")
if key:
    print(f"Key Length: {len(key)}")
    print(f"Key Start: {key[:4]}")
    print(f"Key End: {key[-4:]}")
