# Prosograph

**Time-aligned annotation schema for speech that captures meaning beyond words.**

Prosograph is a specification for encoding paralinguistic information alongside transcribed speech—emotions, prosody, voice quality, tone, emphasis, and non-speech events—in a format that is:

- **Machine-validatable**: JSON Schema + semantic constraints
- **LLM-friendly**: structured YAML/JSON that models can generate and consume
- **Diffable**: deterministic ordering for version control
- **Multilingual**: first-class support for tonal languages (Thai, Mandarin, Vietnamese, etc.)

## What Problem Does Prosograph Solve?

Standard transcription loses everything except words. But speech carries rich paralinguistic information:

| Lost Information | Prosograph Track |
|------------------|------------------|
| "They said it sarcastically" | `emotion`, `voice_quality` |
| "With rising intonation" | `prosody`, `tone` |
| "Emphasizing 'never'" | `delivery.emphasis` |
| "After a dramatic pause" | `delivery.pauses` |
| "In a breathy whisper" | `voice_quality.breathiness` |
| "Thai rising tone on ไหม" | `tone.lexical`, `tone.surface` |

Prosograph provides a **standardized vocabulary** for this information, enabling:

- TTS systems to reproduce expressive speech
- Voice cloning with emotional fidelity
- Cross-lingual dubbing that preserves tone semantics
- Training data for expressive speech models
- Annotation interchange between tools

## Quick Start

### Minimal Valid Document

```yaml
prosograph: "1.0"
audio:
  uri: "file:clip.wav"
  duration_s: 2.5

segments:
  - id: "seg_1"
    t0: 0.0
    t1: 2.5
    text: "Hello, world!"
```

### With Expressive Annotations

```yaml
prosograph: "1.0"
audio:
  uri: "file:disappointed.wav"
  duration_s: 3.2

segments:
  - id: "seg_1"
    t0: 0.0
    t1: 3.2
    text: "Oh... I really thought this would work."
    tracks:
      emotion:
        label: "disappointed"
        vad:
          valence: -0.6
          arousal: 0.25
          dominance: 0.3
      prosody:
        rate_wpm: 95
        pitch_st: -1.5
      delivery:
        emphasis:
          - span: "really"
            strength: 0.7
            method: ["pitch_up", "duration_up"]
        pauses:
          - { t0: 0.15, t1: 0.35, type: "breath" }
      voice_quality:
        creak: 0.35
        breathiness: 0.45
```

## Project Structure

```
prosograph/
├── prosograph-spec.md        # Normative specification (RFC-style)
├── schema/
│   └── prosograph-1.0.json   # JSON Schema for validation
├── examples/
│   ├── thai-question.prosograph.yaml    # Tonal language example
│   └── english-emotive.prosograph.yaml  # Expressive speech example
├── tools/
│   └── validator.py          # Python validation tool
├── prompts/
│   └── audio-transcription.md # LLM prompt for generating Prosograph
└── README.md
```

## Validation

```bash
# Install dependencies
pip install pyyaml jsonschema

# Validate a document
python tools/validator.py examples/thai-question.prosograph.yaml

# JSON output
python tools/validator.py --json examples/english-emotive.prosograph.yaml
```

## Compliance Profiles

Prosograph defines three compliance levels:

| Profile | Requirements |
|---------|-------------|
| **PG-Core** | Segments with `t0`/`t1`, optional `text` |
| **PG-Expressive** | PG-Core + at least one of: `emotion`, `prosody`, `delivery`, `voice_quality` |
| **PG-Tonal** | PG-Expressive + `tone.system` for tonal languages + `tone.lexical` on tokens |

Declare your profile in `meta.profile` for interoperability.

## Core Tracks

### Emotion (`emotion`)
```yaml
emotion:
  label: "frustrated"
  vad:
    valence: -0.4    # [-1, 1] negative to positive
    arousal: 0.6     # [0, 1] calm to excited
    dominance: 0.3   # [0, 1] submissive to dominant
  confidence: 0.85
```

### Prosody (`prosody`)
```yaml
prosody:
  rate_wpm: 120
  pitch_st: 2.0      # semitones relative to baseline
  energy_db: 1.5     # dB relative to baseline
  contour:
    - { t: 0.5, f0_hz: 180 }
    - { t: 1.2, f0_hz: 220 }
```

### Delivery (`delivery`)
```yaml
delivery:
  enunciation: "crisp"
  clarity: 0.9
  emphasis:
    - span: "absolutely"
      strength: 0.8
      method: ["pitch_up", "energy_up"]
  pauses:
    - { t0: 1.2, t1: 1.5, type: "dramatic" }
```

### Voice Quality (`voice_quality`)
```yaml
voice_quality:
  creak: 0.3         # vocal fry
  breathiness: 0.2
  nasal: 0.0
  tension: 0.4
  smile: 0.6
```

### Tone (`tone`) - for tonal languages
```yaml
# Segment level
tone:
  system: "thai"
  phrase_type: "interrogative"

# Token level
tone:
  lexical: "rising"
  surface: "rising"
  contour: "24"
  realized:
    onset_hz: 200
    offset_hz: 280
```

## Tonal Language Support

Prosograph distinguishes:

- **Lexical tone**: The underlying, meaning-bearing tone
- **Surface tone**: The realized tone after sandhi rules
- **Phrase intonation**: Overlay that modifies but doesn't replace lexical tone

This prevents the common error of confusing emotional intonation with lexical tone in languages like Thai, Mandarin, or Vietnamese.

```yaml
interaction:
  tone_preservation: 0.95    # Lexical tone is sacred
  emotion_pitch_override: 0.15  # Emotion can only slightly modify pitch
```

## Design Principles

1. **Separation of concerns**: Lexical content, paralinguistics, and timing are orthogonal
2. **Inheritance**: Defaults flow down (document → segment → token)
3. **Extensibility**: Custom tracks via namespaced `extensions`
4. **No frame-level data by default**: Sparse contours, not dense features
5. **Round-trip stability**: YAML ↔ JSON without loss

## What Prosograph Is NOT

- A phonological theory (not trying to be ToBI)
- A forced-alignment tool (use WhisperX, Montreal, etc.)
- A feature extractor (use OpenSMILE, librosa, etc.)
- A TTS markup language (SSML does that)

Prosograph is the **interchange format** that sits between these tools.

## Use Cases

- **Training expressive TTS**: Provide emotion/prosody labels alongside audio
- **Voice cloning**: Preserve speaker's paralinguistic patterns
- **Dubbing**: Transfer tone semantics across languages
- **Accessibility**: Describe speech characteristics for deaf/HoH users
- **Research**: Standardized corpus annotation

## Contributing

See the [specification](prosograph-spec.md) for normative requirements. Contributions welcome:

- Additional examples for underrepresented languages
- Tooling integrations (forced aligners, TTS systems)
- JSON Schema refinements

## License

[TBD - suggest MIT or Apache 2.0]

## Acknowledgments

Prosograph draws inspiration from:
- ToBI (Tones and Break Indices)
- SSML (Speech Synthesis Markup Language)
- Praat TextGrid format
- Emotion annotation standards (VAD model)
