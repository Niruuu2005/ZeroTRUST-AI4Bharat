"""
Property-based tests for credibility scoring.

Property 5: Credibility Score Formula Correctness
**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

Property: For any set of agent results and sources, the credibility score should be 
calculated as: (Evidence Quality × 0.4) + (Agent Consensus × 0.3) + (Source Reliability × 0.3), 
with each component correctly weighted and the final score in the range [0, 100].
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from src.services.scorer import CredibilityScorer, TIER_WEIGHTS


# Custom strategies for generating test data

@st.composite
def source_strategy(draw):
    """Generate a valid source dictionary."""
    return {
        'url': draw(st.text(min_size=10, max_size=100)),
        'title': draw(st.text(min_size=5, max_size=100)),
        'credibility_tier': draw(st.sampled_from(['tier_1', 'tier_2', 'tier_3', 'tier_4'])),
        'credibility_score': draw(st.floats(min_value=0.0, max_value=1.0)),
        'stance': draw(st.sampled_from(['supporting', 'contradicting', 'neutral']))
    }


@st.composite
def agent_result_strategy(draw):
    """Generate a valid agent result dictionary."""
    return {
        'agent': draw(st.sampled_from(['news', 'research', 'scientific', 'social_media', 'sentiment', 'scraper'])),
        'verdict': draw(st.sampled_from(['supporting', 'contradicting', 'neutral', 'insufficient'])),
        'confidence': draw(st.floats(min_value=0.0, max_value=1.0))
    }


class TestCredibilityScoringProperties:
    """Property-based tests for credibility scoring."""
    
    @given(
        sources=st.lists(source_strategy(), min_size=1, max_size=50),
        agent_results=st.lists(agent_result_strategy(), min_size=1, max_size=6)
    )
    @settings(max_examples=100)
    def test_score_always_in_valid_range(self, sources, agent_results):
        """
        Property 5: Score Range Validity
        **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
        
        For any set of agent results and sources, the credibility score should 
        always be in the range [0, 100].
        """
        scorer = CredibilityScorer()
        evidence_summary = {'supporting': 0, 'contradicting': 0, 'neutral': 0}
        
        score, category, confidence = scorer.calculate(agent_results, sources, evidence_summary)
        
        # Property: Score must be in valid range
        assert 0 <= score <= 100, (
            f"Score {score} is out of valid range [0, 100]\n"
            f"Sources: {len(sources)}\n"
            f"Agent results: {len(agent_results)}"
        )
        
        # Property: Score must be an integer
        assert isinstance(score, int), (
            f"Score {score} is not an integer (type: {type(score)})"
        )
    
    @given(
        sources=st.lists(source_strategy(), min_size=1, max_size=50),
        agent_results=st.lists(agent_result_strategy(), min_size=1, max_size=6)
    )
    @settings(max_examples=100)
    def test_weighted_formula_components_contribute(self, sources, agent_results):
        """
        Property 5: Weighted Formula Component Contribution
        **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
        
        The final score should be influenced by all three components:
        Evidence Quality (40%), Agent Consensus (30%), Source Reliability (30%).
        """
        scorer = CredibilityScorer()
        evidence_summary = {'supporting': 0, 'contradicting': 0, 'neutral': 0}
        
        # Calculate individual components
        evidence_quality = scorer._calculate_evidence_quality(sources)
        agent_consensus = scorer._calculate_agent_consensus(agent_results)
        source_reliability = scorer._calculate_source_reliability(sources)
        
        # Property: Each component should be in valid range [0, 100]
        assert 0 <= evidence_quality <= 100, (
            f"Evidence quality {evidence_quality} out of range"
        )
        assert 0 <= agent_consensus <= 100, (
            f"Agent consensus {agent_consensus} out of range"
        )
        assert 0 <= source_reliability <= 100, (
            f"Source reliability {source_reliability} out of range"
        )
        
        # Calculate expected weighted score (before confidence penalty)
        expected_raw_score = (
            (evidence_quality * 0.4) +
            (agent_consensus * 0.3) +
            (source_reliability * 0.3)
        )
        
        # Property: Raw weighted score should be in valid range
        assert 0 <= expected_raw_score <= 100, (
            f"Raw weighted score {expected_raw_score} out of range\n"
            f"Evidence Quality: {evidence_quality}\n"
            f"Agent Consensus: {agent_consensus}\n"
            f"Source Reliability: {source_reliability}"
        )
    
    @given(
        sources=st.lists(source_strategy(), min_size=1, max_size=50),
        agent_results=st.lists(agent_result_strategy(), min_size=1, max_size=6)
    )
    @settings(max_examples=100)
    def test_score_deterministic_for_same_inputs(self, sources, agent_results):
        """
        Property 5: Deterministic Calculation
        **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
        
        For the same inputs, the credibility score calculation should always 
        produce the same result (deterministic).
        """
        scorer = CredibilityScorer()
        evidence_summary = {'supporting': 0, 'contradicting': 0, 'neutral': 0}
        
        # Calculate score twice with same inputs
        score1, category1, confidence1 = scorer.calculate(agent_results, sources, evidence_summary)
        score2, category2, confidence2 = scorer.calculate(agent_results, sources, evidence_summary)
        
        # Property: Results should be identical
        assert score1 == score2, (
            f"Non-deterministic score calculation:\n"
            f"First call: {score1}\n"
            f"Second call: {score2}"
        )
        assert category1 == category2, (
            f"Non-deterministic category mapping:\n"
            f"First call: {category1}\n"
            f"Second call: {category2}"
        )
        assert confidence1 == confidence2, (
            f"Non-deterministic confidence calculation:\n"
            f"First call: {confidence1}\n"
            f"Second call: {confidence2}"
        )
    
    @given(
        sources=st.lists(
            st.builds(
                dict,
                credibility_tier=st.just('tier_1'),
                stance=st.just('supporting'),
                credibility_score=st.floats(min_value=0.8, max_value=1.0),
                url=st.text(min_size=10)
            ),
            min_size=5,
            max_size=20
        ),
        agent_results=st.lists(
            st.builds(
                dict,
                agent=st.sampled_from(['news', 'research', 'scientific']),
                verdict=st.just('supporting'),
                confidence=st.floats(min_value=0.7, max_value=1.0)
            ),
            min_size=3,
            max_size=6
        )
    )
    @settings(max_examples=100)
    def test_all_supporting_evidence_gives_high_score(self, sources, agent_results):
        """
        Property 5: All Supporting Evidence Produces High Score
        **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
        
        When all sources are supporting with high credibility and all agents 
        agree with supporting verdict and high confidence, the score should be high (>= 70).
        """
        scorer = CredibilityScorer()
        evidence_summary = {'supporting': len(sources), 'contradicting': 0, 'neutral': 0}
        
        score, category, confidence = scorer.calculate(agent_results, sources, evidence_summary)
        
        # Property: All supporting evidence should produce high score
        assert score >= 70, (
            f"Expected high score (>= 70) for all supporting evidence, got {score}\n"
            f"Sources: {len(sources)} all supporting tier_1\n"
            f"Agents: {len(agent_results)} all supporting with high confidence"
        )
    
    @given(
        sources=st.lists(
            st.builds(
                dict,
                credibility_tier=st.just('tier_1'),
                stance=st.just('contradicting'),
                credibility_score=st.floats(min_value=0.8, max_value=1.0),
                url=st.text(min_size=10)
            ),
            min_size=5,
            max_size=20
        ),
        agent_results=st.lists(
            st.builds(
                dict,
                agent=st.sampled_from(['news', 'research', 'scientific']),
                verdict=st.just('contradicting'),
                confidence=st.floats(min_value=0.7, max_value=1.0)
            ),
            min_size=3,
            max_size=6
        )
    )
    @settings(max_examples=100)
    def test_all_contradicting_evidence_gives_low_score(self, sources, agent_results):
        """
        Property 5: All Contradicting Evidence Produces Low Score
        **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
        
        When all sources are contradicting with high credibility and all agents 
        agree with contradicting verdict and high confidence, the score should be low (<= 40).
        """
        scorer = CredibilityScorer()
        evidence_summary = {'supporting': 0, 'contradicting': len(sources), 'neutral': 0}
        
        score, category, confidence = scorer.calculate(agent_results, sources, evidence_summary)
        
        # Property: All contradicting evidence should produce low score
        assert score <= 40, (
            f"Expected low score (<= 40) for all contradicting evidence, got {score}\n"
            f"Sources: {len(sources)} all contradicting tier_1\n"
            f"Agents: {len(agent_results)} all contradicting with high confidence"
        )
    
    @given(
        tier=st.sampled_from(['tier_1', 'tier_2', 'tier_3', 'tier_4']),
        num_sources=st.integers(min_value=2, max_value=20)
    )
    @settings(max_examples=100)
    def test_tier_weights_affect_evidence_quality(self, tier, num_sources):
        """
        Property 5: Tier Weights Correctly Applied
        **Validates: Requirements 4.2**
        
        Sources with different tiers should be weighted according to the tier weights:
        tier_1: 1.0, tier_2: 0.7, tier_3: 0.4, tier_4: 0.2
        """
        scorer = CredibilityScorer()
        
        # Create sources with same stance but different tiers
        sources_supporting = [
            {
                'credibility_tier': tier,
                'stance': 'supporting',
                'credibility_score': 0.8,
                'url': f'http://example.com/{i}'
            }
            for i in range(num_sources)
        ]
        
        sources_contradicting = [
            {
                'credibility_tier': tier,
                'stance': 'contradicting',
                'credibility_score': 0.8,
                'url': f'http://example.com/{i}'
            }
            for i in range(num_sources)
        ]
        
        # Calculate evidence quality for both
        quality_supporting = scorer._calculate_evidence_quality(sources_supporting)
        quality_contradicting = scorer._calculate_evidence_quality(sources_contradicting)
        
        # Property: All supporting should give 100%, all contradicting should give 0%
        assert quality_supporting == 100.0, (
            f"All supporting sources should give 100% evidence quality, got {quality_supporting}"
        )
        assert quality_contradicting == 0.0, (
            f"All contradicting sources should give 0% evidence quality, got {quality_contradicting}"
        )
    
    @given(
        num_supporting=st.integers(min_value=1, max_value=10),
        num_contradicting=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100)
    def test_evidence_quality_proportional_to_stance_ratio(self, num_supporting, num_contradicting):
        """
        Property 5: Evidence Quality Proportional to Stance Ratio
        **Validates: Requirements 4.2**
        
        Evidence quality should be proportional to the ratio of supporting vs 
        contradicting sources (weighted by tier).
        """
        scorer = CredibilityScorer()
        
        # Create equal-tier sources with different stances
        sources = []
        for i in range(num_supporting):
            sources.append({
                'credibility_tier': 'tier_1',
                'stance': 'supporting',
                'credibility_score': 0.8,
                'url': f'http://example.com/s{i}'
            })
        for i in range(num_contradicting):
            sources.append({
                'credibility_tier': 'tier_1',
                'stance': 'contradicting',
                'credibility_score': 0.8,
                'url': f'http://example.com/c{i}'
            })
        
        quality = scorer._calculate_evidence_quality(sources)
        
        # Calculate expected quality
        expected_quality = (num_supporting / (num_supporting + num_contradicting)) * 100
        
        # Property: Quality should match expected ratio
        assert abs(quality - expected_quality) < 0.1, (
            f"Evidence quality {quality} doesn't match expected {expected_quality}\n"
            f"Supporting: {num_supporting}, Contradicting: {num_contradicting}"
        )
    
    @given(
        num_agents=st.integers(min_value=2, max_value=6),
        verdict=st.sampled_from(['supporting', 'contradicting'])
    )
    @settings(max_examples=100)
    def test_unanimous_agent_consensus(self, num_agents, verdict):
        """
        Property 5: Unanimous Agent Consensus
        **Validates: Requirements 4.3**
        
        When all agents have the same verdict, consensus should be 100% for 
        supporting or 0% for contradicting.
        """
        scorer = CredibilityScorer()
        
        agent_results = [
            {
                'agent': f'agent_{i}',
                'verdict': verdict,
                'confidence': 0.8
            }
            for i in range(num_agents)
        ]
        
        consensus = scorer._calculate_agent_consensus(agent_results)
        
        # Property: Unanimous verdict should give extreme consensus
        if verdict == 'supporting':
            assert consensus == 100.0, (
                f"Unanimous supporting verdict should give 100% consensus, got {consensus}"
            )
        elif verdict == 'contradicting':
            assert consensus == 0.0, (
                f"Unanimous contradicting verdict should give 0% consensus, got {consensus}"
            )
    
    @given(
        credibility_scores=st.lists(
            st.floats(min_value=0.0, max_value=1.0),
            min_size=1,
            max_size=50
        )
    )
    @settings(max_examples=100)
    def test_source_reliability_is_average_of_scores(self, credibility_scores):
        """
        Property 5: Source Reliability is Average
        **Validates: Requirements 4.4**
        
        Source reliability should be the average of all source credibility scores 
        (converted to 0-100 scale).
        """
        scorer = CredibilityScorer()
        
        sources = [
            {
                'credibility_tier': 'tier_1',
                'stance': 'supporting',
                'credibility_score': score,
                'url': f'http://example.com/{i}'
            }
            for i, score in enumerate(credibility_scores)
        ]
        
        reliability = scorer._calculate_source_reliability(sources)
        
        # Calculate expected average
        expected_avg = (sum(credibility_scores) / len(credibility_scores)) * 100
        
        # Property: Reliability should equal average of scores
        assert abs(reliability - expected_avg) < 0.01, (
            f"Source reliability {reliability} doesn't match expected average {expected_avg}\n"
            f"Scores: {credibility_scores}"
        )
    
    @given(
        sources=st.lists(source_strategy(), min_size=1, max_size=50),
        agent_results=st.lists(agent_result_strategy(), min_size=1, max_size=6)
    )
    @settings(max_examples=100)
    def test_confidence_penalty_reduces_or_maintains_score(self, sources, agent_results):
        """
        Property 5: Confidence Penalty Never Increases Score
        **Validates: Requirements 4.1, 4.10**
        
        Applying confidence penalty should never increase the score, only 
        reduce it or keep it the same.
        """
        scorer = CredibilityScorer()
        
        # Calculate raw score without penalty
        evidence_quality = scorer._calculate_evidence_quality(sources)
        agent_consensus = scorer._calculate_agent_consensus(agent_results)
        source_reliability = scorer._calculate_source_reliability(sources)
        
        raw_score = (
            (evidence_quality * 0.4) +
            (agent_consensus * 0.3) +
            (source_reliability * 0.3)
        )
        
        # Apply penalty
        penalized_score = scorer._apply_confidence_penalty(raw_score, agent_results)
        
        # Property: Penalty should never increase score
        assert penalized_score <= raw_score, (
            f"Confidence penalty increased score from {raw_score} to {penalized_score}\n"
            f"Agent results: {agent_results}"
        )
    
    @given(
        sources=st.lists(source_strategy(), min_size=1, max_size=50),
        low_confidence_agents=st.lists(
            st.builds(
                dict,
                agent=st.sampled_from(['news', 'research', 'scientific']),
                verdict=st.sampled_from(['supporting', 'contradicting']),
                confidence=st.floats(min_value=0.0, max_value=0.49)
            ),
            min_size=1,
            max_size=6
        )
    )
    @settings(max_examples=100)
    def test_low_confidence_applies_penalty(self, sources, low_confidence_agents):
        """
        Property 5: Low Confidence Applies Penalty
        **Validates: Requirements 4.10**
        
        When average agent confidence is below 0.5, a penalty should be applied 
        to the credibility score.
        """
        scorer = CredibilityScorer()
        evidence_summary = {'supporting': 0, 'contradicting': 0, 'neutral': 0}
        
        # Calculate raw score
        evidence_quality = scorer._calculate_evidence_quality(sources)
        agent_consensus = scorer._calculate_agent_consensus(low_confidence_agents)
        source_reliability = scorer._calculate_source_reliability(sources)
        
        raw_score = (
            (evidence_quality * 0.4) +
            (agent_consensus * 0.3) +
            (source_reliability * 0.3)
        )
        
        # Calculate final score with penalty
        final_score, _, _ = scorer.calculate(low_confidence_agents, sources, evidence_summary)
        
        # Property: Final score should be less than raw score due to penalty
        # (unless raw score is already very low)
        if raw_score > 10:  # Only check if raw score is meaningful
            assert final_score < raw_score, (
                f"Low confidence should apply penalty:\n"
                f"Raw score: {raw_score}\n"
                f"Final score: {final_score}\n"
                f"Avg confidence: {sum(a['confidence'] for a in low_confidence_agents) / len(low_confidence_agents)}"
            )
    
    @given(st.integers(min_value=0, max_value=100))
    @settings(max_examples=100)
    def test_score_to_category_mapping_complete(self, score):
        """
        Property 5: Complete Score-to-Category Mapping
        **Validates: Requirements 4.1**
        
        Every score in the range [0, 100] should map to exactly one category.
        """
        scorer = CredibilityScorer()
        category = scorer._map_score_to_category(score)
        
        # Property: Category should be one of the five valid categories
        valid_categories = [
            "Verified False",
            "Likely False",
            "Uncertain",
            "Likely True",
            "Verified True"
        ]
        
        assert category in valid_categories, (
            f"Score {score} mapped to invalid category '{category}'"
        )
        
        # Property: Category should match expected range
        if 0 <= score <= 39:
            assert category == "Verified False"
        elif 40 <= score <= 59:
            assert category == "Likely False"
        elif 60 <= score <= 69:
            assert category == "Uncertain"
        elif 70 <= score <= 84:
            assert category == "Likely True"
        elif 85 <= score <= 100:
            assert category == "Verified True"
    
    @given(
        sources=st.lists(source_strategy(), min_size=0, max_size=50),
        agent_results=st.lists(agent_result_strategy(), min_size=0, max_size=6)
    )
    @settings(max_examples=100)
    def test_empty_inputs_produce_valid_output(self, sources, agent_results):
        """
        Property 5: Empty Inputs Handled Gracefully
        **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
        
        Even with empty or minimal inputs, the scorer should produce valid output
        without crashing.
        """
        scorer = CredibilityScorer()
        evidence_summary = {'supporting': 0, 'contradicting': 0, 'neutral': 0}
        
        # Should not raise exception
        score, category, confidence = scorer.calculate(agent_results, sources, evidence_summary)
        
        # Property: Output should still be valid
        assert 0 <= score <= 100
        assert category in ["Verified False", "Likely False", "Uncertain", "Likely True", "Verified True"]
        assert confidence in ["High", "Medium", "Low"]
    
    @given(
        sources=st.lists(
            st.builds(
                dict,
                credibility_tier=st.just('tier_1'),
                stance=st.just('neutral'),
                credibility_score=st.floats(min_value=0.5, max_value=0.8),
                url=st.text(min_size=10)
            ),
            min_size=5,
            max_size=20
        ),
        agent_results=st.lists(
            st.builds(
                dict,
                agent=st.sampled_from(['news', 'research', 'scientific']),
                verdict=st.just('neutral'),
                confidence=st.floats(min_value=0.5, max_value=0.8)
            ),
            min_size=3,
            max_size=6
        )
    )
    @settings(max_examples=100)
    def test_neutral_evidence_gives_middle_range_score(self, sources, agent_results):
        """
        Property 5: Neutral Evidence Produces Middle-Range Score
        **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
        
        When all evidence is neutral, the score should be in the middle range
        (approximately 40-70).
        """
        scorer = CredibilityScorer()
        evidence_summary = {'supporting': 0, 'contradicting': 0, 'neutral': len(sources)}
        
        score, category, confidence = scorer.calculate(agent_results, sources, evidence_summary)
        
        # Property: Neutral evidence should produce middle-range score
        assert 30 <= score <= 70, (
            f"Expected middle-range score (30-70) for neutral evidence, got {score}\n"
            f"Sources: {len(sources)} all neutral\n"
            f"Agents: {len(agent_results)} all neutral"
        )
