"""
Text Normalization — strip HTML, fix unicode, normalize whitespace
"""
import re
import unicodedata
import html as html_lib


class TextNormalizer:
    """🔤 Text Normalization — strip HTML, fix unicode, normalize whitespace."""

    # Common stop words for cache key generation
    STOP_WORDS = frozenset([
        'a','an','the','is','are','was','were','be','been','being',
        'have','has','had','do','does','did','will','would','could',
        'should','may','might','shall','can','of','in','at','by','for',
        'with','about','as','from','that','this','it','its','to','and','or',
    ])

    def normalize(self, text: str) -> str:
        """Normalize text for processing.
        
        Implements requirements 13.1, 13.2, 13.3, 13.4:
        - Strip HTML tags and decode entities (13.1)
        - Convert to lowercase (13.2)
        - Remove stop words (13.3)
        - Normalize unicode characters (13.4)
        """
        # Decode HTML entities (Requirement 13.1)
        text = html_lib.unescape(text)
        
        # Strip HTML tags (Requirement 13.1)
        text = re.sub(r'<[^>]+>', '', text)
        
        # Normalize unicode (NFC) (Requirement 13.4)
        text = unicodedata.normalize('NFC', text)
        
        # Convert to lowercase (Requirement 13.2)
        text = text.lower()
        
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove stop words (Requirement 13.3)
        tokens = text.split()
        tokens = [w for w in tokens if w not in self.STOP_WORDS]
        text = ' '.join(tokens)
        
        return text

    def to_cache_key(self, text: str) -> str:
        """Order-independent cache key (for near-duplicate detection).
        
        Creates a canonical representation by normalizing, removing punctuation,
        and sorting tokens for consistent cache key generation.
        """
        # Normalize text (already handles lowercase, stop words, unicode, HTML)
        normalized = self.normalize(text)
        
        # Remove punctuation
        import string
        normalized = normalized.translate(str.maketrans('', '', string.punctuation))
        
        # Sort tokens for order-independent matching
        tokens = normalized.split()
        canonical = ' '.join(sorted(tokens))
        
        return canonical
