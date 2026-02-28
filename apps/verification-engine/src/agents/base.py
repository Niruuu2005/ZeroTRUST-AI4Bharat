"""
Base Agent class — all 6 specialist agents inherit from this.
"""
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

SOURCE_TIER_SCORES = {'tier_1': 0.95, 'tier_2': 0.80, 'tier_3': 0.60, 'tier_4': 0.35}


class BaseAgent(ABC):
    """All specialist agents must implement investigate()."""

    @abstractmethod
    async def investigate(self, claim: str, analysis: dict) -> dict:
        """
        Returns:
          { agent, verdict, confidence, summary, sources, evidence, error? }
        """
        pass

    def _make_source(
        self, url: str, title: str, excerpt: str,
        tier: str, stance: str, source_type: str,
        published_at: str | None = None
    ) -> dict:
        return {
            "url": url,
            "title": title,
            "excerpt": excerpt[:300],
            "credibility_tier": tier,
            "credibility_score": SOURCE_TIER_SCORES.get(tier, 0.3),
            "stance": stance,
            "source_type": source_type,
            "published_at": published_at,
        }

    def _error_result(self, name: str, error: str) -> dict:
        return {
            "agent": name,
            "verdict": "insufficient",
            "confidence": 0.0,
            "summary": f"Agent error: {error[:200]}",
            "sources": [],
            "evidence": {"supporting": 0, "contradicting": 0, "neutral": 0},
            "error": error[:200],
        }
