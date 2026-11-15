from collections import defaultdict, deque

import torch
import mido
from mido import MidiTrack, MidiFile, Message
from preprocess_data_lstm_helpers import PreprocessDataLSTMHelpers
from utils import Utils

class PreprocessMIDIInferenceData():
    @staticmethod
    def midifile_to_dict(mid):
        '''Pull out midi messages and specifically get note_on and note_off messages'''
        notes = []
        other_messages = []
        time_so_far = 0
        for msg in mido.merge_tracks(mid.tracks):
            msg_dict = vars(msg).copy()
            time_so_far += msg_dict["time"]
            
            print(time_so_far)
            if (msg_dict["type"] == "note_on" or msg_dict["type"] == "note_off"):
                note = {
                    "channel": msg_dict["channel"],
                    "type": msg_dict["type"],
                    "note": msg_dict["note"],
                    "velocity": msg_dict["velocity"],
                    "time": msg_dict["time"],
                    "time_so_far": time_so_far
                }
                notes.append(note)
            else:
                other_messages.append({
                    "time_so_far": time_so_far,
                    "message": msg_dict
                })
        return notes, other_messages

    @staticmethod
    def normalize_all_notes(all_notes):
        '''Normalize the inputted midi notes (already combined on/off)'''
        normalizers = PreprocessDataLSTMHelpers.get_all_normalizers()
        for note_datum in all_notes:
            input_data = note_datum["input_data"]
            for feature_index, feature_datum in enumerate(input_data):
                normalizers[feature_index] = normalizers[feature_index].partial_fit([[feature_datum]])
        
        normalized_input = [
            {
                "note_on_note": note_datum["note_on_note"],
                "note_off_note": note_datum["note_off_note"],
                "input_data": note_datum["input_data"],
                "normalized_input_data": PreprocessDataLSTMHelpers.normalize_input_features(note_datum["input_data"], normalizers)
            }
            for note_datum in all_notes
        ]

        return normalized_input

    @staticmethod
    def get_on_off_note_pairs(notes):
        """Pair channel/pitch onsets and releases in FIFO order; reject broken streams."""
        active = defaultdict(deque)
        pairs = []
        previous_tick = -1
        for index, event in enumerate(notes):
            tick = event["time_so_far"]
            if tick < previous_tick:
                raise ValueError("Note events must be ordered by absolute tick")
            previous_tick = tick
            key = (event["channel"], event["note"])
            if event["type"] == "note_on" and event["velocity"] > 0:
                active[key].append((index, event))
            elif event["type"] == "note_off" or (
                event["type"] == "note_on" and event["velocity"] == 0
            ):
                if not active[key]:
                    raise ValueError(f"Unmatched note release at tick {tick}, channel/pitch {key}")
                onset_index, onset = active[key].popleft()
                pairs.append((onset_index, {
                    "note_on_note": onset,
                    "note_off_note": event,
                    "input_data": [tick - onset["time_so_far"], False,
                                   onset["note"], onset["time_so_far"]],
                }))
            else:
                raise ValueError(f"Unsupported note event type: {event['type']}")
        if any(active.values()):
            raise ValueError("Unmatched note onset(s): MIDI contains notes without releases")
        return [pair for _, pair in sorted(pairs, key=lambda item: item[0])]

    @staticmethod
    def combine_on_off_notes(notes):
        '''From the dictionaries { note_on_notes: x, note_off_note: y... } pull them out and flatten into an array'''
        all_notes_flat = []
        for full_note_datum in notes:
            note_on = full_note_datum["note_on_note"]
            note_off = full_note_datum["note_off_note"]
            
            all_notes_flat.append(note_on)
            all_notes_flat.append(note_off)

        return all_notes_flat
    
    @staticmethod
    def get_midi_messages_and_fix_deltas(time_sorted_notes):
        '''After the messages have been sorted into absolute time,
        we need to fix the deltas between them as they may have shifted
        in the process of splitting the notes into two tracks (left/right hand tracks)'''
        last_time_so_far = 0
        midi_messages = []
        for note in time_sorted_notes:
            delta = note["time_so_far"] - last_time_so_far
            
            midi_messages.append(
                Message(
                    note["type"],
                    note=note["note"],
                    velocity=note["velocity"],
                    time=delta
                )
            )

            last_time_so_far = note["time_so_far"]

        return midi_messages
    
    @staticmethod
    def organize_song_by_time(all_notes):
        '''The note dictionaries { hand: x, time_so_far: y... } have information
        for absolute time within the song. Split songs by the 'hand' property
        and sort by the 'time_so_far' property. Returns a tuple of left and right hand notes'''
        left_handed_notes = [note for note in all_notes if note["hand"] == "LEFT"]
        right_handed_notes = [note for note in all_notes if note["hand"] == "RIGHT"]

        left_time_sorted_notes = sorted(
            PreprocessMIDIInferenceData.combine_on_off_notes(left_handed_notes),
            key=lambda item: item["time_so_far"]
        )
        # Now that the notes are sorted, the deltas are incorrect. Fix them to be relative to each other.
        left_midi_messages = PreprocessMIDIInferenceData.get_midi_messages_and_fix_deltas(left_time_sorted_notes)
        right_time_sorted_notes = sorted(
            PreprocessMIDIInferenceData.combine_on_off_notes(right_handed_notes),
            key=lambda item: item["time_so_far"]
        )
        # Now that the notes are sorted, the deltas are incorrect. Fix them to be relative to each other.
        right_midi_messages = PreprocessMIDIInferenceData.get_midi_messages_and_fix_deltas(right_time_sorted_notes)

        return (
            right_midi_messages,
            left_midi_messages
        )
        
    @staticmethod
    def get_midi_file_with_handedness(all_notes):
        '''Takes in the note dictionaries for all notes and returns a mido MidiFile.'''
        outfile = MidiFile()
        right_hand_track = MidiTrack()
        left_hand_track = MidiTrack()

        (right_midi_messages, left_midi_messages) = PreprocessMIDIInferenceData.organize_song_by_time(all_notes)
        
        all_midi_messages_left = []
        for midi_message in left_midi_messages:
            left_hand_track.append(midi_message)
            all_midi_messages_left.append(midi_message)

        all_midi_messages_right = []
        for midi_message in right_midi_messages:
            right_hand_track.append(midi_message)
            all_midi_messages_right.append(midi_message)

        outfile.tracks.append(left_hand_track)
        outfile.tracks.append(right_hand_track)
        
        return outfile

    @staticmethod
    def run_inference_and_get_flat_results(model, notes_chunked_full, sequence_length):
        """Infer full chunks plus an optional short final chunk, preserving note order."""
        if not notes_chunked_full:
            return []

        # Copy the chunk containers so padding never changes caller-owned data.
        chunks = [list(chunk) for chunk in notes_chunked_full]
        note_count = sum(len(chunk) for chunk in chunks)
        padding_count = sequence_length - len(chunks[-1])
        if padding_count:
            # Preserve the previous-chunk context used by the original model.
            # A sole short chunk repeats its own notes until the batch is rectangular.
            padding_source = chunks[-2] if len(chunks) > 1 else list(chunks[-1])
            chunks[-1].extend(padding_source[i % len(padding_source)] for i in range(padding_count))

        result = model(torch.tensor(chunks, dtype=torch.float))
        # An explicit real-note count also handles full chunks (no [:-0] slice).
        return [item for sublist in result for item in sublist][:note_count]

    @staticmethod
    def get_handedness_from_all_notes(model=None, midi_input_filename=None):
        '''Get handedness information from a midi input filename,
        passed through a neural net LSTM model and returns an array of handedness.'''
        sequence_length = 16
        mid = mido.MidiFile(file=midi_input_filename)
        (notes, _other_messages) = PreprocessMIDIInferenceData.midifile_to_dict(mid)

        on_off_pairs_of_notes = PreprocessMIDIInferenceData.get_on_off_note_pairs(notes)
        notes_normalized = PreprocessMIDIInferenceData.normalize_all_notes(on_off_pairs_of_notes)
        notes_chunked = Utils.chunks([note["normalized_input_data"] for note in notes_normalized], sequence_length)
        notes_chunked_full = [chunk for chunk in notes_chunked]
        flat_result = PreprocessMIDIInferenceData.run_inference_and_get_flat_results(model, notes_chunked_full, sequence_length)

        all_hands = [
            ("RIGHT" if output <= 0 else "LEFT")
            for output in flat_result
        ]
        hands_and_notes = [
            {
                "note_on_note": on_off_pairs_of_notes[note_index]["note_on_note"],
                "note_off_note": on_off_pairs_of_notes[note_index]["note_off_note"],
                "input_data": on_off_pairs_of_notes[note_index]["input_data"],
                "hand": hand,
            }
            for (note_index, hand) in enumerate(all_hands)
        ]

        return hands_and_notes

    @staticmethod
    def get_left_right_hands_midifile(
        model,
        midi_input_filename
    ):
        '''Get handedness information from a midi input filename,
        passed through a neural net LSTM model and returns a mido MidiFile to be saved somewhere'''
        hands_and_notes = PreprocessMIDIInferenceData.get_handedness_from_all_notes(model=model, midi_input_filename=midi_input_filename)

        return PreprocessMIDIInferenceData.get_midi_file_with_handedness(hands_and_notes)
