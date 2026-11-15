# MIDI integrity repairs

Scope: FR-01/FR-04, AC-01/AC-04, audit H-01/H-02. User authorized continued bounded project work on 2026-11-15 and selected preserving original tracks while splitting notes by hand. No model/feature changes or Synthesia compatibility claim.

## T-02: pairing — verified

Pair by (channel, pitch), independent of release velocity. Treat note_on velocity zero only as a release. Repeated overlapping notes use FIFO onset order and consume each release once; this is a deterministic interpretation where MIDI does not identify note instances. Return pairs in onset order, preserving references to original events.

Unmatched releases, dangling onsets, and descending absolute tick order raise ValueError. No synthetic release is invented and no malformed note is silently discarded. This is a strict supported-input policy, not a repair heuristic for damaged files.

Seven targeted test methods initially produced 10 failing subcases. After repair all seven and all six prior sequence tests pass in the core environment. The original checkpoint is unchanged. Files: preprocess_midi_inference_data.py and tests/test_midi_pairing.py.

## T-03: preservation — verified for the supported contract

Approved layout direction: keep each original track and split its notes by hand, preserving original instruments and events. The comparison validator is prepared in midi_validation.py with tests/test_midi_validation.py; it checks PPQ, end tick, exact decoded events, and conservative same-tick ordering. Independent notes at the same tick may commute; events for the same channel/pitch keep order, while non-note events are ordering barriers. Track layout and intermediate end-of-track markers may change. Original metadata is not exempt from comparison.

Implementation: midi_engine.py attaches stable (source track, event index) identities. Each original track remains a contiguous group of hand subtracks; original messages are routed without reconstructing their payloads. Even hand lanes contain left notes and odd lanes contain right notes. Original track-name events remain unchanged within the source-track group; they are not proof of Synthesia hand identity. Type 0 becomes type 1 only when multiple output tracks are required. Original PPQ, channels, velocities, metadata, SysEx, and source-track end ticks are retained.

Real files exposed same-pitch off/on reversals when a pitch changed hands at one tick, and aftertouch tied to a note ending. Export now builds ordering constraints for complete note pairs and non-note barriers. Iterative strongly-connected-component analysis allows compatible events to share a hand lane; dependency ranks add another same-hand subtrack only when required. Non-note events follow those ranks rather than being forced ahead of right-hand notes. A cycle requiring both hands in one lane remains an explicit error. Independent serialized validation is still mandatory; no invariant was relaxed. More than two active hand parts per original track may result, which requires actual Synthesia usability validation.

The full get_left_right_hands_midifile path loads the source once, predicts labels, serializes the split, reparses bytes, and runs validation before returning output. Filename/Path and binary stream input are accepted. The low-level legacy get_midi_file_with_handedness without source_midi remains a note-only helper; it cannot preserve source metadata it never received. Application inference uses the source-aware path.

Supported inputs are synchronous PPQ MIDI types 0/1 with nonnegative integer delta ticks and fully paired notes. Type 2, SMPTE timing, missing/duplicate/foreign labels, and unsafe same-tick rearrangements fail explicitly. No quantization, default tempo replacement, channel remapping, or event reconstruction is used. Because preserving original non-note events can conflict with right-track ordering at an identical tick, some valid but ambiguous-to-split inputs are intentionally rejected pending a richer export policy.

Verification: `.inference-venv/Scripts/python -m unittest discover -s tests -v` passed **28 methods**, including eight exporter tests, seven validator tests, seven pairing tests, and six prior sequence tests. Integration checks cover types 0/1, full stream/filename prediction, manual routing, metadata-only files, trailing silence, invalid identities, and conservative ordering rejection. A separate original-checkpoint call on the bundled 69-note example passed preservation comparison: 138 decoded non-EOT events, PPQ 480, final tick 9615, two output tracks. No musical derivative was committed. This verifies event invariants, not hand accuracy or Synthesia playback.

Subsequent evidence: all 11 user-supplied MIDIs (9,829 notes) passed four export scenarios each: suggested hands, all-left group correction, all-right group correction, and a single-note flip. All 44 scenarios passed event/timing comparison and source checksum checks. Corrected suggested outputs use 2–7 tracks. Original files and derivatives were not added to Git. See REAL_MIDI_RESULTS.md for model/label evidence, and WEB_PREVIEW.md for the working correction UI.

The checkpoint remains unchanged. The later sign-decoding correction is documented separately in REAL_MIDI_RESULTS.md; original normalization remains unchanged. Remaining gates include preprocessing provenance, rights, and actual Synthesia/device validation. Historical 28-test results above describe the first preservation slice; the current combined suite has 56 passing methods, including ordering/long-chain regressions.
