# Real MIDI validation and first model benchmark

2026-11-15. All results are local; no user MIDI, derived musical content, or reference-note label files are committed. Original checkpoint SHA-256: 638d1359db7ecafa252b0b3739fbb58595e25e4b05ed6ece4566d96dc1faac36 (unchanged).

## Input and authority

The user supplied a local MIDI folder, initially containing four pieces, and explicitly confirmed original track index 1 = right hand and index 2 = left hand for those four. Track 0 has no notes. These are user-confirmed track-derived reference labels, not an independently reviewed score corpus. Three pieces explicitly name their hand tracks; Canon uses generic names but the user confirmed its orientation too.

The folder later contained 11 files. All 11 were used for read-only import/export fidelity checks. Accuracy remains limited to the four confirmed pieces; the seven additional files were not silently assigned reference labels. The user authorized private local testing. Redistribution/training rights and checkpoint training provenance are unresolved.

## Original pipeline versus corrected label decoding

The checkpoint weights, architecture, per-piece normalization, and input features were held constant. Training source encodes staff 1 as +1 (right), staff 2 as -1 (left). Existing inference called positive values LEFT and nonpositive RIGHT. The corrected decoder maps nonnegative to RIGHT and negative to LEFT, consistent with the training sign convention and its zero boundary.

| Piece identifier | Notes | Original decoder | Corrected decoder | Pitch baseline (<60 left) |
| --- | ---: | ---: | ---: | ---: |
| A_Time_for_us-Romeo_and_Juliet-Nino_Rota-As_Flabis_score | 621 | 6.60% | 93.40% | 89.37% |
| Canon_in_D-Pachelbel-As_score | 1,032 | 5.43% | 94.57% | 94.96% |
| Kiss_The_Rain-Yiruma-As_Flabis_score | 1,060 | 8.96% | 91.04% | 83.30% |
| Only_Time-Enya-As_Flabis_score | 872 | 10.78% | 89.22% | 92.78% |
| **Aggregate** | **3,585** | **7.98%** | **92.02%** | **90.01%** |

Corrected decoding is a semantic bug repair, not retraining or model replacement. The original report is retained separately. Original decoder: 286/3,585 correct. Corrected decoder: 3,299/3,585 correct. Pitch baseline: 3,227/3,585 correct.

The four pieces are a small development-check sample, not proof of generalization or an approved quality threshold. The checkpoint's unknown training corpus may overlap these works. Reusing this sample for diagnosis prevents treating subsequent improvements as untouched held-out evidence.

## Preservation checks on 11 files

The 11 pieces contain 9,829 paired notes. Each received exactly one suggestion per note. Four scenarios per file passed serialized event/timing validation: original suggestions, all-left group correction, all-right group correction, and first-note hand flip. **44/44 passed**, with original file SHA-256 unchanged. Suggested outputs contain 2–7 tracks because tied retriggers and controller ordering can require additional same-hand subtracks. This is not a Synthesia playback test.

The initial fixed two-lane exporter correctly rejected some inputs when a repeated pitch switched hands at an identical tick. A later source-aware ordering graph handles those retriggers and aftertouch/end-note ordering without changing timing, channels, pitches, velocities, or other events. Unsatisfiable mixed-hand ordering cycles still produce a clear error, and independent event validation is mandatory.

## Separate feature diagnostic, not activated

A process-local experiment encoded non-rest as -1, matching the training helper, instead of the retained legacy MIDI value 0. It scored 92.64% on the same four-file development sample. It was **not** enabled in production. This small result does not resolve training-scaler provenance, MIDI/MusicXML unit parity, or unknown checkpoint preprocessing. The current default preserves legacy features while repairing label decoding. A broader independently labeled sample and an explicit feature-contract decision are needed before additional model changes.

Reproduction: patch P.get_on_off_note_pairs only within a diagnostic process, call its original implementation, set each returned pair's input_data[1] to -1, and evaluate the same manifest/model. The patch is removed when that process exits. No source input or checkpoint was changed.

## Local evidence and reproduction

- output/real-midi-checks/report.json: first four-file checks, prior to ordering repair.
- output/real-midi-checks-final/report.json: 11-file final preservation checks and per-file hashes/counts.
- output/user-evaluation/manifest.json and piece-*.labels.json: local reference material with explicit user confirmation and local-only use declarations.
- output/user-evaluation/original-model.json and original-model-context.json: original decoder baseline and code hashes.
- output/user-evaluation/sign-corrected-model.json: corrected decoder comparison, checksums, confusion matrices, per-hand precision/recall/F1, and per-piece results.
- output/user-evaluation/rest-flag-diagnostic.json: unactivated feature diagnostic.

Use evaluate.py and tools/check_midi_files.py with core requirements; see EVALUATION.md for schemas. output/ is ignored to keep user files/derivatives out of Git. The historical audit script now refuses to overwrite baseline evidence from a different source revision.

## Remaining gates

Physical Android/browser matrix, actual Synthesia import/part identity/playback, larger independent labeled evaluation, dataset/checkpoint rights/provenance, full preprocessing parity, production architecture/NFR budgets, and deployment approval remain open. Common Synthesia install paths and installed-program entries did not locate an installation; no EULA or installer was accepted. The responsive browser preview is a tested local development slice, not a release-ready MVP.
