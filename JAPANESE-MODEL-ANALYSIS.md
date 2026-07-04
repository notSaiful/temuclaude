# Japanese AI Model Ecosystem — Deep Analysis for Temuclaude

## Why This Matters for Temuclaude

These Japanese models represent a different philosophy from the Chinese models we're using: lightweight, culturally specialized, efficiency-focused. Like Sakana AI (which means "fish" in Japanese), they follow a nature-inspired, efficient approach.

**For Temuclaude, the relevance is:**
1. Some of these models are available on Ollama and could join our model pool
2. Their fine-tuning approaches (continual pre-training on specific corpora) could inform our skill design
3. For Japanese/bilingual tasks, these models could beat our Chinese models
4. Their lightweight efficiency aligns with our cost-saving mission

---

## 1. SWALLOW (Tokyo Tech / AIST)

**What it is:** Academic project by Institute of Science Tokyo + AIST. Continually pre-trains foundational architectures (Llama, Mistral, Gemma, Qwen, GPT-OSS) on massive Japanese corpora.

**Model lineup (as of March 2026):**
- GPT-OSS Swallow — based on OpenAI's open model
- Qwen3 Swallow — based on Alibaba's Qwen3
- Gemma-2-Llama Swallow
- Llama 3.3 Swallow 70B
- Llama 3.1 Swallow 8B v0.5
- Llama 3 Swallow
- Swallow (Mistral) — based on Mistral 7B
- SwallowCode-v2 — coding-focused

**Stats:**
- 2.4M model downloads
- 551K dataset downloads
- 132 models released
- 19 datasets
- Permissive licenses (commercial use allowed)

**Key strength:** Takes the best open architectures and adds deep Japanese language understanding through continual pre-training. This is exactly what we could do for Temuclaude — take our models and continually pre-train on benchmark-specific data.

**Architecture:** Llama-based (LlamaForCausalLM), so compatible with Ollama.

**Ollama availability:** Likely available via community GGUF conversions. Llama-based models convert easily.

**Relevance for Temuclaude:** If we need Japanese language support, Swallow models are the best open-weight option. They also prove that continual pre-training on domain-specific data works — we could apply the same technique to our model pool for benchmark optimization.

---

## 2. ELYZA (ELYZA Inc.)

**What it is:** Tokyo University Matsuo Lab spinoff. Fine-tunes Llama models for high-quality Japanese instruction-following.

**Model lineup:**
- Llama-3-ELYZA-JP-8B — 7,227 downloads, 149 likes
- Based on Llama 3 architecture

**Key strength:** Highly efficient Japanese conversational AI. Excel at natural conversational routing — exactly the kind of routing we need for Temuclaude's query classification.

**Architecture:** LlamaForCausalLM, Ollama-compatible.

**Relevance for Temuclaude:** Could serve as a lightweight router model for Japanese queries. ELYZA's approach (fine-tuning for instruction-following) is what we do with skills — but at the weight level.

---

## 3. PLaMo (Preferred Networks)

**What it is:** Ground-up bilingual (JP/EN) foundation model. Built from scratch, not fine-tuned from existing models. By Preferred Networks (Japanese tech giant).

**Model lineup:**
- PLaMo 3: 31B, 8B, 2B variants (NICT collaboration)
- PLaMo 2: 1B (34.9K downloads), translate 10B (6K downloads)
- PLaMo 2-VL: 8B and 2B vision-language models
- Custom architecture: Plamo2ForCausalLM (not Llama-based)

**Key strength:** Built from scratch for bilingual efficiency. High computational efficiency. Deep cultural context. Apache 2.0 license.

**Architecture:** Custom (Plamo2ForCausalLM). NOT Llama-based — has its own architecture. Uses hybrid state space models for efficient unlimited context.

**Ollama availability:** Uncertain — custom architecture may need conversion. The 1B model could run locally.

**Relevance for Temuclaude:** PLaMo's from-scratch bilingual approach is interesting but not directly useful for our orchestration. However, their hybrid state space model architecture (unlimited context) is worth studying — could inform how we handle very long context tasks.

---

## 4. RAKUTEN AI

**What it is:** Rakuten's suite of open models optimized for Japanese enterprise use.

**Model lineup:**
- RakutenAI-3.0 — **671B MoE** (DeepseekV3 architecture, FP8 quantized) — 108 downloads, 77 likes
- RakutenAI-2.0-mini — 2B
- RakutenAI-2.0-8x7B — 47B MoE
- RakutenAI-7B — 7B
- Apache 2.0 license

**Key strength:** RakutenAI-3.0 is a **671B parameter MoE model** — same size class as DeepSeek V3/V4. Built on DeepseekV3 architecture. Optimized for Japanese + English bilingual enterprise use.

**Architecture:** DeepseekV3ForCausalLM — same as DeepSeek V3/V4 Pro. FP8 quantized.

**Ollama availability:** 671B is very large. Would need significant hardware or cloud hosting. The 7B and 2B variants are Ollama-friendly.

**Relevance for Temuclaude:** **This is significant.** RakutenAI-3.0 is a 671B MoE model on the same architecture as DeepSeek V4 Pro. If it's available on Ollama Cloud (or could be), it could serve as a Japanese-specialized alternative to DeepSeek V4 Pro. For Japanese benchmarks, this could outperform our Chinese models.

**The 7B/2B variants** could serve as lightweight Japanese routers — cheap, fast, locally deployable.

---

## 5. KARAKURI LM (Karakuri Inc.)

**What it is:** Open-weight models for Japanese conversational AI, RAG, and customer support.

**Model lineup:**
- karakuri-lm-70b-chat-v0.1 — 70B, conversational
- karakuri-lm-70b-v0.1 — 70B base
- karakuri-lm-8x7b-chat-v0.1 — 47B MoE, conversational
- karakuri-lm-32b-thinking-2501-exp — **32B with thinking/reasoning** (100 downloads)
- karakuri-vl-32b-thinking-2507-exp — **32B vision+language with thinking** (70 downloads)
- karakuri-vl-2-8b-thinking-2603 — 8B VL with thinking
- karakuri-lm-7b-apm-v0.1/v0.2 — 7B, conversational + APM (appearance-based)

**Key strength:** The "thinking" models are the most interesting — they have reasoning capabilities similar to DeepSeek R1's chain-of-thought. The VL (vision-language) thinking model could handle multimodal Japanese tasks.

**Relevance for Temuclaude:** The 32B thinking model could be a lightweight reasoning specialist for Japanese tasks. The VL thinking model could handle vision tasks in Japanese — something our current pool doesn't specialize in.

---

## 6. JAPANESE STABLE LM (Stability AI)

**What it is:** Stability AI's Tokyo-based research team. Highly efficient, open-weight Japanese language models.

**Model lineup:**
- japanese-stablelm-base-alpha-7b — 241 downloads, 121 likes
- japanese-stablelm-instruct-alpha-7b-v2 — 36 downloads
- japanese-stablelm-3b-4e1t-base — 3B, efficient

**Key strength:** Stability AI's expertise in efficient architectures. The 3B model is extremely lightweight.

**Relevance for Temuclaude:** The 3B model could serve as an ultra-lightweight Japanese router — fast, cheap, locally deployable. For simple Japanese queries, this costs almost nothing.

---

## 7. RINNA (Rinna Co., Ltd.)

**What it is:** Pioneer in Japanese AI. Specializes in smaller, highly efficient language models (sub-10B) for edge devices.

**Model lineup:**
- qwen2.5-bakeneko-32b-instruct-v2 — 32B, based on Qwen2.5
- qwq-bakeneko-32b — 32B reasoning model (based on QwQ)
- deepseek-r1-distill-qwen2.5-bakeneko-32b — DeepSeek R1 distilled for Japanese
- llama-3-youko-70b / 8b — Llama 3 based
- gemma-2-baku-2b — 2B, based on Gemma 2
- nekomata-14b / 7b — older models

**Key strength:** Rinna's philosophy is Sakana-like — lightweight, efficient, edge-deployable. They distill large models (DeepSeek R1, QwQ) into Japanese-optimized versions. The "bakeneko" (化け猫, supernatural cat) line is their flagship.

**Relevance for Temuclaude:** **The DeepSeek R1 distillation for Japanese is very interesting.** It takes DeepSeek R1's reasoning capability and optimizes it for Japanese. If we need Japanese reasoning, this could be our specialist — lighter than full DeepSeek V4 Pro but with similar reasoning quality for Japanese tasks.

The 2B baku model could be an ultra-cheap Japanese router.

---

## 8. FUGAKU-LLM (RIKEN)

**What it is:** Trained on the RIKEN Fugaku supercomputer (formerly world's fastest). Purely domestic Japanese LLM trained entirely on locally sourced data.

**Model lineup:**
- Fugaku-LLM-13B — 134 likes, 24 downloads
- Fugaku-LLM-13B-instruct — 29 likes
- Fugaku-LLM-13B-instruct-gguf — 43 likes (GGUF = Ollama ready)

**Key strength:** Trained entirely on Japanese infrastructure with Japanese data. Strict adherence to Japanese cultural and corporate standards. The GGUF version is Ollama-ready.

**Relevance for Temuclaude:** The 13B GGUF model could run on Ollama for Japanese-specific tasks. It's the most "domestically Japanese" model — no foreign pre-training data. For tasks requiring strict Japanese cultural compliance, this is the specialist.

---

## COMPARATIVE ANALYSIS

| Model | Size | Architecture | Japanese Quality | Ollama Ready | Best For |
|-------|------|-------------|-----------------|-------------|----------|
| Swallow 70B | 70B | Llama 3.3 | Excellent | Likely (Llama) | General Japanese tasks |
| ELYZA-JP 8B | 8B | Llama 3 | Good | Yes (Llama) | Japanese routing, chat |
| PLaMo 2 | 1B-31B | Custom | Excellent (native) | Uncertain | Bilingual efficiency |
| RakutenAI-3.0 | 671B | DeepseekV3 | Excellent | Needs cloud | Japanese enterprise MoE |
| Karakuri 32B Thinking | 32B | Llama-based | Good + reasoning | Likely | Japanese reasoning |
| Japanese Stable LM | 3B-7B | Custom | Good | Yes | Lightweight Japanese |
| Rinna Bakeneko 32B | 32B | Qwen2.5 | Excellent + reasoning | Likely (Qwen) | Japanese reasoning (distilled R1) |
| Fugaku-LLM | 13B | Custom | Pure domestic | Yes (GGUF) | Japanese cultural compliance |

---

## HOW THESE FIT INTO TEMUCLAUDE

### Scenario 1: Japanese Benchmark Support
If we want to compete on Japanese benchmarks (like Japanese-SimpleQA where DeepSeek V4 Pro scores 84.4%), we could add:
- **Rinna Bakeneko 32B** (DeepSeek R1 distilled for Japanese) as our Japanese reasoning specialist
- **Swallow 70B** as our Japanese general model
- **RakutenAI-3.0** (if available on Ollama Cloud) as our Japanese MoE powerhouse

### Scenario 2: Lightweight Routing
For routing Japanese queries cheaply:
- **ELYZA-JP 8B** — fast, efficient, good at instruction-following
- **Japanese Stable LM 3B** — ultra-lightweight
- **Rinna Baku 2B** — smallest, cheapest

### Scenario 3: Multilingual Expansion
The philosophy of these models — continual pre-training on domain-specific corpora — is exactly what we could do for Temuclaude:
- Take our 5 Ollama Cloud models
- Apply continual pre-training on benchmark-specific data
- Create Temuclaude-specialized variants

### Scenario 4: Cultural Compliance
For users who need strict data sovereignty (like Japanese enterprise):
- **Fugaku-LLM** — purely domestic, no foreign data
- This is a selling point Fugu/Fable 5 can't match

---

## KEY INSIGHTS FOR TEMUCLAUDE

1. **The Japanese ecosystem proves continual pre-training works.** Swallow takes Llama and makes it Japanese-expert. We could take GLM-5.2 and make it benchmark-expert.

2. **Distillation is powerful.** Rinna distills DeepSeek R1 into a 32B Japanese model. We could distill our orchestration strategies into lighter models.

3. **Lightweight routing is viable.** 2B-8B models can serve as fast, cheap routers. We don't need GLM-5.2 for every routing decision.

4. **MoE scales.** RakutenAI-3.0 (671B MoE) proves the DeepseekV3 architecture scales for Japanese. Our DeepSeek V4 Pro is already on this architecture.

5. **Thinking models matter.** Karakuri and Rinna both have "thinking" variants. Our DeepSeek V4 Pro already has 3 thinking modes. The lesson: always use max thinking for hard problems.

6. **Cultural specialization is a market.** These companies exist because Japanese users need Japanese-optimized AI. Temuclaude could specialize per language/region — something Fugu (closed, Japan-focused) doesn't offer as a feature.

7. **Open-weight philosophy is shared.** All 8 companies release open-weight models. This aligns with our mission. We're not alone in believing open beats closed.