"""
Test script to verify a specific claim and display results.
"""
import sys
sys.path.insert(0, 'apps/verification-engine')

from src.normalization.text_normalizer import TextNormalizer
from src.normalization.metadata_extractor import MetadataExtractor
from src.normalization.language_detector import LanguageDetector
from src.services.scorer import CredibilityScorer
from src.services.evidence import EvidenceAggregator
import hashlib
import json


def test_claim_verification():
    """Test the verification pipeline with a specific claim."""
    
    # The claim to verify
    claim = "raul gandhi has been elected as indan prime minister"
    
    print("=" * 80)
    print("ZEROTRUST CLAIM VERIFICATION TEST")
    print("=" * 80)
    print(f"\nOriginal Claim: {claim}")
    print("-" * 80)
    
    # Step 1: Text Normalization
    print("\n[STEP 1] TEXT NORMALIZATION")
    normalizer = TextNormalizer()
    normalized_claim = normalizer.normalize(claim)
    claim_hash = hashlib.sha256(normalized_claim.encode()).hexdigest()[:32]
    
    print(f"Normalized Text: {normalized_claim}")
    print(f"Claim Hash: {claim_hash}")
    
    # Step 2: Metadata Extraction
    print("\n[STEP 2] METADATA EXTRACTION")
    extractor = MetadataExtractor()
    metadata = extractor.extract(claim)
    
    print(f"URLs Found: {metadata.get('urls', [])}")
    print(f"Statistics Found: {metadata.get('statistics', [])}")
    print(f"Quotes Found: {metadata.get('quotes', [])}")
    
    # Step 3: Language Detection
    print("\n[STEP 3] LANGUAGE DETECTION")
    detector = LanguageDetector()
    language = detector.detect(claim)
    
    print(f"Detected Language: {language}")
    
    # Step 4: Mock Agent Results (simulating what agents would return)
    print("\n[STEP 4] SIMULATED AGENT RESULTS")
    print("(In production, this would query 6 specialist agents)")
    
    # Simulate agent results for this false claim
    agent_results = [
        {
            'agent': 'news',
            'verdict': 'contradicting',
            'confidence': 0.95,
            'summary': 'No credible news sources report Rahul Gandhi as Prime Minister. Current PM is Narendra Modi.',
            'sources': [
                {
                    'url': 'https://timesofindia.com/india/current-pm',
                    'title': 'Narendra Modi continues as Prime Minister of India',
                    'excerpt': 'Prime Minister Narendra Modi leads the government...',
                    'credibility_tier': 'tier_1',
                    'credibility_score': 0.95,
                    'stance': 'contradicting',
                    'source_type': 'news'
                },
                {
                    'url': 'https://indianexpress.com/politics/pm-modi',
                    'title': 'PM Modi addresses nation',
                    'excerpt': 'Prime Minister Modi announced...',
                    'credibility_tier': 'tier_1',
                    'credibility_score': 0.93,
                    'stance': 'contradicting',
                    'source_type': 'news'
                },
                {
                    'url': 'https://hindustantimes.com/india-news/rahul-gandhi-opposition',
                    'title': 'Rahul Gandhi leads opposition in Parliament',
                    'excerpt': 'Opposition leader Rahul Gandhi...',
                    'credibility_tier': 'tier_1',
                    'credibility_score': 0.92,
                    'stance': 'contradicting',
                    'source_type': 'news'
                }
            ]
        },
        {
            'agent': 'research',
            'verdict': 'contradicting',
            'confidence': 0.98,
            'summary': 'Official government records show Narendra Modi as current PM since 2014.',
            'sources': [
                {
                    'url': 'https://pmindia.gov.in',
                    'title': 'Prime Minister of India - Official Website',
                    'excerpt': 'Shri Narendra Modi is the 14th Prime Minister of India...',
                    'credibility_tier': 'tier_1',
                    'credibility_score': 1.0,
                    'stance': 'contradicting',
                    'source_type': 'general'
                },
                {
                    'url': 'https://eci.gov.in/election-results',
                    'title': 'Election Commission of India - Results',
                    'excerpt': 'BJP-led NDA won majority, Modi sworn in as PM...',
                    'credibility_tier': 'tier_1',
                    'credibility_score': 0.98,
                    'stance': 'contradicting',
                    'source_type': 'general'
                }
            ]
        },
        {
            'agent': 'social_media',
            'verdict': 'contradicting',
            'confidence': 0.85,
            'summary': 'Social media posts confirm Modi as PM, no credible claims about Rahul Gandhi.',
            'sources': [
                {
                    'url': 'https://twitter.com/narendramodi/status/123',
                    'title': 'PM Modi Official Twitter',
                    'excerpt': 'As Prime Minister, I am committed to...',
                    'credibility_tier': 'tier_2',
                    'credibility_score': 0.85,
                    'stance': 'contradicting',
                    'source_type': 'social'
                },
                {
                    'url': 'https://twitter.com/PMOIndia/status/456',
                    'title': 'PMO India Official',
                    'excerpt': 'PM @narendramodi inaugurates...',
                    'credibility_tier': 'tier_2',
                    'credibility_score': 0.88,
                    'stance': 'contradicting',
                    'source_type': 'social'
                }
            ]
        },
        {
            'agent': 'sentiment',
            'verdict': 'contradicting',
            'confidence': 0.80,
            'summary': 'Public sentiment analysis shows no support for this claim.',
            'sources': [
                {
                    'url': 'https://reddit.com/r/india/comments/pm-discussion',
                    'title': 'Discussion about current PM',
                    'excerpt': 'Modi is the current PM, this is well established...',
                    'credibility_tier': 'tier_3',
                    'credibility_score': 0.70,
                    'stance': 'contradicting',
                    'source_type': 'social'
                }
            ]
        }
    ]
    
    for result in agent_results:
        print(f"\n  Agent: {result['agent']}")
        print(f"  Verdict: {result['verdict']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Sources: {len(result['sources'])}")
    
    # Step 5: Evidence Aggregation
    print("\n[STEP 5] EVIDENCE AGGREGATION")
    aggregator = EvidenceAggregator()
    aggregated = aggregator.aggregate(agent_results)
    
    print(f"Total Sources (after deduplication): {aggregated['total_sources']}")
    print(f"Evidence Summary:")
    print(f"  - Supporting: {aggregated['summary']['supporting']}")
    print(f"  - Contradicting: {aggregated['summary']['contradicting']}")
    print(f"  - Neutral: {aggregated['summary']['neutral']}")
    print(f"\nAgent Coverage:")
    print(f"  - Total Agents: {aggregated['agent_coverage']['total']}")
    print(f"  - Successful: {aggregated['agent_coverage']['successful']}")
    print(f"  - Failed: {aggregated['agent_coverage']['failed']}")
    print(f"  - Success Rate: {aggregated['agent_coverage']['success_rate']:.1f}%")
    
    # Step 6: Credibility Scoring
    print("\n[STEP 6] CREDIBILITY SCORING")
    scorer = CredibilityScorer()
    score, category, confidence = scorer.calculate(
        agent_results,
        aggregated['sources'],
        aggregated['summary']
    )
    
    print(f"Credibility Score: {score}/100")
    print(f"Category: {category}")
    print(f"Confidence Level: {confidence}")
    
    # Step 7: Scoring Formula
    print("\n[STEP 7] SCORING FORMULA")
    print("Formula: (Evidence Quality × 0.4) + (Agent Consensus × 0.3) + (Source Reliability × 0.3)")
    print("Components:")
    print("  - Evidence Quality: Weighted by source tier and stance (40%)")
    print("  - Agent Consensus: Percentage of agents agreeing (30%)")
    print("  - Source Reliability: Average credibility of sources (30%)")
    print("  - Confidence Penalty: Applied if agent confidence < 0.5")
    
    # Step 8: Top Sources
    print("\n[STEP 8] TOP SOURCES (by credibility)")
    for i, source in enumerate(aggregated['sources'][:5], 1):
        print(f"\n  {i}. {source['title']}")
        print(f"     URL: {source['url']}")
        print(f"     Credibility: {source['credibility_score']:.2f} ({source['credibility_tier']})")
        print(f"     Stance: {source['stance']}")
    
    # Step 9: Final Report Summary
    print("\n" + "=" * 80)
    print("VERIFICATION REPORT SUMMARY")
    print("=" * 80)
    print(f"\nClaim: {claim}")
    print(f"\nVERDICT: {category}")
    print(f"Credibility Score: {score}/100")
    print(f"Confidence: {confidence}")
    print(f"\nSources Consulted: {aggregated['total_sources']}")
    print(f"Agent Consensus: {aggregated['agent_coverage']['success_rate']:.0f}% of agents agree")
    
    print(f"\nEvidence Breakdown:")
    print(f"  ✓ Supporting: {aggregated['summary']['supporting']}")
    print(f"  ✗ Contradicting: {aggregated['summary']['contradicting']}")
    print(f"  ○ Neutral: {aggregated['summary']['neutral']}")
    
    print(f"\nRecommendation:")
    if score < 40:
        print("  This claim is VERIFIED FALSE. Multiple credible sources contradict it.")
        print("  Do NOT trust or share this information.")
    elif score < 60:
        print("  This claim is LIKELY FALSE. Most sources contradict it.")
        print("  Exercise caution and verify with additional sources.")
    elif score < 70:
        print("  This claim is UNCERTAIN. Evidence is mixed or insufficient.")
        print("  Further verification is needed before accepting as fact.")
    elif score < 85:
        print("  This claim is LIKELY TRUE. Most sources support it.")
        print("  Generally trustworthy but verify for critical decisions.")
    else:
        print("  This claim is VERIFIED TRUE. Strong evidence supports it.")
        print("  High confidence in accuracy.")
    
    print("\n" + "=" * 80)
    
    return {
        'claim': claim,
        'normalized_claim': normalized_claim,
        'claim_hash': claim_hash,
        'language': language,
        'metadata': metadata,
        'credibility_score': score,
        'category': category,
        'confidence': confidence,
        'sources_consulted': aggregated['total_sources'],
        'evidence_summary': aggregated['summary'],
        'agent_results': agent_results,
        'aggregated_evidence': aggregated
    }


if __name__ == '__main__':
    result = test_claim_verification()
