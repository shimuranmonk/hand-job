"""Source-aware note identity and conservative, validated hand-track export."""
import io
from collections import defaultdict
import heapq

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


def _ordered_lanes(source, pairs, pair_for_event):
    """Assign complete notes and metadata to lanes without reversing tied events.

    Note nodes require a hand parity; barrier nodes may share either hand's lane.
    Equality cycles can share one lane only when all their notes have one hand.
    No graph recursion is used, so long passages do not hit Python's stack limit.
    """
    parity = {i: 0 if pair['hand'] == 'LEFT' else 1 for i, pair in enumerate(pairs)}
    event_node = dict(pair_for_event)
    before, after = defaultdict(set), defaultdict(set)

    def edge(first, second):
        if first is not None and first != second:
            after[first].add(second)
            before[second].add(first)

    for track_index, track in enumerate(source.tracks):
        tick, block_tick = 0, None
        pending, previous_note, last_barrier = set(), {}, None
        for event_index, message in enumerate(track):
            tick += message.time
            if tick != block_tick:
                pending, previous_note, last_barrier = set(), {}, None
                block_tick = tick
            if message.type == 'end_of_track':
                continue
            identity = (track_index, event_index)
            if identity in pair_for_event:
                node = pair_for_event[identity]
                edge(last_barrier, node)
                key = (message.channel, message.note)
                edge(previous_note.get(key), node)
                previous_note[key] = node
                pending.add(node)
            else:
                node = len(parity)
                parity[node] = None
                event_node[identity] = node
                edge(last_barrier, node)
                for predecessor in pending:
                    edge(predecessor, node)
                pending.clear()
                last_barrier = node

    # Kosaraju's two iterative traversals find nodes that must share a lane.
    visited, finish = set(), []
    for node in parity:
        if node in visited:
            continue
        visited.add(node)
        stack = [(node, iter(after[node]))]
        while stack:
            current, children = stack[-1]
            try:
                child = next(children)
                if child not in visited:
                    visited.add(child)
                    stack.append((child, iter(after[child])))
            except StopIteration:
                stack.pop()
                finish.append(current)
    component_of, components = {}, []
    for node in reversed(finish):
        if node in component_of:
            continue
        component = len(components)
        members, stack = [], [node]
        component_of[node] = component
        while stack:
            current = stack.pop()
            members.append(current)
            for predecessor in before[current]:
                if predecessor not in component_of:
                    component_of[predecessor] = component
                    stack.append(predecessor)
        components.append(members)
    required = {}
    for component, members in enumerate(components):
        hands = {parity[node] for node in members if parity[node] is not None}
        if len(hands) > 1:
            raise MIDIIntegrityError('Same-tick note/control ordering cannot be split safely by hand')
        required[component] = next(iter(hands), None)
    predecessors, followers = defaultdict(set), defaultdict(set)
    for first, targets in after.items():
        for second in targets:
            a, b = component_of[first], component_of[second]
            if a != b:
                predecessors[b].add(a)
                followers[a].add(b)
    remaining = {i: len(predecessors[i]) for i in range(len(components))}
    ready = [i for i, count in remaining.items() if count == 0]
    heapq.heapify(ready)
    ranks = {}
    while ready:
        component = heapq.heappop(ready)
        minimum = max((ranks[p] for p in predecessors[component]), default=0)
        hand = required[component]
        ranks[component] = minimum if hand is None or minimum % 2 == hand else minimum + 1
        for follower in sorted(followers[component]):
            remaining[follower] -= 1
            if remaining[follower] == 0:
                heapq.heappush(ready, follower)
    return {identity: ranks[component_of[node]] for identity, node in event_node.items()}


def export_hands(source, labeled_pairs):
    """Retain source tracks/events, separating right-hand notes per source track.

    Each source track remains a group of hand lanes. Extra lanes preserve tied
    note/control order without changing channels or ticks. Unsplittable hand
    assignments are rejected; the serialized result is independently validated.
    """
    source_notes, _ = read_note_events(source)
    expected = {tuple(event['source_event']) for event in source_notes}
    assignments = {}
    pair_for_event = {}
    for pair_index, pair in enumerate(labeled_pairs):
        hand = pair['hand']
        if hand not in ('LEFT', 'RIGHT'):
            raise MIDIIntegrityError(f'Invalid hand assignment: {hand}')
        for name in ('note_on_note', 'note_off_note'):
            identity = tuple(pair[name].get('source_event', ()))
            if identity not in expected or identity in assignments:
                raise MIDIIntegrityError('Missing, duplicated, or foreign source note identity')
            assignments[identity] = hand
            pair_for_event[identity] = pair_index
    if set(assignments) != expected:
        raise MIDIIntegrityError('Each source note event needs exactly one hand assignment')

    event_lanes = _ordered_lanes(source, labeled_pairs, pair_for_event)

    output = mido.MidiFile(type=1, ticks_per_beat=source.ticks_per_beat,
                           charset=source.charset)
    track_map = []
    for track_index, track in enumerate(source.tracks):
        routed = defaultdict(list)
        tick = 0
        for event_index, message in enumerate(track):
            tick += message.time
            if message.type == 'end_of_track':
                continue
            identity = (track_index, event_index)
            lane = event_lanes[identity]
            routed[lane].append((tick, message))
        for lane in sorted({0, *routed}):
            new_track = mido.MidiTrack()
            previous_tick = 0
            for absolute_tick, message in routed[lane]:
                new_track.append(message.copy(time=absolute_tick - previous_tick))
                previous_tick = absolute_tick
            new_track.append(mido.MetaMessage('end_of_track', time=tick - previous_tick))
            note_count = sum(message.type == 'note_on' and message.velocity > 0 for _, message in routed[lane])
            track_map.append(dict(output_track=len(output.tracks), source_track=track_index,
                                  hand=('LEFT' if lane % 2 == 0 else 'RIGHT') if note_count else None,
                                  note_count=note_count))
            output.tracks.append(new_track)
    if len(output.tracks) > 65535:
        raise MIDIIntegrityError('Hand splitting exceeds the MIDI track-count limit')
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
    verified.handjob_track_map = track_map
    return verified
