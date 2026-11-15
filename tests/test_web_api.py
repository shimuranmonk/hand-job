import importlib.util
import io
import json
import unittest

import mido
import torch

from midi_validation import validate_preservation

WEB_AVAILABLE = (importlib.util.find_spec('flask') is not None and
                 importlib.util.find_spec('flask_limiter') is not None)
if WEB_AVAILABLE:
    from server import create_app


class PitchModel:
    def __call__(self, data):
        return data[:, :, 2:3]


def source_bytes(unsafe=False):
    source = mido.MidiFile(type=0, ticks_per_beat=960)
    events = [mido.MetaMessage('set_tempo', tempo=600000),
              mido.Message('program_change', program=5, channel=3),
              mido.Message('note_on', channel=3, note=48, velocity=64)]
    events += [mido.Message('note_on', channel=3, note=72, velocity=64),
               *([mido.Message('control_change', channel=3, control=64, value=127)] if unsafe else []),
               mido.Message('note_off', channel=3, note=48, velocity=0, time=0 if unsafe else 960),
               mido.Message('note_on', channel=3, note=72, velocity=0),
               mido.MetaMessage('end_of_track', time=120)]
    source.tracks.append(mido.MidiTrack(events))
    data = io.BytesIO()
    source.save(file=data)
    return data.getvalue()


@unittest.skipUnless(WEB_AVAILABLE, 'Install requirements/web.txt for web API checks')
class WebAPITests(unittest.TestCase):
    def setUp(self):
        self.loads = 0
        def loader(path):
            self.loads += 1
            return PitchModel()
        self.config = dict(TESTING=True, RATELIMIT_ENABLED=False, MODEL_LOADER=loader)
        self.app = create_app(self.config)
        self.client = self.app.test_client()
        self.data = source_bytes()

    def upload(self, path, **fields):
        return self.client.post(path, data=dict(midi=(io.BytesIO(self.data), 'input.mid'), **fields))

    def test_home_and_analyze_return_usable_note_data(self):
        self.assertTrue(self.app.jinja_env.auto_reload)
        self.assertIn(b'id="checkPlayability"', self.client.get('/').data)
        self.assertEqual(self.client.get('/').status_code, 200)
        response = self.upload('/api/analyze')
        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertEqual(result['note_count'], 2)
        self.assertEqual([n['pitch'] for n in result['notes']], [48,72])
        self.assertEqual(result['ticks_per_beat'], 960)
        self.assertEqual(len({n['id'] for n in result['notes']}), 2)
        self.assertEqual(self.loads, 1)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')

    def test_group_manual_corrections_control_export_without_model_reload(self):
        notes = self.upload('/api/analyze').get_json()['notes']
        for hand in ('LEFT', 'RIGHT'):
            choices = {n['id']: hand for n in notes}
            response = self.upload('/api/export', assignments=json.dumps(choices))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, 'audio/midi')
            exported = mido.MidiFile(file=io.BytesIO(response.data))
            validate_preservation(mido.MidiFile(file=io.BytesIO(self.data)), exported)
            note_tracks = [i for i,t in enumerate(exported.tracks) if any(m.type == 'note_on' and m.velocity for m in t)]
            self.assertEqual(note_tracks, [0 if hand == 'LEFT' else 1])
            response.close()
        self.assertEqual(self.loads, 1)

    def test_review_current_choices_without_loading_model_or_changing_export(self):
        notes = self.upload('/api/analyze').get_json()['notes']
        self.assertEqual(self.loads, 1)
        choices = {n['id']: 'RIGHT' for n in notes}
        response = self.upload('/api/review', assignments=json.dumps(choices))
        self.assertEqual(response.status_code, 200)
        self.assertIn('simultaneous_span', [f['kind'] for f in response.get_json()['flags']])
        self.assertEqual(self.loads, 1)
        choices[notes[0]['id']] = 'LEFT'
        result = self.upload('/api/review', assignments=json.dumps(choices)).get_json()
        self.assertEqual(result['flags'], [])
        self.assertEqual(self.upload('/api/review', assignments='{}').status_code, 400)
        exported = self.upload('/api/export', assignments=json.dumps({n['id']:'RIGHT' for n in notes}))
        self.assertEqual(exported.status_code, 200)
        validate_preservation(mido.MidiFile(file=io.BytesIO(self.data)), mido.MidiFile(file=io.BytesIO(exported.data)))
        exported.close()

    def test_note_level_corrections_route_individual_notes(self):
        notes = self.upload('/api/analyze').get_json()['notes']
        response = self.upload('/api/export', assignments=json.dumps({notes[0]['id']:'LEFT', notes[1]['id']:'RIGHT'}))
        self.assertEqual(response.status_code, 200)
        exported = mido.MidiFile(file=io.BytesIO(response.data))
        self.assertEqual([m.note for m in exported.tracks[0] if m.type == 'note_on' and m.velocity], [48])
        self.assertEqual([m.note for m in exported.tracks[1] if m.type == 'note_on' and m.velocity], [72])
        response.close()

    def test_invalid_requests_get_clear_errors_and_do_not_load_model(self):
        self.assertEqual(self.client.post('/api/analyze').status_code, 400)
        response = self.client.post('/api/analyze', data={'midi':(io.BytesIO(b'bad'), 'bad.mid')})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())
        for choices in ('not json', '{}', '[]', '{"foreign":"LEFT"}'):
            self.assertEqual(self.upload('/api/export', assignments=choices).status_code, 400)
        self.assertEqual(self.loads, 0)

    def test_unsafe_ordering_is_a_422_instead_of_a_changed_download(self):
        self.data = source_bytes(unsafe=True)
        notes = self.upload('/api/analyze').get_json()['notes']
        response = self.upload('/api/export', assignments=json.dumps({notes[0]['id']:'RIGHT',notes[1]['id']:'LEFT'}))
        self.assertEqual(response.status_code, 422)
        self.assertIn('safely', response.get_json()['error'])

    def test_upload_limit_is_applied_when_imported_not_just_when_run(self):
        app = create_app(dict(self.config, MAX_CONTENT_LENGTH=128))
        response = app.test_client().post('/midi-to-midi', data=b'x'*129)
        self.assertEqual(response.status_code, 413)
        self.assertIn('error', response.get_json())

    def test_note_limit_is_configurable(self):
        app = create_app(dict(self.config, MAX_MIDI_NOTES=1))
        response = app.test_client().post('/api/analyze', data={'midi':(io.BytesIO(self.data),'input.mid')})
        self.assertEqual(response.status_code, 400)
        self.assertIn('1 notes', response.get_json()['error'])

    def test_rate_limit_is_effective_and_model_is_cached(self):
        app = create_app(dict(self.config, RATELIMIT_ENABLED=True))
        client = app.test_client()
        codes = [client.post('/api/analyze', data={'midi':(io.BytesIO(self.data),'input.mid')}).status_code for _ in range(3)]
        self.assertEqual(codes, [200,200,429])
        self.assertEqual(self.loads, 1)

    def test_legacy_conversion_endpoint_still_preserves_midi(self):
        response = self.client.post('/midi-to-midi', data=self.data, content_type='audio/midi')
        self.assertEqual(response.status_code, 200)
        validate_preservation(mido.MidiFile(file=io.BytesIO(self.data)), mido.MidiFile(file=io.BytesIO(response.data)))
        response.close()

    def test_mixed_instrument_input_is_rejected_without_loading_model(self):
        source=mido.MidiFile(file=io.BytesIO(self.data))
        source.tracks[0].insert(2,mido.Message('program_change',channel=3,program=48))
        buffer=io.BytesIO();source.save(file=buffer);self.data=buffer.getvalue()
        response=self.upload('/api/analyze')
        self.assertEqual(response.status_code,400)
        self.assertIn('piano-only',response.get_json()['error'])
        self.assertEqual(self.loads,0)
        self.assertEqual(self.upload('/api/export',assignments='{}').status_code,400)
        self.assertEqual(self.client.post('/midi-to-midi',data=self.data).status_code,400)


if __name__ == '__main__':
    unittest.main()
