"""Evaluate the unchanged checkpoint and a pitch baseline on reviewed hand labels."""
import argparse
import hashlib
import json
from pathlib import Path

import torch

from hand_service import note_id, parse_source
from inference import load_inference_model
from preprocess_midi_inference_data import PreprocessMIDIInferenceData as P


HANDS = ('LEFT', 'RIGHT')


def metrics(truth, predictions):
    if len(truth) != len(predictions) or any(v not in HANDS for v in [*truth, *predictions]):
        raise ValueError('Metrics require one valid hand prediction per reference note')
    confusion = {hand: {predicted: 0 for predicted in HANDS} for hand in HANDS}
    for actual, predicted in zip(truth, predictions):
        confusion[actual][predicted] += 1
    per_hand = {}
    for hand in HANDS:
        other = 'RIGHT' if hand == 'LEFT' else 'LEFT'
        tp, fp, fn = confusion[hand][hand], confusion[other][hand], confusion[hand][other]
        precision = tp/(tp+fp) if tp+fp else None
        recall = tp/(tp+fn) if tp+fn else None
        f1 = (2*tp/(2*tp+fp+fn)) if 2*tp+fp+fn else None
        per_hand[hand] = dict(precision=precision, recall=recall, f1=f1, support=tp+fn)
    return dict(note_count=len(truth),
                accuracy=sum(confusion[h][h] for h in HANDS)/len(truth) if truth else None,
                confusion_matrix=confusion, per_hand=per_hand)


def _json(path):
    def unique_pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f'Duplicate JSON key: {key}')
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique_pairs)


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def load_manifest(path):
    path = Path(path)
    manifest = _json(path)
    if manifest.get('version') != 1 or not isinstance(manifest.get('pieces'), list) or not manifest['pieces']:
        raise ValueError('Manifest version 1 needs a nonempty pieces list')
    pieces, identities, hashes, work_splits = [], set(), set(), {}
    for record in manifest['pieces']:
        if not all(isinstance(record.get(k), str) and record[k].strip() for k in ('id','work_id','midi','labels')):
            raise ValueError('Each piece needs id, work_id, midi, and labels')
        if record['id'] in identities:
            raise ValueError('Piece IDs must be unique')
        identities.add(record['id'])
        split = record.get('split')
        if split not in ('train','validation','test'):
            raise ValueError('Every piece needs a train, validation, or test split')
        previous = work_splits.setdefault(record['work_id'], split)
        if previous != split:
            raise ValueError('A work or arrangement group occurs in multiple splits')
        license_info = record.get('license', {})
        if (not isinstance(license_info, dict) or not license_info.get('identifier')
            or not license_info.get('source')):
            raise ValueError('Every piece needs license/status and source declarations')
        if license_info.get('reviewed') is not True and record.get('use_authorization') != 'user_authorized_local_evaluation':
            raise ValueError('Unreviewed rights require explicit user-authorized local evaluation')
        midi_path, labels_path = path.parent/record['midi'], path.parent/record['labels']
        data = midi_path.read_bytes()
        digest = _digest(data)
        if digest in hashes:
            raise ValueError('Duplicate MIDI content would contaminate or overweight evaluation')
        hashes.add(digest)
        labels = _json(labels_path)
        if labels.get('midi_sha256') != digest:
            raise ValueError('Reference labels do not match the MIDI checksum')
        if labels.get('method') not in ('manual_hand_review', 'user_confirmed_track_mapping') or not labels.get('reviewer'):
            raise ValueError('Reference labels require a named manual hand review; staff alone is insufficient')
        entries = labels.get('notes')
        if not isinstance(entries, list):
            raise ValueError('Label notes must be a list')
        expected = {}
        for label in entries:
            if (not isinstance(label, dict) or not isinstance(label.get('id'), str)
                or label.get('hand') not in HANDS or label['id'] in expected):
                raise ValueError('Reference note labels need unique IDs and LEFT/RIGHT values')
            expected[label['id']] = label['hand']
        source, pairs = parse_source(data)
        if set(expected) != {note_id(pair) for pair in pairs}:
            raise ValueError('Reference labels must cover exactly the notes in this MIDI')
        if labels['method'] == 'user_confirmed_track_mapping':
            mapping = labels.get('track_hands', {})
            if any(mapping.get(str(pair['note_on_note']['source_event'][0])) != expected[note_id(pair)] for pair in pairs):
                raise ValueError('Reference labels disagree with the confirmed source-track mapping')
        pieces.append(dict(record=record, source=source, pairs=pairs,
                           labels=expected, midi_sha256=digest,
                           labels_sha256=_digest(labels_path.read_bytes()),
                           reviewer=labels['reviewer'], label_method=labels['method']))
    return pieces


def evaluate_manifest(manifest_path, model, split='test', pitch_threshold=60):
    if split not in ('validation','test') or not 0 <= pitch_threshold <= 128:
        raise ValueError('Evaluate validation/test only, with a pitch threshold from 0 to 128')
    pieces = load_manifest(manifest_path)
    selected = [p for p in pieces if p['record']['split'] == split]
    if not selected:
        raise ValueError(f'No pieces belong to the {split} split')
    all_truth, all_model, all_baseline, reports = [], [], [], []
    with torch.inference_mode():
        for piece in selected:
            predicted = P.get_handedness_from_all_notes(model=model, source_midi=piece['source'])
            ids = [note_id(pair) for pair in piece['pairs']]
            if [note_id(pair) for pair in predicted] != ids:
                raise ValueError('Model inference lost or reordered source note identities')
            truth = [piece['labels'][identity] for identity in ids]
            guesses = [pair['hand'] for pair in predicted]
            baseline = ['LEFT' if p['note_on_note']['note'] < pitch_threshold else 'RIGHT' for p in piece['pairs']]
            reports.append(dict(id=piece['record']['id'], work_id=piece['record']['work_id'],
                                midi_sha256=piece['midi_sha256'], labels_sha256=piece['labels_sha256'],
                                reviewer=piece['reviewer'], license_declaration=piece['record']['license'],
                                label_method=piece['label_method'],
                                use_authorization=piece['record'].get('use_authorization','reviewed_rights'),
                                model=metrics(truth, guesses), pitch_baseline=metrics(truth, baseline)))
            all_truth.extend(truth); all_model.extend(guesses); all_baseline.extend(baseline)
    return dict(version=1, split=split, piece_count=len(reports), pitch_threshold=pitch_threshold,
                pieces=reports, aggregate=dict(model=metrics(all_truth, all_model),
                                               pitch_baseline=metrics(all_truth, all_baseline)),
                limitations=[
                    'Declared label and license reviews are supplied by the corpus owner, not independently certified here.',
                    'User-authorized local evaluation does not establish redistribution or training rights.',
                    'The original checkpoint training corpus/provenance is unknown; overlap with it is not ruled out.',
                    'Original inference sign mapping and feature normalization are retained; no model change is evaluated.',
                    'Null metrics indicate an undefined denominator; empty data is not a perfect score.',
                ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest')
    parser.add_argument('checkpoint')
    parser.add_argument('output')
    parser.add_argument('--config')
    parser.add_argument('--split', choices=['validation','test'], default='test')
    parser.add_argument('--pitch-threshold', type=int, default=60)
    args = parser.parse_args()
    try:
        model = load_inference_model(args.checkpoint, args.config)
        report = evaluate_manifest(args.manifest, model, args.split, args.pitch_threshold)
        report['checkpoint_sha256'] = _digest(Path(args.checkpoint).read_bytes())
        report['manifest_sha256'] = _digest(Path(args.manifest).read_bytes())
        config = Path(args.config) if args.config else Path(__file__).resolve().parent/'example/trains.example.json'
        report['config_sha256'] = _digest(config.read_bytes())
        report['torch_version'] = torch.__version__
        report['hand_label_convention'] = P.HAND_LABEL_CONVENTION
        report['code_sha256'] = {name: _digest((Path(__file__).resolve().parent/name).read_bytes())
                                 for name in ('inference.py','preprocess_midi_inference_data.py','midi_engine.py')}
        output = Path(args.output).resolve()
        if output in {Path(args.manifest).resolve(), Path(args.checkpoint).resolve(), config.resolve()}:
            raise ValueError('Evaluation output must not overwrite an input artifact')
        # Also protect every corpus file referenced by the manifest.
        manifest = _json(args.manifest)
        inputs = { (Path(args.manifest).parent / p[k]).resolve() for p in manifest['pieces'] for k in ('midi','labels') }
        if output in inputs:
            raise ValueError('Evaluation output must not overwrite corpus data')
        output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, EOFError) as error:
        parser.exit(2, f'Error: {error}\n')


if __name__ == '__main__':
    main()
