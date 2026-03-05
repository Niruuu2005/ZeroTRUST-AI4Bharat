"""
Step 5.3 — CloudWatch Verification Script
Sends a test log event directly to /zerotrust/api-gateway without needing Docker or the API server.
Run from project root: .\\venv\\python.exe test_cloudwatch.py
"""

import os
import json
import time
import datetime
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load credentials from project root .env.local
load_dotenv(".env.local")

LOG_GROUP   = os.environ.get("CW_LOG_GROUP", "/zerotrust/api-gateway")
LOG_PREFIX  = os.environ.get("CW_LOG_STREAM_PREFIX", "api-gateway")
REGION      = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

today       = datetime.date.today().isoformat()          # e.g. 2026-03-02
STREAM_NAME = f"{LOG_PREFIX}-{today}"

client = boto3.client(
    "logs",
    region_name=REGION,
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
)

def create_stream():
    try:
        client.create_log_stream(logGroupName=LOG_GROUP, logStreamName=STREAM_NAME)
        print(f"[+] Created log stream: {STREAM_NAME}")
    except client.exceptions.ResourceAlreadyExistsException:
        print(f"[~] Log stream already exists: {STREAM_NAME} (OK)")

def put_log():
    now_ms = int(time.time() * 1000)
    event = {
        "level":     "info",
        "message":   "GET /health 200",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "service":   "api-gateway",
        "method":    "GET",
        "path":      "/health",
        "status":    200,
        "duration":  3,
        "note":      "CloudWatch verification — sent from test_cloudwatch.py"
    }
    client.put_log_events(
        logGroupName=LOG_GROUP,
        logStreamName=STREAM_NAME,
        logEvents=[{"timestamp": now_ms, "message": json.dumps(event)}],
    )
    print(f"[+] Log event sent successfully!")
    print(f"    Message: {json.dumps(event, indent=2)}")

def describe_stream():
    resp = client.describe_log_streams(
        logGroupName=LOG_GROUP,
        logStreamNamePrefix=STREAM_NAME,
    )
    streams = resp.get("logStreams", [])
    if streams:
        s = streams[0]
        print(f"\n[+] Stream confirmed in CloudWatch:")
        print(f"    Name:           {s['logStreamName']}")
        print(f"    Stored bytes:   {s.get('storedBytes', 0)}")
        print(f"    Last event:     {s.get('lastEventTimestamp', 'N/A')}")
    else:
        print("[-] Stream not found via describe_log_streams")

if __name__ == "__main__":
    print(f"\n=== CloudWatch Log Verification ===")
    print(f"Log Group:   {LOG_GROUP}")
    print(f"Log Stream:  {STREAM_NAME}")
    print(f"Region:      {REGION}")
    print()

    create_stream()
    put_log()
    time.sleep(2)  # give AWS a moment to index
    describe_stream()

    print(f"\n✅ Done! Open the AWS Console to confirm:")
    print(f"   https://console.aws.amazon.com/cloudwatch/home#logsV2:log-groups/log-group/$252Fzerotrust$252Fapi-gateway")
