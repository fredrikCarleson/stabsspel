# Utskrivbara orderkort

Papperskort för lag som fyller i för hand. Den **digitala** orderinmatningen är en annan sak: QR från team-sidan → `/team/<spel_id>/<token>/enter_order`.

## Var man hittar dem

| Vem | Väg |
|-----|-----|
| Lag | Team-sidan `/team/<spel_id>/<lag>` → **Skriv ut orderkort** (`/team/<spel_id>/<lag>/orderkort`) |
| Spelledare | Direkt-URL `/admin/<spel_id>/orderkort` → välj runda → `/admin/<spel_id>/orderkort/<runda>` |

Spelledarpanelens **Meny** länkar till aktivitetskort och LLM-export, inte till orderkort. Använd URL:en ovan eller lagets utskriftslänk.

## Vad ett kort innehåller

Per lag och runda (A4, utskrifts-CSS i själva HTML:en från `orderkort.py`):

- Team, runda, max handlingspoäng
- Tabell (upp till 6 rader): aktivitet, syfte, målområde, påverkar, typ av handling, HP
- Tomt fält för satsade HP

## Kod

| Fil | Roll |
|-----|------|
| `orderkort.py` | `generate_orderkort_html(spel_id, runda)`, `generate_team_orderkort_html(spel_id, team_name)`, `get_available_rounds(spel_id)` |
| `admin_routes.py` | `/admin/<id>/orderkort` och `/admin/<id>/orderkort/<runda>` |
| `team_routes.py` | `/team/<id>/<lag>/orderkort` |

Exempel:

```python
from orderkort import generate_orderkort_html, get_available_rounds

get_available_rounds("20260817120000")
html = generate_orderkort_html("20260817120000", 1)
```

Det finns **ingen** `test_orderkort.py` i repot. Öppna utskrifts-URL:en i webbläsaren och skriv ut därifrån.
