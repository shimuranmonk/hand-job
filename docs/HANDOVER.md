# HandJob — Authoritative Initial Project Handover

Date: 2026-11-15 (Asia/Manila).
Status: initial planning authority; baseline audit NOT STARTED; no application tests run for this handover.
Authority: the user's finalized decisions in the current handover request, informed by [Review repository fork](chatgpt-conversation://6af8fe9d-b344-83ec-aa49-b6dbd29c27aa). The current request controls if earlier discussion differs.

## 1. Purpose, authority, and immediate gate

This document establishes durable project memory before technical work. Use **eFORGE: Continue Project HandJob**, not a full restart. Reuse approved decisions; fill missing evidence and artifacts at the earliest relevant stage.

**Hard prerequisite:** Phase 0 must not begin until this document is committed to the authorized fork or delivered to the user for upload. Delivery or commit clears only this prerequisite; it does not mean Phase 0 has run or passed. This task ends after handover delivery and synchronization reporting.

Approved requirements below are authoritative. Recommended designs, proposed acceptance thresholds, unknowns, and unverified hypotheses are explicitly distinguished. Do not silently promote them to approved decisions. Amend durable decisions when later evidence or user direction changes them.

## 2. Repository and starting evidence

- Authorized repository: [shimuranmonk/hand-job](https://github.com/shimuranmonk/hand-job), a fork of [sarapple/midi_hands](https://github.com/sarapple/midi_hands).
- Never push to upstream. All authorized commits and pushes must target the fork.
- Locally verified before writing: checkout at `hand-job`, branch `audit/phase-0-continuation`, HEAD `83b39230c83b59284ba20019cb0fc572f9af86b4`; origin fetch and push both point to the authorized fork; working tree initially clean.
- No tracked `AGENTS.md`, `docs/CONTINUATION.md`, or `docs/HANDOVER.md` was found in that checkout. The user reports that project planning documents have not yet been uploaded.
- Historical context supplied by the user: a 2020-era prototype using a PyTorch LSTM, MusicXML-derived supervised labels, and `example/checkpoint.pth`. Treat execution, checkpoint usability, accuracy, current interface behavior, and compatibility as unverified.
- The original baseline has not been run. No audit conclusion, dependency compatibility result, model score, or Synthesia success is asserted here.
- A GitHub contents lookup for the handover returned 404 before creation; that alone does not distinguish a missing path from unavailable repository access.

## 3. Approved product scope

The project helps piano learners turn MIDI into editable left/right hand assignments while preserving the musical source.

| ID | Agreed MVP requirement |
| --- | --- |
| FR-01 | Import MIDI and retain the source information needed for faithful export. |
| FR-02 | Use ML/LSTM inference to predict left or right hand for notes. Benchmark the original LSTM before considering alternatives. |
| FR-03 | Let users manually correct individual notes and selected groups. Corrections must control final exported assignments. |
| FR-04 | Preserve MIDI timing, pitch, tempo, and events through processing and export, except explicitly documented structural changes required to represent hand assignment. |
| FR-05 | Export MIDI verified to work with Synthesia, including distinguishable left/right assignments. |
| FR-06 | Provide a responsive browser UI usable on Android and desktop. |

iOS is out of scope. Fully offline Android operation is a feasibility question, not an MVP promise. A Synthesia-style player is deferred to Phase 6, and finger assignment is deferred to Phase 7. Basic note visualization needed for correction does not authorize a full player. There is no requirement for an LLM, paid AI API, or external inference service.

## 4. Recommended design — not finalized technology choices

Use modular Python components for MIDI parsing/serialization, inference, training, and validation, with an API boundary and responsive web frontend. Keep the MIDI engine independent of UI and model choices. FastAPI and React are candidates, not locked decisions. Runtime versions, libraries, deployment, persistence, authentication, hosting, and packaging remain unresolved.

Recommended data flow: import immutable source plus event identity → extract model features → infer hand labels → apply explicit user overrides → serialize assignments → compare source/export invariants → validate in Synthesia.

Retain stable note identity and absolute tick timing alongside original track, channel, ordering, tempo, controllers, and metadata. Derive model features without mutating the musical source. Define a deterministic policy for overlaps, unmatched events, unsupported input, and export structure before implementation. These are design recommendations to validate, not claims about existing code.

An Android browser can potentially call a Python service; this does not demonstrate offline inference. Assess browser runtime/model conversion, local packaging, device memory, latency, and storage only within a bounded feasibility study. Do not adopt an offline architecture or replace the model before evidence and approval.

## 5. AI, labels, and data

First reproduce the existing preprocessing, checkpoint loading, inference, and evaluation behavior. Record checkpoint provenance, supported sequence shapes, feature definitions, normalization, label orientation, random seeds, software versions, and reproducible commands.

MusicXML staff is not guaranteed to equal hand. Cross-staff notation, staff changes, and ambiguous passages require validation; do not call staff-derived labels ground truth without qualification. Manually validate a representative labeled subset and document exclusions or uncertainty.

Use piece-level splits and check for duplicated works/arrangements to reduce leakage. Report left/right precision, recall, F1, confusion matrix, aggregate and per-piece results, difficult passages, and failure cases. Compare the original LSTM with a simple pitch-based baseline on the same held-out data before proposing alternatives. Record training/inference feature parity and checkpoint compatibility.

Dataset sources, redistribution rights, checkpoint rights, and the README's reported CC BY-NC 4.0 notice require review. Do not infer that a README notice establishes every asset's license, commercial permission, or permission to redistribute training material.

## 6. Unverified code-risk hypotheses

These originate in a prior read-only review. None is a confirmed defect in this handover. For each, preserve a minimal reproducer, expected behavior, observed result, and conclusion before fixing.

| ID | Hypothesis to test | Smallest useful evidence |
| --- | --- | --- |
| H-01 | Note-off handling, including note-on velocity zero, pairing, or operator precedence may be wrong. | Fixtures with both encodings, overlapping same-pitch notes, multiple channels, and malformed pairs. |
| H-02 | Channels, tempo, or other meta/events may be lost or changed. | Event-level source/export comparison with tempo changes, controllers, programs, and metadata. |
| H-03 | Staff label orientation may invert left/right or assume staff equals hand. | Trace labels through preprocessing, training, inference, and a manually checked score subset. |
| H-04 | Training and inference scalers may be inconsistent. | Compare transforms and feature arrays on identical known inputs. |
| H-05 | Empty or short sequences may fail or silently lose notes. | Boundary fixtures below, at, and above the model sequence length. |
| H-06 | Duplicate LSTM keys in a ModuleDict may overwrite intended modules or affect checkpoint loading. | Inspect actual keys/state dict and exercise loading and forward execution. |
| H-07 | Hardcoded training configuration may impede reproducibility. | Identify configuration inputs and reproduce a bounded run without hidden edits. |
| H-08 | Outdated dependencies may prevent supported installation or execution. | Isolated dependency resolution and documented baseline execution. |

## 7. Roadmap and exit evidence

| Phase | Scope | Required exit evidence |
| --- | --- | --- |
| 0 | Baseline audit | Reproducible environment and baseline attempt, evidence-backed findings, label/license review, prioritized risks and next task. |
| 1 | Modern architecture/tooling | Approved component boundaries, runtime/tooling choices, measurable NFR, and incremental migration plan. |
| 2 | Reliable MIDI engine | Passing preservation and edge-case fixtures; deterministic import/edit/export contract. |
| 3 | AI baseline/evaluation/training pipeline | Reproducible original-LSTM benchmark, validated labels/splits, evaluation report, and versioned preprocessing/model contract. |
| 4 | Responsive UI | Android and desktop import, prediction, individual/group correction, and export acceptance evidence. |
| 5 | Synthesia compatibility validation | Named Synthesia version/platform and fixture-level import, hand mapping, and playback evidence. |
| 6 | Synthesia-style player — deferred | Separate post-MVP scope and approval before work. |
| 7 | Finger assignment — deferred | Separate post-MVP scope and approval before work. |

Roadmap phases describe delivery order; the eight eFORGE lifecycle stages below describe engineering gates. A phase is not complete because its documentation exists. No full application rewrite is authorized by Phase 0.

## 8. Measurable MVP acceptance and traceability

The capabilities and preservation requirements are approved. The following concrete verification plan is recommended; fixture count, device matrix, accuracy target, performance budgets, and any tolerance require explicit recording before implementation/release. Do not invent an approved accuracy percentage.

| Test ID / requirement | Measurable pass condition |
| --- | --- |
| AC-01 / FR-01 | Every supported fixture imports with the expected note count; invalid/unsupported fixtures produce a clear error and no misleading export. Publish the supported MIDI types and limits. |
| AC-02 / FR-02 | Each imported supported note receives exactly one valid hand label; repeated inference with the same input/model/config yields identical results. Record model checksum and configuration. |
| AC-03 / FR-03 | Individual and group edits change exactly the selected labels; all edits survive export and reinspection, with zero unintended assignment changes. |
| AC-04 / FR-04 | Across every preservation fixture: zero missing/added notes, zero pitch/onset/duration changes in ticks, and zero unapproved changes to velocities, tempo maps, controllers, programs, or metadata. Record and verify any required track/channel remapping and same-tick ordering policy. Byte identity is not required. |
| AC-05 / FR-05 | Every agreed compatibility fixture opens in the recorded Synthesia version, presents the intended left/right separation, and plays with preserved pitches, timing, and tempo changes. Actual Synthesia evidence is required; parseability alone is insufficient. |
| AC-06 / FR-06 | The full import→predict→individual/group edit→export flow passes on every agreed Android and desktop browser/device combination, without clipped essential controls or blocked editing. Record browser versions, viewport, and input method. |
| AC-07 / AI quality | Publish held-out per-hand metrics and simple-baseline comparison on validated piece-level splits. Set the numeric quality threshold after Phase 0 evidence and obtain approval before treating model quality as release-ready. |
| AC-08 / reliability and NFR | Set representative file sizes, latency/memory budgets, upload/privacy/retention behavior, and failure recovery targets before implementation; release requires measured results against those recorded targets. |

Recommended fixtures include single-note and polyphonic files; simultaneous notes; repeated/overlapping pitches; velocity-zero note-offs; empty/short pieces; multi-track/channel data; tempo/time-signature changes; sustain/controllers; program changes; metadata; and malformed inputs. Use licensed material and record expected outcomes. Acceptable unsupported cases must be declared, not silently corrupted.

## 9. Phase 0 execution plan — pending

Only begin after the handover prerequisite in section 1 is satisfied, in a subsequent bounded task.

1. Read applicable AGENTS.md and compact continuation state if present; verify repository, branch, HEAD, worktree, and remote. Reconcile stale memory without overwriting user work.
2. Establish minimal operating memory: AGENTS.md, docs/CONTINUATION.md, and docs/DECISIONS.md as appropriate, linking this handover rather than duplicating it. Record inherited approvals and missing artifacts.
3. Inventory only relevant entry points, dependencies, checkpoint, sample data, UI routes, and training/inference paths. Record source commit and environment. No broad refactor.
4. Attempt installation and original execution in an isolated environment. Record exact commands, versions, input provenance, outputs, errors, and limitations. If blocked, preserve the failed attempt; do not call it a passing baseline.
5. Run a small licensed input through original inference/export where possible. Capture counts, timing, feature/label behavior, model load outcome, and UI observations.
6. Test H-01 through H-08 using bounded fixtures; mark each confirmed, refuted, or unresolved with evidence. Separate audit findings from proposed repairs.
7. Validate staff/hand assumptions and available evaluation data; review licenses and checkpoint provenance. Document what cannot be legally or technically evaluated.
8. Probe MIDI preservation and Synthesia representation. If Synthesia is unavailable, report compatibility as pending and identify the exact manual validation needed.
9. Assess Android/desktop delivery and offline feasibility without promising offline support or locking frameworks. Identify architecture decisions needing approval.
10. Publish a baseline audit report, prioritized blockers, proposed acceptance budgets, lifecycle coverage, and the smallest next task. Update continuation with exact checks and next action. Commit only task-owned fork changes when authorized.

Phase 0 exits with evidence and a decision-ready plan, including explicit blockers. It does not require speculative fixes, model replacement, a rewritten frontend, a player, or finger assignment.

## 10. eFORGE lifecycle and gates

eFORGE means Earl's Framework for Organized Requirements, Generation and Engineering. Continue from existing approvals and the earliest missing dependency; do not restart ceremonially.

| Stage | Initial status and required next artifact/evidence |
| --- | --- |
| 1. Business Challenge | Approved problem/scope direction captured here; no independent validated business artifact claimed. |
| 2. Intent | Approved MVP, platforms, exclusions, and fork policy captured here. |
| 3. Intent Analysis | Pending: baseline evidence, feasibility, label validity, licensing, and risk tests. |
| 4. PRD | Requirements inherited here; formal traceability and measurable thresholds need completion. |
| 5. Solution Specification | Recommended modular direction; frameworks and consequential design choices remain unapproved. |
| 6. Non-Functional Requirements | Pending measurable performance, reliability, privacy, compatibility, and deployment targets. |
| 7. Solution Generation | Existing prototype inherited; modernization not started or verified. |
| 8. Testing & Quality Control | Pending; no passing baseline, model-quality, preservation, UI, or Synthesia gate claimed. |

Reuse approvals within their actual scope. Obtain approval for consequential unresolved product/design choices before dependent implementation. Changed requirements reopen affected gates only. Quality completion requires evidence; a blocked test stays blocked unless the user explicitly accepts an exception.

## 11. CREP and durable project memory

CREP is the Context and Resource Efficiency Protocol. Its purpose is to reduce avoidable work; it does not guarantee provider allowance, cost, or time savings.

- Start with AGENTS.md and docs/CONTINUATION.md; consult relevant handover sections only for gaps. Verify actual state before trusting memory.
- Load minimal context: search paths/symbols first, inspect bounded excerpts, and read only active lifecycle references. Avoid repeated full repository scans and copied chat histories.
- Execute bounded tasks with objective, allowed files, acceptance criteria, checks, and stopping condition. Keep refactoring within scope.
- Maintain docs/DECISIONS.md with stable IDs, status, context, options, choice, rationale, approver/scope/date, evidence, consequences, and revisit trigger.
- Use deterministic tests for evidence. Re-run checks after relevant changes, failures, or uncertainty; never label unrun tests as passed.
- Keep AGENTS.md operational and compact; docs/CONTINUATION.md records current state; docs/HANDOVER.md preserves transfer authority. Link detailed artifacts rather than duplicating narratives. This initial handover is intentionally complete; do not trim agreed scope to meet a line budget.
- Before stopping, record branch, relevant commit, dirty files, active stage/task, completed and pending checks, approvals, blockers, and exact next action.
- Respect the current worktree and user changes. Never blanket-stage, reset, force-push, or edit unrelated projects. Use concise commits containing only reviewed task-owned changes.
- Distinguish local files, local commits, remote commits, and merged state. Verify each reported mutation. Never push upstream.

## 12. Decision register and unresolved questions

Approved decisions as of this handover: D-01 continue eFORGE; D-02 fork-only work; D-03 MIDI/ML/manual-correction/Synthesia MVP; D-04 Android and desktop browsers, iOS excluded; D-05 player and fingers deferred; D-06 original LSTM benchmark first; D-07 handover precedes audit. The approver is the user through the current request. These IDs can seed docs/DECISIONS.md without requesting the same approvals again.

Unresolved: supported MIDI types and export encoding of hands; original model accuracy/usability; exact staff orientation and label quality; dataset/checkpoint/software rights; runtime and frontend choices; deployment and data retention; device/browser matrix; offline Android feasibility; model/performance thresholds; available Synthesia version and tester. Assign evidence and owners in the audit; do not resolve these by assumption.

## 13. Recovery checkpoint and exact next action

At authoring: documentation-only task on local branch `audit/phase-0-continuation`, starting HEAD `83b39230c83b59284ba20019cb0fc572f9af86b4`. Only `docs/HANDOVER.md` is intended to change. No application code changed, baseline executed, or Phase 0 tests run.

Handover completion criteria: complete file exists; approved/recommended/unknown/hypothesis distinctions checked; only this file committed to the fork if access permits, otherwise user receives the file. The delivery response must state the verified remote commit hash or clearly state that upload remains pending. This document does not assert its own publication success.

**Exact next action after delivery:** verify this handover's actual repository/local status, then initiate the bounded Phase 0 baseline-audit task from section 9. Until that task begins, Phase 0 remains NOT STARTED.
