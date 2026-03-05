# Step 5 — AWS CloudWatch Logs Setup

> **This step is optional for local development.** The API Gateway will log to stdout (visible in your terminal) without CloudWatch. Enable CloudWatch when you want centralised, searchable long-term log retention.

> **⚠️ 2026 NOTE:** The global `aws` CLI command may not be on your system PATH. Use the project's venv instead:
> ```powershell
> # Instead of:  aws <command>
> # Use this:    .\venv\python.exe -m awscli <command>
> ```

---

## How Logging Works

The API Gateway uses **Winston** for structured JSON logging. There are two transports:

1. **Console** — always active, logs to stdout/terminal
2. **CloudWatch** — active only when `CW_LOG_GROUP` env var is set

Code: `apps/api-gateway/src/utils/cloudwatch-transport.ts`

The CloudWatch transport batches log entries and uses the `PutLogEvents` API.

---

## Log Group Structure

```
/zerotrust/
└── api-gateway/
    ├── api-gateway-2026-03-01   (log stream per day)
    ├── api-gateway-2026-03-02
    └── ...
```

---

## 5.1 — Create Log Group

### Using AWS Console ✅ (Recommended)

1. Open [CloudWatch Console](https://console.aws.amazon.com/cloudwatch)
2. Left sidebar → **Logs → Log groups**
3. Click **Create log group**
4. Configure:

| Setting | Value |
|---------|-------|
| Log group name | `/zerotrust/api-gateway` |
| Retention setting | 7 days (or 30 for production) |
| KMS key | None (or your CMK for production) |

5. Click **Create**

> **Note:** Set the retention to **7 days** directly in this dialog. The CLI command for setting retention (`put-retention-policy`) requires the `logs:PutRetentionPolicy` IAM permission, which is **not** included in `ZeroTrustDevPolicy`. Setting it via the Console at creation time avoids this issue entirely.

### Using AWS CLI (alternative)

```powershell
# Create log group
.\venv\python.exe -m awscli logs create-log-group `
  --log-group-name /zerotrust/api-gateway `
  --region us-east-1

# Set 7-day retention
# ⚠️ This will fail with AccessDeniedException unless you add
# logs:PutRetentionPolicy to ZeroTrustDevPolicy.
# Use the Console method above instead.
.\venv\python.exe -m awscli logs put-retention-policy `
  --log-group-name /zerotrust/api-gateway `
  --retention-in-days 7 `
  --region us-east-1
```

> **Known IAM Gap:** `ZeroTrustDevPolicy` includes `logs:PutLogEvents`, `logs:CreateLogStream`, `logs:CreateLogGroup`, and `logs:DescribeLogStreams` — but **not** `logs:PutRetentionPolicy` or `logs:DescribeLogGroups`. If those CLI commands fail with `AccessDeniedException`, that is expected. Use the Console instead.

---

## 5.2 — Update .env.local

Add to the **project root** `.env.local` (`ZeroTRUST-AI4Bharat/.env.local`):

```env
CW_LOG_GROUP=/zerotrust/api-gateway
CW_LOG_STREAM_PREFIX=api-gateway
```

The transport auto-creates a new log stream each day in the format `api-gateway-YYYY-MM-DD`.

---

## 5.3 — Verify Logs Appearing

### Option A — Python Script (No Docker Required) ✅ Recommended

The full API Gateway server requires **Docker** (for Postgres and Redis) to start. If you don't have Docker, use the standalone Python verification script instead:

```powershell
.\venv\python.exe test_cloudwatch.py
```

This script (located at the project root) will:
1. Create the daily log stream (`api-gateway-YYYY-MM-DD`) in the log group
2. Send a test JSON log event simulating a `GET /health 200` request
3. Confirm the stream is visible via `describe_log_streams`

Expected output:
```
=== CloudWatch Log Verification ===
Log Group:   /zerotrust/api-gateway
Log Stream:  api-gateway-2026-03-02
Region:      us-east-1

[+] Created log stream: api-gateway-2026-03-02
[+] Log event sent successfully!
    Message: {
      "level": "info",
      "message": "GET /health 200",
      ...
    }
[+] Stream confirmed in CloudWatch:
    Name:  api-gateway-2026-03-02
    ...
```

Then open [CloudWatch → Log groups → /zerotrust/api-gateway](https://console.aws.amazon.com/cloudwatch/home#logsV2:log-groups/log-group/$252Fzerotrust$252Fapi-gateway) and confirm the stream and event are visible.

---

### Option B — Via Full API Server (Requires Docker)

> **⚠️ This option requires Docker Desktop to be installed and running.** The API Gateway depends on Postgres (`localhost:5432`) and Redis (`localhost:6379`), which are managed via Docker Compose. Without them, the server crashes before binding to port 3000 and `npm run dev` exits with `Can't reach database server at localhost:5432`.

**Step 1 — Start the data layer from the project root:**

```powershell
docker compose up postgres redis -d
```

Wait ~10 seconds for Postgres to become healthy.

**Step 2 — Install dependencies (first time only):**

```powershell
cd apps/api-gateway
npm install
```

**Step 3 — Start the API Gateway:**

```powershell
npm run dev
```

Expected output:
```
[dotenv] injecting env from .env.local
info: Redis connected
info: PostgreSQL connected
info: API Gateway running on port 3000 [development]
```

**Step 4 — Send a health check request** (from a second terminal at project root):

```powershell
Invoke-RestMethod http://localhost:3000/health
```

**Step 5 — Check CloudWatch:**

```powershell
.\venv\python.exe -m awscli logs describe-log-streams `
  --log-group-name /zerotrust/api-gateway `
  --region us-east-1

.\venv\python.exe -m awscli logs get-log-events `
  --log-group-name /zerotrust/api-gateway `
  --log-stream-name "api-gateway-2026-03-02" `
  --limit 10 `
  --region us-east-1
```

You should see JSON log entries like:

```json
{
  "level": "info",
  "message": "GET /health 200",
  "timestamp": "2026-03-01T10:00:00.000Z",
  "service": "api-gateway",
  "method": "GET",
  "path": "/health",
  "status": 200,
  "duration": 3
}
```

---

## 5.4 — Create a Metric Filter for Errors (Optional)

Track 5xx errors with a CloudWatch metric:

```powershell
.\venv\python.exe -m awscli logs put-metric-filter `
  --log-group-name /zerotrust/api-gateway `
  --filter-name "5xxErrors" `
  --filter-pattern '{ $.status >= 500 }' `
  --metric-transformations `
    metricName=ServerErrors,metricNamespace=ZeroTRUST,metricValue=1 `
  --region us-east-1
```

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| No logs appearing | `CW_LOG_GROUP` not set | Add to `.env.local` at the **project root** and restart API |
| `ResourceNotFoundException` | Log group not created | Run step 5.1 |
| `AccessDeniedException` on `put-retention-policy` | `ZeroTrustDevPolicy` lacks `logs:PutRetentionPolicy` | Set retention via the Console dialog when creating the log group — expected, not a blocker |
| `AccessDeniedException` on `describe-log-groups` | `ZeroTrustDevPolicy` lacks `logs:DescribeLogGroups` | Verify via the AWS Console instead — expected, not a blocker |
| `AccessDeniedException` on `logs:PutLogEvents` | IAM missing `logs:PutLogEvents` | Check `ZeroTrustDevPolicy` CloudWatch statement (resource must match `/zerotrust/*`) |
| `Can't reach database server at localhost:5432` | Postgres not running (Docker not started) | Use Option A (Python script) to verify CloudWatch without Docker |
| `npm run dev` exits immediately | Postgres unavailable | Start `docker compose up postgres redis -d` first, or use the Python script instead |
| `tsx` not recognised | `npm install` not run | Run `npm install` in `apps/api-gateway` first |
| Sequence token errors | Concurrent writers | The transport handles `InvalidSequenceTokenException` — auto-recovers |

---

## Next Step

→ [06-lambda-setup.md](06-lambda-setup.md)
