# Step 7 — AWS Media Services Setup (Textract, Rekognition, Transcribe)

> These three services require **no provisioning** — they are fully managed APIs. You just need the correct IAM permissions (already covered in `01-iam-setup.md`) and to understand how the code uses them.

---

## Services Overview

| Service | Purpose in ZeroTRUST | Input | Output |
|---------|---------------------|-------|--------|
| **Textract** | Extract text from uploaded images (OCR) | S3 bucket + key | Text lines, blocks |
| **Rekognition** | Detect objects, labels, content moderation in images | S3 bucket + key | Labels + moderation flags |
| **Transcribe** | Convert audio/video to text (async) | S3 URI | Transcript text |

Code: `apps/media-analysis/src/aws_media.py`

---

## 7.1 — Verify IAM Permissions

Confirm your `ZeroTrustDevPolicy` includes these statements (from step 1):

```json
"textract:DetectDocumentText",
"textract:AnalyzeDocument",
"rekognition:DetectLabels",
"rekognition:DetectModerationLabels",
"rekognition:StartLabelDetection",
"rekognition:GetLabelDetection",
"transcribe:StartTranscriptionJob",
"transcribe:GetTranscriptionJob",
"transcribe:ListTranscriptionJobs"
```

Quick check:
```powershell
aws iam simulate-principal-policy `
  --policy-source-arn arn:aws:iam::762102778340:user/zerotrust-dev `
  --action-names textract:DetectDocumentText rekognition:DetectLabels transcribe:StartTranscriptionJob `
  --resource-arns "*" `
  --query "EvaluationResults[].{Action:EvalActionName,Decision:EvalDecision}"
```

All three should show `allowed`.

---

## 7.2 — Textract: Image OCR

### What the code does

```python
# apps/media-analysis/src/aws_media.py
def analyze_image_textract(bucket: str, key: str) -> dict:
    client = boto3.client("textract", region_name=REGION)
    resp = client.detect_document_text(Document={"S3Object": {"Bucket": bucket, "Name": key}})
    lines = [item["Text"] for item in resp["Blocks"] if item["BlockType"] == "LINE"]
    return {"text": "\n".join(lines), "block_count": len(resp["Blocks"])}
```

### Test it manually

Upload a test image to S3 first:
```powershell
aws s3 cp C:\path\to\test-image.jpg s3://zerotrust-media-dev/uploads/test.jpg
```

Then test via the media analysis API (with the service running):
```powershell
$body = '{"url":"https://zerotrust-media-dev.s3.us-east-1.amazonaws.com/uploads/test.jpg","content_type":"image/jpeg"}'
Invoke-RestMethod -Method Post -Uri "http://localhost:8001/analyze" `
  -ContentType "application/json" -Body $body
```

### Direct CLI test

```powershell
aws textract detect-document-text `
  --document '{"S3Object":{"Bucket":"zerotrust-media-dev","Name":"uploads/test.jpg"}}' `
  --region us-east-1 `
  --query "Blocks[?BlockType=='LINE'].Text"
```

---

## 7.3 — Rekognition: Image/Video Analysis

### What the code does

```python
# Image labels
label_resp = client.detect_labels(Image={"S3Object": {"Bucket": bucket, "Name": key}}, MaxLabels=20)
# Content moderation
mod_resp = client.detect_moderation_labels(Image={"S3Object": {"Bucket": bucket, "Name": key}})
```

### Test it manually

```powershell
# Detect labels in a test image
aws rekognition detect-labels `
  --image '{"S3Object":{"Bucket":"zerotrust-media-dev","Name":"uploads/test.jpg"}}' `
  --max-labels 10 `
  --region us-east-1 `
  --query "Labels[].{Name:Name,Confidence:Confidence}"

# Check for moderation flags (adult content, violence, etc.)
aws rekognition detect-moderation-labels `
  --image '{"S3Object":{"Bucket":"zerotrust-media-dev","Name":"uploads/test.jpg"}}' `
  --region us-east-1
```

### Supported Image Formats

| Format | Textract | Rekognition |
|--------|----------|-------------|
| JPEG | ✅ | ✅ |
| PNG | ✅ | ✅ |
| PDF | ✅ | ❌ |
| TIFF | ✅ | ❌ |
| GIF | ❌ | ✅ |
| WEBP | ❌ | ✅ |

---

## 7.4 — Transcribe: Audio/Video Speech-to-Text

### What the code does (async/poll pattern)

```python
# Start job
client.start_transcription_job(
    TranscriptionJobName=job_name,
    Media={"MediaFileUri": f"s3://{bucket}/{key}"},
    MediaFormat=key.split(".")[-1],  # mp3, mp4, wav, etc.
    LanguageCode="en-US",
)

# Poll every 3s until COMPLETED or FAILED (max 120s timeout)
while time.time() - start < 120:
    status = client.get_transcription_job(...)["TranscriptionJob"]["TranscriptionJobStatus"]
    if status == "COMPLETED":
        # fetch transcript from S3 URL in job output
```

### Test it manually

Upload an audio file:
```powershell
aws s3 cp C:\path\to\audio.mp3 s3://zerotrust-media-dev/uploads/test.mp3
```

Start a transcription job:
```powershell
aws transcribe start-transcription-job `
  --transcription-job-name "zerotrust-test-job" `
  --media MediaFileUri=s3://zerotrust-media-dev/uploads/test.mp3 `
  --media-format mp3 `
  --language-code en-US `
  --region us-east-1

# Poll for completion
aws transcribe get-transcription-job `
  --transcription-job-name "zerotrust-test-job" `
  --region us-east-1 `
  --query "TranscriptionJob.{Status:TranscriptionJobStatus,Transcript:Transcript.TranscriptFileUri}"
```

### Supported Audio/Video Formats

`mp3`, `mp4`, `wav`, `flac`, `ogg`, `amr`, `webm`

---

## 7.5 — Full Media Analysis Flow Test

With the media-analysis service running locally:

```powershell
# Activate venv
cd "C:\Users\PRIHTVIRAJ\Desktop\ZeroTRUST-AI4Bharat\apps\media-analysis"
.venv\Scripts\Activate.ps1

# Start service
uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
```

In another terminal:
```powershell
# Test with an S3 image URL
$body = @{
  url = "https://zerotrust-media-dev.s3.us-east-1.amazonaws.com/uploads/test.jpg"
  content_type = "image/jpeg"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://localhost:8001/analyze" `
  -ContentType "application/json" -Body $body
```

Expected response shape:
```json
{
  "status": "success",
  "source_url": "https://...",
  "media_type": "image",
  "textract": { "text": "extracted text...", "block_count": 14 },
  "rekognition": {
    "labels": [{"name": "Document", "confidence": 99.2}],
    "moderation": null
  }
}
```

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `SubscriptionRequiredException` | AWS requires a verified credit card for Marketplace services (common in India) | Login to AWS Root account → Billing → Payment Methods. Support for UPI/GPay is limited for these services. |
| `AccessDeniedException` | IAM policy is missing or only partially applied | Verify `ZeroTrustDevPolicy` contains **all 8 services**. Use the JSON editor, not the visual builder. |
| `InvalidS3ObjectException` | File missing or IAM cannot read S3 metadata | If you get this during a test with a "non-existent" file, it actually means your **IAM permissions are working** (the call was allowed). Just upload a real file to fix. |
| `UnsupportedDocumentException` | Wrong format for Textract | Use JPEG/PNG/PDF/TIFF |
| Transcribe `ClientError: job already exists` | Job name collision | Job names must be unique; code uses timestamp prefix |
| Timeout on Transcribe | Audio file too long for 120s poll | Increase `TRANSCRIBE_POLL_TIMEOUT` in `aws_media.py` |

---

## Cost Estimate

| Service | Price |
|---------|-------|
| Textract | $1.50 per 1,000 pages |
| Rekognition labels | $1.00 per 1,000 images |
| Rekognition moderation | $1.00 per 1,000 images |
| Transcribe | $0.024 per minute of audio |

---

## Next Step

→ [08-env-config.md](08-env-config.md)
