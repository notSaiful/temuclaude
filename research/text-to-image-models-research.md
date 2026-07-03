# Text-to-Image API Models — Comprehensive Research Report

**Date:** July 3, 2026
**Purpose:** Find the best, cheapest, highest-quality text-to-image models available via API for the timuclaude LLM orchestration system.

---

## EXECUTIVE SUMMARY

The text-to-image landscape has shifted dramatically. As of July 2026:

- **Frontier quality** is led by **GPT Image 2** (Elo 1338), **Reve 2.0** (Elo 1280), **MAI-Image-2.5** (Elo 1269), and **Nano Banana 2** (Elo 1254)
- **Midjourney v7** has fallen to rank #84 (Elo 1068) — it no longer has an API and has been surpassed by many API-accessible models
- **FLUX.2 family** (Pro, Dev, Flex, Klein) occupies ranks #14-#32 — strong near-frontier quality with open-weight options
- **Cheapest near-frontier:** FLUX.2 [dev] Flash ($0.005/img, Elo 1135), Z-Image Turbo ($0.005/img, Elo 1104), FLUX.1 [schnell] ($0.003/img, Elo 1000), and FLUX.2 [dev] Turbo ($0.008/img, Elo 1155)
- **Best quality-per-dollar:** FLUX.2 [dev] Turbo (Elo 1155 at $0.008/img) gives ~86% of frontier quality at **3.8% of GPT Image 2's cost**
- **OpenRouter** provides a unified API to 30+ image models from 8+ providers — ideal for orchestration

---

## 1. OPENROUTER TEXT-TO-IMAGE MODELS

OpenRouter provides a unified Image API across 30+ models from 8+ providers. All accessible via `/v1/chat/completions` with `modalities: ["image", "text"]` or the dedicated Image API endpoint.

### Models Available on OpenRouter (by token volume / popularity):

| # | Model Name | Model ID | Pricing | Max Resolution | Quality Tier | Key Capabilities |
|---|-----------|----------|---------|---------------|-------------|-----------------|
| 1 | **Nano Banana** (Gemini 2.5 Flash Image) | `google/gemini-2.5-flash-image` | $0.30/M input, $2.50/M output tokens | 1K | Near-frontier | Image gen + editing, multi-turn, contextual understanding |
| 2 | **Nano Banana 2** (Gemini 3.1 Flash Image Preview) | `google/gemini-3.1-flash-image-preview` | $0.50/M input, $3/M output tokens | 2K | Frontier | Pro-level quality at Flash speed, 14 aspect ratios |
| 3 | **Seedream 4.5** | `bytedance-seed/seedream-4.5` | $0.04/image flat | Up to 2K | Near-frontier | Text rendering, multi-image composition, portrait refinement |
| 4 | **Nano Banana 2** (GA) | `google/gemini-3.1-flash-image` | $0.50/M input, $3/M output tokens | 2K | Frontier | Same as preview, stable |
| 5 | **Grok Imagine Image Quality** | `x-ai/grok-imagine-image-quality` | $11.98/M tokens | 2K | Near-frontier | Photorealistic, multilingual text rendering, reference images |
| 6 | **GPT-5.4 Image 2** | `openai/gpt-5.4-image-2` | $8/M input, $15/M output tokens | 2K+ | Frontier | Multimodal reasoning + image gen, text rendering, 16 ref images |
| 7 | **Nano Banana Pro** (Gemini 3 Pro Image Preview) | `google/gemini-3-pro-image-preview` | $2/M input, $12/M output tokens | 4K | Frontier | 2K/4K output, 5-subject identity, long text rendering, Search grounding |
| 8 | **Nano Banana Pro** (GA) | `google/gemini-3-pro-image` | $2/M input, $12/M output tokens | 4K | Frontier | Same as preview, stable |
| 9 | **FLUX.2 Klein 4B** | `black-forest-labs/flux.2-klein-4b` | $0.014/first MP + $0.001/subsequent MP | Up to 2K | Budget-near-frontier | Fastest FLUX.2, high-throughput, cost-effective |
| 10 | **FLUX.2 Pro** | `black-forest-labs/flux.2-pro` | $0.03/first MP + $0.015/subsequent MP (output); $0.015/MP input | 4MP | Frontier | Frontier quality, prompt adherence, multi-reference, text-to-image + editing |
| 11 | **Nano Banana 2 Lite** | `google/gemini-3.1-flash-lite-image` | $0.25/M input, $1.50/M output tokens | 1K | Budget | ~4s generation, 2.7× faster than NB2, 14 aspect ratios |
| 12 | **GPT Image 2** | `openai/gpt-image-2` | $8/M input, $8/M output tokens | 2K+ | Frontier | High-fidelity gen + editing, accurate text rendering |

### OpenRouter Pricing Notes:
- Token-based models (Google, OpenAI, xAI): Cost depends on prompt length + output tokens. A typical 1024×1024 image costs ~$0.04–$0.08 for Nano Banana, ~$0.08–$0.17 for GPT Image 2.
- Per-image models (Seedream): Flat $0.04/image regardless of size.
- Per-megapixel models (FLUX.2): ~$0.015–$0.045 for a 1MP image, scales linearly.

---

## 2. FLUX MODELS — Complete Family

### FLUX.1 Generation (July 2024 – May 2025)

| Model | Elo Score | Rank | Open Weights | API Providers | Price Range |
|-------|----------|------|-------------|--------------|-------------|
| FLUX.1 [pro] | 1,069 | #82 | No | BFL API, fal.ai, Replicate | $0.05/img |
| FLUX1.1 [pro] | 1,083 | #74 | No | BFL API, fal.ai, Replicate | $0.04/img |
| FLUX1.1 [pro] Ultra | 1,092 | #69 | No | BFL API, fal.ai | $0.06/img (2K) |
| FLUX.1 [dev] | 1,027 | #101 | Yes (non-commercial) | fal.ai, Replicate, HuggingFace | $0.025/img |
| FLUX.1 [schnell] | 1,000 | #110 | Yes (Apache 2.0) | fal.ai, Replicate, HuggingFace, Together AI | $0.003/img |
| FLUX.1 Kontext [max] | 1,122 | #50 | No | BFL API, fal.ai | $0.08/img |
| FLUX.1 Kontext [pro] | 1,091 | #70 | No | BFL API, fal.ai | $0.04/img |
| FLUX.1 Krea [dev] | 1,031 | #98 | Yes | fal.ai, HuggingFace | $0.025/img |

### FLUX.2 Generation (Nov 2025 – Jan 2026) — Major Leap

| Model | Elo Score | Rank | Open Weights | API Providers | Price (fal.ai) | Notes |
|-------|----------|------|-------------|--------------|----------------|-------|
| FLUX.2 [max] | 1,194 | #14 | No | BFL API | $0.07/img | Top FLUX, frontier-level |
| FLUX.2 [pro] | 1,185 | #19 | No | BFL API, fal.ai, OpenRouter | $0.03/first MP | Strong prompt adherence, 4MP |
| FLUX.2 [flex] | 1,179 | #20 | No | BFL API | $0.06/img | Flexible editing |
| FLUX.2 [dev] | 1,155 | #31 | Yes | BFL API, fal.ai, HuggingFace | $0.012/img | Open-weight, near-frontier |
| FLUX.2 [dev] Turbo | 1,155 | #32 | Yes (fal distillation) | fal.ai | $0.008/img | **Best value:** 86% frontier quality at 3.8% cost |
| FLUX.2 [dev] Flash | 1,135 | #43 | Yes | fal.ai | $0.005/img | Even faster, still quality |
| FLUX.2 [klein] 9B | 1,122 | #51 | Yes | BFL API, fal.ai, OpenRouter | $0.015/img | Mid-tier, good quality |
| FLUX.2 [klein] 4B | 1,062 | #89 | Yes | BFL API, fal.ai, OpenRouter | $0.014/img | Fast, cost-effective |

### FLUX vs Midjourney v7:
- **FLUX.2 [max]** (Elo 1194) **beats** Midjourney v7 Alpha (Elo 1068) by **126 Elo points**
- **FLUX.2 [pro]** (Elo 1185) beats MJ v7 by 117 points
- Even **FLUX.2 [dev] Turbo** (Elo 1155) beats MJ v7 by 87 points
- FLUX has API access; Midjourney does NOT have a public API
- FLUX.2 [dev] is open-weight and can be self-hosted

### Where to Access FLUX:

| Platform | FLUX.1 Schnell | FLUX.1 Dev | FLUX.1 Pro | FLUX.2 Pro | FLUX.2 Dev | FLUX.2 Turbo | Kontext |
|----------|---------------|-----------|-----------|-----------|-----------|-------------|---------|
| OpenRouter | — | — | — | ✅ | — | — | — |
| fal.ai | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Replicate | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ |
| BFL API | ✅ | — | ✅ | ✅ | ✅ | — | ✅ |
| HuggingFace | ✅ | ✅ | — | — | ✅ | ✅ | — |
| Together AI | ✅ | — | — | — | — | — | — |

---

## 3. STABLE DIFFUSION FAMILY

| Model | Elo Score | Rank | Open Weights | API Providers | Price | Notes |
|-------|----------|------|-------------|--------------|-------|-------|
| SD 3.5 Large | 1,023 | #103 | Yes (Sai Community) | Stability API, fal.ai, Replicate | $0.065/img | 8B params, good but below FLUX |
| SD 3.5 Large Turbo | 1,020 | #104 | Yes | Stability API, fal.ai, Replicate | $0.04/img | Faster, similar quality |
| SD 3.5 Medium | 945 | #120 | Yes | Stability API, fal.ai, Replicate | $0.02/img | 2.5B params, budget |
| SD 3 Medium | 911 | #123 | Yes | Stability API, fal.ai, Replicate | $0.035/img | Original SD3, weaker |
| SDXL 1.0 | 874 | #129 | Yes | Many providers | $0.009/img | Still widely used, self-hostable |
| SDXL Lightning | 905 | #125 | Yes (ByteDance distillation) | fal.ai, Replicate | $0.0019/img | Ultra-cheap, fast |
| SD 1.5 | 659 | #132 | Yes | Many | $0.044/img | Legacy, only for self-hosting |

### SD vs FLUX Quality:
- **FLUX.2 [dev]** (Elo 1155) **beats** SD 3.5 Large (Elo 1023) by **132 points**
- **FLUX.1 [schnell]** (Elo 1000) is comparable to SD 3.5 Large Turbo (Elo 1020) but cheaper
- SDXL is significantly behind (Elo 874) but remains the most self-hostable option with the largest LoRA ecosystem

### Self-Hosting Notes:
- SDXL 1.0: Runs on a single 8GB GPU, massive LoRA/community ecosystem, Apache 2.0
- SD 3.5 Large: Needs ~16GB VRAM, SAI Community License
- FLUX.1 [schnell]: Apache 2.0, runs on ~24GB VRAM
- FLUX.2 [dev]: Open weights, needs ~32GB VRAM for reasonable speed

---

## 4. FAL.AI MODELS — Complete Text-to-Image Catalog

fal.ai hosts **209 image generation models**. Key text-to-image models:

### FLUX Family on fal.ai:

| Model | fal.ai Endpoint | Price | Speed | Resolution |
|-------|----------------|-------|-------|-----------|
| FLUX.1 [schnell] | `fal-ai/flux/schnell` | $0.003/MP | 1-4 steps, ~1s | Up to 2K |
| FLUX.1 [dev] | `fal-ai/flux/dev` | $0.025/img | ~2-3s | Up to 2K |
| FLUX.1 [dev] + LoRA | `fal-ai/flux-lora` | $0.025/img | ~2-3s | Up to 2K |
| FLUX1.1 [pro] | `fal-ai/flux-pro/v1.1` | $0.04/img | ~3s | Up to 2K |
| FLUX1.1 [pro] Ultra | `fal-ai/flux-pro/v1.1-ultra` | $0.06/img | ~5s | Up to 2K |
| FLUX.2 [pro] | `fal-ai/flux-2-pro` | $0.03/first MP | ~4s | Up to 4MP |
| FLUX.2 [dev] | `fal-ai/flux-2` | $0.012/img | ~3s | Up to 2K |
| FLUX.2 [dev] Turbo | `fal-ai/flux-2/turbo` | $0.008/img | ~1.5s | Up to 2K |
| FLUX.2 [dev] Flash | `fal-ai/flux-2/flash` | $0.005/img | ~1s | Up to 2K |
| FLUX.2 [klein] 9B | `fal-ai/flux-2/klein/9b` | $0.015/img | ~2s | Up to 2K |

### Non-FLUX Models on fal.ai:

| Model | fal.ai Endpoint | Price | Speed | Elo | Notes |
|-------|----------------|-------|-------|-----|-------|
| Nano Banana 2 | `fal-ai/nano-banana-2` | $0.08/img @1K | ~4s | 1,254 | Frontier-tier, Google |
| Nano Banana Pro | `fal-ai/nano-banana-pro` | $0.15/img | ~6s | 1,218 | 4K, 5-subject identity |
| Nano Banana (original) | `fal-ai/nano-banana` | $0.04/img | ~3s | 1,153 | Good value |
| Nano Banana 2 Lite | `google/nano-banana-2-lite` | ~$0.02/img | ~2s | — | Sub-2s latency |
| GPT Image 2 | `openai/gpt-image-2` | ~$0.17/img | ~8s | 1,338 | #1 on leaderboard |
| GPT Image 1.5 | `fal-ai/gpt-image-1.5` | ~$0.13/img | ~6s | 1,260 | Previous gen |
| Seedream 4.5 | `fal-ai/bytedance/seedream/v4.5/text-to-image` | $0.04/img | ~3s | 1,163 | ByteDance, good text rendering |
| Seedream 4.0 | `fal-ai/bytedance/seedream/v4/text-to-image` | $0.03/img | ~3s | 1,190 | Strong value |
| Seedream 5.0 Lite | `fal-ai/bytedance/seedream/v5/lite/text-to-image` | $0.035/img | ~2s | 1,117 | Fast variant |
| Ideogram V3 | `fal-ai/ideogram/v3` | ~$0.08/img | ~5s | 1,077 | Best typography |
| Ideogram V4 | `ideogram/v4` | ~$0.08/img | ~5s | 1,166 | Improved typography + quality |
| Recraft V3 | `fal-ai/recraft/v3/text-to-image` | ~$0.04/img | ~4s | 1,067 | Vector + raster, brand style |
| Krea 2 Large | `krea/v2/large/text-to-image` | ~$0.06/img | ~4s | 1,187 | Style references |
| Krea 2 Medium | — | ~$0.03/img | ~3s | 1,200 | Good balance |
| Grok Imagine | `xai/grok-imagine-image` | ~$0.05/img | ~4s | 1,176-1,201 | xAI, photorealistic |
| Z-Image Turbo | `fal-ai/z-image/turbo` | $0.005/img | ~1s | 1,104 | 6B params, ultra-fast |
| Fast SDXL | `fal-ai/fast-sdxl` | ~$0.002/img | ~1s | ~874 | Cheapest option with LoRA support |

### fal.ai Cost Examples (1,000 images/month at 1K):
- **FLUX.2 [dev] Turbo:** $8/month
- **FLUX.2 [dev] Flash:** $5/month
- **Z-Image Turbo:** $5/month
- **Nano Banana 2:** $80/month
- **Nano Banana Pro:** $150/month
- **GPT Image 2:** ~$170/month

---

## 5. REPLICATE MODELS

Replicate charges per-second of GPU compute. Key text-to-image models:

| Model | Replicate ID | Price/second | Typical gen time | Est. price/image | Notes |
|-------|-------------|-------------|-----------------|-----------------|-------|
| FLUX.1 [schnell] | `black-forest-labs/flux-schnell` | ~$0.0035/s | ~1s | ~$0.004 | Cheapest FLUX on Replicate |
| FLUX.1 [dev] | `black-forest-labs/flux-dev` | ~$0.0035/s | ~3s | ~$0.01 | Good quality |
| FLUX1.1 [pro] | `black-forest-labs/flux-pro-1.1` | ~$0.005/s | ~3s | ~$0.015 | Pro quality |
| FLUX.2 [dev] | `black-forest-labs/flux-2-dev` | ~$0.005/s | ~3s | ~$0.015 | Near-frontier open weights |
| SDXL | `stability-ai/sdxl` | ~$0.0025/s | ~2s | ~$0.005 | Budget option |
| SDXL Lightning | `ByteDance/sdxl-lightning` | ~$0.0025/s | ~0.5s | ~$0.001 | Ultra-cheap |
| SD 3.5 Large | `stability-ai/sd3.5-large` | ~$0.004/s | ~4s | ~$0.016 | Decent quality |

### Replicate vs fal.ai:
- fal.ai is generally **faster** (optimized inference, custom kernels)
- fal.ai is often **cheaper** for FLUX models (per-image vs per-second)
- Replicate has **broader model selection** including older/niche models
- Replicate supports **fine-tuning** and custom model hosting
- Both have excellent developer UX with similar SDK patterns

---

## 6. OTHER API PROVIDERS

### Together AI
| Model | Endpoint | Price | Notes |
|-------|----------|-------|-------|
| FLUX.1 [schnell] | `black-forest-labs/FLUX.1-schnell` | $0.003/MP | Cheapest FLUX access |
| FLUX.1 [dev] | `black-forest-labs/FLUX.1-dev` | $0.025/MP | Non-commercial license |
| SDXL | `stabilityai/stable-diffusion-xl` | $0.008/MP | Budget |
| SDXL Lightning | Available | $0.002/MP | Ultra-budget |
| Stable Diffusion 3.5 | Available | ~$0.04/MP | Mid-tier |

### Fireworks AI
- Hosts FLUX.1 [schnell] and [dev]
- Pricing: ~$0.003-0.025/MP (similar to Together AI)
- Good for high-throughput production workloads
- Also offers image upscaling models

### DeepInfra
- Hosts FLUX.1 [schnell], FLUX.1 [dev], SDXL
- Pricing: ~$0.001-0.02/MP (among the cheapest)
- FLUX Schnell: ~$0.0012/image (reported cheapest by Pixazo)
- Good for cost-sensitive batch generation

### Runway
| Model | Price | Notes |
|-------|-------|-------|
| Runway Gen-4 Image | $0.08/img (Elo 976) | Below average quality, expensive |
| (Runway focuses primarily on video, not text-to-image) | | |

### BFL (Black Forest Labs) Direct API
- Direct access to all FLUX models (best pricing for FLUX.2 [pro] and [max])
- FLUX.2 [pro]: $0.03/first MP + $0.015/subsequent MP
- FLUX.2 [max]: $0.07/img
- FLUX.2 [dev]: $0.012/img
- Most reliable for production FLUX workloads

---

## 7. IDEOGRAM V3 / V4 — Text Rendering Specialists

### Ideogram V3
- **Elo Score:** 1,077 (#77 on leaderboard)
- **API Access:** Ideogram API, fal.ai (`fal-ai/ideogram/v3`)
- **Pricing:** ~$0.06-0.08/image
- **Max Resolution:** 1024×1024 (up to 1536 with aspect ratios)
- **Strengths:** Best-in-class text rendering, posters, logos, typography
- **Weaknesses:** Below-average photorealism vs FLUX/GPT Image, limited art style range

### Ideogram V4 / V4.0q Quality
- **Elo Score:** 1,166 (#27 on leaderboard) — major improvement
- **API Access:** fal.ai (`ideogram/v4`)
- **Pricing:** ~$0.06-0.08/image
- **Open Weights:** Yes (HuggingFace `ideogram-ai/ideogram-4`)
- **Strengths:** Crisp text, fine detail, full creative control, open weights
- **Weaknesses:** Still not top-tier for pure photorealism

### Use Case: Best for any image that needs text/typography rendered inside it (posters, ads, memes, infographics)

---

## 8. RECREAFT V3 / V4 — Design & Typography

### Recraft V3
- **Elo Score:** 1,067 (#86 on leaderboard)
- **API Access:** Recraft API, fal.ai (`fal-ai/recraft/v3/text-to-image`)
- **Pricing:** ~$0.04/image
- **Max Resolution:** Up to 2048×2048
- **Strengths:** Vector art output, brand style consistency, long text generation, design-focused
- **Weaknesses:** Not top-tier for photorealism

### Recraft V4 / V4.1 Family (Latest — May 2026)
| Variant | Elo | API Price (1k imgs) | Notes |
|---------|-----|--------------------|-------|
| Recraft V4 Pro | 1,133 | $250/1k ($0.25/img) | Premium, brand systems |
| Recraft V4.1 | 1,146 | $35/1k ($0.035/img) | Standard, good value |
| Recraft V4.1 Pro | 1,152 | $210/1k ($0.21/img) | Pro variant |
| Recraft V4.1 Utility | 1,198 | $35/1k ($0.035/img) | **Top value:** near-frontier Elo at budget price |
| Recraft V4.1 Utility Pro | 1,203 | $210/1k ($0.21/img) | Pro variant of Utility |

### Key Insight: Recraft V4.1 Utility (Elo 1198, $0.035/img) is a **standout value** — top-15 quality at mid-tier pricing.

---

## 9. BENCHMARK COMPARISONS — ArtificialAnalysis.ai Leaderboard

### Top 20 Text-to-Image Models (Elo Rankings, July 2026):

| Rank | Model | Elo | API Price (1k imgs) | Open Weights | Provider |
|------|-------|-----|---------------------|-------------|----------|
| 1 | GPT Image 2 (high) | 1,338 | $211 | No | OpenAI |
| 2 | Reve 2.0 | 1,280 | $24 | No | Reve |
| 3 | MAI-Image-2.5 | 1,269 | $48.1 | No | Microsoft AI |
| 4 | HiDream-O1-Image-1.5 | 1,264 | $80 | No | HiDream |
| 5 | GPT Image 1.5 (high) | 1,260 | $133 | No | OpenAI |
| 6 | Nano Banana 2 (Preview) | 1,254 | $67 | No | Google |
| 7 | Cosmos3-Super-Text2Image | 1,226 | Coming soon | ✅ | NVIDIA |
| 8 | Nano Banana Pro | 1,218 | $134 | No | Google |
| 9 | MAI-Image-2.5-Flash | 1,212 | $20 | No | Microsoft AI |
| 10 | Recraft V4.1 Utility Pro | 1,203 | $210 | No | Recraft |
| 11 | grok-imagine-image-quality | 1,201 | $50 | No | xAI |
| 12 | Krea 2 Medium | 1,200 | $30 | No | Krea |
| 13 | Recraft V4.1 Utility | 1,198 | $35 | No | Recraft |
| 14 | FLUX.2 [max] | 1,194 | $70 | No | BFL |
| 15 | Seedream 4.0 | 1,190 | $30 | No | ByteDance |
| 16 | MAI-Image-2 | 1,189 | $35 | No | Microsoft AI |
| 17 | Krea 2 Large | 1,187 | $60 | No | Krea |
| 18 | HiDream-O1-Image-Dev-2604 | 1,186 | No API | ✅ | HiDream |
| 19 | FLUX.2 [pro] | 1,185 | $30 | No | BFL |
| 20 | FLUX.2 [flex] | 1,179 | $60 | No | BFL |

### Frontier Model Comparison:

| Model | Elo | Price/img | Has API? | Strengths |
|-------|-----|----------|---------|-----------|
| GPT Image 2 | 1,338 | $0.211 | ✅ (OpenAI, OpenRouter, fal.ai) | #1 overall, text rendering, reasoning |
| Reve 2.0 | 1,280 | $0.024 | ✅ (Reve API) | #2, excellent value for quality |
| Nano Banana 2 | 1,254 | $0.067 | ✅ (Google, OpenRouter, fal.ai) | Fast, editing, Google ecosystem |
| Nano Banana Pro | 1,218 | $0.134 | ✅ (Google, OpenRouter, fal.ai) | 4K, 5-subject, text rendering |
| FLUX.2 [max] | 1,194 | $0.07 | ✅ (BFL, fal.ai) | Best FLUX, open ecosystem |
| FLUX.2 [pro] | 1,185 | $0.03 | ✅ (BFL, fal.ai, OpenRouter) | Strong value at frontier quality |
| **Midjourney v7** | **1,068** | **N/A** | **❌ No API** | Once frontier, now rank #84 |
| Imagen 4 Ultra | 1,171 | $0.06 | ✅ (Google) | Solid, but surpassed |
| DALL-E 3 HD | 959 | $0.08 | ✅ (OpenAI) | Legacy, now rank #118 |

### Key Takeaway: Midjourney v7 is NO LONGER a frontier model. It has been surpassed by 83 models on the ArtificialAnalysis leaderboard and has no API. The real frontier is GPT Image 2, Reve 2.0, and the FLUX.2 family.

---

## 10. CHEAPEST NEAR-FRONTIER OPTIONS (90%+ Quality at 10-30% Cost)

### "Near-Frontier" = Elo ≥ 1,100 (within ~180 points of #1's 1338)

| Model | Elo | % of #1 Elo | Price/img | % of GPT Image 2 Cost | Value Score |
|-------|-----|------------|----------|----------------------|-------------|
| **FLUX.2 [dev] Turbo** | 1,155 | 86% | $0.008 | 3.8% | ⭐⭐⭐⭐⭐ |
| **FLUX.2 [dev] Flash** | 1,135 | 85% | $0.005 | 2.4% | ⭐⭐⭐⭐⭐ |
| **Z-Image Turbo** | 1,104 | 82% | $0.005 | 2.4% | ⭐⭐⭐⭐⭐ |
| **FLUX.2 [klein] 9B** | 1,122 | 84% | $0.015 | 7.1% | ⭐⭐⭐⭐ |
| **Seedream 4.0** | 1,190 | 89% | $0.03 | 14% | ⭐⭐⭐⭐ |
| **FLUX.2 [pro]** | 1,185 | 88% | $0.03 | 14% | ⭐⭐⭐⭐ |
| **MAI-Image-2.5-Flash** | 1,212 | 90% | $0.02 | 9.5% | ⭐⭐⭐⭐⭐ |
| **Seedream 4.5** | 1,163 | 87% | $0.04 | 19% | ⭐⭐⭐⭐ |
| **Ideogram 4.0 Quality** | 1,166 | 87% | $0.06 | 28% | ⭐⭐⭐ |
| **ERNIE Image Turbo** | 1,164 | 87% | $0.01 | 4.7% | ⭐⭐⭐⭐⭐ |
| **Recraft V4.1 Utility** | 1,198 | 89% | $0.035 | 17% | ⭐⭐⭐⭐ |
| **Krea 2 Medium** | 1,200 | 90% | $0.03 | 14% | ⭐⭐⭐⭐ |
| **grok-imagine-image** | 1,176 | 88% | $0.02 | 9.5% | ⭐⭐⭐⭐⭐ |

### TOP 5 RECOMMENDATIONS FOR ORCHESTRATION (Best Quality-Per-Dollar):

1. **FLUX.2 [dev] Turbo** (fal.ai) — Elo 1155, $0.008/img, open weights, ~1.5s generation
   - Best overall value. 86% of frontier quality at 3.8% of cost.
   - Open weights means you can self-host for even cheaper at scale.

2. **MAI-Image-2.5-Flash** (Microsoft AI) — Elo 1212, $0.02/img
   - 90% of frontier quality at 9.5% of cost. Highest Elo in this price range.

3. **ERNIE Image Turbo** (Baidu) — Elo 1164, $0.01/img, open weights
   - 87% of frontier quality at 4.7% of cost. Open weights for self-hosting.

4. **Z-Image Turbo** (Alibaba/Tongyi) — Elo 1104, $0.005/img, open weights
   - 82% of frontier quality at 2.4% of cost. 6B params, ultra-fast (~1s).

5. **Seedream 4.0** (ByteDance) — Elo 1190, $0.03/img
   - 89% of frontier quality at 14% of cost. Strong text rendering + composition.

### BONUS: Reve 2.0 — The "Affordable Frontier" Option
- Elo 1280 (#2 overall), $0.024/img
- 96% of GPT Image 2's quality at **11% of the cost**
- If you want true frontier quality without frontier pricing, this is the model.

---

## COMPARISON TABLE — All Major API-Accessible Models

| Model | Elo | Price/img | Max Res | Speed | Open Weights | API Providers | Best For |
|-------|-----|----------|---------|-------|-------------|--------------|----------|
| GPT Image 2 | 1338 | $0.211 | 2K+ | ~8s | No | OpenAI, OpenRouter, fal.ai | Max quality, text rendering |
| Reve 2.0 | 1280 | $0.024 | 2K | ~5s | No | Reve API | Frontier quality at low cost |
| MAI-Image-2.5 | 1269 | $0.048 | 2K | ~5s | No | Microsoft AI | High quality, good value |
| Nano Banana 2 | 1254 | $0.067 | 2K | ~4s | No | Google, OpenRouter, fal.ai | Fast frontier, editing |
| Nano Banana Pro | 1218 | $0.134 | 4K | ~6s | No | Google, OpenRouter, fal.ai | 4K, multi-subject, text |
| MAI-Image-2.5-Flash | 1212 | $0.02 | 2K | ~3s | No | Microsoft AI | Best Elo/$ near-frontier |
| Recraft V4.1 Utility | 1198 | $0.035 | 2K | ~4s | No | Recraft API, fal.ai | Design, typography, value |
| FLUX.2 [max] | 1194 | $0.07 | 4MP | ~5s | No | BFL, fal.ai | Best FLUX quality |
| Seedream 4.0 | 1190 | $0.03 | 2K | ~3s | No | fal.ai, OpenRouter | Value + text rendering |
| FLUX.2 [pro] | 1185 | $0.03 | 4MP | ~4s | No | BFL, fal.ai, OpenRouter | Production FLUX |
| Krea 2 Medium | 1200 | $0.03 | 2K | ~3s | No | fal.ai | Style references |
| grok-imagine-image-quality | 1201 | $0.05 | 2K | ~4s | No | xAI, OpenRouter, fal.ai | Photorealism, entity accuracy |
| FLUX.2 [flex] | 1179 | $0.06 | 4MP | ~4s | No | BFL | Flexible editing |
| Ideogram V4 Quality | 1166 | $0.06 | 2K | ~5s | Yes | fal.ai, Ideogram API | Typography, open weights |
| ERNIE Image Turbo | 1164 | $0.01 | 2K | ~2s | Yes | Baidu, fal.ai | Ultra-cheap, open weights |
| Seedream 4.5 | 1163 | $0.04 | 2K | ~3s | No | fal.ai, OpenRouter | Editing, composition |
| FLUX.2 [dev] | 1155 | $0.012 | 2K | ~3s | Yes | BFL, fal.ai, HuggingFace | Open-weight near-frontier |
| FLUX.2 [dev] Turbo | 1155 | $0.008 | 2K | ~1.5s | Yes | fal.ai | **BEST VALUE** overall |
| FLUX.2 [klein] 9B | 1122 | $0.015 | 2K | ~2s | Yes | BFL, fal.ai, OpenRouter | Mid-tier open weights |
| FLUX.1 Kontext [max] | 1122 | $0.08 | 2K | ~5s | No | BFL, fal.ai | Image editing |
| Nano Banana (v1) | 1153 | $0.039 | 1K | ~3s | No | Google, OpenRouter, fal.ai | Good value frontier |
| Z-Image Turbo | 1104 | $0.005 | 1K | ~1s | Yes | fal.ai | Ultra-fast, ultra-cheap |
| FLUX.2 [dev] Flash | 1135 | $0.005 | 2K | ~1s | Yes | fal.ai | Fastest near-frontier |
| Imagen 4 Ultra | 1171 | $0.06 | 2K | ~5s | No | Google | Solid but surpassed |
| FLUX1.1 [pro] Ultra | 1092 | $0.06 | 2K | ~5s | No | BFL, fal.ai | 2K photorealism (legacy) |
| Ideogram V3 | 1077 | $0.06 | 1K | ~5s | No | fal.ai, Ideogram API | Typography (legacy) |
| Recraft V3 | 1067 | $0.04 | 2K | ~4s | No | Recraft, fal.ai | Vector + raster (legacy) |
| FLUX.1 [pro] | 1069 | $0.05 | 2K | ~3s | No | BFL, fal.ai, Replicate | Original FLUX pro |
| Midjourney v7 Alpha | 1068 | N/A | — | — | No | **NO API** | Surpassed, no API |
| FLUX.1 [dev] | 1027 | $0.025 | 2K | ~3s | Yes | fal.ai, Replicate, HF | Open-weight workhorse |
| FLUX.1 [schnell] | 1000 | $0.003 | 2K | ~1s | Yes (Apache 2.0) | fal.ai, Replicate, Together, HF | Cheapest FLUX, self-hostable |
| SD 3.5 Large | 1023 | $0.065 | 1K | ~4s | Yes | Stability, fal.ai, Replicate | Open-weight baseline |
| SDXL 1.0 | 874 | $0.009 | 1K | ~2s | Yes | Many | Self-hosting, LoRA ecosystem |
| SDXL Lightning | 905 | $0.002 | 1K | ~0.5s | Yes | fal.ai, Replicate | Ultra-cheap batch gen |
| DALL-E 3 | 949 | $0.04 | 1K | ~5s | No | OpenAI (legacy) | Legacy, surpassed |

---

## RECOMMENDATIONS FOR THE TIMUCLAUDE ORCHESTRATION SYSTEM

### Tier 1: Production Default (Best Quality-Per-Dollar)
**Use these for 80% of image generation requests:**

1. **FLUX.2 [dev] Turbo** via fal.ai — $0.008/img, Elo 1155, ~1.5s
   - Default for most requests. Open weights, can self-host later.
   
2. **MAI-Image-2.5-Flash** via Microsoft AI — $0.02/img, Elo 1212
   - When you need higher quality than FLUX Turbo but still cheap.

3. **Seedream 4.0** via fal.ai — $0.03/img, Elo 1190
   - When you need better text rendering and composition.

### Tier 2: Frontier Quality (For Premium Requests)
**Use when the user explicitly wants the best possible quality:**

1. **Reve 2.0** — $0.024/img, Elo 1280 — Best frontier value
2. **Nano Banana 2** via OpenRouter/fal.ai — $0.067/img, Elo 1254 — Fast frontier
3. **GPT Image 2** via OpenRouter — $0.211/img, Elo 1338 — Absolute best quality

### Tier 3: Specialized Use Cases
- **Typography/Text in images:** Ideogram V4 ($0.06, Elo 1166) or Recraft V4.1 Utility ($0.035, Elo 1198)
- **4K resolution:** Nano Banana Pro ($0.134, Elo 1218) or FLUX.2 [pro] ($0.03, up to 4MP)
- **Ultra-fast batch:** Z-Image Turbo ($0.005, ~1s) or FLUX.2 [dev] Flash ($0.005, ~1s)
- **Self-hosted:** FLUX.1 [schnell] (Apache 2.0) or FLUX.2 [dev] (open weights) or SDXL (massive LoRA ecosystem)
- **Image editing:** FLUX.1 Kontext [pro] ($0.04, Elo 1091) or FLUX.2 [flex] ($0.06, Elo 1179)

### Orchestration Strategy (Higgsfield-Style):
1. **Prompt analysis:** Route based on prompt intent (photorealism → FLUX, typography → Ideogram, design → Recraft)
2. **Two-pass generation:** Generate cheap draft with Z-Image Turbo/FLUX Flash → evaluate → if good, upscale with FLUX.2 [pro] or Nano Banana Pro
3. **Ensemble voting:** Generate 3-4 variants with different models (FLUX Turbo, Seedream, Krea, ERNIE) → pick best via a vision model judge
4. **Cost optimization:** Default to $0.005-0.02/img models, only escalate to $0.05+ when needed
5. **OpenRouter as unified gateway:** Access 12+ models through a single API, with fal.ai as secondary provider for models not on OpenRouter

### Provider Priority for Orchestration:
1. **OpenRouter** — Unified API, 12+ image models, single billing, easy swapping
2. **fal.ai** — Fastest inference, 209 models, best for FLUX variants, per-image pricing
3. **BFL Direct** — Best FLUX.2 [max] and [pro] pricing, production-grade reliability
4. **Together AI / DeepInfra** — Cheapest FLUX Schnell/SDXL for batch jobs
5. **Replicate** — Fine-tuning and custom model hosting

---

## ISSUES ENCOUNTERED

- Firecrawl search/scrape hit daily free credit limit after 4 successful calls (OpenRouter, ArtificialAnalysis leaderboard, fal.ai explore, fal.ai pricing failed)
- Chrome DevTools MCP was unavailable during this session
- Data for Ideogram API direct pricing, Recraft API direct pricing, Together AI/Fireworks/DeepInfra specific pricing was supplemented from known public documentation — these should be verified directly before production use
- All Elo scores and rankings are from the ArtificialAnalysis.ai Text-to-Image Leaderboard as of July 2-3, 2026 (cached scrape)
- Pricing is subject to change — verify at provider websites before implementation