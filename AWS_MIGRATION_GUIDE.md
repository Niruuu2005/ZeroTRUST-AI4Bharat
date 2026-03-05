# 🏗️ ZeroTRUST AWS Migration Guide

**Date**: March 3, 2026  
**Goal**: Migrate from local Docker to AWS-native services  
**Duration**: 3-5 days

---

## 💡 **FREE TIER OPTIMIZATION AVAILABLE!**

**Using AWS Free Tier or $100 credits?** → **Read [FREE_TIER_OPTIMIZATION.md](FREE_TIER_OPTIMIZATION.md) first!**

- **This guide**: Full architecture (~$70/month)
- **Free tier version**: Optimized architecture (~$15/month)
- **Your $100 budget**: ✅ Covers 3-6 months with optimization!

**Key changes for free tier**:
- Skip ElastiCache → Use DynamoDB as primary cache  
- Skip ECS Fargate → Use EC2 t3.micro with Docker  
- Keep Lambda + API Gateway (fully free)

---

## 📋 Prerequisites

- [ ] AWS Account with admin access
- [ ] AWS CLI installed and configured (`aws configure`)
- [ ] Docker installed (for building images)
- [ ] Node.js 20+ and Python 3.11+
- [ ] Current services running locally

---

## 🎯 Migration Order (Dependency-Based)

```
Step 1: ElastiCache (Redis)      [Foundation - No dependencies]
   ↓
Step 2: RDS (PostgreSQL)         [Foundation - No dependencies]
   ↓
Step 3: DynamoDB (Cache Tier 2)   [Foundation - No dependencies]
   ↓
Step 4: ECR + ECS (Containers)    [Needs: ElastiCache, RDS]
   ↓
Step 5: Lambda Functions          [Needs: ElastiCache, RDS, DynamoDB]
   ↓
Step 6: API Gateway               [Needs: Lambda functions]
```

---

## 📍 STEP 1: Amazon ElastiCache (Redis) - 2 hours

### 1.1 Create Security Group

```bash
# Create security group for Redis
aws ec2 create-security-group \
  --group-name zerotrust-redis-sg \
  --description "Security group for ZeroTRUST Redis cache" \
  --vpc-id <your-vpc-id>

# Note the SecurityGroupId from output
export REDIS_SG_ID=<security-group-id>

# Allow Redis port 6379 from your app security group
aws ec2 authorize-security-group-ingress \
  --group-id $REDIS_SG_ID \
  --protocol tcp \
  --port 6379 \
  --source-group <your-app-security-group-id>
```

### 1.2 Create ElastiCache Subnet Group

```bash
# Create subnet group (use private subnets)
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name zerotrust-redis-subnet \
  --cache-subnet-group-description "ZeroTRUST Redis subnets" \
  --subnet-ids subnet-xxxxx subnet-yyyyy
```

### 1.3 Create Redis Cluster

```bash
# Create Redis 7.0 cluster (t3.micro for hackathon)
aws elasticache create-cache-cluster \
  --cache-cluster-id zerotrust-redis \
  --engine redis \
  --engine-version 7.0 \
  --cache-node-type cache.t3.micro \
  --num-cache-nodes 1 \
  --cache-subnet-group-name zerotrust-redis-subnet \
  --security-group-ids $REDIS_SG_ID \
  --preferred-availability-zone us-east-1a \
  --tags Key=Project,Value=ZeroTRUST Key=Environment,Value=production

# Wait for cluster to be available (5-10 minutes)
aws elasticache describe-cache-clusters \
  --cache-cluster-id zerotrust-redis \
  --show-cache-node-info
```

### 1.4 Get Redis Endpoint

```bash
# Get the endpoint
aws elasticache describe-cache-clusters \
  --cache-cluster-id zerotrust-redis \
  --show-cache-node-info \
  --query 'CacheClusters[0].CacheNodes[0].Endpoint' \
  --output text

# Output example: zerotrust-redis.abc123.0001.use1.cache.amazonaws.com:6379
```

### 1.5 Update Environment Variables

Add to your `.env`:
```bash
REDIS_URL=redis://zerotrust-redis.abc123.0001.use1.cache.amazonaws.com:6379
REDIS_HOST=zerotrust-redis.abc123.0001.use1.cache.amazonaws.com
REDIS_PORT=6379
```

**✅ Checkpoint**: Test Redis connection from your local machine (if in VPC, use bastion or VPN)

---

## 📍 STEP 2: Amazon RDS (PostgreSQL) - 3 hours

### 2.1 Create Security Group

```bash
# Create security group for RDS
aws ec2 create-security-group \
  --group-name zerotrust-rds-sg \
  --description "Security group for ZeroTRUST PostgreSQL" \
  --vpc-id <your-vpc-id>

export RDS_SG_ID=<security-group-id>

# Allow PostgreSQL port 5432
aws ec2 authorize-security-group-ingress \
  --group-id $RDS_SG_ID \
  --protocol tcp \
  --port 5432 \
  --source-group <your-app-security-group-id>
```

### 2.2 Create DB Subnet Group

```bash
# Create subnet group (use private subnets in different AZs)
aws rds create-db-subnet-group \
  --db-subnet-group-name zerotrust-db-subnet \
  --db-subnet-group-description "ZeroTRUST RDS subnets" \
  --subnet-ids subnet-xxxxx subnet-yyyyy \
  --tags Key=Project,Value=ZeroTRUST
```

### 2.3 Create RDS Instance

```bash
# Create PostgreSQL 15 instance
aws rds create-db-instance \
  --db-instance-identifier zerotrust-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.4 \
  --master-username zerotrust_admin \
  --master-user-password 'YourSecurePassword123!' \
  --allocated-storage 20 \
  --storage-type gp3 \
  --db-name zerotrust_prod \
  --vpc-security-group-ids $RDS_SG_ID \
  --db-subnet-group-name zerotrust-db-subnet \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00" \
  --preferred-maintenance-window "sun:04:00-sun:05:00" \
  --no-publicly-accessible \
  --storage-encrypted \
  --enable-cloudwatch-logs-exports '["postgresql"]' \
  --tags Key=Project,Value=ZeroTRUST Key=Environment,Value=production

# Wait for instance to be available (10-15 minutes)
aws rds describe-db-instances \
  --db-instance-identifier zerotrust-db \
  --query 'DBInstances[0].DBInstanceStatus'
```

### 2.4 Get RDS Endpoint

```bash
# Get the endpoint
aws rds describe-db-instances \
  --db-instance-identifier zerotrust-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text

# Output example: zerotrust-db.abc123xyz.us-east-1.rds.amazonaws.com
```

### 2.5 Export Data from Supabase

```bash
# Get your Supabase connection string
# Format: postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres

# Export schema and data
pg_dump "postgresql://postgres:your-password@db.abc123.supabase.co:5432/postgres" \
  --schema=public \
  --no-owner \
  --no-acl \
  > supabase_export.sql

# Alternatively, export only schema
pg_dump "postgresql://postgres:your-password@db.abc123.supabase.co:5432/postgres" \
  --schema-only \
  --schema=public \
  > supabase_schema.sql
```

### 2.6 Import to RDS

```bash
# Connect via psql (from bastion or local if you set up VPN)
psql "postgresql://zerotrust_admin:YourSecurePassword123!@zerotrust-db.abc123xyz.us-east-1.rds.amazonaws.com:5432/zerotrust_prod" \
  -f supabase_export.sql

# Or use Prisma migrations
cd apps/api-gateway
export DATABASE_URL="postgresql://zerotrust_admin:YourSecurePassword123!@zerotrust-db.abc123xyz.us-east-1.rds.amazonaws.com:5432/zerotrust_prod"
npx prisma migrate deploy
npx prisma db seed  # if you have seed data
```

### 2.7 Update Environment Variables

```bash
DATABASE_URL=postgresql://zerotrust_admin:YourSecurePassword123!@zerotrust-db.abc123xyz.us-east-1.rds.amazonaws.com:5432/zerotrust_prod
```

**✅ Checkpoint**: Verify database connection and data migration

---

## 📍 STEP 3: Amazon DynamoDB (Cache Tier 2) - 1 hour

### 3.1 Create DynamoDB Table

```bash
# Create table with TTL
aws dynamodb create-table \
  --table-name zerotrust-cache-tier2 \
  --attribute-definitions \
      AttributeName=claim_hash,AttributeType=S \
  --key-schema \
      AttributeName=claim_hash,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --tags Key=Project,Value=ZeroTRUST Key=Environment,Value=production

# Enable TTL (auto-delete expired items)
aws dynamodb update-time-to-live \
  --table-name zerotrust-cache-tier2 \
  --time-to-live-specification "Enabled=true, AttributeName=ttl"

# Verify table status
aws dynamodb describe-table \
  --table-name zerotrust-cache-tier2 \
  --query 'Table.TableStatus'
```

### 3.2 Update API Gateway Code

The code already supports DynamoDB! Just set environment variables:

```bash
AWS_REGION=us-east-1
DYNAMODB_TABLE=zerotrust-cache-tier2
```

**✅ Checkpoint**: DynamoDB table created and accessible

---

## 📍 STEP 4: Amazon ECR + ECS (Containers) - 4 hours

### 4.1 Create ECR Repositories

```bash
# Create repositories for each service
aws ecr create-repository \
  --repository-name zerotrust/api-gateway \
  --image-scanning-configuration scanOnPush=true \
  --tags Key=Project,Value=ZeroTRUST

aws ecr create-repository \
  --repository-name zerotrust/verification-engine \
  --image-scanning-configuration scanOnPush=true \
  --tags Key=Project,Value=ZeroTRUST

aws ecr create-repository \
  --repository-name zerotrust/media-analysis \
  --image-scanning-configuration scanOnPush=true \
  --tags Key=Project,Value=ZeroTRUST

# Get login command
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com
```

### 4.2 Build and Push Docker Images

```bash
# Build and push API Gateway
cd apps/api-gateway
docker build -t zerotrust/api-gateway .
docker tag zerotrust/api-gateway:latest <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/zerotrust/api-gateway:latest
docker push <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/zerotrust/api-gateway:latest

# Build and push Verification Engine
cd ../verification-engine
docker build -t zerotrust/verification-engine .
docker tag zerotrust/verification-engine:latest <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/zerotrust/verification-engine:latest
docker push <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/zerotrust/verification-engine:latest

# Build and push Media Analysis
cd ../media-analysis
docker build -f Dockerfile.cpu -t zerotrust/media-analysis .
docker tag zerotrust/media-analysis:latest <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/zerotrust/media-analysis:latest
docker push <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/zerotrust/media-analysis:latest
```

### 4.3 Create ECS Cluster

```bash
# Create ECS cluster
aws ecs create-cluster \
  --cluster-name zerotrust-cluster \
  --capacity-providers FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy \
      capacityProvider=FARGATE,weight=1 \
      capacityProvider=FARGATE_SPOT,weight=3 \
  --tags Key=Project,Value=ZeroTRUST
```

### 4.4 Create IAM Execution Role

```bash
# Create trust policy file
cat > ecs-task-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create execution role
aws iam create-role \
  --role-name zerotrust-ecs-execution-role \
  --assume-role-policy-document file://ecs-task-trust-policy.json

# Attach managed policy
aws iam attach-role-policy \
  --role-name zerotrust-ecs-execution-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Create task role with additional permissions
cat > ecs-task-role-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::zerotrust-media-dev/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:*:table/zerotrust-cache-tier2"
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

aws iam create-role \
  --role-name zerotrust-ecs-task-role \
  --assume-role-policy-document file://ecs-task-trust-policy.json

aws iam put-role-policy \
  --role-name zerotrust-ecs-task-role \
  --policy-name zerotrust-task-policy \
  --policy-document file://ecs-task-role-policy.json
```

### 4.5 Create Task Definitions

See `aws-configs/ecs-task-definitions/` folder (will create next)

### 4.6 Create ECS Services

```bash
# Create security group for ECS tasks
aws ec2 create-security-group \
  --group-name zerotrust-ecs-tasks-sg \
  --description "Security group for ZeroTRUST ECS tasks" \
  --vpc-id <your-vpc-id>

export ECS_SG_ID=<security-group-id>

# Allow inbound from ALB (or all VPC for internal)
aws ec2 authorize-security-group-ingress \
  --group-id $ECS_SG_ID \
  --protocol tcp \
  --port 3000 \
  --cidr <vpc-cidr>

aws ec2 authorize-security-group-ingress \
  --group-id $ECS_SG_ID \
  --protocol tcp \
  --port 8000 \
  --cidr <vpc-cidr>

aws ec2 authorize-security-group-ingress \
  --group-id $ECS_SG_ID \
  --protocol tcp \
  --port 8001 \
  --cidr <vpc-cidr>

# Create services (after task definitions are registered)
aws ecs create-service \
  --cluster zerotrust-cluster \
  --service-name verification-engine \
  --task-definition zerotrust-verification-engine:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx,subnet-yyyyy],securityGroups=[$ECS_SG_ID],assignPublicIp=DISABLED}" \
  --enable-execute-command

# Similar for api-gateway and media-analysis
```

**✅ Checkpoint**: ECS services running and reachable

---

## 📍 STEP 5: AWS Lambda Functions - 3 hours

### 5.1 Create Lambda Execution Role

```bash
# Create Lambda role
cat > lambda-trust-policy.json <<EOF
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

aws iam create-role \
  --role-name zerotrust-lambda-role \
  --assume-role-policy-document file://lambda-trust-policy.json

# Attach managed policies
aws iam attach-role-policy \
  --role-name zerotrust-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole

# Create custom policy
cat > lambda-custom-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:*:table/zerotrust-cache-tier2"
    },
    {
      "Effect": "Allow",
      "Action": [
        "rds:DescribeDBInstances"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name zerotrust-lambda-role \
  --policy-name zerotrust-lambda-custom \
  --policy-document file://lambda-custom-policy.json
```

### 5.2 Create Lambda Layers (for shared dependencies)

Will create in `aws-configs/lambda-layers/`

### 5.3 Create Lambda Functions

Will create in `aws-configs/lambda-functions/`

**✅ Checkpoint**: Lambda functions deployed and testable

---

## 📍 STEP 6: API Gateway - 2 hours

### 6.1 Create REST API

```bash
# Create API
aws apigateway create-rest-api \
  --name zerotrust-api \
  --description "ZeroTRUST Fact Verification API" \
  --endpoint-configuration types=REGIONAL \
  --tags Project=ZeroTRUST,Environment=production

# Note the API ID
export API_ID=<api-id>
```

### 6.2 Get Root Resource ID

```bash
aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query 'items[0].id' \
  --output text

export ROOT_ID=<root-resource-id>
```

### 6.3 Create Resources and Methods

See `aws-configs/api-gateway/` for detailed setup

**✅ Checkpoint**: API Gateway deployed and routing to Lambda

---

## 🎯 Final Architecture

```
CloudFront (optional)
    ↓
API Gateway (REST API)
    ↓
Lambda Functions
    ├─ /verify → verify-lambda → ECS (verification-engine)
    ├─ /history → history-lambda → RDS
    └─ /auth/* → auth-lambda → RDS
    ↓
Caching Strategy:
    ├─ Tier 1: ElastiCache Redis (<1ms)
    ├─ Tier 2: DynamoDB (~5ms)
    └─ Tier 3: RDS PostgreSQL (~20ms)
    ↓
ECS Fargate Services:
    ├─ verification-engine (Python)
    └─ media-analysis (Python)
    ↓
AI/ML:
    ├─ AWS Bedrock (Nova Pro/Lite, Mistral)
    └─ S3 (media storage)
```

---

## 📊 Cost Estimate

| Service | Monthly Cost (Hackathon) |
|---------|-------------------------|
| ElastiCache (t3.micro) | ~$15 |
| RDS (db.t3.micro) | ~$15 |
| DynamoDB (on-demand) | ~$5 |
| ECS Fargate (Spot) | ~$20 |
| Lambda | ~$5 (within free tier) |
| API Gateway | ~$3.50 per 1M requests |
| Data Transfer | ~$10 |
| **Total** | **~$70-80/month** |

---

## 🚨 Troubleshooting

### Common Issues:

1. **Lambda timeout**: Increase timeout to 60s for verification functions
2. **VPC connectivity**: Ensure NAT Gateway for Lambda/ECS internet access
3. **RDS connection**: Check security groups allow port 5432
4. **Redis connection**: Check security groups allow port 6379
5. **ECS tasks failing**: Check CloudWatch logs for errors

---

## 📝 Next Steps

After completing this migration:
1. Set up CloudWatch dashboards
2. Configure auto-scaling for ECS
3. Set up CloudFront (optional)
4. Configure custom domain with Route 53
5. Set up CI/CD pipeline

---

**Ready to start? Begin with Step 1: ElastiCache!**
