/**
 * End-to-End Tests for Claim Verification
 * 
 * This test suite automates browser testing of the claim verification flow,
 * validating that claims are properly analyzed with reasoning, sources,
 * and detailed evidence supporting or denying the claim.
 */

import { test, expect, Page } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:3001';
const API_URL = process.env.API_URL || 'http://localhost:3000';

// Test claims with expected outcomes
const TEST_CLAIMS = [
  {
    claim: "COVID-19 vaccines contain microchips for tracking",
    expectedCategory: "Verified False",
    expectedScoreRange: [0, 20],
    expectedConfidence: "High",
    minSources: 10,
    expectedStance: {
      supporting: { max: 2 },
      contradicting: { min: 8 },
      neutral: { max: 5 }
    },
    expectedAgents: ['research', 'news', 'scientific', 'sentiment'],
    reasoningKeywords: ['false', 'debunked', 'no evidence', 'conspiracy'],
    sourceTypes: ['scientific', 'news', 'fact-check']
  },
  {
    claim: "India launched Chandrayaan-3 moon mission in 2023",
    expectedCategory: "Verified True",
    expectedScoreRange: [80, 100],
    expectedConfidence: "High",
    minSources: 15,
    expectedStance: {
      supporting: { min: 10 },
      contradicting: { max: 2 },
      neutral: { max: 5 }
    },
    expectedAgents: ['research', 'news'],
    reasoningKeywords: ['successful', 'launched', 'ISRO', 'confirmed'],
    sourceTypes: ['news', 'government', 'encyclopedia']
  },
  {
    claim: "5G towers cause health problems",
    expectedCategory: "Likely False",
    expectedScoreRange: [20, 50],
    expectedConfidence: "Medium",
    minSources: 8,
    expectedStance: {
      supporting: { max: 3 },
      contradicting: { min: 5 },
      neutral: { max: 5 }
    },
    expectedAgents: ['research', 'scientific', 'news'],
    reasoningKeywords: ['no evidence', 'studies show', 'WHO', 'radiation'],
    sourceTypes: ['scientific', 'health-organization']
  },
  {
    claim: "The Earth is flat",
    expectedCategory: "Verified False",
    expectedScoreRange: [0, 15],
    expectedConfidence: "High",
    minSources: 10,
    expectedStance: {
      supporting: { max: 1 },
      contradicting: { min: 10 },
      neutral: { max: 3 }
    },
    expectedAgents: ['research', 'scientific'],
    reasoningKeywords: ['spherical', 'proven', 'science', 'evidence'],
    sourceTypes: ['scientific', 'encyclopedia']
  },
  {
    claim: "Climate change is caused by human activities",
    expectedCategory: "Verified True",
    expectedScoreRange: [85, 100],
    expectedConfidence: "High",
    minSources: 15,
    expectedStance: {
      supporting: { min: 12 },
      contradicting: { max: 2 },
      neutral: { max: 3 }
    },
    expectedAgents: ['research', 'scientific', 'news'],
    reasoningKeywords: ['consensus', 'IPCC', 'greenhouse gases', 'evidence'],
    sourceTypes: ['scientific', 'research', 'government']
  }
];

// Helper functions
async function navigateToHomePage(page: Page) {
  await page.goto(BASE_URL);
  await expect(page).toHaveTitle(/ZeroTRUST/i);
}

async function submitClaim(page: Page, claim: string) {
  // Find and fill the claim input
  const claimInput = page.locator('textarea[placeholder*="claim" i], textarea[name="content"]').first();
  await claimInput.fill(claim);
  
  // Click verify button
  const verifyButton = page.locator('button:has-text("Verify"), button:has-text("Check")').first();
  await verifyButton.click();
  
  // Wait for loading to complete
  await page.waitForSelector('[data-testid="loading-spinner"]', { state: 'hidden', timeout: 60000 });
}

async function extractVerificationResult(page: Page) {
  // Wait for results to appear
  await page.waitForSelector('[data-testid="verification-result"], .credibility-score', { timeout: 5000 });
  
  // Extract credibility score
  const scoreElement = page.locator('[data-testid="credibility-score"], .score-value').first();
  const scoreText = await scoreElement.textContent();
  const score = parseInt(scoreText?.match(/\d+/)?.[0] || '0');
  
  // Extract category
  const categoryElement = page.locator('[data-testid="category"], .category-badge').first();
  const category = await categoryElement.textContent();
  
  // Extract confidence
  const confidenceElement = page.locator('[data-testid="confidence"], .confidence-level').first();
  const confidence = await confidenceElement.textContent();
  
  // Extract sources
  const sourceElements = page.locator('[data-testid="source-item"], .source-card');
  const sourceCount = await sourceElements.count();
  
  const sources = [];
  for (let i = 0; i < Math.min(sourceCount, 50); i++) {
    const source = sourceElements.nth(i);
    const title = await source.locator('.source-title, [data-testid="source-title"]').textContent();
    const url = await source.locator('.source-url, [data-testid="source-url"]').textContent();
    const stance = await source.locator('.source-stance, [data-testid="source-stance"]').textContent();
    const excerpt = await source.locator('.source-excerpt, [data-testid="source-excerpt"]').textContent();
    
    sources.push({
      title: title?.trim(),
      url: url?.trim(),
      stance: stance?.trim().toLowerCase(),
      excerpt: excerpt?.trim()
    });
  }
  
  // Extract evidence summary
  const evidenceSummary = {
    supporting: 0,
    contradicting: 0,
    neutral: 0
  };
  
  const supportingElement = page.locator('[data-testid="supporting-count"]').first();
  const contradictingElement = page.locator('[data-testid="contradicting-count"]').first();
  const neutralElement = page.locator('[data-testid="neutral-count"]').first();
  
  if (await supportingElement.isVisible()) {
    evidenceSummary.supporting = parseInt(await supportingElement.textContent() || '0');
  }
  if (await contradictingElement.isVisible()) {
    evidenceSummary.contradicting = parseInt(await contradictingElement.textContent() || '0');
  }
  if (await neutralElement.isVisible()) {
    evidenceSummary.neutral = parseInt(await neutralElement.textContent() || '0');
  }
  
  // Extract agent verdicts
  const agentElements = page.locator('[data-testid="agent-verdict"], .agent-card');
  const agentCount = await agentElements.count();
  
  const agents = [];
  for (let i = 0; i < agentCount; i++) {
    const agent = agentElements.nth(i);
    const name = await agent.locator('.agent-name, [data-testid="agent-name"]').textContent();
    const verdict = await agent.locator('.agent-verdict, [data-testid="agent-verdict"]').textContent();
    const summary = await agent.locator('.agent-summary, [data-testid="agent-summary"]').textContent();
    
    agents.push({
      name: name?.trim().toLowerCase(),
      verdict: verdict?.trim().toLowerCase(),
      summary: summary?.trim()
    });
  }
  
  // Extract recommendation
  const recommendationElement = page.locator('[data-testid="recommendation"], .recommendation-text').first();
  const recommendation = await recommendationElement.textContent();
  
  // Extract limitations
  const limitationElements = page.locator('[data-testid="limitation-item"], .limitation');
  const limitationCount = await limitationElements.count();
  
  const limitations = [];
  for (let i = 0; i < limitationCount; i++) {
    const limitation = await limitationElements.nth(i).textContent();
    limitations.push(limitation?.trim());
  }
  
  return {
    score,
    category: category?.trim(),
    confidence: confidence?.trim(),
    sourceCount,
    sources,
    evidenceSummary,
    agents,
    recommendation: recommendation?.trim(),
    limitations
  };
}

// Test suite
test.describe('Claim Verification - Automated Browser Tests', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToHomePage(page);
  });

  for (const testCase of TEST_CLAIMS) {
    test(`should verify claim: "${testCase.claim.substring(0, 50)}..." with proper reasoning and sources`, async ({ page }) => {
      console.log(`\n${'='.repeat(80)}`);
      console.log(`Testing Claim: ${testCase.claim}`);
      console.log('='.repeat(80));
      
      // Submit the claim
      await submitClaim(page, testCase.claim);
      
      // Extract verification result
      const result = await extractVerificationResult(page);
      
      console.log('\n📊 VERIFICATION RESULTS:');
      console.log(`   Score: ${result.score}/100`);
      console.log(`   Category: ${result.category}`);
      console.log(`   Confidence: ${result.confidence}`);
      console.log(`   Sources Consulted: ${result.sourceCount}`);
      
      // Validate credibility score
      expect(result.score).toBeGreaterThanOrEqual(testCase.expectedScoreRange[0]);
      expect(result.score).toBeLessThanOrEqual(testCase.expectedScoreRange[1]);
      console.log(`   ✅ Score within expected range [${testCase.expectedScoreRange[0]}-${testCase.expectedScoreRange[1]}]`);
      
      // Validate category
      expect(result.category).toContain(testCase.expectedCategory);
      console.log(`   ✅ Category matches: ${testCase.expectedCategory}`);
      
      // Validate confidence level
      expect(result.confidence).toContain(testCase.expectedConfidence);
      console.log(`   ✅ Confidence level: ${testCase.expectedConfidence}`);
      
      // Validate minimum sources
      expect(result.sourceCount).toBeGreaterThanOrEqual(testCase.minSources);
      console.log(`   ✅ Sufficient sources (${result.sourceCount} >= ${testCase.minSources})`);
      
      // Validate evidence stance distribution
      console.log('\n📈 EVIDENCE SUMMARY:');
      console.log(`   Supporting: ${result.evidenceSummary.supporting}`);
      console.log(`   Contradicting: ${result.evidenceSummary.contradicting}`);
      console.log(`   Neutral: ${result.evidenceSummary.neutral}`);
      
      if (testCase.expectedStance.supporting.min !== undefined) {
        expect(result.evidenceSummary.supporting).toBeGreaterThanOrEqual(testCase.expectedStance.supporting.min);
        console.log(`   ✅ Supporting evidence >= ${testCase.expectedStance.supporting.min}`);
      }
      if (testCase.expectedStance.supporting.max !== undefined) {
        expect(result.evidenceSummary.supporting).toBeLessThanOrEqual(testCase.expectedStance.supporting.max);
        console.log(`   ✅ Supporting evidence <= ${testCase.expectedStance.supporting.max}`);
      }
      
      if (testCase.expectedStance.contradicting.min !== undefined) {
        expect(result.evidenceSummary.contradicting).toBeGreaterThanOrEqual(testCase.expectedStance.contradicting.min);
        console.log(`   ✅ Contradicting evidence >= ${testCase.expectedStance.contradicting.min}`);
      }
      if (testCase.expectedStance.contradicting.max !== undefined) {
        expect(result.evidenceSummary.contradicting).toBeLessThanOrEqual(testCase.expectedStance.contradicting.max);
        console.log(`   ✅ Contradicting evidence <= ${testCase.expectedStance.contradicting.max}`);
      }
      
      // Validate agent execution
      console.log('\n🤖 AGENT VERDICTS:');
      for (const expectedAgent of testCase.expectedAgents) {
        const agentResult = result.agents.find(a => a.name?.includes(expectedAgent));
        expect(agentResult).toBeDefined();
        console.log(`   ✅ ${expectedAgent} agent executed`);
        console.log(`      Verdict: ${agentResult?.verdict}`);
        console.log(`      Summary: ${agentResult?.summary?.substring(0, 100)}...`);
      }
      
      // Validate reasoning keywords in sources and summaries
      console.log('\n🔍 REASONING ANALYSIS:');
      let keywordFound = false;
      const allText = [
        result.recommendation,
        ...result.agents.map(a => a.summary),
        ...result.sources.map(s => s.excerpt)
      ].join(' ').toLowerCase();
      
      for (const keyword of testCase.reasoningKeywords) {
        if (allText.includes(keyword.toLowerCase())) {
          console.log(`   ✅ Found reasoning keyword: "${keyword}"`);
          keywordFound = true;
        }
      }
      expect(keywordFound).toBe(true);
      
      // Validate source diversity
      console.log('\n📚 SOURCE ANALYSIS:');
      console.log(`   Total sources: ${result.sources.length}`);
      
      // Check for source type diversity
      const sourceUrls = result.sources.map(s => s.url?.toLowerCase() || '');
      const hasScientific = sourceUrls.some(url => 
        url.includes('pubmed') || url.includes('arxiv') || url.includes('nature') || url.includes('science')
      );
      const hasNews = sourceUrls.some(url => 
        url.includes('news') || url.includes('bbc') || url.includes('reuters') || url.includes('ap.org')
      );
      const hasEncyclopedia = sourceUrls.some(url => 
        url.includes('wikipedia') || url.includes('britannica')
      );
      
      console.log(`   Scientific sources: ${hasScientific ? '✅' : '❌'}`);
      console.log(`   News sources: ${hasNews ? '✅' : '❌'}`);
      console.log(`   Encyclopedia sources: ${hasEncyclopedia ? '✅' : '❌'}`);
      
      // Detailed source breakdown
      console.log('\n📖 DETAILED SOURCES:');
      const supportingSources = result.sources.filter(s => s.stance === 'supporting');
      const contradictingSources = result.sources.filter(s => s.stance === 'contradicting');
      const neutralSources = result.sources.filter(s => s.stance === 'neutral');
      
      console.log(`\n   SUPPORTING (${supportingSources.length}):`);
      supportingSources.slice(0, 3).forEach((source, i) => {
        console.log(`   ${i + 1}. ${source.title}`);
        console.log(`      URL: ${source.url}`);
        console.log(`      Excerpt: ${source.excerpt?.substring(0, 100)}...`);
      });
      
      console.log(`\n   CONTRADICTING (${contradictingSources.length}):`);
      contradictingSources.slice(0, 3).forEach((source, i) => {
        console.log(`   ${i + 1}. ${source.title}`);
        console.log(`      URL: ${source.url}`);
        console.log(`      Excerpt: ${source.excerpt?.substring(0, 100)}...`);
      });
      
      console.log(`\n   NEUTRAL (${neutralSources.length}):`);
      neutralSources.slice(0, 3).forEach((source, i) => {
        console.log(`   ${i + 1}. ${source.title}`);
        console.log(`      URL: ${source.url}`);
        console.log(`      Excerpt: ${source.excerpt?.substring(0, 100)}...`);
      });
      
      // Validate recommendation exists and is meaningful
      console.log('\n💡 RECOMMENDATION:');
      expect(result.recommendation).toBeTruthy();
      expect(result.recommendation!.length).toBeGreaterThan(20);
      console.log(`   ${result.recommendation}`);
      
      // Validate limitations are provided
      console.log('\n⚠️  LIMITATIONS:');
      expect(result.limitations.length).toBeGreaterThan(0);
      result.limitations.forEach((limitation, i) => {
        console.log(`   ${i + 1}. ${limitation}`);
      });
      
      console.log(`\n${'='.repeat(80)}`);
      console.log('✅ ALL VALIDATIONS PASSED');
      console.log('='.repeat(80));
    });
  }

  test('should handle invalid claims gracefully', async ({ page }) => {
    const invalidClaims = [
      '',
      'a',
      'test',
      '   ',
    ];
    
    for (const claim of invalidClaims) {
      await navigateToHomePage(page);
      
      const claimInput = page.locator('textarea[placeholder*="claim" i]').first();
      await claimInput.fill(claim);
      
      const verifyButton = page.locator('button:has-text("Verify")').first();
      await verifyButton.click();
      
      // Should show validation error
      const errorMessage = page.locator('[data-testid="error-message"], .error-text').first();
      await expect(errorMessage).toBeVisible({ timeout: 5000 });
      
      console.log(`✅ Invalid claim "${claim}" properly rejected`);
    }
  });

  test('should display processing time', async ({ page }) => {
    await submitClaim(page, TEST_CLAIMS[0].claim);
    
    const processingTimeElement = page.locator('[data-testid="processing-time"], .processing-time').first();
    await expect(processingTimeElement).toBeVisible();
    
    const processingTime = await processingTimeElement.textContent();
    console.log(`⏱️  Processing time: ${processingTime}`);
    
    // Processing time should be reasonable (< 30 seconds)
    const timeMatch = processingTime?.match(/(\d+\.?\d*)/);
    if (timeMatch) {
      const seconds = parseFloat(timeMatch[1]);
      expect(seconds).toBeLessThan(30);
      console.log(`✅ Processing completed in ${seconds}s (< 30s)`);
    }
  });

  test('should allow viewing source details', async ({ page }) => {
    await submitClaim(page, TEST_CLAIMS[1].claim);
    
    // Click on first source to view details
    const firstSource = page.locator('[data-testid="source-item"]').first();
    await firstSource.click();
    
    // Should show expanded source details
    const sourceDetails = page.locator('[data-testid="source-details"]').first();
    await expect(sourceDetails).toBeVisible({ timeout: 5000 });
    
    console.log('✅ Source details can be expanded');
  });

  test('should show agent breakdown', async ({ page }) => {
    await submitClaim(page, TEST_CLAIMS[2].claim);
    
    // Find agent breakdown section
    const agentBreakdown = page.locator('[data-testid="agent-breakdown"], .agent-section').first();
    await expect(agentBreakdown).toBeVisible();
    
    // Should show multiple agents
    const agentCards = page.locator('[data-testid="agent-verdict"]');
    const agentCount = await agentCards.count();
    
    expect(agentCount).toBeGreaterThan(0);
    console.log(`✅ Agent breakdown shows ${agentCount} agents`);
  });
});

test.describe('Claim Verification - API Direct Tests', () => {
  test('should verify claim via API with detailed response', async ({ request }) => {
    const testClaim = TEST_CLAIMS[0];
    
    console.log(`\n${'='.repeat(80)}`);
    console.log(`API Test - Claim: ${testClaim.claim}`);
    console.log('='.repeat(80));
    
    const response = await request.post(`${API_URL}/api/v1/verify`, {
      data: {
        content: testClaim.claim,
        type: 'text',
        source: 'api'
      }
    });
    
    expect(response.ok()).toBeTruthy();
    
    const result = await response.json();
    
    console.log('\n📊 API RESPONSE:');
    console.log(JSON.stringify(result, null, 2));
    
    // Validate response structure
    expect(result).toHaveProperty('id');
    expect(result).toHaveProperty('credibility_score');
    expect(result).toHaveProperty('category');
    expect(result).toHaveProperty('confidence');
    expect(result).toHaveProperty('sources');
    expect(result).toHaveProperty('agent_verdicts');
    expect(result).toHaveProperty('evidence_summary');
    expect(result).toHaveProperty('recommendation');
    expect(result).toHaveProperty('limitations');
    
    console.log('\n✅ API response has all required fields');
    
    // Validate evidence summary structure
    expect(result.evidence_summary).toHaveProperty('supporting');
    expect(result.evidence_summary).toHaveProperty('contradicting');
    expect(result.evidence_summary).toHaveProperty('neutral');
    
    console.log('\n📈 Evidence Summary:');
    console.log(`   Supporting: ${result.evidence_summary.supporting}`);
    console.log(`   Contradicting: ${result.evidence_summary.contradicting}`);
    console.log(`   Neutral: ${result.evidence_summary.neutral}`);
    
    // Validate sources have required fields
    if (result.sources.length > 0) {
      const firstSource = result.sources[0];
      expect(firstSource).toHaveProperty('url');
      expect(firstSource).toHaveProperty('title');
      expect(firstSource).toHaveProperty('stance');
      
      console.log('\n📚 Sample Source:');
      console.log(`   Title: ${firstSource.title}`);
      console.log(`   URL: ${firstSource.url}`);
      console.log(`   Stance: ${firstSource.stance}`);
      console.log(`   Excerpt: ${firstSource.excerpt?.substring(0, 100)}...`);
    }
    
    console.log(`\n${'='.repeat(80)}`);
    console.log('✅ API TEST PASSED');
    console.log('='.repeat(80));
  });
});
