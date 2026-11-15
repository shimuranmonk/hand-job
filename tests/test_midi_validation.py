import copy
import unittest

import mido

from midi_validation import MIDIIntegrityError, validate_preservation


def midi(messages, ppq=960):
    result = mido.MidiFile(ticks_per_beat=ppq)
    result.tracks.append(mido.MidiTrack(messages))
    return result


class PreservationValidatorTests(unittest.TestCase):
    def setUp(self):
        self.source = midi([
            mido.MetaMessage('set_tempo', tempo=600000),
            mido.MetaMessage('text', text='preserve me'),
            mido.Message('program_change', channel=3, program=5),
            mido.Message('control_change', channel=3, control=64, value=127),
            mido.Message('sysex', data=(1,2,3)),
            mido.Message('note_on', channel=3, note=60, velocity=90),
            mido.Message('note_on', channel=3, note=64, velocity=80),
            mido.Message('note_off', channel=3, note=60, velocity=7, time=960),
            mido.Message('note_on', channel=3, note=64, velocity=0),
            mido.MetaMessage('end_of_track', time=120),
        ])

    def test_copy_passes_and_reports_total_time(self):
        result = validate_preservation(self.source, copy.deepcopy(self.source))
        self.assertEqual(result, {'event_count': 9, 'end_tick': 1080, 'ticks_per_beat': 960})

    def test_note_data_meta_controllers_and_ppq_changes_fail(self):
        for index, field, value in [(0,'tempo',500000), (1,'text','lost'),
                                    (2,'program',1), (3,'value',0),
                                    (5,'channel',0), (5,'note',61),
                                    (5,'velocity',1), (7,'time',959)]:
            with self.subTest(index=index, field=field):
                changed = copy.deepcopy(self.source)
                setattr(changed.tracks[0][index], field, value)
                with self.assertRaises(MIDIIntegrityError):
                    validate_preservation(self.source, changed)
        changed = copy.deepcopy(self.source)
        changed.ticks_per_beat = 480
        with self.assertRaises(MIDIIntegrityError):
            validate_preservation(self.source, changed)

    def test_removed_event_and_changed_tail_silence_fail(self):
        for index in (1,3,4,9):
            changed = copy.deepcopy(self.source)
            del changed.tracks[0][index]
            with self.subTest(index=index), self.assertRaises(MIDIIntegrityError):
                validate_preservation(self.source, changed)

    def test_independent_simultaneous_notes_may_reorder(self):
        changed = copy.deepcopy(self.source)
        changed.tracks[0][5], changed.tracks[0][6] = changed.tracks[0][6], changed.tracks[0][5]
        validate_preservation(self.source, changed)

    def test_controller_cannot_cross_a_note_at_the_same_tick(self):
        changed = copy.deepcopy(self.source)
        changed.tracks[0][3], changed.tracks[0][5] = changed.tracks[0][5], changed.tracks[0][3]
        with self.assertRaises(MIDIIntegrityError):
            validate_preservation(self.source, changed)

    def test_same_pitch_retrigger_order_is_not_commutative(self):
        source = midi([mido.Message('note_on', note=60), mido.Message('note_off', note=60)])
        changed = midi(list(reversed(source.tracks[0])))
        with self.assertRaises(MIDIIntegrityError):
            validate_preservation(source, changed)

    def test_asynchronous_type_two_is_rejected(self):
        self.source.type = 2
        with self.assertRaises(MIDIIntegrityError):
            validate_preservation(self.source, copy.deepcopy(self.source))


if __name__ == '__main__':
    unittest.main()
