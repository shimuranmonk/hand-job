import io
import unittest

import mido

from hand_service import InvalidMIDIInput, parse_source
from piano_scope import PianoOnlyError, require_piano_only
from preprocess_midi_inference_data import PreprocessMIDIInferenceData as P


def piece(channel=0, program=None):
    midi=mido.MidiFile()
    track=mido.MidiTrack()
    if program is not None:
        track.append(mido.Message('program_change',channel=channel,program=program))
    track.extend([mido.Message('note_on',channel=channel,note=60,velocity=64),
                  mido.Message('note_off',channel=channel,note=60,time=480)])
    midi.tracks.append(track)
    return midi


class PianoScopeTests(unittest.TestCase):
    def test_unspecified_and_piano_family_programs_are_accepted(self):
        for program in (None,*range(6)):
            with self.subTest(program=program): require_piano_only(piece(program=program))

    def test_all_piano_tracks_belong_to_the_performance(self):
        source=piece()
        source.tracks.append(piece(channel=1,program=4).tracks[0])
        before=[list(t) for t in source.tracks]
        require_piano_only(source)
        self.assertEqual(source.tracks,before)

    def test_percussion_and_non_piano_programs_are_rejected(self):
        for source in (piece(channel=9),piece(program=6),piece(program=7),piece(program=48),piece(program=32)):
            with self.subTest(source=source),self.assertRaises(PianoOnlyError): require_piano_only(source)

    def test_program_changes_are_followed_across_tracks_in_time(self):
        source=piece()
        source.tracks.insert(0,mido.MidiTrack([mido.Message('program_change',program=48)]))
        with self.assertRaises(PianoOnlyError): require_piano_only(source)
        # A change after the last sounding onset does not invent an extra part.
        source.tracks[0][0].time=960
        require_piano_only(source)

    def test_names_do_not_override_instrument_events(self):
        source=piece(program=48)
        source.tracks[0].insert(0,mido.MetaMessage('track_name',name='Main Piano'))
        with self.assertRaises(PianoOnlyError): require_piano_only(source)

    def test_an_empty_conductor_track_is_allowed(self):
        source=mido.MidiFile()
        source.tracks.append(mido.MidiTrack([mido.MetaMessage('set_tempo',tempo=600000)]))
        require_piano_only(source)

    def test_service_and_core_reject_before_model_execution(self):
        source=piece(program=48)
        buffer=io.BytesIO();source.save(file=buffer)
        with self.assertRaisesRegex(InvalidMIDIInput,'piano-only'): parse_source(buffer.getvalue())
        class NeverRun:
            def __call__(self,data): raise AssertionError('Non-piano input reached the model')
        with self.assertRaises(PianoOnlyError): P.get_handedness_from_all_notes(NeverRun(),source_midi=source)


if __name__=='__main__': unittest.main()
