# Stabsspelet — krisledningssimulation

Digital spelledarhjälp för **Stabsspel Traineeprogrammet**: fyra rundor med Orderfas → Diplomatifas → Resultatfas, lag, handlingspoäng och en projektor till salen.

Nyheter skrivs fortfarande utanför appen (kopiera ordrar till en LLM, papper, nyhetsstudio). Appens jobb är klocka, ordrar, HP och backlog.

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
