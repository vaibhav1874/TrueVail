import subprocess
import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEY", "")

cmd = f'curl.exe -s -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={key}" -H "Content-Type: application/json" -d "{{\\\"contents\\\": [{{\\\"parts\\\":[{{\\\"text\\\":\\\"Hello\\\"}}]}}]}}"'
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print(result.stdout)
