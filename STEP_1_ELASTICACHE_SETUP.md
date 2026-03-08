# Step 1: Amazon ElastiCache (Redis) Setup

**Duration**: ~2 hours  
**Prerequisites**: AWS CLI configured, VPC with private subnets

---

## 🎯 Goal
Replace local Docker Redis with managed ElastiCache Redis cluster

---

## 📋 Step-by-Step Implementation

### 1. Create Security Group for Redis

```bash
# Set your VPC ID
export VPC_ID=<your-vpc-id>

# Create security group
aws ec2 create-security-group \
  --group-name zerotrust-redis-sg \
  --description "Security group for ZeroTRUST Redis cache" \
  --vpc-id $VPC_ID \
  --region us-east-1

# Save the output SecurityGroupId
export REDIS_SG_ID=<security-group-id-from-output>
```

### 2. Configure Security Group Rules

```bash
# Allow Redis port 6379 from your application security group
# (Replace <app-sg-id> with your ECS tasks or Lambda security group)
aws ec2 authorize-security-group-ingress \
  --group-id $REDIS_SG_ID \
  --protocol tcp \
  --port 6379 \
  --source-group <app-sg-id> \
  --region us-east-1

# Or allow from entire VPC (less secure but easier for testing)
aws ec2 authorize-security-group-ingress \
  --group-id $REDIS_SG_ID \
  --protocol tcp \
  --port 6379 \
  --cidr 10.0.0.0/16 \
  --region us-east-1
```

### 3. Create Cache Subnet Group

```bash
# List your private subnets
aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'Subnets[?MapPublicIpOnLaunch==`false`].[SubnetId,AvailabilityZone]' \
  --output table

# Create subnet group (use at least 2 private subnets in different AZs)
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name zerotrust-redis-subnet \
  --cache-subnet-group-description "ZeroTRUST Redis subnets" \
  --subnet-ids subnet-xxxxx subnet-yyyyy \
  --region us-east-1
```

### 4. Create Redis Cluster

```bash
# Create single-node Redis 7.0 cluster (t3.micro for cost optimization)
aws elasticache create-cache-cluster \
  --cache-cluster-id zerotrust-redis \
  --engine redis \
  --engine-version 7.0 \
  --cache-node-type cache.t3.micro \
  --num-cache-nodes 1 \
  --cache-subnet-group-name zerotrust-redis-subnet \
  --security-group-ids $REDIS_SG_ID \
  --preferred-availability-zone us-east-1a \
  --snapshot-retention-limit 1 \
  --snapshot-window "03:00-05:00" \
  --region us-east-1 \
  --tags Key=Project,Value=ZeroTRUST Key=Environment,Value=production Key=ManagedBy,Value=Manual

# For Multi-AZ with automatic failover (recommended for production, higher cost):
# aws elasticache create-replication-group \
#   --replication-group-id zerotrust-redis-cluster \
#   --replication-group-description "ZeroTRUST Redis with failover" \
#   --engine redis \
#   --cache-node-type cache.t3.micro \
#   --num-cache-clusters 2 \
#   --automatic-failover-enabled \
#   --cache-subnet-group-name zerotrust-redis-subnet \
#   --security-group-ids $REDIS_SG_ID
```

### 5. Wait for Cluster to be Available

```bash
# Check status (repeat until status is "available")
aws elasticache describe-cache-clusters \
  --cache-cluster-id zerotrust-redis \
  --region us-east-1 \
  --query 'CacheClusters[0].CacheClusterStatus' \
  --output text

# This usually takes 5-10 minutes
# You can add --show-cache-node-info to see more details
```

### 6. Get Redis Endpoint

```bash
# Get the primary endpoint
aws elasticache describe-cache-clusters \
  --cache-cluster-id zerotrust-redis \
  --show-cache-node-info \
  --region us-east-1 \
  --query 'CacheClusters[0].CacheNodes[0].Endpoint.{Address:Address,Port:Port}' \
  --output table

# Example output:
# zerotrust-redis.abc123.0001.use1.cache.amazonaws.com:6379
```

### 7. Update Your Application Configuration

#### For API Gateway (Node.js)

Update `apps/api-gateway/.env` or environment variables:

```bash
# ElastiCache endpoint (no redis:// prefix for ioredis)
REDIS_HOST=zerotrust-redis.abc123.0001.use1.cache.amazonaws.com
REDIS_PORT=6379

# Or as full URL (for redis clients that support it)
REDIS_URL=redis://zerotrust-redis.abc123.0001.use1.cache.amazonaws.com:6379
```

#### For Verification Engine (Python)

Update `apps/verification-engine/.env`:

```bash
REDIS_URL=redis://zerotrust-redis.abc123.0001.use1.cache.amazonaws.com:6379
```

### 8. Test Connection from Your VPC

If you have a bastion host or are connected via VPN:

```bash
# Install redis-cli if not available
sudo apt-get install redis-tools  # Ubuntu/Debian
# or
brew install redis  # macOS

# Test connection
redis-cli -h zerotrust-redis.abc123.0001.use1.cache.amazonaws.com -p 6379 ping
# Expected: PONG

# Test set/get
redis-cli -h zerotrust-redis.abc123.0001.use1.cache.amazonaws.com -p 6379
> SET test "Hello from ElastiCache"
> GET test
> EXIT
```

### 9. Update API Gateway Redis Client (if needed)

Your existing code in `apps/api-gateway/src/config/redis.ts` should work as-is. Verify it uses these environment variables:

```typescript
const redisClient = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  // ... rest of config
});
```

### 10. Verify Application Still Works

```bash
# Start your services with new Redis endpoint
cd apps/api-gateway
npm run dev

# Test verification endpoint
curl -X POST http://localhost:3000/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{"content":"Test claim","type":"text","source":"api"}'

# Check Redis cache hit
# Run the same request again - should be faster with cache
```

---

## 🔍 Verification Checklist

- [ ] Security group created and rules configured
- [ ] Subnet group created with private subnets
- [ ] Redis cluster status is "available"
- [ ] Redis endpoint accessible from VPC
- [ ] Application environment variables updated
- [ ] Application successfully connects to ElastiCache
- [ ] Cache hit/miss working correctly
- [ ] Old local Redis container stopped

---

## 💰 Cost Optimization

**cache.t3.micro** costs approximately **$0.017/hour** = **~$12.50/month**

For hackathon/testing, you can:
- Use single-node (no replication) to save 50%
- Stop/delete when not actively testing
- Set up CloudWatch alarms for unexpected usage

---

## 🚨 Troubleshooting

### Cannot connect to Redis
- **Check security group**: Ensure port 6379 is open from your app's SG
- **Check subnet group**: Must be in private subnets with NAT gateway
- **Check VPC connectivity**: Ensure your app can reach private subnets

### Connection timeouts
- **Check route tables**: Private subnets need route to NAT gateway
- **Check NACL**: Ensure Network ACLs allow traffic

### High latency
- **Check availability zones**: App and Redis should be in same AZ
- **Check connection pooling**: Ensure your Redis client uses connection pooling

---

## 🔄 Rollback Plan

If you need to rollback to local Redis:

```bash
# Delete ElastiCache cluster
aws elasticache delete-cache-cluster \
  --cache-cluster-id zerotrust-redis \
  --region us-east-1

# Revert environment variables
REDIS_HOST=localhost
REDIS_PORT=6379

# Start local Redis
docker-compose up -d redis
```

---

## 📊 Monitoring

Add CloudWatch alarms:

```bash
# Create alarm for high CPU
aws cloudwatch put-metric-alarm \
  --alarm-name zerotrust-redis-high-cpu \
  --alarm-description "Alert when Redis CPU > 75%" \
  --metric-name CPUUtilization \
  --namespace AWS/ElastiCache \
  --statistic Average \
  --period 300 \
  --threshold 75 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=CacheClusterId,Value=zerotrust-redis

# Create alarm for high memory
aws cloudwatch put-metric-alarm \
  --alarm-name zerotrust-redis-high-memory \
  --alarm-description "Alert when Redis memory > 80%" \
  --metric-name DatabaseMemoryUsagePercentage \
  --namespace AWS/ElastiCache \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=CacheClusterId,Value=zerotrust-redis
```

---

**✅ Once complete, proceed to Step 2: RDS PostgreSQL Setup**
