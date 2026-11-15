# Hosting HandJob

## Diagnosis — 2026-11-15

The app is Python Flask, Jinja (`templates/index.html`), plain JavaScript and CSS
(`static/`), and server-side PyTorch inference. There is no package.json, Node
build, dist directory, or tracked GitHub Actions deployment workflow at
60f07b409b61eb654ed51ebe8fb37c007eef722c. The page is rendered by GET / in
server.py; MIDI processing requires POST /api/analyze and POST /api/export.

GitHub Pages serves static files; it cannot run this Python service or its model.
Publishing repository source is not deploying the application. The reported
README page is consistent with Pages rendering repository Markdown rather than
running Flask. The exact Pages source branch/folder remains unverified: the
unauthenticated Pages API returned 404, which does not establish that Pages is
disabled. The connector returned no workflow runs for the current commit.

Do not delete README, move the Jinja template to the root, or add a Vite base
setting. Those changes cannot supply the missing Python runtime. A Pages workflow
that uploads templates or static assets alone would leave MIDI processing broken.

## Recommended deployment: one Python service

Keep the existing frontend and backend together on a Python-capable host or
container service, behind HTTPS. This needs no application rewrite and no CORS.

1. Deploy only the authorized fork, shimuranmonk/hand-job, using a reviewed commit.
2. Install requirements/web.txt in an isolated Python environment. The existing
   observed environment is Windows x64 / CPython 3.13; validate package and CPU
   PyTorch wheel availability on the chosen host before committing to it.
3. Include templates/, static/, example/checkpoint.pth, and the imported Python
   modules. Keep the checkpoint path unchanged.
4. Use a production WSGI server targeting server:app. For example, on Linux with
   Gunicorn separately installed, a candidate start command is
   `gunicorn --bind 0.0.0.0:$PORT --workers 1 server:app`. This command is a proposed
   deployment configuration, not a tested Linux deployment. Do not expose the
   Flask development server or the current localhost preview to the Internet.
5. Serve the application at the service domain root: /, /static/*, and /api/*.
   The existing root-relative API requests then work without a /hand-job/ prefix.
6. Before public use, measure model RAM, cold start and representative processing
   time; set request/time limits accordingly. Decide access controls, upload and
   temporary-storage policy, proxy-aware rate limiting and logging. Current
   rate-limit storage is process-local; multiple workers need a shared strategy.
   Recheck software/checkpoint licensing before public or commercial deployment.
7. Verify HTTPS home/assets, analyze a piano MIDI, correct notes, export and
   independently check the MIDI; verify invalid input and limits. Test on Android.

No paid service, hosting account, public exposure, or production readiness is
approved or claimed by this diagnostic. Choose a host and deployment policy
before creating external resources. The resulting app URL will be the Python
service's HTTPS URL; no such URL has been provisioned yet.

## If keeping GitHub Pages

The Pages URL https://shimuranmonk.github.io/hand-job/ can remain documentation
and later link or redirect to the deployed Python service. Do not invent that
target URL. Alternatively, a separate static frontend could call an HTTPS Python
backend, but that requires explicitly implementing an API origin, restricted
CORS, error handling, and a static render step for the current Jinja template.
All Pages asset URLs must then resolve under /hand-job/; root-relative /api/*
would incorrectly call shimuranmonk.github.io. This is a larger architecture
change and is unnecessary for the recommended same-origin deployment.

## Observed validation

In the existing .inference-venv, all 10 test_web_api.py tests passed on
2026-11-15. These cover the rendered homepage, analyze, corrections/export,
validation, limits, model caching, and legacy conversion. No static build applies.
These are local tests, not evidence of a successful hosted deployment.
