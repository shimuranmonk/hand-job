# HandJob continuation

Updated: 2026-11-15 (Asia/Manila). eFORGE Continue; branch fix/midi-integrity.

## Authority and repository

- Read AGENTS.md, then this checkpoint. docs/HANDOVER.md is the approved scope; docs/DECISIONS.md records choices.
- Only fork origin https://github.com/shimuranmonk/hand-job.git; never push upstream.
- Handover d0908f8 is remote. Local audit ee76f07, sequence repair eb8d3b3, pairing repair 0d391db. Current preservation commit contains this checkpoint; resolve with git log -1.
- No push of audit/repair work has been performed. Worktree changes are task-owned; virtual environments are ignored.
- User requested sustained progress through agreed work without stopping after small tasks. Daily allowance is not visible or measurable. Do not waste work to consume it.

## Verified slices

- T-01 sequence completeness: six regressions, checkpoint unchanged; docs/INFERENCE_CORE.md and core-verification.json. Reference CPython 3.13.3, Windows x64, CPU; requirements/inference-core.txt installs core only.
- T-02 pairing: channel/pitch FIFO; release velocity independent; zero-velocity note-on releases; malformed/unmatched streams error. Seven targeted tests.
- T-03 source-aware export: user chose preserving original tracks and splitting by hand. Original non-note events stay on original tracks; right notes use adjacent tracks. Source event identities prevent silent omissions/duplication. Reparsed serialized output must pass midi_validation.py before return.
- All 28 unittest methods passed. Separate original-checkpoint sample call preserved 138 events, PPQ 480, final tick 9615, two tracks. See docs/MIDI_INTEGRITY.md.
- Source-aware full path accepts filenames/Path/binary streams; lower-level note-only legacy helper does not promise metadata preservation.

## Exact next task

T-04 verified: standalone CLI now uses core-only imports, source-relative default config, restricted CPU checkpoint loading, correct filenames/streams, and source-overwrite protection. All 33 tests pass in the core environment. Next T-05: repair Flask startup and request validation, then build a stateless manual-correction flow in the existing web stack. No app rewrite or model replacement.

## Open gates and limits

- Export supports synchronous PPQ types 0/1 with fully paired notes. Type 2, SMPTE, malformed notes, and unsafe same-tick reorderings fail explicitly.
- Standalone CLI works with core pins; Flask-Limiter startup remains broken. Core pins do not include web/training dependencies.
- Staff-sign mismatch, scaler/rest/unit consistency, model accuracy, licensed evaluation data and checkpoint provenance unresolved. No label flip or retraining without evidence.
- Manual note/group UI, Android/desktop usability, production architecture/NFR budgets, offline Android feasibility, rights determination, and actual Synthesia validation remain pending.
- iOS excluded; player/fingers deferred. FastAPI/React not locked.
- Historical docs/audit evidence remains the pre-repair baseline; do not overwrite it with current behavior.

## Gates and next effort

Scoped pairing/preservation implementation and tests are verified; broad MVP and release quality gates are not passed. Preserve existing scope approvals. Medium effort suits the bounded CLI/server repair; consequential architecture choices require separate evidence/approval. No settings changed.
