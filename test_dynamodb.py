import boto3
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_dynamodb_connection():
    region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    
    if not access_key or not secret_key:
        print("❌ Error: AWS credentials not found in .env.local")
        return False

    print(f"Connecting to DynamoDB in {region}...")
    
    # Initialize DynamoDB client
    try:
        dynamodb = boto3.client(
            'dynamodb',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        
        table_name = 'zerotrust-claim-verifications'
        
        # 1. Describe Table
        print(f"\n[Test 1] Describing table: {table_name}")
        response = dynamodb.describe_table(TableName=table_name)
        status = response['Table']['TableStatus']
        print(f"✅ Table status: {status}")
        
        # 2. Put Item
        print(f"\n[Test 2] Putting test item...")
        test_hash = "test-hash-123456"
        ttl_value = int((datetime.now() + timedelta(hours=24)).timestamp())
        
        item = {
            'claim_hash': {'S': test_hash},
            'created_at': {'S': datetime.now().isoformat()},
            'ttl': {'N': str(ttl_value)},
            'result_json': {'S': json.dumps({"test": "success", "message": "DynamoDB setup verified"})}
        }
        
        dynamodb.put_item(TableName=table_name, Item=item)
        print("✅ Successfully put test item")
        
        # 3. Get Item
        print(f"\n[Test 3] Getting test item back...")
        response = dynamodb.get_item(
            TableName=table_name,
            Key={'claim_hash': {'S': test_hash}}
        )
        
        if 'Item' in response:
            print("✅ Successfully retrieved test item")
            print(f"Data: {response['Item']['result_json']['S']}")
        else:
            print("❌ Error: Item not found after PutItem")
            return False
            
        # 4. Delete Item (cleanup)
        print(f"\n[Test 4] Cleaning up...")
        dynamodb.delete_item(
            TableName=table_name,
            Key={'claim_hash': {'S': test_hash}}
        )
        print("✅ Successfully removed test item")
        
        print("\n" + "="*40)
        print("🚀 DYNAMODB SETUP VERIFIED SUCCESSFULLY!")
        print("="*40)
        return True

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\n💡 Troubleshooting Tip:")
        if "AccessDenied" in str(e):
            print("It looks like your IAM policy 'ZeroTrustDevPolicy' is missing some permissions.")
            print("Ensure it includes: dynamodb:DescribeTable, dynamodb:PutItem, dynamodb:GetItem, dynamodb:DeleteItem")
        return False

if __name__ == "__main__":
    test_dynamodb_connection()
