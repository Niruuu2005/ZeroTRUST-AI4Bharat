# Step 3 — AWS S3 Setup

> S3 stores user-submitted media files (images, audio, video) that need fact-checking. Files are uploaded **directly from the browser** using presigned URLs — they never pass through your server.

---

## Flow

```
Browser → POST /api/v1/media/presign → API Gateway generates presigned URL
Browser → PUT <presigned-url> → File lands in S3
S3 PutObject event → Lambda fires → Media Analysis runs
```

Code: `apps/api-gateway/src/routes/media.routes.ts`

---

## 3.1 — Create the S3 Bucket

1. Open [S3 Console](https://s3.console.aws.amazon.com/s3)
2. Click **Create bucket**
3. Configure:

| Setting | Value |
|---------|-------|
| Bucket name | `zerotrust-media-dev` *(must be globally unique — confirmed created on 2026-03-01)* |
| AWS Region | `us-east-1` |
| Object Ownership | ACLs disabled (recommended) |
| Block Public Access | ✅ **Block all public access** (keep ON) |
| Versioning | Disabled |
| Default encryption | SSE-S3 (AES-256) — enabled by default |

4. Click **Create bucket**

> **Note the exact bucket name** — you will put it in `.env.local` as `S3_MEDIA_BUCKET`.

---

## 3.2 — Add CORS Configuration

The browser uploads directly to S3 via presigned URL, so CORS must be configured.

1. Open your bucket → **Permissions** tab
2. Scroll to **Cross-origin resource sharing (CORS)** → **Edit**
3. Paste:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["PUT", "GET"],
    "AllowedOrigins": [
      "http://localhost:5173",
      "http://localhost:3000"
    ],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }
]
```

> For production, replace `localhost` entries with your actual domain.

4. Click **Save changes**

---

## 3.3 — Create an uploads/ Prefix Lifecycle Rule

Automatically delete uploaded files after 7 days to avoid storage cost accumulation.

1. Bucket → **Management** tab → **Create lifecycle rule**
2. Configure:

| Setting | Value |
|---------|-------|
| Rule name | `delete-uploads-7d` |
| Prefix | `uploads/` |
| Rule actions | ✅ Expire current versions of objects |
| Days after object creation | `7` |

3. Click **Create rule**

---

## 3.4 — Verify Presign Works

Start the API Gateway locally, then test:

```powershell
# With API Gateway running on port 3000:
$body = '{"contentType":"image/jpeg","extension":"jpg"}'
$response = Invoke-RestMethod -Method Post -Uri "http://localhost:3000/api/v1/media/presign" `
  -ContentType "application/json" -Body $body
$response
```

Expected response:
```json
{
  "uploadUrl": "https://zerotrust-media-dev.s3.us-east-1.amazonaws.com/uploads/uuid.jpg?X-Amz-Algorithm=...",
  "key": "uploads/550e8400-e29b-41d4-a716-446655440000.jpg",
  "expiresIn": 900
}
```

If `S3_MEDIA_BUCKET` is not set, the API returns a clear 503 — the rest of the app still works.

---

## 3.5 — Verify Bucket via Python (venv)

> **Note:** Use the project venv since `aws` CLI may not be on the system PATH.

```powershell
cd "c:\Users\PRIHTVIRAJ\Desktop\ZeroTRUST-AI4Bharat"
.\venv\python.exe verify_s3.py
```

Expected output:
```
--- Verifying S3 Setup for Bucket: zerotrust-media-dev ---
✅ Bucket is reachable.
✅ CORS configuration found.
   Allowed Origins: [['http://localhost:5173', 'http://localhost:3000']]
✅ Lifecycle configuration found.
   Active Rules: ['delete-uploads-7d']
✅ Successfully wrote test file to uploads/connection_test.txt
✅ Successfully deleted test file.
```

---

## Update .env.local

Add to `.env.local` at the project root:

```env
S3_MEDIA_BUCKET=zerotrust-media-dev
AWS_DEFAULT_REGION=us-east-1
```

> **Status (2026-03-01):** Both variables are confirmed present in `.env.local`. ✅

---

## Verification Status (2026-03-01)

| Check | Status |
|-------|--------|
| Bucket `zerotrust-media-dev` created in `us-east-1` | ✅ Done |
| Block all public access ON | ✅ Done |
| CORS configured for `localhost:5173` and `localhost:3000` | ✅ Done |
| Lifecycle rule `delete-uploads-7d` on `uploads/` prefix | ✅ Done |
| IAM inline policy `ZeroTrustS3Access` with CORS + Lifecycle perms | ✅ Done |
| `S3_MEDIA_BUCKET` set in `.env.local` | ✅ Done |
| Write/Delete test to `uploads/` | ✅ Passed |

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| API returns 503 `Media upload not configured` | `S3_MEDIA_BUCKET` not set | Add to `.env.local` and restart API |
| `AccessDenied` on presigned PUT | IAM policy missing `s3:PutObject` for this bucket | Check `ZeroTrustDevPolicy` S3 resource ARN matches bucket name |
| CORS error in browser | CORS rules not saved | Re-check step 3.2 |
| Bucket name already exists | Name is globally unique across all AWS accounts | Try `zerotrust-media-dev-<your-account-id>` |

---

## Next Step

→ [04-dynamodb-setup.md](04-dynamodb-setup.md)
