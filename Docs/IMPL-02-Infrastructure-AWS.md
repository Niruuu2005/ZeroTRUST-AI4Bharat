# ZeroTRUST — Infrastructure & AWS Setup
## IMPL-02: Prototype Infrastructure (Local Dev + Minimal AWS)

**Series:** IMPL-02 of 05  
**Scope:** 🚧 PROTOTYPE — simplified single-region, single-AZ, no production HA

> [!IMPORTANT]
> For the prototype, many production configs are simplified: single-AZ instead of Multi-AZ, minimal instance sizes, no SCP/GuardDuty, no CodeDeploy blue/green. The goal is **demo-able** in hours, not production-hardened.

---

## Table of Contents

1. [Quick Start — Local Development](#1-quick-start--local-development)
2. [AWS Architecture (Diagram 5 Reference)](#2-aws-architecture-diagram-5-reference)
3. [VPC & Networking (Prototype)](#3-vpc--networking-prototype)
4. [IAM — Minimal Role Setup](#4-iam--minimal-role-setup)
5. [ECS Fargate — Prototype Task Defs](#5-ecs-fargate--prototype-task-defs)
6. [Database Layer](#6-database-layer)
7. [Caching — Redis + DynamoDB + CloudFront](#7-caching--redis--dynamodb--cloudfront)
8. [S3 Buckets](#8-s3-buckets)
9. [SQS — Media Queue](#9-sqs--media-queue)
10. [Bedrock Configuration](#10-bedrock-configuration)
11. [Environment Variables Reference](#11-environment-variables-reference)

---

## 1. Quick Start — Local Development

### 1.1 Prerequisites

```bash
# Required tools
node --version      # 20.x
python --version    # 3.11.x
docker --version    # 24+
aws --version       # 2.15+

# Configure AWS (for Bedrock access)
aws configure
# Region: us-east-1 (Bedrock lives here per diagram)
# Output: json
```

### 1.2 Clone & Run Locally

```bash
git clone https://github.com/zerotrust-team/zerotrust-aws.git
cd zerotrust-aws

# Start all local services (Postgres, Redis, + all app services)
docker-compose up -d

# Verify
curl http://localhost:3000/health
curl http://localhost:8000/health
open http://localhost:5173
```

### 1.3 docker-compose.yml (Full Local Stack)

```yaml
version: '3.9'

services:
  # ── Data Layer ───────────────────────────────────────────────
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: zerotrust_dev
      POSTGRES_USER: zerotrust
      POSTGRES_PASSWORD: devpassword
    ports: ["5432:5432"]
    volumes: [postgres_data:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U zerotrust"]
      interval: 10s; timeout: 5s; retries: 5

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s; timeout: 3s; retries: 5

  # ── Application Services ─────────────────────────────────────
  api-gateway:
    build:
      context: apps/api-gateway
      target: development
    command: npm run dev
    ports: ["3000:3000"]
    volumes: [./apps/api-gateway/src:/app/src:ro]
    environment:
      NODE_ENV: development
      PORT: "3000"
      DATABASE_URL: postgresql://zerotrust:devpassword@postgres:5432/zerotrust_dev
      REDIS_URL: redis://redis:6379
      JWT_SECRET: dev-secret-change-in-prod-minimum-32chars
      VERIFICATION_ENGINE_URL: http://verification-engine:8000
      MEDIA_ENGINE_URL: http://media-analysis:8001
      RATE_LIMIT_PUBLIC: "10"
    depends_on: {postgres: {condition: service_healthy}, redis: {condition: service_healthy}}

  verification-engine:
    build:
      context: apps/verification-engine
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
    ports: ["8000:8000"]
    volumes: [./apps/verification-engine/src:/app/src:ro]
    environment:
      ENVIRONMENT: development
      PORT: "8000"
      DATABASE_URL: postgresql://zerotrust:devpassword@postgres:5432/zerotrust_dev
      REDIS_URL: redis://redis:6379
      AWS_REGION: us-east-1
      BEDROCK_REGION: us-east-1
      # API keys loaded from .env.local — see §11
    env_file: [.env.local]
    depends_on: {postgres: {condition: service_healthy}, redis: {condition: service_healthy}}

  media-analysis:
    build:
      context: apps/media-analysis
    command: uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
    ports: ["8001:8001"]
    volumes:
      - ./apps/media-analysis/src:/app/src:ro
      - ./models:/app/models:ro         # ML model files
    environment:
      ENVIRONMENT: development
      PORT: "8001"
      MODEL_DIR: /app/models
      REDIS_URL: redis://redis:6379
      AWS_REGION: us-east-1
    env_file: [.env.local]
    depends_on: [redis]

  web-portal:
    build: apps/web-portal
    command: npm run dev -- --host 0.0.0.0
    ports: ["5173:5173"]
    volumes: [./apps/web-portal/src:/app/src:ro]
    environment:
      VITE_API_BASE_URL: http://localhost:3000

volumes:
  postgres_data:
```

### 1.4 .env.local (create this, never commit)

```bash
# External search APIs
NEWS_API_KEY=your_newsapi_key_here
GNEWS_API_KEY=your_gnews_key_here
GOOGLE_SEARCH_KEY=your_google_search_key
GOOGLE_SEARCH_ENGINE_ID=your_cse_id
SERPER_API_KEY=your_serper_key

# Fact-check APIs
SNOPES_API_KEY=optional
AFP_API_KEY=optional

# Social APIs
TWITTER_BEARER_TOKEN=your_bearer_token
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_secret

# Scientific (PubMed — optional, gives higher rate limits)
PUBMED_API_KEY=optional

# AWS (if using Bedrock locally)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1
```

---

## 2. AWS Architecture (Diagram 5 Reference)

> Source: `ZeroTRUST_Architecture_Diagrams.html` — Diagram 5

The VPC lives in **us-east-1** (for Bedrock colocation). Two Availability Zones:

```
Internet
   │
CloudFront + WAF → Route 53 → ALB (public subnets)
                                │
           ┌────────────────────┴──────────────────────────┐
           │         VPC  10.0.0.0/16 (us-east-1)          │
           │                                               │
           │  PUBLIC SUBNET A        PUBLIC SUBNET B        │
           │  10.0.1.0/24 (AZ-a)    10.0.2.0/24 (AZ-b)    │
           │  ALB  |  NAT-GW-a      NAT-GW-b               │
           │                                               │
           │  PRIVATE SUBNET A       PRIVATE SUBNET B       │
           │  10.0.11.0/24 (AZ-a)   10.0.12.0/24 (AZ-b)   │
           │  ECS: API Service       ECS: API Service       │
           │  ECS: Verify Engine     ECS: Verify Engine     │
           │  ECS: Media (GPU)                              │
           │                                               │
           │  DATA SUBNET A          DATA SUBNET B          │
           │  10.0.21.0/24 (AZ-a)   10.0.22.0/24 (AZ-b)   │
           │  RDS Primary            RDS Standby            │
           │  Redis Node 1           Redis Node 2           │
           └───────────────────────────────────────────────┘
                          │ NAT → Internet
                          ▼
         AWS Managed Services (outside VPC):
         Bedrock · DynamoDB · S3 · Neptune · Lambda · CloudWatch
         Textract · Transcribe · Rekognition
```

> [!NOTE]
> **Prototype simplification:** For the prototype demo, use **Single-AZ** (just AZ-a). Remove RDS standby, second Redis node, and NAT-GW-b to reduce AWS cost.

---

## 3. VPC & Networking (Prototype)

### 3.1 Prototype VPC Setup (AWS CLI)

```bash
# Create VPC
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --region us-east-1 \
  --query 'Vpc.VpcId' --output text)
aws ec2 create-tags --resources $VPC_ID --tags Key=Name,Value=zerotrust-vpc

# Enable DNS
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames

# Internet Gateway
IGW_ID=$(aws ec2 create-internet-gateway --query 'InternetGateway.InternetGatewayId' --output text)
aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID

# Subnets (single AZ for prototype — us-east-1a)
PUB_A=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 --availability-zone us-east-1a \
  --query 'Subnet.SubnetId' --output text)
PRIV_A=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.11.0/24 --availability-zone us-east-1a \
  --query 'Subnet.SubnetId' --output text)
DATA_A=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.21.0/24 --availability-zone us-east-1a \
  --query 'Subnet.SubnetId' --output text)

# NAT Gateway (for ECS tasks to call external APIs)
EIP=$(aws ec2 allocate-address --query 'AllocationId' --output text)
NAT_ID=$(aws ec2 create-nat-gateway --subnet-id $PUB_A --allocation-id $EIP \
  --query 'NatGateway.NatGatewayId' --output text)
echo "Wait ~60s for NAT Gateway to become available..."
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_ID

# Route tables
PUB_RT=$(aws ec2 create-route-table --vpc-id $VPC_ID --query 'RouteTable.RouteTableId' --output text)
aws ec2 create-route --route-table-id $PUB_RT --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID
aws ec2 associate-route-table --subnet-id $PUB_A --route-table-id $PUB_RT

PRIV_RT=$(aws ec2 create-route-table --vpc-id $VPC_ID --query 'RouteTable.RouteTableId' --output text)
aws ec2 create-route --route-table-id $PRIV_RT --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT_ID
aws ec2 associate-route-table --subnet-id $PRIV_A --route-table-id $PRIV_RT
aws ec2 associate-route-table --subnet-id $DATA_A --route-table-id $PRIV_RT

echo "VPC setup complete."
echo "VPC_ID=$VPC_ID  PUB_A=$PUB_A  PRIV_A=$PRIV_A  DATA_A=$DATA_A"
```

### 3.2 Security Groups

```bash
# ALB group — internet-facing
SG_ALB=$(aws ec2 create-security-group --group-name sg-alb --description "ALB" \
  --vpc-id $VPC_ID --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress --group-id $SG_ALB --protocol tcp --port 443 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $SG_ALB --protocol tcp --port 80 --cidr 0.0.0.0/0

# API Service (only from ALB)
SG_API=$(aws ec2 create-security-group --group-name sg-api --description "API Service" \
  --vpc-id $VPC_ID --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress --group-id $SG_API --protocol tcp --port 3000 \
  --source-group $SG_ALB

# Verification Engine (only from API service)
SG_VE=$(aws ec2 create-security-group --group-name sg-verification --description "Verification Engine" \
  --vpc-id $VPC_ID --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress --group-id $SG_VE --protocol tcp --port 8000 \
  --source-group $SG_API

# Media Analysis (from API service)
SG_MA=$(aws ec2 create-security-group --group-name sg-media --description "Media Analysis" \
  --vpc-id $VPC_ID --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress --group-id $SG_MA --protocol tcp --port 8001 \
  --source-group $SG_API

# Redis (from API + Verification)
SG_REDIS=$(aws ec2 create-security-group --group-name sg-redis --description "Redis" \
  --vpc-id $VPC_ID --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress --group-id $SG_REDIS --protocol tcp --port 6379 \
  --source-group $SG_API
aws ec2 authorize-security-group-ingress --group-id $SG_REDIS --protocol tcp --port 6379 \
  --source-group $SG_VE

# RDS (from API + Verification)
SG_RDS=$(aws ec2 create-security-group --group-name sg-rds --description "RDS PostgreSQL" \
  --vpc-id $VPC_ID --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress --group-id $SG_RDS --protocol tcp --port 5432 \
  --source-group $SG_API
aws ec2 authorize-security-group-ingress --group-id $SG_RDS --protocol tcp --port 5432 \
  --source-group $SG_VE
```

---

## 4. IAM — Minimal Role Setup

### 4.1 ECS Task Execution Role (shared)

```bash
# Trust policy for ECS tasks
cat > /tmp/ecs-trust.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

aws iam create-role --role-name ecsTaskExecutionRole \
  --assume-role-policy-document file:///tmp/ecs-trust.json
aws iam attach-role-policy --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
```

### 4.2 Verification Engine Task Role (Bedrock access)

```bash
aws iam create-role --role-name zerotrust-verification-task-role \
  --assume-role-policy-document file:///tmp/ecs-trust.json

cat > /tmp/verification-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-haiku-20241022-v1:0",
        "arn:aws:bedrock:us-east-1::foundation-model/mistral.mistral-large-2407-v1:0",
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:Query"],
      "Resource": "arn:aws:dynamodb:us-east-1:*:table/zerotrust-*"
    },
    {
      "Effect": "Allow",
      "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
      "Resource": "arn:aws:logs:us-east-1:*:log-group:/ecs/zerotrust-*"
    }
  ]
}
EOF

aws iam put-role-policy --role-name zerotrust-verification-task-role \
  --policy-name ZeroTrustVerificationPolicy \
  --policy-document file:///tmp/verification-policy.json
```

---

## 5. ECS Fargate — Prototype Task Defs

### 5.1 Create ECR Repositories

```bash
for repo in zerotrust-api-gateway zerotrust-verification zerotrust-media; do
  aws ecr create-repository --repository-name $repo \
    --image-scanning-configuration scanOnPush=true \
    --region us-east-1
  echo "Created: $repo"
done
```

### 5.2 Build & Push Images

```bash
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
ECR="${ACCOUNT}.dkr.ecr.us-east-1.amazonaws.com"
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR

# API Gateway
docker build -t $ECR/zerotrust-api-gateway:latest apps/api-gateway/
docker push $ECR/zerotrust-api-gateway:latest

# Verification Engine
docker build -t $ECR/zerotrust-verification:latest apps/verification-engine/
docker push $ECR/zerotrust-verification:latest

# Media Analysis (GPU build if g4dn available, else CPU-only for prototype)
docker build -f apps/media-analysis/Dockerfile.cpu -t $ECR/zerotrust-media:latest apps/media-analysis/
docker push $ECR/zerotrust-media:latest
```

### 5.3 ECS Cluster + Services

```bash
aws ecs create-cluster --cluster-name zerotrust-prototype --region us-east-1

# Register task definitions (JSON in §5.4 below)
aws ecs register-task-definition --cli-input-json file://infrastructure/task-defs/api-gateway.json
aws ecs register-task-definition --cli-input-json file://infrastructure/task-defs/verification.json

# Create services
aws ecs create-service \
  --cluster zerotrust-prototype \
  --service-name api-gateway \
  --task-definition zerotrust-api-gateway \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={
    subnets=[$PRIV_A],
    securityGroups=[$SG_API],
    assignPublicIp=DISABLED}" \
  --load-balancers "targetGroupArn=$TG_API_ARN,containerName=api-gateway,containerPort=3000"

aws ecs create-service \
  --cluster zerotrust-prototype \
  --service-name verification-engine \
  --task-definition zerotrust-verification \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={
    subnets=[$PRIV_A],
    securityGroups=[$SG_VE],
    assignPublicIp=DISABLED}"
```

### 5.4 API Gateway Task Definition JSON

```json
{
  "family": "zerotrust-api-gateway",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "containerDefinitions": [{
    "name": "api-gateway",
    "image": "ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/zerotrust-api-gateway:latest",
    "portMappings": [{"containerPort": 3000, "protocol": "tcp"}],
    "environment": [
      {"name": "NODE_ENV", "value": "production"},
      {"name": "PORT", "value": "3000"},
      {"name": "VERIFICATION_ENGINE_URL", "value": "http://verification-engine.zerotrust.local:8000"}
    ],
    "secrets": [
      {"name": "DATABASE_URL", "valueFrom": "arn:aws:ssm:us-east-1:ACCOUNT:parameter/zerotrust/db-url"},
      {"name": "JWT_SECRET", "valueFrom": "arn:aws:ssm:us-east-1:ACCOUNT:parameter/zerotrust/jwt-secret"},
      {"name": "REDIS_URL", "valueFrom": "arn:aws:ssm:us-east-1:ACCOUNT:parameter/zerotrust/redis-url"}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/zerotrust-api-gateway",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "ecs",
        "awslogs-create-group": "true"
      }
    },
    "healthCheck": {
      "command": ["CMD-SHELL", "curl -f http://localhost:3000/health || exit 1"],
      "interval": 30, "timeout": 5, "retries": 3, "startPeriod": 60
    }
  }]
}
```

> [!NOTE]
> For prototype, secrets are stored in **AWS SSM Parameter Store** (free tier) instead of Secrets Manager ($0.40/secret/month). See §11 for the parameter names.

---

## 6. Database Layer

### 6.1 RDS PostgreSQL (Prototype)

```bash
# Create DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name zerotrust-subnet-grp \
  --db-subnet-group-description "ZeroTRUST prototype" \
  --subnet-ids $DATA_A

# Create RDS instance (single-AZ, minimal size for prototype)
aws rds create-db-instance \
  --db-instance-identifier zerotrust-postgres \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 15.4 \
  --master-username zerotrust \
  --master-user-password "ChangeThisPassword123!" \
  --db-name zerotrust_prod \
  --vpc-security-group-ids $SG_RDS \
  --db-subnet-group-name zerotrust-subnet-grp \
  --no-multi-az \
  --allocated-storage 20 \
  --storage-type gp2 \
  --backup-retention-period 1 \
  --region us-east-1

aws rds wait db-instance-available --db-instance-identifier zerotrust-postgres
echo "RDS ready"
```

### 6.2 Schema (apply after RDS is ready)

```bash
# From api-gateway directory, run Prisma migrations
cd apps/api-gateway
DATABASE_URL="postgresql://zerotrust:password@<rds-endpoint>:5432/zerotrust_prod" \
  npx prisma migrate deploy
```

```sql
-- Key tables (Prisma generates these from schema.prisma)

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    password_hash VARCHAR(255),
    oauth_provider VARCHAR(50),
    subscription_tier VARCHAR(20) DEFAULT 'free',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_hash VARCHAR(64) NOT NULL,
    claim_text TEXT NOT NULL,
    claim_type VARCHAR(20) NOT NULL,
    credibility_score SMALLINT NOT NULL CHECK (credibility_score BETWEEN 0 AND 100),
    category VARCHAR(30) NOT NULL,
    confidence VARCHAR(10) NOT NULL,
    sources_consulted SMALLINT DEFAULT 0,
    agent_consensus VARCHAR(100),
    evidence_summary JSONB DEFAULT '{}',
    sources JSONB DEFAULT '[]',
    agent_verdicts JSONB DEFAULT '{}',
    limitations JSONB DEFAULT '[]',
    recommendation TEXT,
    processing_time REAL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    source_platform VARCHAR(20),
    cached BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_verifications_claim_hash ON verifications(claim_hash);
CREATE INDEX idx_verifications_user_id ON verifications(user_id);
CREATE INDEX idx_verifications_created ON verifications(created_at DESC);

CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    credibility_tier VARCHAR(10),
    credibility_score REAL,
    category VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 7. Caching — Redis + DynamoDB + CloudFront

### 7.1 ElastiCache Redis (Prototype — single node)

```bash
# Subnet group for Redis
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name zerotrust-redis-subnets \
  --cache-subnet-group-description "ZeroTRUST Redis" \
  --subnet-ids $DATA_A

# Single-node Redis (for prototype)
aws elasticache create-cache-cluster \
  --cache-cluster-id zerotrust-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --engine-version 7.0 \
  --num-cache-nodes 1 \
  --cache-subnet-group-name zerotrust-redis-subnets \
  --security-group-ids $SG_REDIS \
  --region us-east-1

aws elasticache wait cache-cluster-available --cache-cluster-id zerotrust-redis
REDIS_ENDPOINT=$(aws elasticache describe-cache-clusters \
  --cache-cluster-id zerotrust-redis \
  --show-cache-node-info \
  --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address' --output text)
echo "Redis endpoint: $REDIS_ENDPOINT"
```

### 7.2 DynamoDB Table (Tier-2 Cache)

```bash
aws dynamodb create-table \
  --table-name zerotrust-claim-verifications \
  --attribute-definitions \
    AttributeName=claim_hash,AttributeType=S \
    AttributeName=created_at,AttributeType=S \
  --key-schema \
    AttributeName=claim_hash,KeyType=HASH \
    AttributeName=created_at,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --time-to-live-specification Enabled=true,AttributeName=ttl \
  --region us-east-1

# Also create user sessions table
aws dynamodb create-table \
  --table-name zerotrust-user-sessions \
  --attribute-definitions AttributeName=session_id,AttributeType=S \
  --key-schema AttributeName=session_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --time-to-live-specification Enabled=true,AttributeName=ttl \
  --region us-east-1
```

### 7.3 CloudFront Distribution (Tier-3 Cache)

```bash
# Creates CloudFront distribution pointing to ALB
# CloudFront adds edge-cache for popular/trending claims (TTL 30 days)
# Also serves the static web portal from S3

cat > /tmp/cf-config.json <<EOF
{
  "CallerReference": "zerotrust-$(date +%s)",
  "Comment": "ZeroTRUST API + Web Portal",
  "DefaultCacheBehavior": {
    "ViewerProtocolPolicy": "redirect-to-https",
    "CachePolicyId": "4135ea2d-6df8-44a3-9df3-4b5a84be39ad",
    "OriginRequestPolicyId": "b689b0a8-53d0-40ab-baf2-68738e2966ac",
    "TargetOriginId": "api-alb",
    "Compress": true
  },
  "Origins": {
    "Quantity": 1,
    "Items": [{
      "Id": "api-alb",
      "DomainName": "YOUR-ALB-DNS.us-east-1.elb.amazonaws.com",
      "CustomOriginConfig": {
        "HTTPPort": 80, "HTTPSPort": 443,
        "OriginProtocolPolicy": "https-only"
      }
    }]
  },
  "Enabled": true,
  "PriceClass": "PriceClass_100"
}
EOF

aws cloudfront create-distribution --distribution-config file:///tmp/cf-config.json
```

---

## 8. S3 Buckets

```bash
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

# Media uploads bucket
aws s3api create-bucket \
  --bucket zerotrust-media-uploads-$ACCOUNT \
  --region us-east-1
aws s3api put-bucket-cors --bucket zerotrust-media-uploads-$ACCOUNT \
  --cors-configuration '{
    "CORSRules": [{
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["PUT", "POST", "GET"],
      "AllowedOrigins": ["http://localhost:5173", "https://yourdomain.com"],
      "MaxAgeSeconds": 3000
    }]
  }'

# Static web portal bucket
aws s3api create-bucket \
  --bucket zerotrust-static-$ACCOUNT \
  --region us-east-1
aws s3api put-public-access-block --bucket zerotrust-static-$ACCOUNT \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# ML models bucket (for deepfake models)
aws s3api create-bucket \
  --bucket zerotrust-models-$ACCOUNT \
  --region us-east-1
```

---

## 9. SQS — Media Queue

```bash
aws sqs create-queue \
  --queue-name zerotrust-media-queue \
  --attributes '{
    "VisibilityTimeout": "600",
    "MessageRetentionPeriod": "86400",
    "ReceiveMessageWaitTimeSeconds": "20"
  }' \
  --region us-east-1

# Configure S3 → SQS notification
QUEUE_ARN=$(aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/$ACCOUNT/zerotrust-media-queue \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' --output text)

aws s3api put-bucket-notification-configuration \
  --bucket zerotrust-media-uploads-$ACCOUNT \
  --notification-configuration "{
    \"QueueConfigurations\": [{
      \"QueueArn\": \"$QUEUE_ARN\",
      \"Events\": [\"s3:ObjectCreated:*\"]
    }]
  }"
```

---

## 10. Bedrock Configuration

```bash
# Enable model access in AWS Console (manual step):
# AWS Console → Bedrock → Model access → Enable:
#   - Anthropic Claude 3.5 Sonnet v2
#   - Anthropic Claude 3.5 Haiku
#   - Mistral Large 2407
#   - Amazon Titan Text Embeddings G1

# Verify Bedrock access from CLI
aws bedrock list-foundation-models \
  --by-provider anthropic \
  --region us-east-1 \
  --query 'modelSummaries[*].modelId'
```

---

## 11. Environment Variables Reference

### 11.1 SSM Parameters (stores all secrets for ECS)

```bash
# Store all app secrets in SSM Parameter Store (free vs Secrets Manager)
aws ssm put-parameter --name /zerotrust/db-url \
  --value "postgresql://zerotrust:password@<rds-endpoint>:5432/zerotrust_prod" \
  --type SecureString --region us-east-1

aws ssm put-parameter --name /zerotrust/redis-url \
  --value "redis://<redis-endpoint>:6379" \
  --type SecureString --region us-east-1

aws ssm put-parameter --name /zerotrust/jwt-secret \
  --value "$(openssl rand -base64 48)" \
  --type SecureString --region us-east-1

aws ssm put-parameter --name /zerotrust/news-api-key \
  --value "your_newsapi_key" --type SecureString --region us-east-1

aws ssm put-parameter --name /zerotrust/google-search-key \
  --value "your_google_key" --type SecureString --region us-east-1

aws ssm put-parameter --name /zerotrust/google-cse-id \
  --value "your_cse_id" --type SecureString --region us-east-1

aws ssm put-parameter --name /zerotrust/twitter-bearer-token \
  --value "your_bearer_token" --type SecureString --region us-east-1
```

### 11.2 API Gateway Service Env Vars

| Variable | Value | Required |
|----------|-------|---------|
| `NODE_ENV` | `production` | ✅ |
| `PORT` | `3000` | ✅ |
| `DATABASE_URL` | from SSM | ✅ |
| `REDIS_URL` | from SSM | ✅ |
| `JWT_SECRET` | from SSM | ✅ |
| `JWT_ACCESS_EXPIRY` | `15m` | ✅ |
| `JWT_REFRESH_EXPIRY` | `7d` | ✅ |
| `VERIFICATION_ENGINE_URL` | `http://verification-engine.zerotrust.local:8000` | ✅ |
| `MEDIA_ENGINE_URL` | `http://media-analysis.zerotrust.local:8001` | ✅ |
| `RATE_LIMIT_PUBLIC` | `10` | ✅ |
| `AWS_REGION` | `us-east-1` | ✅ |

### 11.3 Verification Engine Env Vars

| Variable | Value | Required |
|----------|-------|---------|
| `ENVIRONMENT` | `production` | ✅ |
| `PORT` | `8000` | ✅ |
| `DATABASE_URL` | from SSM | ✅ |
| `REDIS_URL` | from SSM | ✅ |
| `BEDROCK_REGION` | `us-east-1` | ✅ |
| `NEWS_API_KEY` | from SSM | ✅ |
| `GOOGLE_SEARCH_KEY` | from SSM | ✅ |
| `GOOGLE_SEARCH_ENGINE_ID` | from SSM | ✅ |
| `TWITTER_BEARER_TOKEN` | from SSM | ⚠️ optional |
| `PUBMED_API_KEY` | from SSM | ⚠️ optional |
| `MAX_AGENT_TIMEOUT` | `10` | ✅ |
| `MAX_SOURCES_PER_AGENT` | `20` | ✅ |
