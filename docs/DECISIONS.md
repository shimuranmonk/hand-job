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
