import requests
import json

url = "http://localhost:8000/verify"
payload = {
    "content": "Pakistan was bombed by North Korea and America yesterday",
    "type": "text",
    "source": "web_portal"
}

print(f"🧪 Testing local verification engine...")
print(f"URL: {url}\n")

try:
    r = requests.post(url, json=payload, timeout=60)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"✅ SUCCESS!")
        print(f"  Score:       {data.get('credibility_score')}")
        print(f"  Category:    {data.get('category')}")
        print(f"  Confidence:  {data.get('confidence')}")
        print(f"  Cached:      {data.get('cached')}")
        print(f"  Claim Type:  {data.get('claim_type')}")
        print(f"  Agent Count: {len(data.get('agent_verdicts', {}))}")
        print(f"  Source Count:{len(data.get('sources', []))}")
        print(f"\n  Recommendation: {data.get('recommendation', '')[:200]}")
    else:
        print(f"❌ Error: {r.text}")
except Exception as e:
    print(f"❌ Exception: {e}")
