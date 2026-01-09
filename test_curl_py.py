import subprocess
import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEY", "")

cmd = f'curl.exe -s -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}" -H "Content-Type: application/json" -d "{{\\\"contents\\\": [{{\\\"parts\\\":[{{\\\"text\\\":\\\"Hello\\\"}}]}}]}}"'

print("Running curl from python...")
try:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
    print("Stdout:", result.stdout)
    print("Stderr:", result.stderr)
except Exception as e:
    print("Error:", e)
