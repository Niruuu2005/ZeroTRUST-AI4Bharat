"""
AWS Media APIs: Textract, Transcribe, Rekognition.
Uses S3 bucket/key; sync for image, async poll for audio/video.
"""
import json
import time
import logging
from typing import Any

import boto3
from botocore.exceptions import ClientError

from src.s3_utils import parse_s3_url

logger = logging.getLogger(__name__)

REGION = __import__("os").environ.get("AWS_REGION", "us-east-1")
TRANSCRIBE_POLL_TIMEOUT = 120
REKOGNITION_VIDEO_POLL_TIMEOUT = 180
POLL_INTERVAL = 3


def _s3_ref(bucket: str, key: str) -> dict:
    return {"S3Object": {"Bucket": bucket, "Name": key}}


def analyze_image_textract(bucket: str, key: str) -> dict[str, Any]:
    """Sync OCR on image in S3. Returns { "text": str, "blocks": list, "error": str? }."""
    try:
        client = boto3.client("textract", region_name=REGION)
        resp = client.detect_document_text(Document=_s3_ref(bucket, key))
        lines = [
            item["Text"]
            for item in resp.get("Blocks", [])
            if item.get("BlockType") == "LINE"
        ]
        return {
            "text": "\n".join(lines).strip(),
            "block_count": len(resp.get("Blocks", [])),
            "raw_blocks": len(resp.get("Blocks", [])),
        }
    except ClientError as e:
        logger.warning("Textract failed: %s", e)
        return {"text": "", "error": str(e)}


def analyze_image_rekognition(bucket: str, key: str) -> dict[str, Any]:
    """Labels + moderation for image in S3."""
    out: dict[str, Any] = {"labels": [], "moderation": None, "error": None}
    try:
        client = boto3.client("rekognition", region_name=REGION)
        # Labels
        label_resp = client.detect_labels(Image=_s3_ref(bucket, key), MaxLabels=20)
        out["labels"] = [
            {"name": x["Name"], "confidence": x["Confidence"]}
            for x in label_resp.get("Labels", [])
        ]
        # Moderation
        mod_resp = client.detect_moderation_labels(Image=_s3_ref(bucket, key))
        mods = mod_resp.get("ModerationLabels", [])
        if mods:
            out["moderation"] = [
                {"label": m["Name"], "confidence": m["Confidence"]}
                for m in mods
            ]
    except ClientError as e:
        logger.warning("Rekognition image failed: %s", e)
        out["error"] = str(e)
    return out


def analyze_audio_transcribe(bucket: str, key: str) -> dict[str, Any]:
    """Start Transcribe job, poll until done, return transcript. Async."""
    job_name = f"zt-{int(time.time())}-{key.replace('/', '-')}"[:200]
    media_uri = f"s3://{bucket}/{key}"
    try:
        client = boto3.client("transcribe", region_name=REGION)
        client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={"MediaFileUri": media_uri},
            MediaFormat=key.split(".")[-1].lower() if "." in key else "mp3",
            LanguageCode="en-US",
        )
        start = time.time()
        while time.time() - start < TRANSCRIBE_POLL_TIMEOUT:
            job = client.get_transcription_job(TranscriptionJobName=job_name)
            status = job["TranscriptionJob"]["TranscriptionJobStatus"]
            if status == "COMPLETED":
                transcript_uri = job["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
                import urllib.request
                with urllib.request.urlopen(transcript_uri) as f:
                    data = json.loads(f.read().decode())
                transcript = (
                    data.get("results", {})
                    .get("transcripts", [{}])[0]
                    .get("transcript", "")
                )
                return {"transcript": transcript, "job": job_name, "status": "completed"}
            if status == "FAILED":
                return {
                    "transcript": "",
                    "error": job["TranscriptionJob"].get("FailureReason", "Job failed"),
                    "job": job_name,
                }
            time.sleep(POLL_INTERVAL)
        return {"transcript": "", "error": "Transcribe job timeout", "job": job_name}
    except ClientError as e:
        logger.warning("Transcribe failed: %s", e)
        return {"transcript": "", "error": str(e)}


def analyze_video_rekognition(bucket: str, key: str) -> dict[str, Any]:
    """Start Rekognition label detection on video, poll, return labels."""
    try:
        client = boto3.client("rekognition", region_name=REGION)
        start_resp = client.start_label_detection(
            Video={"S3Object": {"Bucket": bucket, "Name": key}},
        )
        job_id = start_resp["JobId"]
        start = time.time()
        while time.time() - start < REKOGNITION_VIDEO_POLL_TIMEOUT:
            resp = client.get_label_detection(JobId=job_id)
            status = resp["JobStatus"]
            if status == "SUCCEEDED":
                labels = resp.get("Labels", [])
                by_name: dict[str, float] = {}
                for l in labels:
                    n = l["Label"]["Name"]
                    c = l["Label"].get("Confidence", 0)
                    by_name[n] = max(by_name.get(n, 0), c)
                return {
                    "labels": [{"name": k, "confidence": v} for k, v in by_name.items()],
                    "status": "completed",
                }
            if status == "FAILED":
                return {"labels": [], "error": "Rekognition video job failed"}
            time.sleep(POLL_INTERVAL)
        return {"labels": [], "error": "Rekognition video timeout"}
    except ClientError as e:
        logger.warning("Rekognition video failed: %s", e)
        return {"labels": [], "error": str(e)}


def run_media_pipeline(url: str, content_type: str) -> dict[str, Any]:
    """
    Run Textract/Transcribe/Rekognition based on content_type.
    url: S3 URL (s3://bucket/key or https://bucket.s3.../key).
    content_type: e.g. image/jpeg, audio/mpeg, video/mp4.
    Returns merged evidence dict and any errors.
    """
    parsed = parse_s3_url(url)
    if not parsed:
        return {"error": "Invalid S3 URL", "evidence": {}}
    bucket, key = parsed

    evidence: dict[str, Any] = {
        "textract": {},
        "rekognition": {},
        "transcribe": {},
        "forensic": {"note": "Metadata/deepfake checks not implemented"},
    }
    errors: list[str] = []

    mt = (content_type or "").lower()
    if mt.startswith("image/"):
        evidence["textract"] = analyze_image_textract(bucket, key)
        evidence["rekognition"] = analyze_image_rekognition(bucket, key)
        if evidence["textract"].get("error"):
            errors.append(evidence["textract"]["error"])
        if evidence["rekognition"].get("error"):
            errors.append(evidence["rekognition"]["error"])
    elif mt.startswith("audio/"):
        evidence["transcribe"] = analyze_audio_transcribe(bucket, key)
        if evidence["transcribe"].get("error"):
            errors.append(evidence["transcribe"]["error"])
    elif mt.startswith("video/"):
        evidence["rekognition"] = analyze_video_rekognition(bucket, key)
        evidence["transcribe"] = {"note": "Video transcript requires separate Transcribe job for video"}
        if evidence["rekognition"].get("error"):
            errors.append(evidence["rekognition"].get("error", "Rekognition error"))
    else:
        # Try image as fallback for unknown
        evidence["textract"] = analyze_image_textract(bucket, key)
        evidence["rekognition"] = analyze_image_rekognition(bucket, key)

    return {"evidence": evidence, "errors": errors, "bucket": bucket, "key": key}
