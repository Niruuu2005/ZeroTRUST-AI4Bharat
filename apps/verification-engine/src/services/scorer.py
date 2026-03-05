"""
Credibility Scoring Engine

Implements the weighted formula from the design specification:
Credibility Score = (Evidence Quality × 0.4) + (Agent Consensus × 0.3) + (Source Reliability × 0.3)

Validates Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 4.10
"""
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

# Tier weights for Evidence Quality calculation (Requirement 4.2)
TIER_WEIGHTS = {
    'tier_1': 1.0,
    'tier_2': 0.7,
    'tier_3': 0.4,
    'tier_4': 0.2
}


class CredibilityScorer:
    """
    Calculate credibility score using the weighted formula:
    Credibility Score = (Evidence Quality × 0.4) + (Agent Consensus × 0.3) + (Source Reliability × 0.3)
    """

    def calculate(
        self,
        agent_results: List[Dict[str, Any]],
        sources: List[Dict[str, Any]],
        evidence_summary: Dict[str, int]
    ) -> Tuple[int, str, str]:
        """
        Calculate credibility score using weighted formula.
        
        When an official fact-check verdict exists (from FactCheckAgent / Google Fact Check API),
        it gets a strong anchor weight of 60% — outweighing inferred signals.
        Otherwise: Credibility = (Evidence Quality × 0.4) + (Consensus × 0.3) + (Reliability × 0.3)
        """
        # ── Step 1: Check for official fact-check verdict ──────────────
        official_result = next(
            (r for r in agent_results
             if r.get('agent') == 'factcheck' and r.get('is_official_verdict')
             and r.get('verdict') not in ('insufficient', None)
             and r.get('official_checks_found', 0) > 0),
            None
        )
        
        # ── Step 2: Standard components ────────────────────────────────
        evidence_quality    = self._calculate_evidence_quality(sources)
        agent_consensus     = self._calculate_agent_consensus(agent_results)
        source_reliability  = self._calculate_source_reliability(sources)
        
        raw_score = (
            (evidence_quality  * 0.4) +
            (agent_consensus   * 0.3) +
            (source_reliability * 0.3)
        )
        
        # ── Step 3: Official verdict anchor (if exists) ────────────────
        if official_result:
            # Convert avg_truth_score (0-1) to 0-100 scale
            official_score = official_result.get('avg_truth_score', 0.5) * 100
            # Blend: 60% official truth score + 40% inferred pipeline score
            raw_score = (official_score * 0.60) + (raw_score * 0.40)
            logger.info(
                f"Official fact-check anchor applied: official={official_score:.1f}, "
                f"inferred={raw_score:.1f}, blended={raw_score:.1f}"
            )
        
        # ── Step 4: Confidence penalty ─────────────────────────────────
        final_score = self._apply_confidence_penalty(raw_score, agent_results)
        final_score = max(0, min(100, int(final_score)))
        
        category   = self._map_score_to_category(final_score)
        confidence = self._calculate_confidence_level(agent_results, sources)
        
        # Upgrade confidence when we have an official verdict
        if official_result and confidence == "Low":
            confidence = "Medium"   # Official source auto-bumps Low → Medium
        
        return final_score, category, confidence

    def _calculate_evidence_quality(self, sources: List[Dict[str, Any]]) -> float:
        """
        Calculate Evidence Quality (40% weight) by weighting sources by tier and stance.
        
        Requirement 4.2: Weight sources by tier (Tier 1: 1.0, Tier 2: 0.7, Tier 3: 0.4, Tier 4: 0.2)
        
        Returns:
            Score in range [0, 100]
        """
        if not sources:
            return 50.0  # Neutral when no evidence
        
        supporting_score = 0.0
        contradicting_score = 0.0
        
        for source in sources:
            tier = source.get('credibility_tier', 'tier_4')
            stance = source.get('stance', 'neutral')
            weight = TIER_WEIGHTS.get(tier, 0.2)
            
            if stance == 'supporting':
                supporting_score += weight
            elif stance == 'contradicting':
                contradicting_score += weight
        
        total_weight = supporting_score + contradicting_score
        
        if total_weight == 0:
            return 50.0  # Neutral when no supporting or contradicting evidence
        
        # Higher supporting score = higher credibility
        return (supporting_score / total_weight) * 100

    def _calculate_agent_consensus(self, agent_results: List[Dict[str, Any]]) -> float:
        """
        Calculate Agent Consensus (30% weight) as percentage of agents with matching verdicts.
        
        Requirement 4.3: Compute the percentage of agents with matching verdicts
        
        Returns:
            Score in range [0, 100]
        """
        if not agent_results:
            return 50.0  # Neutral when no agents
        
        # Filter out insufficient verdicts
        verdicts = [
            r.get('verdict', 'insufficient')
            for r in agent_results
            if r.get('verdict') != 'insufficient'
        ]
        
        if not verdicts:
            return 50.0  # Neutral when no verdicts
        
        # Count most common verdict
        from collections import Counter
        verdict_counts = Counter(verdicts)
        most_common_verdict, max_count = verdict_counts.most_common(1)[0]
        
        # Calculate consensus percentage
        consensus_pct = (max_count / len(verdicts)) * 100
        
        # If most common verdict is 'supporting', high consensus = high score
        # If most common verdict is 'contradicting', high consensus = low score
        if most_common_verdict == 'supporting':
            return consensus_pct
        elif most_common_verdict == 'contradicting':
            return 100 - consensus_pct
        else:  # neutral or other
            return 50.0

    def _calculate_source_reliability(self, sources: List[Dict[str, Any]]) -> float:
        """
        Calculate Source Reliability (30% weight) as average credibility scores of all sources.
        
        Requirement 4.4: Average the credibility scores of all consulted sources
        
        Returns:
            Score in range [0, 100]
        """
        if not sources:
            return 50.0  # Neutral when no sources
        
        # credibility_score is 0.0-1.0, convert to 0-100
        scores = [source.get('credibility_score', 0.5) * 100 for source in sources]
        
        return sum(scores) / len(scores)

    def _apply_confidence_penalty(
        self,
        score: float,
        agent_results: List[Dict[str, Any]]
    ) -> float:
        """
        Apply penalty to score if agent confidence is below 0.5.
        
        Requirement 4.10: When agent confidence is below 0.5, apply a penalty to the credibility score
        
        Returns:
            Adjusted score
        """
        confidences = [
            r.get('confidence', 0.0)
            for r in agent_results
            if r.get('confidence', 0.0) > 0
        ]
        
        if not confidences:
            return score * 0.5  # 50% penalty if no confidence scores
        
        avg_confidence = sum(confidences) / len(confidences)
        
        if avg_confidence < 0.5:
            # Apply proportional penalty: 0-50% penalty based on how low confidence is
            penalty_factor = 1 - (0.5 - avg_confidence)
            return score * penalty_factor
        
        return score

    def _map_score_to_category(self, score: int) -> str:
        """
        Map credibility score to category.
        
        Requirements 4.5-4.9:
        - 0-39: "Verified False"
        - 40-59: "Likely False"
        - 60-69: "Uncertain"
        - 70-84: "Likely True"
        - 85-100: "Verified True"
        
        Returns:
            Category string
        """
        if score >= 85:
            return "Verified True"
        elif score >= 70:
            return "Likely True"
        elif score >= 60:
            return "Uncertain"
        elif score >= 40:
            return "Likely False"
        else:
            return "Verified False"

    def _calculate_confidence_level(
        self,
        agent_results: List[Dict[str, Any]],
        sources: List[Dict[str, Any]]
    ) -> str:
        """
        Calculate confidence level based on agent confidence and source count.
        
        Returns:
            "High", "Medium", or "Low"
        """
        confidences = [
            r.get('confidence', 0.0)
            for r in agent_results
            if r.get('confidence', 0.0) > 0
        ]
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        source_count = len(sources)
        
        if avg_confidence >= 0.8 and source_count >= 30:
            return "High"
        elif avg_confidence >= 0.6 and source_count >= 15:
            return "Medium"
        else:
            return "Low"
