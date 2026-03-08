#!/usr/bin/env python3
"""Quick sequential model test - clean output, no async issues."""
import os, sys, boto3
from dotenv import load_dotenv

load_dotenv('.env.local')

MODELS = [
    (os.getenv('MANAGER_MODEL_ID',   'us.anthropic.claude-3-7-sonnet-20250219-v1:0'), 'Claude 3.7 Sonnet  (Manager)'),
    (os.getenv('SENTIMENT_MODEL_ID', 'us.anthropic.claude-3-5-haiku-20241022-v1:0'),  'Claude 3.5 Haiku   (Sentiment)'),
    (os.getenv('RESEARCH_MODEL_ID',  'us.mistral.pixtral-large-2502-v1:0'),           'Mistral Pixtral    (Research)'),
]

print("\n" + "="*60)
print("  ZeroTRUST — Bedrock Model Connectivity Check")
print("="*60)

client = boto3.client('bedrock-runtime', region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'))
all_ok = True

for model_id, label in MODELS:
    sys.stdout.write(f"  Testing {label} ... ")
    sys.stdout.flush()
    try:
        resp = client.converse(
            modelId=model_id,
            messages=[{'role': 'user', 'content': [{'text': 'Reply with: OK'}]}],
            inferenceConfig={'maxTokens': 10, 'temperature': 0.1}
        )
        reply = resp['output']['message']['content'][0]['text']
        print(f"PASS  ({reply.strip()[:30]})")
    except Exception as e:
        short = str(e)[:90]
        print(f"FAIL\n    -> {short}")
        all_ok = False

print("="*60)
if all_ok:
    print("  All models PASSED. Bedrock is fully operational!")
else:
    print("  One or more models FAILED. See errors above.")
print("="*60 + "\n")
sys.exit(0 if all_ok else 1)
