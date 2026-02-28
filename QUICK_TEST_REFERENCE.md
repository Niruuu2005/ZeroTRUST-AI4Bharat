# ZeroTRUST - Quick Test Reference Card

## 🚀 Quick Start (3 Steps)

### 1. Start Services
```powershell
# Terminal 1: Start all services
docker-compose up -d

# Terminal 2: API Gateway
cd apps/api-gateway && npm run dev

# Terminal 3: Verification Engine  
cd apps/verification-engine && uvicorn src.main:app --reload

# Terminal 4: Web Portal
cd apps/web-portal && npm run dev
```

### 2. Install Playwright
```powershell
npm install
npx playwright install --with-deps
```

### 3. Run Tests
```powershell
.\run-claim-verification-tests.ps1
```

---

## 📋 Test Commands Cheat Sheet

| Command | Description |
|---------|-------------|
| `.\run-claim-verification-tests.ps1` | Run all tests (headless) |
| `.\run-claim-verification-tests.ps1 headed` | Run with visible browser |
| `.\run-claim-verification-tests.ps1 debug` | Debug mode with inspector |
| `.\run-claim-verification-tests.ps1 ui` | Interactive UI mode |
| `npm run test:report` | View HTML report |

---

## ✅ What Gets Validated

### For Each Claim:
- ✅ Credibility score (0-100)
- ✅ Category (Verified True/False, Likely True/False, Mixed)
- ✅ Confidence level (High/Medium/Low)
- ✅ Minimum sources consulted (10-15+)
- ✅ Evidence stance (supporting/contradicting/neutral)
- ✅ Agent execution (6 agents)
- ✅ Reasoning keywords present
- ✅ Source diversity (scientific, news, encyclopedia)
- ✅ Recommendation provided
- ✅ Limitations disclosed

---

## 🎯 Test Claims

| Claim | Expected Result |
|-------|----------------|
| "COVID-19 vaccines contain microchips" | ❌ Verified False (0-20) |
| "India launched Chandrayaan-3 in 2023" | ✅ Verified True (80-100) |
| "5G towers cause health problems" | ⚠️ Likely False (20-50) |
| "The Earth is flat" | ❌ Verified False (0-15) |
| "Climate change is human-caused" | ✅ Verified True (85-100) |

---

## 📊 Expected Output Example

```
📊 VERIFICATION RESULTS:
   Score: 12/100
   Category: Verified False
   Confidence: High
   Sources: 23

📈 EVIDENCE:
   Supporting: 1
   Contradicting: 18
   Neutral: 4

🤖 AGENTS:
   ✅ research (false)
   ✅ news (false)
   ✅ scientific (false)
   ✅ sentiment (manipulation detected)

🔍 REASONING:
   ✅ Keywords: false, debunked, no evidence

📚 SOURCES:
   Scientific: ✅
   News: ✅
   Encyclopedia: ✅
```

---

## 🐛 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| Service not running | Check `curl http://localhost:3000/health` |
| Tests timeout | Increase timeout in `playwright.config.ts` |
| Browser not found | Run `npx playwright install --with-deps` |
| Tests fail | Check `test-results/html/index.html` |

---

## 📁 Test Artifacts Location

```
test-results/
├── html/index.html          # 👁️ View this first
├── results.json             # Machine-readable
├── junit.xml                # CI/CD integration
├── screenshots/             # Failure screenshots
└── videos/                  # Failure videos
```

---

## 🎨 Test Modes

| Mode | Use Case | Command |
|------|----------|---------|
| Headless | CI/CD, fast execution | `npm run test:e2e` |
| Headed | Visual debugging | `npm run test:e2e:headed` |
| Debug | Step-by-step debugging | `npm run test:e2e:debug` |
| UI | Interactive exploration | `npm run test:e2e:ui` |

---

## 🔧 Configuration Files

| File | Purpose |
|------|---------|
| `playwright.config.ts` | Test configuration |
| `tests/e2e/claim-verification.spec.ts` | Test suite |
| `run-claim-verification-tests.ps1` | Test runner |
| `E2E_TESTING_GUIDE.md` | Full documentation |

---

## 💡 Pro Tips

1. **Run headed mode first** to see what's happening
2. **Check HTML report** for visual confirmation
3. **Use debug mode** to step through failures
4. **Review screenshots** to understand UI issues
5. **Watch videos** to see the full failure flow

---

## 📞 Need Help?

1. Read `E2E_TESTING_GUIDE.md` for detailed instructions
2. Check `TEST_ANALYSIS_REPORT.md` for system status
3. Review `test-results/html/index.html` for test results
4. Run `npm run test:e2e:debug` to debug failures

---

**Quick Reference Version:** 1.0  
**Last Updated:** February 28, 2026
