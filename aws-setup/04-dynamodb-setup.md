# Step 4 — AWS DynamoDB Setup

> DynamoDB serves as **Tier-2 cache** in the 3-tier caching system. It stores serialised verification results for 24 hours — faster than a DB query but slower than Redis.

---

## Caching Architecture

```
Incoming claim
     │
     ▼
Tier 1: Redis ──hit──► return (< 1 ms)
     │ miss
     ▼
Tier 2: DynamoDB ──hit──► return + backfill Redis (< 10 ms)
     │ miss
     ▼
Tier 3: PostgreSQL ──hit──► return + backfill DynamoDB + Redis (< 50 ms)
     │ miss
     ▼
  Run full AI verification (2–15 s)
  └──► store in all 3 tiers
```

Code: `apps/api-gateway/src/services/CacheService.ts`

---

## 4.1 — Create the DynamoDB Table

### Using AWS Console

> **⚠️ 2026 NOTE:** The global `aws` CLI command may not be on your system PATH. Use the project's venv instead:
> ```powershell
> # Instead of:  aws <command>
> # Use this:    .\venv\python.exe -m awscli <command>
> ```

1. Open [DynamoDB Console](https://console.aws.amazon.com/dynamodb)
2. Click **Create table**
3. Configure:

| Setting | Value |
|---------|-------|
| Table name | `zerotrust-claim-verifications` |
| Partition key | `claim_hash` (String) |
| Sort key | *(leave empty)* |
| Table class | DynamoDB Standard |
| Read/write capacity | **On-demand** (recommended for dev) |

4. Expand **Additional settings**:
   - Enable **Time to Live (TTL)**: attribute name = `ttl`

5. Click **Create table**

### Using AWS CLI (alternative)

```powershell
# Create the table
.\venv\python.exe -m awscli dynamodb create-table `
  --table-name zerotrust-claim-verifications `
  --attribute-definitions AttributeName=claim_hash,AttributeType=S `
  --key-schema AttributeName=claim_hash,KeyType=HASH `
  --billing-mode PAY_PER_REQUEST `
  --region us-east-1

# Enable TTL
.\venv\python.exe -m awscli dynamodb update-time-to-live `
  --table-name zerotrust-claim-verifications `
  --time-to-live-specification Enabled=true,AttributeName=ttl `
  --region us-east-1
```

---

## 4.2 — Table Schema (Reference)

The `CacheService` stores items with this structure:

```json
{
  "claim_hash": "a3f1b2c4d5...",        // Partition key (SHA-256, first 32 chars)
  "created_at": "2026-03-01T10:00:00Z", // ISO timestamp
  "ttl": 1709294400,                    // Unix epoch + 24h
  "result_json": "{...}"                // Full JSON verification result
}
```

The `ttl` attribute matches what you named it in step 4.1 — DynamoDB will auto-delete items when `ttl` passes current time.

---

## 4.3 — Verify Table Exists

```powershell
.\venv\python.exe -m awscli dynamodb describe-table `
  --table-name zerotrust-claim-verifications `
  --region us-east-1 `
  --query "Table.{Name:TableName,Status:TableStatus,TTL:TableArn}"
```

Expected:
```json
{
    "Name": "zerotrust-claim-verifications",
    "Status": "ACTIVE",
    "TTL": "arn:aws:dynamodb:us-east-1:123456789:table/zerotrust-claim-verifications"
}
```

---

## 4.4 — Verification Script (Recommended)

Run the automated verification script to confirm your IAM policy and table access are set up correctly:

```powershell
.\venv\python.exe test_dynamodb.py
```

Expected output:
```text
✅ Table status: ACTIVE
✅ Successfully put test item
✅ Successfully retrieved test item
✅ Successfully removed test item
🚀 DYNAMODB SETUP VERIFIED SUCCESSFULLY!
```

---

## 4.5 — Test Cache Integration

With all services running locally, submit the same claim twice:

```powershell
$claim = '{"claim":"The Eiffel Tower is in Paris","type":"factual"}'
$headers = @{"Content-Type"="application/json"; "Authorization"="Bearer <your-jwt>"}

# First request — cache miss, runs full verification
Invoke-RestMethod -Method Post -Uri "http://localhost:3000/api/v1/verify" `
  -Headers $headers -Body $claim

# Second request (within 24h) — should hit DynamoDB
Invoke-RestMethod -Method Post -Uri "http://localhost:3000/api/v1/verify" `
  -Headers $headers -Body $claim
```

Look for `"cached": true` in the second response.

Check what's stored in DynamoDB:

```powershell
.\venv\python.exe -m awscli dynamodb scan `
  --table-name zerotrust-claim-verifications `
  --max-items 3 `
  --region us-east-1
```

---

## 4.6 — DynamoDB Graceful Degradation

The `CacheService.ts` loads the DynamoDB SDK lazily:

```typescript
async function loadDynamo() {
  try {
    // attempts to load the SDK
    dynamo = new DynamoDBClient(...)
  } catch {
    logger.warn('DynamoDB SDK not available — Tier 2 cache disabled');
  }
}
```

If AWS credentials are invalid or the table doesn't exist:
- A warning is logged
- Tier-2 is skipped silently
- Tier-1 (Redis) and Tier-3 (PostgreSQL) continue functioning
- **The app does not crash**

---

## Cost Estimate

DynamoDB on-demand pricing (`us-east-1`):

| Operation | Price |
|-----------|-------|
| Read request unit | $0.25 per million |
| Write request unit | $1.25 per million |
| Storage | $0.25 per GB/month |

For a typical dev/hackathon workload (thousands of verifications), cost is effectively **< $1/month**.

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `ResourceNotFoundException` | Table not created or wrong region | Create table in `us-east-1` |
| `AccessDeniedException` | IAM policy missing | Ensure `ZeroTrustDevPolicy` is attached to `zerotrust-dev` user |
| `DynamoDB SDK not available` log | SDK failed to init (credentials) | Check `AWS_ACCESS_KEY_ID` in `.env.local` |
| Items not expiring | TTL attribute wrong name | Confirm TTL attribute is `ttl` (lowercase) |

---

## Next Step

→ [05-cloudwatch-setup.md](05-cloudwatch-setup.md)
