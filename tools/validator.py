#!/usr/bin/env python3
"""
Prosograph Validator v1.0

Validates Prosograph documents against the JSON Schema and performs
additional semantic validations per the specification.

Usage:
    python validator.py <file.prosograph.yaml>
    python validator.py <file.prosograph.json>
    python validator.py --check-profile <file>
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

try:
    import jsonschema
    from jsonschema import Draft202012Validator, ValidationError
except ImportError:
    jsonschema = None


class ValidationResult:
    """Container for validation results."""

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []
        self.profile: str | None = None

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def add_info(self, msg: str) -> None:
        self.info.append(msg)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def print_report(self) -> None:
        """Print validation report to stdout."""
        if self.profile:
            print(f"\n{'='*60}")
            print(f"Profile Compliance: {self.profile}")
            print(f"{'='*60}")

        if self.errors:
            print(f"\n{'='*60}")
            print(f"ERRORS ({len(self.errors)})")
            print(f"{'='*60}")
            for i, err in enumerate(self.errors, 1):
                print(f"  {i}. {err}")

        if self.warnings:
            print(f"\n{'='*60}")
            print(f"WARNINGS ({len(self.warnings)})")
            print(f"{'='*60}")
            for i, warn in enumerate(self.warnings, 1):
                print(f"  {i}. {warn}")

        if self.info:
            print(f"\n{'='*60}")
            print(f"INFO ({len(self.info)})")
            print(f"{'='*60}")
            for i, info in enumerate(self.info, 1):
                print(f"  {i}. {info}")

        print(f"\n{'='*60}")
        if self.is_valid:
            print("VALIDATION PASSED")
        else:
            print("VALIDATION FAILED")
        print(f"{'='*60}\n")


class ProsographValidator:
    """Validates Prosograph documents."""

    def __init__(self, schema_path: Path | None = None):
        self.schema: dict | None = None
        if schema_path and schema_path.exists():
            with open(schema_path) as f:
                self.schema = json.load(f)

    def load_document(self, file_path: Path) -> dict:
        """Load a Prosograph document from YAML or JSON."""
        content = file_path.read_text(encoding='utf-8')

        if file_path.suffix in ('.yaml', '.yml'):
            if yaml is None:
                raise ImportError("PyYAML is required for YAML files: pip install pyyaml")
            return yaml.safe_load(content)
        else:
            return json.loads(content)

    def validate(self, doc: dict) -> ValidationResult:
        """Run all validations on a document."""
        result = ValidationResult()

        # Schema validation
        if self.schema and jsonschema:
            self._validate_schema(doc, result)
        elif not jsonschema:
            result.add_warning("jsonschema not installed - skipping schema validation")

        # Semantic validations
        self._validate_required_fields(doc, result)
        self._validate_temporal_constraints(doc, result)
        self._validate_id_uniqueness(doc, result)
        self._validate_references(doc, result)
        self._validate_ranges(doc, result)
        self._validate_tonal_requirements(doc, result)

        # Profile detection
        self._detect_profile(doc, result)

        return result

    def _validate_schema(self, doc: dict, result: ValidationResult) -> None:
        """Validate against JSON Schema."""
        try:
            validator = Draft202012Validator(self.schema)
            errors = list(validator.iter_errors(doc))
            for error in errors:
                path = " -> ".join(str(p) for p in error.absolute_path)
                result.add_error(f"Schema: {error.message} (at {path or 'root'})")
        except Exception as e:
            result.add_error(f"Schema validation error: {e}")

    def _validate_required_fields(self, doc: dict, result: ValidationResult) -> None:
        """Check required top-level fields."""
        if 'prosograph' not in doc:
            result.add_error("Missing required field: prosograph (version string)")
        elif not doc['prosograph'].startswith('1.'):
            result.add_error(f"Unsupported version: {doc['prosograph']} (expected 1.x)")

        if 'audio' not in doc:
            result.add_error("Missing required field: audio")
        else:
            audio = doc['audio']
            if 'uri' not in audio:
                result.add_error("Missing required field: audio.uri")
            if 'duration_s' not in audio:
                result.add_error("Missing required field: audio.duration_s")
            elif audio['duration_s'] <= 0:
                result.add_error("audio.duration_s must be > 0")

        if 'segments' not in doc:
            result.add_error("Missing required field: segments")

    def _validate_temporal_constraints(self, doc: dict, result: ValidationResult) -> None:
        """Validate all timing constraints."""
        duration = doc.get('audio', {}).get('duration_s', float('inf'))

        for seg in doc.get('segments', []):
            seg_id = seg.get('id', '<unknown>')
            t0 = seg.get('t0')
            t1 = seg.get('t1')

            if t0 is None:
                result.add_error(f"Segment {seg_id}: missing t0")
                continue
            if t1 is None:
                result.add_error(f"Segment {seg_id}: missing t1")
                continue

            if t0 < 0:
                result.add_error(f"Segment {seg_id}: t0 ({t0}) < 0")
            if t1 <= t0:
                result.add_error(f"Segment {seg_id}: t1 ({t1}) must be > t0 ({t0})")
            if t1 > duration:
                result.add_error(f"Segment {seg_id}: t1 ({t1}) > duration ({duration})")

            # Token timing
            for tok in seg.get('tokens', []):
                tok_id = tok.get('id', '<unknown>')
                tok_t0 = tok.get('t0')
                tok_t1 = tok.get('t1')

                if tok_t0 is None or tok_t1 is None:
                    result.add_error(f"Token {tok_id}: missing t0 or t1")
                    continue

                if tok_t0 < t0:
                    result.add_error(f"Token {tok_id}: t0 ({tok_t0}) < segment t0 ({t0})")
                if tok_t1 > t1:
                    result.add_error(f"Token {tok_id}: t1 ({tok_t1}) > segment t1 ({t1})")
                if tok_t1 <= tok_t0:
                    result.add_error(f"Token {tok_id}: t1 ({tok_t1}) must be > t0 ({tok_t0})")

    def _validate_id_uniqueness(self, doc: dict, result: ValidationResult) -> None:
        """Check that all IDs are unique within the document."""
        segment_ids = set()
        token_ids = set()

        for seg in doc.get('segments', []):
            seg_id = seg.get('id')
            if seg_id:
                if seg_id in segment_ids:
                    result.add_error(f"Duplicate segment ID: {seg_id}")
                segment_ids.add(seg_id)
            else:
                result.add_error("Segment missing required 'id' field")

            for tok in seg.get('tokens', []):
                tok_id = tok.get('id')
                if tok_id:
                    if tok_id in token_ids:
                        result.add_error(f"Duplicate token ID: {tok_id}")
                    token_ids.add(tok_id)
                else:
                    result.add_error("Token missing required 'id' field")

    def _validate_references(self, doc: dict, result: ValidationResult) -> None:
        """Validate all token references exist."""
        token_ids = set()
        for seg in doc.get('segments', []):
            for tok in seg.get('tokens', []):
                if 'id' in tok:
                    token_ids.add(tok['id'])

        # Check emphasis spans with token_ids
        for seg in doc.get('segments', []):
            delivery = seg.get('tracks', {}).get('delivery', {})
            for emphasis in delivery.get('emphasis', []):
                span = emphasis.get('span')
                if isinstance(span, dict) and 'token_ids' in span:
                    for ref_id in span['token_ids']:
                        if ref_id not in token_ids:
                            result.add_error(f"Emphasis references non-existent token: {ref_id}")

    def _validate_ranges(self, doc: dict, result: ValidationResult) -> None:
        """Validate all [0,1] and [-1,1] ranges."""

        def check_unit(value: Any, path: str) -> None:
            if value is not None and (value < 0 or value > 1):
                result.add_error(f"{path}: value {value} not in [0,1]")

        def check_signed_unit(value: Any, path: str) -> None:
            if value is not None and (value < -1 or value > 1):
                result.add_error(f"{path}: value {value} not in [-1,1]")

        def check_emotion(emotion: dict, path: str) -> None:
            vad = emotion.get('vad', {})
            check_signed_unit(vad.get('valence'), f"{path}.vad.valence")
            check_unit(vad.get('arousal'), f"{path}.vad.arousal")
            check_unit(vad.get('dominance'), f"{path}.vad.dominance")
            check_unit(emotion.get('confidence'), f"{path}.confidence")

        def check_voice_quality(vq: dict, path: str) -> None:
            for key in ['creak', 'breathiness', 'nasal', 'tension', 'smile']:
                check_unit(vq.get(key), f"{path}.{key}")

        # Check defaults
        defaults_style = doc.get('defaults', {}).get('style', {})
        if 'emotion' in defaults_style:
            check_emotion(defaults_style['emotion'], 'defaults.style.emotion')
        if 'voice_quality' in defaults_style:
            check_voice_quality(defaults_style['voice_quality'], 'defaults.style.voice_quality')

        # Check segments
        for i, seg in enumerate(doc.get('segments', [])):
            seg_id = seg.get('id', f'segment[{i}]')
            tracks = seg.get('tracks', {})

            if 'emotion' in tracks:
                check_emotion(tracks['emotion'], f"{seg_id}.tracks.emotion")
            if 'voice_quality' in tracks:
                check_voice_quality(tracks['voice_quality'], f"{seg_id}.tracks.voice_quality")
            if 'delivery' in tracks:
                check_unit(tracks['delivery'].get('clarity'), f"{seg_id}.tracks.delivery.clarity")

            # Check tokens
            for j, tok in enumerate(seg.get('tokens', [])):
                tok_id = tok.get('id', f'token[{j}]')
                tok_tracks = tok.get('tracks', {})

                if 'emotion' in tok_tracks:
                    check_emotion(tok_tracks['emotion'], f"{tok_id}.tracks.emotion")
                if 'voice_quality' in tok_tracks:
                    check_voice_quality(tok_tracks['voice_quality'], f"{tok_id}.tracks.voice_quality")
                if 'tone' in tok_tracks:
                    check_unit(tok_tracks['tone'].get('confidence'), f"{tok_id}.tracks.tone.confidence")

    def _validate_tonal_requirements(self, doc: dict, result: ValidationResult) -> None:
        """Check tonal language requirements."""
        # Get language from defaults or per-segment
        default_lang = doc.get('defaults', {}).get('language', '')
        tonal_langs = {'th', 'zh', 'vi', 'yue', 'cmn'}  # Thai, Chinese, Vietnamese, Cantonese, Mandarin

        for seg in doc.get('segments', []):
            seg_id = seg.get('id', '<unknown>')
            lang = seg.get('language', default_lang)
            lang_prefix = lang.split('-')[0].lower() if lang else ''

            if lang_prefix in tonal_langs:
                tone = seg.get('tracks', {}).get('tone', {})
                if 'system' not in tone:
                    result.add_warning(
                        f"Segment {seg_id}: tonal language ({lang}) but no tone.system declared"
                    )

                # Check tokens for lexical tone
                for tok in seg.get('tokens', []):
                    tok_id = tok.get('id', '<unknown>')
                    kind = tok.get('kind', 'word')
                    if kind in ('word', 'morpheme', 'char'):
                        tok_tone = tok.get('tracks', {}).get('tone', {})
                        if 'lexical' not in tok_tone:
                            result.add_warning(
                                f"Token {tok_id}: tonal language but no tone.lexical"
                            )

    def _detect_profile(self, doc: dict, result: ValidationResult) -> None:
        """Detect which compliance profile the document satisfies."""
        has_expressive = False
        has_tonal = False
        tonal_langs = {'th', 'zh', 'vi', 'yue', 'cmn'}

        default_lang = doc.get('defaults', {}).get('language', '')

        for seg in doc.get('segments', []):
            tracks = seg.get('tracks', {})

            # Check for expressive tracks
            if any(k in tracks for k in ['emotion', 'prosody', 'delivery', 'voice_quality']):
                has_expressive = True

            # Check for tonal
            lang = seg.get('language', default_lang)
            lang_prefix = lang.split('-')[0].lower() if lang else ''

            if lang_prefix in tonal_langs:
                if 'tone' in tracks and 'system' in tracks.get('tone', {}):
                    has_tonal = True

        # Determine profile
        if has_tonal and has_expressive:
            result.profile = "PG-Tonal (includes PG-Expressive, PG-Core)"
        elif has_expressive:
            result.profile = "PG-Expressive (includes PG-Core)"
        else:
            result.profile = "PG-Core"

        # Check declared profile
        declared = doc.get('meta', {}).get('profile')
        if declared:
            result.add_info(f"Declared profile: {declared}")


def main():
    parser = argparse.ArgumentParser(
        description='Validate Prosograph documents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s document.prosograph.yaml
    %(prog)s document.prosograph.json
    %(prog)s --schema ../schema/prosograph-1.0.json document.yaml
        """
    )
    parser.add_argument('file', type=Path, help='Prosograph document to validate')
    parser.add_argument(
        '--schema', '-s',
        type=Path,
        help='Path to JSON schema (default: ../schema/prosograph-1.0.json)'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Only print errors'
    )
    parser.add_argument(
        '--json', '-j',
        action='store_true',
        help='Output results as JSON'
    )

    args = parser.parse_args()

    if not args.file.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    # Find schema
    schema_path = args.schema
    if not schema_path:
        # Try relative to this script
        script_dir = Path(__file__).parent
        schema_path = script_dir.parent / 'schema' / 'prosograph-1.0.json'

    if not schema_path.exists():
        print(f"Warning: Schema not found at {schema_path}", file=sys.stderr)
        schema_path = None

    try:
        validator = ProsographValidator(schema_path)
        doc = validator.load_document(args.file)
        result = validator.validate(doc)

        if args.json:
            output = {
                'valid': result.is_valid,
                'profile': result.profile,
                'errors': result.errors,
                'warnings': result.warnings,
                'info': result.info
            }
            print(json.dumps(output, indent=2))
        else:
            if not args.quiet or not result.is_valid:
                print(f"\nValidating: {args.file}")
                result.print_report()

        sys.exit(0 if result.is_valid else 1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
