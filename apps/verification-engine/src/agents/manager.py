"""
Manager Agent — LangGraph Orchestration
"""
import asyncio
import json
import time
import uuid
import logging
from datetime import datetime
from typing import TypedDict, Annotated, Sequence
import operator

from langgraph.graph import StateGraph, END

from src.normalization import NormalizationLayer
from src.integrations.bedrock import invoke_bedrock
from src.agents import (
    ResearchAgent, NewsAgent, ScientificAgent,
    SocialMediaAgent, SentimentAgent, ScraperAgent, FactCheckAgent
)
from src.services.scorer import CredibilityScorer
from src.services.evidence import EvidenceAggregator
from src.services.report import ReportGenerator
from src.models.verification import VerificationRequest, VerificationResult, ClaimType

logger = logging.getLogger(__name__)

# Agent registry
AGENT_REGISTRY = {
    'research': ResearchAgent(),
    'news': NewsAgent(),
    'scientific': ScientificAgent(),
    'social_media': SocialMediaAgent(),
    'sentiment': SentimentAgent(),
    'scraper': ScraperAgent(),
    'factcheck': FactCheckAgent(),  # Agent 7: Official professional fact-checker database
}

# Domain → agents mapping
DOMAIN_AGENTS = {
    'politics':      ['news', 'social_media', 'research', 'sentiment', 'factcheck'],
    'health':        ['scientific', 'news', 'research', 'factcheck'],
    'science':       ['scientific', 'research', 'factcheck'],
    'technology':    ['news', 'research', 'factcheck'],
    'climate':       ['scientific', 'news', 'research', 'factcheck'],
    'sports':        ['news', 'social_media', 'factcheck'],
    'entertainment': ['news', 'social_media', 'factcheck'],
    'business':      ['news', 'research', 'factcheck'],
    'default':       ['research', 'news', 'social_media', 'factcheck'],
}


class AgentState(TypedDict):
    """State passed through the graph."""
    request: dict
    normalized: dict
    claim_analysis: dict
    selected_agents: list[str]
    agent_results: Annotated[Sequence[dict], operator.add]
    evidence: dict
    credibility: dict
    report: dict
    errors: Annotated[Sequence[str], operator.add]


class ManagerAgent:
    """Orchestrates the multi-agent verification pipeline."""

    def __init__(self):
        self.normalizer = NormalizationLayer()
        self.scorer = CredibilityScorer()
        self.aggregator = EvidenceAggregator()
        self.reporter = ReportGenerator()
        self.graph = self._build_graph()

    def _build_graph(self):
        """Build LangGraph state machine."""
        g = StateGraph(AgentState)
        
        # Add nodes
        g.add_node("normalize", self._normalize_node)
        g.add_node("analyze_claim", self._analyze_claim_node)
        g.add_node("select_agents", self._select_agents_node)
        g.add_node("execute_agents", self._execute_agents_node)
        g.add_node("aggregate_evidence", self._aggregate_evidence_node)
        g.add_node("calculate_credibility", self._calculate_credibility_node)
        g.add_node("generate_report", self._generate_report_node)
        
        # Define edges
        g.set_entry_point("normalize")
        g.add_edge("normalize", "analyze_claim")
        g.add_edge("analyze_claim", "select_agents")
        g.add_edge("select_agents", "execute_agents")
        g.add_edge("execute_agents", "aggregate_evidence")
        g.add_edge("aggregate_evidence", "calculate_credibility")
        g.add_edge("calculate_credibility", "generate_report")
        g.add_edge("generate_report", END)
        
        return g.compile()

    async def verify(self, request: VerificationRequest) -> VerificationResult:
        """Main verification entry point."""
        start_time = time.time()
        
        initial_state: AgentState = {
            "request": request.model_dump(),
            "normalized": {},
            "claim_analysis": {},
            "selected_agents": [],
            "agent_results": [],
            "evidence": {},
            "credibility": {},
            "report": {},
            "errors": [],
        }
        
        try:
            final_state = await self.graph.ainvoke(initial_state)
        except Exception as e:
            logger.error(f"Manager Agent failed: {e}", exc_info=True)
            raise
        
        processing_time = time.time() - start_time
        
        # Build final result
        return VerificationResult(
            id=str(uuid.uuid4()),
            credibility_score=final_state['credibility'].get('score', 0),
            category=final_state['credibility'].get('category', 'Insufficient Evidence'),
            confidence=final_state['credibility'].get('confidence', 'Low'),
            claim_type=ClaimType(final_state['claim_analysis'].get('type', 'mixed')),
            sources_consulted=final_state['evidence'].get('total_sources', 0),
            agent_consensus=final_state['credibility'].get('consensus', 'No consensus'),
            evidence_summary=final_state['evidence'].get('summary', {}),
            sources=final_state['evidence'].get('sources', []),
            agent_verdicts=final_state['report'].get('agent_verdicts', {}),
            limitations=final_state['report'].get('limitations', []),
            recommendation=final_state['report'].get('recommendation', ''),
            processing_time=round(processing_time, 2),
            created_at=datetime.utcnow().isoformat(),
        )

    # ── Node Implementations ──────────────────────────────────────

    async def _normalize_node(self, state: AgentState) -> dict:
        """Normalization Layer — text norm, metadata, language."""
        logger.info("Node: normalize")
        try:
            normalized = await self.normalizer.process(state['request'])
            return {"normalized": normalized}
        except Exception as e:
            logger.error(f"Normalization failed: {e}")
            return {"normalized": state['request'], "errors": [str(e)]}

    async def _analyze_claim_node(self, state: AgentState) -> dict:
        """Analyze claim to extract entities, type, domain."""
        logger.info("Node: analyze_claim")
        
        claim = state['normalized'].get('normalized_content', state['request']['content'])
        
        prompt = f"""Analyze this claim. Return ONLY valid JSON (no markdown):
{{
  "main_assertion": "<one sentence>",
  "entities": ["<entity1>", "<entity2>"],
  "type": "factual|statistical|quote|prediction|opinion|mixed",
  "domain": "politics|health|science|technology|climate|sports|entertainment|business|general",
  "verification_scope": "<what needs checking>"
}}

Claim: {claim}"""

        try:
            response = await invoke_bedrock('manager', prompt)
            # Strip markdown code fences
            response = response.strip().replace('```json', '').replace('```', '')
            analysis = json.loads(response)
        except Exception as e:
            logger.warning(f"Claim analysis failed: {e}")
            analysis = {
                "domain": "general",
                "type": "mixed",
                "entities": [],
                "main_assertion": claim[:100],
                "verification_scope": "General verification",
            }
        
        return {"claim_analysis": analysis}

    async def _select_agents_node(self, state: AgentState) -> dict:
        """Select which agents to run based on claim domain."""
        logger.info("Node: select_agents")
        
        domain = state['claim_analysis'].get('domain', 'default')
        agents = set(DOMAIN_AGENTS.get(domain, DOMAIN_AGENTS['default']))
        
        # Always include: sentiment (manipulation) + factcheck (official truth DB)
        agents.add('sentiment')
        agents.add('factcheck')
        
        # Add scraper if URL detected
        meta = state['normalized'].get('metadata', {})
        if meta.get('is_url'):
            agents.add('scraper')
        
        # Add scientific for health/science/climate
        if domain in ('health', 'science', 'climate'):
            agents.add('scientific')
        
        # Add research for statistical claims
        if state['claim_analysis'].get('type') == 'statistical':
            agents.add('research')
        
        logger.info(f"Selected agents: {sorted(agents)}")
        return {"selected_agents": list(agents)}

    async def _execute_agents_node(self, state: AgentState) -> dict:
        """Execute all selected agents in parallel."""
        logger.info("Node: execute_agents")
        
        claim = state['normalized'].get('normalized_content', state['request']['content'])
        analysis = state['claim_analysis']
        
        import os
        timeout = float(os.getenv('MAX_AGENT_TIMEOUT', '10'))
        
        async def run_agent(name: str):
            """Run single agent with timeout."""
            try:
                agent = AGENT_REGISTRY[name]
                result = await asyncio.wait_for(
                    agent.investigate(claim, analysis),
                    timeout=timeout
                )
                logger.info(f"Agent {name} completed: {result.get('verdict')}")
                return result
            except asyncio.TimeoutError:
                logger.warning(f"Agent {name} timed out")
                return {
                    "agent": name,
                    "verdict": "insufficient",
                    "confidence": 0.0,
                    "summary": f"Agent timed out after {timeout}s",
                    "sources": [],
                    "error": "timeout",
                }
            except Exception as e:
                logger.error(f"Agent {name} failed: {e}")
                return {
                    "agent": name,
                    "verdict": "insufficient",
                    "confidence": 0.0,
                    "summary": f"Agent error: {str(e)[:100]}",
                    "sources": [],
                    "error": str(e)[:200],
                }
        
        results = await asyncio.gather(*[
            run_agent(name) for name in state['selected_agents']
        ])
        
        return {"agent_results": list(results)}

    async def _aggregate_evidence_node(self, state: AgentState) -> dict:
        """Aggregate evidence from all agents."""
        logger.info("Node: aggregate_evidence")
        evidence = self.aggregator.aggregate(state['agent_results'])
        return {"evidence": evidence}

    async def _calculate_credibility_node(self, state: AgentState) -> dict:
        """Calculate credibility score."""
        logger.info("Node: calculate_credibility")
        evidence = state['evidence']
        sources = evidence.get('sources', [])
        evidence_summary = evidence.get('summary', {})

        score, category, confidence = self.scorer.calculate(
            agent_results=state['agent_results'],
            sources=sources,
            evidence_summary=evidence_summary,
        )

        # Build agent consensus string
        from collections import Counter
        verdicts = [r.get('verdict', 'insufficient') for r in state['agent_results']
                    if r.get('verdict') not in ('insufficient', None)]
        if verdicts:
            most_common, count = Counter(verdicts).most_common(1)[0]
            consensus = f"{most_common} ({count}/{len(verdicts)} agents agree)"
        else:
            consensus = "No consensus reached"

        return {"credibility": {
            "score": score,
            "category": category,
            "confidence": confidence,
            "consensus": consensus,
        }}

    async def _generate_report_node(self, state: AgentState) -> dict:
        """Generate final report."""
        logger.info("Node: generate_report")
        report = await self.reporter.generate(
            claim=state['request']['content'],
            analysis=state['claim_analysis'],
            evidence=state['evidence'],
            credibility=state['credibility'],
            agent_results=state['agent_results'],
        )
        return {"report": report}
