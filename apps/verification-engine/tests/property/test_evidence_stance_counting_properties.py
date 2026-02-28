"""
Property-Based Tests for Evidence Stance Counting

**Validates: Requirements 5.2**

Property 9: Evidence Stance Counting
For any deduplicated source list, the evidence summary should correctly count sources 
by stance (supporting/contradicting/neutral), with the sum of all stance counts 
equaling the total number of sources.
"""
import pytest
from hypothesis import given, strategies as st, settings
from src.services.evidence import EvidenceAggregator


# Strategy for generating sources with valid stances
@st.composite
def source_strategy(draw):
    """Generate a source with valid stance."""
    stance = draw(st.sampled_from(['supporting', 'contradicting', 'neutral']))
    url = draw(st.text(min_size=10, max_size=100))
    
    return {
        'url': f'https://example.com/{url}',
        'title': draw(st.text(min_size=5, max_size=100)),
        'excerpt': draw(st.text(min_size=10, max_size=300)),
        'credibility_tier': draw(st.sampled_from(['tier_1', 'tier_2', 'tier_3', 'tier_4'])),
        'credibility_score': draw(st.floats(min_value=0.0, max_value=1.0)),
        'stance': stance,
        'source_type': draw(st.sampled_from(['news', 'academic', 'social', 'fact_checker', 'general'])),
    }


# Strategy for generating agent results with sources
@st.composite
def agent_result_strategy(draw):
    """Generate an agent result with sources."""
    agent_name = draw(st.sampled_from(['research', 'news', 'scientific', 'social_media', 'sentiment', 'scraper']))
    sources = draw(st.lists(source_strategy(), min_size=0, max_size=20))
    
    return {
        'agent': agent_name,
        'verdict': draw(st.sampled_from(['supporting', 'contradicting', 'neutral', 'insufficient'])),
        'confidence': draw(st.floats(min_value=0.0, max_value=1.0)),
        'summary': draw(st.text(min_size=10, max_size=200)),
        'sources': sources,
    }


@given(agent_results=st.lists(agent_result_strategy(), min_size=1, max_size=6))
def test_stance_count_sum_equals_total_sources(agent_results):
    """
    Property 9: Evidence Stance Counting
    
    The sum of all stance counts (supporting + contradicting + neutral) 
    should equal the total number of deduplicated sources.
    """
    aggregator = EvidenceAggregator()
    result = aggregator.aggregate(agent_results)
    
    stance_counts = result['summary']
    total_sources = result['total_sources']
    
    # Sum of stance counts should equal total sources
    stance_sum = stance_counts['supporting'] + stance_counts['contradicting'] + stance_counts['neutral']
    
    assert stance_sum == total_sources, (
        f"Stance count sum ({stance_sum}) does not equal total sources ({total_sources}). "
        f"Counts: {stance_counts}"
    )


@given(agent_results=st.lists(agent_result_strategy(), min_size=1, max_size=6))
def test_stance_counts_are_non_negative(agent_results):
    """
    Property: All stance counts should be non-negative integers.
    """
    aggregator = EvidenceAggregator()
    result = aggregator.aggregate(agent_results)
    
    stance_counts = result['summary']
    
    assert stance_counts['supporting'] >= 0, "Supporting count should be non-negative"
    assert stance_counts['contradicting'] >= 0, "Contradicting count should be non-negative"
    assert stance_counts['neutral'] >= 0, "Neutral count should be non-negative"


@given(agent_results=st.lists(agent_result_strategy(), min_size=1, max_size=6))
def test_stance_counts_match_actual_sources(agent_results):
    """
    Property: Stance counts should match the actual count of sources with each stance.
    """
    aggregator = EvidenceAggregator()
    result = aggregator.aggregate(agent_results)
    
    stance_counts = result['summary']
    sources = result['sources']
    
    # Manually count stances from deduplicated sources
    actual_supporting = sum(1 for s in sources if s.get('stance') == 'supporting')
    actual_contradicting = sum(1 for s in sources if s.get('stance') == 'contradicting')
    actual_neutral = sum(1 for s in sources if s.get('stance') == 'neutral')
    
    assert stance_counts['supporting'] == actual_supporting, (
        f"Supporting count mismatch: expected {actual_supporting}, got {stance_counts['supporting']}"
    )
    assert stance_counts['contradicting'] == actual_contradicting, (
        f"Contradicting count mismatch: expected {actual_contradicting}, got {stance_counts['contradicting']}"
    )
    assert stance_counts['neutral'] == actual_neutral, (
        f"Neutral count mismatch: expected {actual_neutral}, got {stance_counts['neutral']}"
    )


@given(agent_results=st.lists(agent_result_strategy(), min_size=1, max_size=6))
def test_stance_counting_after_deduplication(agent_results):
    """
    Property: Stance counts should be calculated AFTER deduplication, not before.
    
    This ensures that duplicate sources don't inflate stance counts.
    """
    aggregator = EvidenceAggregator()
    result = aggregator.aggregate(agent_results)
    
    # Count total sources before deduplication
    total_before_dedup = sum(len(r.get('sources', [])) for r in agent_results)
    
    # Count after deduplication
    total_after_dedup = result['total_sources']
    stance_sum = (
        result['summary']['supporting'] + 
        result['summary']['contradicting'] + 
        result['summary']['neutral']
    )
    
    # Stance counts should match deduplicated count, not original count
    assert stance_sum == total_after_dedup, (
        f"Stance counts should be based on deduplicated sources. "
        f"Before dedup: {total_before_dedup}, After dedup: {total_after_dedup}, "
        f"Stance sum: {stance_sum}"
    )


@given(
    agent_results=st.lists(agent_result_strategy(), min_size=1, max_size=6),
    stance_filter=st.sampled_from(['supporting', 'contradicting', 'neutral'])
)
def test_stance_count_consistency(agent_results, stance_filter):
    """
    Property: The count for a specific stance should match the number of sources with that stance.
    """
    aggregator = EvidenceAggregator()
    result = aggregator.aggregate(agent_results)
    
    stance_counts = result['summary']
    sources = result['sources']
    
    # Count sources with the filtered stance
    filtered_count = sum(1 for s in sources if s.get('stance') == stance_filter)
    
    assert stance_counts[stance_filter] == filtered_count, (
        f"Count for stance '{stance_filter}' does not match actual sources. "
        f"Expected {filtered_count}, got {stance_counts[stance_filter]}"
    )
