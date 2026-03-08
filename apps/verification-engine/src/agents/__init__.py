"""
All 6 specialist agents for ZeroTRUST verification pipeline.
"""
import asyncio
import json
import re
import logging
import os
from typing import Any

import httpx

from src.agents.base import BaseAgent
from src.integrations.bedrock import invoke_bedrock
from src.integrations.duckduckgo_search import search_web, search_news
from src.integrations.rss_feeds import fetch_news_from_rss

logger = logging.getLogger(__name__)

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")
GOOGLE_SEARCH_KEY = os.getenv("GOOGLE_SEARCH_KEY", "")
GOOGLE_CSE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")
TWITTER_BEARER = os.getenv("TWITTER_BEARER_TOKEN", "")
PUBMED_API_KEY = os.getenv("PUBMED_API_KEY", "")

TIER_1_SOURCES = {
    'bbc.com','bbc.co.uk','reuters.com','apnews.com','npr.org',
    'pbs.org','altnews.in','boomlive.in','factcheck.org','snopes.com',
    'politifact.com','who.int','cdc.gov','pubmed.ncbi.nlm.nih.gov'
}
TIER_2_SOURCES = {
    'theguardian.com','washingtonpost.com','nytimes.com','bloomberg.com',
    'ndtv.com','thehindu.com','indianexpress.com','hindustantimes.com',
    'timesofindia.com','theprint.in','thewire.in','scroll.in'
}


def _tier_from_url(url: str) -> str:
    from urllib.parse import urlparse
    try:
        domain = urlparse(url).netloc.lstrip('www.')
        if domain in TIER_1_SOURCES: return 'tier_1'
        if domain in TIER_2_SOURCES: return 'tier_2'
    except Exception:
        pass
    return 'tier_4'


async def _llm_verdict(config_key: str, claim: str, context: str, label: str) -> dict:
    prompt = f"""You are a real-time fact-checker with access to live web search results.
The sources below are fetched RIGHT NOW from the internet — they may include recent events
that occurred after any AI training cutoff. Trust the sources over prior knowledge.

If sources clearly describe the claim as having happened, respond with 'supports'.
If sources clearly refute it, respond with 'contradicts'.
If sources are ambiguous or conflicting, respond with 'mixed'.
Only use 'insufficient' when there are truly zero relevant sources.

Claim: {claim}

{label.capitalize()} sources (live, fetched now):
{context}

Return ONLY valid JSON (no markdown, no explanation):
{{"verdict":"supports|contradicts|mixed|insufficient","confidence":0.0,"summary":"2 sentence max","evidence":{{"supporting":0,"contradicting":0,"neutral":0}}}}"""
    try:
        raw = await invoke_bedrock(config_key, prompt)
        # Strip markdown code fences if present
        raw = re.sub(r'```[a-z]*\n?', '', raw).strip()
        return json.loads(raw)
    except Exception as e:
        logger.warning(f"LLM verdict parse failed: {e}")
        return {"verdict": "insufficient", "confidence": 0.0, "summary": "Analysis unavailable", "evidence": {}}


# ──────────────────────────────────────────────────────────────
# Agent 1: Research Agent (in-house: DuckDuckGo + Wikipedia; no API keys)
# ──────────────────────────────────────────────────────────────
class ResearchAgent(BaseAgent):
    """🔍 DuckDuckGo web search + Wikipedia — in-house, no API keys."""

    async def investigate(self, claim: str, analysis: dict) -> dict:
        query = analysis.get('main_assertion', claim)[:200]
        results = await asyncio.gather(
            self._duckduckgo_search(query),
            self._wikipedia_search(query),
            return_exceptions=True
        )
        sources = []
        for r in results:
            if isinstance(r, list): sources.extend(r)

        if not sources:
            return self._error_result("research", "No results found from web search")

        context = "\n".join([f"- {s['title']}: {s['excerpt'][:150]}" for s in sources[:10]])
        verdict = await _llm_verdict('research', claim, context, 'web search')
        return {"agent": "research", **verdict, "sources": sources[:15]}

    async def _duckduckgo_search(self, query: str) -> list:
        """In-house: DuckDuckGo text search (no API key)."""
        try:
            items = await search_web(query, max_results=10)
            return [self._make_source(
                i.get("url", ""), i.get("title", ""), i.get("snippet", ""),
                _tier_from_url(i.get("url", "")), "neutral", "web"
            ) for i in items]
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")
            return []

    async def _wikipedia_search(self, query: str) -> list:
        """Search Wikipedia via the proper search API, not a direct title lookup."""
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                # Step 1: find matching article titles
                search_r = await client.get(
                    "https://en.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "list": "search",
                        "srsearch": query[:150],
                        "format": "json",
                        "srlimit": 3,
                        "utf8": 1,
                    },
                    headers={"User-Agent": "ZeroTRUST/1.0"},
                )
                hits = search_r.json().get("query", {}).get("search", [])
                sources = []
                for hit in hits[:2]:
                    title = hit.get("title", "")
                    if not title:
                        continue
                    # Step 2: fetch the summary for the matched article
                    sum_r = await client.get(
                        f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}",
                        headers={"User-Agent": "ZeroTRUST/1.0"},
                    )
                    if sum_r.status_code == 200:
                        data = sum_r.json()
                        sources.append(self._make_source(
                            data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                            data.get('title', ''), data.get('extract', '')[:300],
                            'tier_2', 'neutral', 'encyclopedia'
                        ))
                return sources
        except Exception:
            pass
        return []


# ──────────────────────────────────────────────────────────────
# Agent 2: News Agent (in-house: RSS feeds + DuckDuckGo news; no API keys)
# ──────────────────────────────────────────────────────────────
class NewsAgent(BaseAgent):
    """📰 RSS feeds (trusted sources) + DuckDuckGo news — in-house, no API keys."""

    async def investigate(self, claim: str, analysis: dict) -> dict:
        # Use main_assertion as primary query to preserve event context (e.g. 'renamed', 'banned').
        # Falling back to entity list only loses the verb/action that distinguishes the event.
        main_q = analysis.get('main_assertion', claim)[:200]
        entity_q = ' '.join(analysis.get('entities', [])[:4]) or claim[:100]

        results = await asyncio.gather(
            fetch_news_from_rss(main_q, max_items=20),
            self._duckduckgo_news(main_q),
            self._duckduckgo_news(entity_q),
            return_exceptions=True
        )
        sources = []
        seen = set()
        for r in results:
            if isinstance(r, list):
                for s in r:
                    key = s.get("url") or s.get("title", "")
                    if key and key not in seen:
                        seen.add(key)
                        sources.append(self._normalize_news_source(s))

        # Sort by recency so the LLM context leads with newest articles
        sources.sort(key=lambda s: s.get('published_at', ''), reverse=True)
        sources = sources[:20]

        if not sources:
            return self._error_result("news", "No news found from RSS or search")

        context = "\n".join([f"- {s['title']} ({s.get('published_at','')}): {s['excerpt'][:150]}"
                            for s in sources[:12]])
        verdict = await _llm_verdict('manager', claim, context, 'news')
        return {"agent": "news", **verdict, "sources": sources}

    def _normalize_news_source(self, item: dict) -> dict:
        """Convert RSS/DDG news item to standard source format."""
        return self._make_source(
            item.get("url", ""), item.get("title", ""), item.get("excerpt", item.get("snippet", ""))[:200],
            _tier_from_url(item.get("url", "")), "neutral", "news",
            item.get("published_at", item.get("date", ""))
        )

    async def _duckduckgo_news(self, q: str) -> list:
        """In-house: DuckDuckGo news search (no API key)."""
        try:
            items = await search_news(q, max_results=10)
            return [{"url": i.get("url", ""), "title": i.get("title", ""), "excerpt": i.get("snippet", ""), "published_at": i.get("date", "")} for i in items]
        except Exception as e:
            logger.warning(f"DuckDuckGo news failed: {e}")
            return []


# ──────────────────────────────────────────────────────────────
# Agent 3: Scientific Agent
# ──────────────────────────────────────────────────────────────
class ScientificAgent(BaseAgent):
    """🔬 PubMed + arXiv peer-reviewed literature search."""

    async def investigate(self, claim: str, analysis: dict) -> dict:
        q = analysis.get('main_assertion', claim)[:150]
        results = await asyncio.gather(
            self._pubmed(q), self._arxiv(q), return_exceptions=True
        )
        papers: list = []
        for r in results:
            if isinstance(r, list): papers.extend(r)

        if not papers:
            return {"agent": "scientific", "verdict": "insufficient", "confidence": 0.2,
                    "summary": "No peer-reviewed sources found", "sources": [], "evidence": {}}

        context = "\n".join([f"- {p['title']} ({p.get('published_at','')[:7]}): {p['excerpt'][:150]}"
                            for p in papers[:10]])
        prompt = f"""As a scientific fact-checker, does the peer-reviewed literature support this claim?

Claim: {claim}

Papers:
{context}

Return ONLY JSON:
{{"verdict":"supports|contradicts|mixed|insufficient","confidence":0.0,"summary":"<2 sentences>","consensus_level":"strong|moderate|weak|divided","evidence":{{"supporting":0,"contradicting":0,"neutral":0}}}}"""
        try:
            raw = re.sub(r'```[a-z]*\n?', '', await invoke_bedrock('research', prompt)).strip()
            parsed = json.loads(raw)
        except Exception:
            parsed = {"verdict": "insufficient", "confidence": 0.0, "summary": "Parse failed", "evidence": {}}

        return {"agent": "scientific", **parsed, "sources": papers[:10]}

    async def _pubmed(self, query: str) -> list:
        try:
            params = {"db": "pubmed", "term": query, "retmax": 5, "retmode": "json",
                      "sort": "relevance"}
            if PUBMED_API_KEY: params["api_key"] = PUBMED_API_KEY
            async with httpx.AsyncClient(timeout=8.0) as client:
                r = await client.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                                     params=params)
                ids = r.json().get('esearchresult', {}).get('idlist', [])
                if not ids: return []
                # Fetch summaries
                r2 = await client.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                    params={"db": "pubmed", "id": ','.join(ids), "retmode": "json"})
                data = r2.json().get('result', {})
                sources = []
                for uid in ids:
                    if uid not in data: continue
                    art = data[uid]
                    sources.append(self._make_source(
                        f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                        art.get('title', ''), art.get('summary', '')[:200],
                        'tier_1', 'neutral', 'academic',
                        art.get('pubdate', '')[:10]
                    ))
                return sources
        except Exception as e:
            logger.warning(f"PubMed failed: {e}")
            return []

    async def _arxiv(self, query: str) -> list:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                r = await client.get("http://export.arxiv.org/api/query", params={
                    "search_query": f"all:{query}", "start": 0, "max_results": 5
                })
                import xml.etree.ElementTree as ET
                root = ET.fromstring(r.text)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                sources = []
                for entry in root.findall('atom:entry', ns):
                    title = (entry.find('atom:title', ns) or {}).text or ''  # type: ignore
                    summary = (entry.find('atom:summary', ns) or {}).text or ''  # type: ignore
                    link = (entry.find('atom:id', ns) or {}).text or ''  # type: ignore
                    published = (entry.find('atom:published', ns) or {}).text or ''  # type: ignore
                    sources.append(self._make_source(
                        link, title.strip(), summary[:200].strip(),
                        'tier_1', 'neutral', 'preprint', published[:10]
                    ))
                return sources
        except Exception as e:
            logger.warning(f"arXiv failed: {e}")
            return []


# ──────────────────────────────────────────────────────────────
# Agent 4: Social Media Agent (in-house: Reddit public JSON — no API key)
# ──────────────────────────────────────────────────────────────
class SocialMediaAgent(BaseAgent):
    """📣 Reddit public search — in-house scraping, no API key."""

    async def investigate(self, claim: str, analysis: dict) -> dict:
        q = analysis.get('main_assertion', claim)[:100]
        sources = await self._reddit(q)

        if not sources:
            return {"agent": "social_media", "verdict": "insufficient", "confidence": 0.0,
                    "summary": "No relevant Reddit discussion found", "sources": [], "evidence": {}}

        context = "\n".join([f"- {s['title']}: {s['excerpt'][:100]}" for s in sources[:10]])
        verdict = await _llm_verdict('sentiment', claim, context, 'social media')
        return {"agent": "social_media", **verdict, "sources": sources[:15]}

    async def _reddit(self, q: str) -> list:
        try:
            async with httpx.AsyncClient(timeout=8.0, headers={"User-Agent": "ZeroTRUST/1.0"}) as client:
                r = await client.get("https://www.reddit.com/search.json",
                    params={"q": q, "sort": "relevance", "limit": 8, "type": "link"}
                )
                posts = r.json().get('data', {}).get('children', [])
                return [self._make_source(
                    f"https://reddit.com{p['data'].get('permalink','')}",
                    p['data'].get('title',''), p['data'].get('selftext','')[:200],
                    'tier_4', 'neutral', 'social'
                ) for p in posts if p.get('data')]
        except Exception as e:
            logger.warning(f"Reddit failed: {e}")
            return []


# ──────────────────────────────────────────────────────────────
# Agent 5: Sentiment & Propaganda Agent
# ──────────────────────────────────────────────────────────────

PROPAGANDA_PATTERNS: dict[str, str] = {
    'name_calling':     r'\b(radical|extremist|traitor|fascist|terrorist)\b',
    'loaded_language':  r'\b(devastating|catastrophic|explosive|shocking|outrageous|bombshell)\b',
    'false_urgency':    r'\b(act now|urgent|immediate action|before it\'s too late|share now)\b',
    'bandwagon':        r'\b(everyone knows|everyone is|millions are|join the|they don\'t want you)\b',
    'false_dilemma':    r'\b(either.*or|you\'re (with us|against us)|no other choice)\b',
    'ad_hominem':       r'\b(stupid|idiot|liar|dishonest|corrupt|criminal)\b',
    'appeal_to_fear':   r'\b(dangerous|threat|attack|destroy|collapse|invasion|catastrophe)\b',
    'repetition':       r'\b(\w+)\s+\1\s+\1',  # same word 3+ times
}


class SentimentAgent(BaseAgent):
    """😤 Detect emotional manipulation, propaganda, and bias — text only."""

    async def investigate(self, claim: str, analysis: dict) -> dict:
        detected = [name for name, pattern in PROPAGANDA_PATTERNS.items()
                    if re.search(pattern, claim, re.IGNORECASE)]

        prompt = f"""Analyze this claim for propaganda, emotional manipulation, and logical fallacies.
Claim: {claim}
Pre-detected patterns: {detected}
Return ONLY JSON:
{{"manipulation_score":0.0,"techniques":[],"is_emotional":false,"summary":"<2 sentences>","evidence":{{"supporting":0,"contradicting":0,"neutral":1}}}}"""

        try:
            raw = re.sub(r'```[a-z]*\n?', '', await invoke_bedrock('sentiment', prompt)).strip()
            llm = json.loads(raw)
        except Exception:
            llm = {"manipulation_score": 0.0, "summary": "Unavailable", "evidence": {}}

        manip = min(1.0, len(detected) * 0.15 + llm.get('manipulation_score', 0) * 0.85)
        verdict = ('contradicts' if manip > 0.6 else 'mixed' if manip > 0.3 else 'supports')

        return {
            "agent": "sentiment",
            "verdict": verdict,
            "confidence": min(0.95, 0.6 + manip * 0.35),
            "summary": llm.get('summary', f"Detected {len(detected)} manipulation technique(s)."),
            "sources": [],
            "evidence": llm.get('evidence', {"supporting": 0, "contradicting": 0, "neutral": 1}),
            "manipulation_score": manip,
            "detected_techniques": detected,
        }


# ──────────────────────────────────────────────────────────────
# Agent 6: Web Scraper Agent
# ──────────────────────────────────────────────────────────────
class ScraperAgent(BaseAgent):
    """🕷️ Fetch and analyze URL content directly."""

    async def investigate(self, claim: str, analysis: dict) -> dict:
        meta = analysis.get('metadata', {})
        url = claim.strip() if meta.get('is_url') else None

        if not url:
            return {"agent": "scraper", "verdict": "insufficient", "confidence": 0.0,
                    "summary": "No URL to scrape", "sources": [], "evidence": {}}

        content = await self._fetch(url)
        if not content:
            return self._error_result("scraper", f"Could not fetch {url}")

        context = content[:500]
        verdict = await _llm_verdict('manager', claim, context, 'webpage')
        return {
            "agent": "scraper", **verdict,
            "sources": [self._make_source(url, "Source URL", content[:200],
                                          _tier_from_url(url), 'neutral', 'web')]
        }

    async def _fetch(self, url: str) -> str | None:
        try:
            from bs4 import BeautifulSoup
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True,
                                         headers={"User-Agent": "ZeroTRUST/1.0"}) as client:
                r = await client.get(url)
                if r.status_code != 200: return None
                soup = BeautifulSoup(r.text, 'html.parser')
                for tag in soup(['script','style','nav','footer','header']): tag.decompose()
                return ' '.join(soup.get_text().split())[:2000]
        except Exception as e:
            logger.warning(f"Scraper fetch failed for {url}: {e}")
            return None


# ──────────────────────────────────────────────────────────────
# Agent 7: Fact-Check API Agent (Official Professional Verdicts)
# ──────────────────────────────────────────────────────────────
class FactCheckAgent(BaseAgent):
    """✅ Google Fact Check Explorer — professional fact-checker database.
    
    Queries Snopes, AltNews, BoomLive, PolitiFact, FactCheck.org, AFP Fact Check,
    BBC Reality Check, Reuters Fact Check, and 100+ other registered fact-checkers.
    
    When a match is found, this agent's verdict is treated as the highest-authority
    signal in the credibility scoring pipeline (overrides inferred verdicts).
    """

    async def investigate(self, claim: str, analysis: dict) -> dict:
        from src.integrations.factcheck_api import query_factcheck_api

        # Try the main assertion first, then the raw claim as fallback
        query = analysis.get('main_assertion', claim)[:200]
        checks = await query_factcheck_api(query)

        # If no results for the main assertion, retry with raw claim (broader query)
        if not checks and query != claim[:200]:
            checks = await query_factcheck_api(claim[:200])

        if not checks:
            return {
                "agent": "factcheck",
                "verdict": "insufficient",
                "confidence": 0.0,
                "summary": "No official fact-checks found for this claim.",
                "sources": [],
                "evidence": {"supporting": 0, "contradicting": 0, "neutral": 0},
                "official_checks_found": 0,
            }

        # Build source objects — official fact-checks are always Tier 1
        sources = []
        for fc in checks:
            sources.append(self._make_source(
                url=fc.get("url", ""),
                title=fc.get("title", f"{fc.get('publisher', 'Fact-checker')}: {fc.get('textual_rating', '')}"),
                excerpt=f"Claim reviewed: \"{fc.get('claim_reviewed', '')[:150]}\" — Rating: {fc.get('textual_rating', 'Unknown')}",
                tier="tier_1",        # Professional fact-checkers → Tier 1 always
                stance=fc.get("verdict", "mixed"),
                source_type="factcheck",
            ))

        # Compute aggregate verdict from all official checks
        from collections import Counter
        verdicts = [fc.get("verdict", "mixed") for fc in checks]
        truth_scores = [fc.get("truth_score", 0.5) for fc in checks]
        avg_truth = sum(truth_scores) / len(truth_scores)

        verdict_counts = Counter(verdicts)
        dominant_verdict = verdict_counts.most_common(1)[0][0]
        dominant_count = verdict_counts.most_common(1)[0][1]
        confidence = min(0.98, 0.75 + (dominant_count / len(verdicts)) * 0.23)  # 75-98%

        # Build a human-readable summary
        publishers = list({fc.get("publisher", "Unknown") for fc in checks[:4]})
        publisher_str = ", ".join(publishers)
        ratings = list({fc.get("textual_rating", "") for fc in checks[:4]})
        summary = (
            f"Found {len(checks)} official fact-check(s) from: {publisher_str}. "
            f"Ratings include: {', '.join(ratings[:3])}. "
            f"Overall official verdict: {dominant_verdict.upper()}."
        )

        evidence_counts = {
            "supporting":    verdicts.count("supports"),
            "contradicting": verdicts.count("contradicts"),
            "neutral":       verdicts.count("mixed"),
        }

        return {
            "agent": "factcheck",
            "verdict": dominant_verdict,
            "confidence": round(confidence, 2),
            "summary": summary,
            "sources": sources,
            "evidence": evidence_counts,
            "official_checks_found": len(checks),
            "avg_truth_score": round(avg_truth, 3),
            "is_official_verdict": True,  # Scorer uses this flag for bonus weight
        }
