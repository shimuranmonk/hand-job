# HandJob continuation

Updated: 2026-11-15, Asia/Manila. Mode: eFORGE Continue; initial Phase 0 audit delivered with open validation gates.

## Verified starting state

- Fork origin: https://github.com/shimuranmonk/hand-job.git; never push upstream.
- Branch: audit/phase-0-continuation. Fast-forwarded from 83b3923 to handover commit d0908f889a91324a4caa1c944b2844fb5f71497f.
- Local handover was compared with the remote text; an equivalent local backup is at ../HANDOVER.local-backup.md. Committed handover is authoritative.
- Read AGENTS.md for operating rules; docs/HANDOVER.md for scope/AC; docs/DECISIONS.md for inherited approvals.

## Active bounded task

Audit unchanged prototype; add only operating memory, audit tooling, synthetic fixtures, and evidence. Stop with findings, blockers, and exact next task. No rewrite, model replacement, or production framework decision.

Initial requirements installation failed on deprecated sklearn package. Diagnostic environment .audit-venv uses scikit-learn and supplemental runtime dependencies without editing application files. `pip check` passes in this diagnostic environment only.

## Findings and evidence

- Read docs/PHASE_0_AUDIT.md for dispositions of H-01–H-08, priorities, and reproduction. Raw evidence: docs/audit/results.json and entry-point logs; tools/audit_baseline.py reproduces probes.
- Checkpoint loads, state keys match, [1,16,1] forward shape. Stream inference retains 69/69 bundled example notes and 17/17 synthetic notes; synthetic 1/16/32-note files export zero notes.
- Confirmed: pairing defects, lost tempo/controller/program/meta events, channel and PPQ changes, preprocessing mismatch, sequence truncation. Staff-sign mismatch observed; musical label orientation remains unresolved.
- Two distinct LSTM modules load successfully; repeated lstm config entries share weights. No checkpoint-load failure reproduced.
- Original CLI fails on filename/file-object usage. Current Flask-Limiter API prevents server import. No application source was changed.
- No browser/device or Synthesia playback validation; no model accuracy score, training run, label corpus validation, or completed rights determination.

## Exact next task and boundaries

Define supported minimal inference environment and sequence-test contract; then repair sequence completeness in a separate bounded task, keeping checkpoint and architecture unchanged. Boundary counts: 0/1/7/8/15/16/17/31/32/33; require exactly one output per input note. Pairing/preservation repairs follow separately.

Remaining Phase 0 gates: licensed evaluation data/provenance, musical staff/hand orientation, coherent runtime choice, actual platform usability, and Synthesia validation. Do not treat the audit report as a passing MVP gate.

## Repository checkpoint

Base: d0908f889a91324a4caa1c944b2844fb5f71497f. Task-owned changes: AGENTS.md, this continuation, DECISIONS.md, PHASE_0_AUDIT.md, tools/audit_baseline.py, and docs/audit evidence. Resolve the audit commit with `git log -1` after committing this checkpoint. These audit changes are local only; no audit push is claimed or authorized by this checkpoint. Virtual environment is ignored, not committed. Handover remains unchanged and already remote.

## Lifecycle

Business Challenge/Intent approvals inherited; Intent Analysis has initial evidence with open risks. PRD metrics, Solution Specification, and NFR gates pending. Existing implementation inherited, not quality-verified. See handover lifecycle table and audit report.

Advisory effort: High for runtime/feature-contract choices; Medium for the subsequent isolated regression repair once its design is settled. Settings unchanged. No product scope or framework choices were added during the audit.
