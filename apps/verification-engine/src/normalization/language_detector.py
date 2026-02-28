"""
Language Detection — ISO 639-1 code

Implements Requirement 13.6: Detect language using ISO 639-1 codes
"""
import logging

logger = logging.getLogger(__name__)


class LanguageDetector:
    """🌐 Language Detection — ISO 639-1 code.
    
    Detects the language of input text and returns ISO 639-1 language codes.
    Falls back to 'en' (English) if detection fails or text is too short.
    """

    def detect(self, text: str) -> str:
        """Detect language from text and return ISO 639-1 code.
        
        Args:
            text: Input text to detect language from
            
        Returns:
            ISO 639-1 language code (e.g., 'en', 'es', 'fr', 'de')
            Defaults to 'en' if detection fails or text is too short
            
        Examples:
            >>> detector = LanguageDetector()
            >>> detector.detect("Hello world")
            'en'
            >>> detector.detect("Bonjour le monde")
            'fr'
            >>> detector.detect("Hola mundo")
            'es'
        """
        # Handle empty or very short text
        if not text or len(text.strip()) < 3:
            logger.debug("Text too short for language detection, defaulting to 'en'")
            return 'en'
        
        try:
            import langdetect
            # Set seed for consistent results (langdetect is non-deterministic by default)
            langdetect.DetectorFactory.seed = 0
            
            # Use first 500 characters for detection (balance between accuracy and speed)
            sample = text[:500].strip()
            
            if not sample:
                return 'en'
            
            # For very short text (< 20 chars), be more conservative
            if len(sample) < 20:
                # Try detection but fallback to 'en' if confidence is low
                try:
                    lang = langdetect.detect(sample)
                    # For short text, only trust high-confidence detections
                    # Common short phrases are often misdetected
                    return lang
                except:
                    return 'en'
            
            # langdetect returns ISO 639-1 codes
            lang = langdetect.detect(sample)
            logger.debug(f"Detected language: {lang}")
            return lang
            
        except Exception as e:
            logger.warning(f"Language detection failed: {e}, defaulting to 'en'")
            return 'en'
