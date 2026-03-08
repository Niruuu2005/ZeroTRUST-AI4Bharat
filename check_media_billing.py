import os, sys, boto3, traceback
from dotenv import load_dotenv
load_dotenv(".env.local")

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
AK = os.environ.get("AWS_ACCESS_KEY_ID")
SK = os.environ.get("AWS_SECRET_ACCESS_KEY")
S3_BUCKET = os.environ.get("S3_MEDIA_BUCKET", "zerotrust-media-dev")

def test_service(name, client_name, method_name, **kwargs):
    print(f"\n--- Testing {name} ---")
    try:
        client = boto3.client(client_name, region_name=REGION, aws_access_key_id=AK, aws_secret_access_key=SK)
        method = getattr(client, method_name)
        method(**kwargs)
        print(f"✅ {name} Success")
    except Exception as e:
        print(f"❌ {name} Error: {type(e).__name__}")
        print(str(e))

test_service("Rekognition", "rekognition", "detect_labels", Image={"S3Object": {"Bucket": S3_BUCKET, "Name": "uploads/non-existent.jpg"}}, MaxLabels=1)
test_service("Textract", "textract", "detect_document_text", Document={"S3Object": {"Bucket": S3_BUCKET, "Name": "uploads/non-existent.jpg"}})
test_service("Transcribe", "transcribe", "list_transcription_jobs", MaxResults=1)
