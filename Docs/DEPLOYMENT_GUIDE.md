# Deployment — Stabsspel

Produktion körs med **Gunicorn** mot `wsgi:app` (inte `app:app`). Python-versionen står i `runtime.txt` (**3.12.10**).

## Render.com

### 1. Web Service

1. [render.com](https://render.com) → **New +** → **Web Service**
2. Koppla GitHub-repot (`fredrikCarleson/stabsspel` eller din fork)
3. Inställningar:

```text
Build Command:  pip install -r requirements.txt
Start Command:  gunicorn wsgi:app --log-file -
```

(`Procfile` innehåller redan samma startkommando.)

### 2. Environment variables

```text
SECRET_KEY   # python -c "import secrets; print(secrets.token_hex(32))"
FLASK_ENV    production
```

Render sätter `PORT` själv. Gunicorn i `Procfile` läser den via plattformen; bind inte hårdkodat till 5000 i produktion.

### 3. Persistent disk för speldata (obligatoriskt)

`speldata/` är **gitignored**. Utan skrivbar persistent disk försvinner alla spel vid restart/deploy.

Montera en disk på t.ex. `/var/data` och peka appen dit, eller se till att processens arbetskatalog har en skrivbar `speldata/`-mapp som överlever deploys. Utan det är appen bara en tom skal efter varje ny build.

### 4. Verifiera

- `GET /health` → JSON med `"status": "healthy"`, `"version": "1.1"`
- `GET /` → startsida med spellista
- `GET /admin` → skapa spel / ladda upp JSON

## Lokal Gunicorn-test

```bash
venv\Scripts\activate
gunicorn wsgi:app --bind 0.0.0.0:5000
```

Vanlig utveckling: `python app.py` (debug-reload). Inte `flask app.py`.

## Felsökning

| Symptom | Kolla |
|---------|--------|
| ImportError | `requirements.txt` / venv |
| Sessioner dör / “lösenord krävs” hela tiden | `SECRET_KEY` saknas eller ändras mellan deploys |
| Spel försvinner | Ingen persistent `speldata/` |
| Debug på i prod | `FLASK_ENV` måste vara `production`; `wsgi.py` laddar `config.py` |

Loggar: Render Dashboard → Logs. I produktion skriver `config.py` även till `logs/stabsspel.log` om mappen kan skapas.

## Användning live

**Spelledare:** `/admin` skapa spel (eller `/` öppna ett befintligt) → lösenord → spelledarpanel. Öppna **Spelarskärm** till projektorn.

**Lag:** spelledaren delar team-sidan `/team/<id>/<lag>` (QR till orderformuläret). Spelare väljer inte lag på en öppen startsida.

**Ta bort spel:** **Ta bort** på `/` eller `/admin`, ange spellösenordet. Sidan byts inte till “Starta nytt spel”.
