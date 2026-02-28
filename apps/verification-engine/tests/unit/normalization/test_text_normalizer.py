"""
Unit tests for TextNormalizer class.

Tests Requirements 13.1, 13.2, 13.3, 13.4:
- HTML tag stripping and entity decoding (13.1)
- Lowercase conversion (13.2)
- Stop word removal (13.3)
- Unicode normalization (13.4)
"""
import pytest
from src.normalization.text_normalizer import TextNormalizer


class TestTextNormalizer:
    """Test suite for TextNormalizer class."""
    
    @pytest.fixture
    def normalizer(self):
        """Create a TextNormalizer instance for testing."""
        return TextNormalizer()
    
    # Requirement 13.1: HTML tag stripping and entity decoding
    
    def test_html_entity_decoding(self, normalizer):
        """Test that HTML entities are decoded correctly."""
        text = "COVID-19 vaccines are &quot;safe&quot; &amp; effective"
        result = normalizer.normalize(text)
        assert '"' in result
        assert '&' in result
        assert '&quot;' not in result
        assert '&amp;' not in result
    
    def test_html_tag_stripping(self, normalizer):
        """Test that HTML tags are removed."""
        text = "<p>COVID-19 vaccines are <strong>safe</strong> and effective</p>"
        result = normalizer.normalize(text)
        assert '<p>' not in result
        assert '<strong>' not in result
        assert '</strong>' not in result
        assert '</p>' not in result
        assert 'covid-19' in result
        assert 'vaccines' in result
    
    def test_html_complex_tags(self, normalizer):
        """Test stripping of complex HTML with attributes."""
        text = '<div class="content"><a href="http://example.com">Click here</a></div>'
        result = normalizer.normalize(text)
        assert '<div' not in result
        assert '<a' not in result
        assert 'click here' in result
    
    # Requirement 13.2: Lowercase conversion
    
    def test_lowercase_conversion(self, normalizer):
        """Test that text is converted to lowercase."""
        text = "COVID-19 Vaccines Are SAFE and Effective"
        result = normalizer.normalize(text)
        assert result == result.lower()
        assert 'COVID' not in result
        assert 'SAFE' not in result
    
    def test_mixed_case_handling(self, normalizer):
        """Test handling of mixed case text."""
        text = "ThE QuIcK BrOwN FoX"
        result = normalizer.normalize(text)
        assert 'quick' in result
        assert 'brown' in result
        assert 'fox' in result
    
    # Requirement 13.3: Stop word removal
    
    def test_stop_word_removal(self, normalizer):
        """Test that common stop words are removed."""
        text = "The COVID-19 vaccines are safe and effective"
        result = normalizer.normalize(text)
        # Stop words should be removed
        assert 'the' not in result.split()
        assert 'are' not in result.split()
        assert 'and' not in result.split()
        # Content words should remain
        assert 'covid-19' in result
        assert 'vaccines' in result
        assert 'safe' in result
        assert 'effective' in result
    
    def test_multiple_stop_words(self, normalizer):
        """Test removal of multiple consecutive stop words."""
        text = "This is a test of the system"
        result = normalizer.normalize(text)
        tokens = result.split()
        # Stop words removed: this, is, a, of, the
        assert 'this' not in tokens
        assert 'is' not in tokens
        assert 'a' not in tokens
        assert 'of' not in tokens
        assert 'the' not in tokens
        # Content words remain
        assert 'test' in tokens
        assert 'system' in tokens
    
    # Requirement 13.4: Unicode normalization
    
    def test_unicode_normalization(self, normalizer):
        """Test that unicode characters are normalized to NFC form."""
        # Using combining characters vs precomposed
        text_composed = "café"  # é as single character
        text_decomposed = "café"  # e + combining acute accent
        
        result1 = normalizer.normalize(text_composed)
        result2 = normalizer.normalize(text_decomposed)
        
        # Both should normalize to the same form
        assert result1 == result2
    
    def test_unicode_special_characters(self, normalizer):
        """Test handling of various unicode characters."""
        text = "Ñoño's café résumé"
        result = normalizer.normalize(text)
        # Should preserve unicode characters after normalization
        assert 'ñ' in result or 'n' in result  # Depends on normalization
        assert len(result) > 0
    
    # Edge cases and integration tests
    
    def test_empty_string(self, normalizer):
        """Test handling of empty string."""
        result = normalizer.normalize("")
        assert result == ""
    
    def test_whitespace_only(self, normalizer):
        """Test handling of whitespace-only string."""
        result = normalizer.normalize("   \t\n  ")
        assert result == ""
    
    def test_whitespace_normalization(self, normalizer):
        """Test that multiple whitespaces are collapsed."""
        text = "COVID-19    vaccines   are\t\tsafe\n\nand    effective"
        result = normalizer.normalize(text)
        # Should not have multiple consecutive spaces
        assert '  ' not in result
        assert '\t' not in result
        assert '\n' not in result
    
    def test_combined_html_and_entities(self, normalizer):
        """Test handling of both HTML tags and entities together."""
        text = "<p>The &quot;quick&quot; brown &amp; <strong>fast</strong> fox</p>"
        result = normalizer.normalize(text)
        assert '<' not in result
        assert '>' not in result
        assert '&quot;' not in result
        assert '&amp;' not in result
        assert '"quick"' in result
        assert '&' in result
        assert 'fast' in result
    
    def test_all_requirements_combined(self, normalizer):
        """Test all normalization requirements together."""
        text = "<div>The COVID-19 &amp; vaccines are <strong>SAFE</strong> and effective!</div>"
        result = normalizer.normalize(text)
        
        # HTML stripped (13.1)
        assert '<' not in result
        assert '>' not in result
        
        # Entities decoded (13.1)
        assert '&amp;' not in result
        assert '&' in result
        
        # Lowercase (13.2)
        assert result == result.lower()
        
        # Stop words removed (13.3)
        tokens = result.split()
        assert 'the' not in tokens
        assert 'are' not in tokens
        assert 'and' not in tokens
        
        # Content preserved
        assert 'covid-19' in result
        assert 'vaccines' in result
        assert 'safe' in result
        assert 'effective' in result
    
    # Tests for to_cache_key method
    
    def test_cache_key_order_independence(self, normalizer):
        """Test that cache keys are order-independent."""
        text1 = "vaccines are safe"
        text2 = "safe are vaccines"
        
        key1 = normalizer.to_cache_key(text1)
        key2 = normalizer.to_cache_key(text2)
        
        # Should produce the same cache key
        assert key1 == key2
    
    def test_cache_key_punctuation_removal(self, normalizer):
        """Test that punctuation is removed from cache keys."""
        text = "COVID-19 vaccines are safe, effective, and important!"
        key = normalizer.to_cache_key(text)
        
        # Punctuation should be removed
        assert ',' not in key
        assert '!' not in key
        assert '.' not in key
    
    def test_cache_key_consistency(self, normalizer):
        """Test that identical normalized text produces identical cache keys."""
        text = "The COVID-19 vaccines are safe and effective"
        key1 = normalizer.to_cache_key(text)
        key2 = normalizer.to_cache_key(text)
        
        assert key1 == key2
    
    def test_cache_key_with_html(self, normalizer):
        """Test cache key generation with HTML content."""
        text1 = "<p>COVID-19 vaccines are safe</p>"
        text2 = "COVID-19 vaccines are safe"
        
        key1 = normalizer.to_cache_key(text1)
        key2 = normalizer.to_cache_key(text2)
        
        # Should produce similar keys after HTML stripping
        assert key1 == key2
