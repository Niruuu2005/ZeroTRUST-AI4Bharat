"""
Unit tests for MetadataExtractor class.

Tests Requirement 13.5:
- URL extraction
- Statistics extraction
- Quote extraction
"""
import pytest
from src.normalization.metadata_extractor import MetadataExtractor


class TestMetadataExtractor:
    """Test suite for MetadataExtractor class."""
    
    @pytest.fixture
    def extractor(self):
        """Create a MetadataExtractor instance for testing."""
        return MetadataExtractor()
    
    # Requirement 13.5: URL extraction
    
    def test_extract_single_url(self, extractor):
        """Test extraction of a single URL from text."""
        text = "Check this article: https://example.com/article for more info"
        result = extractor.extract_urls(text)
        assert len(result) == 1
        assert result[0] == "https://example.com/article"
    
    def test_extract_multiple_urls(self, extractor):
        """Test extraction of multiple URLs from text."""
        text = "Visit https://example.com and https://test.org for details"
        result = extractor.extract_urls(text)
        assert len(result) == 2
        assert "https://example.com" in result
        assert "https://test.org" in result
    
    def test_extract_http_and_https_urls(self, extractor):
        """Test extraction of both HTTP and HTTPS URLs."""
        text = "HTTP: http://example.com and HTTPS: https://secure.com"
        result = extractor.extract_urls(text)
        assert len(result) == 2
        assert "http://example.com" in result
        assert "https://secure.com" in result
    
    def test_extract_urls_with_paths(self, extractor):
        """Test extraction of URLs with complex paths."""
        text = "Read https://example.com/path/to/article?id=123&ref=home"
        result = extractor.extract_urls(text)
        assert len(result) == 1
        assert "https://example.com/path/to/article?id=123&ref=home" in result
    
    def test_extract_no_urls(self, extractor):
        """Test that no URLs are extracted when none exist."""
        text = "This is just plain text without any URLs"
        result = extractor.extract_urls(text)
        assert len(result) == 0
    
    def test_extract_urls_with_fragments(self, extractor):
        """Test extraction of URLs with fragments."""
        text = "See https://example.com/page#section for details"
        result = extractor.extract_urls(text)
        assert len(result) == 1
        assert "https://example.com/page#section" in result
    
    # Requirement 13.5: Statistics extraction
    
    def test_extract_percentage(self, extractor):
        """Test extraction of percentage statistics."""
        text = "The vaccine is 95% effective"
        result = extractor.extract_statistics(text)
        assert len(result) == 1
        assert result[0]['value'] == '95'
        assert result[0]['unit'] == '%'
        assert 'effective' in result[0]['context']
    
    def test_extract_percentage_with_percent_word(self, extractor):
        """Test extraction of statistics with 'percent' word."""
        text = "Efficacy rate is 92 percent"
        result = extractor.extract_statistics(text)
        assert len(result) == 1
        assert result[0]['value'] == '92'
        assert result[0]['unit'] == 'percent'
    
    def test_extract_million(self, extractor):
        """Test extraction of statistics with 'million'."""
        text = "Over 5 million people vaccinated"
        result = extractor.extract_statistics(text)
        assert len(result) == 1
        assert result[0]['value'] == '5'
        assert result[0]['unit'] == 'million'
        assert 'vaccinated' in result[0]['context']
    
    def test_extract_billion(self, extractor):
        """Test extraction of statistics with 'billion'."""
        text = "The budget is 3.5 billion dollars"
        result = extractor.extract_statistics(text)
        assert len(result) == 1
        assert result[0]['value'] == '3.5'
        assert result[0]['unit'] == 'billion'
    
    def test_extract_multiple_statistics(self, extractor):
        """Test extraction of multiple statistics from text."""
        text = "The vaccine is 95% effective and 5 million doses were distributed"
        result = extractor.extract_statistics(text)
        assert len(result) == 2
        # Check first statistic
        assert result[0]['value'] == '95'
        assert result[0]['unit'] == '%'
        # Check second statistic
        assert result[1]['value'] == '5'
        assert result[1]['unit'] == 'million'
    
    def test_extract_statistics_case_insensitive(self, extractor):
        """Test that statistics extraction is case-insensitive."""
        text = "The rate is 75 PERCENT and 2 BILLION people affected"
        result = extractor.extract_statistics(text)
        assert len(result) == 2
        assert result[0]['unit'] == 'percent'
        assert result[1]['unit'] == 'billion'
    
    def test_extract_no_statistics(self, extractor):
        """Test that no statistics are extracted when none exist."""
        text = "This is just plain text without any numbers or units"
        result = extractor.extract_statistics(text)
        assert len(result) == 0
    
    def test_extract_statistics_with_decimal(self, extractor):
        """Test extraction of statistics with decimal values."""
        text = "The rate increased by 12.5 percent"
        result = extractor.extract_statistics(text)
        assert len(result) == 1
        assert result[0]['value'] == '12.5'
        assert result[0]['unit'] == 'percent'
    
    def test_extract_statistics_indian_units(self, extractor):
        """Test extraction of Indian numbering units (crore, lakh)."""
        text = "The population is 1.4 billion or 140 crore or 14000 lakh"
        result = extractor.extract_statistics(text)
        assert len(result) == 3
        units = [stat['unit'] for stat in result]
        assert 'billion' in units
        assert 'crore' in units
        assert 'lakh' in units
    
    def test_extract_statistics_context(self, extractor):
        """Test that context is captured correctly."""
        text = "The vaccine efficacy rate is 95% in clinical trials"
        result = extractor.extract_statistics(text)
        assert len(result) == 1
        context = result[0]['context']
        assert 'efficacy' in context or 'vaccine' in context
        assert 'clinical' in context or 'trials' in context
    
    # Requirement 13.5: Quote extraction
    
    def test_extract_double_quotes(self, extractor):
        """Test extraction of text in double quotes."""
        text = 'The expert said "vaccines are safe and effective"'
        result = extractor.extract_quotes(text)
        assert len(result) == 1
        assert "vaccines are safe and effective" in result
    
    def test_extract_single_quotes(self, extractor):
        """Test extraction of text in single quotes."""
        text = "The report states 'no serious side effects were observed'"
        result = extractor.extract_quotes(text)
        assert len(result) == 1
        assert "no serious side effects were observed" in result
    
    def test_extract_curly_double_quotes(self, extractor):
        """Test extraction of text in curly double quotes."""
        text = 'The study concluded "the vaccine is highly effective"'
        result = extractor.extract_quotes(text)
        assert len(result) == 1
        assert "the vaccine is highly effective" in result
    
    def test_extract_curly_single_quotes(self, extractor):
        """Test extraction of text in curly single quotes."""
        text = "The author wrote 'this is a breakthrough'"
        result = extractor.extract_quotes(text)
        assert len(result) == 1
        assert "this is a breakthrough" in result
    
    def test_extract_multiple_quotes(self, extractor):
        """Test extraction of multiple quotes from text."""
        text = 'He said "first quote" and she replied "second quote"'
        result = extractor.extract_quotes(text)
        assert len(result) == 2
        assert "first quote" in result
        assert "second quote" in result
    
    def test_extract_no_quotes(self, extractor):
        """Test that no quotes are extracted when none exist."""
        text = "This is plain text without any quoted content"
        result = extractor.extract_quotes(text)
        assert len(result) == 0
    
    def test_extract_quotes_removes_duplicates(self, extractor):
        """Test that duplicate quotes are removed."""
        text = 'He said "same quote" and repeated "same quote" again'
        result = extractor.extract_quotes(text)
        assert len(result) == 1
        assert "same quote" in result
    
    def test_extract_mixed_quote_styles(self, extractor):
        """Test extraction of different quote styles in same text."""
        text = 'She said "double quotes" and he said \'single quotes\''
        result = extractor.extract_quotes(text)
        assert len(result) == 2
        assert "double quotes" in result
        assert "single quotes" in result
    
    def test_extract_guillemets(self, extractor):
        """Test extraction of text in guillemets (French quotes)."""
        text = "The document states «this is important»"
        result = extractor.extract_quotes(text)
        assert len(result) == 1
        assert "this is important" in result
    
    def test_extract_empty_quotes(self, extractor):
        """Test handling of empty quotes."""
        text = 'He said "" nothing'
        result = extractor.extract_quotes(text)
        # Empty quotes might be extracted or ignored depending on implementation
        # Just ensure it doesn't crash
        assert isinstance(result, list)
    
    # Integration tests for extract() method
    
    def test_extract_basic_metadata(self, extractor):
        """Test extraction of basic metadata flags."""
        text = "The vaccine is 95% effective"
        result = extractor.extract(text, 'text')
        
        assert 'is_url' in result
        assert 'has_numbers' in result
        assert 'has_quote_markers' in result
        assert 'word_count' in result
        assert 'contains_statistics' in result
        
        assert result['has_numbers'] is True
        assert result['contains_statistics'] is True
        assert result['word_count'] == 5
    
    def test_extract_url_metadata(self, extractor):
        """Test extraction when content is a URL."""
        text = "https://example.com/article"
        result = extractor.extract(text, 'url')
        
        assert result['is_url'] is True
        assert result['source_domain'] == 'example.com'
    
    def test_extract_all_metadata_types(self, extractor):
        """Test extraction of URLs, statistics, and quotes together."""
        text = 'Expert says "95% effective" - see https://example.com for 5 million doses info'
        result = extractor.extract(text, 'text')
        
        # Check URLs
        assert 'urls' in result
        assert len(result['urls']) == 1
        assert 'https://example.com' in result['urls']
        
        # Check statistics
        assert 'statistics' in result
        assert len(result['statistics']) >= 2  # 95% and 5 million
        
        # Check quotes
        assert 'quotes' in result
        assert len(result['quotes']) >= 1
        assert any('95% effective' in quote for quote in result['quotes'])
    
    def test_extract_with_no_metadata(self, extractor):
        """Test extraction when no special metadata exists."""
        text = "This is plain text"
        result = extractor.extract(text, 'text')
        
        assert result['urls'] == []
        assert result['statistics'] == []
        assert result['quotes'] == []
        assert result['is_url'] is False
        assert result['contains_statistics'] is False
    
    def test_extract_complex_claim(self, extractor):
        """Test extraction from a complex claim with multiple metadata types."""
        text = '''
        The CDC reports "COVID-19 vaccines are 95% effective" according to 
        https://cdc.gov/covid. Over 5 million doses have been administered, 
        with "minimal side effects" reported in clinical trials.
        '''
        result = extractor.extract(text, 'text')
        
        # Should extract URLs
        assert len(result['urls']) >= 1
        assert any('cdc.gov' in url for url in result['urls'])
        
        # Should extract statistics
        assert len(result['statistics']) >= 2  # 95% and 5 million
        
        # Should extract quotes
        assert len(result['quotes']) >= 2
        assert any('effective' in quote for quote in result['quotes'])
        assert any('side effects' in quote for quote in result['quotes'])
    
    def test_extract_preserves_backward_compatibility(self, extractor):
        """Test that new fields don't break existing metadata structure."""
        text = "Test claim with 50% accuracy"
        result = extractor.extract(text, 'text')
        
        # Old fields should still exist
        assert 'is_url' in result
        assert 'has_numbers' in result
        assert 'has_quote_markers' in result
        assert 'word_count' in result
        assert 'contains_statistics' in result
        
        # New fields should be added
        assert 'urls' in result
        assert 'statistics' in result
        assert 'quotes' in result
    
    # Edge cases
    
    def test_extract_empty_string(self, extractor):
        """Test handling of empty string."""
        result = extractor.extract("", 'text')
        assert result['urls'] == []
        assert result['statistics'] == []
        assert result['quotes'] == []
        assert result['word_count'] == 0  # Empty string should have 0 words
    
    def test_extract_whitespace_only(self, extractor):
        """Test handling of whitespace-only string."""
        result = extractor.extract("   \t\n  ", 'text')
        assert result['urls'] == []
        assert result['statistics'] == []
        assert result['quotes'] == []
    
    def test_extract_special_characters(self, extractor):
        """Test handling of special characters in text."""
        text = "Rate: 50%! See: https://example.com & 'quoted text' #trending"
        result = extractor.extract(text, 'text')
        
        assert len(result['urls']) >= 1
        assert len(result['statistics']) >= 1
        assert len(result['quotes']) >= 1
    
    def test_extract_unicode_content(self, extractor):
        """Test handling of unicode characters."""
        text = "El estudio dice «95% efectivo» - ver https://ejemplo.com"
        result = extractor.extract(text, 'text')
        
        assert len(result['urls']) >= 1
        assert len(result['statistics']) >= 1
        assert len(result['quotes']) >= 1
