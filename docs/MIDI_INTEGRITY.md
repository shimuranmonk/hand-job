# MIDI integrity repairs

Scope: FR-01/FR-04, AC-01/AC-04, audit H-01/H-02. User authorized continued bounded project work on 2026-11-15 and selected preserving original tracks while splitting notes by hand. No model/feature changes or Synthesia compatibility claim.

## T-02: pairing — verified

Pair by (channel, pitch), independent of release velocity. Treat note_on velocity zero only as a release. Repeated overlapping notes use FIFO onset order and consume each release once; this is a deterministic interpretation where MIDI does not identify note instances. Return pairs in onset order, preserving references to original events.

Unmatched releases, dangling onsets, and descending absolute tick order raise ValueError. No synthetic release is invented and no malformed note is silently discarded. This is a strict supported-input policy, not a repair heuristic for damaged files.

Seven targeted test methods initially produced 10 failing subcases. After repair all seven and all six prior sequence tests pass in the core environment. The original checkpoint is unchanged. Files: preprocess_midi_inference_data.py and tests/test_midi_pairing.py.

## T-03: preservation — in progress

Approved layout direction: keep each original track and split its notes by hand, preserving original instruments and events. The comparison validator is prepared in midi_validation.py with tests/test_midi_validation.py; it checks PPQ, end tick, exact decoded events, and conservative same-tick ordering. Independent notes at the same tick may commute; events for the same channel/pitch keep order, while non-note events are ordering barriers. Track layout and intermediate end-of-track markers may change. Original metadata is not exempt from comparison.

Current checks: 20 total unittest methods passed (pairing, sequence, and validator). Exporter integration remains pending; no preservation success is claimed yet. Next action: retain source event identities, implement the approved track split, and validate serialized output before returning it.
