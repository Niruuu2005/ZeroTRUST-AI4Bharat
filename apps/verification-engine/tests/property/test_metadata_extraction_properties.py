"""
Property-based tests for metadata extraction.

Property 24: Metadata Extraction Completeness
**Validates: Requirements 13.5**

Property: For any claim text containing URLs, statistics, or quotes, the metadata 
extractor should identify and extract all such elements into the metadata dictionary.
"""
import re
import pytest
from hypothesis import given, strategies as st, settings, assume
from src.normalization.metadata_extractor import MetadataExtractor


# Custom strategies for generating test data
@st.composite
def text_with_urls(draw):
    """Generate text containing one or more URLs."""
    base_text = draw(st.text(min_size=0, max_size=200))
    num_urls = draw(st.integers(min_value=1, max_value=5))
    
    urls = []
    for _ in range(num_urls):
        protocol = draw(st.sampled_from(['http://', 'https://']))
        domain = draw(st.text(
            alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), min_codepoint=97, max_codepoint=122),
            min_size=3,
            max_size=15
        ))
        tld = draw(st.sampled_from(['.com', '.org', '.net', '.edu', '.gov']))
        path = draw(st.text(
            alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), min_codepoint=97, max_codepoint=122),
            min_size=0,
            max_size=20
        ))
        
        url = f"{protocol}{domain}{tld}"
        if path:
            url += f"/{path}"
        urls.append(url)
    
    # Insert URLs into text
    parts = [base_text] + urls
    text = ' '.join(parts)
    
    return text, urls


@st.composite
def text_with_statistics(draw):
    """Generate text containing one or more statistics."""
    base_text = draw(st.text(min_size=0, max_size=200))
    num_stats = draw(st.integers(min_value=1, max_value=5))
    
    statistics = []
    for _ in range(num_stats):
        value = draw(st.one_of(
            st.integers(min_value=1, max_value=999),
            st.floats(min_value=0.1, max_value=999.9, allow_nan=False, allow_infinity=False).map(lambda x: round(x, 1))
        ))
        unit = draw(st.sampled_from(['%', 'percent', 'million', 'billion', 'trillion', 'thousand', 'crore', 'lakh', 'hundred']))
        
        stat_text = f"{value} {unit}" if unit != '%' else f"{value}%"
        statistics.append({'text': stat_text, 'value': str(value), 'unit': unit})
    
    # Insert statistics into text
    parts = [base_text] + [s['text'] for s in statistics]
    text = ' '.join(parts)
    
    return text, statistics


@st.composite
def text_with_quotes(draw):
    """Generate text containing one or more quotes."""
    # Generate base text without quote characters
    base_words = draw(st.lists(
        st.text(
            alphabet='abcdefghijklmnopqrstuvwxyz',
            min_size=1,
            max_size=10
        ),
        min_size=0,
        max_size=10
    ))
    base_text = ' '.join(base_words)
    
    num_quotes = draw(st.integers(min_value=1, max_value=3))
    
    quotes = []
    for _ in range(num_quotes):
        # Generate simple alphanumeric quote content
        quote_words = draw(st.lists(
            st.text(
                alphabet='abcdefghijklmnopqrstuvwxyz',
                min_size=1,
                max_size=8
            ),
            min_size=1,
            max_size=5
        ))
        quote_content = ' '.join(quote_words)
        
        # Use only double quotes for simplicity and reliability
        quoted_text = f'"{quote_content}"'
        quotes.append({'text': quoted_text, 'content': quote_content})
    
    # Build text with quotes
    parts = []
    if base_text:
        parts.append(base_text)
    for q in quotes:
        parts.append(q['text'])
    text = ' '.join(parts)
    
    return text, quotes


class TestMetadataExtractionProperties:
    """Property-based tests for metadata extraction."""
    
    @given(text_with_urls())
    @settings(max_examples=100)
    def test_url_extraction_completeness(self, data):
        """
        Property 24: URL Extraction Completeness
        **Validates: Requirements 13.5**
        
        For any claim text containing URLs, the metadata extractor should 
        identify and extract all URLs.
        """
        text, expected_urls = data
        extractor = MetadataExtractor()
        
        # Extract metadata
        result = extractor.extract(text, 'text')
        
        # Property: All URLs should be extracted
        extracted_urls = result['urls']
        
        # Check that we extracted at least as many URLs as we inserted
        assert len(extracted_urls) >= len(expected_urls), (
            f"Not all URLs were extracted:\n"
            f"Text: {repr(text)}\n"
            f"Expected URLs: {expected_urls}\n"
            f"Extracted URLs: {extracted_urls}\n"
            f"Expected count: {len(expected_urls)}\n"
            f"Extracted count: {len(extracted_urls)}"
        )
        
        # Check that each expected URL is found in the extracted URLs
        for expected_url in expected_urls:
            assert any(expected_url in extracted for extracted in extracted_urls), (
                f"Expected URL not found in extracted URLs:\n"
                f"Expected: {expected_url}\n"
                f"Extracted: {extracted_urls}\n"
                f"Text: {repr(text)}"
            )
    
    @given(text_with_statistics())
    @settings(max_examples=100)
    def test_statistics_extraction_completeness(self, data):
        """
        Property 24: Statistics Extraction Completeness
        **Validates: Requirements 13.5**
        
        For any claim text containing statistics, the metadata extractor should 
        identify and extract all statistical elements.
        """
        text, expected_stats = data
        extractor = MetadataExtractor()
        
        # Extract metadata
        result = extractor.extract(text, 'text')
        
        # Property: All statistics should be extracted
        extracted_stats = result['statistics']
        
        # Check that we extracted at least as many statistics as we inserted
        assert len(extracted_stats) >= len(expected_stats), (
            f"Not all statistics were extracted:\n"
            f"Text: {repr(text)}\n"
            f"Expected stats: {expected_stats}\n"
            f"Extracted stats: {extracted_stats}\n"
            f"Expected count: {len(expected_stats)}\n"
            f"Extracted count: {len(extracted_stats)}"
        )
        
        # Check that each expected statistic is found in the extracted statistics
        for expected_stat in expected_stats:
            # Normalize unit for comparison (% vs percent)
            expected_unit = expected_stat['unit'].lower()
            
            found = False
            for extracted in extracted_stats:
                extracted_unit = extracted['unit'].lower()
                extracted_value = extracted['value']
                
                # Match if value and unit match
                if extracted_value == expected_stat['value'] and extracted_unit == expected_unit:
                    found = True
                    break
            
            assert found, (
                f"Expected statistic not found in extracted statistics:\n"
                f"Expected: value={expected_stat['value']}, unit={expected_stat['unit']}\n"
                f"Extracted: {extracted_stats}\n"
                f"Text: {repr(text)}"
            )
    
    @given(text_with_quotes())
    @settings(max_examples=100)
    def test_quote_extraction_completeness(self, data):
        """
        Property 24: Quote Extraction Completeness
        **Validates: Requirements 13.5**
        
        For any claim text containing quotes, the metadata extractor should 
        identify and extract all quoted text.
        """
        text, expected_quotes = data
        extractor = MetadataExtractor()
        
        # Extract metadata
        result = extractor.extract(text, 'text')
        
        # Property: All quotes should be extracted
        extracted_quotes = result['quotes']
        
        # Check that we extracted at least as many quotes as we inserted
        # Note: Duplicates are removed, so we check unique quotes
        unique_expected = list(set(q['content'] for q in expected_quotes))
        
        assert len(extracted_quotes) >= len(unique_expected), (
            f"Not all quotes were extracted:\n"
            f"Text: {repr(text)}\n"
            f"Expected quotes: {unique_expected}\n"
            f"Extracted quotes: {extracted_quotes}\n"
            f"Expected count: {len(unique_expected)}\n"
            f"Extracted count: {len(extracted_quotes)}"
        )
        
        # Check that each expected quote content is found in the extracted quotes
        for expected_quote in unique_expected:
            assert expected_quote in extracted_quotes, (
                f"Expected quote not found in extracted quotes:\n"
                f"Expected: {repr(expected_quote)}\n"
                f"Extracted: {extracted_quotes}\n"
                f"Text: {repr(text)}"
            )
    
    @given(st.text(min_size=1, max_size=1000))
    @settings(max_examples=100)
    def test_metadata_dictionary_structure(self, text):
        """
        Property 24: Metadata Dictionary Structure
        **Validates: Requirements 13.5**
        
        For any claim text, the metadata extractor should return a dictionary
        with all required fields (urls, statistics, quotes).
        """
        extractor = MetadataExtractor()
        
        # Extract metadata
        result = extractor.extract(text, 'text')
        
        # Property: Result should be a dictionary with required fields
        assert isinstance(result, dict), (
            f"Result is not a dictionary: {type(result)}"
        )
        
        # Check required fields exist
        required_fields = ['urls', 'statistics', 'quotes']
        for field in required_fields:
            assert field in result, (
                f"Required field '{field}' missing from metadata:\n"
                f"Result keys: {result.keys()}\n"
                f"Text: {repr(text[:100])}"
            )
        
        # Check that fields are lists
        assert isinstance(result['urls'], list), (
            f"'urls' field is not a list: {type(result['urls'])}"
        )
        assert isinstance(result['statistics'], list), (
            f"'statistics' field is not a list: {type(result['statistics'])}"
        )
        assert isinstance(result['quotes'], list), (
            f"'quotes' field is not a list: {type(result['quotes'])}"
        )
    
    @given(st.text(min_size=1, max_size=1000))
    @settings(max_examples=100)
    def test_statistics_structure(self, text):
        """
        Property 24: Statistics Structure
        **Validates: Requirements 13.5**
        
        For any extracted statistic, it should have the required fields:
        value, unit, context, and full_match.
        """
        extractor = MetadataExtractor()
        
        # Extract metadata
        result = extractor.extract(text, 'text')
        
        # Property: Each statistic should have required fields
        for stat in result['statistics']:
            assert isinstance(stat, dict), (
                f"Statistic is not a dictionary: {type(stat)}"
            )
            
            required_fields = ['value', 'unit', 'context', 'full_match']
            for field in required_fields:
                assert field in stat, (
                    f"Required field '{field}' missing from statistic:\n"
                    f"Statistic: {stat}\n"
                    f"Text: {repr(text[:100])}"
                )
            
            # Check field types
            assert isinstance(stat['value'], str), (
                f"Statistic value is not a string: {type(stat['value'])}"
            )
            assert isinstance(stat['unit'], str), (
                f"Statistic unit is not a string: {type(stat['unit'])}"
            )
            assert isinstance(stat['context'], str), (
                f"Statistic context is not a string: {type(stat['context'])}"
            )
            assert isinstance(stat['full_match'], str), (
                f"Statistic full_match is not a string: {type(stat['full_match'])}"
            )
    
    @given(st.text(min_size=0, max_size=1000))
    @settings(max_examples=100)
    def test_empty_extraction_returns_empty_lists(self, text):
        """
        Property 24: Empty Extraction Returns Empty Lists
        **Validates: Requirements 13.5**
        
        For any text without URLs, statistics, or quotes, the extractor should
        return empty lists (not None or other values).
        """
        # Filter out texts that might contain URLs, statistics, or quotes
        assume(not re.search(r'https?://', text))
        assume(not re.search(r'\d+\.?\d*\s*(%|percent|million|billion|trillion|thousand|crore|lakh|hundred)', text, re.IGNORECASE))
        assume(not re.search(r'["\'""''«»]', text))
        
        extractor = MetadataExtractor()
        
        # Extract metadata
        result = extractor.extract(text, 'text')
        
        # Property: Empty results should be empty lists, not None
        assert result['urls'] == [], (
            f"URLs should be empty list but got: {result['urls']}\n"
            f"Text: {repr(text[:100])}"
        )
        assert result['statistics'] == [], (
            f"Statistics should be empty list but got: {result['statistics']}\n"
            f"Text: {repr(text[:100])}"
        )
        assert result['quotes'] == [], (
            f"Quotes should be empty list but got: {result['quotes']}\n"
            f"Text: {repr(text[:100])}"
        )
    
    @given(
        st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), min_codepoint=97, max_codepoint=122),
                min_size=3,
                max_size=15
            ),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=100)
    def test_url_extraction_no_false_positives(self, words):
        """
        Property 24: URL Extraction No False Positives
        **Validates: Requirements 13.5**
        
        For any text without valid URLs, the extractor should not extract
        false positives.
        """
        # Create text without URLs
        text = ' '.join(words)
        
        # Ensure no URLs in text
        assume(not re.search(r'https?://', text))
        
        extractor = MetadataExtractor()
        
        # Extract metadata
        result = extractor.extract(text, 'text')
        
        # Property: Should not extract any URLs
        assert len(result['urls']) == 0, (
            f"False positive URLs extracted:\n"
            f"Text: {repr(text)}\n"
            f"Extracted URLs: {result['urls']}"
        )
    
    @given(st.text(min_size=1, max_size=500))
    @settings(max_examples=100)
    def test_quote_deduplication(self, text):
        """
        Property 24: Quote Deduplication
        **Validates: Requirements 13.5**
        
        For any text with duplicate quotes, the extractor should deduplicate
        them and return unique quotes only.
        """
        extractor = MetadataExtractor()
        
        # Extract metadata
        result = extractor.extract(text, 'text')
        
        # Property: Extracted quotes should be unique
        extracted_quotes = result['quotes']
        unique_quotes = list(set(extracted_quotes))
        
        assert len(extracted_quotes) == len(unique_quotes), (
            f"Duplicate quotes found:\n"
            f"Extracted: {extracted_quotes}\n"
            f"Unique: {unique_quotes}\n"
            f"Text: {repr(text[:200])}"
        )
    
    @given(
        st.text(min_size=1, max_size=200),
        st.lists(
            st.tuples(
                st.integers(min_value=1, max_value=999),
                st.sampled_from(['%', 'percent', 'million', 'billion'])
            ),
            min_size=1,
            max_size=3
        )
    )
    @settings(max_examples=100)
    def test_combined_metadata_extraction(self, base_text, stats):
        """
        Property 24: Combined Metadata Extraction
        **Validates: Requirements 13.5**
        
        For any text containing multiple types of metadata (URLs, statistics, quotes),
        the extractor should extract all types correctly.
        """
        # Build text with multiple metadata types
        url = "https://example.com/article"
        quote = '"this is a quote"'
        stat_texts = [f"{value} {unit}" if unit != '%' else f"{value}%" for value, unit in stats]
        
        text = f"{base_text} {url} {quote} {' '.join(stat_texts)}"
        
        extractor = MetadataExtractor()
        
        # Extract metadata
        result = extractor.extract(text, 'text')
        
        # Property: Should extract all types of metadata
        assert len(result['urls']) >= 1, (
            f"URL not extracted:\n"
            f"Text: {repr(text)}\n"
            f"Extracted URLs: {result['urls']}"
        )
        
        assert len(result['statistics']) >= len(stats), (
            f"Not all statistics extracted:\n"
            f"Text: {repr(text)}\n"
            f"Expected stats: {stats}\n"
            f"Extracted stats: {result['statistics']}"
        )
        
        assert len(result['quotes']) >= 1, (
            f"Quote not extracted:\n"
            f"Text: {repr(text)}\n"
            f"Extracted quotes: {result['quotes']}"
        )
