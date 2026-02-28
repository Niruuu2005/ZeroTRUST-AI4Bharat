"""
Metadata Extraction — entity hints, URL domain, claim markers
"""
import re
from typing import List, Dict, Any
from urllib.parse import urlparse


class MetadataExtractor:
    """🏷️ Metadata Extraction — entity hints, URL domain, claim markers.
    
    Implements Requirement 13.5: Extract metadata (URLs, statistics, quotes) from claim text.
    """

    def extract(self, content: str, claim_type: str = 'text') -> Dict[str, Any]:
        """Extract metadata from content.
        
        Implements Requirement 13.5:
        - URL extraction
        - Statistics extraction
        - Quote extraction
        
        Args:
            content: The claim text to extract metadata from
            claim_type: Type of claim (text, url, etc.)
            
        Returns:
            Dictionary containing extracted metadata
        """
        # Calculate word count properly (empty string should be 0)
        word_count = len(content.split()) if content.strip() else 0
        
        metadata: Dict[str, Any] = {
            'is_url': bool(re.match(r'https?://', content.strip())),
            'has_numbers': bool(re.search(r'\d+\.?\d*%?', content)),
            'has_quote_markers': bool(re.search(r'["\'"]', content)),
            'word_count': word_count,
            'contains_statistics': bool(re.search(
                r'\d+\.?\d*\s*(%|percent|million|billion|crore|lakh)', 
                content, 
                re.IGNORECASE
            )),
        }
        
        # Extract domain if URL
        if metadata['is_url']:
            try:
                parsed = urlparse(content.strip())
                metadata['source_domain'] = parsed.netloc
            except Exception:
                pass
        
        # Requirement 13.5: Extract URLs from text
        metadata['urls'] = self.extract_urls(content)
        
        # Requirement 13.5: Extract statistics from text
        metadata['statistics'] = self.extract_statistics(content)
        
        # Requirement 13.5: Extract quotes from text
        metadata['quotes'] = self.extract_quotes(content)
        
        return metadata

    def extract_urls(self, text: str) -> List[str]:
        """Extract all URLs from text.
        
        Implements Requirement 13.5: URL extraction
        
        Args:
            text: The text to extract URLs from
            
        Returns:
            List of URLs found in the text
        """
        # Pattern to match http/https URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        return urls

    def extract_statistics(self, text: str) -> List[Dict[str, Any]]:
        """Extract statistical claims from text.
        
        Implements Requirement 13.5: Statistics extraction
        
        Extracts numbers with units like percentages, millions, billions, etc.
        
        Args:
            text: The text to extract statistics from
            
        Returns:
            List of dictionaries containing value, unit, and context
        """
        statistics = []
        
        # Pattern to match numbers with units
        # Matches: "50%", "5 million", "3.2 billion", "75 percent", etc.
        # Updated to handle punctuation after units like "50%!" or "5 million."
        stat_pattern = r'(\d+(?:\.\d+)?)\s*(%|percent|million|billion|trillion|thousand|crore|lakh|hundred)'
        
        matches = re.finditer(stat_pattern, text, re.IGNORECASE)
        
        for match in matches:
            value = match.group(1)
            unit = match.group(2).lower()
            
            # Get surrounding context (up to 50 chars before and after)
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].strip()
            
            statistics.append({
                'value': value,
                'unit': unit,
                'context': context,
                'full_match': match.group(0)
            })
        
        return statistics

    def extract_quotes(self, text: str) -> List[str]:
        """Extract quoted text from content.
        
        Implements Requirement 13.5: Quote extraction
        
        Extracts text within quotation marks (both straight and curly quotes).
        
        Args:
            text: The text to extract quotes from
            
        Returns:
            List of quoted strings found in the text
        """
        quotes = []
        
        # Pattern to match text within various quote styles
        # Matches: "text", 'text', "text", 'text', «text»
        quote_patterns = [
            r'"([^"]+)"',                      # Double quotes
            r"'([^']+)'",                      # Single quotes
            r'\u201c([^\u201d]+)\u201d',       # Curly double quotes (U+201C and U+201D)
            r'\u2018([^\u2019]+)\u2019',       # Curly single quotes (U+2018 and U+2019)
            r'«([^»]+)»',                      # Guillemets
        ]
        
        for pattern in quote_patterns:
            matches = re.findall(pattern, text)
            quotes.extend(matches)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_quotes = []
        for quote in quotes:
            if quote not in seen:
                seen.add(quote)
                unique_quotes.append(quote)
        
        return unique_quotes
