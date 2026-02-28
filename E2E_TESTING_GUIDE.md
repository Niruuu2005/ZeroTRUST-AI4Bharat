# ZeroTRUST - End-to-End Testing Guide
**Automated Browser Tests for Claim Verification**

## Overview

This guide explains how to run automated browser tests that verify claims with proper reasoning, sources, and detailed evidence analysis. The tests validate that the ZeroTRUST system correctly identifies supporting and contradicting evidence for various types of claims.

---

## What Gets Tested

### 1. Claim Verification Flow
- ✅ Credibility score calculation (0-100 range)
- ✅ Category assignment (Verified True/False, Likely True/False, Mixed Evidence)
- ✅ Confidence level (High, Medium, Low)
- ✅ Source consultation (minimum 10-15 sources per claim)
- ✅ Evidence stance distribution (supporting, contradicting, neutral)

### 2. Agent Execution
- ✅ Research Agent (Wikipedia, Google)
- ✅ News Agent (NewsAPI, GNews)
- ✅ Scientific Agent (PubMed, arXiv)
- ✅ Social Media Agent (Reddit, Twitter)
- ✅ Sentiment Agent (propaganda detection)
- ✅ Scraper Agent (URL content extraction)

### 3. Reasoning Analysis
- ✅ Presence of reasoning keywords in summaries
- ✅ Logical consistency in verdicts
- ✅ Evidence-based recommendations
- ✅ Transparent limitations disclosure

### 4. Source Quality
- ✅ Source diversity (scientific, news, encyclopedia)
- ✅ Source credibility tiers (Tier 1-4)
- ✅ Source stance classification
- ✅ Excerpt relevance to claim

---

## Test Claims

The test suite includes 5 carefully selected claims covering different categories:

### 1. Verified False Claim
**Claim:** "COVID-19 vaccines contain microchips for tracking"
- Expected Score: 0-20
- Expected Category: Verified False
- Expected Confidence: High
- Minimum Sources: 10
- Expected Stance: High contradicting evidence

### 2. Verified True Claim
**Claim:** "India launched Chandrayaan-3 moon mission in 2023"
- Expected Score: 80-100
- Expected Category: Verified True
- Expected Confidence: High
- Minimum Sources: 15
- Expected Stance: High supporting evidence

### 3. Likely False Claim
**Claim:** "5G towers cause health problems"
- Expected Score: 20-50
- Expected Category: Likely False
- Expected Confidence: Medium
- Minimum Sources: 8
- Expected Stance: More contradicting than supporting

### 4. Conspiracy Theory
**Claim:** "The Earth is flat"
- Expected Score: 0-15
- Expected Category: Verified False
- Expected Confidence: High
- Minimum Sources: 10
- Expected Stance: Overwhelming contradicting evidence

### 5. Scientific Consensus
**Claim:** "Climate change is caused by human activities"
- Expected Score: 85-100
- Expected Category: Verified True
- Expected Confidence: High
- Minimum Sources: 15
- Expected Stance: Strong supporting evidence

---

## Prerequisites

### 1. Services Running
Ensure all services are running before executing tests:

```powershell
# Terminal 1: API Gateway
cd apps/api-gateway
npm run dev

# Terminal 2: Verification Engine
cd apps/verification-engine
uvicorn src.main:app --reload

# Terminal 3: Web Portal
cd apps/web-portal
npm run dev

# Terminal 4: Database & Cache
docker-compose up postgres redis
```

### 2. Install Playwright
```powershell
npm install
npx playwright install --with-deps
```

---

## Running Tests

### Quick Start
```powershell
# Run all tests (headless mode)
.\run-claim-verification-tests.ps1

# Or using npm
npm run test:e2e
```

### Test Modes

#### 1. Headless Mode (Default)
Runs tests in the background without visible browser windows.
```powershell
npm run test:e2e
```

#### 2. Headed Mode
Shows browser windows during test execution (useful for debugging).
```powershell
.\run-claim-verification-tests.ps1 headed
# Or
npm run test:e2e:headed
```

#### 3. Debug Mode
Opens Playwright Inspector for step-by-step debugging.
```powershell
.\run-claim-verification-tests.ps1 debug
# Or
npm run test:e2e:debug
```

#### 4. UI Mode
Opens interactive Playwright UI for test exploration.
```powershell
.\run-claim-verification-tests.ps1 ui
# Or
npm run test:e2e:ui
```

#### 5. Single Browser
Run tests in a specific browser only.
```powershell
# Chromium only
.\run-claim-verification-tests.ps1 chromium
npm run test:e2e:chromium

# Firefox only
.\run-claim-verification-tests.ps1 firefox
npm run test:e2e:firefox

# WebKit (Safari) only
.\run-claim-verification-tests.ps1 webkit
npm run test:e2e:webkit
```

#### 6. Mobile Browsers
Test on mobile viewports.
```powershell
npm run test:e2e:mobile
```

---

## Understanding Test Output

### Console Output Example

```
================================================================================
Testing Claim: COVID-19 vaccines contain microchips for tracking
================================================================================

📊 VERIFICATION RESULTS:
   Score: 12/100
   Category: Verified False
   Confidence: High
   Sources Consulted: 23
   ✅ Score within expected range [0-20]
   ✅ Category matches: Verified False
   ✅ Confidence level: High
   ✅ Sufficient sources (23 >= 10)

📈 EVIDENCE SUMMARY:
   Supporting: 1
   Contradicting: 18
   Neutral: 4
   ✅ Supporting evidence <= 2
   ✅ Contradicting evidence >= 8

🤖 AGENT VERDICTS:
   ✅ research agent executed
      Verdict: false
      Summary: No credible evidence supports the claim that COVID-19 vaccines contain microchips...
   ✅ news agent executed
      Verdict: false
      Summary: Multiple fact-checking organizations have debunked this conspiracy theory...
   ✅ scientific agent executed
      Verdict: false
      Summary: Scientific literature shows no evidence of microchips in vaccines...
   ✅ sentiment agent executed
      Verdict: supports
      Summary: Detected 2 manipulation technique(s): fear-mongering, conspiracy theory

🔍 REASONING ANALYSIS:
   ✅ Found reasoning keyword: "false"
   ✅ Found reasoning keyword: "debunked"
   ✅ Found reasoning keyword: "no evidence"
   ✅ Found reasoning keyword: "conspiracy"

📚 SOURCE ANALYSIS:
   Total sources: 23
   Scientific sources: ✅
   News sources: ✅
   Encyclopedia sources: ✅

📖 DETAILED SOURCES:

   SUPPORTING (1):
   1. Social Media Discussion
      URL: https://reddit.com/r/conspiracy/...
      Excerpt: Some users claim vaccines contain tracking devices...

   CONTRADICTING (18):
   1. CDC Official Statement
      URL: https://www.cdc.gov/coronavirus/vaccines-safety
      Excerpt: COVID-19 vaccines do not contain microchips. This is a false claim...
   2. Reuters Fact Check
      URL: https://www.reuters.com/article/factcheck-vaccine-microchip
      Excerpt: Fact check: COVID-19 vaccines do not contain microchips...
   3. PubMed Study
      URL: https://pubmed.ncbi.nlm.nih.gov/...
      Excerpt: Analysis of vaccine composition shows no electronic components...

   NEUTRAL (4):
   1. Wikipedia: COVID-19 Vaccine
      URL: https://en.wikipedia.org/wiki/COVID-19_vaccine
      Excerpt: COVID-19 vaccines are biological preparations that provide immunity...

💡 RECOMMENDATION:
   This claim is false and has been thoroughly debunked by scientific and medical authorities. 
   The claim appears to be a conspiracy theory with no credible evidence. Multiple fact-checking 
   organizations and health authorities have confirmed that COVID-19 vaccines do not contain 
   microchips or tracking devices.

⚠️  LIMITATIONS:
   1. Limited access to some paywalled scientific journals
   2. Social media data may not represent full public discourse
   3. Some sources may have regional bias

================================================================================
✅ ALL VALIDATIONS PASSED
================================================================================
```

---

## Test Reports

### 1. HTML Report
Interactive HTML report with screenshots and videos.
```powershell
npm run test:report
```

Opens `test-results/html/index.html` in your browser showing:
- Test execution timeline
- Pass/fail status for each test
- Screenshots of failures
- Video recordings of failures
- Detailed error messages

### 2. JSON Report
Machine-readable test results.
```
test-results/results.json
```

### 3. JUnit XML
For CI/CD integration.
```
test-results/junit.xml
```

---

## Test Artifacts

All test artifacts are saved to `test-results/`:

```
test-results/
├── html/                    # HTML report
│   └── index.html
├── results.json             # JSON results
├── junit.xml                # JUnit XML
├── screenshots/             # Failure screenshots
│   └── test-name-chromium.png
└── videos/                  # Failure videos
    └── test-name-chromium.webm
```

---

## Validations Performed

### 1. Score Validation
```typescript
expect(result.score).toBeGreaterThanOrEqual(expectedScoreRange[0]);
expect(result.score).toBeLessThanOrEqual(expectedScoreRange[1]);
```

### 2. Category Validation
```typescript
expect(result.category).toContain(expectedCategory);
```

### 3. Evidence Stance Validation
```typescript
expect(result.evidenceSummary.supporting).toBeGreaterThanOrEqual(minSupporting);
expect(result.evidenceSummary.contradicting).toBeGreaterThanOrEqual(minContradicting);
```

### 4. Agent Execution Validation
```typescript
for (const expectedAgent of expectedAgents) {
  const agentResult = result.agents.find(a => a.name?.includes(expectedAgent));
  expect(agentResult).toBeDefined();
}
```

### 5. Reasoning Keyword Validation
```typescript
const allText = [recommendation, ...summaries, ...excerpts].join(' ');
for (const keyword of reasoningKeywords) {
  expect(allText.toLowerCase()).toContain(keyword.toLowerCase());
}
```

### 6. Source Diversity Validation
```typescript
expect(hasScientificSources).toBe(true);
expect(hasNewsSources).toBe(true);
expect(hasEncyclopediaSources).toBe(true);
```

---

## Troubleshooting

### Tests Fail with "Service Not Running"
**Solution:** Ensure all services are running:
```powershell
# Check service health
curl http://localhost:3000/health  # API Gateway
curl http://localhost:8000/health  # Verification Engine
curl http://localhost:5173         # Web Portal
```

### Tests Timeout
**Solution:** Increase timeout in `playwright.config.ts`:
```typescript
timeout: 180 * 1000,  // 3 minutes
```

### Browser Not Found
**Solution:** Reinstall Playwright browsers:
```powershell
npx playwright install --with-deps
```

### Tests Pass Locally but Fail in CI
**Solution:** Check CI environment variables and service availability.

### Flaky Tests
**Solution:** Enable retries in `playwright.config.ts`:
```typescript
retries: 2,
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm install
      
      - name: Install Playwright
        run: npx playwright install --with-deps
      
      - name: Start services
        run: docker-compose up -d
      
      - name: Run E2E tests
        run: npm run test:e2e
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test-results/
```

---

## Best Practices

### 1. Run Tests Regularly
- Before committing code
- Before deploying to production
- After adding new features
- When API keys are updated

### 2. Review Test Reports
- Check HTML report for visual confirmation
- Review screenshots of failures
- Watch failure videos to understand issues

### 3. Keep Tests Updated
- Update expected values when system improves
- Add new test claims for edge cases
- Adjust timeouts based on performance

### 4. Monitor Test Performance
- Track test execution time
- Identify slow tests
- Optimize verification pipeline

---

## Advanced Usage

### Custom Test Claims

Add your own test claims to `tests/e2e/claim-verification.spec.ts`:

```typescript
const CUSTOM_CLAIMS = [
  {
    claim: "Your custom claim here",
    expectedCategory: "Likely True",
    expectedScoreRange: [60, 80],
    expectedConfidence: "Medium",
    minSources: 10,
    expectedStance: {
      supporting: { min: 5 },
      contradicting: { max: 3 },
      neutral: { max: 5 }
    },
    expectedAgents: ['research', 'news'],
    reasoningKeywords: ['keyword1', 'keyword2'],
    sourceTypes: ['news', 'scientific']
  }
];
```

### Parallel Execution

For faster test execution (use with caution due to rate limiting):

```typescript
// playwright.config.ts
workers: 3,  // Run 3 tests in parallel
```

### Custom Reporters

Add custom reporters in `playwright.config.ts`:

```typescript
reporter: [
  ['html'],
  ['json', { outputFile: 'results.json' }],
  ['junit', { outputFile: 'junit.xml' }],
  ['./custom-reporter.ts']  // Your custom reporter
],
```

---

## Next Steps

1. ✅ Run the test suite to validate current system
2. ✅ Review test reports and identify issues
3. ✅ Configure API keys for full agent functionality
4. ✅ Add more test claims for comprehensive coverage
5. ✅ Integrate tests into CI/CD pipeline
6. ✅ Set up automated test scheduling

---

**Guide Version:** 1.0  
**Last Updated:** February 28, 2026  
**Status:** Ready for execution
