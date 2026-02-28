#!/usr/bin/env python3
"""
Test script for AWS Bedrock and External API configuration
Validates: Requirements 1.1, 1.2, 2.1, 2.2, 2.3

This script tests:
1. AWS credentials are properly configured
2. Bedrock models are accessible (Claude 3.5 Sonnet, Claude 3 Haiku, Mistral Large)
3. External API keys are configured (optional but recommended)
4. Each Bedrock model can be invoked successfully
"""

import os
import sys
import json
import asyncio
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'verification-engine'))

try:
    import boto3
    from botocore.config import Config
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Missing required package: {e}")
    print("Install with: pip install boto3 python-dotenv")
    sys.exit(1)

# Load environment variables
load_dotenv('.env.local')

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text: str):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}⚠ {text}{RESET}")


def print_info(text: str):
    """Print info message"""
    print(f"  {text}")


def check_aws_credentials() -> Tuple[bool, str]:
    """Check if AWS credentials are configured"""
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    if not access_key:
        return False, "AWS_ACCESS_KEY_ID not found in .env.local"
    if not secret_key:
        return False, "AWS_SECRET_ACCESS_KEY not found in .env.local"
    
    # Mask credentials for display
    masked_access = access_key[:4] + '*' * (len(access_key) - 8) + access_key[-4:]
    masked_secret = secret_key[:4] + '*' * (len(secret_key) - 8) + secret_key[-4:]
    
    return True, f"AWS_ACCESS_KEY_ID: {masked_access}\n  AWS_SECRET_ACCESS_KEY: {masked_secret}\n  AWS_DEFAULT_REGION: {region}"


def check_external_api_keys() -> Dict[str, bool]:
    """Check which external API keys are configured"""
    api_keys = {
        'NEWS_API_KEY': os.getenv('NEWS_API_KEY'),
        'GNEWS_API_KEY': os.getenv('GNEWS_API_KEY'),
        'GOOGLE_SEARCH_KEY': os.getenv('GOOGLE_SEARCH_KEY'),
        'GOOGLE_SEARCH_ENGINE_ID': os.getenv('GOOGLE_SEARCH_ENGINE_ID'),
        'TWITTER_BEARER_TOKEN': os.getenv('TWITTER_BEARER_TOKEN'),
        'REDDIT_CLIENT_ID': os.getenv('REDDIT_CLIENT_ID'),
        'REDDIT_CLIENT_SECRET': os.getenv('REDDIT_CLIENT_SECRET'),
    }
    
    return {key: bool(value and value.strip()) for key, value in api_keys.items()}


async def test_bedrock_model(client, model_id: str, model_name: str) -> Tuple[bool, str]:
    """Test a specific Bedrock model"""
    try:
        response = client.converse(
            modelId=model_id,
            messages=[{
                'role': 'user',
                'content': [{'text': 'Respond with exactly: "Model test successful"'}]
            }],
            inferenceConfig={'maxTokens': 50, 'temperature': 0.1}
        )
        
        text = response['output']['message']['content'][0]['text']
        return True, f"Response: {text[:100]}"
        
    except client.exceptions.ResourceNotFoundException:
        return False, "Model not found or not enabled in AWS Console"
    except client.exceptions.AccessDeniedException:
        return False, "Access denied - check IAM permissions for Bedrock"
    except client.exceptions.ThrottlingException:
        return False, "Throttled - too many requests"
    except Exception as e:
        return False, f"Error: {str(e)[:100]}"


async def test_all_bedrock_models():
    """Test all Bedrock models in the fallback chain"""
    print_header("Testing AWS Bedrock Models")
    
    # Check credentials first
    creds_ok, creds_msg = check_aws_credentials()
    if not creds_ok:
        print_error(f"AWS Credentials: {creds_msg}")
        return False
    
    print_success("AWS Credentials configured")
    print_info(creds_msg)
    
    # Initialize Bedrock client
    try:
        client = boto3.client(
            'bedrock-runtime',
            region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
            config=Config(
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                connect_timeout=5,
                read_timeout=60,
            )
        )
        print_success("Bedrock client initialized")
    except Exception as e:
        print_error(f"Failed to initialize Bedrock client: {e}")
        return False
    
    # Test each model
    models = [
        ('anthropic.claude-3-5-sonnet-20241022-v2:0', 'Claude 3.5 Sonnet'),
        ('anthropic.claude-3-5-haiku-20241022-v1:0', 'Claude 3 Haiku'),
        ('mistral.mistral-large-2407-v1:0', 'Mistral Large'),
    ]
    
    all_passed = True
    for model_id, model_name in models:
        print(f"\nTesting {model_name}...")
        success, message = await test_bedrock_model(client, model_id, model_name)
        
        if success:
            print_success(f"{model_name}: {message}")
        else:
            print_error(f"{model_name}: {message}")
            all_passed = False
    
    return all_passed


def test_external_apis():
    """Test external API configuration"""
    print_header("Checking External API Keys")
    
    api_status = check_external_api_keys()
    
    # Required APIs for comprehensive verification
    required_apis = ['NEWS_API_KEY', 'GNEWS_API_KEY']
    optional_apis = [
        'GOOGLE_SEARCH_KEY', 'GOOGLE_SEARCH_ENGINE_ID',
        'TWITTER_BEARER_TOKEN', 'REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET'
    ]
    
    all_configured = True
    
    print("Required APIs (for news verification):")
    for api in required_apis:
        if api_status[api]:
            print_success(f"{api}: Configured")
        else:
            print_warning(f"{api}: Not configured (system will use RSS feeds)")
            all_configured = False
    
    print("\nOptional APIs (for enhanced verification):")
    for api in optional_apis:
        if api_status[api]:
            print_success(f"{api}: Configured")
        else:
            print_info(f"{api}: Not configured (optional)")
    
    # Count configured APIs
    configured_count = sum(api_status.values())
    total_count = len(api_status)
    
    print(f"\n{BLUE}Summary: {configured_count}/{total_count} API keys configured{RESET}")
    
    if configured_count == 0:
        print_warning("No external API keys configured. System will use free sources only.")
        print_info("This may limit source diversity and verification accuracy.")
    elif configured_count < 4:
        print_warning("Limited API keys configured. Consider adding more for better coverage.")
    else:
        print_success("Good API coverage for comprehensive verification!")
    
    return all_configured


def print_configuration_summary():
    """Print a summary of the configuration status"""
    print_header("Configuration Summary")
    
    print("To enable Bedrock models in AWS Console:")
    print_info("1. Go to AWS Console → Bedrock → Model access")
    print_info("2. Click 'Manage model access'")
    print_info("3. Enable the following models:")
    print_info("   - Claude 3.5 Sonnet v2")
    print_info("   - Claude 3 Haiku")
    print_info("   - Mistral Large")
    print_info("4. Wait for access to be granted (usually instant)")
    
    print("\nTo configure external API keys:")
    print_info("1. Edit .env.local file")
    print_info("2. Add your API keys for the services you want to use")
    print_info("3. Restart the verification engine")
    
    print("\nAPI Key Resources:")
    print_info("- NewsAPI: https://newsapi.org/")
    print_info("- GNews: https://gnews.io/")
    print_info("- Google Custom Search: https://developers.google.com/custom-search")
    print_info("- Twitter API: https://developer.twitter.com/")
    print_info("- Reddit API: https://www.reddit.com/prefs/apps")


async def main():
    """Main test function"""
    print(f"\n{BLUE}╔═══════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BLUE}║  AWS Bedrock & External API Configuration Test           ║{RESET}")
    print(f"{BLUE}║  Task 1: Configure AWS Bedrock and External APIs         ║{RESET}")
    print(f"{BLUE}╚═══════════════════════════════════════════════════════════╝{RESET}")
    
    # Test Bedrock
    bedrock_ok = await test_all_bedrock_models()
    
    # Test external APIs
    apis_ok = test_external_apis()
    
    # Print configuration guide
    print_configuration_summary()
    
    # Final summary
    print_header("Test Results")
    
    if bedrock_ok:
        print_success("AWS Bedrock: All models accessible ✓")
    else:
        print_error("AWS Bedrock: Some models failed ✗")
        print_info("Check AWS Console → Bedrock → Model access")
    
    if apis_ok:
        print_success("External APIs: All required APIs configured ✓")
    else:
        print_warning("External APIs: Some APIs not configured (system will use fallbacks)")
    
    print()
    
    # Exit code
    if bedrock_ok:
        print(f"{GREEN}✓ Configuration test PASSED{RESET}")
        print_info("AWS Bedrock is properly configured and all models are accessible")
        return 0
    else:
        print(f"{RED}✗ Configuration test FAILED{RESET}")
        print_info("Please fix the issues above and run the test again")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
