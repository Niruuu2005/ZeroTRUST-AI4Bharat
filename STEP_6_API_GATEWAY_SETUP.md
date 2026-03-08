# Step 6: Amazon API Gateway Setup

**Duration**: ~2 hours  
**Prerequisites**: Lambda functions deployed and tested

---

## 🎯 Goal
Create AWS API Gateway (REST API) to replace Express.js API, routing requests to Lambda functions

**Final Architecture**:
```
Client → API Gateway → Lambda → ECS/RDS
```

---

## 📋 Step-by-Step Implementation

### 1. Create REST API

```bash
# Create REST API
aws apigateway create-rest-api \
  --name zerotrust-api \
  --description "ZeroTRUST Fact Verification API - Serverless" \
  --endpoint-configuration types=REGIONAL \
  --region us-east-1 \
  --tags Project=ZeroTRUST,Environment=production

# Save API ID
export API_ID=<api-id-from-output>
echo "API ID: $API_ID"

# Get root resource ID
export ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --region us-east-1 \
  --query 'items[0].id' \
  --output text)

echo "Root Resource ID: $ROOT_ID"
```

### 2. Create API Resources

```bash
# Create /verify resource
aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part verify \
  --region us-east-1

export VERIFY_RESOURCE_ID=<resource-id-from-output>

# Create /auth resource
aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part auth \
  --region us-east-1

export AUTH_RESOURCE_ID=<resource-id-from-output>

# Create /auth/login resource
aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $AUTH_RESOURCE_ID \
  --path-part login \
  --region us-east-1

export LOGIN_RESOURCE_ID=<resource-id-from-output>

# Create /auth/register resource
aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $AUTH_RESOURCE_ID \
  --path-part register \
  --region us-east-1

export REGISTER_RESOURCE_ID=<resource-id-from-output>

# Create /history resource
aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part history \
  --region us-east-1

export HISTORY_RESOURCE_ID=<resource-id-from-output>
```

### 3. Create POST Method for /verify

```bash
# Create POST method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $VERIFY_RESOURCE_ID \
  --http-method POST \
  --authorization-type NONE \
  --request-validator-id <validator-id> \
  --region us-east-1

# Integrate with Lambda
export VERIFY_LAMBDA_ARN=$(aws lambda get-function \
  --function-name zerotrust-verify-handler \
  --query 'Configuration.FunctionArn' \
  --output text)

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $VERIFY_RESOURCE_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$VERIFY_LAMBDA_ARN/invocations" \
  --region us-east-1

# Grant API Gateway permission to invoke Lambda
aws lambda add-permission \
  --function-name zerotrust-verify-handler \
  --statement-id apigateway-invoke-verify \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:$AWS_ACCOUNT_ID:$API_ID/*/*/verify" \
  --region us-east-1
```

### 4. Enable CORS for /verify

```bash
# Add OPTIONS method for CORS preflight
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $VERIFY_RESOURCE_ID \
  --http-method OPTIONS \
  --authorization-type NONE \
  --region us-east-1

# Mock integration for OPTIONS
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $VERIFY_RESOURCE_ID \
  --http-method OPTIONS \
  --type MOCK \
  --request-templates '{"application/json":"{\"statusCode\":200}"}' \
  --region us-east-1

# Method response for OPTIONS
aws apigateway put-method-response \
  --rest-api-id $API_ID \
  --resource-id $VERIFY_RESOURCE_ID \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters '{
    "method.response.header.Access-Control-Allow-Headers": false,
    "method.response.header.Access-Control-Allow-Methods": false,
    "method.response.header.Access-Control-Allow-Origin": false
  }' \
  --region us-east-1

# Integration response for OPTIONS
aws apigateway put-integration-response \
  --rest-api-id $API_ID \
  --resource-id $VERIFY_RESOURCE_ID \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters '{
    "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''",
    "method.response.header.Access-Control-Allow-Methods": "'\''POST,OPTIONS'\''",
    "method.response.header.Access-Control-Allow-Origin": "'\''*'\''"
  }' \
  --region us-east-1
```

### 5. Create POST Methods for /auth/login and /auth/register

```bash
# Get Auth Lambda ARN
export AUTH_LAMBDA_ARN=$(aws lambda get-function \
  --function-name zerotrust-auth-handler \
  --query 'Configuration.FunctionArn' \
  --output text)

# Create POST /auth/login
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $LOGIN_RESOURCE_ID \
  --http-method POST \
  --authorization-type NONE \
  --region us-east-1

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $LOGIN_RESOURCE_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$AUTH_LAMBDA_ARN/invocations" \
  --region us-east-1

aws lambda add-permission \
  --function-name zerotrust-auth-handler \
  --statement-id apigateway-invoke-auth-login \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:$AWS_ACCOUNT_ID:$API_ID/*/POST/auth/login" \
  --region us-east-1

# Create POST /auth/register
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $REGISTER_RESOURCE_ID \
  --http-method POST \
  --authorization-type NONE \
  --region us-east-1

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $REGISTER_RESOURCE_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$AUTH_LAMBDA_ARN/invocations" \
  --region us-east-1

aws lambda add-permission \
  --function-name zerotrust-auth-handler \
  --statement-id apigateway-invoke-auth-register \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:$AWS_ACCOUNT_ID:$API_ID/*/POST/auth/register" \
  --region us-east-1
```

### 6. Create GET Method for /history (with Authorization)

```bash
# Get History Lambda ARN
export HISTORY_LAMBDA_ARN=$(aws lambda get-function \
  --function-name zerotrust-history-handler \
  --query 'Configuration.FunctionArn' \
  --output text)

# Create Lambda authorizer (JWT validation)
# First, create authorizer function
mkdir -p lambda-functions/jwt-authorizer
cd lambda-functions/jwt-authorizer

cat > index.mjs <<'EOF'
import jwt from 'jsonwebtoken';
import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';

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
  const token = event.authorizationToken?.replace('Bearer ', '');
  
  if (!token) {
    throw new Error('Unauthorized');
  }
  
  try {
    const secret = await getJwtSecret();
    const decoded = jwt.verify(token, secret);
    
    return {
      principalId: decoded.sub,
      policyDocument: {
        Version: '2012-10-17',
        Statement: [{
          Action: 'execute-api:Invoke',
          Effect: 'Allow',
          Resource: event.methodArn
        }]
      },
      context: {
        userId: decoded.sub,
        email: decoded.email,
        tier: decoded.tier
      }
    };
  } catch (error) {
    console.error('Auth error:', error);
    throw new Error('Unauthorized');
  }
};
EOF

cat > package.json <<'EOF'
{
  "name": "jwt-authorizer",
  "version": "1.0.0",
  "type": "module"
}
EOF

zip -r jwt-authorizer.zip index.mjs package.json
cd ../../..

# Deploy authorizer Lambda
aws lambda create-function \
  --function-name zerotrust-jwt-authorizer \
  --runtime nodejs20.x \
  --role $LAMBDA_ROLE_ARN \
  --handler index.handler \
  --zip-file fileb://lambda-functions/jwt-authorizer/jwt-authorizer.zip \
  --timeout 10 \
  --memory-size 128 \
  --environment Variables="{AWS_REGION=us-east-1}" \
  --layers $NODEJS_LAYER_ARN \
  --region us-east-1

export AUTHORIZER_LAMBDA_ARN=$(aws lambda get-function \
  --function-name zerotrust-jwt-authorizer \
  --query 'Configuration.FunctionArn' \
  --output text)

# Create authorizer in API Gateway
aws apigateway create-authorizer \
  --rest-api-id $API_ID \
  --name zerotrust-jwt-authorizer \
  --type TOKEN \
  --authorizer-uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$AUTHORIZER_LAMBDA_ARN/invocations" \
  --identity-source method.request.header.Authorization \
  --authorizer-result-ttl-in-seconds 300 \
  --region us-east-1

export AUTHORIZER_ID=<authorizer-id-from-output>

# Grant permission for authorizer
aws lambda add-permission \
  --function-name zerotrust-jwt-authorizer \
  --statement-id apigateway-invoke-authorizer \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:$AWS_ACCOUNT_ID:$API_ID/authorizers/$AUTHORIZER_ID" \
  --region us-east-1

# Create GET /history with authorization
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $HISTORY_RESOURCE_ID \
  --http-method GET \
  --authorization-type CUSTOM \
  --authorizer-id $AUTHORIZER_ID \
  --region us-east-1

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $HISTORY_RESOURCE_ID \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$HISTORY_LAMBDA_ARN/invocations" \
  --region us-east-1

aws lambda add-permission \
  --function-name zerotrust-history-handler \
  --statement-id apigateway-invoke-history \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:$AWS_ACCOUNT_ID:$API_ID/*/GET/history" \
  --region us-east-1
```

### 7. Create Request Validators

```bash
# Create validator for request body
aws apigateway create-request-validator \
  --rest-api-id $API_ID \
  --name body-validator \
  --validate-request-body \
  --no-validate-request-parameters \
  --region us-east-1

export BODY_VALIDATOR_ID=<validator-id-from-output>
```

### 8. Deploy API

```bash
# Create deployment
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --stage-description "Production deployment" \
  --description "Initial deployment" \
  --region us-east-1

# Get invoke URL
echo "API URL: https://$API_ID.execute-api.us-east-1.amazonaws.com/prod"
export API_URL="https://$API_ID.execute-api.us-east-1.amazonaws.com/prod"
```

### 9. Configure API Settings

```bash
# Enable CloudWatch logging
aws apigateway update-stage \
  --rest-api-id $API_ID \
  --stage-name prod \
  --patch-operations \
    op=replace,path=/methodSettings/*/*/loggingLevel,value=INFO \
    op=replace,path=/methodSettings/*/*/dataTraceEnabled,value=true \
    op=replace,path=/methodSettings/*/*/metricsEnabled,value=true \
  --region us-east-1

# Set throttling limits
aws apigateway update-stage \
  --rest-api-id $API_ID \
  --stage-name prod \
  --patch-operations \
    op=replace,path=/*/*/throttling/rateLimit,value=100 \
    op=replace,path=/*/*/throttling/burstLimit,value=200 \
  --region us-east-1
```

### 10. Test API Endpoints

```bash
# Test /verify endpoint
curl -X POST $API_URL/verify \
  -H "Content-Type: application/json" \
  -d '{"content":"The Earth is round","type":"text","source":"api"}'

# Test /auth/register
curl -X POST $API_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@zerotrust.com","password":"Test123!"}'

# Test /auth/login
curl -X POST $API_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@zerotrust.com","password":"Test123!"}'

# Save the access_token from response
export ACCESS_TOKEN=<token-from-login-response>

# Test /history (with authorization)
curl -X GET $API_URL/history \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 11. Set Up Custom Domain (Optional)

```bash
# Request ACM certificate
aws acm request-certificate \
  --domain-name api.zerotrust.yourcompany.com \
  --validation-method DNS \
  --region us-east-1

# After DNS validation, create custom domain
aws apigateway create-domain-name \
  --domain-name api.zerotrust.yourcompany.com \
  --certificate-arn <acm-certificate-arn> \
  --endpoint-configuration types=REGIONAL \
  --region us-east-1

# Create base path mapping
aws apigateway create-base-path-mapping \
  --domain-name api.zerotrust.yourcompany.com \
  --rest-api-id $API_ID \
  --stage prod \
  --region us-east-1

# Add CNAME record in Route 53 pointing to the API Gateway domain
```

### 12. Enable API Key (Optional - for rate limiting partners)

```bash
# Create API key
aws apigateway create-api-key \
  --name partner-key-1 \
  --description "API key for partner integration" \
  --enabled \
  --region us-east-1

export API_KEY_ID=<api-key-id-from-output>

# Create usage plan
aws apigateway create-usage-plan \
  --name zerotrust-pro-plan \
  --description "Professional tier - 5000 requests/day" \
  --throttle rateLimit=10,burstLimit=20 \
  --quota limit=5000,period=DAY \
  --api-stages apiId=$API_ID,stage=prod \
  --region us-east-1

export USAGE_PLAN_ID=<usage-plan-id-from-output>

# Associate API key with usage plan
aws apigateway create-usage-plan-key \
  --usage-plan-id $USAGE_PLAN_ID \
  --key-id $API_KEY_ID \
  --key-type API_KEY \
  --region us-east-1

# Update method to require API key
aws apigateway update-method \
  --rest-api-id $API_ID \
  --resource-id $VERIFY_RESOURCE_ID \
  --http-method POST \
  --patch-operations op=replace,path=/apiKeyRequired,value=true \
  --region us-east-1

# Redeploy
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --region us-east-1
```

---

## 🔍 Verification Checklist

- [ ] REST API created
- [ ] All resources created (/verify, /auth/*, /history)
- [ ] Lambda integrations configured
- [ ] CORS enabled for browser access
- [ ] JWT authorizer working
- [ ] API deployed to prod stage
- [ ] CloudWatch logging enabled
- [ ] Throttling configured
- [ ] Test endpoints returning correct responses

---

## 💰 Cost Estimate

**API Gateway pricing**:
- First 333M requests: $3.50 per million
- After 333M: $2.80 per million
- Cache (optional): $0.02 per hour (0.5GB)

**Estimated monthly cost** (10K requests/day):
- 300K requests/month = $1.05
- CloudWatch logs = ~$0.50
- **Total**: ~$1.50/month

Very affordable!

---

## 🚨 Troubleshooting

### 502 Bad Gateway
- Check Lambda function logs in CloudWatch
- Verify Lambda has correct VPC configuration
- Check Lambda timeout settings

### 403 Forbidden
- Check API Gateway resource policy
- Verify API key if required
- Check JWT authorizer configuration

### CORS errors
- Ensure OPTIONS method returns correct headers
- Verify Access-Control-Allow-Origin header

### High latency
- Enable API Gateway caching
- Use Lambda provisioned concurrency
- Check VPC NAT gateway performance

---

## 📊 Monitoring

### CloudWatch Dashboard

```bash
# View API Gateway metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Count \
  --dimensions Name=ApiName,Value=zerotrust-api \
  --start-time 2026-03-02T00:00:00Z \
  --end-time 2026-03-02T23:59:59Z \
  --period 3600 \
  --statistics Sum

# View latency
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Latency \
  --dimensions Name=ApiName,Value=zerotrust-api \
  --start-time 2026-03-02T00:00:00Z \
  --end-time 2026-03-02T23:59:59Z \
  --period 3600 \
  --statistics Average,Maximum

# View 4XX errors
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name 4XXError \
  --dimensions Name=ApiName,Value=zerotrust-api \
  --start-time 2026-03-02T00:00:00Z \
  --end-time 2026-03-02T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

---

## 🎉 Migration Complete!

Your ZeroTRUST system is now fully AWS-native:

```
✅ ElastiCache (Redis) - Tier 1 cache
✅ RDS (PostgreSQL) - Persistent storage
✅ DynamoDB - Tier 2 cache
✅ ECS Fargate - Containerized services
✅ Lambda - Serverless API handlers
✅ API Gateway - REST API endpoint
```

### Update Your Web Portal

Change API endpoint in `apps/web-portal/.env`:

```bash
VITE_API_URL=https://$API_ID.execute-api.us-east-1.amazonaws.com/prod
```

Rebuild and redeploy web portal to Amplify!

---

**🎯 Total Monthly Cost: ~$70-90**
- ElastiCache: $12
- RDS: $15
- DynamoDB: $1
- ECS: $40
- Lambda: FREE (within tier)
- API Gateway: $2

**Amazing value for a production-grade fact-checking platform!**
