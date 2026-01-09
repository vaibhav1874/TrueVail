import subprocess
import os
import json
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEY", "")

cmd = f'curl.exe -s "https://generativelanguage.googleapis.com/v1beta/models?key={key}"'
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
try:
    data = json.loads(result.stdout)
    model_names = [m['name'] for m in data.get('models', [])]
    print("\n".join(model_names))
except:
    print(result.stdout)
