# Orderkort-funktionalitet för Stabsspelet

## Översikt

Denna funktionalitet låter dig skriva ut strukturerade orderkort för alla team för varje runda i spelet. Orderkorten baseras på mallen från bilden och ger tillräckligt med plats för att skriva flera meningar om aktiviteter, syften och kommentarer.

## Funktioner

### 🎯 Strukturerade Orderkort
- **Ett A4 per runda** - Varje runda får sina egna orderkort
- **Ett kort per team** - Alla team i spelet får sina egna orderkort
- **Utökad skrivyta** - Mer plats för aktiviteter, syften och kommentarer
- **Utskriftsvänlig** - Optimerad för utskrift med sidbrytningar

### 📋 Orderkortets struktur

#### Övre del (identitet)
- **Team**: Teamets namn
- **Runda**: Aktuell rundanummer
- **Max handlingspoäng**: Teamets max handlingspoäng
- **Totalt satsade HP**: Tomt fält för att fylla i

#### Ordertabell (max 6 rader)
Varje rad innehåller:
- **Nr**: Radnummer (1-6)
- **Aktivitet (Vad?)**: Textfält för att beskriva aktiviteten
- **Syfte/Mål (Varför?)**: Textfält för att förklara syftet
- **Målområde 🎯**: Kryssrutor för "Eget mål" eller "Annat mål"
- **Påverkar/Vem**: Lista med alla team + textfält
- **Typ av handling ⚔️**: Kryssrutor för "Bygga/Förstärka" eller "Förstöra/Störa"
- **HP**: Numeriskt fält för handlingspoäng

#### Fältens funktion
Förklaringar av vad varje fält betyder och hur det ska användas.

## Användning

### Via webbgränssnittet

1. **Öppna admin-panelen** för ett spel
2. **Klicka på "Skriv ut orderkort"** knappen
3. **Välj runda** från listan med tillgängliga rundor
4. **Skriv ut** orderkorten för alla team

### Via API

```python
from orderkort import generate_orderkort_html, get_available_rounds

# Hämta tillgängliga rundor för ett spel
available_rounds = get_available_rounds("spel_id")

# Generera orderkort för en specifik runda
html = generate_orderkort_html("spel_id", 1)
```

## Teknisk implementation

### Filer
- `orderkort.py` - Huvudmodul för orderkort-funktionalitet
- `admin_routes.py` - Webbgränssnitt för orderkort
- `test_orderkort.py` - Test-fil för att demonstrera funktionaliteten

### Funktioner

#### `generate_orderkort_html(spel_id, runda)`
Genererar HTML för orderkort för alla team för en specifik runda.

**Parametrar:**
- `spel_id` (str): Spel-ID
- `runda` (int): Rundanummer

**Returvärde:**
- `str`: HTML-kod för orderkorten

#### `get_available_rounds(spel_id)`
Hämtar tillgängliga rundor för ett spel.

**Parametrar:**
- `spel_id` (str): Spel-ID

**Returvärde:**
- `list`: Lista med rundonummer

### CSS-styling
Orderkorten använder responsiv CSS med:
- **Print-optimering** - Sidbrytningar och utskriftsvänlig layout
- **A4-format** - 21cm x 29.7cm
- **Flexibla textfält** - Tillräckligt med plats för flera meningar
- **Tydlig typografi** - Lättläst för utskrift

## Fördelar jämfört med originalmallen

1. **Mer skrivyta** - Textfält istället för korta rader
2. **Digital hantering** - Kan skrivas ut när som helst
3. **Automatisk teamdata** - Teamnamn och handlingspoäng hämtas från spelet
4. **Flexibel struktur** - Kan anpassas efter behov
5. **Utskriftsvänlig** - Optimerad för A4-utskrift

## Framtida förbättringar

- **Spara orderdata** - Möjlighet att spara ifyllda orderkort
- **Digitala formulär** - Interaktiva formulär som kan fyllas i digitalt
- **Export-funktioner** - Exportera till PDF eller andra format
- **Anpassningsbara mallar** - Olika mallar för olika typer av spel

## Testning

Kör test-filen för att se funktionaliteten i aktion:

```bash
python test_orderkort.py
```

Detta genererar en `test_orderkort.html` fil som du kan öppna i en webbläsare för att se hur orderkorten ser ut.
