# ZeroTRUST Development Plan
**Complete Implementation Roadmap**  
**Target:** Production-Ready System  
**Timeline:** 12 Days (Hackathon Sprint)

---

## Overview

This plan provides a step-by-step guide to complete the ZeroTRUST project from its current 45% state to a fully functional, production-ready system.

**Current State:** 45% complete (prototype phase)  
**Target State:** 100% complete with all features functional  
**Approach:** Agile sprints with daily milestones

---

## Phase Breakdown

### Phase 1: Critical Backend (Days 1-3) - PRIORITY 🔴
### Phase 2: API Integration (Days 4-5)
### Phase 3: Media Analysis (Days 6-7)
### Phase 4: Client Applications (Days 8-9)
### Phase 5: AWS Deployment (Day 10)
### Phase 6: Testing & Polish (Days 11-12)

---

## DAY 1: Verification Engine Core

**Goal:** Make verification engine functional end-to-end

### Morning (4 hours)

**Task 1.1: Implement Normalization Layer** (2h)
```bash
cd apps/verification-engine/src/normalization
```

Create `text_normalizer.py`:

```python
import re
import unicodedata
import html

class TextNormalizer:
    STOP_WORDS = frozenset([
        'a','an','the','is','are','was','were','be','been','being',
        'have','has','had','do','does','did','will','would','could',
        'should','may','might','shall','can','of','in','at','by','for',
        'with','about','as','from','that','this','it','its'
    ])
    
    def normalize(self, text: str) -> str:
        text = html.unescape(text)
        text = re.sub(r'<[^>]+>', '', text)
        text = unicodedata.normalize('NFC', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def to_cache_key(self, text: str) -> str:
        normalized = self.normalize(text).lower()
        import string
        normalized = normalized.translate(str.maketrans('', '', string.punctuation))
        tokens = [w for w in normalized.split() if w not in self.STOP_WORDS]
        return ' '.join(sorted(tokens))
```

Create `metadata_extractor.py`:
```python
import re
from urllib.parse import urlparse

class MetadataExtractor:
    def extract(self, content: str, claim_type: str) -> dict:
        return {
            'is_url': bool(re.match(r'https?://', content.strip())),
            'has_numbers': bool(re.search(r'\d+\.?\d*%?', content)),
            'has_quote_markers': bool(re.search(r'["\'"]', content)),
            'word_count': len(content.split()),
            'contains_statistics': bool(re.search(
                r'\d+\.?\d*\s*(%|percent|million|billion|crore|lakh)', 
                content, re.I
            )),
            'source_domain': self._extract_domain(content) if content.startswith('http') else None
        }
    
    def _extract_domain(self, url: str) -> str:
        try:
            return urlparse(url).netloc
        except:
            return None
```

Create `language_detector.py`:
```python
import langdetect
from langdetect.lang_detect_exception import LangDetectException

class LanguageDetector:
    SUPPORTED = {'en', 'hi', 'mr', 'ta', 'te', 'bn', 'gu', 'kn', 'ml', 'pa'}
    
    def detect(self, text: str) -> str:
        try:
            lang = langdetect.detect(text[:200])
            return lang if lang in self.SUPPORTED else 'en'
        except LangDetectException:
            return 'en'
```

Create `__init__.py`:
```python
from .text_normalizer import TextNormalizer
from .metadata_extractor import MetadataExtractor
from .language_detector import LanguageDetector

class NormalizationLayer:
    def __init__(self):
        self.text_norm = TextNormalizer()
        self.meta_extract = MetadataExtractor()
        self.lang_detect = LanguageDetector()
    
    async def process(self, request: dict) -> dict:
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
```

**Task 1.2: Implement Credibility Scorer** (2h)

Create `apps/verification-engine/src/services/scorer.py`:
```python
class CredibilityScorer:
    AGENT_WEIGHTS = {
        'news': 0.25,
        'scientific': 0.25,
        'research': 0.20,
        'social_media': 0.10,
        'sentiment': 0.10,
        'scraper': 0.10
    }
    
    def calculate(self, evidence: dict, agent_results: list, claim_analysis: dict) -> dict:
        # Base score from agent verdicts
        base_score = self._calculate_base_score(agent_results)
        
        # Evidence strength multiplier
        total_sources = evidence.get('total_sources', 0)
        evidence_multiplier = min(1.0, total_sources / 30)
        
        # Conflict penalty
        conflict_penalty = self._calculate_conflict(agent_results) * 0.15
        
        # Diversity bonus
        diversity_bonus = self._calculate_diversity(evidence) * 0.10
        
        # Final score
        final_score = int(max(0, min(100, 
            (base_score * evidence_multiplier) - conflict_penalty + diversity_bonus
        )))
        
        return {
            'score': final_score,
            'category': self._score_to_category(final_score),
            'confidence': self._calculate_confidence(agent_results, total_sources),
            'consensus': self._calculate_consensus(agent_results)
        }
    
    def _calculate_base_score(self, agent_results: list) -> float:
        score = 0.0
        for result in agent_results:
            agent_name = result.get('agent', '').replace('_agent', '')
            weight = self.AGENT_WEIGHTS.get(agent_name, 0.10)
            verdict = result.get('verdict', 'insufficient')
            confidence = result.get('confidence', 0.0)
            
            verdict_score = {
                'supports': 100,
                'contradicts': 0,
                'mixed': 50,
                'insufficient': 50
            }.get(verdict, 50)
            
            score += verdict_score * weight * confidence
        
        return score
    
    def _score_to_category(self, score: int) -> str:
        if score >= 85: return 'Verified True'
        if score >= 70: return 'Likely True'
        if score >= 55: return 'Mixed Evidence'
        if score >= 40: return 'Likely False'
        return 'Verified False'
    
    def _calculate_confidence(self, agent_results: list, total_sources: int) -> str:
        avg_confidence = sum(r.get('confidence', 0) for r in agent_results) / max(len(agent_results), 1)
        if avg_confidence > 0.8 and total_sources > 20: return 'High'
        if avg_confidence > 0.6 and total_sources > 10: return 'Medium'
        return 'Low'
    
    def _calculate_consensus(self, agent_results: list) -> str:
        verdicts = [r.get('verdict') for r in agent_results if r.get('verdict') != 'insufficient']
        if not verdicts: return 'No consensus'
        
        from collections import Counter
        counts = Counter(verdicts)
        most_common = counts.most_common(1)[0]
        percentage = (most_common[1] / len(verdicts)) * 100
        
        return f"{most_common[0].title()} consensus ({percentage:.0f}%)"
    
    def _calculate_conflict(self, agent_results: list) -> float:
        supports = sum(1 for r in agent_results if r.get('verdict') == 'supports')
        contradicts = sum(1 for r in agent_results if r.get('verdict') == 'contradicts')
        total = len(agent_results)
        if total == 0: return 0.0
        return abs(supports - contradicts) / total
    
    def _calculate_diversity(self, evidence: dict) -> float:
        source_types = set()
        for source in evidence.get('sources', []):
            source_types.add(source.get('source_type', 'unknown'))
        return min(1.0, len(source_types) / 5)
```

### Afternoon (4 hours)

**Task 1.3: Implement Evidence Aggregator** (1h)

Create `apps/verification-engine/src/services/evidence.py`:
```python
class EvidenceAggregator:
    def aggregate(self, agent_results: list) -> dict:
        all_sources = []
        seen_urls = set()
        
        for result in agent_results:
            for source in result.get('sources', []):
                url = source.get('url', '')
                if url and url not in seen_urls:
                    all_sources.append(source)
                    seen_urls.add(url)
        
        # Sort by credibility score
        all_sources.sort(key=lambda s: s.get('credibility_score', 0), reverse=True)
        
        # Count stances
        supporting = sum(1 for s in all_sources if s.get('stance') == 'supporting')
        contradicting = sum(1 for s in all_sources if s.get('stance') == 'contradicting')
        neutral = sum(1 for s in all_sources if s.get('stance') == 'neutral')
        
        # Agent coverage
        coverage = {}
        for result in agent_results:
            agent = result.get('agent', 'unknown')
            coverage[agent] = len(result.get('sources', []))
        
        return {
            'sources': all_sources,
            'summary': {
                'supporting': supporting,
                'contradicting': contradicting,
                'neutral': neutral
            },
            'total_sources': len(all_sources),
            'agent_coverage': coverage
        }
```

**Task 1.4: Implement Report Generator** (1h)

Create `apps/verification-engine/src/services/report.py`:
```python
from src.integrations.bedrock import invoke_bedrock

class ReportGenerator:
    async def generate(self, claim: str, analysis: dict, evidence: dict, 
                      credibility: dict, agent_results: list) -> dict:
        # Serialize agent verdicts
        verdicts = {}
        for result in agent_results:
            agent = result.get('agent', 'unknown')
            verdicts[agent] = {
                'verdict': result.get('verdict'),
                'confidence': result.get('confidence'),
                'summary': result.get('summary'),
                'sources_count': len(result.get('sources', [])),
                'error': result.get('error')
            }
        
        # Generate limitations
        limitations = self._generate_limitations(agent_results, evidence, credibility)
        
        # Generate recommendation
        recommendation = await self._generate_recommendation(
            claim, credibility, evidence, agent_results
        )
        
        return {
            'agent_verdicts': verdicts,
            'limitations': limitations,
            'recommendation': recommendation
        }
    
    def _generate_limitations(self, agent_results: list, evidence: dict, 
                             credibility: dict) -> list:
        limitations = []
        
        # Low confidence
        if credibility.get('confidence') == 'Low':
            limitations.append("Low confidence due to limited sources or agent disagreement")
        
        # Few sources
        total = evidence.get('total_sources', 0)
        if total < 10:
            limitations.append(f"Only {total} sources consulted - more verification recommended")
        
        # Agent errors
        failed = [r.get('agent') for r in agent_results if r.get('error')]
        if failed:
            limitations.append(f"Some agents failed: {', '.join(failed)}")
        
        # Recent claim
        if 'recent' in str(evidence).lower():
            limitations.append("Claim is recent - await independent verification")
        
        return limitations
    
    async def _generate_recommendation(self, claim: str, credibility: dict,
                                      evidence: dict, agent_results: list) -> str:
        prompt = f"""Generate a 2-sentence recommendation for this fact-check result.

Claim: {claim}
Score: {credibility.get('score')}/100
Category: {credibility.get('category')}
Sources: {evidence.get('total_sources')} consulted
Evidence: {evidence.get('summary')}

Write a clear, actionable recommendation for the user."""
        
        try:
            return await invoke_bedrock('manager', prompt)
        except:
            score = credibility.get('score', 50)
            if score >= 70:
                return "This claim appears to be accurate based on multiple credible sources. However, always verify important information independently."
            elif score >= 40:
                return "This claim has mixed evidence. Exercise caution and seek additional verification before sharing or acting on it."
            else:
                return "This claim appears to be false or misleading based on available evidence. Do not share without verification."
```

**Task 1.5: Implement Manager Agent** (2h)

Create `apps/verification-engine/src/agents/manager.py`:
