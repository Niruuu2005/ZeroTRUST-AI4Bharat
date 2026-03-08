import requests
import json
import os

api_url = "https://n7u8j4qzwi.execute-api.us-east-1.amazonaws.com/prod/verify"
payload = {
    "content": "The Earth is round",
    "type": "text",
    "source": "test"
}

print(f"Testing API: {api_url}")
try:
    response = requests.post(api_url, json=payload, timeout=40)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
