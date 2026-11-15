# MIDI integrity repairs

Scope: FR-01/FR-04, AC-01/AC-04, audit H-01/H-02. User authorized continued bounded project work on 2026-11-15 and selected preserving original tracks while splitting notes by hand. No model/feature changes or Synthesia compatibility claim.

## T-02: pairing — verified

Pair by (channel, pitch), independent of release velocity. Treat note_on velocity zero only as a release. Repeated overlapping notes use FIFO onset order and consume each release once; this is a deterministic interpretation where MIDI does not identify note instances. Return pairs in onset order, preserving references to original events.

Unmatched releases, dangling onsets, and descending absolute tick order raise ValueError. No synthetic release is invented and no malformed note is silently discarded. This is a strict supported-input policy, not a repair heuristic for damaged files.

Seven targeted test methods initially produced 10 failing subcases. After repair all seven and all six prior sequence tests pass in the core environment. The original checkpoint is unchanged. Files: preprocess_midi_inference_data.py and tests/test_midi_pairing.py.

## T-03: preservation — verified for the supported contract

Approved layout direction: keep each original track and split its notes by hand, preserving original instruments and events. The comparison validator is prepared in midi_validation.py with tests/test_midi_validation.py; it checks PPQ, end tick, exact decoded events, and conservative same-tick ordering. Independent notes at the same tick may commute; events for the same channel/pitch keep order, while non-note events are ordering barriers. Track layout and intermediate end-of-track markers may change. Original metadata is not exempt from comparison.

Implementation: midi_engine.py attaches stable (source track, event index) identities. Export routes both note endpoints from their original messages, keeps non-note events on the original track, and adds an adjacent right-hand track only where needed. Original tracks contain left notes and original non-note events; original track-name events remain untouched. Track names are not proof of Synthesia hand identity. Type 0 becomes type 1 only when multiple output tracks are required. Original PPQ, channel data, velocities, metadata, SysEx, and each source track's end tick are retained.

The full get_left_right_hands_midifile path loads the source once, predicts labels, serializes the split, reparses bytes, and runs validation before returning output. Filename/Path and binary stream input are accepted. The low-level legacy get_midi_file_with_handedness without source_midi remains a note-only helper; it cannot preserve source metadata it never received. Application inference uses the source-aware path.

Supported inputs are synchronous PPQ MIDI types 0/1 with nonnegative integer delta ticks and fully paired notes. Type 2, SMPTE timing, missing/duplicate/foreign labels, and unsafe same-tick rearrangements fail explicitly. No quantization, default tempo replacement, channel remapping, or event reconstruction is used. Because preserving original non-note events can conflict with right-track ordering at an identical tick, some valid but ambiguous-to-split inputs are intentionally rejected pending a richer export policy.

Verification: `.inference-venv/Scripts/python -m unittest discover -s tests -v` passed **28 methods**, including eight exporter tests, seven validator tests, seven pairing tests, and six prior sequence tests. Integration checks cover types 0/1, full stream/filename prediction, manual routing, metadata-only files, trailing silence, invalid identities, and conservative ordering rejection. A separate original-checkpoint call on the bundled 69-note example passed preservation comparison: 138 decoded non-EOT events, PPQ 480, final tick 9615, two output tracks. No musical derivative was committed. This verifies event invariants, not hand accuracy or Synthesia playback.

Original checkpoint bytes and feature/sign contracts remain unchanged. Remaining work: make the standalone CLI use the minimal core without training imports and handle binary streams/filenames correctly; repair server startup; then establish a reviewable manual-correction flow. Model label orientation, preprocessing parity, data rights, and actual Synthesia/device validation remain open.
