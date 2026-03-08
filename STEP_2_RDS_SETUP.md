# Step 2: Amazon RDS PostgreSQL Setup

**Duration**: ~3 hours  
**Prerequisites**: AWS CLI configured, VPC with private subnets, Supabase data to migrate

---

## 🎯 Goal
Migrate from Supabase to Amazon RDS PostgreSQL for production-grade database

---

## 📋 Step-by-Step Implementation

### 1. Create Security Group for RDS

```bash
# Set your VPC ID
export VPC_ID=<your-vpc-id>

# Create security group
aws ec2 create-security-group \
  --group-name zerotrust-rds-sg \
  --description "Security group for ZeroTRUST PostgreSQL" \
  --vpc-id $VPC_ID \
  --region us-east-1

# Save the output SecurityGroupId
export RDS_SG_ID=<security-group-id-from-output>
```

### 2. Configure Security Group Rules

```bash
# Allow PostgreSQL port 5432 from your application security group
aws ec2 authorize-security-group-ingress \
  --group-id $RDS_SG_ID \
  --protocol tcp \
  --port 5432 \
  --source-group <app-sg-id> \
  --region us-east-1

# For development/testing, allow from entire VPC
aws ec2 authorize-security-group-ingress \
  --group-id $RDS_SG_ID \
  --protocol tcp \
  --port 5432 \
  --cidr 10.0.0.0/16 \
  --region us-east-1

# If you need to connect from your local machine via bastion
# aws ec2 authorize-security-group-ingress \
#   --group-id $RDS_SG_ID \
#   --protocol tcp \
#   --port 5432 \
#   --source-group <bastion-sg-id>
```

### 3. Create DB Subnet Group

```bash
# Create subnet group (use private subnets in at least 2 different AZs)
aws rds create-db-subnet-group \
  --db-subnet-group-name zerotrust-db-subnet \
  --db-subnet-group-description "ZeroTRUST RDS subnets" \
  --subnet-ids subnet-xxxxx subnet-yyyyy subnet-zzzzz \
  --region us-east-1 \
  --tags Key=Project,Value=ZeroTRUST Key=Environment,Value=production
```

### 4. Generate Secure Password

```bash
# Generate a secure random password (save this securely!)
openssl rand -base64 24

# Or use AWS Secrets Manager to generate and store
aws secretsmanager create-secret \
  --name zerotrust/db/master-password \
  --description "ZeroTRUST RDS master password" \
  --generate-random-password PasswordLength=32,ExcludeCharacters='/@"' \
  --region us-east-1

# Get the generated password
aws secretsmanager get-secret-value \
  --secret-id zerotrust/db/master-password \
  --query SecretString \
  --output text
```

### 5. Create RDS PostgreSQL Instance

```bash
# Set master password
export DB_PASSWORD='YourSecurePassword123!'

# Create db.t3.micro instance (hackathon-friendly pricing)
aws rds create-db-instance \
  --db-instance-identifier zerotrust-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.4 \
  --master-username zerotrust_admin \
  --master-user-password "$DB_PASSWORD" \
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
  --enable-cloudwatch-logs-exports '["postgresql","upgrade"]' \
  --auto-minor-version-upgrade \
  --deletion-protection \
  --region us-east-1 \
  --tags Key=Project,Value=ZeroTRUST Key=Environment,Value=production

# For Multi-AZ (recommended for production, 2x cost):
# Add: --multi-az

# For better performance (more cost):
# --db-instance-class db.t3.small
# --iops 3000 --storage-type io1
```

### 6. Wait for Instance to be Available

```bash
# Check status (this takes 10-15 minutes)
watch -n 30 'aws rds describe-db-instances \
  --db-instance-identifier zerotrust-db \
  --region us-east-1 \
  --query "DBInstances[0].DBInstanceStatus" \
  --output text'

# Or check periodically
aws rds describe-db-instances \
  --db-instance-identifier zerotrust-db \
  --region us-east-1 \
  --query 'DBInstances[0].{Status:DBInstanceStatus,Endpoint:Endpoint.Address}' \
  --output table
```

### 7. Get RDS Endpoint

```bash
# Get the connection endpoint
aws rds describe-db-instances \
  --db-instance-identifier zerotrust-db \
  --region us-east-1 \
  --query 'DBInstances[0].Endpoint.{Address:Address,Port:Port}' \
  --output table

# Save this endpoint
export RDS_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier zerotrust-db \
  --region us-east-1 \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text)

echo "RDS Endpoint: $RDS_ENDPOINT"
# Example: zerotrust-db.abc123xyz.us-east-1.rds.amazonaws.com
```

### 8. Export Data from Supabase

#### Option A: Using pg_dump (Complete Backup)

```bash
# Set your Supabase connection details
export SUPABASE_PROJECT=<your-project-id>
export SUPABASE_PASSWORD=<your-supabase-password>

# Export complete database
pg_dump "postgresql://postgres:$SUPABASE_PASSWORD@db.$SUPABASE_PROJECT.supabase.co:5432/postgres" \
  --schema=public \
  --no-owner \
  --no-acl \
  --format=custom \
  --file=supabase_backup.dump

# Or as SQL file
pg_dump "postgresql://postgres:$SUPABASE_PASSWORD@db.$SUPABASE_PROJECT.supabase.co:5432/postgres" \
  --schema=public \
  --no-owner \
  --no-acl \
  > supabase_export.sql
```

#### Option B: Export Schema Only (Then Use Prisma Migrate)

```bash
# Export only schema (structure)
pg_dump "postgresql://postgres:$SUPABASE_PASSWORD@db.$SUPABASE_PROJECT.supabase.co:5432/postgres" \
  --schema-only \
  --schema=public \
  --no-owner \
  > supabase_schema.sql

# Export only data
pg_dump "postgresql://postgres:$SUPABASE_PASSWORD@db.$SUPABASE_PROJECT.supabase.co:5432/postgres" \
  --data-only \
  --schema=public \
  > supabase_data.sql
```

### 9. Connect to RDS Instance

First, ensure you can connect. If RDS is in private subnet, use a bastion host or VPN.

```bash
# Test connection
psql -h $RDS_ENDPOINT \
     -U zerotrust_admin \
     -d zerotrust_prod \
     -c "SELECT version();"

# If successful, you'll see PostgreSQL version info
```

### 10. Import Data to RDS

#### Option A: Restore from Custom Dump

```bash
# Restore using pg_restore
pg_restore -h $RDS_ENDPOINT \
  -U zerotrust_admin \
  -d zerotrust_prod \
  --no-owner \
  --no-acl \
  supabase_backup.dump

# Enter password when prompted
```

#### Option B: Import SQL File

```bash
# Import schema first
psql -h $RDS_ENDPOINT \
     -U zerotrust_admin \
     -d zerotrust_prod \
     -f supabase_schema.sql

# Then import data
psql -h $RDS_ENDPOINT \
     -U zerotrust_admin \
     -d zerotrust_prod \
     -f supabase_data.sql
```

#### Option C: Use Prisma Migrate (Recommended for Clean Start)

```bash
# Navigate to API Gateway directory
cd apps/api-gateway

# Set new DATABASE_URL
export DATABASE_URL="postgresql://zerotrust_admin:$DB_PASSWORD@$RDS_ENDPOINT:5432/zerotrust_prod"

# Run Prisma migrations
npx prisma migrate deploy

# Generate Prisma client
npx prisma generate

# Seed database if you have seed data
npx prisma db seed
```

### 11. Verify Data Migration

```bash
# Connect and check tables
psql -h $RDS_ENDPOINT \
     -U zerotrust_admin \
     -d zerotrust_prod

# In psql:
\dt                          -- List all tables
SELECT COUNT(*) FROM users;  -- Check user count
SELECT COUNT(*) FROM verifications;  -- Check verifications
\q                           -- Exit
```

### 12. Update Application Configuration

#### For API Gateway

Update `apps/api-gateway/.env`:

```bash
# RDS Connection String
DATABASE_URL=postgresql://zerotrust_admin:YourSecurePassword123!@zerotrust-db.abc123xyz.us-east-1.rds.amazonaws.com:5432/zerotrust_prod

# Or use AWS Secrets Manager reference
# DATABASE_URL=arn:aws:secretsmanager:us-east-1:123456789:secret:zerotrust/db/connection-string
```

#### Update Prisma Schema (if needed)

Check `apps/api-gateway/prisma/schema.prisma`:

```prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}
```

### 13. Test Application with RDS

```bash
# Restart API Gateway with new DATABASE_URL
cd apps/api-gateway
npm run dev

# Test database connection
curl http://localhost:3000/health

# Test user registration
curl -X POST http://localhost:3000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@zerotrust.com","password":"Test123!"}'

# Test verification (which saves to DB)
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@zerotrust.com","password":"Test123!"}'
```

### 14. Enable Enhanced Monitoring (Optional)

```bash
# Enable enhanced monitoring (collect metrics every 60 seconds)
aws rds modify-db-instance \
  --db-instance-identifier zerotrust-db \
  --monitoring-interval 60 \
  --monitoring-role-arn arn:aws:iam::YOUR_ACCOUNT_ID:role/rds-monitoring-role \
  --apply-immediately \
  --region us-east-1
```

---

## 🔍 Verification Checklist

- [ ] RDS instance status is "available"
- [ ] Security group allows connections from app
- [ ] Database endpoint accessible from VPC
- [ ] Data successfully migrated from Supabase
- [ ] Table counts match source database
- [ ] Application connects successfully
- [ ] CRUD operations working
- [ ] Prisma migrations applied
- [ ] CloudWatch logs enabled

---

## 💰 Cost Optimization

**db.t3.micro** costs approximately:
- **Single-AZ**: $0.017/hour = ~$12.50/month
- **Multi-AZ**: $0.034/hour = ~$25/month
- **Storage**: ~$2.30/month (20GB gp3)
- **Backups**: First 20GB free

**Total**: ~$15-30/month for hackathon

To save costs:
- Use db.t3.micro (sufficient for testing)
- Single-AZ for non-production
- Delete instance when not testing
- Use Aurora Serverless v2 (pay per second)

---

## 🚨 Troubleshooting

### Cannot connect to RDS
- **Check security group**: Port 5432 must be open
- **Check subnet**: Must be in private subnet with NAT
- **Check bastion**: Use bastion host if no VPN
- **Check credentials**: Verify username/password

### Migration fails
- **Check PostgreSQL versions**: Supabase and RDS should match
- **Check extensions**: Some Supabase extensions may not be available
- **Check permissions**: Use `--no-owner --no-acl` flags

### Slow queries
- **Check connection pooling**: Use PgBouncer or Prisma connection pool
- **Check indexes**: Ensure indexes migrated correctly
- **Check parameters**: RDS parameter group may need tuning

---

## 🔒 Security Best Practices

### 1. Store Credentials in AWS Secrets Manager

```bash
# Create secret for database connection
aws secretsmanager create-secret \
  --name zerotrust/db/connection-string \
  --description "ZeroTRUST RDS connection string" \
  --secret-string "postgresql://zerotrust_admin:$DB_PASSWORD@$RDS_ENDPOINT:5432/zerotrust_prod" \
  --region us-east-1

# Update application to fetch from Secrets Manager
```

### 2. Enable IAM Database Authentication (Optional)

```bash
# Modify instance to enable IAM auth
aws rds modify-db-instance \
  --db-instance-identifier zerotrust-db \
  --enable-iam-database-authentication \
  --apply-immediately
```

### 3. Enable Encryption at Rest

Already enabled with `--storage-encrypted` flag during creation.

### 4. Enable SSL/TLS Connections

In your application:

```bash
DATABASE_URL=postgresql://zerotrust_admin:password@endpoint:5432/db?sslmode=require
```

---

## 📊 Monitoring

### Create CloudWatch Dashboard

```bash
# View CPU utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name CPUUtilization \
  --dimensions Name=DBInstanceIdentifier,Value=zerotrust-db \
  --start-time 2026-03-02T00:00:00Z \
  --end-time 2026-03-02T23:59:59Z \
  --period 3600 \
  --statistics Average \
  --region us-east-1

# View connection count
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=zerotrust-db \
  --start-time 2026-03-02T00:00:00Z \
  --end-time 2026-03-02T23:59:59Z \
  --period 3600 \
  --statistics Average \
  --region us-east-1
```

### Set Up Alarms

```bash
# High CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name zerotrust-rds-high-cpu \
  --alarm-description "Alert when RDS CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=DBInstanceIdentifier,Value=zerotrust-db

# Low storage alarm
aws cloudwatch put-metric-alarm \
  --alarm-name zerotrust-rds-low-storage \
  --alarm-description "Alert when RDS storage < 2GB" \
  --metric-name FreeStorageSpace \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --threshold 2147483648 \
  --comparison-operator LessThanThreshold \
  --evaluation-periods 1 \
  --dimensions Name=DBInstanceIdentifier,Value=zerotrust-db
```

---

## 🔄 Rollback Plan

If you need to rollback to Supabase:

```bash
# Revert DATABASE_URL to Supabase
DATABASE_URL=postgresql://postgres:password@db.project.supabase.co:5432/postgres

# Restart application
npm run dev
```

To delete RDS instance (careful!):

```bash
# Create final snapshot
aws rds create-db-snapshot \
  --db-instance-identifier zerotrust-db \
  --db-snapshot-identifier zerotrust-db-final-snapshot

# Delete instance
aws rds delete-db-instance \
  --db-instance-identifier zerotrust-db \
  --skip-final-snapshot  # Or --final-db-snapshot-identifier for backup
```

---

**✅ Once complete, proceed to Step 3: DynamoDB Setup**
