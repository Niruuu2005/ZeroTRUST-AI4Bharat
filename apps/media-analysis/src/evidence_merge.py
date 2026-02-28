"""
Merge AWS media results into a single credibility-style score and report.
"""
from typing import Any


def compute_credibility_from_evidence(evidence: dict[str, Any], errors: list[str]) -> tuple[int, str, str]:
    """
    Returns (credibility_score 0-100, category, confidence).
    category: Verified True | Likely True | Mixed | Likely False | Verified False
    confidence: High | Medium | Low
    """
    score = 50  # neutral start
    textract = evidence.get("textract") or {}
    rekognition = evidence.get("rekognition") or {}
    transcribe = evidence.get("transcribe") or {}

    # Moderation labels (Rekognition) lower score
    mod = rekognition.get("moderation") or []
    if mod:
        for m in mod:
            conf = m.get("confidence", 0) / 100.0
            if conf > 0.5:
                score -= 25
    if score < 0:
        score = 0

    # Has transcript or OCR text → slight boost (content analyzed)
    if (textract.get("text") or "").strip():
        score = min(100, score + 5)
    if (transcribe.get("transcript") or "").strip():
        score = min(100, score + 5)

    # Errors reduce confidence
    confidence = "High" if len(errors) == 0 else "Medium" if len(errors) <= 2 else "Low"

    if score >= 80:
        category = "Verified True"
    elif score >= 60:
        category = "Likely True"
    elif score >= 40:
        category = "Mixed"
    elif score >= 20:
        category = "Likely False"
    else:
        category = "Verified False"

    return score, category, confidence


def build_agent_verdicts(evidence: dict[str, Any]) -> dict[str, Any]:
    """Build agent_verdicts-style map for media pipeline."""
    verdicts: dict[str, Any] = {}
    if evidence.get("textract", {}).get("text"):
        verdicts["textract"] = {
            "agent": "textract",
            "verdict": "supports" if evidence["textract"].get("text") else "insufficient",
            "confidence": 0.8,
            "summary": f"OCR extracted {len(evidence['textract'].get('text', ''))} chars",
        }
    if evidence.get("rekognition"):
        r = evidence["rekognition"]
        verdicts["rekognition"] = {
            "agent": "rekognition",
            "verdict": "neutral" if not r.get("moderation") else "contradicts",
            "confidence": 0.75,
            "summary": f"Labels: {len(r.get('labels', []))}; Moderation: {len(r.get('moderation') or [])}",
        }
    if evidence.get("transcribe", {}).get("transcript"):
        verdicts["transcribe"] = {
            "agent": "transcribe",
            "verdict": "supports",
            "confidence": 0.8,
            "summary": "Speech-to-text completed",
        }
    return verdicts


def build_sources(evidence: dict[str, Any], bucket: str, key: str) -> list[dict]:
    """Build sources list for media (AWS services)."""
    return [
        {"url": f"s3://{bucket}/{key}", "title": "S3 object", "credibility_tier": "primary", "source_type": "media"},
    ]


def build_limitations(errors: list[str], content_type: str) -> list[str]:
    """Build limitations list."""
    limits = [
        "Media analysis uses AWS Textract/Transcribe/Rekognition; forensic (deepfake, reverse image) not implemented.",
        "Credibility score for media is heuristic based on moderation labels and content presence.",
    ]
    if errors:
        limits.append("Errors during analysis: " + "; ".join(errors[:3]))
    return limits
