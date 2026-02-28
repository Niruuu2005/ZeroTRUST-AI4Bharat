"""
Normalization Layer — Pre-processes claim before Manager Agent
"""
from .text_normalizer import TextNormalizer
from .metadata_extractor import MetadataExtractor
from .language_detector import LanguageDetector


class NormalizationLayer:
    """Pre-processes claim before Manager Agent — Diagram 2: Normalization Layer."""

    def __init__(self):
        self.text_norm = TextNormalizer()
        self.meta_extract = MetadataExtractor()
        self.lang_detect = LanguageDetector()

    async def process(self, request: dict) -> dict:
        """Process and normalize the request."""
        content = request['content']
        claim_type = request['type']

        normalized_text = self.text_norm.normalize(content)
        metadata = self.meta_extract.extract(content, claim_type)
        language = self.lang_detect.detect(content)

        return {
            **request,
            'normalized_content': normalized_text,
            'metadata': metadata,
            'language': language,
            'original_content': content
        }


__all__ = ['NormalizationLayer', 'TextNormalizer', 'MetadataExtractor', 'LanguageDetector']
