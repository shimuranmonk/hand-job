# HandJob

**We Know Exactly Where Your Fingers Should Go.**

![HandJob logo](static/handjob-logo.png)

A black, gold, and white piano MIDI hand editor: predict left/right hands, review individual notes or groups, and export with timing, pitch, tempo, channels, and events checked. Individual finger assignment is a planned post-MVP feature; the tagline is branding, not a claim that fingering exists.

**Status: working local preview, not a release-verified MVP.** Further features and production architecture are still being planned on paper. The next acceptance step is user testing of exported MIDI in licensed Synthesia on an Android phone and iPad. This does not add an iOS app to scope.

Exports preserve source tracks and split their notes by hand; they can contain more than two parts. Automatic Synthesia hand setup is not yet verified.

## HandJob continuation

Project scope and status: [handover](docs/HANDOVER.md), [continuation](docs/CONTINUATION.md), and [baseline audit](docs/PHASE_0_AUDIT.md). Development is fork-only. The original checkpoint is retained; [real MIDI results](docs/REAL_MIDI_RESULTS.md) record the four-piece development comparison and its limits. A desktop Synthesia import, manual hand assignment, and demo-limited playback were observed; full compatibility remains unverified.

For the verified Windows/Python 3.13 core setup:

```powershell
python -m venv .inference-venv
.\.inference-venv\Scripts\python.exe -m pip install -r requirements/inference-core.txt
.\.inference-venv\Scripts\python.exe -m unittest discover -s tests -v
.\.inference-venv\Scripts\python.exe inference.py example/checkpoint.pth input.mid result.mid
```

Use a different output filename. No configuration file needs moving. `--config path/to/config.json` accepts one matching model parameter set. See [core setup](docs/INFERENCE_CORE.md) and [MIDI integrity contract](docs/MIDI_INTEGRITY.md) for supported inputs and explicit rejection cases. Core requirements do not install web or training dependencies.

For the local responsive correction screen, install `requirements/web.txt`, run `python server.py`, and open [localhost:5000](http://127.0.0.1:5000). Import a MIDI, edit individual notes or selected groups, and export the corrected file. See [web preview instructions and limits](docs/WEB_PREVIEW.md). Edits last only while the page remains open; actual Android and Synthesia acceptance checks are still pending.

The current MVP targets **piano-only MIDI**. Separate right/left-hand or piano-voice tracks are processed together. Declared drums or other instruments are rejected with a clear message; multi-instrument selection and accompaniment processing are outside the current scope.

MIDI Left and Right-Handedness Transcription (For Piano)

## What This Does

Imports piano-only MIDI, suggests left/right hand assignments, supports manual corrections, and exports validated MIDI hand subtracks. It does not yet guarantee automatic Synthesia hand assignments.

## How MIDI Works and Goal

Typically, separate tracks ae used to separate left and right hands in a MIDI-version of a song. 

This aims to improve existing tracks without any separation of handedness, as well as generating handedness in MIDI files with a single track.

## How It Learned

A Pytorch LSTM neural net was used to predict left and right handedness on sequences of notes.  Ground truth sheet music in musicxml form (containing left and right handedness) was used to learn. The output predicts either left or right on each note.

## Checkpoint

A checkpoint is made available for others to use in the `/example` folder. Parameters for learning are not hard-coded, and can be adjusted by adding a `trains.json` json file to the root of the project. An example file `/example/trains.example.json` is provided.

## Legacy training reference (not a verified modern training pipeline)

- Add musicxml files numbered as 0000.musicxml, 0001.musicxml... to `source_data/musicxml`
- Rename `/example/trains.example.json` to `trains.json` and move it to the root of the folder. 
- Then call the following command:
```
python learn.py
```

Outputs:

- MusicXML will be stored in `output/train_output/progress/{your_model_name}`.
- A state object for evey epoch will be created in `output/train_output/progress/{your_model_name}.pth`.
- The final model will be stored as `output/train_output/completed/{your_model_name}.pth`

## To generate a midi file from an original with left and right hand encodings

- The standalone command uses `example/trains.example.json` by default. Keep that file in place; use `--config` for a different matching, single-configuration file.
- Call the following command:
```
python inference.py example/checkpoint.pth example/simple_midi.example.mid result.mid
```

## Credits

HandJob continues the original [sarapple/midi_hands](https://github.com/sarapple/midi_hands) prototype. The original PyTorch LSTM checkpoint and historical training work are retained. Development and publication take place only in [shimuranmonk/hand-job](https://github.com/shimuranmonk/hand-job).

A helper file from Magenta (Copyright 2020 The Magenta Authors)was pulled out and used, unaltered from the source.  This was done in favor of importing the large lib involved with installing Magenta. This was used for parseing MusicXML into a dictionary.

## License

This work is licensed under a [Creative Commons Attribution-NonCommercial 4.0 International License](http://creativecommons.org/licenses/by-nc/4.0/)
