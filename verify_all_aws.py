#!/usr/bin/env python3
"""
ZeroTRUST — Master AWS Verification Script
Tests all 5 AWS setup steps: IAM, Bedrock, S3, DynamoDB, CloudWatch
Run from project root: .\\venv\\python.exe verify_all_aws.py
"""
import os, sys, json, time, datetime, boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

load_dotenv(".env.local")

REGION     = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID", "")
SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
S3_BUCKET  = os.environ.get("S3_MEDIA_BUCKET", "zerotrust-media-dev")
DDB_TABLE  = "zerotrust-claim-verifications"
CW_GROUP   = os.environ.get("CW_LOG_GROUP", "/zerotrust/api-gateway")
CW_PREFIX  = os.environ.get("CW_LOG_STREAM_PREFIX", "api-gateway")
MANAGER_MODEL   = os.environ.get("MANAGER_MODEL_ID",   "us.amazon.nova-pro-v1:0")
RESEARCH_MODEL  = os.environ.get("RESEARCH_MODEL_ID",  "us.mistral.pixtral-large-2502-v1:0")
SENTIMENT_MODEL = os.environ.get("SENTIMENT_MODEL_ID", "us.amazon.nova-lite-v1:0")

results = {}

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def ok(msg):   print(f"  ✅ {msg}")
def fail(msg): print(f"  ❌ {msg}")
def info(msg): print(f"  ℹ️  {msg}")

# ─────────────────────────────────────────────────────────────
# STEP 1 — IAM / Credentials Check
# ─────────────────────────────────────────────────────────────
section("STEP 1 — IAM & Credentials")
passed = True

if ACCESS_KEY and SECRET_KEY:
    ok(f".env.local loaded  — Key ID: {ACCESS_KEY[:6]}...{ACCESS_KEY[-4:]}")
else:
    fail("AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY missing from .env.local")
    passed = False

try:
    sts = boto3.client("sts", region_name=REGION,
                       aws_access_key_id=ACCESS_KEY,
                       aws_secret_access_key=SECRET_KEY)
    identity = sts.get_caller_identity()
    ok(f"STS get-caller-identity succeeded")
    info(f"Account : {identity['Account']}")
    info(f"ARN     : {identity['Arn']}")
    if "zerotrust-dev" in identity["Arn"]:
        ok("User is 'zerotrust-dev' ✓")
    else:
        fail(f"Expected user 'zerotrust-dev' but got: {identity['Arn']}")
        passed = False
except NoCredentialsError:
    fail("No credentials — check .env.local")
    passed = False
except Exception as e:
    fail(f"STS call failed: {e}")
    passed = False

results["1_IAM"] = "PASS" if passed else "FAIL"

# ─────────────────────────────────────────────────────────────
# STEP 2 — Bedrock Model Access
# ─────────────────────────────────────────────────────────────
section("STEP 2 — Bedrock Models")
bedrock = boto3.client("bedrock-runtime", region_name=REGION,
                       aws_access_key_id=ACCESS_KEY,
                       aws_secret_access_key=SECRET_KEY)
models = [
    (MANAGER_MODEL,   "Amazon Nova Pro     (Manager)"),
    (RESEARCH_MODEL,  "Mistral Pixtral     (Research)"),
    (SENTIMENT_MODEL, "Amazon Nova Lite    (Sentiment)"),
]
bedrock_pass = True
for model_id, label in models:
    sys.stdout.write(f"  Testing {label} ... ")
    sys.stdout.flush()
    try:
        resp = bedrock.converse(
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": "Reply with: OK"}]}],
            inferenceConfig={"maxTokens": 10, "temperature": 0.1}
        )
        reply = resp["output"]["message"]["content"][0]["text"].strip()[:30]
        print(f"PASS  ({reply})")
    except Exception as e:
        print(f"FAIL\n      -> {str(e)[:100]}")
        bedrock_pass = False

results["2_Bedrock"] = "PASS" if bedrock_pass else "FAIL"

# ─────────────────────────────────────────────────────────────
# STEP 3 — S3 Bucket
# ─────────────────────────────────────────────────────────────
section("STEP 3 — S3 Bucket")
s3_pass = True
try:
    s3 = boto3.client("s3", region_name=REGION,
                      aws_access_key_id=ACCESS_KEY,
                      aws_secret_access_key=SECRET_KEY)
    info(f"Bucket: {S3_BUCKET}")

    # Check bucket reachable
    s3.head_bucket(Bucket=S3_BUCKET)
    ok("Bucket is reachable")

    # Check CORS
    try:
        cors = s3.get_bucket_cors(Bucket=S3_BUCKET)
        rules = cors.get("CORSRules", [])
        origins = [o for r in rules for o in r.get("AllowedOrigins", [])]
        ok(f"CORS configured — Origins: {origins}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchCORSConfiguration":
            fail("No CORS configuration found — run step 3.2")
            s3_pass = False
        else:
            raise

    # Check lifecycle
    try:
        lc = s3.get_bucket_lifecycle_configuration(Bucket=S3_BUCKET)
        rules = [r.get("ID", "?") for r in lc.get("Rules", [])]
        ok(f"Lifecycle rules: {rules}")
    except ClientError as e:
        if e.response["Error"]["Code"] in ("NoSuchLifecycleConfiguration", "NoSuchLifecycleConfiguration"):
            fail("No lifecycle configuration — run step 3.3")
            s3_pass = False
        else:
            raise

    # Write/Delete test
    test_key = "uploads/verify_all_aws_test.txt"
    s3.put_object(Bucket=S3_BUCKET, Key=test_key, Body=b"zerotrust test")
    ok(f"Write test passed → {test_key}")
    s3.delete_object(Bucket=S3_BUCKET, Key=test_key)
    ok("Delete (cleanup) passed")

except Exception as e:
    fail(f"S3 error: {e}")
    s3_pass = False

results["3_S3"] = "PASS" if s3_pass else "FAIL"

# ─────────────────────────────────────────────────────────────
# STEP 4 — DynamoDB
# ─────────────────────────────────────────────────────────────
section("STEP 4 — DynamoDB")
ddb_pass = True
try:
    ddb = boto3.client("dynamodb", region_name=REGION,
                       aws_access_key_id=ACCESS_KEY,
                       aws_secret_access_key=SECRET_KEY)
    info(f"Table: {DDB_TABLE}")

    # Describe
    desc = ddb.describe_table(TableName=DDB_TABLE)
    status = desc["Table"]["TableStatus"]
    billing = desc["Table"].get("BillingModeSummary", {}).get("BillingMode", "PROVISIONED")
    ok(f"Table status: {status}  |  Billing: {billing}")

    # TTL check
    ttl_resp = ddb.describe_time_to_live(TableName=DDB_TABLE)
    ttl_status = ttl_resp["TimeToLiveDescription"]["TimeToLiveStatus"]
    ttl_attr   = ttl_resp["TimeToLiveDescription"].get("AttributeName", "N/A")
    if ttl_status == "ENABLED" and ttl_attr == "ttl":
        ok(f"TTL enabled on attribute '{ttl_attr}'")
    else:
        fail(f"TTL status={ttl_status}, attr={ttl_attr} — expected ENABLED on 'ttl'")
        ddb_pass = False

    # Put / Get / Delete
    test_hash = "verify-all-aws-test-99999"
    ttl_val = int((datetime.datetime.now() + datetime.timedelta(hours=1)).timestamp())
    ddb.put_item(TableName=DDB_TABLE, Item={
        "claim_hash": {"S": test_hash},
        "created_at": {"S": datetime.datetime.utcnow().isoformat()},
        "ttl":        {"N": str(ttl_val)},
        "result_json": {"S": json.dumps({"test": "verify_all_aws"})}
    })
    ok("PutItem succeeded")

    get_resp = ddb.get_item(TableName=DDB_TABLE, Key={"claim_hash": {"S": test_hash}})
    if "Item" in get_resp:
        ok("GetItem succeeded")
    else:
        fail("GetItem returned no item")
        ddb_pass = False

    ddb.delete_item(TableName=DDB_TABLE, Key={"claim_hash": {"S": test_hash}})
    ok("DeleteItem (cleanup) succeeded")

except Exception as e:
    fail(f"DynamoDB error: {e}")
    ddb_pass = False

results["4_DynamoDB"] = "PASS" if ddb_pass else "FAIL"

# ─────────────────────────────────────────────────────────────
# STEP 5 — CloudWatch Logs
# ─────────────────────────────────────────────────────────────
section("STEP 5 — CloudWatch Logs")
cw_pass = True
today  = datetime.date.today().isoformat()
stream = f"{CW_PREFIX}-{today}"
info(f"Log group:  {CW_GROUP}")
info(f"Log stream: {stream}")
try:
    logs = boto3.client("logs", region_name=REGION,
                        aws_access_key_id=ACCESS_KEY,
                        aws_secret_access_key=SECRET_KEY)

    # Create stream
    try:
        logs.create_log_stream(logGroupName=CW_GROUP, logStreamName=stream)
        ok(f"Log stream created: {stream}")
    except logs.exceptions.ResourceAlreadyExistsException:
        ok(f"Log stream already exists: {stream}")

    # Put log event
    now_ms = int(time.time() * 1000)
    event_msg = json.dumps({
        "level": "info", "message": "GET /health 200",
        "service": "api-gateway", "source": "verify_all_aws.py"
    })
    logs.put_log_events(
        logGroupName=CW_GROUP,
        logStreamName=stream,
        logEvents=[{"timestamp": now_ms, "message": event_msg}]
    )
    ok("PutLogEvents succeeded")

    # Confirm stream visible
    time.sleep(2)
    resp = logs.describe_log_streams(logGroupName=CW_GROUP, logStreamNamePrefix=stream)
    found = [s for s in resp.get("logStreams", []) if s["logStreamName"] == stream]
    if found:
        ok(f"Stream confirmed in CloudWatch (storedBytes={found[0].get('storedBytes',0)})")
    else:
        fail("Stream not found via describe_log_streams")
        cw_pass = False

    # Check env vars set
    if os.environ.get("CW_LOG_GROUP"):
        ok("CW_LOG_GROUP is set in .env.local")
    else:
        fail("CW_LOG_GROUP not set in .env.local")
        cw_pass = False

    if os.environ.get("CW_LOG_STREAM_PREFIX"):
        ok("CW_LOG_STREAM_PREFIX is set in .env.local")
    else:
        fail("CW_LOG_STREAM_PREFIX not set in .env.local")
        cw_pass = False

except Exception as e:
    fail(f"CloudWatch error: {e}")
    cw_pass = False

results["5_CloudWatch"] = "PASS" if cw_pass else "FAIL"

# ─────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────
section("OVERALL SUMMARY")
all_pass = all(v == "PASS" for v in results.values())
labels = {
    "1_IAM":       "Step 1 — IAM & Credentials",
    "2_Bedrock":   "Step 2 — Bedrock Models",
    "3_S3":        "Step 3 — S3 Bucket",
    "4_DynamoDB":  "Step 4 — DynamoDB",
    "5_CloudWatch":"Step 5 — CloudWatch Logs",
}
for key, label in labels.items():
    status = results.get(key, "SKIP")
    icon = "✅" if status == "PASS" else "❌"
    print(f"  {icon} {label}: {status}")

print(f"\n{'='*60}")
if all_pass:
    print("  🚀 ALL STEPS PASSED — Ready to proceed to Step 6 (Lambda)!")
else:
    print("  ⚠️  Some checks failed — review output above before continuing.")
print(f"{'='*60}\n")
sys.exit(0 if all_pass else 1)
