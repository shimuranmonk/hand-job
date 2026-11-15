import copy
import io
from pathlib import Path
import tempfile
import unittest

import mido
import torch

from midi_engine import export_hands, read_midi, read_note_events
from midi_validation import MIDIIntegrityError, validate_preservation
from preprocess_midi_inference_data import PreprocessMIDIInferenceData as P


def fixture():
    mid = mido.MidiFile(type=1, ticks_per_beat=960)
    mid.tracks.append(mido.MidiTrack([
        mido.MetaMessage('track_name', name='Conductor'),
        mido.MetaMessage('set_tempo', tempo=600000),
        mido.MetaMessage('time_signature', numerator=3, denominator=4),
        mido.MetaMessage('key_signature', key='Dm'),
        mido.MetaMessage('text', text='original event'),
        mido.Message('sysex', data=(1, 2, 3)),
        mido.MetaMessage('set_tempo', tempo=400000, time=960),
        mido.MetaMessage('end_of_track', time=480),
    ]))
    mid.tracks.append(mido.MidiTrack([
        mido.MetaMessage('track_name', name='Piano'),
        mido.Message('program_change', channel=3, program=5),
        mido.Message('control_change', channel=3, control=64, value=127),
        mido.Message('note_on', channel=3, note=48, velocity=90, time=120),
        mido.Message('note_on', channel=3, note=72, velocity=80),
        mido.Message('note_off', channel=3, note=48, velocity=7, time=480),
        mido.Message('note_on', channel=3, note=72, velocity=0),
        mido.Message('control_change', channel=3, control=64, value=0, time=120),
        mido.MetaMessage('end_of_track', time=720),
    ]))
    return mid


def label(source):
    notes, _ = read_note_events(source)
    pairs = P.get_on_off_note_pairs(notes)
    for pair in pairs:
        pair['hand'] = 'LEFT' if pair['note_on_note']['note'] < 60 else 'RIGHT'
    return pairs


class PitchModel:
    def __call__(self, data):
        return data[:, :, 2:3]


class ExportTests(unittest.TestCase):
    def test_source_aware_export_retains_events_and_original_tracks(self):
        source = fixture()
        before = copy.deepcopy(source)
        exported = export_hands(source, label(source))
        self.assertEqual(len(exported.tracks), 3)
        self.assertEqual(source.tracks, before.tracks)
        self.assertEqual(exported.ticks_per_beat, 960)
        self.assertEqual(exported.tracks[0][0].name, 'Conductor')
        self.assertEqual(exported.tracks[1][0].name, 'Piano')
        self.assertEqual([m.note for m in exported.tracks[1] if m.type == 'note_on' and m.velocity], [48])
        self.assertEqual([m.note for m in exported.tracks[2] if m.type == 'note_on' and m.velocity], [72])
        self.assertEqual([t['hand'] for t in exported.handjob_track_map], [None,'LEFT','RIGHT'])
        self.assertEqual([t['note_count'] for t in exported.handjob_track_map], [0,1,1])
        self.assertEqual(validate_preservation(source, exported)['end_tick'], 1440)

    def test_manual_labels_route_both_endpoints_of_selected_notes(self):
        source = fixture()
        pairs = label(source)
        for pair in pairs:
            pair['hand'] = 'LEFT'
        exported = export_hands(source, pairs)
        self.assertEqual(len(exported.tracks), 2)
        validate_preservation(source, exported)
        for pair in pairs:
            pair['hand'] = 'RIGHT'
        exported = export_hands(source, pairs)
        self.assertEqual(len(exported.tracks), 3)
        self.assertFalse(any(m.type in ('note_on', 'note_off') for m in exported.tracks[1]))
        self.assertEqual(sum(m.type in ('note_on', 'note_off') for m in exported.tracks[2]), 4)

    def test_missing_duplicate_foreign_or_invalid_labels_fail(self):
        source = fixture()
        pairs = label(source)
        invalid = copy.deepcopy(pairs)
        invalid[0]['hand'] = 'UNKNOWN'
        foreign = copy.deepcopy(pairs)
        foreign[0]['note_on_note']['source_event'] = (99,99)
        for data in (pairs[:1], pairs + pairs[:1], invalid, foreign):
            with self.subTest(data=data), self.assertRaises(MIDIIntegrityError):
                export_hands(source, data)

    def test_unsafe_same_tick_controller_reordering_is_rejected(self):
        source = mido.MidiFile()
        source.tracks.append(mido.MidiTrack([
            mido.Message('note_on', note=72),
            mido.Message('note_on', note=48),
            mido.Message('control_change', control=64, value=127),
            mido.Message('note_off', note=72),
            mido.Message('note_off', note=48),
        ]))
        with self.assertRaisesRegex(MIDIIntegrityError, 'ordering'):
            export_hands(source, label(source))

    def test_hand_switching_same_pitch_retriggers_use_additional_safe_tracks(self):
        source = mido.MidiFile(type=0)
        source.tracks.append(mido.MidiTrack([
            mido.Message('note_on', note=60), mido.Message('note_off', note=60, time=120),
            mido.Message('note_on', note=60), mido.Message('note_off', note=60, time=120),
            mido.Message('note_on', note=60), mido.Message('note_off', note=60, time=120)]))
        pairs = label(source)
        for pair, hand in zip(pairs, ('LEFT','RIGHT','LEFT')):
            pair['hand'] = hand
        exported = export_hands(source, pairs)
        self.assertEqual(len(exported.tracks),3)
        validate_preservation(source,exported)

    def test_uniform_right_hand_retains_same_tick_control_order(self):
        source = mido.MidiFile(type=0)
        source.tracks.append(mido.MidiTrack([
            mido.Message('note_on', note=72),
            mido.Message('control_change', control=64, value=127),
            mido.Message('note_off', note=72,time=120)]))
        validate_preservation(source,export_hands(source,label(source)))

    def test_mixed_hands_keep_aftertouch_after_a_right_note_release(self):
        source = mido.MidiFile(type=0)
        source.tracks.append(mido.MidiTrack([
            mido.Message('note_on', note=48), mido.Message('note_off',note=48,time=100),
            mido.Message('note_on', note=72), mido.Message('note_off',note=72,time=100),
            mido.Message('aftertouch', value=0)]))
        validate_preservation(source,export_hands(source,label(source)))

    def test_control_order_cycle_with_one_hand_can_share_a_track(self):
        source = mido.MidiFile(type=0)
        source.tracks.append(mido.MidiTrack([
            mido.Message('note_on', note=72),
            mido.Message('control_change', control=64,value=127),
            mido.Message('note_off', note=72)]))
        validate_preservation(source,export_hands(source,label(source)))

    def test_long_dependency_chain_does_not_recurse_or_change_notes(self):
        source = mido.MidiFile(type=0)
        track = mido.MidiTrack()
        for _ in range(1100):
            track.extend([mido.Message('note_on',note=60), mido.Message('note_off',note=60,time=1)])
        source.tracks.append(track)
        exported = export_hands(source,label(source))
        self.assertEqual(sum(m.type=='note_on' for t in exported.tracks for m in t),1100)
        validate_preservation(source,exported)

    def test_type_zero_becomes_type_one_only_when_split(self):
        source = mido.MidiFile(type=0)
        source.tracks.append(mido.MidiTrack([
            mido.Message('note_on', note=72), mido.Message('note_off', note=72, time=120)]))
        pairs = label(source)
        self.assertEqual(export_hands(source, pairs).type, 1)
        pairs[0]['hand'] = 'LEFT'
        self.assertEqual(export_hands(source, pairs).type, 0)

    def test_empty_piece_preserves_meta_and_tail_silence(self):
        source = mido.MidiFile(type=0)
        source.tracks.append(mido.MidiTrack([
            mido.MetaMessage('set_tempo', tempo=700000),
            mido.MetaMessage('end_of_track', time=2400)]))
        validate_preservation(source, export_hands(source, []))

    def test_filename_and_binary_stream_full_inference_preserve_source(self):
        source = fixture()
        buffer = io.BytesIO()
        source.save(file=buffer)
        buffer.seek(0)
        with torch.no_grad():
            exported = P.get_left_right_hands_midifile(PitchModel(), buffer)
        validate_preservation(source, exported)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'input.mid'
            source.save(path)
            self.assertEqual(read_midi(path).ticks_per_beat, 960)
            with torch.no_grad():
                exported = P.get_left_right_hands_midifile(PitchModel(), str(path))
            validate_preservation(source, exported)

    def test_asynchronous_smpte_and_bad_delta_inputs_are_rejected(self):
        for kind in ('type2', 'smpte', 'negative', 'fractional'):
            source = fixture()
            if kind == 'type2':
                source.type = 2
            elif kind == 'smpte':
                source.ticks_per_beat = -24
            else:
                source.tracks[1][3].time = -1 if kind == 'negative' else 0.5
            with self.subTest(kind=kind), self.assertRaises(MIDIIntegrityError):
                read_note_events(source)


if __name__ == '__main__':
    unittest.main()
