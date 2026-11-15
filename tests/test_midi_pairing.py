import copy
import unittest

from preprocess_midi_inference_data import PreprocessMIDIInferenceData as P


def note(kind, tick, pitch=60, velocity=64, channel=0):
    return dict(type=kind, time_so_far=tick, time=0, note=pitch,
                velocity=velocity, channel=channel)


class PairingTests(unittest.TestCase):
    def test_release_velocity_is_independent_of_onset(self):
        events = [note('note_on', 0), note('note_off', 100, velocity=0)]
        result = P.get_on_off_note_pairs(events)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['input_data'], [100, False, 60, 0])

    def test_velocity_zero_is_only_a_release(self):
        events = [note('note_on', 0), note('note_on', 100, velocity=0)]
        self.assertEqual(len(P.get_on_off_note_pairs(events)), 1)

    def test_channel_and_pitch_both_identify_a_note(self):
        events = [note('note_on', 0), note('note_on', 5, channel=1),
                  note('note_on', 10, pitch=72), note('note_off', 20, pitch=72),
                  note('note_off', 30, channel=1), note('note_off', 40)]
        result = P.get_on_off_note_pairs(events)
        self.assertEqual([p['note_off_note']['time_so_far'] for p in result], [40, 30, 20])

    def test_overlapping_same_pitch_consumes_distinct_releases_fifo(self):
        events = [note('note_on', 0), note('note_on', 10),
                  note('note_off', 20), note('note_off', 30)]
        result = P.get_on_off_note_pairs(events)
        self.assertIs(result[0]['note_off_note'], events[2])
        self.assertIs(result[1]['note_off_note'], events[3])

    def test_same_tick_retrigger_preserves_input_order(self):
        events = [note('note_on', 0), note('note_off', 100),
                  note('note_on', 100), note('note_off', 200)]
        self.assertEqual([p['input_data'][0] for p in P.get_on_off_note_pairs(events)], [100, 100])

    def test_unmatched_or_out_of_order_events_are_explicit_errors(self):
        cases = [[note('note_off', 0)], [note('note_on', 0)],
                 [note('note_on', 0, velocity=0)],
                 [note('note_on', 0), note('note_off', 1, pitch=72)],
                 [note('note_on', 0), note('note_off', 1, channel=1)],
                 [note('note_on', 20), note('note_off', 10)]]
        for events in cases:
            with self.subTest(events=events), self.assertRaises(ValueError):
                P.get_on_off_note_pairs(events)

    def test_input_is_unchanged_and_empty_piece_is_valid(self):
        events = [note('note_on', 0), note('note_off', 100)]
        original = copy.deepcopy(events)
        P.get_on_off_note_pairs(events)
        self.assertEqual(events, original)
        self.assertEqual(P.get_on_off_note_pairs([]), [])


if __name__ == '__main__':
    unittest.main()
