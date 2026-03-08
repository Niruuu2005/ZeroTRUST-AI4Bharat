"""
ZeroTRUST Comprehensive System Diagnostic
Tests each component independently to find the root cause.
"""
import asyncio
import json
import os
import sys
import socket
import time

# Load env vars from .env.local
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env.local')
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            if '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

load_env()

PASS = "✅"
FAIL = "❌"
WARN = "⚠️"

def check_port(host, port, label):
    try:
        s = socket.create_connection((host, port), timeout=3)
        s.close()
        print(f"{PASS} {label} is reachable at {host}:{port}")
        return True
    except Exception as e:
        print(f"{FAIL} {label} NOT reachable at {host}:{port} — {e}")
        return False

def check_http(url, label):
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'diagnostic'})
        with urllib.request.urlopen(req, timeout=5) as r:
            body = r.read().decode()[:200]
            print(f"{PASS} {label} HTTP OK — {body[:80]}")
            return True
    except Exception as e:
        print(f"{FAIL} {label} HTTP FAILED — {e}")
        return False

def check_redis():
    try:
        import redis
        r = redis.Redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'), socket_timeout=3)
        r.ping()
        print(f"{PASS} Redis: ping OK")
        return True
    except Exception as e:
        print(f"{FAIL} Redis: {e}")
        return False

def check_database():
    try:
        import psycopg2
        url = os.environ.get('DATABASE_URL', '')
        conn = psycopg2.connect(url, connect_timeout=10)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM verifications")
        count = cur.fetchone()[0]
        conn.close()
        print(f"{PASS} Supabase DB: connected, {count} verifications in DB")
        return True
    except Exception as e:
        print(f"{FAIL} Supabase DB: {e}")
        return False

def check_bedrock():
    try:
        import boto3
        from botocore.config import Config
        client = boto3.client(
            'bedrock-runtime',
            region_name=os.environ.get('BEDROCK_REGION', 'us-east-1'),
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            config=Config(connect_timeout=5, read_timeout=15, retries={'max_attempts': 1})
        )
        model_id = os.environ.get('SENTIMENT_MODEL_ID', 'us.amazon.nova-lite-v1:0')
        t0 = time.time()
        response = client.converse(
            modelId=model_id,
            messages=[{'role': 'user', 'content': [{'text': 'Reply with just the word: OK'}]}],
            inferenceConfig={'maxTokens': 10, 'temperature': 0.1}
        )
        text = response['output']['message']['content'][0]['text']
        elapsed = round(time.time()-t0, 2)
        print(f"{PASS} Bedrock ({model_id}): '{text.strip()}' in {elapsed}s")
        return True
    except Exception as e:
        print(f"{FAIL} Bedrock: {e}")
        return False

def check_duckduckgo():
    try:
        import time
        t0 = time.time()
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text("India Chandrayaan-3 moon", max_results=3))
        elapsed = round(time.time()-t0, 2)
        print(f"{PASS} DuckDuckGo: {len(results)} results in {elapsed}s")
        return True
    except Exception as e:
        print(f"{FAIL} DuckDuckGo: {e}")
        return False

def check_s3():
    try:
        import boto3
        s3 = boto3.client(
            's3',
            region_name=os.environ.get('AWS_REGION', 'us-east-1'),
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        )
        bucket = os.environ.get('S3_MEDIA_BUCKET', 'zerotrust-media-dev')
        s3.head_bucket(Bucket=bucket)
        print(f"{PASS} S3 bucket '{bucket}': accessible")
        return True
    except Exception as e:
        print(f"{FAIL} S3: {e}")
        return False

def direct_verify_test():
    import urllib.request, urllib.error
    body = json.dumps({'content': 'The Earth is round', 'type': 'text', 'source': 'web_portal'}).encode()
    req = urllib.request.Request(
        'http://localhost:8000/verify',
        data=body, headers={'Content-Type': 'application/json'}, method='POST'
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            elapsed = round(time.time()-t0, 2)
            data = json.loads(r.read().decode())
            score = data.get('credibility_score', 'N/A')
            cat = data.get('category', 'N/A')
            src = data.get('sources_consulted', 0)
            print(f"{PASS} Verification Engine direct: score={score}, category={cat}, sources={src} in {elapsed}s")
            return True
    except urllib.error.HTTPError as e:
        elapsed = round(time.time()-t0, 2)
        err = e.read().decode()[:300]
        print(f"{FAIL} Verification Engine direct HTTP {e.code} in {elapsed}s: {err}")
        return False
    except Exception as e:
        elapsed = round(time.time()-t0, 2)
        print(f"{FAIL} Verification Engine direct FAILED in {elapsed}s: {e}")
        return False

print("=" * 60)
print("  ZeroTRUST System Diagnostic")
print("=" * 60)

print("\n--- 1. PORTS ---")
check_port('localhost', 6379, 'Redis')
check_port('localhost', 8000, 'Verification Engine')
check_port('localhost', 3000, 'API Gateway')
check_port('localhost', 5173, 'Web Portal')
check_port('localhost', 8001, 'Media Analysis')

print("\n--- 2. HTTP HEALTH CHECKS ---")
check_http('http://localhost:8000/health', 'Verification Engine /health')
check_http('http://localhost:3000/health', 'API Gateway /health')
check_http('http://localhost:8001/health', 'Media Analysis /health')

print("\n--- 3. AWS SERVICES ---")
check_s3()
check_bedrock()

print("\n--- 4. DATA LAYER ---")
check_redis()
check_database()

print("\n--- 5. DUCKDUCKGO (may take up to 8s) ---")
check_duckduckgo()

print("\n--- 6. DIRECT VERIFY TEST (up to 45s) ---")
direct_verify_test()

print("\n" + "=" * 60)
