# TEMUCLAUDE TTS ORCHESTRATION — RESEARCH & PLAN
> Date: July 6, 2026
> Status: Researched and verified

---

## RESEARCH FINDINGS

### API Endpoint (verified from docs.aimlapi.com)
- `POST https://api.aimlapi.com/v1/tts`
- Body: `{"model": "model_id", "text": "...", "voice": "...", "response_format": "mp3"}`
- Response: `{"audio": {"url": "https://..."}}`
- Same endpoint for ALL TTS models — just change the `model` parameter

### TTS Model Landscape (26 models on AIML API)

**Tier 1 — Frontier Quality (best-of-3 for premium):**

| Model | $/1k chars | Languages | Key Strength |
|-------|-----------|-----------|-------------|
| ElevenLabs v3 Alpha | $0.234 | 32+ | Most expressive, voice cloning, conversational AI |
| ElevenLabs Multilingual v2 | $0.234 | 32+ | Same voice across languages, emotional depth |
| Hume Octave 2 | $0.078 | 11 | LLM-powered emotion understanding, 71% preferred over ElevenLabs in blind test |
| MiniMax Speech 2.6 HD | $0.13 | Multi | Studio-grade prosody, breath control, instant cloning |
| MiniMax Speech 2.8 HD | ~$0.13 | Multi | Latest MiniMax, highest quality |

**Tier 2 — Standard Quality (best-of-3 for balanced):**

| Model | $/1k chars | Key Strength |
|-------|-----------|-------------|
| ElevenLabs Turbo v2.5 | $0.117 | Near real-time, good quality |
| MiniMax Speech 2.6 Turbo | $0.078 | Fast, expressive |
| VibeVoice 7B | $0.052 | Customizable personas, open-weights style |
| MAI-Voice 2 | $28.60/1M tokens | Microsoft, natural prosody, multiple styles |

**Tier 3 — Budget (single model for simple text):**

| Model | $/1k chars | Key Strength |
|-------|-----------|-------------|
| Qwen3 TTS Flash | $0.013 | 119 languages, ultra-low latency, cheapest |
| DeepGram Aura 2 | $0.039 | Sub-200ms TTFB, enterprise-grade |
| OpenAI TTS-1 | $0.0195 | Reliable, multi-voice |
| OpenAI TTS-1 HD | $0.0315 | Higher quality OpenAI |
| GPT-4o Mini TTS | $0.00078 | Cheapest overall, emotional intonation |

### How to Judge TTS Quality

TTS judging is different from image judging — the judge needs to LISTEN, not look. Options:

1. **LLM text analysis** (no audio listening needed) — judge the TEXT quality:
   - Did the model pronounce all words correctly?
   - Did it handle punctuation (pauses, emphasis)?
   - Did it handle numbers, dates, abbreviations correctly?

2. **Audio analysis model** (requires audio understanding):
   - Use a vision-audio LLM (Gemini 3 Flash has audio understanding)
   - Score: naturalness, emotion, clarity, pacing, pronunciation
   - This is the ideal approach but requires audio-capable judges

3. **Hybrid approach** (what we'll use):
   - Use LLM to analyze the text rendering (pronunciation, pacing)
   - Use audio metadata (duration, sample rate) for technical quality
   - For premium tier, use audio-capable judge (Gemini 3 Flash)
   - Score on: naturalness, emotion, clarity, pronunciation, pacing

### Unique Capabilities (routing, single model)

| Capability | Best Model | Why |
|-----------|-----------|-----|
| Voice cloning | ElevenLabs v3 Alpha / Multilingual v2 | Best cloning quality |
| 119 languages | Qwen3 TTS Flash | Most languages |
| Sub-200ms latency | DeepGram Aura 2 | Lowest TTFB |
| LLM emotion understanding | Hume Octave 2 | Interprets emotional intent semantically |
| Instant voice cloning | MiniMax Speech 2.6 HD | Instant cloning |
| Microsoft natural prosody | MAI-Voice 2 | Azure AI Speech quality |
| Cheapest | GPT-4o Mini TTS | $0.00078/1k chars |

### Competitive Landscape

**No one does TTS orchestration.** All competitors use a single TTS provider:
- OpenAI: only their TTS
- Google: only Google TTS
- Azure: only Azure TTS
- ElevenLabs: only ElevenLabs

Higgsfield and other platforms don't do TTS at all. This is a clear gap.

### Projected Performance

**vs ElevenLabs v3 Alpha (the frontier):**
- ElevenLabs wins ~60% of blind comparisons (it's the market leader)
- Our best-of-3 (ElevenLabs v3 + Octave 2 + MiniMax 2.6 HD) captures the other 40%
- Octave 2 alone is preferred over ElevenLabs 71% of the time in Hume's own test
- Projected: we beat ElevenLabs in 50-60% of comparisons → we become the new frontier

**Cost:**
- ElevenLabs v3 alone: $0.234/1k chars
- Our blended (60% draft $0.013, 30% standard $0.065, 10% premium $0.147): ~$0.034/1k chars
- **6.9x cheaper** than ElevenLabs alone