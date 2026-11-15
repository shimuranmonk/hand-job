import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import mido

from inference import inference, load_inference_model
from midi_validation import validate_preservation

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = ROOT/'example/checkpoint.pth'


def sample():
    source = mido.MidiFile(type=0, ticks_per_beat=960)
    source.tracks.append(mido.MidiTrack([
        mido.MetaMessage('set_tempo', tempo=700000),
        mido.Message('note_on', note=60, velocity=64),
        mido.Message('note_on', note=60, velocity=0, time=960),
        mido.MetaMessage('end_of_track', time=120)]))
    return source


class InferenceCLITests(unittest.TestCase):
    def test_binary_stream_function(self):
        source = sample()
        data, output = io.BytesIO(), io.BytesIO()
        source.save(file=data)
        data.seek(0)
        inference(CHECKPOINT, data, output)
        output.seek(0)
        validate_preservation(source, mido.MidiFile(file=output))

    def test_cli_runs_from_another_directory_with_core_dependencies_only(self):
        with tempfile.TemporaryDirectory() as folder:
            src, dst = Path(folder)/'source.mid', Path(folder)/'result.mid'
            sample().save(src)
            run = subprocess.run([sys.executable, str(ROOT/'inference.py'), str(CHECKPOINT), str(src), str(dst)],
                                 cwd=folder, capture_output=True, text=True, timeout=60)
            self.assertEqual(run.returncode, 0, run.stderr)
            validate_preservation(mido.MidiFile(src), mido.MidiFile(dst))

    def test_invalid_midi_returns_nonzero_and_creates_no_output(self):
        with tempfile.TemporaryDirectory() as folder:
            src, dst = Path(folder)/'broken.mid', Path(folder)/'result.mid'
            src.write_bytes(b'not midi')
            run = subprocess.run([sys.executable, str(ROOT/'inference.py'), str(CHECKPOINT), str(src), str(dst)],
                                 capture_output=True, text=True, timeout=60)
            self.assertEqual(run.returncode, 2)
            self.assertIn('Error:', run.stderr)
            self.assertFalse(dst.exists())

    def test_refuse_same_source_and_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'source.mid'
            sample().save(path)
            original = path.read_bytes()
            with self.assertRaisesRegex(ValueError, 'different output'):
                inference(CHECKPOINT, path, str(path))
            self.assertEqual(path.read_bytes(), original)

    def test_ambiguous_config_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'config.json'
            path.write_text(json.dumps([{},{}]))
            with self.assertRaisesRegex(ValueError, 'exactly one'):
                load_inference_model(CHECKPOINT, path)


if __name__ == '__main__':
    unittest.main()
