# HandJob decisions

Authority: [initial handover](HANDOVER.md), user-approved 2026-11-15. These inherited approvals remain valid; the audit does not reopen them merely because formal documents were absent.

| ID | Status | Choice / rationale | Consequence / revisit trigger |
| --- | --- | --- | --- |
| D-01 | Approved by user | eFORGE Continue; existing project and scope | Fill missing evidence; no full lifecycle restart. Revisit if user replaces project scope. |
| D-02 | Approved by user | Work only in shimuranmonk/hand-job | Never push sarapple/midi_hands. Revisit only on explicit user direction. |
| D-03 | Approved by user | MIDI import, LSTM hand prediction, manual note/group edits, faithful Synthesia export | FR-01–FR-05 and AC-01–AC-05 in handover; evidence required before release. |
| D-04 | Approved by user | Android and desktop browser UI; iOS excluded | FR-06; offline Android remains a feasibility question. |
| D-05 | Approved by user | Player and fingers deferred to phases 6/7 | No dependent implementation without new scope approval. |
| D-06 | Approved by user | Benchmark original LSTM before alternatives | No model replacement based on speculation; lack of evaluation data remains visible. |
| D-07 | Approved by user; prerequisite satisfied | Handover precedes Phase 0 | Handover committed and read back at d0908f889a91324a4caa1c944b2844fb5f71497f. |

Recommended direction, not approved framework selection: modular Python MIDI/inference/training/validation + API + responsive frontend; FastAPI and React remain candidates. Alternatives and rationale belong in a subsequent Phase 1 design decision.

Audit execution note (not a product decision): isolated Python 3.13 environment with diagnostic dependencies may test unchanged code after original requirements fail. It is not a reproducible historical 2020 environment or an approved production toolchain.

## D-08 — bounded core inference and sequence-completeness repair

Status: implementation choice within the user's 2026-11-15 “proceed” authorization for the recommended next task. Evidence: [INFERENCE_CORE.md](INFERENCE_CORE.md), H-05 in the audit, and tests/test_sequence_inference.py.

Choice: retain the original checkpoint and model; define a Windows/CPython 3.13 core reference environment separately from broken historical CLI/web packaging. Preserve previous-chunk padding for longer pieces, repeat a sole short input to fill its chunk, copy caller containers, and trim by real note count.

Alternatives: unpadded variable-length model invocation would change the existing batching contract; zero padding would change existing context for longer partial pieces; model/runtime replacement is unnecessary for this defect. The selected repair preserves the working longer-piece context and restores missing outputs with one helper change.

Consequence: sequence completeness is testable independently of pairing and event-preservation failures. This is not production-platform approval or evidence of model accuracy. Revisit if evaluation demonstrates a better padding policy or the model/feature contract changes. FR-02 / AC-02 and the H-05 portion of AC-04 only.

## D-09 — MIDI integrity policies and export direction

User explicitly selected “Preserve original tracks, split by hand” on 2026-11-15. Combining everything into two tracks is not selected. Keep original instruments, channels, timing, and events; actual Synthesia part behavior still requires validation.

Within the authorized repair, channel/pitch pairing uses FIFO for overlapping same-pitch notes; releases are consumed once. Invalid/unmatched streams fail explicitly instead of dropping notes or inventing durations. The event validator conservatively rejects playback-relevant ordering changes during hand splitting. See [MIDI_INTEGRITY.md](MIDI_INTEGRITY.md) for evidence and limitations. Revisit these policies if a licensed fixture demonstrates an unsupported legitimate use case; do not silently relax preservation.

## D-10 — extend Flask for the next MVP slice

Approved by the user on 2026-11-15: “Extend the existing Flask app” with responsive manual corrections and a small API. A new-stack design was the alternative offered. React/FastAPI remain options rather than dependencies or locked choices.

Implementation uses stateless request operations: original MIDI and current assignments remain in the browser and are submitted for validated export; no persistent server MIDI-session store is introduced. The original model is cached per application. Preview bounds and ephemeral-edit behavior are explicit in [WEB_PREVIEW.md](WEB_PREVIEW.md); they do not establish production NFR, offline support, or permanent-storage behavior. Revisit at deployment/performance/privacy design or when persistence becomes a requirement.

## D-11 — confirmed reference tracks and corrected label decoding

User confirmed track index 1=RIGHT and 2=LEFT for the initial four files on 2026-11-15. Files are authorized for private local evaluation; no redistribution/training permission or rights clearance is inferred. Seven later files received fidelity tests only.

Original unchanged-checkpoint decoder scored 7.98% on 3,585 confirmed notes. Training helper encodes staff 1/right as +1, while inference called positive LEFT. The decoder now maps nonnegative RIGHT and negative LEFT, matching training semantics and its zero boundary. That correction scored 92.02% on the same small development sample versus pitch baseline 90.01%. No weights, architecture, or normalization changed. See REAL_MIDI_RESULTS.md; do not generalize this score or call the reused sample untouched held-out evidence.

The separate non-rest=-1 diagnostic scored 92.64% overall but changed individual-piece results in both directions. It remains unactivated pending a broader preprocessing-contract review and independent labels. Actual Synthesia/device checks and release approval remain open.

## D-12 — main-piano-only MVP

Approved by the user on 2026-11-15: the Synthesia target is the main piano performance; mixed-instrument MIDI is not a current target. Keep the default simple, with no instrument-selection wizard. Multiple piano hand/voice tracks are processed together, not ranked by size or reduced to one physical track.

Implementation accepts sounding notes with active zero-based programs 0–5 (acoustic/electric pianos), with unspecified programs assumed to be default piano 0. Active percussion channel 9 (human channel 10) or other declared instrument programs produce a clear unsupported-input error before prediction. Program state is followed by channel and time across source tracks. Track names are not trusted as instrument proof. Incomplete/misleading MIDI instrument declarations cannot be identified acoustically; this is a declared-instrument check, not audio recognition.

No note/event is silently removed, no source instrument is converted, and no accompaniment is assigned to piano hands. The same policy applies to web analysis/export and core/CLI prediction. The low-level MIDI preservation engine remains independent of this product-level scope. All 11 supplied files pass this policy. Revisit mixed-instrument support only if the user expands scope.
