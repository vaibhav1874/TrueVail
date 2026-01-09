import subprocess
import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEY", "")

# Using v1 instead of v1beta
cmd = f'curl.exe -s -X POST "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={key}" -H "Content-Type: application/json" -d "{{\\\"contents\\\": [{{\\\"parts\\\":[{{\\\"text\\\":\\\"Hello\\\"}}]}}]}}"'
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print(result.stdout)
