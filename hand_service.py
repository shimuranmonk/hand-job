"""Stateless analyze/correct/export operations; user MIDI is not stored here."""
import io

import torch

from midi_engine import export_hands, read_midi, read_note_events
from midi_validation import MIDIIntegrityError
from preprocess_midi_inference_data import PreprocessMIDIInferenceData as P


class InvalidMIDIInput(ValueError):
    pass


def parse_source(data, max_notes=20000):
    if not data:
        raise InvalidMIDIInput('Choose a MIDI file first.')
    try:
        source = read_midi(io.BytesIO(data))
        notes, _ = read_note_events(source)
        pairs = P.get_on_off_note_pairs(notes)
    except MIDIIntegrityError:
        raise
    except (OSError, EOFError, ValueError, KeyError, IndexError, UnicodeError) as error:
        raise InvalidMIDIInput('This MIDI could not be read or contains unmatched note endings.') from error
    if len(pairs) > max_notes:
        raise InvalidMIDIInput(f'This local preview supports up to {max_notes:,} notes per file.')
    return source, pairs


def note_id(pair):
    track, event = pair['note_on_note']['source_event']
    return f'{track}:{event}'


def analyze_midi(data, model, max_notes=20000):
    source, _ = parse_source(data, max_notes)
    with torch.inference_mode():
        pairs = P.get_handedness_from_all_notes(model=model, source_midi=source)
    notes = []
    for pair in pairs:
        onset = pair['note_on_note']
        notes.append(dict(id=note_id(pair), pitch=onset['note'], channel=onset['channel'],
                          track=onset['source_event'][0], velocity=onset['velocity'],
                          start_tick=onset['time_so_far'], duration_ticks=pair['input_data'][0],
                          hand=pair['hand'], suggested_hand=pair['hand']))
    tracks = [dict(index=index, name=next((m.name for m in track if m.type == 'track_name'),
                                          f'Track {index+1}'))
              for index, track in enumerate(source.tracks)]
    return dict(notes=notes, note_count=len(notes), tracks=tracks,
                ticks_per_beat=source.ticks_per_beat,
                duration_ticks=max((sum(m.time for m in t) for t in source.tracks), default=0))


def corrected_export(data, assignments, max_notes=20000):
    source, pairs = parse_source(data, max_notes)
    expected = {note_id(pair) for pair in pairs}
    if not isinstance(assignments, dict) or set(assignments) != expected:
        raise InvalidMIDIInput('Hand choices must include every note from this MIDI, with no extra notes.')
    if any(hand not in ('LEFT', 'RIGHT') for hand in assignments.values()):
        raise InvalidMIDIInput('Every note must be assigned to the left or right hand.')
    for pair in pairs:
        pair['hand'] = assignments[note_id(pair)]
    exported = export_hands(source, pairs)
    output = io.BytesIO()
    exported.save(file=output)
    output.seek(0)
    return output
