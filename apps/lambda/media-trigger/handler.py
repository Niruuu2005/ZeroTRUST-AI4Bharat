"""
Lambda handler: S3 Put trigger → invoke Media Analysis service.

Configure: S3 bucket event on Put (suffix .jpg/.png/.mp4/.mp3 etc.) → this Lambda.
Env: MEDIA_ANALYSIS_URL (e.g. https://xxx.execute-api.region.amazonaws.com/analyze or internal URL).
"""
import os
import json
import urllib.request
import urllib.error
import urllib.parse

MEDIA_URL = os.environ.get("MEDIA_ANALYSIS_URL", "").rstrip("/")
REGION = os.environ.get("AWS_REGION", "us-east-1")


def get_content_type(key: str) -> str:
    ext = key.split(".")[-1].lower() if "." in key else ""
    map_ = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif", "webp": "image/webp",
        "mp4": "video/mp4", "webm": "video/webm", "mov": "video/quicktime",
        "mp3": "audio/mpeg", "wav": "audio/wav", "ogg": "audio/ogg", "m4a": "audio/mp4",
    }
    return map_.get(ext, "application/octet-stream")


def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")
    if not MEDIA_URL:
        print("ERROR: MEDIA_ANALYSIS_URL not set")
        return {"statusCode": 500, "body": json.dumps({"error": "MEDIA_ANALYSIS_URL not set"})}

    for record in event.get("Records", []):
        if record.get("eventSource") != "aws:s3":
            continue
        s3 = record.get("s3", {})
        bucket = s3.get("bucket", {}).get("name", "")
        key = urllib.parse.unquote_plus(s3.get("object", {}).get("key", ""))
        
        if not bucket or not key:
            continue
            
        print(f"Processing S3 event: bucket={bucket}, key={key}")
        
        # S3 URL for media-analysis (same region)
        url = f"https://{bucket}.s3.{REGION}.amazonaws.com/{key}"
        body = json.dumps({"url": url, "contentType": get_content_type(key)}).encode("utf-8")
        
        req = urllib.request.Request(
            f"{MEDIA_URL}/analyze",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        
        print(f"Calling media analysis: {MEDIA_URL}/analyze")
        
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                print(f"Analysis call status: {resp.status}")
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode()[:500]
            print(f"HTTP Error {e.code}: {err_msg}")
            return {"statusCode": e.code, "body": err_msg}
        except Exception as e:
            print(f"Connection Error: {str(e)}")
            return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    return {"statusCode": 200, "body": json.dumps({"ok": True})}
