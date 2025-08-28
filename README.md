# Stabsspelet - Krisledningssimulation

En avancerad krisledningssimulation för att träna beslutsfattande under press.

## Funktioner

- ⚡ Snabb beslutsfattande under tidspress
- 👥 Team-samarbete med olika roller
- 📊 Handlingspoäng-system
- ⏰ Tidsbegränsade faser
- 🎯 Målbaserat spel
- 📈 Progressiv svårighet

## Lokal utveckling

1. Skapa en virtuell miljö:
```bash
python -m venv venv
source venv/bin/activate  # På Windows: venv\Scripts\activate
```

2. Installera beroenden:
```bash
pip install -r requirements.txt
```

3. Kör applikationen:
```bash
python app.py
```

4. Öppna http://localhost:5000 i din webbläsare

## Deployment på Render

### Steg 1: Förbered din kod
Se till att du har följande filer i din repository:
- `requirements.txt`
- `Procfile`
- `runtime.txt`
- `app.py`

### Steg 2: Skapa en Render-konto
1. Gå till [render.com](https://render.com)
2. Skapa ett konto eller logga in
3. Koppla ditt GitHub-konto

### Steg 3: Skapa en ny Web Service
1. Klicka på "New +" i Render dashboard
2. Välj "Web Service"
3. Koppla till din GitHub repository
4. Konfigurera följande inställningar:

**Grundläggande inställningar:**
- **Name:** stabsspelet (eller valfritt namn)
- **Environment:** Python 3
- **Region:** Välj närmaste region
- **Branch:** main (eller din huvudbranch)

**Build & Deploy inställningar:**
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`

**Environment Variables:**
- `SECRET_KEY`: En säker slumpmässig sträng (t.ex. genererad med Python: `import secrets; secrets.token_hex(16)`)

### Steg 4: Deploy
1. Klicka på "Create Web Service"
2. Render kommer automatiskt att bygga och deploya din app
3. Vänta tills deployment är klar (grön status)

### Steg 5: Testa din app
1. Klicka på den genererade URL:en
2. Din app ska nu vara live!

## Miljövariabler

För produktion, sätt följande miljövariabler i Render:

- `SECRET_KEY`: En säker slumpmässig sträng för Flask sessions
- `FLASK_ENV`: Sätt till `production` för produktion

## Filstruktur

```
Stabsspel/
├── app.py                 # Huvudapplikation
├── admin_routes.py        # Admin-routes
├── team_routes.py         # Team-routes
├── models.py              # Spellogik och data
├── game_management.py     # Spelhantering
├── requirements.txt       # Python-beroenden
├── Procfile              # Render deployment
├── runtime.txt           # Python-version
├── static/               # Statiska filer
│   ├── style.css
│   └── alarm.mp3
├── teambeskrivning/      # Team-beskrivningar
└── speldata/             # Speldata (skapas automatiskt)
```

## Support

För frågor eller problem med deployment, kontakta utvecklaren eller skapa en issue i repository.

## Licens

Se LICENSE-filen för mer information.
