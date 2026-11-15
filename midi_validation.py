"""Compare decoded musical events while allowing documented track restructuring."""
from collections import defaultdict
import json

import mido


class MIDIIntegrityError(ValueError):
    """An export changed timing, event data, or relevant event ordering."""


def _payload(message):
    return json.dumps({k: v for k, v in message.dict().items() if k != 'time'},
                      sort_keys=True)


def _timeline(mid):
    if mid.type == 2:
        raise MIDIIntegrityError('Asynchronous MIDI type 2 needs a separate timeline policy')
    tick = 0
    events = []
    for message in mido.merge_tracks(mid.tracks):
        tick += message.time
        if message.type != 'end_of_track':
            events.append((tick, message))
    return events, tick


def _signature(events):
    """Distinct notes may commute at one tick; controls/meta/SysEx are barriers.

    Events for the same channel/pitch retain their order, including retriggers.
    This permits hand-track rearrangement of a chord without accepting a changed
    note-off/note-on order or moving controls across note events.
    """
    signature = []
    pending = defaultdict(list)
    current_tick = None

    def flush():
        if pending:
            signature.append((current_tick, 'notes', tuple(
                (key, tuple(values)) for key, values in sorted(pending.items()))))
            pending.clear()

    for tick, message in events:
        if tick != current_tick:
            flush()
            current_tick = tick
        if message.type in ('note_on', 'note_off'):
            pending[(message.channel, message.note)].append(_payload(message))
        else:
            flush()
            signature.append((tick, 'event', _payload(message)))
    flush()
    return signature


def validate_preservation(source, exported):
    """Raise on changed PPQ, decoded event data/order, or total end tick.

    Track count/layout and intermediate end-of-track markers may differ. Original
    track-name events remain part of the comparison; no metadata is silently exempt.
    Both inputs should be reparsed serialized files for a final export check.
    """
    if source.ticks_per_beat != exported.ticks_per_beat:
        raise MIDIIntegrityError('Export changed MIDI timing resolution')
    before, source_end = _timeline(source)
    after, export_end = _timeline(exported)
    if source_end != export_end:
        raise MIDIIntegrityError('Export changed the final absolute tick')
    if _signature(before) != _signature(after):
        raise MIDIIntegrityError('Export changed MIDI events or same-tick ordering')
    return {'event_count': len(before), 'end_tick': source_end,
            'ticks_per_beat': source.ticks_per_beat}
