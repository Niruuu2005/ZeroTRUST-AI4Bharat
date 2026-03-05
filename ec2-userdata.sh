#!/bin/bash
set -ex
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo "Starting ZeroTRUST setup..."

# Add swap space (2GB) for builds on t3.micro
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Update and install dependencies
yum update -y
yum install -y docker git
service docker start
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

# Create app directory and clone
mkdir -p /opt/zerotrust
cd /opt/zerotrust
git clone https://github.com/Niruuu2005/ZeroTRUST-AI4Bharat .

# Build verification-engine image locally (this takes time)
echo "Building verification-engine..."
cd apps/verification-engine
docker build -t zerotrust-verification-engine:latest .
cd ../..

# Build media-analysis image locally
echo "Building media-analysis..."
cd apps/media-analysis
docker build -f Dockerfile.cpu -t zerotrust-media-analysis:latest .
cd ../..

# Create docker-compose file
cat > docker-compose.yml <<'EOF'
version: '3.8'

services:
  verification-engine:
    image: zerotrust-verification-engine:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres.nokqjcnnlhltdcccpxoq:hkhrjspjgspkj@aws-1-ap-south-1.pooler.supabase.com:5432/postgres
      - DYNAMODB_TABLE=ZeroTrustCache
      - AWS_REGION=us-east-1
      - AWS_BEDROCK_ENABLED=true
    restart: always

  media-analysis:
    image: zerotrust-media-analysis:latest
    ports:
      - "8001:8001"
    environment:
      - S3_BUCKET=zerotrust-media-dev
      - AWS_REGION=us-east-1
    restart: always
EOF

# Start services
docker-compose up -d

echo "✅ ZeroTRUST services started successfully!"
