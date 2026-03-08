# Step 1 — IAM Setup

> **Do this before anything else.** All other AWS services depend on the credentials and permissions you configure here.

> **⚠️ 2026 NOTE:** The global `aws` CLI command may not be on your system PATH. Use the project's venv instead:
> ```powershell
> # Instead of:  aws <command>
> # Use this:    .\venv\python.exe -m awscli <command>
> ```

---

## What You're Creating

| What | Why |
|------|-----|
| IAM User `zerotrust-dev` | Programmatic credentials for local development |
| IAM Policy `ZeroTrustDevPolicy` | Least-privilege access to Bedrock, S3, DynamoDB, CloudWatch, Lambda, Textract, Rekognition, Transcribe |
| IAM Role `zerotrust-lambda-role` | Runtime role for the Lambda function (separate from dev credentials) |

---

## 1.1 — Create IAM User

1. Open [IAM Console → Users](https://console.aws.amazon.com/iam/home#/users)
2. Click **Create user**
3. Username: `zerotrust-dev`
4. Select **"Provide user access to AWS Management Console"** → **No** (programmatic only)
5. Click **Next → Next → Create user**

---

## 1.2 — Create the Dev Policy

1. Go to [IAM Console → Policies](https://console.aws.amazon.com/iam/home#/policies)
2. Click **Create policy** → **JSON** tab
3. Paste the following policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock:ListFoundationModels",
        "bedrock:GetFoundationModel"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3MediaBucket",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:GetObjectAttributes"
      ],
      "Resource": "arn:aws:s3:::zerotrust-media-*/*"
    },
    {
      "Sid": "S3MediaBucketList",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": "arn:aws:s3:::zerotrust-media-*"
    },
    {
      "Sid": "DynamoDBCache",
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:DescribeTable"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:*:table/zerotrust-claim-verifications"
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams"
      ],
      "Resource": "arn:aws:logs:us-east-1:*:log-group:/zerotrust/*:*"
    },
    {
      "Sid": "TextractAccess",
      "Effect": "Allow",
      "Action": [
        "textract:DetectDocumentText",
        "textract:AnalyzeDocument"
      ],
      "Resource": "*"
    },
    {
      "Sid": "RekognitionAccess",
      "Effect": "Allow",
      "Action": [
        "rekognition:DetectLabels",
        "rekognition:DetectModerationLabels",
        "rekognition:StartLabelDetection",
        "rekognition:GetLabelDetection"
      ],
      "Resource": "*"
    },
    {
      "Sid": "TranscribeAccess",
      "Effect": "Allow",
      "Action": [
        "transcribe:StartTranscriptionJob",
        "transcribe:GetTranscriptionJob",
        "transcribe:ListTranscriptionJobs"
      ],
      "Resource": "*"
    }
  ]
}
```

> **Note (updated 2026-03-01):** The AWS-managed policy `AmazonBedrockFullAccess` was also attached directly to `zerotrust-dev` to resolve cross-region inference profile access issues with Nova and Mistral models.

4. Name: `ZeroTrustDevPolicy`
5. Description: `ZeroTRUST local development — least-privilege access`
6. Click **Create policy**

---

## 1.3 — Attach Policy to User

1. Go back to **IAM → Users → zerotrust-dev**
2. **Permissions** tab → **Add permissions** → **Attach policies directly**
3. Search `ZeroTrustDevPolicy` → check it → **Next → Add permissions**

> **2026-03-01 UPDATE — Additional Inline Policy:**  
> An additional **inline policy** named `ZeroTrustS3Access` was added directly to the user to grant full S3 bucket management access for the `zerotrust-media-dev` bucket. Use **Add permissions → Create inline policy** and paste the following JSON:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket",
                "s3:GetBucketCORS",
                "s3:PutBucketCORS",
                "s3:GetLifecycleConfiguration",
                "s3:PutLifecycleConfiguration"
            ],
            "Resource": [
                "arn:aws:s3:::zerotrust-media-dev",
                "arn:aws:s3:::zerotrust-media-dev/*"
            ]
        }
    ]
}
```
> **Policy name:** `ZeroTrustS3Access`

---

## 1.4 — Generate Access Keys

1. **IAM → Users → zerotrust-dev → Security credentials** tab
2. Scroll to **Access keys** → **Create access key**
3. Use case: **Command Line Interface (CLI)**
4. Acknowledge the recommendation warning → **Next**
5. Tag (optional): `project=zerotrust`
6. Click **Create access key**
7. **⚠️ Download the CSV or copy both keys NOW** — the secret is shown only once

You will get:
```
Access key ID:     AKIAIOSFODNN7EXAMPLE
Secret access key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

---

## 1.5 — Create Lambda Execution Role

The Lambda function needs its own role (separate from your dev credentials).

1. Go to [IAM Console → Roles](https://console.aws.amazon.com/iam/home#/roles)
2. Click **Create role**
3. Trusted entity: **AWS service** → **Lambda**
4. Click **Next**
5. Search and attach:
   - `AWSLambdaBasicExecutionRole` (AWS managed — CloudWatch Logs from Lambda)
6. Click **Next**
7. Role name: `zerotrust-lambda-role`
8. Click **Create role**

Then add inline S3 read permission for the Lambda trigger:

1. Open **IAM → Roles → zerotrust-lambda-role**
2. **Add permissions → Create inline policy** → JSON:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3ReadForLambda",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:GetObjectAttributes"],
      "Resource": "arn:aws:s3:::zerotrust-media-*/*"
    }
  ]
}
```

3. Name: `ZeroTrustLambdaS3Read` → **Create policy**

---

## 1.6 — Configure AWS CLI (puts keys into your environment)

> **⚠️ 2026 NOTE:** If `aws` is not recognised as a global command, use the project venv instead:

```powershell
# Option A — if aws is on your PATH globally
aws configure

# Option B — using the project venv (always works)
.\venv\python.exe -m awscli configure
```

Enter when prompted:
```
AWS Access Key ID [None]:     <paste your key>
AWS Secret Access Key [None]: <paste your secret>
Default region name [None]:   us-east-1
Default output format [None]: json
```

Verify it works:
```powershell
# Using venv (recommended)
.\venv\python.exe -m awscli sts get-caller-identity
```

Expected output:
```json
{
    "UserId": "AIDA3C4G5RHSFM3EEMZLT",
    "Account": "762102778340",
    "Arn": "arn:aws:iam::762102778340:user/zerotrust-dev"
}
```

> **⚠️ Note on `--max-items`:** The `bedrock list-foundation-models` command in the installed CLI version does **not** support `--max-items`. Use `--query` to filter instead.

---

## 1.7 — Update .env.local

Create (or update) `.env.local` at the **project root** (`ZeroTRUST-AI4Bharat/.env.local`):

> **⚠️ Important:** The test scripts load credentials from the **project root** `.env.local`, NOT from `aws-setup/.env.local`. Copy the file if needed:
> ```powershell
> cp aws-setup\.env.local .env.local
> ```

```env
AWS_ACCESS_KEY_ID=<your-access-key-id>
AWS_SECRET_ACCESS_KEY=<your-secret-access-key>
AWS_DEFAULT_REGION=us-east-1

# 2026 Active Models — bypass Anthropic marketplace/billing blocks
# (Anthropic Claude models require a credit card on file, not UPI)
MANAGER_MODEL_ID=us.amazon.nova-pro-v1:0
RESEARCH_MODEL_ID=us.mistral.pixtral-large-2502-v1:0
SENTIMENT_MODEL_ID=us.amazon.nova-lite-v1:0
```

---

## Verification Checklist

- [x] `.\venv\python.exe -m awscli sts get-caller-identity` returns `arn:aws:iam::762102778340:user/zerotrust-dev`
- [x] `.env.local` exists at the **project root** with valid `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
- [x] `aws-setup/.env.local` also has the same keys (synced)
- [x] `AmazonBedrockFullAccess` (AWS managed) attached to `zerotrust-dev`
- [x] `ZeroTrustDevPolicy` (custom) attached to `zerotrust-dev`
- [x] `ZeroTrustS3Access` (inline) attached to `zerotrust-dev` — grants CORS, Lifecycle & object access
- [x] `python-dotenv` installed in venv: `.\venv\python.exe -m pip install python-dotenv`
- [ ] `zerotrust-lambda-role` exists with `AWSLambdaBasicExecutionRole` + inline S3 read *(set up when Lambda is deployed)*

---

## Next Step

→ [02-bedrock-setup.md](02-bedrock-setup.md)
