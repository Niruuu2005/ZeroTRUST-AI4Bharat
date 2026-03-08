#!/usr/bin/env python3
import os, sys, boto3
from dotenv import load_dotenv

load_dotenv('.env.local')

# Testing models that usually avoid the strict Marketplace/Anthropic payment check
TEST_MODELS = [
    ('us.amazon.nova-pro-v1:0', 'Amazon Nova Pro'),
    ('us.amazon.nova-lite-v1:0', 'Amazon Nova Lite'),
    ('us.mistral.mistral-large-2402-v1:0', 'Mistral Large 2402'),
    ('us.mistral.pixtral-large-2502-v1:0', 'Mistral Pixtral'),
    ('us.meta.llama3-2-3b-instruct-v1:0', 'Llama 3.2 3B'),
]

print("\nScanning for working alternatives...")
client = boto3.client('bedrock-runtime', region_name='us-east-1')

for model_id, label in TEST_MODELS:
    sys.stdout.write(f"  {label} ({model_id}) ... ")
    sys.stdout.flush()
    try:
        client.converse(
            modelId=model_id,
            messages=[{'role': 'user', 'content': [{'text': 'hi'}]}],
            inferenceConfig={'maxTokens': 5}
        )
        print("WORKS ✅")
    except Exception as e:
        print(f"FAILED ❌ ({str(e)[:50]}...)")
