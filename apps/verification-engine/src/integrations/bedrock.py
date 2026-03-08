"""
AWS Bedrock integration — Claude 3.5 Sonnet + fallback chain
"""
import os
import json
import logging
from typing import Optional

import boto3
from botocore.config import Config

logger = logging.getLogger(__name__)

_bedrock_client = None

MODEL_CONFIGS = {
    'manager': {
        'modelId': os.getenv('MANAGER_MODEL_ID', 'us.amazon.nova-pro-v1:0'),
        'inferenceConfig': {'maxTokens': 4096, 'temperature': 0.3, 'topP': 0.9}
    },
    'research': {
        'modelId': os.getenv('RESEARCH_MODEL_ID', 'us.mistral.pixtral-large-2502-v1:0'),
        'inferenceConfig': {'maxTokens': 2048, 'temperature': 0.4, 'topP': 0.85}
    },
    'sentiment': {
        'modelId': os.getenv('SENTIMENT_MODEL_ID', 'us.amazon.nova-lite-v1:0'),
        'inferenceConfig': {'maxTokens': 1024, 'temperature': 0.2}
    },
}

FALLBACK_CHAIN = [
    os.getenv('MANAGER_MODEL_ID', 'us.amazon.nova-pro-v1:0'),
    os.getenv('SENTIMENT_MODEL_ID', 'us.amazon.nova-lite-v1:0'),
    os.getenv('RESEARCH_MODEL_ID', 'us.mistral.pixtral-large-2502-v1:0'),
]


def get_bedrock_client():
    global _bedrock_client
    if _bedrock_client is None:
        try:
            _bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name=os.getenv('BEDROCK_REGION', 'us-east-1'),
                config=Config(
                    retries={'max_attempts': 3, 'mode': 'adaptive'},
                    connect_timeout=5,
                    read_timeout=60,
                )
            )
        except Exception as e:
            logger.warning(f"Bedrock client init failed: {e}")
    return _bedrock_client


async def invoke_bedrock(config_key: str, prompt: str) -> str:
    """Call Bedrock with model fallback chain. Returns text response."""
    client = get_bedrock_client()
    if client is None:
        return _mock_response(config_key, prompt)

    cfg = MODEL_CONFIGS.get(config_key, MODEL_CONFIGS['manager'])
    model_ids = [cfg['modelId']] + [m for m in FALLBACK_CHAIN if m != cfg['modelId']]

    for model_id in model_ids:
        try:
            response = client.converse(
                modelId=model_id,
                messages=[{'role': 'user', 'content': [{'text': prompt}]}],
                inferenceConfig=cfg.get('inferenceConfig', {'maxTokens': 4096, 'temperature': 0.3}),
            )
            return response['output']['message']['content'][0]['text']
        except client.exceptions.ThrottlingException:
            logger.warning(f"Bedrock throttled on {model_id}, trying fallback")
            continue
        except client.exceptions.ModelNotReadyException:
            logger.warning(f"Model {model_id} not ready, trying fallback")
            continue
        except Exception as e:
            err_msg = str(e).lower()
            if 'validationexception' in err_msg or 'not supported' in err_msg or 'invalid' in err_msg:
                logger.warning(f"Bedrock model/config issue on {model_id}: {e}")
            else:
                logger.error(f"Bedrock error on {model_id}: {e}")
            if model_id == model_ids[-1]:
                # Return mock so pipeline completes when Bedrock is misconfigured or unavailable
                return _mock_response(config_key, prompt)
            continue

    return _mock_response(config_key, prompt)


def _mock_response(config_key: str, prompt: str) -> str:
    """Mock response when Bedrock is unavailable (local dev without AWS)."""
    claim_text = "mock claim"
    for line in prompt.split('\n'):
        if line.startswith('Claim:'):
            claim_text = line.replace('Claim:', '').strip()
            break

    if 'domain' in prompt.lower() or 'analyze' in prompt.lower():
        return json.dumps({
            "main_assertion": claim_text,
            "entities": [w for w in claim_text.split() if len(w)>4][:3] if claim_text else ["mock_entity"],
            "type": "factual",
            "domain": "general",
            "verification_scope": "General claim verification"
        })
        
    if 'propaganda' in prompt.lower() or 'emotional' in prompt.lower():
        return json.dumps({
            "manipulation_score": 0.2,
            "techniques": [],
            "is_emotional": False,
            "summary": "Mock sentiment analysis. No strong manipulation detected.",
            "evidence": {"supporting": 0, "contradicting": 0, "neutral": 1}
        })

    # For verdict prompts
    if 'Sources:' in prompt and len(prompt.split('Sources:')[1].strip()) > 10:
        return json.dumps({
            "verdict": "mixed",
            "confidence": 0.5,
            "summary": "Mock verdict based on found sources using local fallback.",
            "evidence": {"supporting": 1, "contradicting": 0, "neutral": 2}
        })
        
    return json.dumps({
        "verdict": "insufficient",
        "confidence": 0.0,
        "summary": "Bedrock unavailable — add AWS credentials to .env.local",
        "evidence": {"supporting": 0, "contradicting": 0, "neutral": 0}
    })
