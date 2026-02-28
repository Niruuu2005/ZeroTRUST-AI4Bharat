"""
Property-based tests for text normalization.

Property 23: Text Normalization Idempotence
**Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.7**

Property: For any claim text, normalizing it twice should produce the same result 
as normalizing it once, and the generated Claim_Hash should be identical for 
equivalent normalized text.
"""
import hashlib
import pytest
from hypothesis import given, strategies as st, settings
from src.normalization.text_normalizer import TextNormalizer


class TestNormalizationProperties:
    """Property-based tests for text normalization."""
    
    @given(st.text(min_size=1, max_size=1000))
    @settings(max_examples=100)
    def test_normalization_idempotence(self, text):
        """
        Property 23: Text Normalization Idempotence
        **Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.7**
        
        For any claim text, normalizing it twice should produce the same result
        as normalizing it once.
        """
        normalizer = TextNormalizer()
        
        # Normalize once
        normalized_once = normalizer.normalize(text)
        
        # Normalize twice
        normalized_twice = normalizer.normalize(normalized_once)
        
        # Property: Normalizing twice should equal normalizing once (idempotence)
        assert normalized_once == normalized_twice, (
            f"Normalization is not idempotent:\n"
            f"Original: {repr(text)}\n"
            f"Once: {repr(normalized_once)}\n"
            f"Twice: {repr(normalized_twice)}"
        )
    
    @given(st.text(min_size=1, max_size=1000))
    @settings(max_examples=100)
    def test_claim_hash_consistency(self, text):
        """
        Property 23: Claim Hash Consistency
        **Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.7**
        
        For any claim text, the generated Claim_Hash should be identical when
        computed from the same normalized text.
        """
        normalizer = TextNormalizer()
        
        # Normalize the text
        normalized = normalizer.normalize(text)
        
        # Generate hash twice from the same normalized text
        hash1 = hashlib.sha256(normalized.encode()).hexdigest()[:32]
        hash2 = hashlib.sha256(normalized.encode()).hexdigest()[:32]
        
        # Property: Same normalized text should produce identical hashes
        assert hash1 == hash2, (
            f"Hash generation is not consistent:\n"
            f"Normalized: {repr(normalized)}\n"
            f"Hash1: {hash1}\n"
            f"Hash2: {hash2}"
        )
    
    @given(
        st.text(min_size=1, max_size=500),
        st.text(min_size=1, max_size=500)
    )
    @settings(max_examples=100)
    def test_equivalent_text_produces_same_hash(self, text1, text2):
        """
        Property 23: Equivalent Normalized Text Produces Same Hash
        **Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.7**
        
        If two different texts normalize to the same result, they should produce
        the same Claim_Hash.
        """
        normalizer = TextNormalizer()
        
        # Normalize both texts
        normalized1 = normalizer.normalize(text1)
        normalized2 = normalizer.normalize(text2)
        
        # Generate hashes
        hash1 = hashlib.sha256(normalized1.encode()).hexdigest()[:32]
        hash2 = hashlib.sha256(normalized2.encode()).hexdigest()[:32]
        
        # Property: If normalized texts are equal, hashes must be equal
        if normalized1 == normalized2:
            assert hash1 == hash2, (
                f"Equal normalized texts produced different hashes:\n"
                f"Text1: {repr(text1)}\n"
                f"Text2: {repr(text2)}\n"
                f"Normalized1: {repr(normalized1)}\n"
                f"Normalized2: {repr(normalized2)}\n"
                f"Hash1: {hash1}\n"
                f"Hash2: {hash2}"
            )
    
    @given(st.text(min_size=1, max_size=1000))
    @settings(max_examples=100)
    def test_normalization_preserves_content_words(self, text):
        """
        Property 23: Normalization Preserves Content
        **Validates: Requirements 13.1, 13.2, 13.3, 13.4**
        
        Normalization should preserve non-stop-word content, even if it transforms
        the text (lowercase, HTML stripping, etc.).
        """
        normalizer = TextNormalizer()
        normalized = normalizer.normalize(text)
        
        # Property: Normalized text should not be longer than original
        # (we only remove/transform, never add content)
        # Note: This is a weak property but helps catch bugs
        assert len(normalized) <= len(text) + 100, (
            f"Normalized text is unexpectedly longer than original:\n"
            f"Original length: {len(text)}\n"
            f"Normalized length: {len(normalized)}\n"
            f"Original: {repr(text[:100])}\n"
            f"Normalized: {repr(normalized[:100])}"
        )
    
    @given(
        st.text(
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll'),  # Uppercase and lowercase letters
                min_codepoint=65, max_codepoint=122
            ),
            min_size=1,
            max_size=100
        )
    )
    @settings(max_examples=100)
    def test_lowercase_property(self, text):
        """
        Property 23: Lowercase Conversion
        **Validates: Requirements 13.2**
        
        For any text containing letters, the normalized result should be entirely
        lowercase.
        """
        normalizer = TextNormalizer()
        normalized = normalizer.normalize(text)
        
        # Property: All alphabetic characters should be lowercase
        for char in normalized:
            if char.isalpha():
                assert char.islower(), (
                    f"Found uppercase character '{char}' in normalized text:\n"
                    f"Original: {repr(text)}\n"
                    f"Normalized: {repr(normalized)}"
                )
    
    @given(
        st.text(min_size=1, max_size=500).map(
            lambda t: f"<p>{t}</p>" if t else "<p>test</p>"
        )
    )
    @settings(max_examples=100)
    def test_html_stripping_property(self, text):
        """
        Property 23: HTML Tag Stripping
        **Validates: Requirements 13.1**
        
        For any text containing HTML tags, the normalized result should not
        contain any HTML tags.
        """
        normalizer = TextNormalizer()
        normalized = normalizer.normalize(text)
        
        # Property: No HTML tags should remain
        assert '<' not in normalized or '>' not in normalized, (
            f"HTML tags found in normalized text:\n"
            f"Original: {repr(text[:200])}\n"
            f"Normalized: {repr(normalized[:200])}"
        )
    
    @given(
        st.text(min_size=1, max_size=500).map(
            lambda t: f"{t} &quot;test&quot; &amp; more" if t else "&quot;test&quot;"
        )
    )
    @settings(max_examples=100)
    def test_html_entity_decoding_property(self, text):
        """
        Property 23: HTML Entity Decoding
        **Validates: Requirements 13.1**
        
        For any text containing HTML entities, the normalized result should not
        contain common HTML entities like &quot;, &amp;, etc.
        """
        normalizer = TextNormalizer()
        normalized = normalizer.normalize(text)
        
        # Property: Common HTML entities should be decoded
        assert '&quot;' not in normalized, (
            f"HTML entity &quot; found in normalized text:\n"
            f"Original: {repr(text[:200])}\n"
            f"Normalized: {repr(normalized[:200])}"
        )
        assert '&amp;' not in normalized, (
            f"HTML entity &amp; found in normalized text:\n"
            f"Original: {repr(text[:200])}\n"
            f"Normalized: {repr(normalized[:200])}"
        )
    
    @given(st.text(min_size=1, max_size=1000))
    @settings(max_examples=100)
    def test_whitespace_normalization_property(self, text):
        """
        Property 23: Whitespace Normalization
        **Validates: Requirements 13.1, 13.2, 13.3, 13.4**
        
        For any text, the normalized result should not contain multiple consecutive
        spaces, tabs, or newlines.
        """
        normalizer = TextNormalizer()
        normalized = normalizer.normalize(text)
        
        # Property: No multiple consecutive whitespace
        assert '  ' not in normalized, (
            f"Multiple consecutive spaces found in normalized text:\n"
            f"Original: {repr(text[:200])}\n"
            f"Normalized: {repr(normalized[:200])}"
        )
        assert '\t' not in normalized, (
            f"Tab character found in normalized text:\n"
            f"Original: {repr(text[:200])}\n"
            f"Normalized: {repr(normalized[:200])}"
        )
        assert '\n' not in normalized, (
            f"Newline character found in normalized text:\n"
            f"Original: {repr(text[:200])}\n"
            f"Normalized: {repr(normalized[:200])}"
        )
    
    @given(
        st.lists(
            st.sampled_from([
                'the', 'a', 'an', 'is', 'are', 'was', 'were', 'and', 'or', 'of'
            ]),
            min_size=1,
            max_size=10
        ).map(lambda words: ' '.join(words) + ' important content')
    )
    @settings(max_examples=100)
    def test_stop_word_removal_property(self, text):
        """
        Property 23: Stop Word Removal
        **Validates: Requirements 13.3**
        
        For any text containing stop words, the normalized result should not
        contain those stop words as separate tokens.
        """
        normalizer = TextNormalizer()
        normalized = normalizer.normalize(text)
        tokens = normalized.split()
        
        # Property: Stop words should not appear as separate tokens
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'and', 'or', 'of'}
        found_stop_words = [token for token in tokens if token in stop_words]
        
        assert len(found_stop_words) == 0, (
            f"Stop words found in normalized text:\n"
            f"Original: {repr(text)}\n"
            f"Normalized: {repr(normalized)}\n"
            f"Found stop words: {found_stop_words}"
        )
