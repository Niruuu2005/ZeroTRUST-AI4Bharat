"""
ZeroTRUST Media Analysis Service — Diagram 4 pipeline.

Uses AWS Textract (OCR), Transcribe (speech-to-text), Rekognition (labels/moderation/video).
Evidence merged into a credibility-style score. S3 URLs only (client uploads via presign).
"""
import os
import time
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.s3_utils import is_s3_url
from src.aws_media import run_media_pipeline
from src.evidence_merge import (
    compute_credibility_from_evidence,
    build_agent_verdicts,
    build_sources,
    build_limitations,
)

app = FastAPI(title="ZeroTRUST Media Analysis", version="2.0.0")


class AnalyzeRequest(BaseModel):
    url: str = Field(..., description="S3 URL of media file (s3://bucket/key or https://bucket.s3.../key)")
    contentType: str = Field("application/octet-stream", description="MIME type: image/*, video/*, audio/*")


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "media-analysis",
        "pipeline": "Textract, Transcribe, Rekognition",
    }


@app.post("/analyze")
async def analyze_media(body: AnalyzeRequest):
    """
    Run full media pipeline: Textract (image), Transcribe (audio), Rekognition (image/video).
    Returns VerificationResult-compatible shape for cache and API Gateway.
    """
    if not body.url or not body.url.strip():
        raise HTTPException(status_code=400, detail="url is required")
    if not is_s3_url(body.url):
        raise HTTPException(
            status_code=400,
            detail="Only S3 URLs are supported. Upload via presigned URL first.",
        )

    start = time.perf_counter()
    result = run_media_pipeline(body.url, body.contentType or "")
    elapsed = round(time.perf_counter() - start, 2)

    if result.get("error") and not result.get("evidence"):
        raise HTTPException(status_code=400, detail=result["error"])

    evidence = result.get("evidence") or {}
    errors = result.get("errors") or []
    bucket = result.get("bucket", "")
    key = result.get("key", "")

    score, category, confidence = compute_credibility_from_evidence(evidence, errors)
    agent_verdicts = build_agent_verdicts(evidence)
    sources = build_sources(evidence, bucket, key)
    limitations = build_limitations(errors, body.contentType or "")
    evidence_summary = {
        "supporting": 1 if score >= 60 else 0,
        "contradicting": 1 if score < 40 else 0,
        "neutral": 1 if 40 <= score < 60 else 0,
    }

    return {
        "id": str(uuid.uuid4()),
        "credibility_score": score,
        "category": category,
        "confidence": confidence,
        "claim_type": "mixed",
        "sources_consulted": len(sources) + len(agent_verdicts),
        "agent_consensus": "media_analysis",
        "evidence_summary": evidence_summary,
        "sources": sources,
        "agent_verdicts": agent_verdicts,
        "limitations": limitations,
        "recommendation": "Consider cross-checking with text verification for claims extracted from this media.",
        "processing_time": elapsed,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "media_evidence": evidence,
        "cached": False,
    }
