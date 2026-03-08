"""
In-house web search via DuckDuckGo — no API key required.
Runs sync DDGS in thread to avoid blocking the event loop.
"""
import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Default region for Indian news queries (DDG region code in-en = India/English)
_INDIA_REGION = "in-en"


def _ddg_text_sync(
    query: str,
    max_results: int = 10,
    timelimit: str | None = "y",
    region: str = _INDIA_REGION,
) -> list[dict[str, Any]]:
    """Synchronous DuckDuckGo text search. Run from asyncio.to_thread.

    Args:
        timelimit: 'd' = past day, 'w' = past week, 'm' = past month, 'y' = past year, None = all time.
        region:   DDG region code. 'in-en' biases results toward Indian English sources.
    """
    try:
        from duckduckgo_search import DDGS
        kwargs: dict[str, Any] = {"max_results": max_results}
        if timelimit:
            kwargs["timelimit"] = timelimit
        if region:
            kwargs["region"] = region
        with DDGS() as ddgs:
            results = list(ddgs.text(query, **kwargs))
        return [
            {"url": r.get("href", ""), "title": r.get("title", ""), "snippet": r.get("body", "")}
            for r in results
        ]
    except Exception as e:
        logger.warning(f"DuckDuckGo text search failed: {e}")
        return []


def _ddg_news_sync(
    query: str,
    max_results: int = 10,
    timelimit: str | None = "y",
    region: str = _INDIA_REGION,
) -> list[dict[str, Any]]:
    """Synchronous DuckDuckGo news search. Run from asyncio.to_thread.

    Args:
        timelimit: 'd'/'w'/'m'/'y'/None — limits results to that recency window.
        region:   DDG region code. 'in-en' biases results toward Indian English sources.
    """
    try:
        from duckduckgo_search import DDGS
        kwargs: dict[str, Any] = {"max_results": max_results}
        if timelimit:
            kwargs["timelimit"] = timelimit
        if region:
            kwargs["region"] = region
        with DDGS() as ddgs:
            results = list(ddgs.news(query, **kwargs))
        return [
            {
                "url": r.get("url", ""),
                "title": r.get("title", ""),
                "snippet": r.get("body", r.get("snippet", "")),
                "date": r.get("date", ""),
            }
            for r in results
        ]
    except Exception as e:
        logger.warning(f"DuckDuckGo news search failed: {e}")
        return []


async def search_web(
    query: str,
    max_results: int = 10,
    timelimit: str | None = "y",
    region: str = _INDIA_REGION,
) -> list[dict[str, Any]]:
    """Async wrapper: DuckDuckGo text search (no API key). Hard 8s timeout."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_ddg_text_sync, query, max_results, timelimit, region),
            timeout=8.0,
        )
    except asyncio.TimeoutError:
        logger.warning(f"DuckDuckGo text search timed out for: {query[:50]}")
        return []
    except Exception as e:
        logger.warning(f"DuckDuckGo text search error: {e}")
        return []


async def search_news(
    query: str,
    max_results: int = 10,
    timelimit: str | None = "y",
    region: str = _INDIA_REGION,
) -> list[dict[str, Any]]:
    """Async wrapper: DuckDuckGo news search (no API key). Hard 8s timeout."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_ddg_news_sync, query, max_results, timelimit, region),
            timeout=8.0,
        )
    except asyncio.TimeoutError:
        logger.warning(f"DuckDuckGo news search timed out for: {query[:50]}")
        return []
    except Exception as e:
        logger.warning(f"DuckDuckGo news search error: {e}")
        return []
