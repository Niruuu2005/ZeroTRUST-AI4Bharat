"""
In-house news gathering via RSS/Atom feeds — no API key required.
Curated list of trusted news and fact-check sources.
Also supports dynamic Google News RSS queries for event-specific searches.
"""
import asyncio
import logging
import re
from typing import Any
from urllib.parse import urlparse, quote_plus

logger = logging.getLogger(__name__)

# Trusted news and fact-check RSS/Atom feed URLs (public, no auth)
RSS_FEED_URLS = [
    # International tier-1
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://feeds.reuters.com/reuters/topNews",
    "https://feeds.apnews.com/rss/topnews",
    "https://www.npr.org/rss/rss.php?id=1001",
    "https://www.theguardian.com/world/rss",
    # Indian general news (tier-2)
    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "https://timesofindia.indiatimes.com/rss/1221656",      # ToI India section
    "https://www.thehindu.com/news/national/feeder/default.rss",
    "https://indianexpress.com/feed/",
    "https://www.ndtv.com/rss/india-news",
    "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
    "https://www.livemint.com/rss/news",
    "https://theprint.in/feed/",
    "https://scroll.in/feed",
    "https://thewire.in/feed",
    # Official Indian government news (tier-1 for India policy/law)
    "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3",  # Press Information Bureau
    # Fact-checkers
    "https://factcheck.afp.com/rss",
    "https://www.factcheck.org/feed/",
    "https://www.altnews.in/feed/",
    "https://www.boomlive.in/feed",
]


def _google_news_rss_url(query: str) -> str:
    """
    Build a dynamic Google News RSS URL for a specific query.
    Targets Indian English news (hl=en-IN, gl=IN, ceid=IN:en).
    No API key required — public RSS endpoint.
    """
    return (
        f"https://news.google.com/rss/search"
        f"?q={quote_plus(query)}"
        f"&hl=en-IN&gl=IN&ceid=IN:en"
    )


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
    Fetch multiple RSS feeds in parallel — both the static curated list AND a dynamic
    Google News RSS feed built around the specific query.

    The Google News RSS returns event-specific articles from thousands of sources,
    so it catches recent government announcements or regional news that the static
    feeds would miss (e.g. state renaming, new laws, breaking events).

    No API key required. Returns list of {url, title, excerpt, published_at}.
    """
    query_lower = query.lower()
    query_words = [w for w in re.split(r"\W+", query_lower) if len(w) > 2][:5]

    def matches(item: dict) -> bool:
        text = f"{item.get('title', '')} {item.get('excerpt', '')}".lower()
        return any(w in text for w in query_words) if query_words else True

    # Fire static feeds AND dynamic Google News RSS together
    google_news_url = _google_news_rss_url(query)
    all_feed_urls = RSS_FEED_URLS + [google_news_url]

    tasks = [asyncio.to_thread(_parse_feed_sync, url) for url in all_feed_urls]
    try:
        results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=15.0  # Hard cap: don't let slow feeds block the whole pipeline
        )
    except asyncio.TimeoutError:
        logger.warning("RSS feed fetch timed out after 15s — returning empty results")
        return []

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
