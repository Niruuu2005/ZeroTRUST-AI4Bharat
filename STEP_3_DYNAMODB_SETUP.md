# Step 3: Amazon DynamoDB Cache Setup

**Duration**: ~1 hour  
**Prerequisites**: AWS CLI configured

---

## 🎯 Goal
Activate DynamoDB as Tier-2 cache for 3-tier caching strategy

**Caching Strategy**:
```
Tier 1: ElastiCache (Redis) - <1ms (hot cache)
Tier 2: DynamoDB - ~5ms (warm cache)  ← YOU ARE HERE
Tier 3: RDS PostgreSQL - ~20ms (cold cache)
```

---

## 📋 Step-by-Step Implementation

### 1. Create DynamoDB Table

```bash
# Create table with on-demand pricing (pay per request)
aws dynamodb create-table \
  --table-name zerotrust-cache-tier2 \
  --attribute-definitions \
      AttributeName=claim_hash,AttributeType=S \
  --key-schema \
      AttributeName=claim_hash,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1 \
  --tags Key=Project,Value=ZeroTRUST Key=Environment,Value=production Key=CacheTier,Value=2

# For provisioned capacity (more predictable costs):
# --billing-mode PROVISIONED \
# --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

### 2. Enable Time-to-Live (TTL)

```bash
# Enable TTL for automatic expiration (24 hours)
aws dynamodb update-time-to-live \
  --table-name zerotrust-cache-tier2 \
  --time-to-live-specification "Enabled=true, AttributeName=ttl" \
  --region us-east-1
```

### 3. Verify Table Creation

```bash
# Check table status
aws dynamodb describe-table \
  --table-name zerotrust-cache-tier2 \
  --region us-east-1 \
  --query 'Table.{Name:TableName,Status:TableStatus,ItemCount:ItemCount,BillingMode:BillingModeSummary.BillingMode}'

# Wait until status is "ACTIVE"
```

### 4. Verify TTL Configuration

```bash
# Check TTL status
aws dynamodb describe-time-to-live \
  --table-name zerotrust-cache-tier2 \
  --region us-east-1
```

### 5. Create IAM Policy for DynamoDB Access

```bash
# Create policy JSON file
cat > dynamodb-cache-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:DeleteItem",
        "dynamodb:UpdateItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-east-1:*:table/zerotrust-cache-tier2",
        "arn:aws:dynamodb:us-east-1:*:table/zerotrust-cache-tier2/index/*"
      ]
    }
  ]
}
EOF

# Create IAM policy
aws iam create-policy \
  --policy-name ZeroTrustDynamoDBCachePolicy \
  --policy-document file://dynamodb-cache-policy.json \
  --description "Allow ZeroTRUST services to access DynamoDB cache"

# Note the PolicyArn from output
```

### 6. Attach Policy to Your Service Role

```bash
# Attach to Lambda execution role
aws iam attach-role-policy \
  --role-name zerotrust-lambda-role \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/ZeroTrustDynamoDBCachePolicy

# Attach to ECS task role
aws iam attach-role-policy \
  --role-name zerotrust-ecs-task-role \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/ZeroTrustDynamoDBCachePolicy
```

### 7. Test DynamoDB Access with AWS CLI

```bash
# Put a test item
aws dynamodb put-item \
  --table-name zerotrust-cache-tier2 \
  --item '{
    "claim_hash": {"S": "test_hash_123"},
    "result": {"S": "{\"score\":85,\"category\":\"Verified True\"}"},
    "cached_at": {"N": "'$(date +%s)'"},
    "ttl": {"N": "'$(($(date +%s) + 86400))'"}
  }' \
  --region us-east-1

# Get the test item
aws dynamodb get-item \
  --table-name zerotrust-cache-tier2 \
  --key '{"claim_hash": {"S": "test_hash_123"}}' \
  --region us-east-1

# Delete the test item
aws dynamodb delete-item \
  --table-name zerotrust-cache-tier2 \
  --key '{"claim_hash": {"S": "test_hash_123"}}' \
  --region us-east-1
```

### 8. Update Application Configuration

Your API Gateway code already supports DynamoDB! Just set environment variables:

#### For API Gateway (Node.js)

Update `apps/api-gateway/.env`:

```bash
# AWS Configuration
AWS_REGION=us-east-1
DYNAMODB_TABLE=zerotrust-cache-tier2

# Your AWS credentials (or use IAM role when deployed to ECS/Lambda)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

### 9. Verify API Gateway Code

Check that `apps/api-gateway/src/services/CacheService.ts` has DynamoDB support. It should look like this:

```typescript
// This code should already exist in your project
import { DynamoDBClient, GetItemCommand, PutItemCommand } from '@aws-sdk/client-dynamodb';
import { marshall, unmarshall } from '@aws-sdk/util-dynamodb';

class CacheService {
  private dynamodb?: DynamoDBClient;
  
  constructor() {
    if (process.env.DYNAMODB_TABLE) {
      this.dynamodb = new DynamoDBClient({ region: process.env.AWS_REGION || 'us-east-1' });
    }
  }

  async get(key: string): Promise<any> {
    // Try Tier 1: Redis
    const redisResult = await this.redis.get(key);
    if (redisResult) {
      return JSON.parse(redisResult);
    }

    // Try Tier 2: DynamoDB
    if (this.dynamodb) {
      const result = await this.dynamodb.send(new GetItemCommand({
        TableName: process.env.DYNAMODB_TABLE,
        Key: marshall({ claim_hash: key })
      }));
      
      if (result.Item) {
        const item = unmarshall(result.Item);
        // Promote to Tier 1
        await this.redis.setex(key, 3600, JSON.stringify(item.result));
        return item.result;
      }
    }

    // Try Tier 3: PostgreSQL
    // ... existing code
  }

  async set(key: string, value: any, ttl: number = 86400): Promise<void> {
    // Set in all tiers
    await this.redis.setex(key, 3600, JSON.stringify(value));
    
    if (this.dynamodb) {
      await this.dynamodb.send(new PutItemCommand({
        TableName: process.env.DYNAMODB_TABLE,
        Item: marshall({
          claim_hash: key,
          result: value,
          cached_at: Math.floor(Date.now() / 1000),
          ttl: Math.floor(Date.now() / 1000) + ttl
        })
      }));
    }
  }
}
```

### 10. Test 3-Tier Caching

```bash
# Start API Gateway with DynamoDB enabled
cd apps/api-gateway
export DYNAMODB_TABLE=zerotrust-cache-tier2
export AWS_REGION=us-east-1
npm run dev

# First request (cache miss - will be slow)
time curl -X POST http://localhost:3000/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{"content":"The Earth is round","type":"text","source":"api"}'
# Expected: 5-10 seconds, cached=false

# Second request (Redis cache hit - very fast)
time curl -X POST http://localhost:3000/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{"content":"The Earth is round","type":"text","source":"api"}'
# Expected: <200ms, cached=true, cache_tier="redis"

# Clear Redis, test DynamoDB tier
redis-cli FLUSHALL

# Third request (DynamoDB cache hit - fast)
time curl -X POST http://localhost:3000/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{"content":"The Earth is round","type":"text","source":"api"}'
# Expected: <500ms, cached=true, cache_tier="dynamodb"
```

### 11. Verify Items in DynamoDB

```bash
# Scan table to see cached items
aws dynamodb scan \
  --table-name zerotrust-cache-tier2 \
  --region us-east-1 \
  --max-items 10

# Get specific item by claim_hash
aws dynamodb get-item \
  --table-name zerotrust-cache-tier2 \
  --key '{"claim_hash": {"S": "your-claim-hash-here"}}' \
  --region us-east-1
```

---

## 🔍 Verification Checklist

- [ ] DynamoDB table created with status "ACTIVE"
- [ ] TTL enabled on `ttl` attribute
- [ ] IAM policy created and attached to service roles
- [ ] Environment variables set (DYNAMODB_TABLE, AWS_REGION)
- [ ] Test item successfully written and read
- [ ] API Gateway connects to DynamoDB
- [ ] 3-tier cache waterfall working (Redis → DynamoDB → PostgreSQL)
- [ ] Cache promotion working (DynamoDB → Redis)

---

## 💰 Cost Optimization

**On-Demand Pricing**:
- **Write**: $1.25 per million write requests
- **Read**: $0.25 per million read requests
- **Storage**: $0.25 per GB-month

**Estimated Monthly Cost** (for hackathon with moderate usage):
- 100,000 writes/month = $0.13
- 500,000 reads/month = $0.13
- 1 GB storage = $0.25
- **Total**: ~$0.50/month

For higher traffic, consider **provisioned capacity**:
- 5 read + 5 write capacity units = ~$4/month (more cost-effective at scale)

---

## 🚨 Troubleshooting

### AccessDeniedException
- **Check IAM policy**: Ensure role has dynamodb:GetItem and dynamodb:PutItem
- **Check policy attachment**: Verify policy is attached to correct role
- **Check AWS credentials**: Ensure credentials are set correctly

### ValidationException
- **Check table name**: Ensure DYNAMODB_TABLE environment variable is correct
- **Check key schema**: Ensure you're using "claim_hash" as partition key
- **Check data types**: String (S), Number (N), etc.

### Items not expiring
- **Check TTL**: Ensure TTL is enabled on correct attribute name
- **Wait time**: TTL deletion can take up to 48 hours (typically within minutes)
- **Check TTL value**: Must be Unix timestamp in seconds

### Slow reads
- **Check region**: Ensure table and app are in same region
- **Check item size**: Large items (>4KB) take longer
- **Enable DAX**: (DynamoDB Accelerator) for microsecond latency (additional cost)

---

## 📊 Monitoring

### Create CloudWatch Alarms

```bash
# Throttled read requests alarm
aws cloudwatch put-metric-alarm \
  --alarm-name zerotrust-dynamodb-throttled-reads \
  --alarm-description "Alert when DynamoDB reads are throttled" \
  --metric-name UserErrors \
  --namespace AWS/DynamoDB \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --dimensions Name=TableName,Value=zerotrust-cache-tier2

# High consumed capacity alarm (for provisioned mode)
aws cloudwatch put-metric-alarm \
  --alarm-name zerotrust-dynamodb-high-consumption \
  --alarm-description "Alert when DynamoDB consumed capacity > 80%" \
  --metric-name ConsumedReadCapacityUnits \
  --namespace AWS/DynamoDB \
  --statistic Sum \
  --period 300 \
  --threshold 240 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=TableName,Value=zerotrust-cache-tier2
```

### View Metrics

```bash
# View read/write metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=zerotrust-cache-tier2 \
  --start-time 2026-03-02T00:00:00Z \
  --end-time 2026-03-02T23:59:59Z \
  --period 3600 \
  --statistics Sum \
  --region us-east-1
```

---

## 🎯 Performance Tips

### 1. Use Consistent Reads Only When Needed

```typescript
// Eventually consistent read (default, faster, cheaper)
await dynamodb.send(new GetItemCommand({
  TableName: 'zerotrust-cache-tier2',
  Key: marshall({ claim_hash: key })
}));

// Strongly consistent read (slower, 2x cost)
await dynamodb.send(new GetItemCommand({
  TableName: 'zerotrust-cache-tier2',
  Key: marshall({ claim_hash: key }),
  ConsistentRead: true
}));
```

### 2. Use Batch Operations for Multiple Items

```typescript
import { BatchGetItemCommand } from '@aws-sdk/client-dynamodb';

// Get multiple items in one request
const result = await dynamodb.send(new BatchGetItemCommand({
  RequestItems: {
    'zerotrust-cache-tier2': {
      Keys: [
        marshall({ claim_hash: 'hash1' }),
        marshall({ claim_hash: 'hash2' }),
        marshall({ claim_hash: 'hash3' })
      ]
    }
  }
}));
```

### 3. Compress Large Items

```typescript
import { gzip, gunzip } from 'zlib';
import { promisify } from 'util';

const gzipAsync = promisify(gzip);
const gunzipAsync = promisify(gunzip);

// Before storing
const compressed = await gzipAsync(JSON.stringify(largeResult));
await dynamodb.send(new PutItemCommand({
  TableName: 'zerotrust-cache-tier2',
  Item: marshall({
    claim_hash: key,
    result: compressed.toString('base64'),
    compressed: true
  })
}));
```

---

## 🔄 Rollback Plan

If you need to disable DynamoDB caching:

```bash
# Remove environment variable
unset DYNAMODB_TABLE

# Or comment out in .env
# DYNAMODB_TABLE=zerotrust-cache-tier2

# The code will automatically fallback to Redis + PostgreSQL only
```

To delete the table:

```bash
# Delete table (careful! data will be lost)
aws dynamodb delete-table \
  --table-name zerotrust-cache-tier2 \
  --region us-east-1
```

---

## 🎨 Advanced Features (Optional)

### Enable Point-in-Time Recovery (PITR)

```bash
aws dynamodb update-continuous-backups \
  --table-name zerotrust-cache-tier2 \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
```

### Enable Auto Scaling (for Provisioned Capacity)

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace dynamodb \
  --resource-id table/zerotrust-cache-tier2 \
  --scalable-dimension dynamodb:table:ReadCapacityUnits \
  --min-capacity 5 \
  --max-capacity 100

# Create scaling policy
aws application-autoscaling put-scaling-policy \
  --service-namespace dynamodb \
  --resource-id table/zerotrust-cache-tier2 \
  --scalable-dimension dynamodb:table:ReadCapacityUnits \
  --policy-name zerotrust-cache-read-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

---

**✅ Once complete, proceed to Step 4: ECS Container Deployment**
