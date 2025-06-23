from dotenv import load_dotenv
import os
import requests

# ✅ Load .env
load_dotenv()

# ✅ Check key
api_key = os.getenv("OPENROUTER_API_KEY")
print("Using key:", api_key[:10] + "..." if api_key else "Key not loaded")

# ✅ Define headers and payload
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "mistralai/mistral-7b-instruct",  # ✅ Safe public model
    "messages": [{"role": "user", "content": "What is an IP address?"}],
}

# ✅ Send request
response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers=headers,
    json=payload
)

print(response.status_code)
print(response.json())