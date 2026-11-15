# HandJob operating rules

- Continue eFORGE from `docs/CONTINUATION.md`; use `docs/HANDOVER.md` for approved scope and acceptance criteria.
- Work only in this fork: `https://github.com/shimuranmonk/hand-job`. Never push upstream.
- Verify branch, HEAD, dirty files, and remotes before edits. Preserve user changes and stage only reviewed task-owned files.
- MVP: MIDI import, original LSTM benchmark, hand prediction, individual/group correction, faithful MIDI export, Synthesia validation; Android and desktop browsers.
- iOS excluded; offline Android unresolved; player and finger assignment deferred. FastAPI/React are candidates, not approved choices.
- Phase 0 permits audit scripts, synthetic fixtures, isolated environments, and documentation, not application rewrites or speculative repairs.
- Keep hypotheses distinct from reproducible findings. No test or compatibility claim without observed evidence.
- Load bounded relevant files; avoid repeated full scans. Record durable choices in `docs/DECISIONS.md`.
- Update continuation with exact state, checks, blockers, approvals, and next bounded action before stopping.
- Do not commit virtual environments, caches, downloaded dependencies, or third-party datasets. Audit outputs belong in `docs/audit/` only when reviewed.
