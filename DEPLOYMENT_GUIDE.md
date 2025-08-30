# 🚀 Snabb Deployment Guide - Stabsspel v1.2

## 🌐 Render.com (Rekommenderat)

### Steg 1: Skapa konto
1. Gå till [render.com](https://render.com)
2. Skapa konto med GitHub

### Steg 2: Skapa Web Service
1. Klicka "New +" → "Web Service"
2. Välj GitHub repository: `fredrikCarleson/stabsspel`
3. Namn: `stabsspel` (eller valfritt)

### Steg 3: Konfiguration
```
Build Command: pip install -r requirements.txt
Start Command: gunicorn wsgi:app
```

### Steg 4: Environment Variables
Lägg till dessa variabler:
```
SECRET_KEY: [generera med: python -c "import secrets; print(secrets.token_hex(32))"]
FLASK_ENV: production
```

### Steg 5: Deploy
1. Klicka "Create Web Service"
2. Vänta på att bygget slutförs
3. Din app är live på: `https://stabsspel.onrender.com`

## 🔧 Lokal Testning

### Testa med Gunicorn
```bash
# Aktivera venv
venv\Scripts\activate

# Testa lokalt
gunicorn wsgi:app --bind 0.0.0.0:5000
```

### Testa Health Check
```bash
curl http://localhost:5000/health
```

## 📊 Verifiering

### Kontrollera att allt fungerar:
1. **Health Check**: `https://din-app.onrender.com/health`
2. **Huvudsida**: `https://din-app.onrender.com/`
3. **Admin Panel**: `https://din-app.onrender.com/admin`

### Förväntad respons:
```json
{
  "status": "healthy",
  "service": "Stabsspel", 
  "version": "1.2",
  "timestamp": 1234567890
}
```

## 🚨 Felsökning

### Vanliga problem:
1. **Import Error**: Kontrollera requirements.txt
2. **Port Error**: Render sätter PORT automatiskt
3. **Secret Key**: Måste vara satt för produktion

### Loggar:
- Render Dashboard → Logs
- Eller: `render logs stabsspel`

## 🔄 Uppdateringar

### Automatisk deployment:
1. Push till GitHub main branch
2. Render deployar automatiskt
3. Verifiera funktionalitet

### Manuell deployment:
1. Render Dashboard → Manual Deploy
2. Välj branch/commit
3. Klicka "Deploy"

## 📱 Användning

### För spelledare:
1. Gå till admin panel
2. Skapa nytt spel
3. Konfigurera lag och tider
4. Starta spelet

### För spelare:
1. Få länk från spelledare
2. Välj lag
3. Skicka in order
4. Följ timer

## 🎉 Klart!

Din Stabsspel-app är nu live och redo för användning! 🚀
