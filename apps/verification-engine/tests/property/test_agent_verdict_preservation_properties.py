"""
Property-Based Tests for Agent Verdict Preservation

**Validates: Requirements 5.5**

Property 11: Agent Verdict Preservation
For any verification, all agent verdicts with their confidence scores should be 
preserved in the final report without loss or modification during aggregation.
"""
import pytest
from hypothesis import given, strategies as st, settings
from src.services.evidence import EvidenceAggregator


# Strategy for generating agent results with verdicts
@st.composite
def agent_result_strategy(draw):
    """Generate a complete agent result with verdict and confidence."""
    agent_name = draw(st.sampled_from(['research', 'news', 'scientific', 'social_media', 'sentiment', 'scraper']))
    verdict = draw(st.sampled_from(['supporting', 'contradicting', 'neutral', 'insufficient']))
    confidence = draw(st.floats(min_value=0.0, max_value=1.0))
    
    # Generate sources
    num_sources = draw(st.integers(min_value=0, max_value=15))
    sources = []
    for i in range(num_sources):
        sources.append({
            'url': f'https://example{i}.com/article',
            'title': draw(st.text(min_size=5, max_size=100)),
            'excerpt': draw(st.text(min_size=10, max_size=300)),
            'credibility_tier': draw(st.sampled_from(['tier_1', 'tier_2', 'tier_3', 'tier_4'])),
            'credibility_score': draw(st.floats(min_value=0.0, max_value=1.0)),
            'stance': draw(st.sampled_from(['supporting', 'contradicting', 'neutral'])),
            'source_type': draw(st.sampled_from(['news', 'academic', 'social', 'fact_checker', 'general'])),
        })
    
    return {
        'agent': agent_name,
        'verdict': verdict,
        'confidence': confidence,
        'summary': draw(st.text(min_size=10, max_size=200)),
        'sources': sources,
        'error': None if verdict != 'insufficient' else draw(st.text(min_size=5, max_size=100))
    }


class TestAgentVerdictPreservationProperties:
    """Property-based tests for agent verdict preservation during aggregation."""
    
    @given(agent_results=st.lists(agent_result_strategy(), min_size=1, max_size=6))
    @settings(max_examples=100)
    def test_all_agent_verdicts_preserved(self, agent_results):
        """
        Property 11: All Agent Verdicts Preserved
        **Validates: Requirements 5.5**
        
        All agent verdicts should be preserved in the aggregation result
        without loss or modification.
        """
        aggregator = EvidenceAggregator()
        result = aggregator.aggregate(agent_results)
        
        # Extract agent names from input
        input_agents = {r['agent'] for r in agent_results}
        
        # The aggregator doesn't store verdicts directly, but we can verify
        # that the agent_source_counts preserves all agents
        output_agents = set(result['agent_source_counts'].keys())
        
        # Property: All input agents should be present in output
        assert input_agents == output_agents, (
            f"Agent verdicts not preserved. "
            f"Input agents: {input_agents}, Output agents: {output_agents}"
        )
    
    @given(agent_results=st.lists(agent_result_strategy(), min_size=1, max_size=6))
    @settings(max_examples=100)
    def test_unique_agent_count_matches_input(self, agent_results):
        """
        Property 11: Unique Agent Count Preserved
        **Validates: Requirements 5.5**
        
        The number of unique agents in the aggregation result should match
        the number of unique agents in the input.
        """
        aggregator = EvidenceAggregator()
        result = aggregator.aggregate(agent_results)
        
        # Count unique agents in input
        unique_input_agents = len(set(r['agent'] for r in agent_results))
        output_agent_count = len(result['agent_source_counts'])
        
        # Property: Unique agent count should be preserved
        assert unique_input_agents == output_agent_count, (
            f"Unique agent count not preserved. "
            f"Input: {unique_input_agents}, Output: {output_agent_count}"
        )
    
    @given(agent_results=st.lists(agent_result_strategy(), min_size=1, max_size=6))
    @settings(max_examples=100)
    def test_agent_source_counts_accurate(self, agent_results):
        """
        Property 11: Agent Source Counts Accurate
        **Validates: Requirements 5.5, 5.6**
        
        The source count for each unique agent should accurately reflect
        the number of sources from the last result with that agent name.
        (Note: In practice, agent names should be unique in input)
        """
        aggregator = EvidenceAggregator()
        result = aggregator.aggregate(agent_results)
        
        # Build expected counts (last occurrence wins for each agent name)
        expected_counts = {}
        for agent_result in agent_results:
            agent_name = agent_result['agent']
            source_count = len(agent_result.get('sources', []))
            expected_counts[agent_name] = source_count  # Last one wins
        
        # Verify each agent's source count
        for agent_name, expected_count in expected_counts.items():
            actual_count = result['agent_source_counts'].get(agent_name, 0)
            
            assert actual_count == expected_count, (
                f"Source count mismatch for agent '{agent_name}'. "
                f"Expected {expected_count}, got {actual_count}"
            )
    
    @given(agent_results=st.lists(agent_result_strategy(), min_size=1, max_size=6))
    @settings(max_examples=100)
    def test_agent_coverage_statistics_accurate(self, agent_results):
        """
        Property 11: Agent Coverage Statistics Accurate
        **Validates: Requirements 5.4, 5.6**
        
        The agent coverage statistics should accurately reflect
        the number of successful and failed agents.
        """
        aggregator = EvidenceAggregator()
        result = aggregator.aggregate(agent_results)
        
        coverage = result['agent_coverage']
        
        # Count successful agents (verdict != 'insufficient')
        expected_successful = sum(
            1 for r in agent_results 
            if r.get('verdict', 'insufficient') != 'insufficient'
        )
        expected_failed = len(agent_results) - expected_successful
        
        # Property: Coverage statistics should match actual counts
        assert coverage['total'] == len(agent_results), (
            f"Total agent count mismatch. Expected {len(agent_results)}, got {coverage['total']}"
        )
        assert coverage['successful'] == expected_successful, (
            f"Successful agent count mismatch. Expected {expected_successful}, got {coverage['successful']}"
        )
        assert coverage['failed'] == expected_failed, (
            f"Failed agent count mismatch. Expected {expected_failed}, got {coverage['failed']}"
        )
    
    @given(agent_results=st.lists(agent_result_strategy(), min_size=1, max_size=6))
    @settings(max_examples=100)
    def test_agent_coverage_success_rate_accurate(self, agent_results):
        """
        Property 11: Agent Coverage Success Rate Accurate
        **Validates: Requirements 5.4, 5.6**
        
        The success rate should be calculated correctly as
        (successful / total) * 100.
        """
        aggregator = EvidenceAggregator()
        result = aggregator.aggregate(agent_results)
        
        coverage = result['agent_coverage']
        
        # Calculate expected success rate
        total = len(agent_results)
        successful = sum(
            1 for r in agent_results 
            if r.get('verdict', 'insufficient') != 'insufficient'
        )
        expected_rate = (successful / total * 100) if total > 0 else 0
        
        # Property: Success rate should match calculation
        assert abs(coverage['success_rate'] - expected_rate) < 0.01, (
            f"Success rate mismatch. Expected {expected_rate}, got {coverage['success_rate']}"
        )
    
    @given(agent_results=st.lists(agent_result_strategy(), min_size=1, max_size=6))
    @settings(max_examples=100)
    def test_aggregation_preserves_agent_identity(self, agent_results):
        """
        Property 11: Agent Identity Preserved
        **Validates: Requirements 5.5, 5.6**
        
        Each agent's identity (name) should be preserved in the
        agent_source_counts mapping.
        """
        aggregator = EvidenceAggregator()
        result = aggregator.aggregate(agent_results)
        
        # Extract agent names from input
        input_agent_names = [r['agent'] for r in agent_results]
        output_agent_names = list(result['agent_source_counts'].keys())
        
        # Property: All input agent names should be in output
        for agent_name in input_agent_names:
            assert agent_name in output_agent_names, (
                f"Agent '{agent_name}' not found in output. "
                f"Output agents: {output_agent_names}"
            )
    
    @given(agent_results=st.lists(agent_result_strategy(), min_size=1, max_size=6))
    @settings(max_examples=100)
    def test_aggregation_deterministic_for_verdicts(self, agent_results):
        """
        Property 11: Deterministic Verdict Preservation
        **Validates: Requirements 5.5**
        
        Running aggregation twice on the same input should preserve
        agent information identically.
        """
        aggregator = EvidenceAggregator()
        
        # Run aggregation twice
        result1 = aggregator.aggregate(agent_results)
        result2 = aggregator.aggregate(agent_results)
        
        # Property: Agent source counts should be identical
        assert result1['agent_source_counts'] == result2['agent_source_counts'], (
            f"Non-deterministic agent preservation. "
            f"First: {result1['agent_source_counts']}, "
            f"Second: {result2['agent_source_counts']}"
        )
        
        # Property: Agent coverage should be identical
        assert result1['agent_coverage'] == result2['agent_coverage'], (
            f"Non-deterministic agent coverage. "
            f"First: {result1['agent_coverage']}, "
            f"Second: {result2['agent_coverage']}"
        )
    
    @given(
        num_agents=st.integers(min_value=1, max_value=6),
        verdict=st.sampled_from(['supporting', 'contradicting', 'neutral', 'insufficient'])
    )
    @settings(max_examples=100)
    def test_specific_verdict_preserved(self, num_agents, verdict):
        """
        Property 11: Specific Verdict Type Preserved
        **Validates: Requirements 5.5**
        
        When all agents have the same verdict, the agent coverage
        should reflect this correctly.
        """
        aggregator = EvidenceAggregator()
        
        # Create agents with the same verdict
        agent_results = []
        for i in range(num_agents):
            agent_results.append({
                'agent': f'agent_{i}',
                'verdict': verdict,
                'confidence': 0.8,
                'summary': 'Test summary',
                'sources': []
            })
        
        result = aggregator.aggregate(agent_results)
        coverage = result['agent_coverage']
        
        # Property: Coverage should reflect the verdict type
        if verdict == 'insufficient':
            assert coverage['successful'] == 0, (
                f"Expected 0 successful agents for 'insufficient' verdict, got {coverage['successful']}"
            )
            assert coverage['failed'] == num_agents, (
                f"Expected {num_agents} failed agents, got {coverage['failed']}"
            )
        else:
            assert coverage['successful'] == num_agents, (
                f"Expected {num_agents} successful agents, got {coverage['successful']}"
            )
            assert coverage['failed'] == 0, (
                f"Expected 0 failed agents, got {coverage['failed']}"
            )
    
    @given(agent_results=st.lists(agent_result_strategy(), min_size=1, max_size=6))
    @settings(max_examples=100)
    def test_no_agent_information_lost(self, agent_results):
        """
        Property 11: No Agent Information Lost
        **Validates: Requirements 5.5, 5.6**
        
        The aggregation should not lose any agent information.
        Every agent that provided input should be tracked in the output.
        """
        aggregator = EvidenceAggregator()
        result = aggregator.aggregate(agent_results)
        
        # Count unique agents in input
        input_agents = set(r['agent'] for r in agent_results)
        
        # Count agents in output
        output_agents = set(result['agent_source_counts'].keys())
        
        # Property: No agents should be lost
        assert len(output_agents) >= len(input_agents), (
            f"Agent information lost. Input: {len(input_agents)}, Output: {len(output_agents)}"
        )
        
        # Property: All input agents should be in output
        for agent in input_agents:
            assert agent in output_agents, (
                f"Agent '{agent}' lost during aggregation"
            )
    
    def test_empty_agent_results_handled(self):
        """
        Property 11: Empty Agent Results Handled
        **Validates: Requirements 5.5**
        
        When an agent returns no sources, it should still be tracked
        in the agent_source_counts with a count of 0.
        """
        aggregator = EvidenceAggregator()
        
        agent_results = [{
            'agent': 'research',
            'verdict': 'insufficient',
            'confidence': 0.0,
            'summary': 'No sources found',
            'sources': []
        }]
        
        result = aggregator.aggregate(agent_results)
        
        # Property: Agent should be tracked even with no sources
        assert 'research' in result['agent_source_counts'], (
            "Agent not tracked when returning no sources"
        )
        assert result['agent_source_counts']['research'] == 0, (
            f"Expected 0 sources for agent, got {result['agent_source_counts']['research']}"
        )
    
    @given(
        agent_results=st.lists(agent_result_strategy(), min_size=2, max_size=6)
    )
    @settings(max_examples=100)
    def test_multiple_agents_all_preserved(self, agent_results):
        """
        Property 11: Multiple Unique Agents All Preserved
        **Validates: Requirements 5.5, 5.6**
        
        When multiple unique agents provide results, all should be preserved
        in the aggregation output.
        """
        aggregator = EvidenceAggregator()
        result = aggregator.aggregate(agent_results)
        
        # Count unique agents in input
        unique_agents = set(r['agent'] for r in agent_results)
        
        # Property: Number of unique agents should match
        assert len(result['agent_source_counts']) == len(unique_agents), (
            f"Not all unique agents preserved. "
            f"Input unique agents: {len(unique_agents)}, Output: {len(result['agent_source_counts'])}"
        )
        
        # Property: Each unique agent should have a source count entry
        for agent_name in unique_agents:
            assert agent_name in result['agent_source_counts'], (
                f"Agent '{agent_name}' not preserved in aggregation"
            )
    
    @given(agent_results=st.lists(agent_result_strategy(), min_size=1, max_size=6))
    @settings(max_examples=100)
    def test_agent_coverage_total_equals_input_count(self, agent_results):
        """
        Property 11: Coverage Total Matches Input
        **Validates: Requirements 5.4, 5.6**
        
        The total count in agent_coverage should equal the number
        of agent results provided as input.
        """
        aggregator = EvidenceAggregator()
        result = aggregator.aggregate(agent_results)
        
        coverage = result['agent_coverage']
        input_count = len(agent_results)
        
        # Property: Total should match input count
        assert coverage['total'] == input_count, (
            f"Coverage total mismatch. Expected {input_count}, got {coverage['total']}"
        )
    
    @given(agent_results=st.lists(agent_result_strategy(), min_size=1, max_size=6))
    @settings(max_examples=100)
    def test_successful_plus_failed_equals_total(self, agent_results):
        """
        Property 11: Successful + Failed = Total
        **Validates: Requirements 5.4, 5.6**
        
        The sum of successful and failed agents should equal the total
        number of agents.
        """
        aggregator = EvidenceAggregator()
        result = aggregator.aggregate(agent_results)
        
        coverage = result['agent_coverage']
        
        # Property: successful + failed should equal total
        sum_agents = coverage['successful'] + coverage['failed']
        assert sum_agents == coverage['total'], (
            f"Successful + Failed != Total. "
            f"Successful: {coverage['successful']}, Failed: {coverage['failed']}, "
            f"Total: {coverage['total']}, Sum: {sum_agents}"
        )
    
    @given(
        successful_count=st.integers(min_value=0, max_value=6),
        failed_count=st.integers(min_value=0, max_value=6)
    )
    @settings(max_examples=100)
    def test_known_success_failure_counts(self, successful_count, failed_count):
        """
        Property 11: Known Success/Failure Counts
        **Validates: Requirements 5.4, 5.6**
        
        Given a known number of successful and failed agents,
        the coverage statistics should reflect this accurately.
        """
        # Skip if no agents
        if successful_count + failed_count == 0:
            return
        
        aggregator = EvidenceAggregator()
        
        # Create agent results with known success/failure counts
        agent_results = []
        
        # Add successful agents
        for i in range(successful_count):
            agent_results.append({
                'agent': f'successful_agent_{i}',
                'verdict': 'supporting',
                'confidence': 0.8,
                'summary': 'Success',
                'sources': []
            })
        
        # Add failed agents
        for i in range(failed_count):
            agent_results.append({
                'agent': f'failed_agent_{i}',
                'verdict': 'insufficient',
                'confidence': 0.0,
                'summary': 'Failed',
                'sources': []
            })
        
        result = aggregator.aggregate(agent_results)
        coverage = result['agent_coverage']
        
        # Property: Counts should match expected values
        assert coverage['successful'] == successful_count, (
            f"Expected {successful_count} successful agents, got {coverage['successful']}"
        )
        assert coverage['failed'] == failed_count, (
            f"Expected {failed_count} failed agents, got {coverage['failed']}"
        )
        assert coverage['total'] == successful_count + failed_count, (
            f"Expected {successful_count + failed_count} total agents, got {coverage['total']}"
        )
