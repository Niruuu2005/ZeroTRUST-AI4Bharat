# Step 4: Amazon ECS Container Deployment

**Duration**: ~4 hours  
**Prerequisites**: Docker, AWS CLI, ECR access, RDS and ElastiCache endpoints

---

## 🎯 Goal
Deploy your containerized services (API Gateway, Verification Engine, Media Analysis) to ECS Fargate

---

## 📋 Step-by-Step Implementation

### 1. Create Amazon ECR Repositories

```bash
# Create repository for API Gateway
aws ecr create-repository \
  --repository-name zerotrust/api-gateway \
  --image-scanning-configuration scanOnPush=true \
  --encryption-configuration encryptionType=AES256 \
  --region us-east-1 \
  --tags Key=Project,Value=ZeroTRUST Key=Service,Value=api-gateway

# Create repository for Verification Engine
aws ecr create-repository \
  --repository-name zerotrust/verification-engine \
  --image-scanning-configuration scanOnPush=true \
  --encryption-configuration encryptionType=AES256 \
  --region us-east-1 \
  --tags Key=Project,Value=ZeroTRUST Key=Service,Value=verification-engine

# Create repository for Media Analysis
aws ecr create-repository \
  --repository-name zerotrust/media-analysis \
  --image-scanning-configuration scanOnPush=true \
  --encryption-configuration encryptionType=AES256 \
  --region us-east-1 \
  --tags Key=Project,Value=ZeroTRUST Key=Service,Value=media-analysis

# Save repository URIs
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ECR_API_GATEWAY=$AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/zerotrust/api-gateway
export ECR_VERIFICATION=$AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/zerotrust/verification-engine
export ECR_MEDIA=$AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/zerotrust/media-analysis

echo "ECR_API_GATEWAY=$ECR_API_GATEWAY"
echo "ECR_VERIFICATION=$ECR_VERIFICATION"
echo "ECR_MEDIA=$ECR_MEDIA"
```

### 2. Authenticate Docker to ECR

```bash
# Get login password and authenticate
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Verify authentication
docker info | grep -i registry
```

### 3. Build and Push Docker Images

#### Build API Gateway Image

```bash
cd apps/api-gateway

# Build for production
docker build -t zerotrust/api-gateway:latest .

# Tag for ECR
docker tag zerotrust/api-gateway:latest $ECR_API_GATEWAY:latest
docker tag zerotrust/api-gateway:latest $ECR_API_GATEWAY:v1.0.0

# Push to ECR
docker push $ECR_API_GATEWAY:latest
docker push $ECR_API_GATEWAY:v1.0.0

cd ../..
```

#### Build Verification Engine Image

```bash
cd apps/verification-engine

# Build for production
docker build -t zerotrust/verification-engine:latest .

# Tag for ECR
docker tag zerotrust/verification-engine:latest $ECR_VERIFICATION:latest
docker tag zerotrust/verification-engine:latest $ECR_VERIFICATION:v1.0.0

# Push to ECR
docker push $ECR_VERIFICATION:latest
docker push $ECR_VERIFICATION:v1.0.0

cd ../..
```

#### Build Media Analysis Image

```bash
cd apps/media-analysis

# Build for CPU (lighter weight)
docker build -f Dockerfile.cpu -t zerotrust/media-analysis:latest .

# Tag for ECR
docker tag zerotrust/media-analysis:latest $ECR_MEDIA:latest
docker tag zerotrust/media-analysis:latest $ECR_MEDIA:v1.0.0

# Push to ECR
docker push $ECR_MEDIA:latest
docker push $ECR_MEDIA:v1.0.0

cd ../..
```

### 4. Create ECS Cluster

```bash
# Create Fargate cluster
aws ecs create-cluster \
  --cluster-name zerotrust-cluster \
  --capacity-providers FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy \
      capacityProvider=FARGATE_SPOT,weight=4,base=0 \
      capacityProvider=FARGATE,weight=1,base=1 \
  --region us-east-1 \
  --tags Key=Project,Value=ZeroTRUST Key=Environment,Value=production

# Verify cluster creation
aws ecs describe-clusters --clusters zerotrust-cluster --region us-east-1
```

### 5. Create IAM Roles for ECS

#### Task Execution Role (For pulling images and logs)

```bash
# Create trust policy
cat > ecs-task-execution-trust-policy.json <<'EOF'
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
  --assume-role-policy-document file://ecs-task-execution-trust-policy.json \
  --description "ECS task execution role for ZeroTRUST"

# Attach AWS managed policy
aws iam attach-role-policy \
  --role-name zerotrust-ecs-execution-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Get role ARN
aws iam get-role --role-name zerotrust-ecs-execution-role --query 'Role.Arn' --output text
```

#### Task Role (For application permissions)

```bash
# Create task policy
cat > ecs-task-role-policy.json <<'EOF'
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
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::zerotrust-media-dev/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::zerotrust-media-dev"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query",
        "dynamodb:UpdateItem"
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
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:*:secret:zerotrust/*"
    }
  ]
}
EOF

# Create task role
aws iam create-role \
  --role-name zerotrust-ecs-task-role \
  --assume-role-policy-document file://ecs-task-execution-trust-policy.json \
  --description "ECS task role for ZeroTRUST application permissions"

# Attach custom policy
aws iam put-role-policy \
  --role-name zerotrust-ecs-task-role \
  --policy-name zerotrust-task-policy \
  --policy-document file://ecs-task-role-policy.json

# Get role ARN
export TASK_ROLE_ARN=$(aws iam get-role --role-name zerotrust-ecs-task-role --query 'Role.Arn' --output text)
export EXECUTION_ROLE_ARN=$(aws iam get-role --role-name zerotrust-ecs-execution-role --query 'Role.Arn' --output text)
```

### 6. Create Security Group for ECS Tasks

```bash
# Create security group
aws ec2 create-security-group \
  --group-name zerotrust-ecs-tasks-sg \
  --description "Security group for ZeroTRUST ECS tasks" \
  --vpc-id $VPC_ID \
  --region us-east-1

export ECS_SG_ID=<security-group-id-from-output>

# Allow HTTP traffic from within VPC
aws ec2 authorize-security-group-ingress \
  --group-id $ECS_SG_ID \
  --protocol tcp \
  --port 3000 \
  --cidr 10.0.0.0/16 \
  --region us-east-1

aws ec2 authorize-security-group-ingress \
  --group-id $ECS_SG_ID \
  --protocol tcp \
  --port 8000 \
  --cidr 10.0.0.0/16 \
  --region us-east-1

aws ec2 authorize-security-group-ingress \
  --group-id $ECS_SG_ID \
  --protocol tcp \
  --port 8001 \
  --cidr 10.0.0.0/16 \
  --region us-east-1

# Allow all outbound (for internet access via NAT)
aws ec2 authorize-security-group-egress \
  --group-id $ECS_SG_ID \
  --protocol -1 \
  --cidr 0.0.0.0/0 \
  --region us-east-1
```

### 7. Create CloudWatch Log Groups

```bash
# Create log groups for each service
aws logs create-log-group \
  --log-group-name /ecs/zerotrust/api-gateway \
  --region us-east-1

aws logs create-log-group \
  --log-group-name /ecs/zerotrust/verification-engine \
  --region us-east-1

aws logs create-log-group \
  --log-group-name /ecs/zerotrust/media-analysis \
  --region us-east-1

# Set retention (7 days for hackathon)
aws logs put-retention-policy \
  --log-group-name /ecs/zerotrust/api-gateway \
  --retention-in-days 7

aws logs put-retention-policy \
  --log-group-name /ecs/zerotrust/verification-engine \
  --retention-in-days 7

aws logs put-retention-policy \
  --log-group-name /ecs/zerotrust/media-analysis \
  --retention-in-days 7
```

### 8. Register Task Definitions

#### API Gateway Task Definition

```bash
cat > api-gateway-task-def.json <<EOF
{
  "family": "zerotrust-api-gateway",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "$EXECUTION_ROLE_ARN",
  "taskRoleArn": "$TASK_ROLE_ARN",
  "containerDefinitions": [
    {
      "name": "api-gateway",
      "image": "$ECR_API_GATEWAY:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 3000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "NODE_ENV", "value": "production"},
        {"name": "PORT", "value": "3000"},
        {"name": "REDIS_HOST", "value": "$REDIS_ENDPOINT"},
        {"name": "REDIS_PORT", "value": "6379"},
        {"name": "DATABASE_URL", "value": "$DATABASE_URL"},
        {"name": "VERIFICATION_SERVICE_URL", "value": "http://verification-engine.zerotrust.local:8000"},
        {"name": "AWS_REGION", "value": "us-east-1"},
        {"name": "DYNAMODB_TABLE", "value": "zerotrust-cache-tier2"}
      ],
      "secrets": [
        {"name": "JWT_SECRET", "valueFrom": "arn:aws:secretsmanager:us-east-1:$AWS_ACCOUNT_ID:secret:zerotrust/jwt-secret"},
        {"name": "JWT_REFRESH_SECRET", "valueFrom": "arn:aws:secretsmanager:us-east-1:$AWS_ACCOUNT_ID:secret:zerotrust/jwt-refresh-secret"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/zerotrust/api-gateway",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:3000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
EOF

# Register task definition
aws ecs register-task-definition \
  --cli-input-json file://api-gateway-task-def.json \
  --region us-east-1
```

#### Verification Engine Task Definition

```bash
cat > verification-engine-task-def.json <<EOF
{
  "family": "zerotrust-verification-engine",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "$EXECUTION_ROLE_ARN",
  "taskRoleArn": "$TASK_ROLE_ARN",
  "containerDefinitions": [
    {
      "name": "verification-engine",
      "image": "$ECR_VERIFICATION:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"},
        {"name": "PORT", "value": "8000"},
        {"name": "AWS_REGION", "value": "us-east-1"},
        {"name": "BEDROCK_REGION", "value": "us-east-1"},
        {"name": "S3_BUCKET", "value": "zerotrust-media-dev"}
      ],
      "secrets": [
        {"name": "NEWS_API_KEY", "valueFrom": "arn:aws:secretsmanager:us-east-1:$AWS_ACCOUNT_ID:secret:zerotrust/news-api-key"},
        {"name": "GOOGLE_SEARCH_KEY", "valueFrom": "arn:aws:secretsmanager:us-east-1:$AWS_ACCOUNT_ID:secret:zerotrust/google-search-key"},
        {"name": "GOOGLE_SEARCH_ENGINE_ID", "valueFrom": "arn:aws:secretsmanager:us-east-1:$AWS_ACCOUNT_ID:secret:zerotrust/google-cse-id"},
        {"name": "FACT_CHECK_API_KEY", "valueFrom": "arn:aws:secretsmanager:us-east-1:$AWS_ACCOUNT_ID:secret:zerotrust/fact-check-api-key"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/zerotrust/verification-engine",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 120
      }
    }
  ]
}
EOF

# Register task definition
aws ecs register-task-definition \
  --cli-input-json file://verification-engine-task-def.json \
  --region us-east-1
```

### 9. Create ECS Services

#### Create Service Discovery Namespace

```bash
# Create private namespace for service discovery
aws servicediscovery create-private-dns-namespace \
  --name zerotrust.local \
  --vpc $VPC_ID \
  --region us-east-1

# Save namespace ID
export NAMESPACE_ID=<namespace-id-from-output>
```

#### Create Service Discovery Services

```bash
# For Verification Engine
aws servicediscovery create-service \
  --name verification-engine \
  --namespace-id $NAMESPACE_ID \
  --dns-config "NamespaceId=$NAMESPACE_ID,DnsRecords=[{Type=A,TTL=60}]" \
  --health-check-custom-config FailureThreshold=1 \
  --region us-east-1

export VERIFICATION_SD_SERVICE_ID=<service-id-from-output>
```

#### Create ECS Service for Verification Engine

```bash
aws ecs create-service \
  --cluster zerotrust-cluster \
  --service-name verification-engine \
  --task-definition zerotrust-verification-engine:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --platform-version LATEST \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx,subnet-yyyyy],securityGroups=[$ECS_SG_ID],assignPublicIp=DISABLED}" \
  --service-registries "registryArn=arn:aws:servicediscovery:us-east-1:$AWS_ACCOUNT_ID:service/$VERIFICATION_SD_SERVICE_ID" \
  --enable-execute-command \
  --region us-east-1 \
  --tags Key=Project,Value=ZeroTRUST Key=Service,Value=verification-engine
```

#### Create ECS Service for API Gateway

```bash
aws ecs create-service \
  --cluster zerotrust-cluster \
  --service-name api-gateway \
  --task-definition zerotrust-api-gateway:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --platform-version LATEST \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx,subnet-yyyyy],securityGroups=[$ECS_SG_ID],assignPublicIp=DISABLED}" \
  --enable-execute-command \
  --region us-east-1 \
  --tags Key=Project,Value=ZeroTRUST Key=Service,Value=api-gateway
```

### 10. Verify Services are Running

```bash
# Check service status
aws ecs describe-services \
  --cluster zerotrust-cluster \
  --services verification-engine api-gateway \
  --region us-east-1 \
  --query 'services[*].{Name:serviceName,Status:status,Running:runningCount,Desired:desiredCount}'

# Check tasks
aws ecs list-tasks \
  --cluster zerotrust-cluster \
  --region us-east-1

# Get task details
aws ecs describe-tasks \
  --cluster zerotrust-cluster \
  --tasks <task-arn> \
  --region us-east-1
```

### 11. Check CloudWatch Logs

```bash
# View API Gateway logs
aws logs tail /ecs/zerotrust/api-gateway --follow --region us-east-1

# View Verification Engine logs
aws logs tail /ecs/zerotrust/verification-engine --follow --region us-east-1
```

---

## 🔍 Verification Checklist

- [ ] ECR repositories created
- [ ] Docker images built and pushed
- [ ] ECS cluster created
- [ ] IAM roles created and attached
- [ ] Security groups configured
- [ ] CloudWatch log groups created
- [ ] Task definitions registered
- [ ] Services running with desired count
- [ ] Health checks passing
- [ ] Services can communicate internally

---

## 💰 Cost Estimate

**Fargate pricing** (us-east-1):
- vCPU: $0.04048 per vCPU hour
- Memory: $0.004445 per GB hour

**API Gateway** (0.5 vCPU, 1GB):
- ~$16/month (running 24/7)

**Verification Engine** (1 vCPU, 2GB):
- ~$39/month (running 24/7)

**Total**: ~$55/month for both services

**Cost optimization**:
- Use FARGATE_SPOT (70% discount, can be interrupted)
- Scale to zero when not testing
- Use Application Auto Scaling

---

## 🚨 Troubleshooting

See next section for common issues and solutions...

---

**✅ Once complete, proceed to Step 5: Lambda Functions Setup**
