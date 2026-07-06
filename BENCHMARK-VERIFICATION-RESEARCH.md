# TEMUCLAUDE — BENCHMARK VERIFICATION + API SERVICE RESEARCH

## Date: July 4, 2026
## Research: How to get verified benchmarks on ArtificialAnalysis.ai + build API service

---

## 1. HOW ARTIFICIAL ANALYSIS WORKS

### What They Do
Artificial Analysis is an independent AI benchmarking company. They:
- Test models on 9 benchmark evaluations (Intelligence Index v4.1)
- Publish scores on their leaderboard
- Are referenced by Amazon, Google, Microsoft, Bloomberg, Reuters, etc.

### Intelligence Index v4.1 — 9 Evaluations

The Intelligence Index is a weighted average across 4 categories:

| Category | Weight | Evaluations |
|----------|--------|-------------|
| Agents | 34% | GDPval-AA v2 (20%), τ³-Banking (14%) |
| Coding | 24% | Terminal-Bench v2.1 (16%), SciCode (8%) |
| Scientific Reasoning | 24% | HLE (12%), GPQA Diamond (6%), CritPt (6%) |
| General | 18% | AA-LCR (6%), AA-Omniscience (12%) |

### Testing Parameters
- Temperature: 0 (non-reasoning), 0.6 (reasoning models)
- Max output tokens: 16,384 (non-reasoning), max allowed (reasoning)
- Zero-shot instruction prompted (no examples)
- Pass@1 scoring (must get correct on first attempt)
- Code eval environment: Ubuntu 22.04, Python 3.12
- Retry on API failures: up to 30 attempts

### How They Test Models
They call the model's API endpoint (OpenAI-compatible format):
- POST /v1/chat/completions
- Send benchmark questions
- Receive responses
- Score with equality checker LLM, regex extraction, or code execution

### What This Means For Us
We need to provide an OpenAI-compatible API endpoint. They will call it, send questions, and score our responses. We appear as a "model" to them, even though we're an orchestration system.

---

## 2. HOW TO GET LISTED ON ARTIFICIAL ANALYSIS

### The Process
1. Build an OpenAI-compatible API endpoint
2. Contact Artificial Analysis via hello@artificialanalysis.ai
3. Provide them:
   - API endpoint URL (e.g., https://temuclaude.com/v1/chat/completions)
   - API key (for authentication)
   - Model name (e.g., "temuclaude")
   - Pricing information
4. They add us to their testing queue
5. They run their 9 benchmark evaluations against our endpoint
6. Results appear on their leaderboard

### Alternative: OpenRouter Integration
Fugu is listed on OpenRouter. ArtificialAnalysis tests through OpenRouter.
If we become an OpenRouter provider (via "Private Models Beta"), we automatically get tested.
- OpenRouter Private Models: bring your own endpoint, OpenRouter routes to it
- Users can call "temuclaude" through OpenRouter
- ArtificialAnalysis tests through OpenRouter
- We get listed without directly contacting ArtificialAnalysis

### What We Need to Provide

For ArtificialAnalysis to test us, our API must:
1. Be OpenAI-compatible (POST /v1/chat/completions)
2. Accept standard OpenAI request format:
   ```json
   {
     "model": "temuclaude",
     "messages": [{"role": "user", "content": "question"}],
     "temperature": 0,
     "max_tokens": 16384
   }
   ```
3. Return standard OpenAI response format:
   ```json
   {
     "id": "chatcmpl-...",
     "object": "chat.completion",
     "choices": [{"message": {"role": "assistant", "content": "answer"}, "finish_reason": "stop"}],
     "usage": {"prompt_tokens": 100, "completion_tokens": 200}
   }
   ```
4. Support streaming (optional but preferred)
5. Be reliable (they retry 30 times on failure)
6. Return token usage in the response

### Critical Requirements
- Temperature 0 support (for non-reasoning evaluation)
- Temperature 0.6 support (for reasoning models)
- Max tokens up to 16,384
- No rate limiting on their test IP (they send many requests)
- Response time < 60 seconds per query
- Must not refuse benchmark questions (no safety filters that block test queries)

---

## 3. BENCHMARK EVALUATION DETAILS

### HLE (Humanity's Last Exam)
- 2,158 questions
- 1 repeat (pass@1)
- Open answer format
- Scored with equality checker LLM
- Weight: 12%
- Our projected score: 50.0% (based on Fugu Ultra)

### GPQA Diamond
- 198 questions
- 5 repeats (pass@1 averaged)
- Multiple choice (4 options)
- Regex extraction for answer
- Weight: 6%
- Our projected score: 95.5%

### Terminal-Bench v2.1
- 89 tasks
- 3 repeats
- Terminal-based task execution
- Test suite pass/fail
- Weight: 16%
- Our projected score: 82.1%
- This is our weakest benchmark (Fable 5 beats us at 85%)

### SciCode
- 288 subproblems
- 3 repeats
- Python code (must pass all unit tests)
- Code execution scoring
- Weight: 8%
- Our projected score: 58.7%

### GDPval-AA v2
- 220 tasks
- 1 repeat
- Agentic task completion with file outputs
- Pairwise comparison (Elo) by judge panel
- Weight: 20%
- Our projected score: 63% (from PLAN-v2)

### τ³-Banking
- 97 tasks
- 5 repeats
- Dual control agent-user simulation
- Backend database state evaluation
- Weight: 14%
- Our projected score: 21.7%

### AA-LCR (Long Context Reasoning)
- 100 questions
- 3 repeats
- Open answer
- Equality checker LLM
- Weight: 6%
- Our projected score: 74.7%

### AA-Omniscience
- 6,000 questions
- 1 repeat
- Open answer
- Accuracy (8%) + 1 - Hallucination Rate (4%)
- Weight: 12%

### CritPt
- 70 questions
- 5 repeats
- Python functions, symbolic expressions, numerical answers
- Official grading server
- Weight: 6%

---

## 4. API SERVICE ARCHITECTURE

### What We Need to Build

#### A. OpenAI-Compatible Endpoint
Route: POST /v1/chat/completions
- Accept standard OpenAI request format
- Return standard OpenAI response format
- Support: model, messages, temperature, max_tokens, stream
- Authenticate via Bearer token (API key)

#### B. API Key Authentication
- Check Authorization header: `Bearer tmc_xxxxx`
- Validate against database
- Return 401 if invalid
- Rate limit per key

#### C. Usage Metering
- Count input/output tokens per API key
- Track in database
- Enforce plan limits:
  - Free: 100/day (playground only, no API access)
  - Developer: 50,000/month
  - Pro: 500,000/month
  - Enterprise: Unlimited
  - PAYG: unlimited (billed per token)

#### D. Rate Limiting
- Pro: 100 requests/minute
- Enterprise: 1,000 requests/minute
- PAYG: 100 requests/minute
- Return 429 if exceeded

#### E. Database (Vercel Postgres)
- Users table (email, plan, created_at)
- API keys table (key_hash, user_id, last_used)
- Usage table (user_id, date, query_count, input_tokens, output_tokens)
- Subscriptions table (razorpay_subscription_id, status, plan)

### API Response Format (Must Match OpenAI Exactly)

```json
{
  "id": "chatcmpl-temuclaude-xxxxxxxxx",
  "object": "chat.completion",
  "created": 1783140000,
  "model": "temuclaude",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The answer is..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 50,
    "completion_tokens": 100,
    "total_tokens": 150
  }
}
```

### Streaming Format (SSE)
```
data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","choices":[{"delta":{"content":"The"}}]}

data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","choices":[{"delta":{"content":" answer"}}]}

data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","choices":[{"delta":{"content":" is..."}}]}

data: [DONE]
```

---

## 5. EXECUTION PLAN

### Phase A: Database (Step 9)
1. Set up Vercel Postgres (free tier, 256MB)
2. Get connection string
3. Add to Vercel env vars
4. Rewrite db.ts to use Postgres instead of JSON file
5. Test: create user, create API key, track usage

### Phase B: OpenAI-Compatible API (Step 4a)
1. Create /v1/chat/completions route
2. Add API key authentication
3. Add rate limiting
4. Add usage metering
5. Match OpenAI response format exactly
6. Support streaming (SSE)
7. Return token usage
8. Test with curl (OpenAI format)

### Phase C: Run Our Own Benchmarks (Step 4b)
1. Run 5 questions on hard_reasoning.json
2. Baseline: GLM-5.2 alone
3. Full: Temuclaude orchestration
4. Compare scores
5. Document results
6. Cost: ~$0.05 (5 queries)

### Phase D: Get Verified (Step 12)
Option 1: Contact ArtificialAnalysis directly
- Email hello@artificialanalysis.ai
- Provide: API endpoint, API key, model name, pricing
- Wait for them to test (may take weeks)

Option 2: OpenRouter Private Models
- Register as OpenRouter provider
- Bring our endpoint as a "Private Model"
- OpenRouter tests through their pipeline
- ArtificialAnalysis picks up automatically
- Faster, more credible

### Phase E: Launch
- Step 11: Blog post with real scores
- Step 13: Product Hunt
- Step 14: Hacker News

---

## 6. COST ANALYSIS FOR BENCHMARKS

### Running Our Own Benchmarks
- 5 questions × $0.005/query = $0.025
- 15 questions × $0.005/query = $0.075
- 50 questions × $0.005/query = $0.25
- Full 9 benchmarks (~3,500 questions) = ~$17.50

### ArtificialAnalysis Testing
- They pay for their own API calls
- We provide free API access during testing
- Cost to us: $0 (they use their credits)
- But: our endpoint calls OpenRouter, so we pay
- 3,500 questions × $0.005 = ~$17.50
- With $7 credits: can run 1,400 queries (enough for partial benchmarks)

### Recommendation
- Run 50 questions ourselves first ($0.25)
- Verify scores match projections
- Then contact ArtificialAnalysis with real numbers
- They may run full suite or subset

---

## 7. KEY INSIGHTS FROM RESEARCH

1. ArtificialAnalysis tests via API — we must be OpenAI-compatible
2. They use pass@1 scoring — first attempt must be correct
3. Temperature 0 for non-reasoning, 0.6 for reasoning
4. No safety filters that block test queries
5. Must return token usage in response
6. Must handle 30 retries on failure (reliability)
7. Response time < 60 seconds per query
8. OpenRouter Private Models is the fastest path to verification
9. Fugu got listed by being on OpenRouter — same path for us
10. Our "9/9 benchmarks beaten" claim is based on Fugu Ultra's published scores — we need to verify with our own tests

---

## 8. WHAT WE MUST NOT DO

- Don't add safety filters that block benchmark questions
- Don't refuse to answer — benchmarks test knowledge, not safety
- Don't add custom system prompts that change answers (AA uses zero-shot)
- Don't add rate limits that block ArtificialAnalysis testing
- Don't change response format from OpenAI standard
- Don't omit token usage from response
- Don't exceed 60 second response time

---

## CONCLUSION

The path to verified benchmarks:
1. Build Postgres database (Step 9)
2. Build OpenAI-compatible API endpoint (Step 4a)
3. Run our own 50-question benchmark (Step 4b)
4. Contact ArtificialAnalysis or OpenRouter for verification (Step 12)
5. Get listed on their leaderboard

Total cost: ~$0.25 for our tests + $17.50 if AA runs full suite
With $7 credits: enough for our tests + partial AA testing

Start with Step 9 (Postgres), then Step 4a (API endpoint), then Step 4b (benchmarks).