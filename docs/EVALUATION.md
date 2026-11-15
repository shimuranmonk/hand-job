# Original-model evaluation contract

Purpose: benchmark the unchanged LSTM and a simple pitch split on the exact same reviewed notes. No model replacement, sign reversal, or scaler changes are performed. evaluate.py uses only the core requirements. Traceability: FR-02 / AC-07 and the audit's data/label risks.

## Run

```powershell
.\.inference-venv\Scripts\python.exe evaluate.py corpus/manifest.json example/checkpoint.pth output/evaluation.json
```

Optional flags: --config for the matching single model configuration, --split validation or test, and --pitch-threshold (default 60: pitches below 60 predict LEFT, others RIGHT). Do not tune a threshold on the test split and then describe its result as held-out validation.

This command must not overwrite the manifest, checkpoint, model config, or corpus files. It returns a nonzero error for missing files, unsupported input, incomplete labels, absent selected split, or invalid declarations. Existing output files at a distinct output path are replaced intentionally. No training data is downloaded or redistributed.

## Manifest schema (version 1)

Paths are relative to the manifest's directory, or explicit absolute paths supplied by the corpus owner. Example structure below is a schema example only, not an existing licensed corpus:

```json
{
  "version": 1,
  "pieces": [{
    "id": "unique-piece-id",
    "work_id": "shared-work-or-arrangement-group",
    "split": "test",
    "midi": "piece.mid",
    "labels": "piece.labels.json",
    "license": {
      "identifier": "actual rights/license declaration",
      "source": "actual source/provenance",
      "reviewed": true
    }
  }]
}
```

Each referenced label file contains the exact MIDI SHA-256, named reviewer, manual hand-review method, and one LEFT/RIGHT label for every onset ID. IDs are original track index:event index (for example 0:3), as returned by /api/analyze. Never identify notes solely by pitch or time when chords/overlaps may collide.

```json
{
  "midi_sha256": "actual full SHA-256 of the original MIDI",
  "method": "manual_hand_review",
  "reviewer": "actual reviewer identity",
  "notes": [{"id": "0:3", "hand": "LEFT"}]
}
```

The declarations are assertions supplied by the corpus owner, not independent certification of rights or labels. Staff number alone is not accepted as verified hand ground truth. A user-confirmed MIDI track mapping is also accepted with method=user_confirmed_track_mapping, a named reviewer, and track_hands mapping source track-index strings to LEFT/RIGHT; every note label must agree with that mapping. Validate cross-staff passages and ambiguous labels before labeling a score corpus reviewed. The default per-piece bound is 20,000 paired notes, shared with the local preview's parse contract.

For explicitly authorized private testing where rights remain unresolved, a piece may declare use_authorization=user_authorized_local_evaluation while license.reviewed remains false. This records the user's scope of permission, not legal clearance or redistribution/training rights. Reports retain that unreviewed status; no favorable rights declaration is invented for user-supplied music.

## Leakage and completeness checks

Piece IDs and note IDs must be unique. Identical MIDI bytes may not appear twice, even under different filenames. Entries sharing a work_id may not cross train/validation/test splits, so arrangements can be grouped deliberately. Label checksums must match their actual MIDI, and label IDs must exactly cover all paired notes. Duplicate JSON keys fail explicitly.

These checks catch declared-corpus contamination, not musical near-duplicates that were given unrelated work IDs. The checkpoint's original training provenance is unknown, so overlap with its training data cannot be ruled out. This limitation is always included in reports.

## Results and current evidence

Reports include original model and pitch-baseline accuracy, per-hand precision/recall/F1/support, confusion matrices (rows actual, columns predicted), per-piece and aggregate results, reviewed-label/source declarations, MIDI/label/checkpoint/config/manifest checksums, and torch version. Undefined denominators are null; an empty piece is not scored as perfectly correct. No approved numeric accuracy threshold has been invented.

Eight evaluator tests pass on wholly synthetic, locally generated fixtures: analytical metric values, model/baseline comparison on identical notes, duplicate/leakage rejection, checksum/completeness checks, review declarations, JSON integrity, local-only authorization, and track-mapping consistency. Their toy scores only verify the evaluator; they are not reported as accuracy of the pretrained LSTM.

The first four-file benchmark and corrected decoder result are recorded in REAL_MIDI_RESULTS.md. Those four track mappings were confirmed by the user. Seven later files were used only for preservation checks, without assuming reference hands. Synthesia installation/path remains unresolved after checks of common install paths and installed-program entries.
