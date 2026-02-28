import argparse
import asyncio
import httpx
import json
import time

async def verify_claim(claim: str, url: str):
    print(f"==================================================")
    print(f"🚀 Verifying: '{claim}'")
    print(f"🔗 Endpoint:  {url}")
    print(f"==================================================\n")
    
    start_time = time.time()
    
    # We use a longer timeout because the verification pipeline runs many agents
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            print("⏳ Sending request to Verification Engine... (this may take up to 20 seconds depending on LLM/search latency)")
            # The Verification Engine expects {"content": claim, "metadata": {}}
            response = await client.post(url, json={"content": claim, "metadata": {}})
            
            if response.status_code != 200:
                print(f"❌ Error: Received status code {response.status_code}")
                print(response.text)
                return
                
            data = response.json()
            elapsed = time.time() - start_time
            
            print(f"\n✅ Verification complete in {elapsed:.2f} seconds!\n")
            print("----- RESULT -----")
            print(f"Verdict:              {data.get('category', 'N/A').upper()}")
            print(f"Credibility Score:    {data.get('credibility_score', 0)}/100")
            print(f"Overall Confidence:   {data.get('confidence', 'N/A')}")
            print("\n----- SUMMARY -----")
            print(data.get('recommendation', 'N/A'))
            
            print("\n----- AGENT CONSENSUS -----")
            breakdown = data.get('agent_verdicts', {})
            for agent, result in breakdown.items():
                print(f" 🤖 {agent.ljust(15)} | Verdict: {result.get('verdict', 'N/A').ljust(12)} | Conf: {str(result.get('confidence', 'N/A'))[:4]} | Sources: {len(result.get('sources', []))}")
                
            print("\n----- TOP EVIDENCE SOURCES -----")
            sources = data.get('sources', [])
            if not sources:
                print("No sources found.")
            for i, src in enumerate(sources[:5]):
                print(f" {i+1}. [{src.get('tier', 'unknown').upper()}] {src.get('title', 'No Title')}")
                print(f"    URL: {src.get('url', 'N/A')}")
                print(f"    Snippet: {src.get('excerpt', 'N/A')[:150]}...\n")
                
        except httpx.ReadTimeout:
            print("❌ Error: Request timed out. The engine took too long to respond.")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ZeroTRUST AI Fact-Checker CLI Tester")
    parser.add_argument("claim", type=str, help="The claim text or URL to verify")
    parser.add_argument("--url", type=str, default="http://localhost:8000/verify", help="Verification Engine endpoint override")
    
    args = parser.parse_args()
    asyncio.run(verify_claim(args.claim, args.url))
