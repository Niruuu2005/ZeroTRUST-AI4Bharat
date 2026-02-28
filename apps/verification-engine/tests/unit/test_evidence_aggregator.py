"""
Unit tests for EvidenceAggregator
"""
import pytest
from src.services.evidence import EvidenceAggregator


class TestURLNormalization:
    """Test URL normalization functionality."""
    
    def test_normalize_url_removes_query_params(self):
        """URL normalization should remove query parameters."""
        aggregator = EvidenceAggregator()
        url = "https://example.com/article?utm_source=twitter&id=123"
        normalized = aggregator.normalize_url(url)
        assert normalized == "https://example.com/article"
    
    def test_normalize_url_removes_fragment(self):
        """URL normalization should remove fragments."""
        aggregator = EvidenceAggregator()
        url = "https://example.com/article#section-2"
        normalized = aggregator.normalize_url(url)
        assert normalized == "https://example.com/article"
    
    def test_normalize_url_removes_trailing_slash(self):
        """URL normalization should remove trailing slashes."""
        aggregator = EvidenceAggregator()
        url = "https://example.com/article/"
        normalized = aggregator.normalize_url(url)
        assert normalized == "https://example.com/article"
    
    def test_normalize_url_lowercases_domain(self):
        """URL normalization should lowercase the domain."""
        aggregator = EvidenceAggregator()
        url = "https://EXAMPLE.COM/Article"
        normalized = aggregator.normalize_url(url)
        assert normalized == "https://example.com/Article"
    
    def test_normalize_url_handles_all_transformations(self):
        """URL normalization should handle all transformations together."""
        aggregator = EvidenceAggregator()
        url = "https://EXAMPLE.COM/Article/?utm_source=twitter#section"
        normalized = aggregator.normalize_url(url)
        assert normalized == "https://example.com/Article"
    
    def test_normalize_url_handles_invalid_url(self):
        """URL normalization should handle invalid URLs gracefully."""
        aggregator = EvidenceAggregator()
        url = "not-a-valid-url"
        normalized = aggregator.normalize_url(url)
        # Should return original URL if parsing fails
        assert normalized == url


class TestSourceDeduplication:
    """Test source deduplication functionality."""
    
    def test_deduplicate_removes_exact_duplicates(self):
        """Deduplication should remove exact duplicate URLs."""
        aggregator = EvidenceAggregator()
        sources = [
            {'url': 'https://example.com/article', 'credibility_score': 0.8},
            {'url': 'https://example.com/article', 'credibility_score': 0.7},
        ]
        
        agent_results = [{'agent': 'test', 'sources': sources}]
        result = aggregator.aggregate(agent_results)
        
        assert len(result['sources']) == 1
        # Should keep the one with higher credibility
        assert result['sources'][0]['credibility_score'] == 0.8
    
    def test_deduplicate_normalizes_urls(self):
        """Deduplication should normalize URLs before comparing."""
        aggregator = EvidenceAggregator()
        sources = [
            {'url': 'https://example.com/article', 'credibility_score': 0.8, 'stance': 'supporting'},
            {'url': 'https://example.com/article?utm_source=twitter', 'credibility_score': 0.7, 'stance': 'supporting'},
            {'url': 'https://EXAMPLE.COM/article/', 'credibility_score': 0.9, 'stance': 'supporting'},
        ]
        
        agent_results = [{'agent': 'test', 'sources': sources}]
        result = aggregator.aggregate(agent_results)
        
        assert len(result['sources']) == 1
        # Should keep the one with highest credibility (0.9)
        assert result['sources'][0]['credibility_score'] == 0.9
    
    def test_deduplicate_keeps_different_urls(self):
        """Deduplication should keep sources with different URLs."""
        aggregator = EvidenceAggregator()
        sources = [
            {'url': 'https://example.com/article1', 'credibility_score': 0.8, 'stance': 'supporting'},
            {'url': 'https://example.com/article2', 'credibility_score': 0.7, 'stance': 'supporting'},
            {'url': 'https://different.com/article', 'credibility_score': 0.9, 'stance': 'supporting'},
        ]
        
        agent_results = [{'agent': 'test', 'sources': sources}]
        result = aggregator.aggregate(agent_results)
        
        assert len(result['sources']) == 3
    
    def test_deduplicate_handles_empty_url(self):
        """Deduplication should skip sources with empty URLs."""
        aggregator = EvidenceAggregator()
        sources = [
            {'url': '', 'credibility_score': 0.8, 'stance': 'supporting'},
            {'url': 'https://example.com/article', 'credibility_score': 0.7, 'stance': 'supporting'},
        ]
        
        agent_results = [{'agent': 'test', 'sources': sources}]
        result = aggregator.aggregate(agent_results)
        
        assert len(result['sources']) == 1
        assert result['sources'][0]['url'] == 'https://example.com/article'


class TestEvidenceSummary:
    """Test evidence summary calculation."""
    
    def test_summary_counts_stances_correctly(self):
        """Summary should correctly count sources by stance."""
        aggregator = EvidenceAggregator()
        sources = [
            {'url': 'https://example.com/1', 'stance': 'supporting', 'credibility_score': 0.8},
            {'url': 'https://example.com/2', 'stance': 'supporting', 'credibility_score': 0.7},
            {'url': 'https://example.com/3', 'stance': 'contradicting', 'credibility_score': 0.6},
            {'url': 'https://example.com/4', 'stance': 'neutral', 'credibility_score': 0.5},
        ]
        
        agent_results = [{'agent': 'test', 'sources': sources}]
        result = aggregator.aggregate(agent_results)
        
        assert result['summary']['supporting'] == 2
        assert result['summary']['contradicting'] == 1
        assert result['summary']['neutral'] == 1
    
    def test_summary_handles_missing_stance(self):
        """Summary should default to neutral for missing stance."""
        aggregator = EvidenceAggregator()
        sources = [
            {'url': 'https://example.com/1', 'credibility_score': 0.8},
            {'url': 'https://example.com/2', 'stance': 'supporting', 'credibility_score': 0.7},
        ]
        
        agent_results = [{'agent': 'test', 'sources': sources}]
        result = aggregator.aggregate(agent_results)
        
        assert result['summary']['neutral'] == 1
        assert result['summary']['supporting'] == 1
    
    def test_summary_total_equals_sum_of_stances(self):
        """Total sources should equal sum of all stance counts."""
        aggregator = EvidenceAggregator()
        sources = [
            {'url': f'https://example.com/{i}', 'stance': stance, 'credibility_score': 0.5}
            for i, stance in enumerate(['supporting'] * 5 + ['contradicting'] * 3 + ['neutral'] * 2)
        ]
        
        agent_results = [{'agent': 'test', 'sources': sources}]
        result = aggregator.aggregate(agent_results)
        
        total = result['summary']['supporting'] + result['summary']['contradicting'] + result['summary']['neutral']
        assert result['total_sources'] == total


class TestSourceSorting:
    """Test source sorting by credibility."""
    
    def test_sources_sorted_by_credibility_descending(self):
        """Sources should be sorted by credibility score in descending order."""
        aggregator = EvidenceAggregator()
        sources = [
            {'url': 'https://example.com/1', 'credibility_score': 0.5, 'stance': 'supporting'},
            {'url': 'https://example.com/2', 'credibility_score': 0.9, 'stance': 'supporting'},
            {'url': 'https://example.com/3', 'credibility_score': 0.7, 'stance': 'supporting'},
        ]
        
        agent_results = [{'agent': 'test', 'sources': sources}]
        result = aggregator.aggregate(agent_results)
        
        scores = [s['credibility_score'] for s in result['sources']]
        assert scores == [0.9, 0.7, 0.5]
    
    def test_sources_sorted_handles_missing_score(self):
        """Sorting should handle sources with missing credibility scores."""
        aggregator = EvidenceAggregator()
        sources = [
            {'url': 'https://example.com/1', 'credibility_score': 0.5, 'stance': 'supporting'},
            {'url': 'https://example.com/2', 'stance': 'supporting'},  # Missing score
            {'url': 'https://example.com/3', 'credibility_score': 0.7, 'stance': 'supporting'},
        ]
        
        agent_results = [{'agent': 'test', 'sources': sources}]
        result = aggregator.aggregate(agent_results)
        
        # Should not crash, missing score treated as 0
        assert len(result['sources']) == 3


class TestAgentCoverage:
    """Test agent coverage statistics."""
    
    def test_agent_coverage_calculates_correctly(self):
        """Agent coverage should calculate total, successful, and failed agents."""
        aggregator = EvidenceAggregator()
        agent_results = [
            {'agent': 'news', 'verdict': 'supporting', 'sources': []},
            {'agent': 'research', 'verdict': 'contradicting', 'sources': []},
            {'agent': 'scientific', 'verdict': 'insufficient', 'sources': []},
            {'agent': 'social', 'verdict': 'neutral', 'sources': []},
        ]
        
        result = aggregator.aggregate(agent_results)
        coverage = result['agent_coverage']
        
        assert coverage['total'] == 4
        assert coverage['successful'] == 3  # All except 'insufficient'
        assert coverage['failed'] == 1
        assert coverage['success_rate'] == 75.0
    
    def test_agent_coverage_handles_all_successful(self):
        """Agent coverage should handle all agents being successful."""
        aggregator = EvidenceAggregator()
        agent_results = [
            {'agent': 'news', 'verdict': 'supporting', 'sources': []},
            {'agent': 'research', 'verdict': 'contradicting', 'sources': []},
        ]
        
        result = aggregator.aggregate(agent_results)
        coverage = result['agent_coverage']
        
        assert coverage['total'] == 2
        assert coverage['successful'] == 2
        assert coverage['failed'] == 0
        assert coverage['success_rate'] == 100.0
    
    def test_agent_coverage_handles_all_failed(self):
        """Agent coverage should handle all agents failing."""
        aggregator = EvidenceAggregator()
        agent_results = [
            {'agent': 'news', 'verdict': 'insufficient', 'sources': []},
            {'agent': 'research', 'verdict': 'insufficient', 'sources': []},
        ]
        
        result = aggregator.aggregate(agent_results)
        coverage = result['agent_coverage']
        
        assert coverage['total'] == 2
        assert coverage['successful'] == 0
        assert coverage['failed'] == 2
        assert coverage['success_rate'] == 0.0
    
    def test_agent_coverage_handles_empty_results(self):
        """Agent coverage should handle empty agent results."""
        aggregator = EvidenceAggregator()
        agent_results = []
        
        result = aggregator.aggregate(agent_results)
        coverage = result['agent_coverage']
        
        assert coverage['total'] == 0
        assert coverage['successful'] == 0
        assert coverage['failed'] == 0
        assert coverage['success_rate'] == 0.0


class TestIntegration:
    """Integration tests for complete aggregation flow."""
    
    def test_aggregate_complete_flow(self):
        """Test complete aggregation with multiple agents and sources."""
        aggregator = EvidenceAggregator()
        agent_results = [
            {
                'agent': 'news',
                'verdict': 'supporting',
                'sources': [
                    {'url': 'https://news.com/1', 'stance': 'supporting', 'credibility_score': 0.9},
                    {'url': 'https://news.com/2', 'stance': 'supporting', 'credibility_score': 0.8},
                ]
            },
            {
                'agent': 'research',
                'verdict': 'contradicting',
                'sources': [
                    {'url': 'https://research.com/1', 'stance': 'contradicting', 'credibility_score': 0.7},
                    {'url': 'https://news.com/1?ref=twitter', 'stance': 'supporting', 'credibility_score': 0.85},  # Duplicate
                ]
            },
            {
                'agent': 'scientific',
                'verdict': 'insufficient',
                'sources': []
            }
        ]
        
        result = aggregator.aggregate(agent_results)
        
        # Should deduplicate the news.com/1 URL
        assert result['total_sources'] == 3
        
        # Should count stances correctly
        assert result['summary']['supporting'] == 2
        assert result['summary']['contradicting'] == 1
        
        # Should sort by credibility
        scores = [s['credibility_score'] for s in result['sources']]
        assert scores == sorted(scores, reverse=True)
        
        # Should calculate agent coverage
        assert result['agent_coverage']['total'] == 3
        assert result['agent_coverage']['successful'] == 2
        assert result['agent_coverage']['failed'] == 1
