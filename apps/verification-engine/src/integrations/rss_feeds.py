"""
In-house news gathering via RSS/Atom feeds — no API key required.
Curated list of trusted news and fact-check sources.
"""
import asyncio
import logging
import re
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Trusted news and fact-check RSS/Atom feed URLs (public, no auth)
RSS_FEED_URLS = [
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://feeds.reuters.com/reuters/topNews",
    "https://feeds.apnews.com/rss/topnews",
    "https://www.npr.org/rss/rss.php?id=1001",
    "https://www.theguardian.com/world/rss",
    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "https://www.thehindu.com/news/national/feeder/default.rss",
    "https://indianexpress.com/feed/",
    "https://www.ndtv.com/rss/india-news",
    "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
    "https://factcheck.afp.com/rss",
    "https://www.factcheck.org/feed/",
    "https://www.poynter.org/ifcn-covid-19-misinformation/feed/",
]


def _parse_feed_sync(url: str) -> list[dict[str, Any]]:
    """Fetch and parse one RSS/Atom feed. Run from asyncio.to_thread."""
    try:
        import feedparser
        import requests
        resp = requests.get(url, timeout=10.0, headers={"User-Agent": "ZeroTRUST/1.0 (RSS reader)"})
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)
        items = []
        for entry in feed.entries[:15]:
            link = entry.get("link", "")
            title = entry.get("title", "")
            summary = entry.get("summary", entry.get("description", ""))
            if isinstance(summary, str):
                summary = re.sub(r"<[^>]+>", "", summary)[:300]
            published = entry.get("published", entry.get("updated", ""))[:10] if entry.get("published") or entry.get("updated") else ""
            items.append({
                "url": link,
                "title": title,
                "excerpt": summary,
                "published_at": published,
            })
        return items
    except Exception as e:
        logger.debug(f"RSS fetch failed for {url}: {e}")
        return []


def _domain_from_url(url: str) -> str:
    try:
        return urlparse(url).netloc.lstrip("www.").lower()
    except Exception:
        return ""


async def fetch_news_from_rss(query: str, max_items: int = 25) -> list[dict[str, Any]]:
    """
    Fetch multiple RSS feeds in parallel and filter items by query (keyword match in title/summary).
    No API key required. Returns list of {url, title, excerpt, published_at}.
    """
    query_lower = query.lower()
    query_words = [w for w in re.split(r"\W+", query_lower) if len(w) > 2][:5]

    def matches(item: dict) -> bool:
        text = f"{item.get('title', '')} {item.get('excerpt', '')}".lower()
        return any(w in text for w in query_words) if query_words else True

    tasks = [asyncio.to_thread(_parse_feed_sync, url) for url in RSS_FEED_URLS]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    combined: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for r in results:
        if isinstance(r, Exception):
            logger.debug(f"RSS task failed: {r}")
            continue
        for item in r:
            url = item.get("url", "")
            if url and url not in seen_urls and matches(item):
                seen_urls.add(url)
                combined.append(item)
    combined.sort(key=lambda x: x.get("published_at", ""), reverse=True)
    return combined[:max_items]
