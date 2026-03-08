# AWS Free Tier Optimization Guide
## Staying Within $100 Credit Budget

**Last Updated**: March 3, 2026  
**Target**: Hackathon deployment with minimal costs

---

## 💰 AWS Free Tier Coverage (12 months)

### ✅ Always Free (No charges within limits)
- **Lambda**: 1M requests/month + 400,000 GB-seconds compute = **FREE**
- **API Gateway**: 1M requests/month (first 12 months) = **FREE**
- **DynamoDB**: 25GB storage + 25 WCU/RCU = **FREE**
- **S3**: 5GB storage + 20,000 GET + 2,000 PUT = **FREE**
- **CloudWatch**: 10 custom metrics + 10 alarms + 5GB logs = **FREE**

### ⚠️ Free Tier with Limits (750 hours/month = 1 instance 24/7)
- **RDS**: 750 hours/month of **db.t3.micro** = **FREE** ✅
- **EC2**: 750 hours/month of **t3.micro** = **FREE** ✅  
- **ElastiCache**: ❌ **NO FREE TIER** (~$12-15/month)
- **ECS Fargate**: ⚠️ First 3 months only (~$40/month after)

### 💵 Paid Services (No Free Tier)
- **AWS Bedrock**: Pay per token (~$10-20/month for hackathon)
- **ElastiCache**: ~$12.50/month (cache.t3.micro)
- **Data Transfer**: First 100GB/month free

---

## 🎯 Optimized Architecture for Free Tier

### Option 1: Maximum Free Tier (Recommended for Hackathon)

```
Browser → API Gateway (FREE) → Lambda (FREE) 
    ↓
    → DynamoDB Cache (FREE) → RDS PostgreSQL (FREE)
    ↓
    → EC2 t3.micro running Docker (FREE)
```

**Monthly Cost**: ~$10-20 (Bedrock tokens only!)

### Changes from Original Plan:
1. ❌ **Skip ElastiCache** (no free tier) → Use **DynamoDB as primary cache**
2. ❌ **Skip ECS Fargate** (expensive) → Use **EC2 t3.micro with Docker**
3. ✅ Keep Lambda + API Gateway (fully free)
4. ✅ Keep RDS db.t3.micro (free tier)
5. ✅ Keep DynamoDB (free tier)

---

## 📊 Detailed Cost Breakdown

### Current Monthly Costs (Original Plan)
| Service | Instance Type | Cost/Month |
|---------|--------------|------------|
| ElastiCache | cache.t3.micro | $12.50 |
| RDS | db.t3.micro | $0 (free tier) |
| DynamoDB | On-demand | $0 (free tier) |
| ECS Fargate | 2 tasks × 0.5 vCPU | $40.00 |
| Lambda | <1M requests | $0 (free tier) |
| API Gateway | <1M requests | $0 (free tier) |
| S3 | <5GB | $0 (free tier) |
| Bedrock | ~50K tokens/day | $15.00 |
| **TOTAL** | | **$67.50/month** |

### Optimized Monthly Costs (Free Tier Maximized)
| Service | Instance Type | Cost/Month |
|---------|--------------|------------|
| ~~ElastiCache~~ | REMOVED | ~~$12.50~~ $0 |
| RDS | db.t3.micro | $0 (free tier) |
| DynamoDB | On-demand (primary cache) | $0 (free tier) |
| ~~ECS Fargate~~ | REMOVED | ~~$40~~ $0 |
| **EC2** | **t3.micro (Docker)** | **$0 (free tier)** |
| Lambda | <1M requests | $0 (free tier) |
| API Gateway | <1M requests | $0 (free tier) |
| S3 | <5GB | $0 (free tier) |
| Bedrock | ~50K tokens/day | $15.00 |
| **TOTAL** | | **$15/month** ✅ |

**Savings**: $52.50/month = **78% reduction!**

---

## 🚀 Revised Implementation Steps

### SKIP These Steps:
- ~~STEP 1: ElastiCache Setup~~ → Not needed
- ~~STEP 4: ECS Deployment~~ → Use EC2 instead

### DO These Steps:
1. ✅ **DynamoDB Setup** (as primary cache)
2. ✅ **RDS Setup** (db.t3.micro - free tier)
3. ✅ **EC2 Docker Deployment** (t3.micro - free tier)
4. ✅ **Lambda Functions** (free tier)
5. ✅ **API Gateway** (free tier)

---

## 🔧 Step-by-Step: Free Tier Implementation

### 1. Set Up DynamoDB (Primary Cache)

```bash
# Create DynamoDB table (FREE)
aws dynamodb create-table \
  --table-name ZeroTrustCache \
  --attribute-definitions \
    AttributeName=cache_key,AttributeType=S \
  --key-schema \
    AttributeName=cache_key,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1 \
  --tags Key=Project,Value=ZeroTRUST Key=Environment,Value=production

# Enable TTL (auto-delete after 24 hours)
aws dynamodb update-time-to-live \
  --table-name ZeroTrustCache \
  --time-to-live-specification Enabled=true,AttributeName=ttl
```

**Cost**: $0 (within 25GB free tier)

---

### 2. Set Up RDS PostgreSQL (Free Tier)

```bash
# Create db.t3.micro instance (FREE - 750 hours/month)
aws rds create-db-instance \
  --db-instance-identifier zerotrust-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.4 \
  --master-username zerotrust_admin \
  --master-user-password "YourSecurePassword123!" \
  --allocated-storage 20 \
  --storage-type gp2 \
  --vpc-security-group-ids sg-xxxxxxxxx \
  --db-subnet-group-name default \
  --backup-retention-period 7 \
  --no-multi-az \
  --publicly-accessible \
  --region us-east-1 \
  --tags Key=Project,Value=ZeroTRUST
```

**Cost**: $0 (within 750 hours free tier)

---

### 3. Deploy to EC2 with Docker (Free Tier)

```bash
# Launch t3.micro EC2 instance (FREE - 750 hours/month)
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.micro \
  --key-name your-key-pair \
  --security-group-ids sg-xxxxxxxxx \
  --subnet-id subnet-xxxxxxxxx \
  --count 1 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=zerotrust-app},{Key=Project,Value=ZeroTRUST}]' \
  --user-data file://ec2-setup.sh \
  --region us-east-1
```

**ec2-setup.sh**:
```bash
#!/bin/bash
# Install Docker
yum update -y
yum install -y docker
service docker start
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Clone your project (or copy files)
mkdir -p /opt/zerotrust
cd /opt/zerotrust

# Create docker-compose.yml
cat > docker-compose.yml <<'EOF'
version: '3.8'

services:
  verification-engine:
    build: ./apps/verification-engine
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://zerotrust_admin:password@<rds-endpoint>:5432/zerotrust_db
      - DYNAMODB_TABLE=ZeroTrustCache
      - AWS_REGION=us-east-1
    restart: always

  media-analysis:
    build: ./apps/media-analysis
    ports:
      - "8001:8001"
    environment:
      - S3_BUCKET=zerotrust-media-dev
      - AWS_REGION=us-east-1
    restart: always
EOF

# Start services
docker-compose up -d
```

**Cost**: $0 (within 750 hours free tier)

---

### 4. Create Lambda Functions (Free Tier)

```bash
# Deploy verify-handler (uses DynamoDB cache)
cd lambda-functions/verify-handler

cat > index.mjs <<'EOF'
import { DynamoDBClient, GetItemCommand, PutItemCommand } from '@aws-sdk/client-dynamodb';
import { marshall, unmarshall } from '@aws-sdk/util-dynamodb';
import crypto from 'crypto';

const dynamodb = new DynamoDBClient({ region: process.env.AWS_REGION });
const EC2_ENDPOINT = process.env.EC2_ENDPOINT; // http://<ec2-ip>:8000

export const handler = async (event) => {
  const body = JSON.parse(event.body);
  const { content, type } = body;
  
  // Generate cache key
  const cacheKey = crypto.createHash('sha256').update(content).digest('hex');
  
  try {
    // Check DynamoDB cache
    const cacheResult = await dynamodb.send(new GetItemCommand({
      TableName: 'ZeroTrustCache',
      Key: marshall({ cache_key: cacheKey })
    }));
    
    if (cacheResult.Item) {
      const cached = unmarshall(cacheResult.Item);
      console.log('Cache HIT - DynamoDB');
      return {
        statusCode: 200,
        body: JSON.stringify({
          ...cached.result,
          cached: true,
          cache_tier: 'dynamodb'
        })
      };
    }
    
    // Cache MISS - call verification engine on EC2
    console.log('Cache MISS - calling EC2');
    const response = await fetch(`${EC2_ENDPOINT}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    
    const result = await response.json();
    
    // Store in DynamoDB
    await dynamodb.send(new PutItemCommand({
      TableName: 'ZeroTrustCache',
      Item: marshall({
        cache_key: cacheKey,
        result: result,
        ttl: Math.floor(Date.now() / 1000) + 86400 // 24 hours
      })
    }));
    
    return {
      statusCode: 200,
      body: JSON.stringify({ ...result, cached: false })
    };
  } catch (error) {
    console.error('Error:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: error.message })
    };
  }
};
EOF

zip -r verify-handler.zip index.mjs package.json

aws lambda create-function \
  --function-name zerotrust-verify-handler \
  --runtime nodejs20.x \
  --role $LAMBDA_ROLE_ARN \
  --handler index.handler \
  --zip-file fileb://verify-handler.zip \
  --timeout 30 \
  --memory-size 256 \
  --environment Variables="{AWS_REGION=us-east-1,EC2_ENDPOINT=http://<ec2-ip>:8000}" \
  --region us-east-1
```

**Cost**: $0 (within 1M requests free tier)

---

### 5. Set Up API Gateway (Free Tier)

```bash
# Create REST API
aws apigateway create-rest-api \
  --name zerotrust-api \
  --description "ZeroTRUST API - Free Tier Optimized" \
  --endpoint-configuration types=REGIONAL \
  --region us-east-1

export API_ID=<api-id>

# Follow STEP_6_API_GATEWAY_SETUP.md for complete setup
# All API Gateway features are FREE for first 1M requests/month
```

**Cost**: $0 (within 1M requests free tier)

---

## 📈 Free Tier Usage Monitoring

### Set Up Billing Alerts

```bash
# Create SNS topic for alerts
aws sns create-topic \
  --name zerotrust-billing-alerts \
  --region us-east-1

export SNS_TOPIC_ARN=<topic-arn>

# Subscribe your email
aws sns subscribe \
  --topic-arn $SNS_TOPIC_ARN \
  --protocol email \
  --notification-endpoint your-email@example.com

# Create billing alarm (alert if cost > $20)
aws cloudwatch put-metric-alarm \
  --alarm-name zerotrust-cost-alert \
  --alarm-description "Alert if monthly cost exceeds $20" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --evaluation-periods 1 \
  --threshold 20 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions $SNS_TOPIC_ARN \
  --dimensions Name=Currency,Value=USD
```

### Check Current Usage

```bash
# Check free tier usage
aws ce get-cost-and-usage \
  --time-period Start=2026-03-01,End=2026-03-03 \
  --granularity MONTHLY \
  --metrics UsageQuantity BlendedCost \
  --group-by Type=SERVICE

# Check Lambda invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --start-time 2026-03-01T00:00:00Z \
  --end-time 2026-03-03T23:59:59Z \
  --period 86400 \
  --statistics Sum

# Check API Gateway requests
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Count \
  --start-time 2026-03-01T00:00:00Z \
  --end-time 2026-03-03T23:59:59Z \
  --period 86400 \
  --statistics Sum
```

---

## 🎯 Cost Optimization Tips

### 1. Minimize Bedrock Token Usage
```python
# In verification-engine/src/agents/manager.py
# Use cheaper models for simple tasks

AGENT_MODELS = {
    'manager': 'anthropic.claude-3-haiku-20240307-v1:0',  # Cheaper!
    'sentiment': 'amazon.titan-text-lite-v1',  # Cheapest!
    'research': 'anthropic.claude-3-haiku-20240307-v1:0'
}
```

**Savings**: ~60% on Bedrock costs

### 2. Aggressive Caching
```python
# Increase cache TTL to reduce duplicate verifications
CACHE_TTL = 7 * 24 * 3600  # 7 days instead of 24 hours
```

### 3. Use Spot Instances (for EC2)
```bash
# Request spot instance (50-90% cheaper)
aws ec2 request-spot-instances \
  --spot-price "0.004" \
  --instance-count 1 \
  --type "one-time" \
  --launch-specification file://spot-spec.json
```

**Savings**: 50-90% on EC2 costs (after free tier expires)

### 4. Stop EC2 When Not Testing
```bash
# Stop instance to avoid charges
aws ec2 stop-instances --instance-ids i-xxxxxxxxx

# Start when needed
aws ec2 start-instances --instance-ids i-xxxxxxxxx
```

---

## 📊 Projected Costs for Hackathon (3 months)

### Scenario: 100 verifications/day

| Month | Service Costs | Free Tier Savings | Your Cost |
|-------|--------------|-------------------|-----------|
| Month 1 | $67.50 | -$52.50 (optimizations) | **$15** |
| Month 2 | $67.50 | -$52.50 | **$15** |
| Month 3 | $67.50 | -$52.50 | **$15** |
| **Total** | $202.50 | -$157.50 | **$45** |

**Remaining Credit**: $100 - $45 = **$55** ✅

### Scenario: 500 verifications/day (heavy usage)

| Month | Bedrock Usage | Other Services | Your Cost |
|-------|---------------|----------------|-----------|
| Month 1 | $25 | $0 (free tier) | **$25** |
| Month 2 | $25 | $0 | **$25** |
| Month 3 | $25 | $0 | **$25** |
| **Total** | $75 | $0 | **$75** |

**Remaining Credit**: $100 - $75 = **$25** ✅

---

## ⚠️ Things That Could Exceed Budget

1. **Data Transfer Out** (>100GB/month)
   - Solution: Use CloudFront CDN (first 1TB free)

2. **Bedrock Heavy Usage** (>100K tokens/day)
   - Solution: Implement request limits per user

3. **DynamoDB Over Limits** (>25 WCU/RCU)
   - Solution: Your cache workload is well within limits

4. **RDS Storage Growth** (>20GB)
   - Solution: Regular cleanup of old verifications

---

## ✅ Final Verdict

**YES! You can implement the entire system within $100 free credits.**

**Expected total cost for 3-month hackathon**: $45-75  
**Remaining budget**: $25-55

### Architecture Summary:
- ✅ API Gateway (FREE)
- ✅ Lambda Functions (FREE)
- ✅ DynamoDB Cache (FREE)
- ✅ RDS PostgreSQL (FREE)
- ✅ EC2 t3.micro Docker (FREE)
- ✅ S3 Storage (FREE)
- 💵 AWS Bedrock ($15-25/month)

**You're good to go! 🚀**
