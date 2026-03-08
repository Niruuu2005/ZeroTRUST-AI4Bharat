# Step 2 — AWS Bedrock Setup

> **This is the most critical service.** Without Bedrock access the verification engine returns mock responses and cannot perform real AI fact-checking.

---

## What You're Doing

- Enable model access in the Bedrock console (one-time, per region)
- Verify you can invoke each model used by the agents

---

## Models Used by ZeroTRUST

> **⚠️ 2026-03-01 UPDATE:** The original Anthropic Claude and Mistral Large models were replaced due to **Marketplace billing / subscription errors** in the AWS console. The models below are the new active models that successfully bypass these restrictions.

| Role | Model ID | Replaces | Feature |
|------|----------|----------|---------|
| **Manager** | `us.amazon.nova-pro-v1:0` | Claude 3.7/3.5 Sonnet | Top-tier quality, cross-region inference |
| **Research** | `us.mistral.pixtral-large-2502-v1:0` | Mistral Large 2407 | Strong factual reasoning + vision |
| **Sentiment** | `us.amazon.nova-lite-v1:0` | Claude 3.5 Haiku | Fast, cheap, bilingual |

All three models use AWS **cross-region inference profiles** (prefixed with `us.`) which do not require Marketplace subscription approval.

---

## 2.1 — Enable Model Access in AWS Console

> **⚠️ 2026 AWS CHANGE:** The old "Model access" page with checkboxes **has been retired**. Models are now activated differently:

1. Sign in to [AWS Console](https://console.aws.amazon.com)
2. Make sure region is **US East (N. Virginia) — us-east-1** (top-right dropdown)
3. Navigate to **Amazon Bedrock** (search "Bedrock" in the services bar)
4. Click **Model catalog** (under "Discover" in left sidebar)

### For Anthropic Models (Claude) — Extra Step Required
> Claude models require a **Use Case form** to be submitted for your account:
> - In Model catalog, click any Claude model
> - Look for **"Submit use case details"** and fill it out
> - Wait up to 15 minutes for activation
> - **⚠️ ADDITIONAL BLOCK:** If your AWS account uses **UPI AutoPay** (PhonePe, GPay, etc.) as the only payment method, Anthropic models will throw `INVALID_PAYMENT_INSTRUMENT`. These are sold via **AWS Marketplace**, which requires a verified credit card. **This is why we switched to Nova + Mistral models.**

### Amazon Nova Models (Recommended — No payment restrictions)
- ✅ `Amazon Nova Pro` → `us.amazon.nova-pro-v1:0`
- ✅ `Amazon Nova Lite` → `us.amazon.nova-lite-v1:0`

### Mistral AI Models
- ✅ `Mistral Pixtral Large (2502)` → `us.mistral.pixtral-large-2502-v1:0`

> **Note:** These models use **cross-region inference profiles** (prefixed with `us.`). Use this prefix when calling the API — it is already set in `.env.local`.

---

## 2.2 — Verify Model Access via Python (venv)

> **⚠️ 2026 NOTE:** Use the project venv instead of the `aws` CLI commands since `aws` may not be on your system PATH. Also install `python-dotenv` first:

```powershell
# One-time: install required package
.\venv\python.exe -m pip install python-dotenv
```

Then run the quick model check:

```powershell
.\venv\python.exe scripts\quick-model-check.py
```

Expected output:
```
============================================================
  ZeroTRUST — Bedrock Model Connectivity Check
============================================================
  Testing Amazon Nova Pro      (Manager) ... PASS  (OK)
  Testing Mistral Pixtral      (Research) ... PASS  (OK)
  Testing Amazon Nova Lite     (Sentiment) ... PASS  (OK)
============================================================
  All models PASSED. Bedrock is fully operational!
============================================================
```

---

## 2.3 — Test a Live Bedrock Invocation

Run the model check script included in the project:

```powershell
.\venv\python.exe scripts\quick-model-check.py
```

What the script tests:
1. AWS credentials readable from `.env.local`
2. Bedrock client can be initialised
3. Each of the 3 active models responds to a real prompt
4. Response parsing works correctly

Expected output:
```
============================================================
  ZeroTRUST — Bedrock Model Connectivity Check
============================================================
  Testing Claude 3.7 Sonnet  (Manager)   ... PASS  (OK)
  Testing Claude 3.5 Haiku   (Sentiment) ... PASS  (OK)
  Testing Mistral Pixtral    (Research)  ... PASS  (OK)
============================================================
  All models PASSED. Bedrock is fully operational!
============================================================
```
*(Labels show original names; actual models used are Nova Pro, Nova Lite, and Pixtral)*

---

## 2.4 — How the Code Uses Bedrock

The integration file is `apps/verification-engine/src/integrations/bedrock.py`.

Key behaviour:
- Uses `boto3.client('bedrock-runtime')` with `Converse` API
- Retries up to 3 times with adaptive backoff (`botocore.config.Config`)
- Falls back through the model chain on `ThrottlingException` or `ModelErrorException`
- If **all** models fail (e.g. no credentials), returns a mock JSON — pipeline won't crash but results will be synthetic

```python
# 2026 Active Models (set via .env.local)
MANAGER_MODEL = os.getenv('MANAGER_MODEL_ID', 'us.amazon.nova-pro-v1:0')
RESEARCH_MODEL = os.getenv('RESEARCH_MODEL_ID', 'us.mistral.pixtral-large-2502-v1:0')
SENTIMENT_MODEL = os.getenv('SENTIMENT_MODEL_ID', 'us.amazon.nova-lite-v1:0')

FALLBACK_CHAIN = [MANAGER_MODEL, RESEARCH_MODEL, SENTIMENT_MODEL]
```

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `AccessDeniedException` | Model not enabled or IAM missing `bedrock:InvokeModel` | Attach `AmazonBedrockFullAccess` to the user in IAM |
| `INVALID_PAYMENT_INSTRUMENT` | Anthropic/Mistral are AWS Marketplace models requiring a credit card. UPI is not accepted. | Switch to Amazon Nova models (`us.amazon.nova-pro-v1:0`, `us.amazon.nova-lite-v1:0`) |
| `ResourceNotFoundException: Fill out use case form` | Anthropic requires a use case form before first invocation | Go to Bedrock → Model catalog → Click Claude → Submit use case details. Wait 15 min. |
| `ValidationException: model ID not supported` | Using bare model ID instead of inference profile ID | Add `us.` prefix: use `us.amazon.nova-pro-v1:0` not `amazon.nova-pro-v1:0` |
| `ResourceNotFoundException: Legacy model` | Model is deprecated and inactive in your account | Upgrade to active model version (e.g. claude-3-7 or Nova Pro) |
| `ValidationException: model not found` | Wrong model ID or wrong region | Confirm region is `us-east-1` |
| `ThrottlingException` | Too many requests (free tier) | Wait and retry; fallback chain handles this automatically |
| `ModuleNotFoundError: dotenv` | `python-dotenv` not installed in venv | Run: `.\venv\python.exe -m pip install python-dotenv` |
| `CommandNotFoundException: aws` | AWS CLI not on system PATH | Use `.\venv\python.exe -m awscli` instead of `aws` |
| `AWS_ACCESS_KEY_ID not found in .env.local` | Script loads from project root, not `aws-setup/` folder | Run: `cp aws-setup\.env.local .env.local` |
| `botocore.exceptions.NoCredentialsError` | `.env.local` not loaded or keys empty | Check `.env.local` values |
| Mock responses returned | Bedrock client init failed silently | Check `logger.warning` output in terminal |

---

## Cost Estimate

> Bedrock charges per 1,000 input/output tokens.

| Model | Input ($/1K tokens) | Output ($/1K tokens) |
|-------|--------------------|--------------------- |
| Amazon Nova Pro | $0.0008 | $0.0032 |
| Mistral Pixtral Large | $0.002 | $0.006 |
| Amazon Nova Lite | $0.00006 | $0.00024 |

A single claim verification (all 6 agents) uses approximately **~15,000–25,000 total tokens** → ~$0.02–0.08 per verification with Nova Pro (significantly cheaper than the previous Sonnet-based setup).

---

## Next Step

→ [03-s3-setup.md](03-s3-setup.md)
