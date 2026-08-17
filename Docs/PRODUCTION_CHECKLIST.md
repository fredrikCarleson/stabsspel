# Production checklist — Stabsspel

Use this before a live event on a host (Render or similar). Unchecked items are for you to confirm on *that* environment; the code already has the hooks.

## Code (in this repo)

- [x] Production entry is `wsgi:app` (`Procfile`: `gunicorn wsgi:app --log-file -`)
- [x] `runtime.txt` pins Python 3.12.10
- [x] `SECRET_KEY` is read from the environment (`config.py`); do not ship with the dev fallback
- [x] `FLASK_ENV=production` loads `ProductionConfig` (debug off, secure cookies)
- [x] `/health` returns JSON (`version` is currently `"1.1"`)
- [x] Game files live in `speldata/` and are gitignored
- [x] Domain tests: `python -m unittest tests.test_domain tests.test_gm_console tests.test_admin_helpers`

## On the host (you must set these)

- [ ] `SECRET_KEY` set to a long random value and **stable across deploys** (changing it logs everyone out)
- [ ] `FLASK_ENV=production`
- [ ] Start command is `gunicorn wsgi:app --log-file -` (not `gunicorn app:app`)
- [ ] **Writable persistent disk** for `speldata/` so games survive restart and deploy
- [ ] `logs/` writable if you want the rotating file log from `config.py`
- [ ] `GET /health` returns 200
- [ ] Create a test game, open spelledarpanel, open `/spelarskarm/<id>`, delete the test game with the password modal

## Optional platforms

Same env vars everywhere. Render is the documented path. Heroku/Railway work if they can run the Procfile and attach a disk for `speldata/`.

## Debug locally as production

```bash
# Windows PowerShell
$env:FLASK_ENV="production"
$env:SECRET_KEY="temporary-local-key"
gunicorn wsgi:app --bind 0.0.0.0:5000
```

```bash
# macOS / Linux
FLASK_ENV=production SECRET_KEY=temporary-local-key gunicorn wsgi:app --bind 0.0.0.0:5000
```

Do not use `python wsgi.py` as the production mental model; Gunicorn is what Render runs.

## After deploy

1. Push `main` (or manual deploy)
2. Hit `/health`, `/`, `/admin`
3. Confirm an old game JSON is still on disk
4. Keep Testläge **off** when a room can see the GM screen
