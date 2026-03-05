import boto3
import sys

def check_bedrock():
    print(f"Python version: {sys.version}")
    try:
        # Initialize bedrock client
        bedrock = boto3.client(service_name='bedrock', region_name='us-east-1') # Defaulting to us-east-1
        
        print("Fetching Bedrock foundation models...")
        response = bedrock.list_foundation_models()
        
        models = response.get('modelSummaries', [])
        print(f"Successfully connected to AWS Bedrock! Found {len(models)} models.")
        
        # Print top 5 models
        for model in models[:5]:
            print(f"- {model['modelId']} ({model['providerName']})")
            
    except Exception as e:
        print("\n[!] Error connecting to AWS Bedrock.")
        print(f"Details: {e}")
        print("\nNote: Make sure you have your AWS credentials configured (run 'aws configure').")

if __name__ == "__main__":
    check_bedrock()
