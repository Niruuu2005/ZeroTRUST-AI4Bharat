# ZeroTRUST — AWS Services Overview

> **Read this first.** This document maps every AWS service used in the project to its role in the architecture, and links to the dedicated setup file for each one.

---

## Architecture Diagram (Services)

```
┌────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                │
│   Web Portal (React)   ·   Browser Extension   ·   Mobile         │
└────────────────────┬───────────────────────────────────────────────┘
                     │ HTTPS
┌────────────────────▼───────────────────────────────────────────────┐
│                    API GATEWAY (Express / Node.js)                 │
│   Auth · Rate Limit · JWT · Logging → CloudWatch                  │
└────┬────────────┬────────────────────┬──────────────────┬──────────┘
     │            │                    │                  │
     │ REST        │ S3 Presign         │ DynamoDB TTL     │ CloudWatch
     ▼            ▼                    ▼                  ▼
┌─────────┐  ┌──────────┐      ┌──────────────┐   ┌──────────────┐
│  Redis  │  │   AWS S3 │      │  DynamoDB    │   │  CloudWatch  │
│ (Cache  │  │  (Media  │      │  (Tier-2     │   │  Logs        │
│  Tier1) │  │  Upload) │      │   Cache)     │   │              │
└─────────┘  └────┬─────┘      └──────────────┘   └──────────────┘
                  │ S3 PUT Event
                  ▼
          ┌──────────────┐
          │  AWS Lambda  │
          │ (S3 Trigger) │
          └──────┬───────┘
                 │ POST
                 ▼
  ┌──────────────────────────────────────────┐
  │        Media Analysis Service            │
  │  Textract · Rekognition · Transcribe     │
  └──────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│              Verification Engine (Python / LangGraph)            │
│                                                                  │
│  Manager Agent → Research / News / Scientific /                  │
│                  Social Media / Sentiment / Scraper              │
│                            │                                     │
│                            ▼                                     │
│                     AWS Bedrock                                   │
│          Claude 3.5 Sonnet · Mistral Large · Claude 3.5 Haiku   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Service Inventory

| #   | AWS Service     | Role                                                           | Required?             | Setup File                                               |
| --- | --------------- | -------------------------------------------------------------- | --------------------- | -------------------------------------------------------- |
| 1   | **Bedrock**     | LLM inference for all 6 AI agents (claim verification core)    | ✅ Required           | [02-bedrock-setup.md](02-bedrock-setup.md)               |
| 2   | **S3**          | Presigned uploads for user-submitted media files               | ✅ Required for media | [03-s3-setup.md](03-s3-setup.md)                         |
| 3   | **DynamoDB**    | Tier-2 cache (24-hour TTL on verified claims)                  | ✅ Required for cache | [04-dynamodb-setup.md](04-dynamodb-setup.md)             |
| 4   | **CloudWatch**  | Structured log shipping from API Gateway                       | ⚠️ Optional           | [05-cloudwatch-setup.md](05-cloudwatch-setup.md)         |
| 5   | **Lambda**      | S3 PutObject event → triggers Media Analysis service           | ✅ Required for media | [06-lambda-setup.md](06-lambda-setup.md)                 |
| 6   | **Textract**    | OCR — extract text from uploaded images                        | ✅ Required for media | [07-media-services-setup.md](07-media-services-setup.md) |
| 7   | **Rekognition** | Label detection + content moderation on images/video           | ✅ Required for media | [07-media-services-setup.md](07-media-services-setup.md) |
| 8   | **Transcribe**  | Speech-to-text for uploaded audio/video                        | ✅ Required for media | [07-media-services-setup.md](07-media-services-setup.md) |
| 9   | **IAM**         | Credentials, roles, and least-privilege policies for all above | ✅ Always first       | [01-iam-setup.md](01-iam-setup.md)                       |

---

## Service Roles Explained

### 1. AWS Bedrock (Core — Do This First)

The **brain** of the system. All 6 AI agents in the Verification Engine call Bedrock:

| Agent                             | Model                                       |
| --------------------------------- | ------------------------------------------- |
| Manager (claim orchestration)     | `anthropic.claude-3-5-sonnet-20241022-v2:0` |
| Research Agent                    | `mistral.mistral-large-2407-v1:0`           |
| Sentiment Agent                   | `anthropic.claude-3-5-haiku-20241022-v1:0`  |
| News, Scientific, Social, Scraper | Inherits from manager/research              |
| Fallback chain                    | Sonnet → Haiku → Mistral                    |

Code: `apps/verification-engine/src/integrations/bedrock.py`

### 2. AWS S3

Stores user-uploaded media (images, audio, video) before analysis. The API Gateway generates a **presigned PUT URL** that the client uploads directly to (no data passes through the server).

Code: `apps/api-gateway/src/routes/media.routes.ts`  
Env var needed: `S3_MEDIA_BUCKET`

### 3. AWS DynamoDB

**Tier-2 cache** — sits between Redis (Tier-1, 1hr TTL) and PostgreSQL (Tier-3). Stores serialized verification results with a 24-hour TTL. Uses a single table `zerotrust-claim-verifications` with `claim_hash` as the partition key.

Code: `apps/api-gateway/src/services/CacheService.ts`  
Env var needed: `AWS_REGION`

### 4. AWS CloudWatch Logs

Winston log transport in the API Gateway ships structured JSON logs to a CloudWatch log group. Only active when `CW_LOG_GROUP` env var is set — fully optional for local dev.

Code: `apps/api-gateway/src/utils/cloudwatch-transport.ts`  
Env vars needed: `CW_LOG_GROUP`, `CW_LOG_STREAM_PREFIX`

### 5. AWS Lambda

Triggered by S3 `PutObject` events. When a file is uploaded to the S3 media bucket, Lambda fires and calls the Media Analysis service (`/analyze` endpoint) with the S3 URL. This decouples the upload from the analysis.

Code: `apps/lambda/media-trigger/handler.py`  
Env var needed: `MEDIA_ANALYSIS_URL`

### 6–8. Textract / Rekognition / Transcribe

Used inside the **Media Analysis service** (`apps/media-analysis/src/aws_media.py`):

- **Textract** → OCR text extraction from images
- **Rekognition** → Object labels + content moderation on images, video frame analysis
- **Transcribe** → Async speech-to-text for audio/video files

---

## Setup Order

```
Step 1 → IAM (credentials & policies for everything)
Step 2 → Bedrock (enable model access — needed to run ANY verification)
Step 3 → S3 (create media bucket)
Step 4 → DynamoDB (create cache table)
Step 5 → CloudWatch (create log group — optional)
Step 6 → Lambda (S3 trigger for media pipeline)
Step 7 → Textract / Rekognition / Transcribe (no setup needed — API-based)
Step 8 → Environment Variables (wire everything together)
```

---

## Region

All services must be in **`us-east-1`** (required by Bedrock model availability).  
Do not mix regions — Bedrock, S3, DynamoDB, Lambda, and CloudWatch should all be in `us-east-1`.

---

## Next Step

→ Start with [01-iam-setup.md](01-iam-setup.md)
