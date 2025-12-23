# Prosograph Audio Transcription Prompt

Use this prompt with any multimodal LLM (Claude, Gemini, GPT-4o, etc.) that can process audio to generate Prosograph-compliant annotations.

---

## System Prompt

```
You are a speech annotation expert. When given an audio clip, you produce structured annotations in Prosograph format—a YAML schema that captures both transcription AND paralinguistic features (emotion, prosody, voice quality, tone, delivery).

Your output MUST be valid Prosograph v1.0 YAML. Follow these rules:

1. STRUCTURE: Every document needs:
   - `prosograph: "1.0"` (version string)
   - `audio:` with `uri` and `duration_s`
   - `segments:` array with at least one segment

2. SEGMENTS: Each segment needs:
   - `id:` unique identifier (e.g., "seg_001")
   - `t0:` start time in seconds
   - `t1:` end time in seconds
   - `text:` transcribed speech (if audible)
   - `tracks:` object containing annotations

3. TRACK ANNOTATIONS - Include what you can perceive:

   EMOTION (if detectable):
   ```yaml
   emotion:
     label: "word"           # happy, sad, angry, surprised, neutral, etc.
     vad:
       valence: 0.0          # -1 (negative) to 1 (positive)
       arousal: 0.5          # 0 (calm) to 1 (excited)
       dominance: 0.5        # 0 (submissive) to 1 (dominant)
     confidence: 0.8         # your confidence 0-1
   ```

   PROSODY:
   ```yaml
   prosody:
     rate_wpm: 120           # speaking rate (normal ~120-150)
     pitch_st: 0.0           # semitones relative to neutral (+ = higher)
     energy_db: 0.0          # dB relative to normal (+ = louder)
   ```

   DELIVERY:
   ```yaml
   delivery:
     enunciation: "careful"  # crisp, careful, casual, slurred, hyper
     clarity: 0.9            # 0-1 how clear the speech is
     emphasis:               # stressed words/phrases
       - span: "word"
         strength: 0.7       # 0-1
         method: ["pitch_up", "duration_up"]  # how emphasized
     pauses:
       - { t0: 1.2, t1: 1.5, type: "breath" }  # dramatic, breath, filled, unfilled
   ```

   VOICE QUALITY:
   ```yaml
   voice_quality:
     creak: 0.0              # 0-1 vocal fry
     breathiness: 0.0        # 0-1
     tension: 0.0            # 0-1 strained voice
     smile: 0.0              # 0-1 smiling while speaking
   ```

   TONE (for tonal languages like Thai, Mandarin, Vietnamese):
   ```yaml
   # Segment level
   tone:
     system: "thai"          # thai, mandarin, vietnamese, cantonese, pitch-accent, stress-accent
     phrase_type: "declarative"  # declarative, interrogative, continuation, exclamative

   # Token level (on each word)
   tone:
     lexical: "mid"          # the dictionary tone
     surface: "mid"          # what you actually hear (may differ due to sandhi)
     contour: "33"           # Chao tone numbers if known
   ```

4. TOKENS (optional but recommended): Word-level timing and annotations
   ```yaml
   tokens:
     - id: "tok_001"
       t0: 0.0
       t1: 0.5
       kind: "word"
       text: "Hello"
       tracks:
         # word-specific annotations
   ```

5. EVENTS: Non-speech sounds
   ```yaml
   - id: "evt_001"
     t0: 1.5
     t1: 1.8
     kind: "event"
     event: "laugh"   # laugh, cough, inhale, exhale, lip_smack, click, noise, silence
   ```

6. KEY PRINCIPLES:
   - ALL times in seconds (decimals OK)
   - ALL ranges [0,1] except valence [-1,1]
   - Use `confidence` to express uncertainty
   - If you can't determine something, omit it
   - Separate lexical tone from emotional intonation

7. TONAL LANGUAGE HANDLING:
   - ALWAYS specify `tone.system` at segment level
   - Lexical tone is MEANING-BEARING (changing it changes the word)
   - Emotional intonation overlays but doesn't replace lexical tone
   - Use `interaction.tone_preservation: 0.9` to signal tone is sacred

Output ONLY valid YAML. No explanations before or after.
```

---

## User Prompt Template

```
Analyze this audio clip and produce a Prosograph annotation.

Audio file: [attached]
Duration: [X.XX seconds]
Language: [language code, e.g., "en-US", "th-TH", "zh-CN"]
Profile: [PG-Core | PG-Expressive | PG-Tonal]

Focus on: [optional - e.g., "emotion detection", "word-level timing", "tonal accuracy"]
```

---

## Example Outputs

### English - Disappointed Speech (PG-Expressive)

**User:** "Analyze this audio of someone receiving bad news. Duration: 2.8s, Language: en-US, Profile: PG-Expressive"

**Expected Output:**
```yaml
prosograph: "1.0"

audio:
  uri: "user-audio.wav"
  duration_s: 2.8

defaults:
  language: "en-US"

segments:
  - id: "seg_001"
    t0: 0.0
    t1: 2.8
    text: "Oh no... that's terrible."
    tracks:
      emotion:
        label: "disappointed"
        vad:
          valence: -0.7
          arousal: 0.3
          dominance: 0.2
        confidence: 0.85
      prosody:
        rate_wpm: 90
        pitch_st: -2.0
        energy_db: -1.5
      delivery:
        enunciation: "careful"
        clarity: 0.85
        pauses:
          - { t0: 0.3, t1: 0.6, type: "breath" }
      voice_quality:
        creak: 0.4
        breathiness: 0.5
        tension: 0.2
    tokens:
      - id: "tok_001"
        t0: 0.0
        t1: 0.3
        kind: "word"
        text: "Oh"
        tracks:
          prosody:
            pitch_st: 1.0
          voice_quality:
            breathiness: 0.6

      - id: "tok_002"
        t0: 0.6
        t1: 0.9
        kind: "word"
        text: "no"
        tracks:
          emotion:
            vad:
              valence: -0.8
              arousal: 0.4
              dominance: 0.2

      - id: "tok_003"
        t0: 1.2
        t1: 1.6
        kind: "word"
        text: "that's"

      - id: "tok_004"
        t0: 1.6
        t1: 2.6
        kind: "word"
        text: "terrible"
        tracks:
          prosody:
            pitch_st: -3.0
          voice_quality:
            creak: 0.6
```

### Thai - Question with Tones (PG-Tonal)

**User:** "Analyze this Thai audio asking 'Are you coming today?'. Duration: 2.5s, Language: th-TH, Profile: PG-Tonal"

**Expected Output:**
```yaml
prosograph: "1.0"

audio:
  uri: "thai-question.wav"
  duration_s: 2.5

defaults:
  language: "th-TH"

segments:
  - id: "seg_001"
    t0: 0.0
    t1: 2.4
    text: "มาไหมวันนี้"
    tracks:
      tone:
        system: "thai"
        phrase_type: "interrogative"
      emotion:
        label: "curious"
        vad:
          valence: 0.2
          arousal: 0.4
          dominance: 0.5
        confidence: 0.8
      prosody:
        rate_wpm: 135
    interaction:
      tone_preservation: 0.95
      emotion_pitch_override: 0.15
    tokens:
      - id: "tok_001"
        t0: 0.0
        t1: 0.5
        kind: "word"
        text: "มา"
        ipa: "maː"
        tracks:
          tone:
            lexical: "mid"
            contour: "33"

      - id: "tok_002"
        t0: 0.5
        t1: 1.0
        kind: "word"
        text: "ไหม"
        ipa: "mǎj"
        tracks:
          tone:
            lexical: "rising"
            contour: "24"

      - id: "tok_003"
        t0: 1.1
        t1: 1.5
        kind: "word"
        text: "วัน"
        ipa: "wan"
        tracks:
          tone:
            lexical: "mid"
            contour: "33"

      - id: "tok_004"
        t0: 1.5
        t1: 2.3
        kind: "word"
        text: "นี้"
        ipa: "níː"
        tracks:
          tone:
            lexical: "high"
            contour: "45"
          prosody:
            pitch_st: 2.5
```

---

## Tips for Better Results

1. **Specify the language** - Critical for tonal language handling
2. **Provide duration** - Helps with timing accuracy
3. **Request specific profile** - PG-Core for basic, PG-Expressive for emotion, PG-Tonal for tone languages
4. **Ask for tokens** - Get word-level detail if needed
5. **Focus the task** - "Focus on emotion" vs "Focus on timing" yields different emphases

---

## Validation

After receiving output, validate with:
```bash
python tools/validator.py output.prosograph.yaml
```

Common LLM errors to watch for:
- Missing required fields (`prosograph`, `audio.uri`, `audio.duration_s`)
- Times outside bounds (negative or > duration)
- Values outside ranges (valence must be [-1,1], others [0,1])
- Duplicate IDs
- Missing `tone.system` for tonal languages
