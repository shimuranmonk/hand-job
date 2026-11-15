# HandJob continuation

Current checkpoint (supersedes T-01's next-action section below): branch fix/midi-integrity, based on eb8d3b3116aee5897c2c03336a2d7dba51b0042e. User authorized ongoing bounded work. T-02 pairing is verified (13 pairing/sequence tests); independent preservation-validator checks also pass (20 tests total). T-03 exporter is in progress; next action is source-aware export integration. See docs/MIDI_INTEGRITY.md and D-09. New validator files remain uncommitted until exporter integration. No remote push.

Updated: 2026-11-15, Asia/Manila. Mode: eFORGE Continue; bounded sequence-completeness repair verified. Broader MVP/Phase 0 validation gates remain open.

## Verified starting state

- Fork origin: https://github.com/shimuranmonk/hand-job.git; never push upstream.
- Branch: fix/sequence-completeness, created from local audit commit ee76f07f0e3398ef3297fc8523a66f4164044588. Handover commit d0908f889a91324a4caa1c944b2844fb5f71497f is an ancestor.
- Local handover was compared with the remote text; an equivalent local backup is at ../HANDOVER.local-backup.md. Committed handover is authoritative.
- Read AGENTS.md for operating rules; docs/HANDOVER.md for scope/AC; docs/DECISIONS.md for inherited approvals.

## Active bounded task

T-01 complete: user authorized “proceed” with minimal core environment and sequence-completeness repair. Only application change: run_inference_and_get_flat_results. It copies chunk containers, fills short sequences, preserves longer-piece padding context, and retains exactly the real note count. No rewrite, model replacement, or production framework decision.

Reference core: CPython 3.13.3 / Windows x64 / CPU, requirements/inference-core.txt. Fresh .inference-venv installation, `pip check`, and all six regression tests passed. See docs/INFERENCE_CORE.md, docs/core-verification.json, and docs/core-environment.txt. Original requirements and CLI/web defects remain separate.

## Findings and evidence

- Read docs/PHASE_0_AUDIT.md for dispositions of H-01–H-08, priorities, and reproduction. Raw evidence: docs/audit/results.json and entry-point logs; tools/audit_baseline.py reproduces probes.
- Historical audit (pre-repair): checkpoint loads and bundled example retains 69/69 notes, but synthetic 1/16/32-note files export zero. Keep docs/audit evidence unchanged as the original baseline.
- Current regression: inputs of 0/1/7/8/15/16/17/31/32/33 notes yield one prediction and one exported note per input in fixtures deliberately isolating pairing. Order/no-mutation and direct model-output equivalence pass; checkpoint hash unchanged.
- Remaining confirmed defects: pairing, lost tempo/controller/program/meta events, channel and PPQ changes, preprocessing mismatch. Staff-sign mismatch observed; musical label orientation remains unresolved.
- Two distinct LSTM modules load successfully; repeated lstm config entries share weights. No checkpoint-load failure reproduced.
- Original CLI fails on filename/file-object usage. Current Flask-Limiter API prevents server import. They are not covered by the minimal core environment or this repair.
- No browser/device or Synthesia playback validation; no model accuracy score, training run, label corpus validation, or completed rights determination.

## Exact next task and boundaries

Next bounded task: repair note-on/off pairing (H-01). Establish channel/pitch identity, velocity-zero handling, consumption of each off event, overlap policy, and malformed-input behavior with fixtures before editing the pairing helper. Preserve this slice's sequence regression tests. Event/timing preservation follows as a separate task.

Remaining Phase 0 gates: licensed evaluation data/provenance, musical staff/hand orientation, coherent runtime choice, actual platform usability, and Synthesia validation. Do not treat the audit report as a passing MVP gate.

## Repository checkpoint

Base for T-01: ee76f07f0e3398ef3297fc8523a66f4164044588. Task-owned changes: the sequence helper, requirements/inference-core.txt, tests/test_sequence_inference.py, docs/INFERENCE_CORE.md, core environment/verification evidence, this continuation, and DECISIONS.md. Resolve the repair commit using `git log -1` after committing this checkpoint. Audit and repair commits are local only; no push is claimed or authorized by this checkpoint. Virtual environments are ignored, not committed. Handover remains unchanged and already remote.

## Lifecycle

Business Challenge/Intent approvals inherited; Intent Analysis retains open risks. User-approved T-01 bounded implementation and focused QC are verified; this does not pass the broader PRD/Solution Specification/NFR or MVP release gates. See handover lifecycle table and audit report.

Advisory effort for next task: Medium for the bounded pairing repair; revisit if overlapping/malformed MIDI policy reveals material design uncertainty. Settings unchanged. No product scope or framework choices were added.
