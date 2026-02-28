# Media Trigger Lambda

On S3 Put to the media bucket, this Lambda calls the Media Analysis service `/analyze` with the new object's S3 URL.

## Environment

- `MEDIA_ANALYSIS_URL` — Base URL of the Media Analysis service (e.g. `https://xxx.execute-api.region.amazonaws.com` or internal `http://media-analysis:8001`). The handler appends `/analyze`.
- `AWS_REGION` — Used to build the S3 object URL (default: `us-east-1`).

## Deployment (AWS Console / SAM / Terraform)

1. Package the handler (zip `handler.py` or use a layer for dependencies; this handler uses only stdlib).
2. Create a Lambda function with Python 3.11+ runtime.
3. Set the S3 bucket trigger: event type **Put**, prefix/suffix as needed (e.g. `uploads/`).
4. Ensure the Lambda execution role can read from the S3 bucket and (if MEDIA_ANALYSIS_URL is in VPC) access the media-analysis service (e.g. same VPC, security group).
5. Set `MEDIA_ANALYSIS_URL` and optionally `AWS_REGION` in the Lambda configuration.

## Local / inline test

```python
event = {
    "Records": [{
        "eventSource": "aws:s3",
        "s3": {"bucket": {"name": "my-bucket"}, "object": {"key": "uploads/test.jpg"}}
    }]
}
lambda_handler(event, None)
```
