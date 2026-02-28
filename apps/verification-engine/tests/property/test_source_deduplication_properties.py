"""
Property-based tests for source deduplication.

Property 8: Source Deduplication by URL
**Validates: Requirements 5.1**

Property: For any list of sources from multiple agents, the evidence aggregator should 
deduplicate sources by normalized URL (ignoring query params, fragments, and case), 
ensuring each unique source appears exactly once in the final list.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from src.services.evidence import EvidenceAggregator


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
def url_with_variations_strategy(draw):
    """Generate a base URL with various normalized forms."""
    # Generate base URL components
    scheme = draw(st.sampled_from(['http', 'https']))
    domain = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=5, max_size=15))
    tld = draw(st.sampled_from(['com', 'org', 'net', 'edu']))
    path = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz/', min_size=0, max_size=20))
    
    base_url = f"{scheme}://{domain}.{tld}/{path}"
    
    # Generate variations
    variations = []
    
    # Original
    variations.append(base_url)
    
    # With trailing slash
    if not base_url.endswith('/'):
        variations.append(base_url + '/')
    
    # With query params
    variations.append(base_url + '?param=value')
    variations.append(base_url + '?foo=bar&baz=qux')
    
    # With fragment
    variations.append(base_url + '#section')
    variations.append(base_url + '#top')
    
    # With both query and fragment
    variations.append(base_url + '?param=value#section')
    
    # Case variations (domain)
    variations.append(base_url.replace(domain, domain.upper()))
    variations.append(base_url.replace(domain, domain.capitalize()))
    
    return base_url, variations


@st.composite
def agent_result_with_sources_strategy(draw):
    """Generate an agent result with sources."""
    num_sources = draw(st.integers(min_value=0, max_value=10))
    sources = [draw(source_strategy()) for _ in range(num_sources)]
    
    return {
        'agent': draw(st.sampled_from(['news', 'research', 'scientific', 'social_media', 'sentiment', 'scraper'])),
        'verdict': draw(st.sampled_from(['supporting', 'contradicting', 'neutral', 'insufficient'])),
        'confidence': draw(st.floats(min_value=0.0, max_value=1.0)),
        'sources': sources
    }


class TestSourceDeduplicationProperties:
    """Property-based tests for source deduplication."""
    
    @given(
        agent_results=st.lists(agent_result_with_sources_strategy(), min_size=1, max_size=6)
    )
    @settings(max_examples=100)
    def test_deduplicated_sources_have_unique_normalized_urls(self, agent_results):
        """
        Property 8: Unique Normalized URLs
        **Validates: Requirements 5.1**
        
        After deduplication, all sources should have unique normalized URLs.
        """
        aggregator = EvidenceAggregator()
        result = aggregator.aggregate(agent_results)
        deduplicated_sources = result['sources']
        
        # Normalize all URLs
        normalized_urls = [
            aggregator.normalize_url(source['url']) 
            for source in deduplicated_sources
        ]
        
        # Property: All normalized URLs should be unique
        assert len(normalized_urls) == len(set(normalized_urls)), (
            f"Found duplicate normalized URLs after deduplication:\n"
            f"Total sources: {len(deduplicated_sources)}\n"
            f"Unique normalized URLs: {len(set(normalized_urls))}\n"
            f"Duplicates: {[url for url in normalized_urls if normalized_urls.count(url) > 1]}"
        )
    
    @given(
        base_url_and_variations=url_with_variations_strategy(),
        credibility_scores=st.lists(
            st.floats(min_value=0.0, max_value=1.0),
            min_size=2,
            max_size=10
        )
    )
    @settings(max_examples=100)
    def test_url_variations_deduplicated_to_single_source(self, base_url_and_variations, credibility_scores):
        """
        Property 8: URL Variations Deduplicated
        **Validates: Requirements 5.1**
        
        Different variations of the same URL (with query params, fragments, 
        trailing slashes, case differences) should be deduplicated to a single source.
        """
        base_url, variations = base_url_and_variations
        aggregator = EvidenceAggregator()
        
        # Create sources with URL variations
        agent_results = []
        for i, (url_variation, score) in enumerate(zip(variations[:len(credibility_scores)], credibility_scores)):
            agent_results.append({
                'agent': f'agent_{i % 6}',
                'verdict': 'supporting',
                'confidence': 0.8,
                'sources': [{
                    'url': url_variation,
                    'title': f'Source {i}',
                    'credibility_tier': 'tier_1',
                    'credibility_score': score,
                    'stance': 'supporting'
                }]
            })
        
        result = aggregator.aggregate(agent_results)
        deduplicated_sources = result['sources']
        
        # Property: Should have exactly 1 source after deduplication
        assert len(deduplicated_sources) == 1, (
            f"Expected 1 source after deduplication, got {len(deduplicated_sources)}\n"
            f"Base URL: {base_url}\n"
            f"Variations: {variations[:len(credibility_scores)]}\n"
            f"Deduplicated URLs: {[s['url'] for s in deduplicated_sources]}"
        )
    
    @given(
        base_url_and_variations=url_with_variations_strategy(),
        credibility_scores=st.lists(
            st.floats(min_value=0.0, max_value=1.0),
            min_size=2,
            max_size=10
        )
    )
    @settings(max_examples=100)
    def test_highest_credibility_source_kept_after_deduplication(self, base_url_and_variations, credibility_scores):
        """
        Property 8: Highest Credibility Source Kept
        **Validates: Requirements 5.1**
        
        When deduplicating sources with the same normalized URL, the source 
        with the highest credibility score should be kept.
        """
        base_url, variations = base_url_and_variations
        aggregator = EvidenceAggregator()
        
        # Ensure we have at least as many variations as scores
        # If we have more scores than variations, truncate scores
        num_sources = min(len(variations), len(credibility_scores))
        used_variations = variations[:num_sources]
        used_scores = credibility_scores[:num_sources]
        
        # Create sources with URL variations and different credibility scores
        agent_results = []
        max_score = max(used_scores)
        
        for i, (url_variation, score) in enumerate(zip(used_variations, used_scores)):
            agent_results.append({
                'agent': f'agent_{i % 6}',
                'verdict': 'supporting',
                'confidence': 0.8,
                'sources': [{
                    'url': url_variation,
                    'title': f'Source {i}',
                    'credibility_tier': 'tier_1',
                    'credibility_score': score,
                    'stance': 'supporting'
                }]
            })
        
        result = aggregator.aggregate(agent_results)
        deduplicated_sources = result['sources']
        
        # Property: Should have exactly 1 source after deduplication
        assert len(deduplicated_sources) == 1, "Should have exactly 1 source"
        kept_source = deduplicated_sources[0]
        
        assert kept_source['credibility_score'] == max_score, (
            f"Expected source with highest credibility score {max_score}, got {kept_source['credibility_score']}\n"
            f"Used scores: {used_scores}\n"
            f"Kept source: {kept_source}"
        )
    
    @given(
        agent_results=st.lists(agent_result_with_sources_strategy(), min_size=1, max_size=6)
    )
    @settings(max_examples=100)
    def test_deduplication_count_less_or_equal_to_total(self, agent_results):
        """
        Property 8: Deduplication Reduces or Maintains Count
        **Validates: Requirements 5.1**
        
        The number of deduplicated sources should be less than or equal to 
        the total number of sources from all agents.
        """
        aggregator = EvidenceAggregator()
        
        # Count total sources before deduplication
        total_sources = sum(len(result.get('sources', [])) for result in agent_results)
        
        result = aggregator.aggregate(agent_results)
        deduplicated_count = len(result['sources'])
        
        # Property: Deduplicated count should not exceed total
        assert deduplicated_count <= total_sources, (
            f"Deduplicated count {deduplicated_count} exceeds total sources {total_sources}"
        )
    
    @given(
        num_agents=st.integers(min_value=1, max_value=6),
        num_unique_urls=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=100)
    def test_known_unique_urls_preserved(self, num_agents, num_unique_urls):
        """
        Property 8: Known Unique URLs Preserved
        **Validates: Requirements 5.1**
        
        When sources have genuinely different URLs (not just variations), 
        all unique sources should be preserved after deduplication.
        """
        aggregator = EvidenceAggregator()
        
        # Create sources with genuinely unique URLs
        agent_results = []
        for agent_idx in range(num_agents):
            sources = []
            for url_idx in range(num_unique_urls):
                sources.append({
                    'url': f'https://example{url_idx}.com/article',
                    'title': f'Article {url_idx}',
                    'credibility_tier': 'tier_1',
                    'credibility_score': 0.8,
                    'stance': 'supporting'
                })
            
            agent_results.append({
                'agent': f'agent_{agent_idx}',
                'verdict': 'supporting',
                'confidence': 0.8,
                'sources': sources
            })
        
        result = aggregator.aggregate(agent_results)
        deduplicated_sources = result['sources']
        
        # Property: Should have exactly num_unique_urls sources
        # (each agent has the same URLs, so deduplication should reduce to unique count)
        assert len(deduplicated_sources) == num_unique_urls, (
            f"Expected {num_unique_urls} unique sources, got {len(deduplicated_sources)}\n"
            f"Agents: {num_agents}\n"
            f"Sources per agent: {num_unique_urls}"
        )
    
    @given(
        agent_results=st.lists(agent_result_with_sources_strategy(), min_size=1, max_size=6)
    )
    @settings(max_examples=100)
    def test_deduplication_preserves_source_fields(self, agent_results):
        """
        Property 8: Source Fields Preserved
        **Validates: Requirements 5.1**
        
        Deduplication should preserve all source fields (title, credibility_tier, 
        credibility_score, stance) without modification.
        """
        aggregator = EvidenceAggregator()
        
        # Collect all original sources
        all_original_sources = []
        for result in agent_results:
            all_original_sources.extend(result.get('sources', []))
        
        result = aggregator.aggregate(agent_results)
        deduplicated_sources = result['sources']
        
        # Property: Each deduplicated source should match an original source
        for deduped_source in deduplicated_sources:
            # Find matching original source by normalized URL
            normalized_url = aggregator.normalize_url(deduped_source['url'])
            
            matching_originals = [
                s for s in all_original_sources
                if aggregator.normalize_url(s['url']) == normalized_url
            ]
            
            assert len(matching_originals) > 0, (
                f"Deduplicated source has no matching original:\n{deduped_source}"
            )
            
            # Check that the deduplicated source matches one of the originals
            # (should be the one with highest credibility)
            max_credibility_original = max(
                matching_originals,
                key=lambda s: s.get('credibility_score', 0)
            )
            
            assert deduped_source['title'] == max_credibility_original['title']
            assert deduped_source['credibility_tier'] == max_credibility_original['credibility_tier']
            assert deduped_source['credibility_score'] == max_credibility_original['credibility_score']
            assert deduped_source['stance'] == max_credibility_original['stance']
    
    @given(
        url=st.text(min_size=10, max_size=100)
    )
    @settings(max_examples=100)
    def test_url_normalization_idempotent(self, url):
        """
        Property 8: URL Normalization Idempotence
        **Validates: Requirements 5.1**
        
        Normalizing a URL twice should produce the same result as normalizing once.
        """
        aggregator = EvidenceAggregator()
        
        normalized_once = aggregator.normalize_url(url)
        normalized_twice = aggregator.normalize_url(normalized_once)
        
        # Property: Normalization should be idempotent
        assert normalized_once == normalized_twice, (
            f"URL normalization not idempotent:\n"
            f"Original: {url}\n"
            f"Normalized once: {normalized_once}\n"
            f"Normalized twice: {normalized_twice}"
        )
    
    def test_url_normalization_removes_query_params(self):
        """
        Property 8: Query Parameters Removed
        **Validates: Requirements 5.1**
        
        URL normalization should remove query parameters.
        """
        aggregator = EvidenceAggregator()
        
        url_with_query = "https://example.com/article?utm_source=twitter&id=123"
        url_without_query = "https://example.com/article"
        
        normalized = aggregator.normalize_url(url_with_query)
        
        assert normalized == url_without_query, (
            f"Query parameters not removed:\n"
            f"Input: {url_with_query}\n"
            f"Expected: {url_without_query}\n"
            f"Got: {normalized}"
        )
    
    def test_url_normalization_removes_fragments(self):
        """
        Property 8: Fragments Removed
        **Validates: Requirements 5.1**
        
        URL normalization should remove fragments (hash sections).
        """
        aggregator = EvidenceAggregator()
        
        url_with_fragment = "https://example.com/article#section-2"
        url_without_fragment = "https://example.com/article"
        
        normalized = aggregator.normalize_url(url_with_fragment)
        
        assert normalized == url_without_fragment, (
            f"Fragment not removed:\n"
            f"Input: {url_with_fragment}\n"
            f"Expected: {url_without_fragment}\n"
            f"Got: {normalized}"
        )
    
    def test_url_normalization_removes_trailing_slash(self):
        """
        Property 8: Trailing Slash Removed
        **Validates: Requirements 5.1**
        
        URL normalization should remove trailing slashes.
        """
        aggregator = EvidenceAggregator()
        
        url_with_slash = "https://example.com/article/"
        url_without_slash = "https://example.com/article"
        
        normalized = aggregator.normalize_url(url_with_slash)
        
        assert normalized == url_without_slash, (
            f"Trailing slash not removed:\n"
            f"Input: {url_with_slash}\n"
            f"Expected: {url_without_slash}\n"
            f"Got: {normalized}"
        )
    
    def test_url_normalization_lowercases_domain(self):
        """
        Property 8: Domain Lowercased
        **Validates: Requirements 5.1**
        
        URL normalization should lowercase the domain.
        """
        aggregator = EvidenceAggregator()
        
        url_mixed_case = "https://Example.COM/Article"
        url_lowercase_domain = "https://example.com/Article"
        
        normalized = aggregator.normalize_url(url_mixed_case)
        
        assert normalized == url_lowercase_domain, (
            f"Domain not lowercased:\n"
            f"Input: {url_mixed_case}\n"
            f"Expected: {url_lowercase_domain}\n"
            f"Got: {normalized}"
        )
    
    @given(
        agent_results=st.lists(
            st.builds(
                dict,
                agent=st.sampled_from(['news', 'research', 'scientific']),
                verdict=st.just('supporting'),
                confidence=st.just(0.8),
                sources=st.just([])
            ),
            min_size=1,
            max_size=6
        )
    )
    @settings(max_examples=100)
    def test_empty_sources_handled_gracefully(self, agent_results):
        """
        Property 8: Empty Sources Handled
        **Validates: Requirements 5.1**
        
        When agents return no sources, deduplication should handle this gracefully
        and return an empty list.
        """
        aggregator = EvidenceAggregator()
        
        result = aggregator.aggregate(agent_results)
        deduplicated_sources = result['sources']
        
        # Property: Should return empty list without errors
        assert deduplicated_sources == [], (
            f"Expected empty list for agents with no sources, got {deduplicated_sources}"
        )
        assert result['total_sources'] == 0
    
    @given(
        num_duplicates=st.integers(min_value=2, max_value=20)
    )
    @settings(max_examples=100)
    def test_exact_duplicate_urls_deduplicated(self, num_duplicates):
        """
        Property 8: Exact Duplicates Deduplicated
        **Validates: Requirements 5.1**
        
        When multiple sources have the exact same URL, they should be 
        deduplicated to a single source.
        """
        aggregator = EvidenceAggregator()
        
        # Create multiple sources with identical URLs but different credibility scores
        agent_results = []
        url = "https://example.com/article"
        
        for i in range(num_duplicates):
            agent_results.append({
                'agent': f'agent_{i % 6}',
                'verdict': 'supporting',
                'confidence': 0.8,
                'sources': [{
                    'url': url,
                    'title': f'Article {i}',
                    'credibility_tier': 'tier_1',
                    'credibility_score': i / num_duplicates,  # Increasing scores
                    'stance': 'supporting'
                }]
            })
        
        result = aggregator.aggregate(agent_results)
        deduplicated_sources = result['sources']
        
        # Property: Should have exactly 1 source
        assert len(deduplicated_sources) == 1, (
            f"Expected 1 source after deduplication of {num_duplicates} duplicates, "
            f"got {len(deduplicated_sources)}"
        )
        
        # Property: Should keep the one with highest credibility
        kept_source = deduplicated_sources[0]
        expected_max_score = (num_duplicates - 1) / num_duplicates
        
        assert abs(kept_source['credibility_score'] - expected_max_score) < 0.01, (
            f"Expected highest credibility score {expected_max_score}, "
            f"got {kept_source['credibility_score']}"
        )
    
    @given(
        agent_results=st.lists(agent_result_with_sources_strategy(), min_size=1, max_size=6)
    )
    @settings(max_examples=100)
    def test_deduplication_deterministic(self, agent_results):
        """
        Property 8: Deterministic Deduplication
        **Validates: Requirements 5.1**
        
        Running deduplication twice on the same input should produce 
        identical results.
        """
        aggregator = EvidenceAggregator()
        
        # Run aggregation twice
        result1 = aggregator.aggregate(agent_results)
        result2 = aggregator.aggregate(agent_results)
        
        sources1 = result1['sources']
        sources2 = result2['sources']
        
        # Property: Results should be identical
        assert len(sources1) == len(sources2), (
            f"Non-deterministic deduplication: {len(sources1)} vs {len(sources2)} sources"
        )
        
        # Compare normalized URLs (order might differ due to dict iteration)
        urls1 = sorted([aggregator.normalize_url(s['url']) for s in sources1])
        urls2 = sorted([aggregator.normalize_url(s['url']) for s in sources2])
        
        assert urls1 == urls2, (
            f"Non-deterministic deduplication:\n"
            f"First run: {urls1}\n"
            f"Second run: {urls2}"
        )
