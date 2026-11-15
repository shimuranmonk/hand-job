"""Sequence completeness regressions; run with unittest from the repository root."""
import copy
import hashlib
import io
import json
from pathlib import Path
import unittest
from contextlib import redirect_stdout

import mido
import torch

from lstm_audio import LSTMAudio
from preprocess_midi_inference_data import PreprocessMIDIInferenceData as P

ROOT = Path(__file__).resolve().parents[1]
COUNTS = (0, 1, 7, 8, 15, 16, 17, 31, 32, 33)


class RecordingModel:
    def __init__(self):
        self.inputs = []

    def __call__(self, data):
        self.inputs.append(data.clone())
        # Unique note identity in feature 0 exposes dropped/reordered/duplicated output.
        return data[:, :, :1]


class SequenceCompletenessTests(unittest.TestCase):
    def test_each_real_note_retains_its_output_in_order_without_mutation(self):
        for n in COUNTS:
            with self.subTest(notes=n):
                notes = [[float(i), 0., 60., 0.] for i in range(n)]
                chunks = [notes[i:i+16] for i in range(0, n, 16)]
                before = copy.deepcopy(chunks)
                model = RecordingModel()
                outputs = P.run_inference_and_get_flat_results(model, chunks, 16)
                self.assertEqual([v.item() for v in outputs], list(range(n)))
                self.assertEqual(chunks, before)
                if n:
                    self.assertEqual(tuple(model.inputs[0].shape), ((n+15)//16, 16, 4))
                else:
                    self.assertEqual(model.inputs, [])

    def test_existing_multi_chunk_padding_context_is_preserved(self):
        notes = [[float(i)] * 4 for i in range(17)]
        model = RecordingModel()
        P.run_inference_and_get_flat_results(model, [notes[:16], notes[16:]], 16)
        self.assertEqual(model.inputs[0][-1, :, 0].tolist(), [16.] + list(map(float, range(15))))

    def test_generic_sequence_length(self):
        model = RecordingModel()
        result = P.run_inference_and_get_flat_results(model, [[[9.] * 4]], 4)
        self.assertEqual([v.item() for v in result], [9.])
        self.assertEqual(model.inputs[0].shape[1], 4)


class CheckpointIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        config = json.loads((ROOT/'example/trains.example.json').read_text())[0]
        cls.model = LSTMAudio(**config['lstm_model_params'], model_layers=config['model_layers'])
        state = torch.load(ROOT/'example/checkpoint.pth', map_location='cpu', weights_only=True)
        cls.model.load_state_dict(state['model_state_dict'], strict=True)
        cls.model.eval()

    def test_checkpoint_identity(self):
        self.assertEqual(hashlib.sha256((ROOT/'example/checkpoint.pth').read_bytes()).hexdigest(),
                         '638d1359db7ecafa252b0b3739fbb58595e25e4b05ed6ece4566d96dc1faac36')

    def test_synthetic_midi_inference_and_export_has_one_label_per_note(self):
        for n in COUNTS:
            with self.subTest(notes=n):
                mid = mido.MidiFile()
                track = mido.MidiTrack()
                for i in range(n):
                    # Equal release velocity intentionally isolates this regression
                    # from the known, separately scoped pairing defect.
                    track.append(mido.Message('note_on', note=48+i % 24, velocity=64))
                    track.append(mido.Message('note_off', note=48+i % 24, velocity=64, time=120))
                mid.tracks.append(track)
                source = io.BytesIO()
                mid.save(file=source)
                source.seek(0)
                with torch.no_grad(), redirect_stdout(io.StringIO()):
                    labels = P.get_handedness_from_all_notes(self.model, source)
                self.assertEqual(len(labels), n)
                self.assertTrue(all(note['hand'] in ('LEFT', 'RIGHT') for note in labels))
                self.assertEqual([note['note_on_note']['note'] for note in labels],
                                 [48+i % 24 for i in range(n)])
                exported = P.get_midi_file_with_handedness(labels)
                output = io.BytesIO()
                exported.save(file=output)
                output.seek(0)
                parsed = mido.MidiFile(file=output)
                self.assertEqual(sum(m.type == 'note_on' and m.velocity > 0
                                     for t in parsed.tracks for m in t), n)

    def test_full_sequence_outputs_match_direct_checkpoint_forward(self):
        data = torch.arange(32*4, dtype=torch.float).reshape(2,16,4) / 128
        with torch.no_grad():
            expected = self.model(data).reshape(-1,1)
            actual = torch.stack(P.run_inference_and_get_flat_results(self.model, data.tolist(), 16))
        torch.testing.assert_close(actual, expected, rtol=0, atol=0)


if __name__ == '__main__':
    unittest.main()
