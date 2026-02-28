"""
Unit tests for CredibilityScorer class

Tests the weighted formula:
Credibility Score = (Evidence Quality × 0.4) + (Agent Consensus × 0.3) + (Source Reliability × 0.3)

Validates Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 4.10
"""
import pytest
from src.services.scorer import CredibilityScorer


class TestCredibilityScorer:
    """Test suite for CredibilityScorer"""

    def setup_method(self):
        """Setup test fixtures"""
        self.scorer = CredibilityScorer()

    # Test Evidence Quality calculation (Requirement 4.2)
    
    def test_evidence_quality_all_supporting_tier1(self):
        """All tier 1 supporting sources should give 100% evidence quality"""
        sources = [
            {'credibility_tier': 'tier_1', 'stance': 'supporting', 'credibility_score': 0.9},
            {'credibility_tier': 'tier_1', 'stance': 'supporting', 'credibility_score': 0.95},
        ]
        quality = self.scorer._calculate_evidence_quality(sources)
        assert quality == 100.0

    def test_evidence_quality_all_contradicting_tier1(self):
        """All tier 1 contradicting sources should give 0% evidence quality"""
        sources = [
            {'credibility_tier': 'tier_1', 'stance': 'contradicting', 'credibility_score': 0.9},
            {'credibility_tier': 'tier_1', 'stance': 'contradicting', 'credibility_score': 0.95},
        ]
        quality = self.scorer._calculate_evidence_quality(sources)
        assert quality == 0.0

    def test_evidence_quality_mixed_stances(self):
        """Mixed supporting and contradicting sources should give proportional score"""
        sources = [
            {'credibility_tier': 'tier_1', 'stance': 'supporting', 'credibility_score': 0.9},
            {'credibility_tier': 'tier_1', 'stance': 'supporting', 'credibility_score': 0.9},
            {'credibility_tier': 'tier_1', 'stance': 'contradicting', 'credibility_score': 0.9},
        ]
        quality = self.scorer._calculate_evidence_quality(sources)
        # 2 supporting (weight 2.0) vs 1 contradicting (weight 1.0) = 2/3 = 66.67%
        assert abs(quality - 66.67) < 0.1

    def test_evidence_quality_tier_weights(self):
        """Different tier weights should affect evidence quality"""
        sources_tier1 = [
            {'credibility_tier': 'tier_1', 'stance': 'supporting', 'credibility_score': 0.9},
            {'credibility_tier': 'tier_1', 'stance': 'contradicting', 'credibility_score': 0.9},
        ]
        sources_tier2 = [
            {'credibility_tier': 'tier_2', 'stance': 'supporting', 'credibility_score': 0.9},
            {'credibility_tier': 'tier_2', 'stance': 'contradicting', 'credibility_score': 0.9},
        ]
        
        quality1 = self.scorer._calculate_evidence_quality(sources_tier1)
        quality2 = self.scorer._calculate_evidence_quality(sources_tier2)
        
        # Both should be 50% since equal supporting/contradicting
        assert quality1 == 50.0
        assert quality2 == 50.0

    def test_evidence_quality_no_sources(self):
        """No sources should return neutral score"""
        quality = self.scorer._calculate_evidence_quality([])
        assert quality == 50.0

    def test_evidence_quality_only_neutral_sources(self):
        """Only neutral sources should return neutral score"""
        sources = [
            {'credibility_tier': 'tier_1', 'stance': 'neutral', 'credibility_score': 0.9},
            {'credibility_tier': 'tier_2', 'stance': 'neutral', 'credibility_score': 0.8},
        ]
        quality = self.scorer._calculate_evidence_quality(sources)
        assert quality == 50.0

    # Test Agent Consensus calculation (Requirement 4.3)
    
    def test_agent_consensus_all_supporting(self):
        """All agents supporting should give 100% consensus"""
        agent_results = [
            {'agent': 'news', 'verdict': 'supporting', 'confidence': 0.9},
            {'agent': 'research', 'verdict': 'supporting', 'confidence': 0.8},
            {'agent': 'scientific', 'verdict': 'supporting', 'confidence': 0.85},
        ]
        consensus = self.scorer._calculate_agent_consensus(agent_results)
        assert consensus == 100.0

    def test_agent_consensus_all_contradicting(self):
        """All agents contradicting should give 0% consensus"""
        agent_results = [
            {'agent': 'news', 'verdict': 'contradicting', 'confidence': 0.9},
            {'agent': 'research', 'verdict': 'contradicting', 'confidence': 0.8},
            {'agent': 'scientific', 'verdict': 'contradicting', 'confidence': 0.85},
        ]
        consensus = self.scorer._calculate_agent_consensus(agent_results)
        assert consensus == 0.0

    def test_agent_consensus_mixed_verdicts(self):
        """Mixed verdicts should give proportional consensus"""
        agent_results = [
            {'agent': 'news', 'verdict': 'supporting', 'confidence': 0.9},
            {'agent': 'research', 'verdict': 'supporting', 'confidence': 0.8},
            {'agent': 'scientific', 'verdict': 'contradicting', 'confidence': 0.85},
        ]
        consensus = self.scorer._calculate_agent_consensus(agent_results)
        # 2 out of 3 supporting = 66.67%
        assert abs(consensus - 66.67) < 0.1

    def test_agent_consensus_ignores_insufficient(self):
        """Insufficient verdicts should be ignored"""
        agent_results = [
            {'agent': 'news', 'verdict': 'supporting', 'confidence': 0.9},
            {'agent': 'research', 'verdict': 'supporting', 'confidence': 0.8},
            {'agent': 'scientific', 'verdict': 'insufficient', 'confidence': 0.0},
        ]
        consensus = self.scorer._calculate_agent_consensus(agent_results)
        # Only 2 valid verdicts, both supporting = 100%
        assert consensus == 100.0

    def test_agent_consensus_no_agents(self):
        """No agents should return neutral score"""
        consensus = self.scorer._calculate_agent_consensus([])
        assert consensus == 50.0

    def test_agent_consensus_all_insufficient(self):
        """All insufficient verdicts should return neutral score"""
        agent_results = [
            {'agent': 'news', 'verdict': 'insufficient', 'confidence': 0.0},
            {'agent': 'research', 'verdict': 'insufficient', 'confidence': 0.0},
        ]
        consensus = self.scorer._calculate_agent_consensus(agent_results)
        assert consensus == 50.0

    # Test Source Reliability calculation (Requirement 4.4)
    
    def test_source_reliability_high_scores(self):
        """High credibility scores should give high reliability"""
        sources = [
            {'credibility_tier': 'tier_1', 'stance': 'supporting', 'credibility_score': 0.9},
            {'credibility_tier': 'tier_1', 'stance': 'supporting', 'credibility_score': 0.95},
            {'credibility_tier': 'tier_1', 'stance': 'supporting', 'credibility_score': 0.85},
        ]
        reliability = self.scorer._calculate_source_reliability(sources)
        # Average: (90 + 95 + 85) / 3 = 90
        assert reliability == 90.0

    def test_source_reliability_low_scores(self):
        """Low credibility scores should give low reliability"""
        sources = [
            {'credibility_tier': 'tier_4', 'stance': 'supporting', 'credibility_score': 0.3},
            {'credibility_tier': 'tier_4', 'stance': 'supporting', 'credibility_score': 0.2},
        ]
        reliability = self.scorer._calculate_source_reliability(sources)
        # Average: (30 + 20) / 2 = 25
        assert reliability == 25.0

    def test_source_reliability_no_sources(self):
        """No sources should return neutral score"""
        reliability = self.scorer._calculate_source_reliability([])
        assert reliability == 50.0

    # Test Confidence Penalty (Requirement 4.10)
    
    def test_confidence_penalty_high_confidence(self):
        """High confidence (>= 0.5) should not apply penalty"""
        agent_results = [
            {'agent': 'news', 'verdict': 'supporting', 'confidence': 0.8},
            {'agent': 'research', 'verdict': 'supporting', 'confidence': 0.7},
        ]
        score = self.scorer._apply_confidence_penalty(80.0, agent_results)
        assert score == 80.0

    def test_confidence_penalty_low_confidence(self):
        """Low confidence (< 0.5) should apply penalty"""
        agent_results = [
            {'agent': 'news', 'verdict': 'supporting', 'confidence': 0.3},
            {'agent': 'research', 'verdict': 'supporting', 'confidence': 0.2},
        ]
        # Average confidence: 0.25
        # Penalty factor: 1 - (0.5 - 0.25) = 0.75
        score = self.scorer._apply_confidence_penalty(80.0, agent_results)
        assert score == 60.0  # 80 * 0.75

    def test_confidence_penalty_no_confidence(self):
        """No confidence scores should apply 50% penalty"""
        agent_results = [
            {'agent': 'news', 'verdict': 'supporting', 'confidence': 0.0},
        ]
        score = self.scorer._apply_confidence_penalty(80.0, agent_results)
        assert score == 40.0  # 80 * 0.5

    # Test Score-to-Category Mapping (Requirements 4.5-4.9)
    
    def test_category_verified_true(self):
        """Score 85-100 should map to 'Verified True'"""
        assert self.scorer._map_score_to_category(85) == "Verified True"
        assert self.scorer._map_score_to_category(90) == "Verified True"
        assert self.scorer._map_score_to_category(100) == "Verified True"

    def test_category_likely_true(self):
        """Score 70-84 should map to 'Likely True'"""
        assert self.scorer._map_score_to_category(70) == "Likely True"
        assert self.scorer._map_score_to_category(75) == "Likely True"
        assert self.scorer._map_score_to_category(84) == "Likely True"

    def test_category_uncertain(self):
        """Score 60-69 should map to 'Uncertain'"""
        assert self.scorer._map_score_to_category(60) == "Uncertain"
        assert self.scorer._map_score_to_category(65) == "Uncertain"
        assert self.scorer._map_score_to_category(69) == "Uncertain"

    def test_category_likely_false(self):
        """Score 40-59 should map to 'Likely False'"""
        assert self.scorer._map_score_to_category(40) == "Likely False"
        assert self.scorer._map_score_to_category(50) == "Likely False"
        assert self.scorer._map_score_to_category(59) == "Likely False"

    def test_category_verified_false(self):
        """Score 0-39 should map to 'Verified False'"""
        assert self.scorer._map_score_to_category(0) == "Verified False"
        assert self.scorer._map_score_to_category(20) == "Verified False"
        assert self.scorer._map_score_to_category(39) == "Verified False"

    # Test Confidence Level calculation
    
    def test_confidence_level_high(self):
        """High confidence (>= 0.8) and many sources (>= 30) should give 'High'"""
        agent_results = [
            {'agent': 'news', 'verdict': 'supporting', 'confidence': 0.85},
            {'agent': 'research', 'verdict': 'supporting', 'confidence': 0.9},
        ]
        sources = [{'url': f'http://example.com/{i}'} for i in range(30)]
        confidence = self.scorer._calculate_confidence_level(agent_results, sources)
        assert confidence == "High"

    def test_confidence_level_medium(self):
        """Medium confidence (>= 0.6) and some sources (>= 15) should give 'Medium'"""
        agent_results = [
            {'agent': 'news', 'verdict': 'supporting', 'confidence': 0.7},
            {'agent': 'research', 'verdict': 'supporting', 'confidence': 0.6},
        ]
        sources = [{'url': f'http://example.com/{i}'} for i in range(15)]
        confidence = self.scorer._calculate_confidence_level(agent_results, sources)
        assert confidence == "Medium"

    def test_confidence_level_low(self):
        """Low confidence or few sources should give 'Low'"""
        agent_results = [
            {'agent': 'news', 'verdict': 'supporting', 'confidence': 0.4},
        ]
        sources = [{'url': 'http://example.com/1'}]
        confidence = self.scorer._calculate_confidence_level(agent_results, sources)
        assert confidence == "Low"

    # Test complete calculate() method (Requirement 4.1)
    
    def test_calculate_weighted_formula(self):
        """Test the complete weighted formula calculation"""
        agent_results = [
            {'agent': 'news', 'verdict': 'supporting', 'confidence': 0.8},
            {'agent': 'research', 'verdict': 'supporting', 'confidence': 0.7},
            {'agent': 'scientific', 'verdict': 'supporting', 'confidence': 0.9},
        ]
        sources = [
            {'credibility_tier': 'tier_1', 'stance': 'supporting', 'credibility_score': 0.9},
            {'credibility_tier': 'tier_1', 'stance': 'supporting', 'credibility_score': 0.85},
            {'credibility_tier': 'tier_2', 'stance': 'supporting', 'credibility_score': 0.8},
        ]
        evidence_summary = {'supporting': 3, 'contradicting': 0, 'neutral': 0}
        
        score, category, confidence = self.scorer.calculate(agent_results, sources, evidence_summary)
        
        # Verify score is in valid range
        assert 0 <= score <= 100
        # With all supporting evidence, should be high
        assert score >= 70
        # Should map to appropriate category
        assert category in ["Likely True", "Verified True"]
        # Should have confidence level
        assert confidence in ["High", "Medium", "Low"]

    def test_calculate_contradicting_evidence(self):
        """Test calculation with contradicting evidence"""
        agent_results = [
            {'agent': 'news', 'verdict': 'contradicting', 'confidence': 0.8},
            {'agent': 'research', 'verdict': 'contradicting', 'confidence': 0.7},
        ]
        sources = [
            {'credibility_tier': 'tier_1', 'stance': 'contradicting', 'credibility_score': 0.9},
            {'credibility_tier': 'tier_1', 'stance': 'contradicting', 'credibility_score': 0.85},
        ]
        evidence_summary = {'supporting': 0, 'contradicting': 2, 'neutral': 0}
        
        score, category, confidence = self.scorer.calculate(agent_results, sources, evidence_summary)
        
        # With all contradicting evidence, should be low
        assert score <= 40
        # Should map to false category
        assert category in ["Verified False", "Likely False"]

    def test_calculate_mixed_evidence(self):
        """Test calculation with mixed evidence"""
        agent_results = [
            {'agent': 'news', 'verdict': 'supporting', 'confidence': 0.7},
            {'agent': 'research', 'verdict': 'contradicting', 'confidence': 0.6},
        ]
        sources = [
            {'credibility_tier': 'tier_1', 'stance': 'supporting', 'credibility_score': 0.8},
            {'credibility_tier': 'tier_1', 'stance': 'contradicting', 'credibility_score': 0.75},
        ]
        evidence_summary = {'supporting': 1, 'contradicting': 1, 'neutral': 0}
        
        score, category, confidence = self.scorer.calculate(agent_results, sources, evidence_summary)
        
        # With mixed evidence, should be in middle range
        assert 30 <= score <= 70
        # Should map to uncertain or mixed category
        assert category in ["Uncertain", "Likely False", "Likely True"]

    def test_calculate_with_low_confidence_penalty(self):
        """Test that low confidence applies penalty"""
        agent_results = [
            {'agent': 'news', 'verdict': 'supporting', 'confidence': 0.3},
            {'agent': 'research', 'verdict': 'supporting', 'confidence': 0.2},
        ]
        sources = [
            {'credibility_tier': 'tier_1', 'stance': 'supporting', 'credibility_score': 0.9},
            {'credibility_tier': 'tier_1', 'stance': 'supporting', 'credibility_score': 0.95},
        ]
        evidence_summary = {'supporting': 2, 'contradicting': 0, 'neutral': 0}
        
        score, category, confidence = self.scorer.calculate(agent_results, sources, evidence_summary)
        
        # Even with all supporting evidence, low confidence should reduce score
        assert score < 80  # Should be penalized

    def test_calculate_empty_inputs(self):
        """Test calculation with empty inputs returns neutral values"""
        score, category, confidence = self.scorer.calculate([], [], {})
        
        # Should return neutral/low values
        assert 0 <= score <= 100
        assert category in ["Verified False", "Likely False", "Uncertain", "Likely True", "Verified True"]
        assert confidence in ["High", "Medium", "Low"]
