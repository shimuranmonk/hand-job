"""Phase 0 diagnostic probes against unchanged prototype code; not a release suite.

Run from repository root: .audit-venv/Scripts/python tools/audit_baseline.py
Writes JSON evidence and a synthetic MIDI under docs/audit/.
"""
import contextlib
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'docs' / 'audit'
OUT.mkdir(parents=True, exist_ok=True)
results = {}

def probe(name, function):
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            results[name] = {'observed': function()}
    except Exception:
        results[name] = {'error': traceback.format_exc()}

import mido
import torch
from preprocess_midi_inference_data import PreprocessMIDIInferenceData as P
from preprocess_data_lstm_helpers import PreprocessDataLSTMHelpers as L
from lstm_audio import LSTMAudio

def event(kind, pitch=60, velocity=64, channel=0, tick=0):
    return dict(type=kind, note=pitch, velocity=velocity, channel=channel,
                time=0, time_so_far=tick)

def pairing():
    cases = {
        'matching_release_velocity': [event('note_on'), event('note_off', tick=120)],
        'different_release_velocity': [event('note_on'), event('note_off', velocity=0, tick=120)],
        'velocity_zero_note_on_off': [event('note_on'), event('note_on', velocity=0, tick=120)],
        'wrong_pitch_same_velocity': [event('note_on'), event('note_off', pitch=72, tick=120)],
        'wrong_channel_same_velocity': [event('note_on'), event('note_off', channel=1, tick=120)],
        'overlap_same_pitch': [event('note_on'), event('note_on', tick=30),
                               event('note_off', tick=60), event('note_off', tick=90)],
    }
    return {name: [{'on': p['note_on_note'], 'off': p['note_off_note']} for p in P.get_on_off_note_pairs(notes)]
            for name, notes in cases.items()}

class ZeroModel:
    def __call__(self, tensor):
        return torch.zeros((*tensor.shape[:2], 1))

def lengths():
    out = {}
    for n in (0, 1, 7, 8, 15, 16, 17, 31, 32, 33):
        notes = [[0., 0., 0., 0.] for _ in range(n)]
        chunks = [notes[i:i+16] for i in range(0, n, 16)]
        out[str(n)] = len(P.run_inference_and_get_flat_results(ZeroModel(), chunks, 16))
    return out

def preservation():
    mid = mido.MidiFile(ticks_per_beat=960)
    track = mido.MidiTrack([
        mido.MetaMessage('set_tempo', tempo=600000),
        mido.MetaMessage('time_signature', numerator=3, denominator=4),
        mido.Message('program_change', channel=3, program=5),
        mido.Message('control_change', channel=3, control=64, value=127),
        mido.Message('note_on', channel=3, note=60, velocity=64),
        mido.Message('note_off', channel=3, note=60, velocity=64, time=960),
        mido.MetaMessage('set_tempo', tempo=400000),
    ])
    mid.tracks.append(track)
    mid.save(OUT / 'synthetic-preservation.mid')
    notes, other = P.midifile_to_dict(mid)
    pairs = P.get_on_off_note_pairs(notes)
    for p in pairs:
        p['hand'] = 'LEFT'
    exported = P.get_midi_file_with_handedness(pairs)
    exported.save(OUT / 'synthetic-export.mid')
    return {'input_ticks_per_beat': mid.ticks_per_beat,
            'output_ticks_per_beat': exported.ticks_per_beat,
            'collected_non_note_events': len(other),
            'input': [str(m) for m in mido.merge_tracks(mid.tracks)],
            'output': [str(m) for m in mido.merge_tracks(exported.tracks)]}

config = json.loads((ROOT / 'example/trains.example.json').read_text())[0]

def checkpoint():
    model = LSTMAudio(**config['lstm_model_params'], model_layers=config['model_layers'])
    # Only the restricted weights loader is used; never opt into arbitrary pickle loading.
    state = torch.load(ROOT / 'example/checkpoint.pth', map_location='cpu', weights_only=True)
    loaded = str(model.load_state_dict(state['model_state_dict']))
    model.eval()
    with torch.no_grad():
        shape = list(model(torch.zeros(1, 16, 4)).shape)
    return {'checkpoint_keys': list(state), 'epoch': state.get('epoch'),
            'load_state_dict': loaded, 'output_shape': shape,
            'module_keys': list(model.model),
            'lstm_execution_names': [name for _, name in model.model_layers_callbacks if 'lstm' in name],
            'state_dict_keys': list(state['model_state_dict'])}

def preprocessing():
    encode = L._PreprocessDataLSTMHelpers__preprocess_output_note_staff
    build = L._PreprocessDataLSTMHelpers__generate_note_datapoint
    sample = dict(note_duration=120, note_is_rest=False, note_midi_pitch=60,
                  note_time_position=0, note_staff='1')
    data, label = build(sample)
    inferred = P.normalize_all_notes([dict(note_on_note={}, note_off_note={}, input_data=[120, False, 60, 0])])[0]
    normalizers = L.get_all_normalizers()
    for features in ([120, -1, 48, 0], [240, -1, 72, 960]):
        for i, value in enumerate(features):
            normalizers[i].partial_fit([[value]])
    return {'staff_labels': {s: encode(s) for s in ('1', '2')},
            'inference_sign_mapping': {'positive': 'LEFT', 'zero_or_negative': 'RIGHT'},
            'training_raw': data, 'training_label': label,
            'training_fitted_transform': L.normalize_input_features(data, normalizers),
            'inference_refitted_transform': inferred['normalized_input_data']}

def cli(name, args):
    run = subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True, timeout=120)
    (OUT / (name + '.log')).write_text((run.stdout + '\nSTDERR\n' + run.stderr).replace(str(ROOT), '<repo>'), encoding='utf-8')
    return {'returncode': run.returncode, 'log': name + '.log'}

def stream_inference():
    from inference import inference
    def run(data):
        source = mido.MidiFile(file=io.BytesIO(data))
        original_onsets = sum(m.type == 'note_on' and m.velocity > 0 for t in source.tracks for m in t)
        raw, _ = P.midifile_to_dict(source)
        paired = len(P.get_on_off_note_pairs(raw))
        output = io.BytesIO()
        start = time.perf_counter()
        inference('example/checkpoint.pth', io.BytesIO(data), output)
        elapsed = time.perf_counter() - start
        output.seek(0)
        parsed = mido.MidiFile(file=output)
        return {'input_notes': original_onsets, 'paired_notes': paired,
                'exported_notes': sum(m.type == 'note_on' and m.velocity > 0 for t in parsed.tracks for m in t),
                'input_ppq': source.ticks_per_beat, 'export_ppq': parsed.ticks_per_beat,
                'seconds': elapsed, 'export_tracks': len(parsed.tracks)}
    observed = {'bundled_example': run((ROOT / 'example/simple_midi.example.mid').read_bytes())}
    for n in (1, 16, 17, 32):
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        for i in range(n):
            track.append(mido.Message('note_on', note=48+i % 24, velocity=64))
            track.append(mido.Message('note_off', note=48+i % 24, velocity=64, time=120))
        mid.tracks.append(track)
        data = io.BytesIO()
        mid.save(file=data)
        observed[str(n)] = run(data.getvalue())
    return observed

probe('pairing', pairing)
probe('sequence_output_counts', lengths)
probe('preservation', preservation)
probe('checkpoint', checkpoint)
probe('preprocessing', preprocessing)
probe('original_cli_example', lambda: cli('original-cli', ['inference.py', 'example/checkpoint.pth', 'example/simple_midi.example.mid', str(OUT / 'original-example-export.mid')]))
probe('original_cli_synthetic', lambda: cli('original-synthetic-cli', ['inference.py', 'example/checkpoint.pth', str(OUT / 'synthetic-preservation.mid'), str(OUT / 'original-synthetic-export.mid')]))
probe('server_import', lambda: cli('server-import', ['-c', 'import server; print(server.app.url_map)']))
probe('stream_inference', stream_inference)
results['environment'] = {'python': platform.python_version(), 'platform': platform.platform(),
    'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    'checkpoint_sha256': hashlib.sha256((ROOT / 'example/checkpoint.pth').read_bytes()).hexdigest(),
    'packages': {p: importlib.metadata.version(p) for p in ('torch', 'scikit-learn', 'mido', 'numpy', 'Flask', 'Flask-Limiter')}}
(OUT / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
print(json.dumps(results, indent=2))
