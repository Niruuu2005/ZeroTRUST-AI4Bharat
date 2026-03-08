# Step 6 — AWS Lambda Setup (S3 Media Trigger)

> This Lambda function listens for files uploaded to the S3 bucket and **automatically triggers the Media Analysis service**. Without it, media uploads sit in S3 unanalysed unless manually triggered.

---

## How It Works

```
User uploads file via presigned URL
       │
       ▼
S3 bucket receives PUT object event
       │
       ▼
Lambda function fires (handler.py)
       │  POST { "url": "https://bucket.s3.../key", "content_type": "image/jpeg" }
       ▼
Media Analysis service (:8001/analyze)
       │
       ▼
Textract / Rekognition / Transcribe → result stored
```

Code: `apps/lambda/media-trigger/handler.py`

---

## 6.1 — Package the Lambda Function

```powershell
cd "C:\Users\PRIHTVIRAJ\Desktop\ZeroTRUST-AI4Bharat\apps\lambda\media-trigger"

# Create zip (Lambda deployment package — stdlib only, no dependencies needed)
Compress-Archive -Path handler.py -DestinationPath media-trigger.zip -Force

# Verify contents
Get-Item media-trigger.zip | Select-Object Name, Length
```

---

## 6.2 — Create the Lambda Function

### Using AWS Console

1. Open [Lambda Console](https://console.aws.amazon.com/lambda)
2. Click **Create function**
3. Select **Author from scratch**
4. Configure:

| Setting | Value |
|---------|-------|
| Function name | `zerotrust-media-trigger` |
| Runtime | **Python 3.12** |
| Architecture | x86_64 |
| Execution role | **Use an existing role** → `zerotrust-lambda-role` |

5. Click **Create function**
6. In the **Code** tab → **Upload from** → **.zip file** → upload `media-trigger.zip`
7. Click **Deploy**

### Using AWS CLI (alternative)

```powershell
aws lambda create-function `
  --function-name zerotrust-media-trigger `
  --runtime python3.12 `
  --role arn:aws:iam::762102778340:role/zerotrust-lambda-role `
  --handler handler.lambda_handler `
  --zip-file fileb://media-trigger.zip `
  --region us-east-1
```

> Replace `<YOUR_ACCOUNT_ID>` with your 12-digit account ID from `aws sts get-caller-identity`.

---

## 6.3 — Set Lambda Environment Variables

### Using AWS Console

1. Lambda function → **Configuration** tab → **Environment variables** → **Edit**
2. Add:

| Key | Value |
|-----|-------|
| `MEDIA_ANALYSIS_URL` | `http://<your-media-analysis-host>:8001` |

> [!IMPORTANT]
> **Do NOT set `AWS_REGION`** as an environment variable. `AWS_REGION` is a **reserved keyword** in Lambda. AWS provides this automatically. If you try to set it manually, you will get an error: *"Reserved keys used in this request: AWS_REGION"*.

> **For local development**: Lambda cannot reach `localhost:8001`. Options:
> - Use [ngrok](https://ngrok.com) to expose your local service: `ngrok http 8001` → use the HTTPS URL
> - For full cloud testing, deploy the media-analysis service first and use its public URL

### Using AWS CLI

```powershell
aws lambda update-function-configuration `
  --function-name zerotrust-media-trigger `
  --environment "Variables={MEDIA_ANALYSIS_URL=https://your-media-host:8001}" `
  --region us-east-1
```

---

## 6.4 — Configure S3 Event Trigger

### Using AWS Console

1. Open [S3 Console](https://s3.console.aws.amazon.com/s3) → your bucket (`zerotrust-media-dev`)
2. **Properties** tab → scroll to **Event notifications** → **Create event notification**
3. Configure:

| Setting | Value |
|---------|-------|
| Event name | `media-upload-trigger` |
| Prefix | `uploads/` |
| Event types | ✅ `PUT` |
| Destination | **Lambda function** → `zerotrust-media-trigger` |

4. Click **Save changes**

> AWS will automatically add the necessary resource-based policy to the Lambda function.

### Using AWS CLI (alternative)

First add S3 permission to invoke Lambda:

```powershell
aws lambda add-permission `
  --function-name zerotrust-media-trigger `
  --statement-id s3-trigger `
  --action lambda:InvokeFunction `
  --principal s3.amazonaws.com `
  --source-arn arn:aws:s3:::zerotrust-media-dev `
  --region us-east-1
```

Then add the S3 notification:

```powershell
$config = @'
{
  "LambdaFunctionConfigurations": [
    {
      "LambdaFunctionArn": "arn:aws:lambda:us-east-1:762102778340:function:zerotrust-media-trigger",
      "Events": ["s3:ObjectCreated:Put"],
      "Filter": {
        "Key": {
          "FilterRules": [
            {"Name": "prefix", "Value": "uploads/"}
          ]
        }
      }
    }
  ]
}
'@ | Set-Content "$env:TEMP\s3-notif.json"

aws s3api put-bucket-notification-configuration `
  --bucket zerotrust-media-dev `
  --notification-configuration file://$env:TEMP/s3-notif.json
```

---

## 6.5 — Test the Lambda Trigger

Upload a test file and check Lambda logs:

```powershell
# Upload test image
aws s3 cp "C:\Windows\System32\@fusion.dll" `
  s3://zerotrust-media-dev/uploads/test.bin

# Check Lambda logs
aws logs tail /aws/lambda/zerotrust-media-trigger --since 5m --region us-east-1
```

Expected log output:
```
START RequestId: abc123...
Processing S3 event: bucket=zerotrust-media-dev, key=uploads/test.bin
Calling media analysis: https://your-host:8001/analyze
Analysis call status: 200
END RequestId: abc123...
```

---

## 6.6 — Update Lambda After Code Changes

```powershell
cd "C:\Users\PRIHTVIRAJ\Desktop\ZeroTRUST-AI4Bharat\apps\lambda\media-trigger"
Compress-Archive -Path handler.py -DestinationPath media-trigger.zip -Force

aws lambda update-function-code `
  --function-name zerotrust-media-trigger `
  --zip-file fileb://media-trigger.zip `
  --region us-east-1
```

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| Lambda not firing | S3 trigger not configured | Re-check step 6.4 |
| `MEDIA_ANALYSIS_URL not set` | Env var missing | Set it in Lambda configuration |
| Timeout on HTTP call | Media service unreachable | Use ngrok for local; increase Lambda timeout to 30s |
| `AccessDenied` on S3 GetObject | Lambda role missing S3 read | Check `ZeroTrustLambdaS3Read` inline policy |
| `Permission denied invoking Lambda` | S3 not allowed to trigger | Run `lambda add-permission` from step 6.4 |

---

## Lambda Timeout Configuration

Default timeout is 3 seconds — too short for media analysis. Increase it:

```powershell
aws lambda update-function-configuration `
  --function-name zerotrust-media-trigger `
  --timeout 30 `
  --region us-east-1
```

---

## Next Step

→ [07-media-services-setup.md](07-media-services-setup.md)
