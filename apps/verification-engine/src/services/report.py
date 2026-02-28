"""
Report Generation Service
"""
import logging
from typing import Dict, Any, List
from src.integrations.bedrock import invoke_bedrock

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate human-readable reports and recommendations."""

    async def generate(
        self, 
        claim: str, 
        analysis: dict, 
        evidence: dict, 
        credibility: dict, 
        agent_results: list
    ) -> dict:
        """
        Generate final report with agent verdicts, limitations, and recommendation.
        
        Returns:
            {
                'agent_verdicts': {agent_name: AgentVerdict, ...},
                'limitations': ['list of transparency disclosures'],
                'recommendation': 'One paragraph human-readable guidance'
            }
        """
        # Serialize agent verdicts
        agent_verdicts = self._serialize_agent_verdicts(agent_results)
        
        # Generate limitations
        limitations = self._generate_limitations(agent_results, evidence, credibility)
        
        # Generate recommendation
        recommendation = await self._generate_recommendation(
            claim, credibility, evidence, agent_results
        )
        
        return {
            'agent_verdicts': agent_verdicts,
            'limitations': limitations,
            'recommendation': recommendation,
        }

    def _serialize_agent_verdicts(self, agent_results: list) -> dict:
        """Convert agent results to AgentVerdict format."""
        verdicts = {}
        
        for result in agent_results:
            agent_name = result.get('agent', 'unknown')
            verdicts[agent_name] = {
                'verdict': result.get('verdict', 'insufficient'),
                'confidence': result.get('confidence', 0.0),
                'summary': result.get('summary', ''),
                'sources_count': len(result.get('sources', [])),
                'error': result.get('error'),
            }
        
        return verdicts

    def _generate_limitations(
        self, 
        agent_results: list, 
        evidence: dict, 
        credibility: dict
    ) -> List[str]:
        """Auto-generate transparency limitations."""
        limitations = []
        
        # Check for low confidence agents
        low_confidence_agents = [
            r.get('agent') for r in agent_results 
            if r.get('confidence', 0) < 0.5
        ]
        if low_confidence_agents:
            limitations.append(
                f"Low confidence from agents: {', '.join(low_confidence_agents)}"
            )
        
        # Check for insufficient sources
        total_sources = evidence.get('total_sources', 0)
        if total_sources < 10:
            limitations.append(
                f"Limited sources available ({total_sources} sources consulted)"
            )
        
        # Check for agent errors
        failed_agents = [
            r.get('agent') for r in agent_results 
            if r.get('error')
        ]
        if failed_agents:
            limitations.append(
                f"Some agents encountered errors: {', '.join(failed_agents)}"
            )
        
        # Check for low overall confidence
        if credibility.get('confidence') == 'Low':
            limitations.append(
                "Overall confidence is low - results should be interpreted cautiously"
            )
        
        # Check for mixed evidence
        summary = evidence.get('summary', {})
        if summary.get('supporting', 0) > 0 and summary.get('contradicting', 0) > 0:
            limitations.append(
                "Mixed evidence found - some sources support while others contradict"
            )
        
        return limitations if limitations else ['No significant limitations identified']

    async def _generate_recommendation(
        self, 
        claim: str, 
        credibility: dict, 
        evidence: dict, 
        agent_results: list
    ) -> str:
        """Generate LLM-based recommendation paragraph."""
        score = credibility.get('score', 50)
        category = credibility.get('category', 'Mixed Evidence')
        consensus = credibility.get('consensus', 'No consensus')
        total_sources = evidence.get('total_sources', 0)
        
        # Build context for LLM
        agent_summaries = '\n'.join([
            f"- {r.get('agent')}: {r.get('summary', 'No summary')}"
            for r in agent_results
            if r.get('summary')
        ])
        
        prompt = f"""Generate a clear, actionable recommendation for this fact-check result.

Claim: {claim}

Credibility Score: {score}/100 ({category})
Agent Consensus: {consensus}
Sources Consulted: {total_sources}

Agent Summaries:
{agent_summaries}

Write ONE paragraph (2-3 sentences) with:
1. Clear verdict on claim accuracy
2. Key evidence supporting the verdict
3. Actionable guidance for the user

Be direct, factual, and helpful. No markdown, just plain text."""

        try:
            recommendation = await invoke_bedrock('manager', prompt)
            # Clean up any markdown or extra formatting
            recommendation = recommendation.strip().replace('**', '').replace('*', '')
            return recommendation
        except Exception as e:
            logger.warning(f"LLM recommendation generation failed: {e}")
            return self._fallback_recommendation(score, category, total_sources)

    def _fallback_recommendation(self, score: int, category: str, total_sources: int) -> str:
        """Generate fallback recommendation without LLM."""
        if score >= 70:
            return (
                f"This claim is rated as '{category}' based on {total_sources} sources. "
                f"The evidence strongly supports the accuracy of this claim. "
                f"You can share this information with confidence."
            )
        elif score >= 40:
            return (
                f"This claim is rated as '{category}' based on {total_sources} sources. "
                f"The evidence is mixed or inconclusive. "
                f"Exercise caution and seek additional verification before sharing."
            )
        else:
            return (
                f"This claim is rated as '{category}' based on {total_sources} sources. "
                f"The evidence strongly contradicts this claim. "
                f"Avoid sharing this information as it appears to be false or misleading."
            )
