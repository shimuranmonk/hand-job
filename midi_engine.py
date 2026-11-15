"""Source-aware note identity and conservative, validated hand-track export."""
import io

import mido

from midi_validation import MIDIIntegrityError, validate_preservation


def read_midi(source):
    if hasattr(source, 'read'):
        return mido.MidiFile(file=source)
    return mido.MidiFile(filename=source)


def read_note_events(mid):
    if mid.type == 2 or mid.ticks_per_beat <= 0:
        raise MIDIIntegrityError('Only synchronous PPQ MIDI types 0 and 1 are supported')
    timeline = []
    for track_index, track in enumerate(mid.tracks):
        tick = 0
        for event_index, message in enumerate(track):
            if message.time < 0 or int(message.time) != message.time:
                raise MIDIIntegrityError('MIDI delta ticks must be nonnegative integers')
            tick += message.time
            timeline.append((tick, track_index, event_index, message))
    notes, other = [], []
    last_tick = 0
    for tick, track_index, event_index, message in sorted(timeline, key=lambda x: x[:3]):
        payload = message.dict()
        payload['time'] = tick - last_tick
        last_tick = tick
        identity = (track_index, event_index)
        if message.type in ('note_on', 'note_off'):
            notes.append(dict(payload, time_so_far=tick, source_event=identity))
        else:
            other.append(dict(time_so_far=tick, message=payload, source_event=identity))
    return notes, other


def export_hands(source, labeled_pairs):
    """Retain source tracks/events, separating right-hand notes per source track.

    The original track contains its non-note events and left notes. An adjacent
    right track is added only where needed. Track count/layout may change, but
    source events and ticks may not. Unsafe same-tick order changes are rejected.
    """
    source_notes, _ = read_note_events(source)
    expected = {tuple(event['source_event']) for event in source_notes}
    assignments = {}
    for pair in labeled_pairs:
        hand = pair['hand']
        if hand not in ('LEFT', 'RIGHT'):
            raise MIDIIntegrityError(f'Invalid hand assignment: {hand}')
        for name in ('note_on_note', 'note_off_note'):
            identity = tuple(pair[name].get('source_event', ()))
            if identity not in expected or identity in assignments:
                raise MIDIIntegrityError('Missing, duplicated, or foreign source note identity')
            assignments[identity] = hand
    if set(assignments) != expected:
        raise MIDIIntegrityError('Each source note event needs exactly one hand assignment')

    output = mido.MidiFile(type=1, ticks_per_beat=source.ticks_per_beat,
                           charset=source.charset)
    for track_index, track in enumerate(source.tracks):
        routed = {'LEFT': [], 'RIGHT': []}
        tick = 0
        for event_index, message in enumerate(track):
            tick += message.time
            if message.type == 'end_of_track':
                continue
            hand = assignments.get((track_index, event_index), 'LEFT')
            routed[hand].append((tick, message))
        for hand in ('LEFT', 'RIGHT'):
            if hand == 'RIGHT' and not routed[hand]:
                continue
            new_track = mido.MidiTrack()
            previous_tick = 0
            for absolute_tick, message in routed[hand]:
                new_track.append(message.copy(time=absolute_tick - previous_tick))
                previous_tick = absolute_tick
            new_track.append(mido.MetaMessage('end_of_track', time=tick - previous_tick))
            output.tracks.append(new_track)
    if not output.tracks:
        raise MIDIIntegrityError('MIDI must contain at least one track')
    if source.type == 0 and len(output.tracks) == 1:
        output.type = 0

    # Validate the decoded bytes, including serialization's event normalization.
    buffer = io.BytesIO()
    output.save(file=buffer)
    buffer.seek(0)
    verified = mido.MidiFile(file=buffer, charset=source.charset)
    validate_preservation(source, verified)
    return verified
