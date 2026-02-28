"""
Evidence Aggregation Service
"""
import logging
from typing import List, Dict, Any
from urllib.parse import urlparse, urlunparse

logger = logging.getLogger(__name__)


class EvidenceAggregator:
    """Aggregate evidence from all agent results."""

    def normalize_url(self, url: str) -> str:
        """
        Normalize URL for deduplication.
        
        Removes query parameters, fragments, trailing slashes, and lowercases domain.
        
        Args:
            url: The URL to normalize
            
        Returns:
            Normalized URL string
        """
        try:
            parsed = urlparse(url)
            # Remove query params and fragment, lowercase domain, remove trailing slash
            normalized = urlunparse((
                parsed.scheme,
                parsed.netloc.lower(),
                parsed.path.rstrip('/'),
                '', '', ''
            ))
            return normalized
        except Exception as e:
            logger.warning(f"Failed to normalize URL {url}: {e}")
            return url

    def aggregate(self, agent_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge all agent results into unified evidence object.
        
        Returns:
            {
                'sources': [...all sources deduped by URL...],
                'summary': {'supporting': N, 'contradicting': N, 'neutral': N},
                'total_sources': N,
                'agent_coverage': {'total': N, 'successful': N, 'failed': N, 'success_rate': float}
            }
        """
        all_sources = []
        agent_source_counts = {}
        
        # Collect all sources from agents
        for result in agent_results:
            agent_name = result.get('agent', 'unknown')
            sources = result.get('sources', [])
            
            agent_source_counts[agent_name] = len(sources)
            
            for source in sources:
                all_sources.append(source)
        
        # Deduplicate sources by URL (keep highest credibility score)
        deduped_sources = self._deduplicate_sources(all_sources)
        
        # Sort by credibility score descending
        deduped_sources.sort(key=lambda s: s.get('credibility_score', 0), reverse=True)
        
        # Count stances AFTER deduplication
        stance_counts = {'supporting': 0, 'contradicting': 0, 'neutral': 0}
        for source in deduped_sources:
            stance = source.get('stance', 'neutral')
            if stance in stance_counts:
                stance_counts[stance] += 1
        
        # Calculate agent coverage statistics
        agent_coverage = self.calculate_agent_coverage(agent_results)
        
        return {
            'sources': deduped_sources,
            'summary': stance_counts,
            'total_sources': len(deduped_sources),
            'agent_coverage': agent_coverage,
            'agent_source_counts': agent_source_counts,
        }

    def calculate_agent_coverage(self, agent_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate agent participation statistics.
        
        Args:
            agent_results: List of agent result dictionaries
            
        Returns:
            Dictionary with total, successful, failed, and success_rate
        """
        total_agents = len(agent_results)
        successful_agents = len([
            r for r in agent_results 
            if r.get('verdict', 'insufficient') != 'insufficient'
        ])
        failed_agents = total_agents - successful_agents
        
        return {
            'total': total_agents,
            'successful': successful_agents,
            'failed': failed_agents,
            'success_rate': (successful_agents / total_agents * 100) if total_agents > 0 else 0
        }

    def _deduplicate_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate sources by normalized URL, keeping highest credibility."""
        url_map: Dict[str, Dict[str, Any]] = {}
        
        for source in sources:
            url = source.get('url', '')
            if not url:
                continue
            
            # Normalize URL for deduplication
            normalized_url = self.normalize_url(url)
            
            # Keep source with highest credibility score
            if normalized_url not in url_map:
                url_map[normalized_url] = source
            else:
                existing_score = url_map[normalized_url].get('credibility_score', 0)
                new_score = source.get('credibility_score', 0)
                if new_score > existing_score:
                    url_map[normalized_url] = source
        
        return list(url_map.values())
