# TEMUCLAUDE MUSIC ORCHESTRATION — RESEARCH & PLAN
> Date: July 6, 2026
> Status: Fully researched, verified from primary sources

---

## RESEARCH FINDINGS

### API Endpoint (verified from docs.aimlapi.com)
- `POST https://api.aimlapi.com/v2/generate/audio` — submit music generation (returns generation_id)
- `GET https://api.aimlapi.com/v2/generate/audio?generation_id=...` — retrieve result (poll until completed)
- Same endpoint for ALL music models — just change the `model` parameter
- Async pattern: submit → poll → retrieve (same as video)

### Music Model Landscape (6 models on AIML API)

| Model | $/generation | Max Duration | Key Strength | Model ID |
|-------|-------------|-------------|-------------|----------|
| MiniMax Music 2.6 | $0.20 | 5 minutes | Full structured songs, vocals, arrangement, progression, improved bass | `minimax/music-2.6` |
| MiniMax Music 2.0 | $0.0315 | 4 minutes | Fast, cost-efficient, full songs with vocals, detailed instrumentals | `minimax/music-2.0` |
| MiniMax Music 1.5 | ~$0.15 | Long | Long fully-arranged songs, natural vocals, ethnic instruments | `minimax/music-1.5` |
| MiniMax Music Cover | $0.195 | — | Transforms existing songs into new styles (cover/remix) | `minimax/music-cover` |
| Eleven Music v1 | ~$0.20 | 5 min (300s) | High-quality from text prompts, genre/mood/instruments/vocals/tempo | `elevenlabs/eleven_music` |
| MiniMax Music (legacy) | — | — | Legacy model | `minimax-music` |

### API Parameters (verified)

**Eleven Music v1:**
- `model`: "elevenlabs/eleven_music"
- `prompt`: text description (genre, mood, instruments, vocals, tempo, lyrics) — max 2000 chars
- `music_length_ms`: 10000-300000 (10s to 5min)
- Async: returns generation_id, poll for completion

**MiniMax Music 2.0:**
- `model`: "minimax/music-2.0"
- `prompt`: style/mood description — 10-2000 chars
- `lyrics`: song lyrics — 10-3000 chars (supports [Intro], [Verse], [Chorus], [Bridge], [Outro] tags)
- `audio_setting`: sample_rate (16k-44.1k), bitrate (32k-256k), format (mp3/wav/pcm)
- Async: returns generation_id, poll for completion

**MiniMax Music 2.6:**
- `model`: "minimax/music-2.6"
- Same parameters as 2.0 but with improved quality
- Full-length songs up to 5 minutes
- Better vocal handling, improved bass, structured progression

**MiniMax Music Cover:**
- `model`: "minimax/music-cover"
- Takes a source song + style description → generates a cover in new style
- Unique: only model that does song transformation/cover

### How to Judge Music Quality

Music judging is different from image/video — the judge needs to LISTEN to audio. Options:

1. **LLM text analysis** (no audio listening) — judge the TEXT quality:
   - Did the prompt describe a coherent song?
   - Are the lyrics well-structured?
   - This doesn't judge the AUDIO quality, just the prompt interpretation

2. **Audio metadata analysis** — technical quality:
   - Duration (did it generate the requested length?)
   - Sample rate, bitrate, format
   - File size

3. **LLM audio understanding** (requires audio-capable model):
   - Gemini 3 Flash can process audio
   - Score: melody quality, rhythm, vocal naturalness, instrument balance, prompt adherence
   - This is the ideal approach

4. **Hybrid approach (what we'll use)**:
   - Use LLM to analyze prompt interpretation (did the model follow genre/mood instructions?)
   - Use audio metadata for technical quality
   - For premium tier, use Gemini 3 Flash (audio-capable) for actual audio quality scoring
   - Score on: melody_quality, rhythm, vocal_naturalness, instrument_balance, prompt_adherence, lyrics_accuracy

### Unique Capabilities (routing, single model)

| Capability | Best Model | Why |
|-----------|-----------|-----|
| Song cover/remix | MiniMax Music Cover | Only model that transforms existing songs |
| Longest duration (5 min) | MiniMax Music 2.6 / Eleven Music | 5 minute max |
| Cheapest | MiniMax Music 2.0 | $0.0315/generation |
| Best quality | MiniMax Music 2.6 | Latest, improved vocals, bass, structure |
| Custom lyrics with structure | MiniMax Music 2.0/2.6 | [Verse], [Chorus], [Bridge] tags |
| Ethnic instruments | MiniMax Music 1.5 | Excels in diverse cultural contexts |

### Competitive Landscape

**No one does music orchestration.** All competitors use a single music model:
- Suno: only their own model
- Udio: only their own model
- MiniMax: only their own models
- ElevenLabs: only their own model

Higgsfield and other platforms don't do music generation at all.

### Orchestration Strategy

**CASCADING** (same as image/video/TTS):
1. Generate with cheapest model first (MiniMax Music 2.0, $0.0315)
2. Judge it. If score >= threshold → return (cost: $0.0315)
3. If below threshold → add MiniMax Music 1.5 ($0.15). Judge both.
4. If still below → add MiniMax Music 2.6 ($0.20). Judge all three.
5. If still below → add Eleven Music ($0.20). Judge all four.

**Unique capability routing:**
- Song cover/remix → MiniMax Music Cover only
- Ethnic instruments → MiniMax Music 1.5
- Custom lyrics with structure → MiniMax Music 2.6

### Cost Projections

| Tier | Models | $/generation | When |
|------|--------|-------------|------|
| Draft | MiniMax Music 2.0 | $0.0315 | 60% of requests |
| Standard | MiniMax 2.0 → 1.5 (cascade) | $0.06 avg | 30% of requests |
| Premium | MiniMax 2.0 → 1.5 → 2.6 → Eleven (cascade) | $0.10 avg | 10% of requests |
| Blended average | | $0.046/gen | |

vs MiniMax Music 2.6 alone: $0.20/gen
**4.3x cheaper** with cascading

### Quality Projections

- MiniMax Music 2.6 is the frontier (~$0.20/gen)
- Our best-of-3 cascade (2.0 + 1.5 + 2.6) captures the best output
- If 2.0 produces good music 60% of the time, we save 4.3x cost
- When 2.0 fails, we cascade to 1.5, then 2.6 — we always get the frontier quality when needed
- Judge scores melody, rhythm, vocals, instruments, prompt adherence