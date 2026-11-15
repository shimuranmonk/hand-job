import copy
import unittest
import mido

from playability import ReviewConfig, review_notes, tick_clock


def note(i, pitch, hand='RIGHT', tick=0, duration=100, seconds=None):
    return dict(id=str(i), pitch=pitch, hand=hand, start_tick=tick,
                duration_ticks=duration, start_seconds=tick/1000 if seconds is None else seconds)


class PlayabilityTests(unittest.TestCase):
    def kinds(self, notes, config=None):
        return {f['kind'] for f in review_notes(notes, config)['flags']}

    def test_span_requires_overlap_and_respects_release_boundary(self):
        for start, expected in [(99, True), (100, False), (101, False)]:
            self.assertEqual('simultaneous_span' in self.kinds([
                note(0, 36), note(1, 72, tick=start)]), expected)

    def test_low_right_alone_is_valid_and_zero_duration_does_not_overlap(self):
        self.assertFalse(self.kinds([note(0, 24)]))
        self.assertFalse(self.kinds([note(0, 24, duration=0), note(1, 80)]))

    def test_whole_chords_are_checked_independently_of_tied_event_order(self):
        # Interleaved broad ranges do not constitute an isolated crossing.
        notes = [note(0, 60, 'LEFT'), note(1, 36), note(2, 40, 'LEFT'), note(3, 64)]
        self.assertNotIn('isolated_crossing', self.kinds(notes))
        self.assertEqual(self.kinds(notes), self.kinds(list(reversed(notes))))

    def test_ordinary_chords_slow_crossings_and_long_rests(self):
        self.assertFalse(self.kinds([note(0,60), note(1,64), note(2,67)]))
        self.assertFalse(self.kinds([note(0,24), note(1,84,tick=5000)]))
        notes = [note(0,36), note(1,60,'LEFT')]
        self.assertNotIn('isolated_crossing', self.kinds(notes, ReviewConfig(crossing_semitones=25)))

    def test_crossing_requires_simultaneity_and_is_advisory(self):
        notes = [note(0, 36), note(1, 60, 'LEFT')]
        original = copy.deepcopy(notes)
        self.assertIn('isolated_crossing', self.kinds(notes))
        self.assertEqual(notes, original)
        notes[1]['start_tick'] = 100
        self.assertNotIn('isolated_crossing', self.kinds(notes))

    def test_jump_uses_seconds_and_nearest_chord_range(self):
        self.assertIn('abrupt_jump', self.kinds([note(0, 36), note(1, 72, tick=120)]))
        self.assertNotIn('abrupt_jump', self.kinds([note(0, 36), note(1, 72, tick=120, seconds=.5)]))
        self.assertNotIn('abrupt_jump', self.kinds([
            note(0, 36), note(1, 60), note(2, 61, tick=120)]))

    def test_continuity_and_configurable_thresholds(self):
        notes = [note(0, 60, tick=0), note(1, 61, 'LEFT', tick=100), note(2, 62, tick=200)]
        self.assertIn('continuity', self.kinds(notes))
        self.assertNotIn('continuity', self.kinds(notes, ReviewConfig(continuity_seconds=.1)))
        self.assertNotIn('simultaneous_span', self.kinds([note(0,36), note(1,60)], ReviewConfig(max_span=24)))

    def test_tempo_map_across_tracks_and_changes(self):
        source = mido.MidiFile(ticks_per_beat=480)
        source.tracks.append(mido.MidiTrack([
            mido.MetaMessage('set_tempo', tempo=1000000, time=480)]))
        clock = tick_clock(source)
        self.assertAlmostEqual(clock(240), .25)
        self.assertAlmostEqual(clock(480), .5)
        self.assertAlmostEqual(clock(960), 1.5)

    def test_bounded_deterministic_output(self):
        notes = [note(i, 24 if i%2 else 100, tick=i) for i in range(1000)]
        result = review_notes(notes, ReviewConfig(max_flags=2))
        self.assertEqual(len(result['flags']), 2)
        self.assertTrue(result['truncated'])
        self.assertEqual(result, review_notes(notes, ReviewConfig(max_flags=2)))

    def test_config_rejects_invalid_values(self):
        for value in (0, -1, float('nan'), True, '12'):
            with self.assertRaises(ValueError):
                ReviewConfig(max_span=value)
