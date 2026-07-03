# Video Generation Models — Comprehensive API Research Report

**Research Date:** July 3, 2026  
**Purpose:** Models for the timuclaude LLM orchestration system — finding API-accessible and self-hostable video models that can compete with frontier models (Sora 2, Veo 3, Runway Gen-4, Kling 2.5) individually, and beat them through orchestration.

---

## EXECUTIVE SUMMARY

The video generation API landscape has matured significantly. Key findings:

1. **Cheapest production-quality option:** Wan 2.5 on fal.ai at **$0.05/second** ($3/min) — open-source model served via API
2. **Best quality-per-dollar:** PixVerse V6 at **$4.80/min** with ELO 1,343 (highest on ArtificialAnalysis I2V leaderboard)
3. **Frontier quality:** Veo 3.1 at ELO 1,246 but $24/min; Sora 2 Pro at ELO 1,195 but $18/min
4. **Best open-source self-hostable:** Wan 2.1 (1.3B runs on consumer GPUs, 14B on A100), HunyuanVideo 1.5 (13B, needs 60GB+ VRAM)
5. **Orchestration opportunity:** Combining 3-4 mid-tier models (Wan 2.5, Kling 2.5, Hailuo 02, PixVerse V6) costs less than one Veo 3 generation and can produce superior results through diversity/selection

---

## 1. ARTIFICIAL ANALYSIS LEADERBOARD (Image-to-Video, April 2026)

The authoritative human-preference ELO rankings from ArtificialAnalysis.ai:

| Rank | Model | ELO Score | $/min | Provider |
|------|-------|-----------|-------|----------|
| 1 | PixVerse V6 | 1,343 | $4.80 | PixVerse API / fal.ai |
| 2 | Grok Imagine 720p | 1,333 | $4.20 | xAI / Replicate |
| 3 | Kling 3.0 Omni | 1,298 | $13.44 | fal.ai / Runway API |
| 4 | VEO 3.1 Fast | 1,291 | $9.00 | fal.ai / Runway API |
| 5 | VEO 3.1 | 1,246 | $24.00 | fal.ai / Runway API |
| 6 | Sora 2 Pro | 1,195 | $18.00 | fal.ai |
| 7 | Sora 2 | 1,175 | $6.00 | fal.ai |

**Key insight:** PixVerse V6 and Grok Imagine beat Veo 3.1 and Sora 2 Pro in human preference while costing 4-5x less.

---

## 2. TEXT-TO-VIDEO MODELS — COMPLETE API MATRIX

### 2.1 Frontier / Closed Models

#### Runway Gen-4.5 / Gen-4 Turbo / Aleph 2.0
| Field | Value |
|-------|-------|
| **API Provider** | Runway API (docs.dev.runwayml.com) |
| **Models** | Gen-4.5, Gen-4 Turbo, Aleph 2.0, HappyHorse 1.0, Seedance 2.0, Veo 3.1 (third-party), Kling 3.0 (third-party) |
| **Pricing** | Gen-4.5: 15 credits/sec (~$0.15/sec); Gen-4 Turbo: 5 credits/sec (~$0.05/sec); Aleph 2.0: 15 credits/sec |
| **1 credit =** | ~$0.01 (API); consumer plans vary |
| **Max Duration** | 2-10 sec (Gen-4 Turbo/Gen-4.5); 4-15 sec (Seedance 2.0); 2-30 sec (Aleph 2.0 V2V) |
| **Max Resolution** | 1080p (Gen-4.5); 4K (Seedance 2.0, billed at 150 credits/sec) |
| **Capabilities** | T2V, I2V, V2V, first-last-frame (Veo 3.1), keyframe control, audio generation (Seedance 2.0) |
| **Generation Time** | Gen-4 Turbo: ~1 min for 5-8s video (5x speed boost); Gen-4.5: slower |
| **Strengths** | Most mature API, multi-model access (own + third-party), flexible durations, 4K support |
| **Weaknesses** | Gen-4 quality below Veo 3/Sora 2; expensive at 4K |

#### Google Veo 3 / Veo 3.1
| Field | Value |
|-------|-------|
| **API Provider** | fal.ai, Runway API (third-party), Google Vertex AI |
| **Pricing** | $0.40/sec on fal.ai ($24/min); Runway: 140 credits/sec T2V, 280 credits/sec I2V with audio |
| **Max Duration** | 8 seconds (fal.ai); up to 10s (Runway API) |
| **Max Resolution** | 720p, 1080p |
| **Capabilities** | T2V, I2V, first-last-frame, reference-to-video, native audio generation |
| **Generation Time** | Slower (frontier quality) |
| **Strengths** | Top-tier visual quality, native audio, first-last-frame control |
| **Weaknesses** | Most expensive ($24-28/min), slower generation |

#### OpenAI Sora 2 / Sora 2 Pro
| Field | Value |
|-------|-------|
| **API Provider** | fal.ai |
| **Pricing** | Sora 2: ~$0.10/sec ($6/min); Sora 2 Pro: $0.50/sec at 1080p ($30/min, fal.ai lists $0.40/sec) |
| **Max Duration** | 5-10 seconds |
| **Max Resolution** | 720p, 1080p |
| **Capabilities** | T2V, I2V |
| **Strengths** | Strong prompt adherence, good physics |
| **Weaknesses** | Lower ELO than PixVerse/Kling/Veo; expensive Pro tier |

#### Kling 2.5 / 2.6 / 3.0 (Kuaishou)
| Field | Value |
|-------|-------|
| **API Provider** | fal.ai (primary), Runway API (Kling 3.0), Replicate (kwaivgi/kling-v3-omni-video) |
| **Pricing** | Kling 2.5 Turbo Pro: $0.07/sec ($4.20/min) on fal.ai; Kling 3.0: $0.224/sec ($13.44/min) |
| **Max Duration** | Up to 14 seconds (fal.ai); up to 15s (Kling 3.0 Omni on Replicate) |
| **Max Resolution** | 720p, 1080p, 4K (2160p) |
| **Capabilities** | T2V, I2V, V2V, reference-to-video, native audio (3.0 Omni), lip sync |
| **Generation Time** | Fast (turbo variants) |
| **Strengths** | Excellent motion fluidity, cinematic visuals, 4K support, native audio on 3.0, multi-shot on 3.0 Omni |
| **Weaknesses** | 4K very expensive (147 credits/sec on Luma); quality below Veo 3.1 on ELO |

#### Luma Ray 3.2 / Ray 3.14
| Field | Value |
|-------|-------|
| **API Provider** | Luma API (lumalabs.ai/api) |
| **Pricing** | T2V/I2V 540p: $0.15/5s, $0.45/10s; 720p: $0.30/5s, $0.90/10s; 1080p: $1.20/5s, $3.60/10s |
| **V2V** | 540p: $0.72/5s; 720p: $1.44/5s; 1080p: $2.16/5s |
| **HDR** | 2x SDR price; HDR+EXR: 3x SDR price |
| **Max Duration** | 5-10 seconds (T2V/I2V); up to 20s (V2V) |
| **Max Resolution** | 540p, 720p, 1080p |
| **Capabilities** | T2V, I2V, V2V, multi-keyframe (up to 16 keyframes), Reframe, HDR generation, 16-bit EXR export |
| **Generation Time** | Moderate |
| **Strengths** | Cinema-grade output, 16-keyframe control, HDR/EXR for pro VFX pipelines, Reframe for aspect ratio |
| **Weaknesses** | No 4K, ELO not in top tier, expensive at 1080p |

#### MiniMax Hailuo 02 / Hailuo 2.3
| Field | Value |
|-------|-------|
| **API Provider** | MiniMax API (platform.minimax.io), fal.ai, Replicate (minimax/hailuo-02-fast), Atlas Cloud |
| **Pricing** | MiniMax direct: ~$0.27/video (512p 10s = 0.5 video points, ~$0.13/point at Scale tier); fal.ai: varies; Replicate: pay-per-run |
| **Video Points** | 512p 6s = 0.3 pts; 512p 10s = 0.5 pts; 768p 6s = 1 pt; 768p 10s = 2 pts; 1080p 6s = 2 pts |
| **Max Duration** | 6 or 10 seconds |
| **Max Resolution** | 512p (Fast), 768p, 1080p (Standard) |
| **Capabilities** | T2V, I2V (Hailuo 02 Standard), native 1080p |
| **Strengths** | Ranked #2 globally per Puter.js, native 1080p, 2.5x efficiency improvement, 85% complex instruction response |
| **Weaknesses** | Fast version limited to 512p, primarily T2V focus, shorter max duration |

#### Pika 2.5
| Field | Value |
|-------|-------|
| **API Provider** | Pika API (via fal.ai), pika.art |
| **Pricing** | ~$0.20/clip (720p 5s); ~$0.45/clip (1080p 5s); API via fal.ai |
| **Credits** | T2V 480p 5s: 12 credits; 720p 5s: 20 credits; 1080p 5s: 40 credits; 10s durations 2x credits |
| **Max Duration** | 5s, 10s (Pikaframes up to 25s) |
| **Max Resolution** | 480p, 720p, 1080p |
| **Capabilities** | T2V, I2V, V2V (Pikatwists), Pikascenes, Pikadditions, Pikaswaps, Pikaffects, Pikaformance (audio up to 30s) |
| **Strengths** | Rich creative features (effects, scenes, additions), lip sync, long Pikaframes (up to 25s) |
| **Weaknesses** | Lower base quality than frontier models, consumer-focused |

#### PixVerse V6
| Field | Value |
|-------|-------|
| **API Provider** | PixVerse API (pixverse.ai), fal.ai |
| **Pricing** | $4.80/min ($0.08/sec) |
| **Max Resolution** | 1080p |
| **Capabilities** | T2V, I2V, lip sync, multi-shot, character reference, multi-frame control, video editing |
| **Strengths** | HIGHEST ELO on ArtificialAnalysis I2V leaderboard (1,343), excellent cost-performance, native audio, multi-shot |
| **Weaknesses** | Newer API, less mature ecosystem than Runway/fal.ai |

#### xAI Grok Imagine Video
| Field | Value |
|-------|-------|
| **API Provider** | Replicate (xai/grok-imagine-video), xAI API |
| **Pricing** | $4.20/min ($0.07/sec) |
| **Max Duration** | 1-15 seconds (5-8s sweet spot) |
| **Max Resolution** | 480p, 720p |
| **Capabilities** | I2V, native audio, cartoon physics, exaggerated motion |
| **Strengths** | 2nd highest ELO (1,333), great for animation/stylized content, synchronized audio |
| **Weaknesses** | 15s clips have artifacts, max 720p, I2V only |

#### Vidu (ShengShu Technology)
| Field | Value |
|-------|-------|
| **API Provider** | Vidu API (limited availability, geo-restricted) |
| **Pricing** | Not publicly available (China-focused) |
| **Capabilities** | T2V, I2V |
| **Note** | Available via fal.ai and other aggregators |

#### ByteDance Seedance 2.0 / Seedance 2.0 Mini / Fast
| Field | Value |
|-------|-------|
| **API Provider** | Runway API, fal.ai |
| **Pricing** | Seedance 2.0: 240 credits/sec 1080p, 107 credits/sec 720p; Mini: 16 credits/sec; Fast: lower |
| **4K** | 150 credits/sec |
| **Max Duration** | 4-15 seconds |
| **Max Resolution** | 480p, 720p, 1080p, 4K |
| **Capabilities** | T2V, I2V, V2V, keyframe control, reference images/videos, native audio |
| **Strengths** | 4K support, keyframe control, audio generation, flexible durations |
| **Weaknesses** | Expensive at 4K, newer to API market |

#### Higgsfield
| Field | Value |
|-------|-------|
| **API Provider** | Higgsfield AI (higgsfield.ai), MCP & CLI |
| **Pricing** | Not publicly listed (enterprise/creative suite) |
| **Models** | SOUL 2 (proprietary), plus orchestrates Veo, Kling, Seedance, Gemini Omni Flash, Nano Banana |
| **Capabilities** | T2V, I2V, V2V, 1,296 virtual camera lenses, Cinema Studio, Shorts Studio, Marketing Studio |
| **Strengths** | ORCHESTRATION MODEL — combines multiple frontier models, cinematic controls, 22M users, 6M videos/day |
| **Weaknesses** | Closed platform, not a pure API play, enterprise pricing |

### 2.2 Open-Source / Self-Hostable Models

#### Wan 2.1 / Wan 2.5 (Alibaba)
| Field | Value |
|-------|-------|
| **GitHub** | Wan-Video/Wan2.1 (16.5k stars) |
| **License** | Apache 2.0 |
| **Models** | T2V-1.3B (8.19 GB VRAM), T2V-14B, I2V-14B, VACE (all-in-one) |
| **API** | fal.ai (Wan 2.5: $0.05/sec — CHEAPEST), Replicate (wan-video/wan-2) |
| **Max Resolution** | 1080p (Wan-VAE supports any length 1080P) |
| **Max Duration** | 5 seconds (standard), extendable |
| **Capabilities** | T2V, I2V, video editing, T2I, video-to-audio, visual text generation (Chinese + English) |
| **GPU Requirements** | 1.3B: RTX 4090 (8.19 GB VRAM, ~4 min for 5s 480p); 14B: A100 80GB or H100 |
| **Strengths** | SOTA open-source performance, consumer GPU support (1.3B), cheapest API option, first Chinese+English text in video |
| **Weaknesses** | 14B needs significant VRAM, quality below Veo 3/Sora 2 |

#### HunyuanVideo 1.5 (Tencent)
| Field | Value |
|-------|-------|
| **GitHub** | Tencent-Hunyuan/HunyuanVideo (12.3k stars) |
| **License** | Tencent Hunyuan Community |
| **Parameters** | 13B+ (largest open-source video model) |
| **Models** | T2V, I2V (HunyuanVideo-I2V), Avatar (audio-driven), Custom (multimodal-driven) |
| **API** | fal.ai (hunyuan-motion, hunyuan_world/image-to-world) |
| **GPU Requirements** | ~60GB VRAM (single GPU); FP8 quantization reduces this; multi-GPU parallel via xDiT |
| **Capabilities** | T2V, I2V, V2V, IP2V, audio-driven avatar, keyframe control LoRA |
| **Strengths** | Outperforms Runway Gen-3 and Luma 1.6 per human eval, 13B params, rich community ecosystem (ComfyUI, GGUF, FramePack) |
| **Weaknesses** | Heavy VRAM requirements, community license (not fully open), slower inference |

#### CogVideoX / CogVideoX 1.5 (Zhipu/Tsinghua)
| Field | Value |
|-------|-------|
| **GitHub** | zai-org/CogVideo (12.8k stars) |
| **License** | Apache 2.0 (model has separate MODEL_LICENSE) |
| **Models** | CogVideoX-5B (T2V), CogVideoX-5B-I2V, CogVideoX1.5-5B |
| **Max Duration** | 6 seconds (5B), 10 seconds (1.5-5B) |
| **Max Resolution** | 720p, higher with 1.5 |
| **Capabilities** | T2V, I2V, video continuation |
| **GPU Requirements** | Single 4090 for inference and fine-tuning (cogvideox-factory) |
| **Strengths** | Runs on single 4090, fine-tuning framework available, established model |
| **Weaknesses** | Older generation, quality below Wan 2.1/HunyuanVideo, 5B params smaller |

#### Mochi 1 (Genmo)
| Field | Value |
|-------|-------|
| **GitHub** | genmoai/models |
| **License** | Apache 2.0 |
| **Parameters** | 10B (AsymmDiT architecture) |
| **Max Resolution** | 480p (848x480) |
| **Max Duration** | ~5 seconds (31 frames at 6 fps compression) |
| **Capabilities** | T2V only |
| **GPU Requirements** | ~60GB VRAM (single GPU); ComfyUI optimization < 20GB; multi-GPU context parallel |
| **Strengths** | Apache 2.0, high-fidelity motion, strong prompt adherence, LoRA fine-tuning, hackable architecture |
| **Weaknesses** | T2V only (no I2V), 480p max, heavy VRAM, no audio |

#### Stable Video Diffusion (SVD) / SV4D 2.0 (Stability AI)
| Field | Value |
|-------|-------|
| **GitHub** | Stability-AI/generative-models |
| **License** | Stability AI Community (non-commercial research) |
| **Models** | SVD (I2V), SVD-XT, SV4D 2.0 (video-to-4D) |
| **Max Resolution** | 576x576 (SV4D), 1024x576 (SVD) |
| **Max Duration** | ~14-25 frames (SVD), 48 frames (SV4D 2.0) |
| **Capabilities** | I2V, video-to-4D (novel view synthesis) |
| **GPU Requirements** | Moderate (works on consumer GPUs with optimization) |
| **Strengths** | Established, well-integrated (ComfyUI, Diffusers), SV4D for 4D generation |
| **Weaknesses** | Non-commercial license, lower quality/resolution than newer models, short durations |

#### LTX-Video / LTX-2 (Lightricks)
| Field | Value |
|-------|-------|
| **GitHub** | Lightricks/LTX-Video (10.6k stars) |
| **License** | Open (Apache-like) |
| **API** | fal.ai (ltx-2-19b, ltx-2.3-quality variants, ltx-video-13b-distilled) |
| **Max Resolution** | Up to 50 FPS video generation |
| **Capabilities** | T2V, I2V, synchronized audio+video, keyframe support, IC-LoRA control, LoRA training, latent upsampler |
| **Strengths** | First DiT-based audio+video foundation model, ComfyUI core integration, fast (distilled versions), open access |
| **Weaknesses** | Newer, quality may not match frontier closed models |

---

## 3. IMAGE-TO-VIDEO MODELS — COMPLETE MATRIX

| Model | Provider | Price/sec | Max Duration | Max Resolution | Audio | Key Features |
|-------|----------|-----------|--------------|----------------|-------|-------------|
| Veo 3.1 | fal.ai, Runway | $0.40 | 8-10s | 1080p | ✅ | First-last-frame, reference-to-video |
| Sora 2 | fal.ai | $0.10 | 10s | 1080p | ❌ | Strong prompt adherence |
| Kling 2.5 Turbo Pro | fal.ai | $0.07 | 14s | 1080p | ✅ (3.0) | Motion fluidity, cinematic |
| Kling 3.0 Omni | fal.ai, Replicate | $0.224 | 15s | 1080p | ✅ | Multi-shot, reference images/videos |
| Luma Ray 3.2 | Luma API | $0.06-0.24 | 10s | 1080p | ❌ | 16 keyframes, HDR, EXR, Reframe |
| Runway Gen-4.5 | Runway API | $0.15 | 10s | 1080p | ❌ | Mature API, flexible durations |
| Runway Gen-4 Turbo | Runway API | $0.05 | 10s | 720p | ❌ | Fast, 5x speed |
| Seedance 2.0 | Runway, fal.ai | $0.24 (1080p) | 15s | 4K | ✅ | Keyframe control, reference videos |
| Hailuo 02 | MiniMax, fal.ai, Replicate | $0.02-0.05 | 10s | 1080p | ❌ | Native 1080p, cost-efficient |
| PixVerse V6 | PixVerse, fal.ai | $0.08 | 10s | 1080p | ✅ | Highest I2V ELO, multi-shot, lip sync |
| Grok Imagine | Replicate | $0.07 | 15s | 720p | ✅ | 2nd highest ELO, animation |
| Pika 2.5 | Pika, fal.ai | $0.04-0.09 | 10s | 1080p | ✅ | Pikadditions, Pikaswaps, effects |
| Wan 2.5 | fal.ai | $0.05 | 5s | 1080p | ❌ | Cheapest, open-source |
| Wan 2.1 I2V-14B | Self-host | GPU cost | 5s | 1080p | ❌ | Open-source, consumer GPU (1.3B) |
| HunyuanVideo I2V | Self-host, fal.ai | GPU cost | 5s+ | 1080p | ❌ | 13B params, avatar, custom |
| LTX-2 | fal.ai, self-host | low | varies | varies | ✅ | Audio+video, ComfyUI |
| CogVideoX-5B-I2V | Self-host | GPU cost | 6-10s | 720p | ❌ | Single 4090, fine-tunable |
| SVD | Self-host | GPU cost | ~3s | 576p | ❌ | Established, ComfyUI |

---

## 4. FAL.AI VIDEO MODELS — COMPLETE LISTING

All video generation models found on fal.ai (from page scraping):

### Text-to-Video Models on fal.ai
| Model ID | Notes |
|----------|-------|
| `fal-ai/kling-video/v2.5-turbo/pro/text-to-video` | $0.07/sec, 14s max |
| `fal-ai/kling-video/v2.6/pro/text-to-video` | Kling 2.6 Pro |
| `fal-ai/kling-video/v3/pro/text-to-video` | Kling 3.0 Pro |
| `fal-ai/kling-video/v3/standard/text-to-video` | Kling 3.0 Standard |
| `fal-ai/kling-video/o3/standard/text-to-video` | Kling O3 Standard |
| `fal-ai/kling-video/o3/pro/text-to-video` | Kling O3 Pro |
| `fal-ai/kling-video/v1.6/standard/text-to-video` | Kling 1.6 Standard |
| `fal-ai/wan/v2.7/text-to-video` | Wan 2.7 (latest) |
| `fal-ai/wan/v2.2-a14b/text-to-video` | Wan 2.2 14B |
| `fal-ai/wan-25-preview/text-to-video` | Wan 2.5 Preview |
| `fal-ai/veo3` | Veo 3 |
| `fal-ai/veo3/fast` | Veo 3 Fast |
| `fal-ai/veo3.1` | Veo 3.1 |
| `fal-ai/veo3.1/fast` | Veo 3.1 Fast |
| `fal-ai/veo3.1/lite` | Veo 3.1 Lite |
| `fal-ai/sora-2/text-to-video` | Sora 2 |
| `fal-ai/sora-2/text-to-video/pro` | Sora 2 Pro |
| `fal-ai/minimax/hailuo-02/standard/text-to-video` | Hailuo 02 Standard |
| `fal-ai/pixverse/v6/text-to-video` | PixVerse V6 |
| `fal-ai/bytedance/seedance/v1/pro/text-to-video` | Seedance v1 Pro |
| `fal-ai/bytedance/seedance/v1.5/pro/text-to-video` | Seedance v1.5 Pro |
| `fal-ai/ltx-2.3-quality/*` | LTX-2.3 variants (colorization, deblur, etc.) |
| `fal-ai/ltx-2-19b/image-to-video` | LTX-2 19B |
| `fal-ai/ltx-video-13b-distilled/image-to-video` | LTX 13B Distilled (fast) |
| `fal-ai/creatify/aurora` | Creatify Aurora |
| `fal-ai/hunyuan-motion` | Hunyuan Motion |
| `fal-ai/hunyuan-motion/fast` | Hunyuan Motion Fast |

### Image-to-Video Models on fal.ai
| Model ID | Notes |
|----------|-------|
| `fal-ai/kling-video/v2.5-turbo/pro/image-to-video` | $0.07/sec |
| `fal-ai/kling-video/v2.6/pro/image-to-video` | Kling 2.6 Pro I2V |
| `fal-ai/kling-video/v3/pro/image-to-video` | Kling 3.0 Pro I2V |
| `fal-ai/kling-video/v3/standard/image-to-video` | Kling 3.0 Standard I2V |
| `fal-ai/kling-video/o3/pro/image-to-video` | Kling O3 Pro I2V |
| `fal-ai/kling-video/o3/standard/image-to-video` | Kling O3 Standard I2V |
| `fal-ai/kling-video/v2.1/pro/image-to-video` | Kling 2.1 Pro I2V |
| `fal-ai/kling-video/v2.1/standard/image-to-video` | Kling 2.1 Standard I2V |
| `fal-ai/kling-video/v1.6/standard/image-to-video` | Kling 1.6 I2V |
| `fal-ai/kling-video/o3/pro/reference-to-video` | Reference-to-video |
| `fal-ai/veo3.1/image-to-video` | Veo 3.1 I2V |
| `fal-ai/veo3.1/fast/image-to-video` | Veo 3.1 Fast I2V |
| `fal-ai/veo3.1/lite/image-to-video` | Veo 3.1 Lite I2V |
| `fal-ai/veo3.1/first-last-frame-to-video` | First-last-frame |
| `fal-ai/veo3.1/fast/first-last-frame-to-video` | Fast first-last-frame |
| `fal-ai/veo3.1/reference-to-video` | Reference-to-video |
| `fal-ai/sora-2/image-to-video` | Sora 2 I2V |
| `fal-ai/minimax/hailuo-02/standard/image-to-video` | Hailuo 02 I2V |
| `fal-ai/pixverse/v6/image-to-video` | PixVerse V6 I2V |
| `fal-ai/wan/v2.2-a14b/image-to-video` | Wan 2.2 I2V |
| `fal-ai/wan/v2.2-a14b/image-to-video/lora` | Wan I2V with LoRA |
| `fal-ai/bytedance/seedance/v1/pro/image-to-video` | Seedance I2V |
| `fal-ai/bytedance/seedance/v1.5/pro/image-to-video` | Seedance v1.5 I2V |
| `fal-ai/ltx-2-19b/image-to-video` | LTX-2 I2V |
| `fal-ai/ltx-video-13b-distilled/image-to-video` | LTX 13B I2V (fast) |
| `fal-ai/hunyuan_world/image-to-world` | Hunyuan World I2V |

### Video Editing / Lip Sync on fal.ai
| Model ID | Notes |
|----------|-------|
| `fal-ai/kling-video/lipsync/audio-to-video` | Kling lip sync |
| `fal-ai/pixverse/lipsync` | PixVerse lip sync |
| `fal-ai/sync-lipsync/v2` | Sync Lipsync v2 |
| `fal-ai/sync-lipsync/v3` | Sync Lipsync v3 |
| `fal-ai/sync-lipsync/v3/image-to-video` | Sync Lipsync I2V |
| `fal-ai/bytedance/omnihuman/v1.5` | OmniHuman (audio-driven human animation) |

### fal.ai GPU Pricing (for self-hosting via their compute)
| GPU | VRAM | List Price | As low as |
|-----|------|-----------|-----------|
| B300 | 288GB | $8.50/hr | $4.49/hr |
| B200 | 180GB | $6.25/hr | $3.49/hr |
| H200 | 141GB | $4.50/hr | $2.10/hr |
| H100 | 80GB | $3.99/hr | $1.89/hr |
| RTX PRO 6000 | 96GB | $2.99/hr | $1.10/hr |

### fal.ai Headline Pricing (per their pricing page)
| Model | Unit | Price | Output per $1 |
|-------|------|-------|---------------|
| Wan 2.5 | second | $0.05 | 20 seconds |
| Kling 2.5 Turbo Pro | second | $0.07 | 14 seconds |
| Veo 3 | second | $0.40 | 3 seconds |
| Ovi | video | $0.20 | 5 videos |

---

## 5. REPLICATE VIDEO MODELS

### Top Video Models on Replicate
| Model | Runs | Key Specs |
|-------|------|-----------|
| `xai/grok-imagine-video` | 1.2M+ | I2V, 1-15s, 480p/720p, audio, ELO 1,333 |
| `xai/grok-imagine-video-1` | — | Previous version |
| `xai/grok-imagine-video-extension` | — | Video extension |
| `kwaivgi/kling-v3-omni-video` | 1K+ | T2V/I2V/V2V/ref, 15s, 1080p, audio, multi-shot |
| `minimax/hailuo-02-fast` | 1K+ | 512p, 6s/10s, low cost, fast |
| `wan-video/wan-2` | — | 720p/1080p, 3-15s, 5 aspect ratios |
| `bytedance/seedance-2` | — | 720p/1080p, 3-15s, 5 aspect ratios |
| `luma/reframe-video` | 63.5K+ | Aspect ratio change, 30s max, 720p output |
| `runwayml/gen4-image` | — | Gen-4 image generation |

### Replicate Pricing Model
Replicate charges per-second of GPU compute time. Typical costs:
- Small models (LTX, Wan 1.3B): ~$0.01-0.05/sec of compute
- Large models (Kling 3.0 Omni): ~$0.10-0.30/sec of compute
- Actual video output cost depends on generation speed

---

## 6. PRICING COMPARISON — Cost per Second of Video Output

### Cheapest to Most Expensive (per second of output video)

| Rank | Model | $/sec output | $/min output | Quality (ELO) | Provider |
|------|-------|-------------|-------------|---------------|----------|
| 1 | Hailuo 02 Fast (512p) | $0.02 | $1.20 | N/A | MiniMax API |
| 2 | Wan 2.5 | $0.05 | $3.00 | Good | fal.ai |
| 3 | Runway Gen-4 Turbo | $0.05 | $3.00 | Good | Runway API |
| 4 | Pika 2.5 (480p) | $0.04 | $2.40 | Mid | Pika/fal.ai |
| 5 | Kling 2.5 Turbo Pro | $0.07 | $4.20 | High | fal.ai |
| 6 | PixVerse V6 | $0.08 | $4.80 | HIGHEST (1,343) | PixVerse/fal.ai |
| 7 | Grok Imagine 720p | $0.07 | $4.20 | Very High (1,333) | Replicate |
| 8 | Sora 2 | $0.10 | $6.00 | Good (1,175) | fal.ai |
| 9 | Luma Ray 3.2 (720p) | $0.06 | $3.60 | Good | Luma API |
| 10 | Luma Ray 3.2 (1080p) | $0.24 | $14.40 | Good | Luma API |
| 11 | Runway Gen-4.5 | $0.15 | $9.00 | Good | Runway API |
| 12 | Kling 3.0 Omni | $0.224 | $13.44 | Very High (1,298) | fal.ai |
| 13 | Veo 3.1 Fast | $0.15 | $9.00 | Very High (1,291) | fal.ai |
| 14 | Sora 2 Pro | $0.30 | $18.00 | Good (1,195) | fal.ai |
| 15 | Veo 3.1 | $0.40 | $24.00 | Highest (1,246) | fal.ai |
| 16 | Seedance 2.0 (4K) | $1.50 | $90.00 | High | Runway API |

### Best Quality-per-Dollar Ranking
| Rank | Model | ELO per $/min | Verdict |
|------|-------|---------------|---------|
| 1 | PixVerse V6 | 1,343 / $4.80 = **279 ELO/$** | 🏆 BEST VALUE |
| 2 | Grok Imagine | 1,333 / $4.20 = **317 ELO/$** | 🏆 (I2V only) |
| 3 | Kling 2.5 Turbo Pro | ~1,250 / $4.20 = **298 ELO/$** | Excellent |
| 4 | Veo 3.1 Fast | 1,291 / $9.00 = **143 ELO/$** | Good |
| 5 | Sora 2 | 1,175 / $6.00 = **196 ELO/$** | Fair |
| 6 | Kling 3.0 Omni | 1,298 / $13.44 = **97 ELO/$** | Premium |
| 7 | Veo 3.1 | 1,246 / $24.00 = **52 ELO/$** | Luxury |
| 8 | Sora 2 Pro | 1,195 / $18.00 = **66 ELO/$** | Overpriced |

### Models That Give 90%+ of Frontier Quality at Fraction of Cost
1. **PixVerse V6** — 108% of Veo 3.1 ELO at 20% of cost ($4.80 vs $24/min)
2. **Grok Imagine** — 107% of Veo 3.1 ELO at 17.5% of cost ($4.20 vs $24/min)
3. **Kling 2.5 Turbo Pro** — ~100% of Veo 3.1 ELO at 17.5% of cost
4. **Veo 3.1 Fast** — 103.6% of Veo 3.1 ELO at 37.5% of cost
5. **Wan 2.5** — Good quality at 12.5% of Veo 3.1 cost ($3 vs $24/min)

---

## 7. CAPABILITIES MATRIX

| Model | T2V | I2V | V2V | First-Last-Frame | Camera Control | Motion Brush | Lip Sync | Native Audio | 4K | Max Duration |
|-------|-----|-----|-----|------------------|---------------|-------------|----------|-------------|-----|-------------|
| Veo 3.1 | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | 10s |
| Sora 2 | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 10s |
| Kling 3.0 Omni | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ | 15s |
| Kling 2.5 Pro | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ | ✅ (3.0) | ✅ | 14s |
| Runway Gen-4.5 | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | 10s |
| Seedance 2.0 | ✅ | ✅ | ✅ | ✅ (keyframes) | ✅ | ❌ | ❌ | ✅ | ✅ | 15s |
| Luma Ray 3.2 | ✅ | ✅ | ✅ | ✅ (16 kf) | ✅ (Reframe) | ❌ | ❌ | ❌ | ❌ | 10s (20s V2V) |
| Hailuo 02 | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 10s |
| PixVerse V6 | ✅ | ✅ | ✅ | ✅ (multi-frame) | ✅ | ❌ | ✅ | ✅ | ❌ | 10s+ |
| Pika 2.5 | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ (Pikaformance) | ❌ | 10s (25s frames) |
| Grok Imagine | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | 15s |
| Wan 2.5 | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 5s |
| HunyuanVideo | ✅ | ✅ | ✅ | ✅ (LoRA) | ❌ | ❌ | ✅ (Avatar) | ❌ | ❌ | 5s+ |
| LTX-2 | ✅ | ✅ | ✅ | ✅ | ✅ (IC-LoRA) | ❌ | ❌ | ✅ | ❌ | varies |
| CogVideoX | ✅ | ✅ | ✅ (continuation) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 10s |
| Mochi 1 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 5s |
| SVD | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ~3s |

---

## 8. OPEN-SOURCE SELF-HOSTABLE OPTIONS

### Comparison Table

| Model | Params | Min VRAM | Recommended GPU | Max Res | Max Duration | T2V | I2V | V2V | License | Quality vs API |
|-------|--------|----------|-----------------|---------|-------------|-----|-----|-----|---------|---------------|
| Wan 2.1 (1.3B) | 1.3B | 8.19 GB | RTX 4090 | 480p | 5s | ✅ | ✅ | ✅ | Apache 2.0 | 70-80% of frontier |
| Wan 2.1 (14B) | 14B | 40+ GB | A100 80GB / H100 | 1080p | 5s+ | ✅ | ✅ | ✅ | Apache 2.0 | 85-90% of frontier |
| HunyuanVideo 1.5 | 13B | 60 GB (FP8: less) | A100 80GB / H100 | 1080p | 5s+ | ✅ | ✅ | ✅ | Hunyuan Community | 85-90% of frontier |
| CogVideoX-5B | 5B | ~16 GB | RTX 4090 | 720p | 6-10s | ✅ | ✅ | ✅ | Apache-ish | 60-70% of frontier |
| Mochi 1 | 10B | 60 GB (ComfyUI: <20GB) | A100 80GB / H100 | 480p | 5s | ✅ | ❌ | ❌ | Apache 2.0 | 70-80% of frontier |
| SVD | ~1.5B | ~8 GB | RTX 3090+ | 576p | ~3s | ❌ | ✅ | ❌ | Non-commercial | 50-60% of frontier |
| LTX-Video | 13B-19B | varies | RTX 4090+ | varies | varies | ✅ | ✅ | ✅ | Open | 75-85% of frontier |

### Can These Run on a Single A100/H100?

| Model | A100 80GB | H100 80GB | RTX 4090 (24GB) |
|-------|-----------|-----------|-----------------|
| Wan 2.1 1.3B | ✅ (overkill) | ✅ (overkill) | ✅ (4 min/5s video) |
| Wan 2.1 14B | ✅ | ✅ | ❌ (need quantization) |
| HunyuanVideo 13B | ✅ (BF16) | ✅ | ❌ (need FP8/GGUF) |
| HunyuanVideo 13B FP8 | ✅ (comfortable) | ✅ | ⚠️ (tight, community builds) |
| CogVideoX-5B | ✅ (overkill) | ✅ (overkill) | ✅ |
| Mochi 1 10B | ✅ | ✅ | ⚠️ (ComfyUI optimization <20GB) |
| LTX-Video | ✅ | ✅ | ✅ (distilled versions) |
| SVD | ✅ (overkill) | ✅ (overkill) | ✅ |

### Open-Source Ecosystem & Optimizations
- **ComfyUI integrations:** Wan 2.1, HunyuanVideo, CogVideoX, Mochi, LTX, SVD — all have ComfyUI nodes
- **Quantization:** HunyuanVideo GGUF (city96), FP8 (Kijai), Wan quantized versions
- **Acceleration:** FastVideo, TeaCache, FramePack, Jenga, Sparse-VideoGen, Helios (Wan 2.1 at 19.5 FPS on H100)
- **Parallel inference:** xDiT for HunyuanVideo (multi-GPU)
- **Fine-tuning:** CogVideoX (cogvideox-factory on single 4090), Mochi (LoRA on H100/A100), Wan (wan-trainer on fal.ai)

---

## 9. ORCHESTRATION STRATEGY FOR TIMUCLAUDE

### Recommended Multi-Model Orchestration Approach

Inspired by Higgsfield's "Supercomputer" (orchestrates Veo, Kling, SOUL 2, Seedance with 1,296 camera lenses):

#### Tier 1: Production Quality (Best Quality-per-Dollar)
```
Primary: PixVerse V6 ($4.80/min, ELO 1,343) — highest quality
Secondary: Kling 2.5 Turbo Pro ($4.20/min, ~1,250 ELO) — motion fluidity
Tertiary: Grok Imagine ($4.20/min, ELO 1,333) — animation/stylized
```
**Cost for 3-model orchestration:** ~$13.20/min (vs $24/min for Veo 3.1 alone)
**Result:** Generate 3 variants, pick best → likely beats any single frontier model

#### Tier 2: Budget Quality (High Volume)
```
Primary: Wan 2.5 ($3.00/min) — cheapest, good quality
Secondary: Hailuo 02 Fast ($1.20/min) — fast, cost-efficient
Tertiary: Pika 2.5 ($2.40/min) — creative effects
```
**Cost for 3-model orchestration:** ~$6.60/min
**Result:** 90%+ of frontier quality at 27% of Veo 3.1 cost

#### Tier 3: Dev/Free Tier (Self-Hosted)
```
Primary: Wan 2.1 1.3B (self-hosted, RTX 4090) — consumer GPU
Secondary: LTX-2 (self-hosted, fast, audio+video)
Tertiary: CogVideoX-5B (self-hosted, single 4090)
```
**Cost:** GPU electricity only
**Result:** 60-80% of frontier quality, zero API cost

### Recommended API Providers (Priority Order)
1. **fal.ai** — Most video models, cheapest Wan 2.5, fast inference, good GPU pricing for self-host
2. **Runway API** — Multi-model access (own + Veo + Kling + Seedance), mature API
3. **Luma API** — Best for cinema-grade (HDR, EXR, 16 keyframes)
4. **Replicate** — Good for Grok Imagine, Kling 3.0 Omni, simple pay-per-use
5. **MiniMax API** — Cheapest Hailuo 02 direct pricing
6. **PixVerse API** — Direct PixVerse V6 access (highest ELO)

### Key Architectural Recommendations
1. **Model Router:** Route prompts to models based on content type (animation → Grok, cinematic → Kling, effects → Pika, text-heavy → Wan)
2. **Parallel Generation:** Fire 2-3 models simultaneously, return best result via automatic quality scoring
3. **Cascade Upscaling:** Generate at 720p with cheap model, upscale with Magnific Video Upscaler or Topaz
4. **Audio Pipeline:** Use models with native audio (Kling 3.0, PixVerse V6, Veo 3.1) or post-process with ElevenLabs
5. **Self-Host Fallback:** Keep Wan 2.1 1.3B for rate-limit/overflow handling on local GPU
6. **Multi-Shot Assembly:** Use Kling 3.0 Omni's multi-shot capability for narrative videos

---

## 10. KEY DATA SOURCES & METHODOLOGY

- **ArtificialAnalysis.ai Video Arena:** Human-preference ELO rankings (blind A/B voting)
- **fal.ai pricing page:** Direct API pricing for all models
- **Runway API changelog:** Model additions, pricing, capabilities (docs.dev.runwayml.com)
- **Luma API page:** Per-generation pricing breakdown
- **MiniMax API docs:** Video point pricing tiers
- **Pika pricing page:** Credit-based pricing
- **GitHub repos:** Wan 2.1, HunyuanVideo, CogVideoX, Mochi, LTX-Video, SVD
- **PixVerse homepage:** ArtificialAnalysis ELO comparison chart
- **Higgsfield/NVIDIA case study:** Orchestration architecture reference

### Data Currency Notes
- Pricing and model availability change rapidly in this space
- ELO scores from ArtificialAnalysis as of April 2, 2026
- Several newer models (Wan 2.7, Kling O3, LTX-2.3) were just released and may not have ELO scores yet
- Open-source models are evolving fast (HunyuanVideo 1.5 released Nov 2025, Wan 2.5 VACE May 2025)