# Stabsspelet — krisledningssimulation

Digital spelledarhjälp för **Stabsspel Traineeprogrammet**: fyra rundor med Orderfas → Diplomatifas → Resultatfas, lag, handlingspoäng och en projektor till salen.

Nyheter skrivs fortfarande på papper och läses i TV-studion. Spelledaren kopierar ordrar till en LLM tillsammans med appens tärningsslag (1–100 per inskickad order), klistrar in JSON-svaret och kan då se utfall, nyhetsförslag samt föreslagen HP/milstolpe-progress. Projektor och spelare ser inte slagen eller sannolikheterna. Appens jobb i övrigt är klocka, ordrar, HP och backlog.

## Lokal utveckling

Kräver **Python 3.12**. Kör inte `flask app.py` — det är inte ett Flask-kommando.

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

Öppna http://localhost:5000

- **`/`** — befintliga spel (öppna, ladda ner, ta bort)
- **`/admin`** — skapa nytt spel eller ladda upp en JSON-backup
- **`/admin/<spel_id>`** — spelledarpanel (lösenord)
- **`/spelarskarm/<spel_id>`** — projektor till salen (ingen inloggning)

Lämna spellösenordet tomt vid skapande för att använda standardlösenordet (`models.get_default_password()`). **Ta bort** frågar efter samma lösenord och stannar på sidan när spelet är borta.

## Dokumentation

| Fil | Innehåll |
|-----|----------|
| [Docs/Stabsspel Traineeprogrammet.md](Docs/Stabsspel%20Traineeprogrammet.md) | Spelet: regler, lag, HP, rundor |
| [Docs/architecture.md](Docs/architecture.md) | Koden: mappar, routes, live-event |
| [Docs/LLM_WORKFLOW.md](Docs/LLM_WORKFLOW.md) | Hur LLM-underlag skapas, JSON tolkas och HP/nyheter/backlog påverkas |
| [Docs/prompt.md](Docs/prompt.md) | LLM-exportens instruktioner (fylls med rundans order och slag) |
| [Docs/UX_CONSOLE_REWORK.md](Docs/UX_CONSOLE_REWORK.md) | UX-arbetslogg (inte nuvarande UI-spec) |
| [Docs/DEPLOYMENT_GUIDE.md](Docs/DEPLOYMENT_GUIDE.md) | Render / produktion |
| [Docs/PRODUCTION_CHECKLIST.md](Docs/PRODUCTION_CHECKLIST.md) | Go-live-checklista |
| [Docs/ORDERKORT_README.md](Docs/ORDERKORT_README.md) | Utskrivbara pappersorderkort |

## Produktion (kort)

Startkommando (står redan i `Procfile`):

```text
gunicorn wsgi:app --log-file -
```

Sätt `SECRET_KEY` och `FLASK_ENV=production`. **`speldata/` måste vara skrivbar persistent disk** — den ligger inte i git, så utan disk försvinner spelen vid varje deploy. Detaljer i [Docs/DEPLOYMENT_GUIDE.md](Docs/DEPLOYMENT_GUIDE.md).

Health check: `GET /health` (version i svaret är `1.1`).

## Tester

```bash
python -m unittest tests.test_domain tests.test_gm_console tests.test_admin_helpers
```

## Bakgrundsbilder

Lägg bilder i `static/backgrounds/`. De serveras som `/static/backgrounds/<filnamn>`.

## Licens

[GNU GPL v3](LICENSE)
