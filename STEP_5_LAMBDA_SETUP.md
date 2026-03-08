# Step 5: AWS Lambda Functions Setup

**Duration**: ~3 hours  
**Prerequisites**: ECS services running, RDS/ElastiCache/DynamoDB configured

---

## 🎯 Goal
Create lightweight Lambda functions as API entry points that call your ECS services

**Architecture**:
```
API Gateway → Lambda (verify-handler) → ECS (verification-engine)
API Gateway → Lambda (history-handler) → RDS
API Gateway → Lambda (auth-handler) → RDS + Redis
```

---

## 📋 Step-by-Step Implementation

### 1. Create Lambda Execution Role

```bash
# Create trust policy
cat > lambda-trust-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
  --role-name zerotrust-lambda-role \
  --assume-role-policy-document file://lambda-trust-policy.json \
  --description "Execution role for ZeroTRUST Lambda functions" \
  --region us-east-1

# Attach AWS managed policy for VPC access
aws iam attach-role-policy \
  --role-name zerotrust-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole

# Attach AWS managed policy for basic execution
aws iam attach-role-policy \
  --role-name zerotrust-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### 2. Create Custom Lambda Policy

```bash
cat > lambda-custom-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:*:table/zerotrust-cache-tier2"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:*:secret:zerotrust/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# Attach custom policy
aws iam put-role-policy \
  --role-name zerotrust-lambda-role \
  --policy-name zerotrust-lambda-custom \
  --policy-document file://lambda-custom-policy.json

# Get role ARN
export LAMBDA_ROLE_ARN=$(aws iam get-role --role-name zerotrust-lambda-role --query 'Role.Arn' --output text)
echo "Lambda Role ARN: $LAMBDA_ROLE_ARN"
```

### 3. Create Lambda Layer for Shared Dependencies

#### Create Node.js Layer

```bash
# Create directory structure
mkdir -p lambda-layers/nodejs-deps/nodejs
cd lambda-layers/nodejs-deps/nodejs

# Create package.json
cat > package.json <<'EOF'
{
  "name": "zerotrust-lambda-deps",
  "version": "1.0.0",
  "dependencies": {
    "axios": "^1.6.0",
    "jsonwebtoken": "^9.0.2",
    "@aws-sdk/client-dynamodb": "^3.478.0",
    "@aws-sdk/util-dynamodb": "^3.478.0",
    "@aws-sdk/client-secrets-manager": "^3.478.0"
  }
}
EOF

# Install dependencies
npm install --production

# Go back and create zip
cd ..
zip -r nodejs-deps.zip nodejs/

# Upload layer
aws lambda publish-layer-version \
  --layer-name zerotrust-nodejs-deps \
  --description "Shared Node.js dependencies for ZeroTRUST Lambda functions" \
  --zip-file fileb://nodejs-deps.zip \
  --compatible-runtimes nodejs20.x \
  --region us-east-1

# Save layer ARN
export NODEJS_LAYER_ARN=<layer-version-arn-from-output>
cd ../../..
```

### 4. Create Lambda Security Group

```bash
# Create security group for Lambda functions
aws ec2 create-security-group \
  --group-name zerotrust-lambda-sg \
  --description "Security group for ZeroTRUST Lambda functions" \
  --vpc-id $VPC_ID \
  --region us-east-1

export LAMBDA_SG_ID=<security-group-id-from-output>

# Allow outbound to ECS services
aws ec2 authorize-security-group-egress \
  --group-id $LAMBDA_SG_ID \
  --protocol tcp \
  --port 8000 \
  --destination-group $ECS_SG_ID \
  --region us-east-1

# Allow outbound to RDS
aws ec2 authorize-security-group-egress \
  --group-id $LAMBDA_SG_ID \
  --protocol tcp \
  --port 5432 \
  --destination-group $RDS_SG_ID \
  --region us-east-1

# Allow outbound to Redis
aws ec2 authorize-security-group-egress \
  --group-id $LAMBDA_SG_ID \
  --protocol tcp \
  --port 6379 \
  --destination-group $REDIS_SG_ID \
  --region us-east-1

# Allow all HTTPS outbound
aws ec2 authorize-security-group-egress \
  --group-id $LAMBDA_SG_ID \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0 \
  --region us-east-1
```

### 5. Create Verify Lambda Function

#### Create function code

```bash
mkdir -p lambda-functions/verify-handler
cd lambda-functions/verify-handler

cat > index.mjs <<'EOF'
import axios from 'axios';
import { DynamoDBClient, GetItemCommand, PutItemCommand } from '@aws-sdk/client-dynamodb';
import { marshall, unmarshall } from '@aws-sdk/util-dynamodb';
import crypto from 'crypto';

const dynamodb = new DynamoDBClient({ region: process.env.AWS_REGION });
const VERIFICATION_SERVICE = process.env.VERIFICATION_SERVICE_URL;

export const handler = async (event) => {
  console.log('Event:', JSON.stringify(event));
  
  try {
    const body = JSON.parse(event.body || '{}');
    const { content, type = 'text', source = 'api' } = body;
    
    if (!content) {
      return {
        statusCode: 400,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Content is required' })
      };
    }
    
    // Generate cache key
    const cacheKey = crypto.createHash('sha256').update(content.toLowerCase()).digest('hex');
    
    // Check DynamoDB cache
    try {
      const cached = await dynamodb.send(new GetItemCommand({
        TableName: process.env.DYNAMODB_TABLE,
        Key: marshall({ claim_hash: cacheKey })
      }));
      
      if (cached.Item) {
        const item = unmarshall(cached.Item);
        console.log('Cache hit (DynamoDB)');
        return {
          statusCode: 200,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ...JSON.parse(item.result),
            cached: true,
            cache_tier: 'dynamodb'
          })
        };
      }
    } catch (err) {
      console.error('DynamoDB error:', err);
    }
    
    // Call verification service
    console.log('Calling verification service:', VERIFICATION_SERVICE);
    const response = await axios.post(`${VERIFICATION_SERVICE}/verify`, {
      content,
      type,
      source
    }, {
      timeout: 60000,
      headers: { 'Content-Type': 'application/json' }
    });
    
    const result = response.data;
    
    // Cache in DynamoDB
    try {
      await dynamodb.send(new PutItemCommand({
        TableName: process.env.DYNAMODB_TABLE,
        Item: marshall({
          claim_hash: cacheKey,
          result: JSON.stringify(result),
          cached_at: Math.floor(Date.now() / 1000),
          ttl: Math.floor(Date.now() / 1000) + 86400 // 24 hours
        })
      }));
    } catch (err) {
      console.error('Failed to cache result:', err);
    }
    
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...result,
        cached: false
      })
    };
    
  } catch (error) {
    console.error('Error:', error);
    return {
      statusCode: error.response?.status || 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        error: error.message || 'Internal server error',
        details: error.response?.data
      })
    };
  }
};
EOF

# Create package.json
cat > package.json <<'EOF'
{
  "name": "verify-handler",
  "version": "1.0.0",
  "type": "module",
  "description": "Lambda handler for claim verification"
}
EOF

# Create deployment package
zip -r verify-handler.zip index.mjs package.json

cd ../..
```

#### Deploy Verify Lambda

```bash
aws lambda create-function \
  --function-name zerotrust-verify-handler \
  --runtime nodejs20.x \
  --role $LAMBDA_ROLE_ARN \
  --handler index.handler \
  --zip-file fileb://lambda-functions/verify-handler/verify-handler.zip \
  --description "ZeroTRUST claim verification handler" \
  --timeout 120 \
  --memory-size 512 \
  --environment Variables="{
    VERIFICATION_SERVICE_URL=http://verification-engine.zerotrust.local:8000,
    DYNAMODB_TABLE=zerotrust-cache-tier2,
    AWS_REGION=us-east-1
  }" \
  --vpc-config SubnetIds=subnet-xxxxx,subnet-yyyyy,SecurityGroupIds=$LAMBDA_SG_ID \
  --layers $NODEJS_LAYER_ARN \
  --region us-east-1 \
  --tags Project=ZeroTRUST,Function=verify

# Grant API Gateway permission to invoke (will do this in Step 6)
```

### 6. Create Auth Lambda Function

```bash
mkdir -p lambda-functions/auth-handler
cd lambda-functions/auth-handler

cat > index.mjs <<'EOF'
import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';
import jwt from 'jsonwebtoken';
import crypto from 'crypto';

const secretsManager = new SecretsManagerClient({ region: process.env.AWS_REGION });

let JWT_SECRET;

async function getJwtSecret() {
  if (JWT_SECRET) return JWT_SECRET;
  
  const response = await secretsManager.send(new GetSecretValueCommand({
    SecretId: 'zerotrust/jwt-secret'
  }));
  
  JWT_SECRET = response.SecretString;
  return JWT_SECRET;
}

export const handler = async (event) => {
  console.log('Auth Event:', JSON.stringify(event));
  
  const path = event.path || event.rawPath;
  const method = event.httpMethod || event.requestContext?.http?.method;
  
  try {
    const body = JSON.parse(event.body || '{}');
    
    // Login
    if (path.includes('/login') && method === 'POST') {
      const { email, password } = body;
      
      if (!email || !password) {
        return {
          statusCode: 400,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ error: 'Email and password required' })
        };
      }
      
      // TODO: Verify credentials against RDS
      // For now, mock response
      
      const secret = await getJwtSecret();
      const token = jwt.sign(
        { sub: 'user-123', email, tier: 'free' },
        secret,
        { expiresIn: '1h' }
      );
      
      return {
        statusCode: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          access_token: token,
          token_type: 'Bearer',
          expires_in: 3600
        })
      };
    }
    
    // Register
    if (path.includes('/register') && method === 'POST') {
      const { email, password } = body;
      
      if (!email || !password) {
        return {
          statusCode: 400,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ error: 'Email and password required' })
        };
      }
      
      // TODO: Create user in RDS
      
      return {
        statusCode: 201,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: 'User registered successfully',
          user: { email, tier: 'free' }
        })
      };
    }
    
    return {
      statusCode: 404,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Not found' })
    };
    
  } catch (error) {
    console.error('Error:', error);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: error.message })
    };
  }
};
EOF

cat > package.json <<'EOF'
{
  "name": "auth-handler",
  "version": "1.0.0",
  "type": "module",
  "description": "Lambda handler for authentication"
}
EOF

zip -r auth-handler.zip index.mjs package.json

cd ../..
```

#### Deploy Auth Lambda

```bash
aws lambda create-function \
  --function-name zerotrust-auth-handler \
  --runtime nodejs20.x \
  --role $LAMBDA_ROLE_ARN \
  --handler index.handler \
  --zip-file fileb://lambda-functions/auth-handler/auth-handler.zip \
  --description "ZeroTRUST authentication handler" \
  --timeout 30 \
  --memory-size 256 \
  --environment Variables="{AWS_REGION=us-east-1}" \
  --vpc-config SubnetIds=subnet-xxxxx,subnet-yyyyy,SecurityGroupIds=$LAMBDA_SG_ID \
  --layers $NODEJS_LAYER_ARN \
  --region us-east-1 \
  --tags Project=ZeroTRUST,Function=auth
```

### 7. Create History Lambda Function

```bash
mkdir -p lambda-functions/history-handler
cd lambda-functions/history-handler

cat > index.mjs <<'EOF'
export const handler = async (event) => {
  console.log('History Event:', JSON.stringify(event));
  
  try {
    // Extract user ID from JWT (passed via authorizer context)
    const userId = event.requestContext?.authorizer?.claims?.sub;
    
    if (!userId) {
      return {
        statusCode: 401,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Unauthorized' })
      };
    }
    
    // TODO: Query RDS for user's verification history
    
    // Mock response for now
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        verifications: [],
        total: 0,
        page: 1,
        limit: 50
      })
    };
    
  } catch (error) {
    console.error('Error:', error);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: error.message })
    };
  }
};
EOF

cat > package.json <<'EOF'
{
  "name": "history-handler",
  "version": "1.0.0",
  "type": "module",
  "description": "Lambda handler for verification history"
}
EOF

zip -r history-handler.zip index.mjs package.json

cd ../..
```

#### Deploy History Lambda

```bash
aws lambda create-function \
  --function-name zerotrust-history-handler \
  --runtime nodejs20.x \
  --role $LAMBDA_ROLE_ARN \
  --handler index.handler \
  --zip-file fileb://lambda-functions/history-handler/history-handler.zip \
  --description "ZeroTRUST verification history handler" \
  --timeout 30 \
  --memory-size 256 \
  --environment Variables="{AWS_REGION=us-east-1}" \
  --vpc-config SubnetIds=subnet-xxxxx,subnet-yyyyy,SecurityGroupIds=$LAMBDA_SG_ID \
  --layers $NODEJS_LAYER_ARN \
  --region us-east-1 \
  --tags Project=ZeroTRUST,Function=history
```

### 8. Test Lambda Functions

```bash
# Test verify handler
aws lambda invoke \
  --function-name zerotrust-verify-handler \
  --payload '{"body":"{\"content\":\"Test claim\",\"type\":\"text\",\"source\":\"api\"}"}' \
  --region us-east-1 \
  response.json

cat response.json

# Test auth handler  - login
aws lambda invoke \
  --function-name zerotrust-auth-handler \
  --payload '{"path":"/auth/login","httpMethod":"POST","body":"{\"email\":\"test@test.com\",\"password\":\"test123\"}"}' \
  --region us-east-1 \
  auth-response.json

cat auth-response.json
```

### 9. Create CloudWatch Log Insights Queries

```bash
# Query Lambda errors
aws logs start-query \
  --log-group-name /aws/lambda/zerotrust-verify-handler \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /Error/ | sort @timestamp desc | limit 20'
```

---

## 🔍 Verification Checklist

- [ ] Lambda execution role created with proper permissions
- [ ] Lambda layer created with dependencies
- [ ] Security group configured for VPC access
- [ ] All Lambda functions deployed
- [ ] Functions can reach ECS services
- [ ] Functions can access RDS/ElastiCache
- [ ] CloudWatch logs working
- [ ] Test invocations successful

---

## 💰 Cost Optimization

**Lambda pricing**:
- Free tier: 1M requests/month + 400,000 GB-seconds
- After free tier: $0.20 per 1M requests
- Compute: $0.0000166667 per GB-second

**Estimated monthly cost** (10K requests/day):
- 300K requests = FREE (within tier)
- Compute (512MB, 2s avg) = FREE (within tier)

Lambda is extremely cost-effective for this use case!

---

## 🚨 Troubleshooting

### Lambda timeout
- Increase timeout (max 15 minutes)
- Check if ECS service is responding
- Verify NAT gateway for internet access

### Cannot reach ECS service
- Check security groups (Lambda SG → ECS SG)
- Verify service discovery DNS working
- Check VPC configuration

### Cold start issues
- Use provisioned concurrency (~$12/month per instance)
- Optimize package size
- Use layers for dependencies

---

**✅ Once complete, proceed to Step 6: API Gateway Setup**
