"""
Google Fact Check Explorer API Integration.
Free API — returns professional fact-checker verdicts (Snopes, AltNews, BoomLive, PolitiFact, etc.)
Requires: GOOGLE_FACTCHECK_API_KEY in environment (free from Google Cloud Console).
Falls back to graceful empty result if key is missing.
"""
import asyncio
import logging
import os
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

FACTCHECK_API_BASE = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
API_KEY = os.getenv("GOOGLE_FACTCHECK_API_KEY", "")

# Maps Google Fact Check textualRating → internal verdict + numeric truth score (0=false, 1=true)
RATING_MAP = {
    # FALSE variants
    "false": ("contradicts", 0.0),
    "mostly false": ("contradicts", 0.15),
    "pants on fire": ("contradicts", 0.0),
    "incorrect": ("contradicts", 0.05),
    "wrong": ("contradicts", 0.05),
    "fake": ("contradicts", 0.0),
    "misleading": ("contradicts", 0.2),
    "disputed": ("contradicts", 0.25),
    "misinformation": ("contradicts", 0.1),
    "disinformation": ("contradicts", 0.0),
    # MIXED / PARTIAL
    "half true": ("mixed", 0.5),
    "partly true": ("mixed", 0.5),
    "partially true": ("mixed", 0.5),
    "mixed": ("mixed", 0.5),
    "unverified": ("mixed", 0.45),
    # TRUE variants
    "true": ("supports", 1.0),
    "mostly true": ("supports", 0.85),
    "correct": ("supports", 1.0),
    "accurate": ("supports", 1.0),
    "verified": ("supports", 0.95),
}


def _parse_rating(rating: str) -> tuple[str, float]:
    """Parse textualRating to (verdict, truth_score). Defaults to mixed."""
    key = rating.lower().strip()
    # Exact match
    if key in RATING_MAP:
        return RATING_MAP[key]
    # Partial match
    for k, v in RATING_MAP.items():
        if k in key:
            return v
    return ("mixed", 0.5)


async def query_factcheck_api(claim: str, language: str = "en") -> list[dict[str, Any]]:
    """
    Query Google Fact Check Explorer API.
    Returns list of structured fact-check results from professional fact-checkers.
    Gracefully returns [] if no API key or on any error.
    """
    if not API_KEY:
        logger.info("GOOGLE_FACTCHECK_API_KEY not set — skipping Fact Check API")
        return []

    # Use only first 200 chars of claim for the query (API limit)
    query = claim[:200]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                FACTCHECK_API_BASE,
                params={
                    "key": API_KEY,
                    "query": query,
                    "languageCode": language,
                    "pageSize": 10,
                },
            )
            if resp.status_code != 200:
                logger.warning(f"Fact Check API returned HTTP {resp.status_code}: {resp.text[:200]}")
                return []

            data = resp.json()
            claims = data.get("claims", [])
            results = []

            for item in claims:
                claim_text = item.get("text", "")
                reviews = item.get("claimReview", [])

                for review in reviews:
                    publisher = review.get("publisher", {})
                    site = publisher.get("site", "")
                    name = publisher.get("name", "Unknown")
                    url = review.get("url", "")
                    title = review.get("title", "")
                    rating = review.get("textualRating", "Unverified")
                    verdict, truth_score = _parse_rating(rating)

                    results.append({
                        "claim_reviewed": claim_text,
                        "publisher": name,
                        "publisher_site": site,
                        "url": url,
                        "title": title if title else f"{name}: {rating}",
                        "textual_rating": rating,
                        "verdict": verdict,
                        "truth_score": truth_score,
                        "is_official": True,   # Flag: this is from a professional fact-checker
                    })

            logger.info(f"Fact Check API: found {len(results)} official checks for claim")
            return results

    except Exception as e:
        logger.warning(f"Fact Check API query failed: {e}")
        return []
