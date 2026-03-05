# Quick Start: Free Tier Deployment ($15/month)

**⏱️ Total Time**: 3 hours  
**💰 Total Cost**: ~$15/month (within your $100 budget!)  
**🎯 Goal**: Deploy fully functional ZeroTRUST on AWS Free Tier

---

## ✅ What You'll Get

```
✅ REST API (1M requests/month FREE)
✅ DynamoDB caching (25GB FREE)
✅ PostgreSQL database (20GB FREE)
✅ 4 microservices running on EC2 (750 hours/month FREE)
✅ Lambda functions (1M invocations FREE)
✅ CloudWatch monitoring (10 metrics FREE)
✅ S3 media storage (5GB FREE)
```

**Only AWS Bedrock costs money**: ~$15/month for AI inference

---

## 🚀 Step-by-Step Implementation

### Phase 1: Set Up Core Services (1 hour)

#### 1. Create DynamoDB Table (5 min)

```bash
# Set your AWS region
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create cache table
aws dynamodb create-table \
  --table-name ZeroTrustCache \
  --attribute-definitions AttributeName=cache_key,AttributeType=S \
  --key-schema AttributeName=cache_key,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region $AWS_REGION

# Wait for table to be active
aws dynamodb wait table-exists --table-name ZeroTrustCache

# Enable TTL for auto-cleanup (24 hours)
aws dynamodb update-time-to-live \
  --table-name ZeroTrustCache \
  --time-to-live-specification "Enabled=true,AttributeName=ttl"

echo "✅ DynamoDB ready!"
```

#### 2. Create RDS PostgreSQL (30 min)

```bash
# Create security group for database
aws ec2 create-security-group \
  --group-name zerotrust-db-sg \
  --description "Security group for ZeroTRUST RDS" \
  --vpc-id <your-vpc-id>

export DB_SG=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=zerotrust-db-sg" \
  --query 'SecurityGroups[0].GroupId' \
  --output text)

# Allow PostgreSQL access from anywhere (for testing - restrict in production!)
aws ec2 authorize-security-group-ingress \
  --group-id $DB_SG \
  --protocol tcp \
  --port 5432 \
  --cidr 0.0.0.0/0

# Create RDS instance (FREE TIER - db.t3.micro)
aws rds create-db-instance \
  --db-instance-identifier zerotrust-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.4 \
  --master-username zerotrust_admin \
  --master-user-password "ChangeThisPassword123!" \
  --allocated-storage 20 \
  --storage-type gp2 \
  --vpc-security-group-ids $DB_SG \
  --backup-retention-period 7 \
  --no-multi-az \
  --publicly-accessible \
  --region $AWS_REGION

# Wait for DB to be available (~10 minutes)
echo "⏳ Waiting for RDS to be ready (this takes ~10 min)..."
aws rds wait db-instance-available --db-instance-identifier zerotrust-db

# Get DB endpoint
export DB_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier zerotrust-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text)

echo "✅ RDS ready at: $DB_ENDPOINT"
```

#### 3. Import Existing Data from Supabase (10 min)

```bash
# Export from Supabase
pg_dump $SUPABASE_URL > zerotrust_backup.sql

# Import to RDS
psql "postgresql://zerotrust_admin:ChangeThisPassword123!@$DB_ENDPOINT:5432/postgres" \
  < zerotrust_backup.sql

echo "✅ Data migrated!"
```

#### 4. Set Up S3 Bucket (5 min)

```bash
# Create S3 bucket (if not exists)
aws s3 mb s3://zerotrust-media-dev --region $AWS_REGION

# Enable CORS for browser uploads
aws s3api put-bucket-cors \
  --bucket zerotrust-media-dev \
  --cors-configuration file://cors.json

cat > cors.json <<'EOF'
{
  "CORSRules": [{
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3000
  }]
}
EOF

echo "✅ S3 bucket ready!"
```

---

### Phase 2: Deploy Application (1 hour)

#### 5. Launch EC2 Instance with Docker (30 min)

```bash
# Create security group for EC2
aws ec2 create-security-group \
  --group-name zerotrust-app-sg \
  --description "Security group for ZeroTRUST application" \
  --vpc-id <your-vpc-id>

export APP_SG=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=zerotrust-app-sg" \
  --query 'SecurityGroups[0].GroupId' \
  --output text)

# Allow HTTP/HTTPS and app ports
aws ec2 authorize-security-group-ingress --group-id $APP_SG --protocol tcp --port 22 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $APP_SG --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $APP_SG --protocol tcp --port 443 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $APP_SG --protocol tcp --port 8000 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $APP_SG --protocol tcp --port 8001 --cidr 0.0.0.0/0

# Create EC2 launch script
cat > ec2-userdata.sh <<EOF
#!/bin/bash
set -e

# Install Docker
yum update -y
yum install -y docker git
service docker start
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create app directory
mkdir -p /opt/zerotrust
cd /opt/zerotrust

# Create docker-compose file
cat > docker-compose.yml <<'COMPOSE'
version: '3.8'

services:
  verification-engine:
    image: public.ecr.aws/your-account/zerotrust-verification-engine:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://zerotrust_admin:ChangeThisPassword123!@$DB_ENDPOINT:5432/zerotrust_db
      - DYNAMODB_TABLE=ZeroTrustCache
      - AWS_REGION=$AWS_REGION
      - AWS_BEDROCK_ENABLED=true
    restart: always

  media-analysis:
    image: public.ecr.aws/your-account/zerotrust-media-analysis:latest
    ports:
      - "8001:8001"
    environment:
      - S3_BUCKET=zerotrust-media-dev
      - AWS_REGION=$AWS_REGION
    restart: always
COMPOSE

# Start services
docker-compose up -d

echo "✅ Services started!"
EOF

# Launch EC2 instance (FREE TIER - t3.micro)
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.micro \
  --security-group-ids $APP_SG \
  --user-data file://ec2-userdata.sh \
  --iam-instance-profile Name=ZeroTrustEC2Role \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=zerotrust-app}]' \
  --region $AWS_REGION

# Get instance ID
export INSTANCE_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=zerotrust-app" "Name=instance-state-name,Values=running" \
  --query 'Reservations[0].Instances[0].InstanceId' \
  --output text)

# Wait for instance
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get public IP
export EC2_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "✅ EC2 instance ready at: $EC2_IP"
echo "Services will be available at:"
echo "  - Verification Engine: http://$EC2_IP:8000"
echo "  - Media Analysis: http://$EC2_IP:8001"
```

#### 6. Create IAM Role for EC2 (10 min)

```bash
# Create trust policy
cat > ec2-trust-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "ec2.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

# Create role
aws iam create-role \
  --role-name ZeroTrustEC2Role \
  --assume-role-policy-document file://ec2-trust-policy.json

# Attach policies
aws iam attach-role-policy \
  --role-name ZeroTrustEC2Role \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

aws iam attach-role-policy \
  --role-name ZeroTrustEC2Role \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

aws iam attach-role-policy \
  --role-name ZeroTrustEC2Role \
  --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess

# Create instance profile
aws iam create-instance-profile --instance-profile-name ZeroTrustEC2Role
aws iam add-role-to-instance-profile --instance-profile-name ZeroTrustEC2Role --role-name ZeroTrustEC2Role

echo "✅ IAM role ready!"
```

---

### Phase 3: Create Serverless API (1 hour)

#### 7. Create Lambda Functions (30 min)

```bash
# Create Lambda execution role
cat > lambda-trust-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

aws iam create-role \
  --role-name ZeroTrustLambdaRole \
  --assume-role-policy-document file://lambda-trust-policy.json

# Attach policies
aws iam attach-role-policy \
  --role-name ZeroTrustLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy \
  --role-name ZeroTrustLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

export LAMBDA_ROLE_ARN=$(aws iam get-role --role-name ZeroTrustLambdaRole --query 'Role.Arn' --output text)

# Create verify handler
mkdir -p lambda-functions/verify
cd lambda-functions/verify

cat > index.mjs <<'EOF'
import { DynamoDBClient, GetItemCommand, PutItemCommand } from '@aws-sdk/client-dynamodb';
import { marshall, unmarshall } from '@aws-sdk/util-dynamodb';
import crypto from 'crypto';

const dynamodb = new DynamoDBClient({ region: process.env.AWS_REGION });

export const handler = async (event) => {
  const body = JSON.parse(event.body);
  const cacheKey = crypto.createHash('sha256').update(body.content).digest('hex');
  
  try {
    // Check cache
    const cached = await dynamodb.send(new GetItemCommand({
      TableName: 'ZeroTrustCache',
      Key: marshall({ cache_key: cacheKey })
    }));
    
    if (cached.Item) {
      return {
        statusCode: 200,
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify({
          ...unmarshall(cached.Item).result,
          cached: true
        })
      };
    }
    
    // Call EC2 service
    const response = await fetch(\`http://\${process.env.EC2_IP}:8000/verify\`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    
    const result = await response.json();
    
    // Store in cache
    await dynamodb.send(new PutItemCommand({
      TableName: 'ZeroTrustCache',
      Item: marshall({
        cache_key: cacheKey,
        result: result,
        ttl: Math.floor(Date.now() / 1000) + 86400
      })
    }));
    
    return {
      statusCode: 200,
      headers: { 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ ...result, cached: false })
    };
  } catch (error) {
    return {
      statusCode: 500,
      headers: { 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ error: error.message })
    };
  }
};
EOF

cat > package.json <<'EOF'
{
  "name": "verify-handler",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {
    "@aws-sdk/client-dynamodb": "^3.x",
    "@aws-sdk/util-dynamodb": "^3.x"
  }
}
EOF

npm install
zip -r function.zip .

# Deploy Lambda
aws lambda create-function \
  --function-name zerotrust-verify \
  --runtime nodejs20.x \
  --role $LAMBDA_ROLE_ARN \
  --handler index.handler \
  --zip-file fileb://function.zip \
  --timeout 30 \
  --memory-size 256 \
  --environment Variables="{AWS_REGION=$AWS_REGION,EC2_IP=$EC2_IP}"

cd ../..
echo "✅ Lambda function deployed!"
```

#### 8. Create API Gateway (20 min)

```bash
# Create REST API
export API_ID=$(aws apigateway create-rest-api \
  --name zerotrust-api \
  --description "ZeroTRUST Free Tier API" \
  --endpoint-configuration types=REGIONAL \
  --query 'id' \
  --output text)

# Get root resource
export ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query 'items[0].id' \
  --output text)

# Create /verify resource
export VERIFY_RESOURCE=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part verify \
  --query 'id' \
  --output text)

# Create POST method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $VERIFY_RESOURCE \
  --http-method POST \
  --authorization-type NONE

# Integrate with Lambda
export LAMBDA_ARN=$(aws lambda get-function \
  --function-name zerotrust-verify \
  --query 'Configuration.FunctionArn' \
  --output text)

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $VERIFY_RESOURCE \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:$AWS_REGION:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations"

# Grant permission
aws lambda add-permission \
  --function-name zerotrust-verify \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$AWS_REGION:$AWS_ACCOUNT_ID:$API_ID/*/*/verify"

# Deploy API
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod

export API_URL="https://$API_ID.execute-api.$AWS_REGION.amazonaws.com/prod"
echo "✅ API Gateway ready at: $API_URL"
```

---

### Phase 4: Test & Monitor (30 min)

#### 9. Test the Complete System

```bash
# Test API
curl -X POST $API_URL/verify \
  -H "Content-Type: application/json" \
  -d '{"content":"The Earth is round","type":"text","source":"test"}'

# Should return verification result with "cached":false first time
# Run again - should return "cached":true from DynamoDB

echo "✅ System is working!"
```

#### 10. Set Up Cost Alerts

```bash
# Create SNS topic for alerts
export SNS_ARN=$(aws sns create-topic \
  --name zerotrust-billing-alerts \
  --query 'TopicArn' \
  --output text)

# Subscribe your email
aws sns subscribe \
  --topic-arn $SNS_ARN \
  --protocol email \
  --notification-endpoint your-email@example.com

# Create billing alarm (alert at $20)
aws cloudwatch put-metric-alarm \
  --alarm-name zerotrust-cost-alert \
  --alarm-description "Alert if cost exceeds $20" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --evaluation-periods 1 \
  --threshold 20 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions $SNS_ARN \
  --dimensions Name=Currency,Value=USD

echo "✅ Cost alerts configured!"
```

---

## 🎉 You're Done!

### Your Infrastructure:
- ✅ API Gateway: `$API_URL`
- ✅ EC2 Services: `http://$EC2_IP:8000` (verification), `http://$EC2_IP:8001` (media)
- ✅ DynamoDB: ZeroTrustCache
- ✅ RDS: zerotrust-db
- ✅ S3: zerotrust-media-dev

### Update Your Web Portal

```bash
# Update .env file
cat > apps/web-portal/.env <<EOF
VITE_API_URL=$API_URL
EOF

# Build and deploy
npm run build
# Deploy to S3 + CloudFront or Vercel
```

---

## 📊 Cost Monitoring

Check your costs:
```bash
# Current month costs
aws ce get-cost-and-usage \
  --time-period Start=2026-03-01,End=2026-03-03 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE
```

---

## 🆘 Troubleshooting

### Lambda can't reach EC2
- Check security group allows inbound on ports 8000, 8001
- Verify EC2 is running: `aws ec2 describe-instances --instance-ids $INSTANCE_ID`

### RDS connection failed
- Check security group allows port 5432
- Verify password is correct
- Check DB is publicly accessible

### DynamoDB throttling
- Increase provisioned capacity or keep on-demand mode
- Within free tier (25 RCU/WCU) you should be fine

---

**🎊 Congratulations! You now have a fully functional ZeroTRUST platform costing only ~$15/month!**
