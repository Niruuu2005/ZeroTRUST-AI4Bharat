# Task 1: AWS Bedrock and External API Configuration Guide

## Status: ⚠️ REQUIRES USER ACTION

This guide provides step-by-step instructions to complete Task 1 of the comprehensive-testing-suite spec.

## Current Status

### ✅ Completed
- AWS credentials are configured in `.env.local`
  - `AWS_ACCESS_KEY_ID`: AKIA************ESCB
  - `AWS_SECRET_ACCESS_KEY`: Configured (masked)
  - `AWS_DEFAULT_REGION`: us-east-1
- Bedrock client successfully initializes
- Test script created: `scripts/test-aws-bedrock-config.py`

### ⚠️ Requires Action
1. **Enable Bedrock models in AWS Console** (CRITICAL)
2. **Configure external API keys** (OPTIONAL but recommended)

---

## Step 1: Enable AWS Bedrock Models (REQUIRED)

The AWS credentials are valid, but the Bedrock models need to be enabled in your AWS account.

### Instructions:

1. **Log in to AWS Console**
   - Go to: https://console.aws.amazon.com/
   - Use your AWS account credentials

2. **Navigate to Bedrock**
   - Search for "Bedrock" in the AWS Console search bar
   - Click on "Amazon Bedrock"

3. **Request Model Access**
   - In the left sidebar, click **"Model access"**
   - Click the **"Manage model access"** button (orange button in top right)

4. **Enable Required Models**
   
   Check the boxes for these models:
   
   - ✅ **Anthropic**
     - Claude 3.5 Sonnet v2 (`anthropic.claude-3-5-sonnet-20241022-v2:0`)
     - Claude 3 Haiku (`anthropic.claude-3-5-haiku-20241022-v1:0`)
   
   - ✅ **Mistral AI**
     - Mistral Large (`mistral.mistral-large-2407-v1:0`)

5. **Submit Request**
   - Scroll to the bottom and click **"Request model access"**
   - Access is usually granted **instantly** for these models
   - Wait for status to change from "Pending" to "Access granted" (refresh the page)

6. **Verify Access**
   - Once all three models show "Access granted", run the test script:
   ```powershell
   python scripts/test-aws-bedrock-config.py
   ```

### Expected Result:
```
✓ Claude 3.5 Sonnet: Response: Model test successful
✓ Claude 3 Haiku: Response: Model test successful
✓ Mistral Large: Response: Model test successful
```

---

## Step 2: Configure External API Keys (OPTIONAL)

External API keys enhance verification quality by providing access to more diverse sources. The system will work without them using free sources (RSS feeds, DuckDuckGo, public Reddit), but accuracy may be limited.

### Priority Levels:

**HIGH PRIORITY** (Recommended for production):
- `NEWS_API_KEY` - NewsAPI for news articles
- `GNEWS_API_KEY` - GNews for international news

**MEDIUM PRIORITY** (Enhances search capabilities):
- `GOOGLE_SEARCH_KEY` - Google Custom Search API
- `GOOGLE_SEARCH_ENGINE_ID` - Google Custom Search Engine ID

**LOW PRIORITY** (Social media verification):
- `TWITTER_BEARER_TOKEN` - Twitter API v2
- `REDDIT_CLIENT_ID` - Reddit API
- `REDDIT_CLIENT_SECRET` - Reddit API

### How to Get API Keys:

#### NewsAPI (FREE tier: 100 requests/day)
1. Go to: https://newsapi.org/
2. Click "Get API Key"
3. Sign up for a free account
4. Copy your API key
5. Add to `.env.local`: `NEWS_API_KEY=your_key_here`

#### GNews (FREE tier: 100 requests/day)
1. Go to: https://gnews.io/
2. Click "Get API Key"
3. Sign up for a free account
4. Copy your API key
5. Add to `.env.local`: `GNEWS_API_KEY=your_key_here`

#### Google Custom Search (FREE tier: 100 queries/day)
1. Go to: https://developers.google.com/custom-search/v1/overview
2. Click "Get a Key"
3. Create a new project or select existing
4. Enable Custom Search API
5. Create credentials (API key)
6. Create a Custom Search Engine at: https://cse.google.com/cse/
7. Add to `.env.local`:
   ```
   GOOGLE_SEARCH_KEY=your_api_key
   GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id
   ```

#### Twitter API (Requires approval)
1. Go to: https://developer.twitter.com/
2. Apply for a developer account
3. Create a new app
4. Generate Bearer Token
5. Add to `.env.local`: `TWITTER_BEARER_TOKEN=your_token`

#### Reddit API (FREE)
1. Go to: https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Select "script" type
4. Fill in name and redirect URI (can be http://localhost)
5. Copy Client ID and Client Secret
6. Add to `.env.local`:
   ```
   REDDIT_CLIENT_ID=your_client_id
   REDDIT_CLIENT_SECRET=your_client_secret
   ```

### Verify API Configuration:
```powershell
python scripts/test-aws-bedrock-config.py
```

---

## Step 3: Verify Complete Configuration

After enabling Bedrock models and optionally configuring API keys, run the test script:

```powershell
python scripts/test-aws-bedrock-config.py
```

### Expected Output (Minimum for Task 1 completion):

```
✓ AWS Bedrock: All models accessible ✓
⚠ External APIs: Some APIs not configured (system will use fallbacks)

✓ Configuration test PASSED
  AWS Bedrock is properly configured and all models are accessible
```

### Full Success Output (All APIs configured):

```
✓ AWS Bedrock: All models accessible ✓
✓ External APIs: All required APIs configured ✓

✓ Configuration test PASSED
  AWS Bedrock is properly configured and all models are accessible
```

---

## Troubleshooting

### Issue: "ValidationException" when calling Bedrock models

**Cause**: Models not enabled in AWS Console

**Solution**: Follow Step 1 above to enable model access

### Issue: "AccessDeniedException" 

**Cause**: IAM user lacks Bedrock permissions

**Solution**: Add this policy to your IAM user:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "*"
    }
  ]
}
```

### Issue: "ThrottlingException"

**Cause**: Too many requests to Bedrock

**Solution**: 
- Wait a few seconds and try again
- The system has automatic retry with exponential backoff
- Check your AWS Bedrock quotas

### Issue: External API returns errors

**Cause**: Invalid API key or rate limit exceeded

**Solution**:
- Verify API key is correct in `.env.local`
- Check API provider dashboard for usage limits
- The system will automatically fall back to free sources

---

## Task Completion Checklist

- [ ] AWS Bedrock models enabled in AWS Console
- [ ] Test script passes for all three Bedrock models
- [ ] (Optional) External API keys configured
- [ ] Test script runs successfully
- [ ] Ready to proceed to Task 2

---

## Next Steps

Once Task 1 is complete (Bedrock models accessible), you can proceed to:

**Task 2**: Implement Normalization Layer
- Create TextNormalizer class
- Create MetadataExtractor class
- Create LanguageDetector class
- Write property-based tests

---

## Support

If you encounter issues:

1. Check AWS Console → Bedrock → Model access for model status
2. Verify `.env.local` has correct credentials
3. Run the test script with verbose output
4. Check AWS CloudWatch logs for detailed error messages

For AWS Bedrock issues, refer to:
- AWS Bedrock Documentation: https://docs.aws.amazon.com/bedrock/
- AWS Bedrock Model Access: https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html
