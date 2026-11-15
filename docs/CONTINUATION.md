# HandJob continuation

Updated: 2026-11-15 (Asia/Manila). eFORGE Continue; branch fix/midi-integrity.

Latest completed slice: piano-only MVP scope (D-12), approved by the user. Programs 0–5 or unspecified default piano are accepted; active percussion channel 9 or other declared programs are rejected before prediction, without dropping events. All piano hand/voice tracks form one performance. No instrument-selection workflow. Web/CLI/core checks and piano-specific UI copy are implemented; all 11 supplied files pass the scope check. See piano-scope-verification.json: 68 discovered tests pass (64 project methods plus four unrelated local metadata-prototype methods), and the live preview rejects percussion with HTTP 400. Prior latest-verification.json is a historical pre-scope snapshot.

The local preview was restarted with the documented core+web environment at http://127.0.0.1:5088; launcher PID 17072 (verify before stopping). Two pre-existing untracked prototype files remain intentionally outside this slice: synthesia_metadata.py and tests/test_synthesia_metadata.py. No automatic Synthesia setup is claimed from their unit tests.

## Authority and repository

- Read AGENTS.md and this checkpoint; HANDOVER.md is approved scope, DECISIONS.md records choices.
- Only fork origin https://github.com/shimuranmonk/hand-job.git; never push upstream.
- Remote handover d0908f8; local audit ee76f07, sequence eb8d3b3, pairing 0d391db, source preservation 737d00a, CLI d751f06, ordering lanes 9216187. Web preview 281e268, decoder/evaluation 73d6cb2, compatibility packet tooling e53cd27. The final verification commit contains this checkpoint; use git log -1.
- Audit/implementation commits are LOCAL ONLY. No push/merge/deployment occurred. User requested sustained progress, not repeated stops after each small task; remaining daily allowance is not visible.
- User approved preserving original tracks and splitting by hand, extending existing Flask, local MIDI testing, and reference mapping track 1 RIGHT / track 2 LEFT for the initial four files.

## Implemented and verified

- Core/CLI: CPython 3.13.3 Windows x64 CPU; requirements/inference-core.txt. Filename/stream support, restricted checkpoint loading, source-overwrite protection; original weights unchanged.
- MIDI pairing: channel/pitch FIFO, velocity-zero handling, unique release consumption, explicit malformed-input errors.
- MIDI export: source identities, PPQ/channels/event payload preservation, dependency-ranked hand subtracks for tied retriggers/controllers, independent serialized validation. Unsatisfiable mixed-hand ordering cycles still reject. Type 2/SMPTE unsupported.
- Flask local preview: requirements/web.txt, stateless analyze/export API, original model cached, responsive note/group correction, filters, pagination, undo, validated downloads. No account/database/persistent edits/external AI service/CDN.
- User's folder grew to 11 MIDI files. All 9,829 notes predicted once; all 44 per-file suggestion/group/single-edit export scenarios passed, with source hashes unchanged. Additional .handjob.json maps and MIDI packet prepared in output/synthesia-validation/.
- Initial four pieces: 3,585 user-confirmed reference notes. Original decoder 7.98%; sign correction 92.02%; pitch baseline 90.01%. Fixed nonnegative RIGHT / negative LEFT to match training. No normalization/weights changes.
- Separate rest-flag=-1 diagnostic scored 92.64% but varied by piece; NOT activated. Broader feature provenance/independent evaluation remains necessary.
- 56 unittest methods passed with web dependencies; latest-verification.json and web-environment.txt capture final clean-core-plus-web verification. Browser import/edit/group/undo/export checked, including 1,436-note file and selection across 100-row pages. Phone viewport showed no page overflow; physical Android not tested.

## Evidence pointers

- MIDI_INTEGRITY.md, INFERENCE_CORE.md, WEB_PREVIEW.md, REAL_MIDI_RESULTS.md, EVALUATION.md, SYNTHESIA_CHECK.md.
- output/user-evaluation/manifest.json references the private input paths and four local label files. Original/corrected/diagnostic reports are separate. These and all musical derivatives remain ignored, never committed.
- output/real-midi-checks-final/report.json: 11-file fidelity results. output/synthesia-validation/: 11 MIDI outputs + track maps + preparation report.
- Historical docs/audit remains the original pre-repair evidence; baseline script now guards its source revision.
- Local preview: http://127.0.0.1:5088, started hidden; replacement launcher PID 23196 (verify actual process before stopping it). User-facing browser tab retained. Screenshots output/editor-desktop.jpg and output/editor-mobile.jpg.

## Exact next action and blockers

Synthesia is now located at C:\Program Files (x86)\Synthesia\Synthesia.exe, version 10.9.5903. One current 621-note export imported, manual hand assignments and visual playback were observed, and the demo stopped at 20 seconds. The user chose demo-limited checks and then stopped computer control with Escape. Automatic hand setup and the complete file matrix remain unverified; see SYNTHESIA_CHECK.md. Resume computer control only for an authorized task, not automatically as part of the piano-only scope fix. No installer/EULA/unlock action was taken.

Physical Android needs a real device and approved reachable backend setup. Current server binds localhost only; do not expose it publicly as a testing shortcut.

After external compatibility evidence, formalize production NFR/architecture and evaluate preprocessing on an independent labeled corpus. Rights/provenance and overlap with unknown checkpoint training data remain unresolved. Do not train, replace the model, blindly flip more features, adopt React/FastAPI, or claim MVP release quality from this small sample.

## Gates

Inherited product scope retained; bounded repair/UI/evaluation slices verified. Broader PRD/NFR, production design, physical-device, Synthesia and release gates remain open. iOS excluded, player/fingers deferred, offline Android unresolved. Next work requires external compatibility evidence or an explicit next design decision; do not manufacture work to exhaust an unknowable allowance.
