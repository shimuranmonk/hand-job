"""Read-only input checks; derivative MIDI stays in an explicit local output folder."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import torch

from inference import load_inference_model
from midi_engine import export_hands, read_midi, read_note_events
from midi_validation import validate_preservation
from preprocess_midi_inference_data import PreprocessMIDIInferenceData as P


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_file(path, model, output, policies=('suggested', 'all_left', 'all_right', 'first_note_flipped')):
    before = digest(path)
    result = dict(name=path.name, source_sha256=before, size=path.stat().st_size)
    source = read_midi(path)
    events, others = read_note_events(source)
    pairs = P.get_on_off_note_pairs(events)
    result.update(type=source.type, ticks_per_beat=source.ticks_per_beat,
                  paired_notes=len(pairs), non_note_events=len(others), tracks=[])
    for index, track in enumerate(source.tracks):
        onsets = [m for m in track if m.type == 'note_on' and m.velocity > 0]
        result['tracks'].append(dict(index=index,
            name=next((m.name for m in track if m.type == 'track_name'), ''),
            note_count=len(onsets), channels=sorted({m.channel for m in onsets}),
            min_pitch=min((m.note for m in onsets), default=None),
            max_pitch=max((m.note for m in onsets), default=None)))
    with torch.inference_mode():
        predicted = P.get_handedness_from_all_notes(model=model, source_midi=source)
    result['predictions'] = len(predicted)
    result['suggested_left'] = sum(p['hand'] == 'LEFT' for p in predicted)
    result['suggested_right'] = sum(p['hand'] == 'RIGHT' for p in predicted)
    result['exports'] = {}
    for policy in policies:
        selected = [dict(pair) for pair in predicted]
        if policy in ('all_left','all_right'):
            for pair in selected:
                pair['hand'] = 'LEFT' if policy == 'all_left' else 'RIGHT'
        elif policy == 'first_note_flipped' and selected:
            selected[0]['hand'] = 'LEFT' if selected[0]['hand'] == 'RIGHT' else 'RIGHT'
        try:
            exported = export_hands(source, selected)
            output_path = output/f'{path.stem}-{policy}.mid'
            exported.save(output_path)
            checks = validate_preservation(source, read_midi(output_path))
            sidecar = dict(source_sha256=before, output_sha256=digest(output_path),
                           purpose='Manual Synthesia validation; not an official .synthesia metadata file',
                           tracks=exported.handjob_track_map)
            output_path.with_suffix('.handjob.json').write_text(json.dumps(sidecar,indent=2),encoding='utf-8')
            result['exports'][policy] = dict(passed=True, **checks, tracks=len(exported.tracks))
        except ValueError as error:
            result['exports'][policy] = dict(passed=False, error=str(error))
    result['original_unchanged'] = before == digest(path)
    if not result['original_unchanged']:
        raise RuntimeError('Source file unexpectedly changed')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder')
    parser.add_argument('output')
    parser.add_argument('--suggested-only',action='store_true',help='Prepare only suggested-hand files and manual test maps')
    args = parser.parse_args()
    folder, output = Path(args.folder).resolve(), Path(args.output).resolve()
    if output == folder or folder in output.parents:
        parser.error('Use an output directory outside the original MIDI folder')
    output.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in ('.mid','.midi'))
    if not files:
        parser.error('No MIDI files found')
    torch.set_num_threads(1)
    model = load_inference_model(ROOT/'example/checkpoint.pth')
    results = []
    for path in files:
        before = digest(path)
        try:
            policies = ('suggested',) if args.suggested_only else ('suggested','all_left','all_right','first_note_flipped')
            results.append(check_file(path, model, output, policies))
        except (OSError, ValueError, EOFError, KeyError) as error:
            results.append(dict(name=path.name, error=str(error), original_unchanged=before == digest(path)))
    report = dict(checkpoint_sha256=digest(ROOT/'example/checkpoint.pth'),
                  files=results, accuracy_measured=False,
                  note='Preservation-only run: reference labels are not read here, and no redistribution rights are assumed.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
