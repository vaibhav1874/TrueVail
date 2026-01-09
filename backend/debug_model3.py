#!/usr/bin/env python
import os
from dotenv import load_dotenv
import google.genai as genai

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

client = genai.Client(api_key=GEMINI_API_KEY)

# Check available methods
print("Client methods:")
print([m for m in dir(client) if not m.startswith('_')])

# Check for models method
if hasattr(client, 'models'):
    print("\nModels attribute available")
    print(f"client.models: {client.models}")
    
if hasattr(client, 'chats'):
    print("\nChats attribute available")
    print(f"client.chats methods: {[m for m in dir(client.chats) if not m.startswith('_')]}")

# Try generating content
print("\nTrying to generate content...")
try:
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Hello"
    )
    print(f"Response: {response.text[:50]}")
except Exception as e:
    print(f"Error with models.generate_content: {e}")

# Try chat
try:
    chat = client.chats.create(model="gemini-2.0-flash")
    response = chat.send_message("Hello")
    print(f"Chat Response: {response.text[:50]}")
except Exception as e:
    print(f"Error with chat: {e}")
