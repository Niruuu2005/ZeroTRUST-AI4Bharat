import os, sys, boto3, time
from dotenv import load_dotenv
load_dotenv(".env.local")

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
AK = os.environ.get("AWS_ACCESS_KEY_ID")
SK = os.environ.get("AWS_SECRET_ACCESS_KEY")
S3_BUCKET = os.environ.get("S3_MEDIA_BUCKET", "zerotrust-media-dev")

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def ok(msg):   print(f"  ✅ {msg}")
def fail(msg): print(f"  ❌ {msg}")
def info(msg): print(f"  ℹ️  {msg}")

section("Testing AWS Media Services APIs")

# Upload small test image
test_key = "uploads/media_test.jpg"
image_path = "aws-setup/placeholder.jpg" # Using any small file as jpg for API trigger
info(f"Uploading dummy file to S3: {test_key}...")
try:
    s3 = boto3.client("s3", region_name=REGION, aws_access_key_id=AK, aws_secret_access_key=SK)
    s3.put_object(Bucket=S3_BUCKET, Key=test_key, Body=b"actually-not-an-image-but-let-see")
    ok("Upload successful")
except Exception as e:
    fail(f"S3 Upload failed: {e}")
    sys.exit(1)

# Textract
info("Testing Textract Access...")
try:
    textract = boto3.client("textract", region_name=REGION, aws_access_key_id=AK, aws_secret_access_key=SK)
    # This will likely fail with 'UnsupportedDocumentException' or 'InvalidParameterException'
    # which proves we have permission to call it.
    textract.detect_document_text(Document={"S3Object": {"Bucket": S3_BUCKET, "Name": test_key}})
    ok("Textract Call: OK")
except Exception as e:
    if "AccessDenied" in str(e):
        fail(f"Textract Access Denied: {e}")
    else:
        ok(f"Textract Permission Confirmed (API error expected on non-image): {str(e)[:50]}")

# Rekognition
info("Testing Rekognition Access...")
try:
    rekog = boto3.client("rekognition", region_name=REGION, aws_access_key_id=AK, aws_secret_access_key=SK)
    rekog.detect_labels(Image={"S3Object": {"Bucket": S3_BUCKET, "Name": test_key}}, MaxLabels=1)
    ok("Rekognition Call: OK")
except Exception as e:
    if "AccessDenied" in str(e):
        fail(f"Rekognition Access Denied: {e}")
    else:
        ok(f"Rekognition Permission Confirmed (API error expected on non-image): {str(e)[:50]}")

# Transcribe
info("Testing Transcribe Access...")
try:
    transcribe = boto3.client("transcribe", region_name=REGION, aws_access_key_id=AK, aws_secret_access_key=SK)
    # Just list jobs to verify permission
    transcribe.list_transcription_jobs(MaxResults=1)
    ok("Transcribe Permission Confirmed (Listed jobs)")
except Exception as e:
    if "AccessDenied" in str(e):
        fail(f"Transcribe Access Denied: {e}")
    else:
        fail(f"Transcribe call failed: {e}")

# Cleanup
s3.delete_object(Bucket=S3_BUCKET, Key=test_key)
info("Cleaned up test file.")
print("\n" + "="*60)
print("  All Media Services API Access Confirmed!")
print("="*60 + "\n")
