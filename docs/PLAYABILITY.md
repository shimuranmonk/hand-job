# HJ-PLAY-001: timing-aware assignment review

2026-11-15, Asia/Manila. User-authorized bounded implementation; advisory heuristics,
not a model repair or proof of physical impossibility.

## Diagnosis and missing evidence

The reported Visual Piano screenshot shows a low orange note and nearby higher blue
notes. The screenshot itself is not present in this checkout, and a repository-wide
filename search found no `Takap sa Dilim Midi - Gerard Chua-hands.mid`. Therefore no
original timestamps, pitches, overlap, track assignments, or precise reproduction
are claimed. The original exported MIDI and viewer URL/settings (including selected
tracks and color legend) are needed to reproduce the report precisely. A still image
alone cannot establish simultaneity.

Actual pipeline: `PreprocessMIDIInferenceData.get_handedness_from_all_notes` merges
source note events, pairs releases, normalizes legacy features, runs the original
LSTM in 16-note chunks, and decodes nonnegative output RIGHT / negative LEFT.
`hand_service.analyze_midi` describes these labels with source-event IDs; manual
choices are reapplied by ID before `midi_engine.export_hands`. Its ordering graph
preserves source tracks as groups of hand lanes: even lane LEFT, odd lane RIGHT.
Extra lanes can preserve tied note/controller ordering. There is no universal global
track 1/2 hand rule. `handjob_track_map` is an in-memory export map, not MIDI color
metadata. Serialized exports are independently checked for event preservation.

Current editor CSS uses gold LEFT and white RIGHT. Neither the classifier nor the
exporter assigns orange/blue colors. Standard MIDI does not define a hand-color
convention, and the exact external Visual Piano color/track mapping remains
unverified. Do not diagnose a label inversion from the colors alone. No external
viewer or Synthesia compatibility check was performed in this slice.

## Small patch and configuration

`playability.py` reviews labels without modifying notes, source MIDI, model features,
weights, or export choices. It is integrated after web inference and available for
current manual choices at `POST /api/review` (same MIDI multipart upload and complete
`assignments` JSON as export). No model load is needed for rechecking. Export is
never blocked by advisory flags; existing integrity validation still applies.

Trusted server configuration: pass `PLAYABILITY_CONFIG=ReviewConfig(...)` to
`create_app`. Standalone callers use `review_notes(notes, config)`. Defaults:

| Flag | Default rule |
| --- | --- |
| simultaneous_span | Same-hand key-down pitch range exceeds 12 semitones. |
| abrupt_jump | Consecutive same-hand onset groups separated by at most 0.15 seconds have disjoint pitch ranges more than 12 semitones apart. |
| isolated_crossing | Concurrent LEFT maximum exceeds RIGHT minimum by at least 7 semitones, and one extreme lies at least 7 semitones outside the other hand's whole range. |
| continuity | Three consecutive single-note onset groups alternate A/B/A hands within 0.25 seconds total and 5 semitones total range. |

All thresholds are configurable positive finite values; pitch/count parameters must
be integers. `max_flags` defaults to 500. Sweep and neighbor processing are
O(n log n), storage O(n + max_flags); output explicitly reports `truncated` when
additional distinct warnings exceed the cap. The existing web note limit is 20,000.
Flags include stable implicated note IDs and tick or elapsed-second evidence, plus
pitch distances where relevant. Only range extremes are implicated for span/crossing
flags, not every note of a chord. Reported count is warnings, not affected notes.

Overlap uses half-open key-down intervals [note_on, note_off): a release at the next
onset does not overlap, zero-duration notes do not contribute to span/crossing checks.
Tempo events from every track determine elapsed seconds, with source track/event
ordering resolving tied changes. Jump checks use onset intervals, not time since
release. Sustain pedal resonance is deliberately excluded from hand reach.

The editor displays reasons next to flagged notes and provides a flagged-note
filter. Detail tooltips include IDs and timing/distance evidence. After any manual
edit, restore or undo, old flags are cleared; “Check current hands” recalculates them.
The recheck is explicit to avoid stale results or repeated uploads while editing.
Individual/group correction, undo and faithful export retain their existing roles.

These defaults are review prompts, not approved ergonomic limits. Large hands,
arpeggiation, redistribution, ornaments, intentional crossings and voice handoffs
can trigger false positives. Broad overlapping chord ranges can hide a crossing.
There is no low-pitch-always-left rule, automatic relabeling, finger model, or full
biomechanical solver. No warnings does not certify playability or inference quality.

## Verification and next action

Synthetic tests cover exact release boundaries, overlap versus proximity, low RIGHT
notes, zero durations, whole tied chords, configurable spans/crossings, rapid versus
slow jumps, nearest chord ranges, continuity, tempo changes, nonmutation, output
caps and invalid configuration. Web tests verify rechecking manual choices without
model reload, invalid assignments, warning removal after correction, and continued
event-validated export despite warnings.

Original-checkpoint smoke check: bundled `example/simple_midi.example.mid`, 69 notes,
9 advisory flags, 626-byte export passed built-in serialized preservation validation.
A local synthetic 20,000-note run took 0.128 seconds before the whole-chord refinement,
returned 500 flags and `truncated=true`; this is a diagnostic, not a latency SLA.
Full unittest discovery, JavaScript syntax, Python compile and whitespace checks are
recorded in CONTINUATION.md. This Flask/Jinja/plain-JavaScript application has no
frontend build step. Template rendering is covered by the web tests. Interactive
browser and physical-device review of the new controls remains pending.

Next: obtain the original MIDI and exact Visual Piano mapping, inspect the flagged
note's source ID, ticks/seconds and overlapping notes, compare viewer track colors
with actual exported hand lanes, and let the user decide corrections. Keep musical
files and derived note data private/ignored. Do not tune the classifier from a still
image or silently replace legitimate crossings.
