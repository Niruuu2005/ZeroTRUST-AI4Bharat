"""
Property-based tests for confidence penalty application.

Property 7: Confidence Penalty Application
**Validates: Requirements 4.10**

Property: For any agent result set where the average confidence is below 0.5, 
the system should apply a proportional penalty to the credibility score, 
reducing it by up to 50%.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from src.services.scorer import CredibilityScorer


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
def agent_result_with_confidence(draw, confidence_value):
    """Generate an agent result with a specific confidence value."""
    return {
        'agent': draw(st.sampled_from(['news', 'research', 'scientific', 'social_media', 'sentiment', 'scraper'])),
        'verdict': draw(st.sampled_from(['supporting', 'contradicting', 'neutral', 'insufficient'])),
        'confidence': confidence_value
    }


@st.composite
def low_confidence_agent_results(draw):
    """Generate agent results with average confidence below 0.5."""
    num_agents = draw(st.integers(min_value=1, max_value=6))
    # Generate confidences that average below 0.5
    confidences = draw(st.lists(
        st.floats(min_value=0.0, max_value=0.49),
        min_size=num_agents,
        max_size=num_agents
    ))
    
    results = []
    for conf in confidences:
        result = draw(agent_result_with_confidence(conf))
        results.append(result)
    
    return results


@st.composite
def high_confidence_agent_results(draw):
    """Generate agent results with average confidence >= 0.5."""
    num_agents = draw(st.integers(min_value=1, max_value=6))
    # Generate confidences that average >= 0.5
    confidences = draw(st.lists(
        st.floats(min_value=0.5, max_value=1.0),
        min_size=num_agents,
        max_size=num_agents
    ))
    
    results = []
    for conf in confidences:
        result = draw(agent_result_with_confidence(conf))
        results.append(result)
    
    return results


class TestConfidencePenaltyProperties:
    """Property-based tests for confidence penalty application."""
    
    @given(
        sources=st.lists(source_strategy(), min_size=1, max_size=50),
        agent_results=low_confidence_agent_results()
    )
    @settings(max_examples=100)
    def test_low_confidence_applies_penalty(self, sources, agent_results):
        """
        Property 7: Low Confidence Penalty Application
        **Validates: Requirements 4.10**
        
        For any agent result set where the average confidence is below 0.5,
        the system should apply a penalty to the credibility score.
        """
        scorer = CredibilityScorer()
        evidence_summary = {'supporting': 0, 'contradicting': 0, 'neutral': 0}
        
        # Calculate score with penalty
        score_with_penalty, _, _ = scorer.calculate(agent_results, sources, evidence_summary)
        
        # Calculate what the score would be without penalty
        # We need to calculate the raw score before penalty
        evidence_quality = scorer._calculate_evidence_quality(sources)
        agent_consensus = scorer._calculate_agent_consensus(agent_results)
        source_reliability = scorer._calculate_source_reliability(sources)
        
        raw_score = (
            (evidence_quality * 0.4) +
            (agent_consensus * 0.3) +
            (source_reliability * 0.3)
        )
        
        # Calculate average confidence (matching implementation logic)
        confidences = [r['confidence'] for r in agent_results if r['confidence'] > 0]
        
        if not confidences:
            # No valid confidences - 50% penalty should be applied
            expected_score = int(raw_score * 0.5)
            assert abs(score_with_penalty - expected_score) <= 1, (
                f"50% penalty not applied for no confidences: score_with_penalty ({score_with_penalty}) != expected ({expected_score})\n"
                f"Raw score: {raw_score}\n"
                f"Agent results: {agent_results}"
            )
        else:
            avg_confidence = sum(confidences) / len(confidences)
            
            # Property: When avg confidence < 0.5, penalty should be applied
            if avg_confidence < 0.5 and raw_score > 0:
                # The penalized score should be less than or equal to the raw score
                assert score_with_penalty <= raw_score, (
                    f"Penalty not applied: score_with_penalty ({score_with_penalty}) > raw_score ({raw_score})\n"
                    f"Average confidence: {avg_confidence}\n"
                    f"Agent results: {agent_results}"
                )
                
                # The penalty should reduce the score by up to 50%
                expected_min_score = raw_score * 0.5
                # Allow for rounding differences
                assert score_with_penalty >= (expected_min_score - 1), (
                    f"Penalty too severe: score_with_penalty ({score_with_penalty}) < expected_min ({expected_min_score})\n"
                    f"Average confidence: {avg_confidence}\n"
                    f"Raw score: {raw_score}"
                )
    
    @given(
        sources=st.lists(source_strategy(), min_size=1, max_size=50),
        agent_results=high_confidence_agent_results()
    )
    @settings(max_examples=100)
    def test_high_confidence_no_penalty(self, sources, agent_results):
        """
        Property 7: High Confidence No Penalty
        **Validates: Requirements 4.10**
        
        For any agent result set where the average confidence is >= 0.5,
        the system should NOT apply a penalty to the credibility score.
        """
        scorer = CredibilityScorer()
        evidence_summary = {'supporting': 0, 'contradicting': 0, 'neutral': 0}
        
        # Calculate score
        final_score, _, _ = scorer.calculate(agent_results, sources, evidence_summary)
        
        # Calculate raw score before penalty
        evidence_quality = scorer._calculate_evidence_quality(sources)
        agent_consensus = scorer._calculate_agent_consensus(agent_results)
        source_reliability = scorer._calculate_source_reliability(sources)
        
        raw_score = (
            (evidence_quality * 0.4) +
            (agent_consensus * 0.3) +
            (source_reliability * 0.3)
        )
        
        # Calculate average confidence
        confidences = [r['confidence'] for r in agent_results if r['confidence'] > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Property: When avg confidence >= 0.5, no penalty should be applied
        # The final score should equal the raw score (within rounding tolerance)
        assert abs(final_score - int(raw_score)) <= 1, (
            f"Unexpected penalty applied: final_score ({final_score}) != raw_score ({int(raw_score)})\n"
            f"Average confidence: {avg_confidence}\n"
            f"Agent results: {agent_results}"
        )
    
    @given(
        sources=st.lists(source_strategy(), min_size=1, max_size=50),
        confidence=st.floats(min_value=0.0, max_value=0.49)
    )
    @settings(max_examples=100)
    def test_proportional_penalty_calculation(self, sources, confidence):
        """
        Property 7: Proportional Penalty Calculation
        **Validates: Requirements 4.10**
        
        The penalty should be proportional to how far below 0.5 the confidence is.
        Lower confidence should result in higher penalty.
        """
        # Create agent results with specific confidence
        agent_results = [
            {
                'agent': 'news',
                'verdict': 'supporting',
                'confidence': confidence
            },
            {
                'agent': 'research',
                'verdict': 'supporting',
                'confidence': confidence
            }
        ]
        
        scorer = CredibilityScorer()
        evidence_summary = {'supporting': 0, 'contradicting': 0, 'neutral': 0}
        
        # Calculate score with penalty
        final_score, _, _ = scorer.calculate(agent_results, sources, evidence_summary)
        
        # Calculate raw score
        evidence_quality = scorer._calculate_evidence_quality(sources)
        agent_consensus = scorer._calculate_agent_consensus(agent_results)
        source_reliability = scorer._calculate_source_reliability(sources)
        
        raw_score = (
            (evidence_quality * 0.4) +
            (agent_consensus * 0.3) +
            (source_reliability * 0.3)
        )
        
        # Calculate expected penalty factor
        # penalty_factor = 1 - (0.5 - avg_confidence)
        expected_penalty_factor = 1 - (0.5 - confidence)
        expected_score = int(raw_score * expected_penalty_factor)
        
        # Property: The penalty should be proportional
        # Allow for rounding differences
        assert abs(final_score - expected_score) <= 1, (
            f"Penalty not proportional: final_score ({final_score}) != expected ({expected_score})\n"
            f"Confidence: {confidence}\n"
            f"Raw score: {raw_score}\n"
            f"Expected penalty factor: {expected_penalty_factor}"
        )
    
    @given(
        sources=st.lists(source_strategy(), min_size=1, max_size=50)
    )
    @settings(max_examples=100)
    def test_zero_confidence_applies_maximum_penalty(self, sources):
        """
        Property 7: Zero Confidence Maximum Penalty
        **Validates: Requirements 4.10**
        
        When confidence is 0, the maximum penalty (50%) should be applied.
        """
        # Create agent results with zero confidence
        agent_results = [
            {
                'agent': 'news',
                'verdict': 'supporting',
                'confidence': 0.0
            }
        ]
        
        scorer = CredibilityScorer()
        evidence_summary = {'supporting': 0, 'contradicting': 0, 'neutral': 0}
        
        # Calculate score with penalty
        final_score, _, _ = scorer.calculate(agent_results, sources, evidence_summary)
        
        # Calculate raw score
        evidence_quality = scorer._calculate_evidence_quality(sources)
        agent_consensus = scorer._calculate_agent_consensus(agent_results)
        source_reliability = scorer._calculate_source_reliability(sources)
        
        raw_score = (
            (evidence_quality * 0.4) +
            (agent_consensus * 0.3) +
            (source_reliability * 0.3)
        )
        
        # Property: Zero confidence should apply 50% penalty
        expected_score = int(raw_score * 0.5)
        
        # Allow for rounding differences
        assert abs(final_score - expected_score) <= 1, (
            f"Maximum penalty not applied: final_score ({final_score}) != expected ({expected_score})\n"
            f"Raw score: {raw_score}\n"
            f"Expected 50% penalty"
        )
    
    @given(
        sources=st.lists(source_strategy(), min_size=1, max_size=50),
        confidences=st.lists(
            st.floats(min_value=0.0, max_value=1.0),
            min_size=1,
            max_size=6
        )
    )
    @settings(max_examples=100)
    def test_penalty_based_on_average_confidence(self, sources, confidences):
        """
        Property 7: Penalty Based on Average Confidence
        **Validates: Requirements 4.10**
        
        The penalty should be based on the average confidence across all agents,
        not individual agent confidences.
        """
        # Create agent results with varying confidences
        agent_results = []
        agent_names = ['news', 'research', 'scientific', 'social_media', 'sentiment', 'scraper']
        
        for i, conf in enumerate(confidences):
            agent_results.append({
                'agent': agent_names[i % len(agent_names)],
                'verdict': 'supporting',
                'confidence': conf
            })
        
        scorer = CredibilityScorer()
        evidence_summary = {'supporting': 0, 'contradicting': 0, 'neutral': 0}
        
        # Calculate score
        final_score, _, _ = scorer.calculate(agent_results, sources, evidence_summary)
        
        # Calculate raw score
        evidence_quality = scorer._calculate_evidence_quality(sources)
        agent_consensus = scorer._calculate_agent_consensus(agent_results)
        source_reliability = scorer._calculate_source_reliability(sources)
        
        raw_score = (
            (evidence_quality * 0.4) +
            (agent_consensus * 0.3) +
            (source_reliability * 0.3)
        )
        
        # Calculate average confidence
        valid_confidences = [c for c in confidences if c > 0]
        avg_confidence = sum(valid_confidences) / len(valid_confidences) if valid_confidences else 0
        
        # Property: Penalty should be based on average confidence
        if avg_confidence < 0.5:
            # Penalty should be applied
            expected_penalty_factor = 1 - (0.5 - avg_confidence)
            expected_score = int(raw_score * expected_penalty_factor)
            
            assert abs(final_score - expected_score) <= 1, (
                f"Penalty not based on average: final_score ({final_score}) != expected ({expected_score})\n"
                f"Average confidence: {avg_confidence}\n"
                f"Individual confidences: {confidences}\n"
                f"Raw score: {raw_score}"
            )
        else:
            # No penalty should be applied
            assert abs(final_score - int(raw_score)) <= 1, (
                f"Unexpected penalty: final_score ({final_score}) != raw_score ({int(raw_score)})\n"
                f"Average confidence: {avg_confidence}\n"
                f"Individual confidences: {confidences}"
            )
    
    @given(
        sources=st.lists(source_strategy(), min_size=1, max_size=50),
        agent_results=st.lists(
            st.builds(
                dict,
                agent=st.sampled_from(['news', 'research', 'scientific']),
                verdict=st.sampled_from(['supporting', 'contradicting', 'neutral']),
                confidence=st.floats(min_value=0.0, max_value=0.49)
            ),
            min_size=1,
            max_size=6
        )
    )
    @settings(max_examples=100)
    def test_penalty_never_produces_negative_score(self, sources, agent_results):
        """
        Property 7: Penalty Never Produces Negative Score
        **Validates: Requirements 4.10**
        
        Even with maximum penalty, the score should never be negative.
        """
        scorer = CredibilityScorer()
        evidence_summary = {'supporting': 0, 'contradicting': 0, 'neutral': 0}
        
        # Calculate score with penalty
        final_score, _, _ = scorer.calculate(agent_results, sources, evidence_summary)
        
        # Property: Score should never be negative
        assert final_score >= 0, (
            f"Penalty produced negative score: {final_score}\n"
            f"Agent results: {agent_results}"
        )
    
    @given(
        sources=st.lists(source_strategy(), min_size=1, max_size=50),
        agent_results=st.lists(
            st.builds(
                dict,
                agent=st.sampled_from(['news', 'research', 'scientific']),
                verdict=st.sampled_from(['supporting', 'contradicting', 'neutral']),
                confidence=st.floats(min_value=0.0, max_value=0.49)
            ),
            min_size=1,
            max_size=6
        )
    )
    @settings(max_examples=100)
    def test_penalty_never_exceeds_fifty_percent(self, sources, agent_results):
        """
        Property 7: Penalty Never Exceeds 50%
        **Validates: Requirements 4.10**
        
        The penalty should reduce the score by up to 50%, never more.
        """
        scorer = CredibilityScorer()
        evidence_summary = {'supporting': 0, 'contradicting': 0, 'neutral': 0}
        
        # Calculate score with penalty
        final_score, _, _ = scorer.calculate(agent_results, sources, evidence_summary)
        
        # Calculate raw score
        evidence_quality = scorer._calculate_evidence_quality(sources)
        agent_consensus = scorer._calculate_agent_consensus(agent_results)
        source_reliability = scorer._calculate_source_reliability(sources)
        
        raw_score = (
            (evidence_quality * 0.4) +
            (agent_consensus * 0.3) +
            (source_reliability * 0.3)
        )
        
        # Property: Penalty should never exceed 50%
        min_allowed_score = raw_score * 0.5
        
        # Allow for rounding differences
        assert final_score >= (min_allowed_score - 1), (
            f"Penalty exceeded 50%: final_score ({final_score}) < min_allowed ({min_allowed_score})\n"
            f"Raw score: {raw_score}\n"
            f"Agent results: {agent_results}"
        )
