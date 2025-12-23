# Prosograph Specification v1.0

A Prosograph document is a time-aligned annotation artifact for speech/audio that captures lexical content + paralinguistics (emotion, prosody, voice quality, articulation/enunciation, tone, disfluencies, events) in a form that is machine-validatable, LLM-friendly, and diffable.

Prosograph is a schema + semantics (not tied to one concrete serialization). This spec defines:
	•	a canonical data model
	•	normative requirements (MUST/SHOULD/MAY)
	•	a canonical YAML/JSON mapping
	•	validation rules
	•	interchange guarantees

⸻

1. Terminology and Normativity

Key words MUST, MUST NOT, SHOULD, SHOULD NOT, MAY are to be interpreted as normative requirements.

Timeline: continuous time axis for the underlying audio.

Span: an interval [t0, t1) measured on the timeline.

Anchor: a single time t.

Track: an annotation layer (e.g., prosody, emotion, tone).

Segment: a higher-level span containing text and track values.

Token: the smallest time-aligned unit (word/morpheme/character/phoneme/event), depending on language and intent.

⸻

2. Design Goals

Prosograph MUST support:
	1.	Precise time alignment (segment and token).
	2.	Multilingual content with tonal and non-tonal languages.
	3.	Layered annotations with explicit precedence/interaction rules.
	4.	Deterministic validation (schema + semantic constraints).
	5.	Extensibility via namespaced custom tracks and fields.
	6.	Round-trip stability across YAML ↔ JSON.

Prosograph does not attempt to:
	•	be a full phonological theory (e.g., ToBI completeness)
	•	mandate a specific forced-aligner or feature extractor
	•	encode raw frame-level features by default (it can, but sparingly)

⸻

3. File Format and Serialization

3.1 Canonical Serialization

A Prosograph document MUST be representable in:
	•	YAML 1.2 or
	•	JSON (UTF-8)

The canonical mapping is “Prosograph-JSON model” (section 4). YAML is a direct syntax sugar over the same object model.

3.2 Deterministic Ordering

To be diff-friendly, writers SHOULD emit object keys in a stable order. Readers MUST NOT rely on ordering.

3.3 Units
	•	Time values MUST be expressed in seconds as a JSON number (IEEE-754 double).
	•	Frequencies in Hz, loudness in LUFS, pitch in semitones (st) relative to speaker baseline when specified, energies in dB relative to a defined reference (section 8.3).

⸻

4. Top-Level Object Model

A Prosograph document is a single object with these top-level keys:

prosograph: "1.0"          # REQUIRED: semantic version string
id: "pg:..."               # OPTIONAL: globally unique identifier (URN/URL recommended)
meta: {...}                # OPTIONAL: provenance, toolchain, hashes
audio: {...}               # REQUIRED
defaults: {...}            # OPTIONAL
tracks: {...}              # OPTIONAL: global track definitions
segments: [...]            # REQUIRED (can be empty only for pure metadata docs)
lexicon: {...}             # OPTIONAL: shared IPA, tone inventories, speaker baselines
extensions: {...}          # OPTIONAL: vendor/user extensions (namespaced)

Readers MUST ignore unknown top-level keys.

⸻

5. audio Object (Required)

audio:
  uri: "..."                     # REQUIRED: pointer to audio asset
  duration_s: 12.34              # REQUIRED
  sample_rate_hz: 48000          # OPTIONAL but RECOMMENDED
  channels: 1                    # OPTIONAL but RECOMMENDED
  codec: "pcm_s16le"             # OPTIONAL
  sha256: "..."                  # OPTIONAL but RECOMMENDED for integrity
  timebase:
    origin: 0.0                  # OPTIONAL default 0.0
    offset_s: 0.0                # OPTIONAL for aligned subsets

Constraints:
	•	duration_s MUST be > 0.
	•	All annotation times MUST satisfy 0 ≤ t ≤ duration_s after applying timebase.offset_s (if present).

⸻

6. defaults Object (Optional)

Defaults provide inheritance to segments/tokens where omitted.

defaults:
  language: "th-TH"              # BCP-47
  speaker:
    id: "spk_01"
    baseline:
      f0_hz: 160                 # OPTIONAL baseline pitch
      f0_range_hz: [120, 220]    # OPTIONAL
      loudness_lufs: -16         # OPTIONAL
  style:
    emotion: {...}
    prosody: {...}
    articulation: {...}
    voice_quality: {...}
  tokenization:
    unit: "word"                 # word | morpheme | char | phoneme | mixed

Inheritance rule:
	•	Segment fields override defaults.
	•	Token fields override segment fields.
	•	A missing field means “inherit if available; else unknown”.

⸻

7. segments Array (Required)

Each segment MUST be an object:

- id: "seg_001"                  # REQUIRED unique within doc
  t0: 0.000                      # REQUIRED
  t1: 4.320                      # REQUIRED, t1 > t0
  language: "en-US"              # OPTIONAL override
  speaker_id: "spk_01"           # OPTIONAL override
  text: "..."                    # OPTIONAL (but RECOMMENDED if speech)
  normalized_text: "..."         # OPTIONAL
  intent: {...}                  # OPTIONAL
  tracks: {...}                  # OPTIONAL: per-segment track payloads
  tokens: [...]                  # OPTIONAL
  events: [...]                  # OPTIONAL (segment-scoped events)
  notes: [...]                   # OPTIONAL free-text (non-normative)

7.1 Segment time semantics
	•	The segment span is half-open: [t0, t1).
	•	Segments MAY overlap (e.g., two annotators; two tiers). Overlap policy is controlled by tracks definitions (section 9).

7.2 Text semantics
	•	text is the human-readable orthography.
	•	normalized_text SHOULD be used when you need deterministic downstream processing (e.g., punctuation normalization, number expansion). If present, it MUST represent the same utterance as text.

⸻

8. Core Track Payloads

Prosograph provides a set of core track names with standardized fields. Producers MAY add custom tracks (section 12), but core track semantics MUST remain stable.

All track payloads can appear at:
	•	defaults.style.<track>
	•	segment.tracks.<track>
	•	token.<track>

8.1 Emotion Track (emotion)

Emotion MUST support both:
	•	categorical label (optional)
	•	dimensional representation (recommended)

emotion:
  label: "disappointed"          # OPTIONAL
  vad:
    valence: -0.45               # REQUIRED if vad present, range [-1, 1]
    arousal: 0.35                # range [0, 1]
    dominance: 0.30              # range [0, 1]
  confidence: 0.82               # OPTIONAL [0,1]
  source: "human|model|hybrid"   # OPTIONAL

Constraints:
	•	If vad exists, its fields MUST be present and within range.
	•	label vocabulary is open; producers SHOULD document their label set in lexicon.emotion_inventory.

8.2 Prosody Track (prosody)

Prosody describes rate, pitch, intensity, and optionally a sparse contour.

prosody:
  rate_wpm: 135                  # OPTIONAL
  pitch_st: -0.8                 # OPTIONAL relative shift (semitones)
  pitch_range_st: 6.0            # OPTIONAL
  energy_db: -1.5                # OPTIONAL relative shift
  contour:
    # sparse anchors on the segment or token span
    - { t: 0.20, f0_hz: 165 }    # t is absolute seconds unless local=true
    - { t: 1.10, f0_hz: 190 }
  local_time: false              # OPTIONAL default false

Semantics:
	•	pitch_st is relative to speaker baseline defaults.speaker.baseline.f0_hz (if known). If baseline unknown, pitch_st is relative to an implicit baseline (documented in meta); consumers MUST treat it as relative-only.
	•	contour is sparse by intent; frame-level data belongs in tracks.frame_features (optional extension).

8.3 Loudness and energy reference

If using energy_db, the reference MUST be declared in one of:
	•	defaults.speaker.baseline.loudness_lufs (preferred) OR
	•	meta.references.energy_db_ref (e.g., “relative to segment RMS”)

If no reference declared, consumers MUST treat energy_db as a purely comparative feature.

8.4 Articulation/Delivery Track (delivery)

Captures enunciation, clarity, emphasis, pauses, and speaking style.

delivery:
  enunciation: "crisp|careful|casual|slurred|hyper"   # OPTIONAL open vocab
  clarity: 0.90                   # OPTIONAL [0,1]
  emphasis:
    - span: "not angry"           # OPTIONAL substring or token_ref span
      strength: 0.60              # [0,1]
      method: ["pitch_up","duration_up","energy_up","pause_before"]
  pauses:
    - { t0: 0.42, t1: 0.58, type: "dramatic|breath|filled|unfilled" }

span resolution:
	•	If span is a string, it is resolved against segment.text by substring match.
	•	For deterministic alignment, producers SHOULD use token references:
span: { token_ids: ["tok_04","tok_05"] }

8.5 Voice Quality Track (voice_quality)

Continuous scalars in [0,1] (unless otherwise specified). Open set but core fields standardized.

voice_quality:
  creak: 0.15
  breathiness: 0.20
  nasal: 0.00
  tension: 0.35
  smile: 0.00

8.6 Tone Track (tone)

Tone MUST separate:
	•	lexical tone (meaning-bearing)
	•	surface tone (post-sandhi)
	•	optional realized anchors

Tone differs by tone.system.

tone:
  system: "thai|mandarin|vietnamese|pitch-accent|stress-accent|none"  # REQUIRED when tone used
  phrase_type: "declarative|interrogative|continuation|exclamative"  # OPTIONAL segment-level
  register: "low|mid|high"                                           # OPTIONAL
  downstep: 0.0                                                      # OPTIONAL [0,1]

Token-level tone payload:

tone:
  lexical: "mid"                 # REQUIRED for tonal languages at token level
  surface: "mid"                 # OPTIONAL (post-sandhi)
  sandhi:
    from: "falling"
    to: "rising"
    rule: "..."                  # OPTIONAL
  contour: "33"                  # OPTIONAL symbolic
  realized:
    onset_hz: 155                # OPTIONAL
    nadir_hz: 120                # OPTIONAL
    offset_hz: 150               # OPTIONAL
  confidence: 0.9                # OPTIONAL

Constraints:
	•	If tone.system is tonal (thai/mandarin/vietnamese), tokens that represent tone-bearing units SHOULD include tone.lexical.
	•	For pitch-accent, lexical MAY be an accent pattern (e.g., H-L), and realized anchors MAY describe f0.
	•	For stress-accent, tone MAY be replaced by prosody + prominence, but the structure remains valid.

Tone inventories SHOULD be declared in lexicon.tone_inventory[system].

⸻

9. Track Definitions (tracks)

tracks defines global behavior: overlap rules, required fields, and interpretation.

tracks:
  emotion:
    scope: ["segment","token"]
    overlap: "allow"             # allow | forbid | last_wins | merge
  prosody:
    scope: ["segment","token"]
    overlap: "allow"
  tone:
    scope: ["segment","token"]
    overlap: "allow"

If omitted, tracks are assumed scope: ["segment","token"] and overlap: "allow".

⸻

10. Tokens

Tokens are optional but RECOMMENDED for precision. Token granularity is defined by defaults.tokenization.unit and may vary per segment.

Token object:

- id: "tok_001"                  # REQUIRED unique within document
  t0: 0.000                      # REQUIRED
  t1: 0.320                      # REQUIRED
  kind: "word"                   # OPTIONAL: word|morpheme|char|phoneme|event
  text: "Look"                   # OPTIONAL (required for word/char)
  norm: "look"                   # OPTIONAL
  ipa: "lʊk"                     # OPTIONAL
  stress: 1                      # OPTIONAL (0/1/2), semantics language-dependent
  tracks:
    prosody: {...}               # OPTIONAL
    tone: {...}                  # OPTIONAL
    delivery: {...}              # OPTIONAL
  refs:
    segment_id: "seg_001"        # OPTIONAL explicit backref

10.1 Token coverage constraints

A segment MAY have gaps without tokens. If tokens are present:
	•	Tokens MUST satisfy segment.t0 ≤ token.t0 < token.t1 ≤ segment.t1.
	•	Tokens SHOULD be non-overlapping and monotonic by time within a segment unless tokenization.unit = mixed and overlap is intentional (e.g., word + phoneme tiers). In that case, kind MUST disambiguate tiers.

10.2 Event tokens

Non-speech events SHOULD be encoded as tokens with kind: event:

- id: "evt_01"
  t0: 1.16
  t1: 1.24
  kind: "event"
  event: "laugh|cough|inhale|exhale|lip_smack|click|noise|silence"
  confidence: 0.8


⸻

11. Interactions and Precedence

Prosograph supports explicit interaction constraints to avoid “tone = emotion” conflation.

At segment or document level:

interaction:
  tone_preservation: 0.90        # [0,1] meaning must survive
  emotion_pitch_override: 0.20   # [0,1] allowed pitch distortion from emotion
  intonation_overlay: "additive|multiplicative|unspecified"

Interpretation:
	•	Consumers MUST treat tone.lexical as semantic-critical when tone_preservation ≥ 0.5.
	•	Where pitch-based tracks conflict, precedence SHOULD be:
	1.	lexical tone constraints
	2.	intonation overlay
	3.	emotion/prosody stylistics
unless explicitly overridden.

⸻

12. Extensibility Rules

Custom fields are allowed but MUST be namespaced to avoid collisions.

12.1 Namespacing

Any extension key MUST either:
	•	be nested under extensions, OR
	•	be prefixed with a reverse-DNS namespace, e.g. com.lumicello.something

Example:

extensions:
  com.lumicello.safety:
    child_directed: true

12.2 Forward compatibility

Readers MUST ignore unknown extension namespaces.

⸻

13. Validation Requirements

A Prosograph document is valid if:

13.1 Structural validity
	•	prosograph is present and supported (major version match required).
	•	audio.uri and audio.duration_s present.
	•	Each segment.id is unique.
	•	All times are numbers and satisfy constraints.

13.2 Temporal validity
	•	For every segment: 0 ≤ t0 < t1 ≤ duration_s.
	•	For every token: same, and within owning segment if segment_ref exists.

13.3 Range validity (core tracks)
	•	clarity, voice_quality.*, confidence MUST be in [0,1] when present.
	•	emotion.vad.valence ∈ [-1,1], arousal ∈ [0,1], dominance ∈ [0,1].

13.4 Referential validity

If token references appear (e.g., in emphasis spans):
	•	referenced token IDs MUST exist.

13.5 Text consistency (recommended)

If normalized_text is present, it SHOULD be derivable from text under documented normalization rules in meta.normalization.

⸻

14. Provenance (meta) and Reproducibility

meta SHOULD include:

meta:
  created_at: "2025-12-23T14:30:00+07:00"
  created_by: { tool: "prosograph-cli", version: "0.3.1" }
  source:
    recording_id: "..."          # if applicable
    transcript_source: "human"
    alignment_source: "whisperx"
  licenses: {...}
  normalization: { scheme: "..." }

Consumers SHOULD propagate provenance to derived artifacts.

⸻

15. Minimal Example (Valid)

prosograph: "1.0"
audio:
  uri: "file:clip.wav"
  duration_s: 2.5

segments:
  - id: "seg_1"
    t0: 0.0
    t1: 2.5
    language: "th-TH"
    text: "มาไหม"
    tracks:
      tone: { system: "thai", phrase_type: "interrogative" }
    tokens:
      - id: "tok_1"
        t0: 0.0
        t1: 1.1
        kind: "word"
        text: "มา"
        tracks:
          tone: { lexical: "mid", contour: "33" }
      - id: "tok_2"
        t0: 1.1
        t1: 2.3
        kind: "word"
        text: "ไหม"
        tracks:
          tone: { lexical: "rising", contour: "24→45" }


⸻

16. Recommended “Profiles” (Interchange Contracts)

To keep systems interoperable, Prosograph defines optional compliance profiles:

16.1 PG-Core
	•	segments with t0/t1
	•	text optional
	•	no tokens required
	•	no tonal requirement

16.2 PG-Expressive
	•	PG-Core
	•	at least one of: emotion/prosody/delivery/voice_quality

16.3 PG-Tonal
	•	PG-Expressive
	•	tone.system declared when language is tonal
	•	tone-bearing tokens include tone.lexical (SHOULD)

A file MAY declare profile in meta.profile.

⸻

17. What to Call It (Terminology Guidance)
	•	Prosograph: the framework/specification
	•	Prosograph document: one .prosograph.yaml / .prosograph.json file
	•	Prosograph schema: the formal validation schema derived from this spec
	•	Avoid calling it a “language” unless you later add procedural directives (generation controls). Today it’s an annotation schema with a canonical serialization.

⸻

18. Recommended File Extensions
	•	*.prosograph.yaml / *.prosograph.yml
	•	*.prosograph.json
