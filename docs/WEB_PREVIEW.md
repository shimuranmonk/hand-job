# Responsive hand-correction preview

T-05/T-06, 2026-11-15. User explicitly approved extending the existing Flask app with a responsive correction screen and small API. This is an incremental local preview, not a production architecture or release claim. Traceability: FR-01/02/03/04/06; source event preservation from T-03 remains mandatory.

## Run locally

```powershell
.\.inference-venv\Scripts\python.exe -m pip install -r requirements/web.txt
.\.inference-venv\Scripts\python.exe server.py
```

Open http://127.0.0.1:5000. For a different port: `python -m flask --app server run --host 127.0.0.1 --port 5088`. The current development preview was started at port 5088. It binds only to localhost; it is not an Android-hosted/offline app or an Internet deployment. Physical Android testing still needs an explicitly selected reachable development setup.

Core-only tests skip the web methods if Flask/Flask-Limiter are absent. Full checks: `python -m unittest discover -s tests -v` with requirements/web.txt installed. Historical requirements.txt remains the original training dependency input, not the preview setup.

## User flow and boundaries

Import a .mid/.midi file; the original LSTM suggests hands. Review notes in a paginated table. Find notes by pitch/name, filter by hand/source track/edited state, select the visible page or all matching notes, change individual hands or groups, undo recent changes, or restore suggestions. Export sends every current hand choice with the unchanged original file. The backend does not rerun the model on export; manual choices win.

Current input scope is a piano-only performance. All piano hand/voice tracks are included; there is no instrument-selection step. Declared percussion/non-piano arrangements receive a clear error, with no silent note removal. Acoustic/electric piano programs 0–5 are accepted; unspecified programs default to piano. Misdeclared or absent instrument information cannot prove the actual intended instrument. See D-12.

The browser keeps the file and edits in memory until a different file is imported or the page is reloaded. No localStorage, account, database, or persistent project saving is implemented. The Python service keeps the model in memory but does not retain MIDI sessions. Multipart request handling may use framework-managed temporary upload storage; no promise of zero temporary disk use is made. Responses use no-store. There are no third-party CDN assets or external AI calls.

Development bounds: request body 16 MiB (including multipart overhead), at most 20,000 paired notes, 100 visible notes per page, last 50 edit operations undoable. MAX_CONTENT_LENGTH and MAX_MIDI_NOTES are app configuration options. These are bounded-preview defaults, not approved production performance targets. Hand suggestions need review; model accuracy, label orientation/preprocessing parity, rights determination, and actual Synthesia behavior remain unverified.

The export layout follows the approved original-track split; it can show more than two Synthesia parts. Conservative ordering rejection can stop export of certain files. No playback, finger hints, iOS support, or offline Android promise was added.

## API contract

| Route | Input | Result |
| --- | --- | --- |
| POST /api/analyze | multipart MIDI file named midi | JSON notes with stable source IDs, pitch/channel/track/tick/duration/velocity and suggested hand; PPQ/source-track summaries |
| POST /api/export | same original MIDI + assignments JSON object mapping every note ID to LEFT/RIGHT | audio/midi attachment, only after serialized event validation |
| POST /midi-to-midi | legacy raw MIDI body | validated suggestion-only MIDI attachment |

400 identifies unreadable/missing input, malformed labels, incomplete choices, or the note cap; 413 is the body-size cap; 422 identifies unsupported MIDI or an unsafe split; 429 is the configured rate limit. Unexpected server errors use a generic JSON response and local server logging. Rate limits are process-local memory state, suitable for this preview only. Analyze/conversion custom limits are 2/minute and export is 30/minute; these override default limits. Other non-exempt routes use the existing 200/day and 50/hour defaults.

## Observed checks

- All **42 unittest methods passed** in the diagnostic environment with web dependencies. Nine web methods test analyze output, per-note/group manual correction, invariant-checked export, malformed input, configurable size/note bounds, active rate limiting, cached model, and the legacy conversion route.
- JavaScript syntax check passed using `Get-Content static/editor.js -Raw | node --check -` (the filename form encountered an environment path-permission error; stdin check succeeded).
- Actual browser: imported the bundled 69-note example through the original checkpoint; changed one hand; filtered pitch 70 (20 matches); selected all matches; assigned right (20 edits); undid to the single prior edit; assigned right again; export returned HTTP 200 and displayed the successful MIDI-check state.
- The browser download-event waiter timed out without issuing the POST. A direct button click then issued POST /api/export (HTTP 200) and showed the successful result. Automated file-path capture from that browser download was not obtained. Independent API export/reparse tests verify event invariants and hand routing.
- Responsive viewport checks at 1440×900 and 390×844: desktop controls visible; phone-sized document client width and scroll width both 375 CSS pixels (no horizontal page overflow). Group editing and undo also worked in the phone-sized view. This is viewport emulation, not an actual Android-device acceptance test.
- Desktop/mobile screenshots saved locally in output/editor-desktop.jpg and output/editor-mobile.jpg (ignored artifacts; not repository music/data).

Later real-file browser check: The Meadow imported 1,436 notes; the table rendered 100 per page. Selection across pages 1 and 2 retained 200 selected notes. Group-left assignment changed 84 suggestions; export returned HTTP 200 and the successful MIDI-check state. Phone-sized undo restored zero edits and reapplying restored 84 edits; page width remained 375/375 CSS pixels, and no browser console errors were observed. Screenshots were refreshed from this real-file flow. The server was restarted after the decoder/ordering changes.

Current combined suite: 56 passing methods. The documented requirements/web.txt was installed into the original clean core environment, and final verification is in latest-verification.json with resolved packages in web-environment.txt. The earlier 42-method result above records the first web slice. See REAL_MIDI_RESULTS.md for the four-file accuracy comparison and 11-file preservation checks.

Remaining quality gates: real device/browser matrix, licensed piece-level accuracy benchmark, scale/performance budgets, label/preprocessing validation, licensing review, and actual Synthesia import/hand/playback checks. No claim that the MVP or Phase 0 is fully passed.

## Branding and current acceptance status — 2026-11-15

User-supplied logo, black/gold/white theme, and approved tagline now identify the preview. Left/right labels remain explicit; these browser colors do not determine Synthesia part colors. Desktop Synthesia import/manual hands/demo-limited playback was observed (see SYNTHESIA_CHECK.md); full-song and licensed Android/iPad checks remain pending. All further features and production design remain on paper pending decisions.
