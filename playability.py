"""Advisory timing-aware checks. Never modify labels or MIDI events."""
from bisect import bisect_right
from dataclasses import asdict, dataclass
import heapq
import math


@dataclass(frozen=True)
class ReviewConfig:
    max_span: int = 12
    jump_semitones: int = 12
    jump_seconds: float = 0.15
    crossing_semitones: int = 7
    continuity_semitones: int = 5
    continuity_seconds: float = 0.25
    max_flags: int = 500

    def __post_init__(self):
        for name, value in asdict(self).items():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f'{name} must be positive and finite')
            if name not in ('jump_seconds', 'continuity_seconds') and not isinstance(value, int):
                raise ValueError(f'{name} must be an integer')


def tick_clock(source):
    """Resolve tempo ties in the same track/event order as source extraction."""
    changes = []
    for ti, track in enumerate(source.tracks):
        tick = 0
        for ei, message in enumerate(track):
            tick += message.time
            if message.type == 'set_tempo':
                changes.append((tick, ti, ei, message.tempo))
    ticks, seconds, tempos = [0], [0.0], [500000]
    for tick, _, _, tempo in sorted(changes):
        elapsed = seconds[-1] + (tick-ticks[-1])*tempos[-1]/source.ticks_per_beat/1e6
        ticks.append(tick); seconds.append(elapsed); tempos.append(tempo)
    def at(tick):
        i = bisect_right(ticks, tick)-1
        return seconds[i] + (tick-ticks[i])*tempos[i]/source.ticks_per_beat/1e6
    return at


def review_notes(notes, config=None):
    """O(n log n) sweep and onset-neighbor checks, capped diagnostic output.

    Notes require stable id, pitch, hand, start_tick, duration_ticks and
    start_seconds. Overlap is key-down [on, off), not sustain-pedal sounding time.
    """
    c = config or ReviewConfig()
    flags, seen = [], set()
    truncated = False
    def flag(kind, members, **evidence):
        nonlocal truncated
        ids = sorted({n['id'] for n in members})
        key = (kind, tuple(ids))
        if key in seen:
            return
        if len(flags) >= c.max_flags:
            truncated = True
            return
        seen.add(key)
        flags.append(dict(kind=kind, note_ids=ids, **evidence))

    ordered = sorted(notes, key=lambda n: (n['start_tick'], n['id']))
    groups = {}
    for n in ordered:
        groups.setdefault(n['start_tick'], []).append(n)
    heaps = {h: ([], []) for h in ('LEFT', 'RIGHT')}
    serial = 0
    for tick, group in groups.items():
        for lo, hi in heaps.values():
            for heap in (lo, hi):
                while heap and heap[0][2]['start_tick']+heap[0][2]['duration_ticks'] <= tick:
                    heapq.heappop(heap)
        for n in group:
            if n['duration_ticks'] <= 0:
                continue
            lo, hi = heaps[n['hand']]
            heapq.heappush(lo, (n['pitch'], serial, n))
            heapq.heappush(hi, (-n['pitch'], serial, n))
            serial += 1
        for lo, hi in heaps.values():
            if lo and -hi[0][0]-lo[0][0] > c.max_span:
                flag('simultaneous_span', [lo[0][2], hi[0][2]], tick=tick,
                     semitones=-hi[0][0]-lo[0][0])
        left, right = heaps['LEFT'][1], heaps['RIGHT'][0]
        if left and right and -left[0][0]-right[0][0] >= c.crossing_semitones:
            # One hand's extreme lies beyond the other hand's entire pitch range.
            llo, rhi = heaps['LEFT'][0], heaps['RIGHT'][1]
            if llo[0][0]-right[0][0] >= c.crossing_semitones or -left[0][0]+rhi[0][0] >= c.crossing_semitones:
                flag('isolated_crossing', [left[0][2], right[0][2]], tick=tick,
                     semitones=-left[0][0]-right[0][0])

    previous = {}
    for group in groups.values():
        for hand in ('LEFT', 'RIGHT'):
            chord = [n for n in group if n['hand'] == hand]
            if not chord:
                continue
            low, high = min(chord, key=lambda n:n['pitch']), max(chord, key=lambda n:n['pitch'])
            if hand in previous:
                a, b = previous[hand]
                gap = low['start_seconds']-a['start_seconds']
                # Minimum travel between chord pitch ranges, not arbitrary note order.
                first, second = (b, low) if low['pitch'] > b['pitch'] else (a, high)
                distance = max(0, low['pitch']-b['pitch'], a['pitch']-high['pitch'])
                if 0 < gap <= c.jump_seconds and distance > c.jump_semitones:
                    flag('abrupt_jump', [first, second], seconds=gap, semitones=distance)
            previous[hand] = low, high
    singles = list(groups.values())
    for before, middle, after in zip(singles, singles[1:], singles[2:]):
        if len(before) == len(middle) == len(after) == 1:
            a, b, d = before[0], middle[0], after[0]
            if (a['hand'] == d['hand'] != b['hand'] and
                0 < d['start_seconds']-a['start_seconds'] <= c.continuity_seconds and
                max(a['pitch'],b['pitch'],d['pitch'])-min(a['pitch'],b['pitch'],d['pitch']) <= c.continuity_semitones):
                flag('continuity', [a,b,d], seconds=d['start_seconds']-a['start_seconds'])
    return dict(flags=flags, truncated=truncated, config=asdict(c))
