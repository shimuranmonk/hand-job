# Synthesia compatibility check — partial and demo-limited

Observed 2026-11-15: the user supplied C:\Program Files (x86)\Synthesia\ and Synthesia 10.9.5903 opened successfully. The current A Time for Us suggested export loaded all 621 notes across five playable parts. All initially appeared as background; the map was used to assign three left-hand and two right-hand parts. Assigned colors and visual playback were observed, but the demo stopped at 20 seconds. Full-song playback, unrestricted practice, portability, and the 11-file acceptance matrix are not passed. The user chose demo-limited checks and later stopped computer control with Escape.

An optional .synthesia metadata prototype and four unit tests exist locally, uncommitted, in synthesia_metadata.py and tests/test_synthesia_metadata.py. Its official-format synthetic probe is in output/synthesia-metadata-probe/. The automatic hand-setup behavior has NOT been verified inside Synthesia. It is not integrated into the app or included in the piano-only task commit.

The local test packet is output/synthesia-validation/. It contains 11 suggested-hand MIDI files, an internal .handjob.json track map for each, and report.json. Inputs were read from the user's supplied MIDI folder. No user music or derivatives are tracked in Git or published remotely.

Preparation command:

```powershell
python tools/check_midi_files.py "YOUR_LOCAL_MIDI_FOLDER" output/synthesia-validation --suggested-only
```

All packet files have already passed decoded MIDI event/timing comparison. Each map records source/output SHA-256, source-track identity, output-track index, intended hand, and note count. It is an internal manual-test aid, **not** Synthesia's official .synthesia metadata format. Tracks with no notes have hand=null.

## Actual Synthesia acceptance steps

1. Record Synthesia version, OS/device, source filename/checksum, exported checksum, and test date. Do not assert a version that was not run.
2. Open each suggested MIDI. Confirm loading succeeds and the intended parts are visible. Follow the [official content guide](https://www.synthesiagame.com/support/guide/contentcreators) for hand-part setup. A file may contain several parts per hand because source tracks/channels/instruments and tied-event order are preserved.
3. Compare visible part identities with the .handjob.json map; ignore metadata-only tracks. Record whether automatic hand guesses are correct or whether manual assignment is required. Existing source track names alone are not a guarantee of corrected export-hand identity.
4. Confirm both intended hands can be practiced independently. For A Time for Us / Kiss the Rain and other repeated pitches, inspect hand switches at shared note-ending ticks. No note should be duplicated, missing, or left hanging.
5. Compare original versus exported playback for pitch, timing/tempo changes, programs, sustain, and expression where present. Event invariants are already checked numerically; record actual player behavior rather than inferring it from parseability.
6. Reopen the song and verify hand setup persistence. If automatic assignment or portability fails, document the exact behavior and decide whether explicit hand-track naming or official sidecar metadata is needed. Do not invent an official metadata schema or silently change preserved original metadata.
7. Mark each file pass/fail/pending with evidence. AC-05 remains pending until these actual checks are complete; a generic “MIDI imported” result is insufficient.

The initial install search was superseded by the user's supplied path above. No software was installed and no EULA/unlock action was taken. Full compatibility remains unverified within the demo limits. Physical Android validation likewise needs an actual device and an explicitly selected reachable development setup; localhost viewport emulation does not supply it.
