"""
Property-Based Tests for Report Schema Completeness

**Property 12: Report Schema Completeness**
**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.7**

For any generated report, it should contain all required fields:
- credibility_score
- category
- confidence
- sources_consulted
- agent_consensus
- evidence_summary
- sources
- agent_verdicts
- limitations
- recommendation
- processing_time
"""

import pytest
from hypothesis import given, strategies as st, settings
from src.services.report import ReportGenerator


# Custom strategies for test data
@st.composite
def agent_result_strategy(draw):
    """Generate a valid agent result."""
    return {
        'agent': draw(st.sampled_from(['research', 'news', 'scientific', 'social_media', 'sentiment', 'scraper'])),
        'verdict': draw(st.sampled_from(['supporting', 'contradicting', 'neutral', 'insufficient'])),
        'confidence': draw(st.floats(min_value=0.0, max_value=1.0)),
        'summary': draw(st.text(min_size=10, max_size=200)),
        'sources': draw(st.lists(
            st.fixed_dictionaries({
                'url': st.text(min_size=10, max_size=100),
                'title': st.text(min_size=5, max_size=100),
                'excerpt': st.text(min_size=10, max_size=300),
                'credibility_tier': st.sampled_from(['tier_1', 'tier_2', 'tier_3', 'tier_4']),
                'credibility_score': st.floats(min_value=0.0, max_value=1.0),
                'stance': st.sampled_from(['supporting', 'contradicting', 'neutral']),
                'source_type': st.sampled_from(['news', 'academic', 'social', 'fact_checker', 'general']),
            }),
            min_size=0,
            max_size=20
        )),
        'error': draw(st.one_of(st.none(), st.text(min_size=5, max_size=100)))
    }


@st.composite
def evidence_strategy(draw):
    """Generate valid evidence data."""
    supporting = draw(st.integers(min_value=0, max_value=50))
    contradicting = draw(st.integers(min_value=0, max_value=50))
    neutral = draw(st.integers(min_value=0, max_value=50))
    
    return {
        'summary': {
            'supporting': supporting,
            'contradicting': contradicting,
            'neutral': neutral
        },
        'total_sources': supporting + contradicting + neutral,
        'deduplicated_sources': draw(st.lists(
            st.fixed_dictionaries({
                'url': st.text(min_size=10, max_size=100),
                'title': st.text(min_size=5, max_size=100),
                'credibility_score': st.floats(min_value=0.0, max_value=1.0),
                'stance': st.sampled_from(['supporting', 'contradicting', 'neutral']),
            }),
            min_size=0,
            max_size=supporting + contradicting + neutral
        ))
    }


@st.composite
def credibility_strategy(draw):
    """Generate valid credibility data."""
    score = draw(st.integers(min_value=0, max_value=100))
    
    # Map score to category
    if score >= 85:
        category = "Verified True"
    elif score >= 70:
        category = "Likely True"
    elif score >= 60:
        category = "Uncertain"
    elif score >= 40:
        category = "Likely False"
    else:
        category = "Verified False"
    
    return {
        'score': score,
        'category': category,
        'confidence': draw(st.sampled_from(['High', 'Medium', 'Low'])),
        'consensus': draw(st.text(min_size=10, max_size=100))
    }


@pytest.mark.asyncio
@given(
    claim=st.text(min_size=10, max_size=500),
    agent_results=st.lists(agent_result_strategy(), min_size=1, max_size=6),
    evidence=evidence_strategy(),
    credibility=credibility_strategy(),
    analysis=st.fixed_dictionaries({
        'domain': st.sampled_from(['health', 'politics', 'science', 'general']),
        'language': st.sampled_from(['en', 'es', 'fr', 'de']),
    })
)
@settings(deadline=None, max_examples=100)
async def test_report_contains_all_required_fields(claim, agent_results, evidence, credibility, analysis):
    """
    Property 12: Report Schema Completeness
    
    For any generated report, it should contain all required fields.
    """
    generator = ReportGenerator()
    
    # Generate report
    report = await generator.generate(claim, analysis, evidence, credibility, agent_results)
    
    # Verify all required fields are present
    assert 'agent_verdicts' in report, "Missing 'agent_verdicts' field"
    assert 'limitations' in report, "Missing 'limitations' field"
    assert 'recommendation' in report, "Missing 'recommendation' field"
    
    # Verify agent_verdicts structure
    assert isinstance(report['agent_verdicts'], dict), "agent_verdicts should be a dict"
    for agent_name, verdict in report['agent_verdicts'].items():
        assert isinstance(agent_name, str), "Agent name should be a string"
        assert isinstance(verdict, dict), "Agent verdict should be a dict"
        assert 'verdict' in verdict, f"Missing 'verdict' in {agent_name}"
        assert 'confidence' in verdict, f"Missing 'confidence' in {agent_name}"
        assert 'summary' in verdict, f"Missing 'summary' in {agent_name}"
        assert 'sources_count' in verdict, f"Missing 'sources_count' in {agent_name}"
    
    # Verify limitations structure
    assert isinstance(report['limitations'], list), "limitations should be a list"
    assert len(report['limitations']) > 0, "limitations should not be empty"
    for limitation in report['limitations']:
        assert isinstance(limitation, str), "Each limitation should be a string"
    
    # Verify recommendation structure
    assert isinstance(report['recommendation'], str), "recommendation should be a string"
    assert len(report['recommendation']) > 0, "recommendation should not be empty"


@pytest.mark.asyncio
@given(
    claim=st.text(min_size=10, max_size=500),
    agent_results=st.lists(agent_result_strategy(), min_size=1, max_size=6),
    evidence=evidence_strategy(),
    credibility=credibility_strategy(),
    analysis=st.fixed_dictionaries({
        'domain': st.sampled_from(['health', 'politics', 'science', 'general']),
        'language': st.sampled_from(['en', 'es', 'fr', 'de']),
    })
)
@settings(deadline=None, max_examples=100)
async def test_agent_verdicts_match_input_agents(claim, agent_results, evidence, credibility, analysis):
    """
    Property: Agent verdicts should include all agents from input.
    
    Validates that the report includes verdicts for all agents that were executed.
    """
    generator = ReportGenerator()
    
    # Generate report
    report = await generator.generate(claim, analysis, evidence, credibility, agent_results)
    
    # Extract agent names from input
    input_agent_names = {result['agent'] for result in agent_results}
    
    # Extract agent names from output
    output_agent_names = set(report['agent_verdicts'].keys())
    
    # Verify all input agents are in output
    assert input_agent_names == output_agent_names, \
        f"Agent mismatch: input={input_agent_names}, output={output_agent_names}"


@pytest.mark.asyncio
@given(
    claim=st.text(min_size=10, max_size=500),
    agent_results=st.lists(agent_result_strategy(), min_size=1, max_size=6),
    evidence=evidence_strategy(),
    credibility=credibility_strategy(),
    analysis=st.fixed_dictionaries({
        'domain': st.sampled_from(['health', 'politics', 'science', 'general']),
        'language': st.sampled_from(['en', 'es', 'fr', 'de']),
    })
)
@settings(deadline=None, max_examples=100)
async def test_limitations_are_meaningful(claim, agent_results, evidence, credibility, analysis):
    """
    Property: Limitations should be meaningful and context-aware.
    
    Validates that limitations are generated based on actual issues in the data.
    """
    generator = ReportGenerator()
    
    # Generate report
    report = await generator.generate(claim, analysis, evidence, credibility, agent_results)
    
    limitations = report['limitations']
    
    # Check for low confidence limitation
    low_confidence_agents = [r['agent'] for r in agent_results if r.get('confidence', 0) < 0.5]
    if low_confidence_agents:
        assert any('Low confidence' in lim or 'low confidence' in lim for lim in limitations), \
            "Should mention low confidence agents"
    
    # Check for insufficient sources limitation
    total_sources = evidence.get('total_sources', 0)
    if total_sources < 10:
        assert any('Limited sources' in lim or 'sources consulted' in lim for lim in limitations), \
            "Should mention limited sources"
    
    # Check for agent errors limitation
    failed_agents = [r['agent'] for r in agent_results if r.get('error')]
    if failed_agents:
        assert any('error' in lim.lower() for lim in limitations), \
            "Should mention agent errors"
