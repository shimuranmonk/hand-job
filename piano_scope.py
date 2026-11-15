"""The MVP processes a piano performance, not a multi-instrument arrangement."""
import mido


class PianoOnlyError(ValueError):
    pass


def require_piano_only(source):
    """Check the active channel program at each sounding note onset.

    Programs 0–5 are accepted as acoustic/electric piano; an unspecified
    program defaults to 0. Channel 9 (human channel 10) is percussion. Track
    names are not used to guess instruments, and unused program changes do
    not cause rejection. No events are removed or rewritten.
    """
    programs = [0] * 16
    for message in mido.merge_tracks(source.tracks):
        if message.type == 'program_change':
            programs[message.channel] = message.program
        elif message.type == 'note_on' and message.velocity > 0:
            if message.channel == 9:
                raise PianoOnlyError('This MIDI contains percussion. Choose a piano-only MIDI file.')
            if programs[message.channel] not in range(6):
                raise PianoOnlyError('This MIDI contains non-piano parts. Choose a piano-only MIDI file.')
