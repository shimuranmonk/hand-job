# Core inference reference environment and sequence repair

Task T-01, authorized by the user's “proceed” after the initial Phase 0 audit. Links: FR-02, AC-02, the sequence-completeness portion of AC-04, and H-05 in [HANDOVER.md](HANDOVER.md) / [PHASE_0_AUDIT.md](PHASE_0_AUDIT.md).

## Scope and environment

Reference platform: Windows x64, CPython 3.13.3, CPU. requirements/inference-core.txt pins the four direct dependencies needed by the original LSTM, MIDI inference helpers, and repaired standalone CLI. tests/test_sequence_inference.py exercises those helpers and the original checkpoint. This is a bounded core reference environment, not the final production runtime, a full training environment, or a working Flask installation.

Fresh environment setup from repository root:

```powershell
python -m venv .inference-venv
.\.inference-venv\Scripts\python.exe -m pip install -r requirements/inference-core.txt --index-url https://pypi.org/simple
.\.inference-venv\Scripts\python.exe -m pip check
.\.inference-venv\Scripts\python.exe -m unittest discover -s tests -v
```

The direct pins are torch 2.15.0, scikit-learn 1.9.1, mido 1.3.3, and numpy 2.5.4. The separately recorded core-environment.txt captures resolved transitive versions for this verification. It is an environment snapshot, not a cross-platform lockfile. Other Python versions/platforms and accelerators are untested. requirements.txt remains the original historical input and still fails on sklearn; it is not the setup command for this core slice.

To call the core from Python, use inference.load_inference_model and pass a filename, Path, or binary stream to PreprocessMIDIInferenceData.get_left_right_hands_midifile inside torch.inference_mode(). The loader uses the existing model parameters, strict state-dict loading, weights_only=True, and CPU mapping. Web startup is a separate task.

## Bounded design and behavior

Allowed application change: run_inference_and_get_flat_results only. Expected input is the existing chunker contract: full chunks of sequence_length notes followed by at most one nonempty short chunk, or an empty chunk list for an empty piece.

- Empty input returns no predictions without invoking the model.
- Copy chunk containers before padding so callers retain their original input.
- Keep existing previous-chunk prefix padding for a final partial chunk in a longer piece. For a sole short chunk, repeat its notes cyclically until it reaches sequence_length. Padding is model context only, never exported notes.
- Flatten model outputs and take the real input note count. Exact multiples of the sequence length therefore retain all outputs instead of hitting the original [:-0] empty slice.
- Preserve checkpoint bytes, architecture, preprocessing, sign mapping, and existing longer-piece context. Musical accuracy of padding and existing model preprocessing remains unmeasured.

No framework, offline Android, new model, or product scope decision follows from this repair. Existing pairing/event-preservation defects can still lose or change MIDI notes before or after this helper. One prediction per successfully paired note is not yet a guarantee for arbitrary imported MIDI.

## Verification contract

The six unittest methods include boundary subcases 0/1/7/8/15/16/17/31/32/33, identity/order checks using distinguishable outputs, no caller mutation, rectangular model input, original longer-piece padding context, a nondefault sequence length, strict original-checkpoint loading/hash, direct-forward equivalence for complete chunks, and synthetic MIDI through prediction/export/reparse.

Synthetic MIDI deliberately uses matched release velocities so this task's result is not confused with H-01. Tests do not claim to pass general event preservation, model accuracy, or Synthesia compatibility.

Before repair, the tests produced 14 failing subcases and one error across six test methods, reproducing truncation and mutation. After repair, all six methods pass in both the diagnostic environment and a fresh .inference-venv installed solely from requirements/inference-core.txt. `pip check` also passes in the fresh environment. See [core-verification.json](core-verification.json) for exact commands/results and [core-environment.txt](core-environment.txt) for its 19 installed distributions. Checkpoint SHA-256 remains unchanged.

## Remaining work

Pairing and source-aware preservation repairs are recorded in MIDI_INTEGRITY.md. T-04 repaired the CLI: no training/web imports, config default relative to the source module, explicit alternate single-config support, correct stream/filename output, protected source filename, and clear nonzero failures. Five CLI tests plus prior tests pass (33 total) using only core dependencies, including subprocess execution from another working directory and no output for invalid MIDI.

Later slices repaired Flask startup and added the responsive correction UI (WEB_PREVIEW.md). A confirmed four-piece comparison exposed and repaired the hand-sign decoder; REAL_MIDI_RESULTS.md records 92.02% on that development sample, with original weights and normalization retained. Generalization, full preprocessing provenance, dataset rights, physical Android, and real Synthesia validation remain open.
