# LLM-flöde i Stabsspel

Det här dokumentet beskriver hur spelledaren tar rundans ordrar till en LLM, hur svaret tolkas, och vad som sedan händer med HP, backlog, nyheter och rummet.

Det är inte spelreglerna (se [Stabsspel Traineeprogrammet.md](Stabsspel%20Traineeprogrammet.md)) och inte en kopia av prompttexten (se [prompt.md](prompt.md)). Programkartan ligger i [architecture.md](architecture.md).

---

## Vad LLM är och inte är

Appen anropar ingen modell. Spelledaren kopierar ett färdigt underlag, klistrar in det i en chat utanför spelet, och klistrar tillbaka **endast JSON**.

LLM:en ska:

- avgöra vilka ordrar som är osäkra och därför hör hemma i `utfall`
- återanvända appens låsta slumpvärden (1–100) när den faktiskt slumpar
- föreslå nyheter som kan läsas i studion
- föreslå HP-delta för **nästa rundas kassa**
- föreslå milstolpeprogress på Teamens arbete

LLM:en ska inte:

- slå tärningen själv eller hitta på nya `order_ref`
- skriva `utfall` för vanligt backlog-arbete (det är deterministisk progress)
- flytta HP automatiskt — spelledaren måste **Tillämpa HP**
- publicera nyheter på spelarskärmen — de kopieras till papper

## Invariants

Bryt inte dessa utan en uttrycklig mekanikändring.

- Varje inskickad `order_ref` får ett låst D100. Det kräver inte `utfall`.
- Vanligt backlog-arbete är deterministisk progress (`milstolpar`), inte ett slag.
- Import av `utfall` ändrar aldrig kassa-HP eller backlog.
- `hp[]` är nästa rundas kassa, och bara efter **Tillämpa HP**.
- `milstolpar[]` är backlog-progress nu, efter **Tillämpa milstolpar** (eller Inkorg).
- `build_public_state` får inte innehålla ordrar, slag, sannolikheter, `utfall`, `llm_forslag` eller `llm_resolution`.
- Omimport får inte återaktivera HP eller milstolpar som redan är tillämpade den här rundan.
- Ångra får inte skapa nya tärningsslag. Låsta slag ligger kvar.
- Regeringsstöd är inte överförbar kassa-HP.
- Ett lyckat `utfall` skapar inte en `hp`-rad av sig själv.

---

## Tre olika HP-begrepp

De blandas lätt. Spelet behandlar dem som tre mekanismer.

| Begrepp | Vad det är | Var det syns | När det ändrar kassan |
|---------|------------|--------------|------------------------|
| **Satsad HP** | Hur mycket ordern satte mot motståndet (`satsad_hp` mot `motstand_hp` i `utfall`) | GM-kort i **LLM-resultat** | Aldrig. Det är insats, inte delta. |
| **Kassa-HP** | Lagets `poang.<lag>.aktuell` | Lag-fliken, spelarskärmen | LLM: efter **Tillämpa HP**, först när **Starta nästa runda** körs. GM ± i Orderfas: direkt. |
| **Backlog-HP** | `spenderade_hp` på en uppgift i Teamens arbete | **Arbete**, ibland Inkorg | Direkt vid **Tillämpa milstolpar** eller när GM lägger HP i Inkorg. Påverkar inte kassan. |

Ett lyckat utfall (FRAMGÅNG) skapar **inte** automatiskt ett HP-delta. Om kassan ska ändras måste LLM:en skriva en rad i `hp[]`, och spelledaren måste tillämpa den.

---

## Flöde steg för steg

```
Diplomatifas eller Resultatfas
        │
        ▼
Kopiera till LLM  →  /admin/<id>/order_summary
        │                 fyller Docs/prompt.md
        │                 låser 1–100 per inskickad order
        ▼
Spelledaren klistrar in texten i en LLM utanför appen
        │
        ▼
Klistra in JSON på samma sida (eller ladda upp fil)
        │
        ├─ ogiltig JSON  →  stannar på export-sidan med rad, utdrag och hint
        └─ giltig JSON   →  spelledarpanelen, fliken LLM-resultat
                │
                ├── Nyheter     → kopiera till papper → studio
                ├── Utfall      → GM-kort (chans → slag → utfall). Ingen auto-HP.
                ├── HP          → Tillämpa HP → hp_pending → nästa runda
                └── Milstolpar  → Tillämpa milstolpar → backlog nu
```

Kopiera-steget är tillgängligt från LLM-statusraden (**Kopiera till LLM** / **Öppna LLM-underlag**) och från **Meny → LLM-export**.

---

## Hur underlaget skapas

Funktion: `build_llm_export_text` i `gm_console.py`. Sidan: `GET /admin/<id>/order_summary`.

Mallen är `Docs/prompt.md`. Appen ersätter platshållarna med den här rundans data:

| Platshållare | Innehåll |
|--------------|----------|
| `{LAGLISTA}` | Lagnamn i spelet |
| `{RUNDA}` | Aktuell runda |
| `{FAS}` | Aktuell fas |
| `{BACKLOG}` | Teamens arbete: id, namn, lagd HP / estimat, status. Bravo-faser som `id_Fasnamn`. |
| `{ORDRAR}` | Inskickade ordrar per lag, med `order_ref` (t.ex. `FM-1`), typ BYGGA/FÖRSTÖRA, HP, syfte, backlog-id, påverkar, målområde. Kassan per lag står i rubriken. |
| `{SLUMPVARDEN}` | Ett heltal 1–100 per inskickad `order_ref`. Texten säger att slumpvärdets existens **inte** betyder att ordern måste slumpas. |
| `{TIDIGARE_UTFALL}` | Sparade `utfall` från tidigare rundor, eller `(Inga tidigare utfall)`. |

### Slumpvärden

`ensure_round_rolls` skapar saknade slag när underlaget byggs och sparar dem i `llm_resolution.<runda>.rolls`.

- Ett värde per inskickad `order_ref`.
- Befintliga värden slås **aldrig om**. Ångra rullar inte tärningen.
- Oanvända slag är tillåtna. Vanligt backlog-arbete ska inte få `utfall`.
- LLM:en får inte hitta på nya tal. Importen avvisar ett `utfall` vars `slump` inte matchar det låsta värdet.

Utkast (oskickade ordrar) ingår inte. Bara `final`-ordrar får `order_ref` och slag.

Lägg inte in live-slag i `prompt.md`. Filen är mallen; rundan fylls vid kopiering.

---

## Hur svaret tolkas

Funktioner: `parse_llm_forslag`, `parse_utfall_items`, `import_llm_forslag`. Route: `POST /admin/<id>/llm_import`.

Förväntad toppnivå (schema i slutet av `prompt.md`):

```json
{
  "runda": 1,
  "utfall": [],
  "nyheter": [],
  "hp": [],
  "milstolpar": []
}
```

Importen tar bara JSON. Ett yttre markdown-staket (```json … ```) strippas. Förklarande text före eller efter objektet är ett fel.

Alias som också läses, så äldre svar fungerar:

| Fält | Alias |
|------|--------|
| `nyheter` | `news` |
| `hp` | `hp_justeringar` |
| `milstolpar` | `milestones`, `backlog` |
| `rubrik` | `headline` |
| `upplasning` | `text`, `lasning` |
| `lag` | `team` / `teams` |
| `orsak` | `reason` |
| milstolpe-id | `uppgift`, `id`, `task` |
| milstolpe-HP | `delta_hp`, `hp` |

Runda i JSON:en jämförs med spelets runda. Fel runda ger en **varning**, inte avvisning. Spelets runda vinner.

### `utfall` — strikt

Tom lista eller saknad nyckel är tillåtet. Inte varje order behöver ett utfall.

Om listan har objekt måste **varje** objekt vara giltigt, annars avvisas hela importen. Krävda fält: `lag`, `order_ref`, `order`, `satsad_hp`, `motstand_hp`, `sannolikhet` (10–90), `slump` (1–100, måste matcha låst slag), `resultat` (`framgång` / `delvis framgång` / `misslyckande`), `motivering`. `delmal` är valfritt när bara en del av ordern slumpas.

`order_ref` måste tillhöra en inskickad order den här rundan, och `lag` måste vara det laget.

### `nyheter`, `hp`, `milstolpar` — milt

Okända lag hoppas över. `hp` med `delta` 0 hoppas över. Negativ milstolpe-HP importeras inte. För stor milstolpe-HP kläms till återstående arbete på uppgiften, med varning.

### Omimport

En ny import **återaktiverar inte** HP eller milstolpar som redan är tillämpade den här rundan. De tillämpade listorna behålls; en varning förklarar att spelledaren måste ångra först för att ändra dem. Ångra är den avsiktliga revisionsvägen.

---

## Vad som händer i spelet

Importen skriver `llm_forslag.<runda>` och, om `utfall` fanns, `llm_resolution.<runda>.result`. Ingenting i rummet ändras av importen ensam.

### Nyheter

Visas i **LLM-resultat** med rubrik, uppläsning och valfria lagnamn. **Kopiera nyheter till papper** lägger texten på urklipp.

`lag` på en nyhet är spelledarmetadata (vilka lag som berörs), inte en publik märkning. Nyheterna går **inte** till spelarskärmen. Studion läser papper.

### Utfall

GM-kort: lag, ordernummer, text, `satsad HP mot motstånd HP`, sedan **Chans → Slag → Utfall** och motivering. Valfritt `delmal` under ordern.

Korten är bara för spelledaren. Inga tärningsslag, sannolikheter eller `order_ref` skickas till projektorn. Ett utfall ändrar varken kassa eller backlog.

### HP (kassa)

Knappen **Tillämpa HP** (`apply_llm_hp`) köar varje rad i `hp[]` via `queue_hp_delta` (`kalla`: `llm`). `aktuell` ändras inte ännu. Loggen: *Schemalade N HP-justeringar till nästa runda*. Flaggan `hp_applied` sätts så knappen inte kan tryckas om.

When spelledaren kör **Starta nästa runda** (`apply_new_round`), eller **Avsluta spelet** efter sista rundan (`end_game`):

1. `nollstall_regeringsstod`
2. `snapshot_backlog_round` — sparar `tidigare_hp` för progressstaplar (endast ny runda)
3. `apply_pending_hp` — skriver kön till `aktuell`, klämd vid 0

Sista rundans HP-delta ska alltså synas i den avslutade kassan, inte bara som en prognos. `end_game` tar inte en ny runda och snapshot:ar inte backloggen.

GM ± i Diplomatifas/Resultatfas köas på samma sätt. GM ± i Orderfas ändrar den här rundan direkt. Överföringar är alltid direkta (utan stöd).

I Resultatfas visar Lag-fliken **Nästa runda ±N**. Projektorn visar **Denna runda → Nästa runda**. Nästa värde är kassan efter kön, **utan** regeringsstöd (stödet nollställs innan kön tillämpas).

**Äldre sparningar:** en tidigare **Tillämpa HP** skrev deltat rakt in i `aktuell` och lämnade `hp_pending` tom. Då räknar `next_round_hp_view` baklänges från den tillämpade `hp`-listan så rummet inte ser *Oförändrat*. Nya spel ska inte hamna där.

### Milstolpar (Teamens arbete)

**Tillämpa milstolpar** (`apply_llm_milestones`) lägger `delta_hp` på backlog **nu** (`add_backlog_spend`). Det är progress, inte kassa. FÖRSTÖRA-ordrar ska inte få milstolpeprogress (promptregeln; appen litar på att svaret följer den).

Samma progress kan också läggas manuellt i **Inkorg**. Om Inkorg redan har hanterat alla föreslagna milstolpar räknas de som klara (`milestones_applied_via`: `inbox`) och LLM-knappen ska inte dubbelräkna. Delvis hanterat i Inkorg blockerar LLM-tillämpning tills spelledaren slutförr eller ångrar.

---

## Vad rummet ser

`build_public_state` är den enda projektorsnappen. Den innehåller runda, fas, tid, publik HP, stöd-flagga, backlog-progress, och i Resultatfas `next_hp` / `next_delta`. Projektorn visar timerstatus på svenska och **en stapel per lag** (procent och lagd/estimerad HP), inte uppgiftsnamn.

Den innehåller **inte** inbox, händelselogg, testläge, ordrar, `llm_forslag`, `llm_resolution`, slag, sannolikheter, utfall eller nyheter.

Resultatfasen är fortfarande den här rundan. Jämförelsen denna → nästa är en **prognos** efter att spelledaren tillämpat HP, inte ett facit som spelet redan har bytt till.

---

## Vad som inte händer automatiskt

- Import flyttar inte HP och lägger inte backlog.
- FRAMGÅNG i `utfall` skapar inte en `hp`-rad.
- Tom `hp`-lista betyder *ingen kassaförändring*, även om utfallen är dramatiska.
- Nyheter publiceras inte digitalt.
- Oanvända slumpvärden tvingar inte fram utfall.
- Ångra tar tillbaka tillämpad HP/milstolpe, men rullar inte om tärningen.

---

## Filer

| Fil | Roll |
|-----|------|
| `Docs/prompt.md` | Instruktionstext och JSON-schema. Fylls vid export. Ändra den här om LLM:en ska tänka annorlunda. |
| `Docs/LLM_WORKFLOW.md` | Det här dokumentet. |
| `gm_console.py` | `build_llm_export_text`, `ensure_round_rolls`, `parse_llm_forslag`, `import_llm_forslag`, `apply_llm_hp`, `apply_llm_milestones`, `next_round_hp_view`, `build_public_state` |
| `gm_console_ui.py` | LLM-statusrad, fliken LLM-resultat, utfallskort, projektor-jämförelse |
| `admin_routes.py` | `/order_summary`, `POST /llm_import`, `POST /llm_apply` |
| `testdata/llm-svar-exempel.json` | Exempelsvar utan utfall |
| `testdata/llm-svar-utfall-exempel.json` | Exempelsvar med utfall |
| `tests/test_domain.py` | Export, parse, köad HP, projektorprognos |
| `tests/test_gm_console.py` | GM-flikar, utfall bara hos spelledaren, projektor denna/nästa |

Exempelfilerna är testdata, inte live-rundor. Byt inte `prompt.md` mot ett ifyllt underlag från ett pågående spel.
