# Playtest: utökat spel utan SÄPO och USA

Datum: 2026-09-05  
Roster: **Alfa, Bravo, STT, FM, BS, Media, Regeringen** (7 lag)  
Frånvarande: **SÄPO, USA**

**Status 2026-09-05:** Buggarna i avsnittet *Buggar som bör fixas* (orderkort HP, Påverkar-kryssrutor, Auto-fyll mot frånvarande lag) är åtgärdade i koden. Det frysta sjulags-LLM-året ligger i `testdata/scenario_llm_7lag/` (`python tests/scenario_runner.py seven`). Resten av rapporten är oförändrad som playtestlogg.

Syftet var att köra ett helt år (fyra rundor) mot den nya valbara laguppsättningen, inte mot det gamla 9-lagsscenariot.

## Hur testet kördes

- Befintlig svit: `python -m unittest tests.test_domain tests.test_gm_console tests.test_admin_helpers tests.test_scenario_playthrough tests.test_live_routes` — **187 tester, alla gröna**.
- In-memory simulering av fyra rundor: skapa spel med `spellage=extended` och `extra_lag=["Media","Regeringen"]`, Auto-fyll från `testdata/testdataroundN.json`, fasbyte, låsta D100, LLM-export, import, Tillämpa HP/milstolpar, nästa runda / avsluta.
- HTTP mot Flask test client (tillfällig katalog, inget skrivet under `speldata/`): skapa spel, GM-konsol, `/live`, spelarskärm, briefs, orderformulär, aktivitetskort, LLM-export, orderkort.
- Befintliga `testdata/scenario_llm/rundaN.json` är skrivna för **nio lag**. De användes bara för att se vad som händer om man klistrar in dem i ett sjulagsspel. De är inte en giltig story för den här rosteren.

---

## Vad som fungerade bra

**Lagurvalet håller i state.** Ett nytt utökat spel med Media + Regeringen sparar exakt sju namn i `lag`, `poang` och `team_tokens`. SÄPO och USA finns varken som kassa, token eller URL. HP följer utökad katalog: STT 30, FM/BS 10, Media/Regeringen 12, Alfa/Bravo 25.

**Liveytorna filtrerar roster.** GM-konsol, live-JSON, överföringsrullgardin, projektor och publik HP visar bara de sju lagen. `/team/<id>/SÄPO` och `/team/<id>/USA` svarar 404: *Laget ingår inte i det här spelet.* Orderformulärets `ACTIVE_TEAMS` / `GRANT_TEAMS` innehåller inte de frånvarande lagen. Regeringen kan bara fördela till aktiva lag.

**LLM-exporten följer roster.** Underlaget listar `Alfa, Bravo, STT, FM, BS, Media, Regeringen` och har inga `=== LAG SÄPO` / `=== LAG USA`-block. HP-rader för inaktiva lag hoppas över. Utfall för ett frånvarande lag avvisar hela importen (`Okänt lag i utfall: SÄPO.`), vilket är rätt för att inte tysta släppa in spökorder.

**Aktivitetskorten anpassas.** Utskriften har inga rubriker för SÄPO eller USA. STT:s *Säkerhetsväktaren* pekar på Regeringen, inte SÄPO. Alfas infiltratörsrisk nämner spelledaren i stället för SÄPO. FM:s SÄPO-bonus på *Kontaktpersonen* tas bort när SÄPO inte är med.

**Briefs varnar.** Bravo, STT och Media får en tydlig mening: *I det här spelet ingår inte: SÄPO* (Media även USA), och att de ska tolkas som världsaktörer spelledaren kan spela.

**Motorflödet över fyra rundor.** Auto-fyll matchade alla sju lag varje runda utan budgetbrott. Fasbyte, HP-kö till nästa runda, milstolpar, projektorsekretess och `end_game` efter runda 4 fungerade. Inga läckor av `utfall` / `order_ref` i `build_public_state`.

**Skapa-spel-UI.** Radio Grundspel / Utökat + kryssrutor för extra lag är tillräckligt för just den här rosteren. Förhandsvisningen räknar `7 lag` när Media och Regeringen är ikryssade.

---

## Vad som fungerade mindre bra

**Testdata och Auto-fyll är fortfarande ett 9-lagsspel.** När SÄPO/USA saknas hoppas deras egna ordrar över, men kvarvarande lags ordrar *pekar fortfarande på dem*. Exempel:

| Runda | Lag | Order | Problem |
|-------|-----|--------|---------|
| 2 | STT | Penetrationstest | `paverkar: SÄPO` |
| 2 | Media | Pentest läckt | `paverkar: SÄPO` |
| 3 | STT | *Ta SÄPO till WAF-arbetet* | hela aktiviteten förutsätter SÄPO vid bordet |
| 3–4 | Media | Källknytaren | `paverkar` innehåller SÄPO och/eller USA |

I Testläge blir LLM-underlaget därför delvis osammanhängande: STT “tar SÄPO till WAF” i ett rum där SÄPO inte finns. Live utan Auto-fyll är spelarna fria att skriva rimliga ordrar, men GM som förlitar sig på testdata får fel story.

**Befintlig scenario-JSON går inte att återanvända.** `testdata/scenario_llm/runda1.json` faller på SÄPO-utfall. Runda 2–4 faller dessutom på slumpmismatch för tidiga `order_ref` (t.ex. Alfa-2), eftersom 9-lagsspelet förbrukar extra tärningsslag för SÄPO/USA. Att “bara ta bort SÄPO-rader” räcker inte. Ett sjulagsspel behöver egen resolution, eller så måste tärning och `resultat` skrivas om mot just det spelets låsta slag.

**Briefs är bara delvis anpassade.** Varningen finns, men brödtexten i Bravo, STT och Media talar fortfarande om att hålla kontakt med SÄPO/USA. Spelare vid bordet ser namnen som om de vore lagkamrater i rummet. Aktivitetskorten är bättre än briefs här.

**Teamöversikten på orderformuläret visar bara backloglag.** `create_team_overview` loopar `data["lag"]` men ritar kort bara om laget finns i `backlog`. Media och Regeringen har ingen backlog, så Alfa/Bravo/STT syns och de politiska lagen försvinner. Inte fel HP, men sämre situationsförståelse för de lagen.

**Regeringens fördelning övas inte av Auto-fyll.** Testdata lägger hela kassan på påverkansordrar (`hp_fordelning` saknas). Grant-regeln är testad i `test_domain.py`, men den här simuleringen visade inte liveflödet “ge HP till STT + behåll påverkan”.

**Nyhetstext från 9-lagssvaret nämner fortfarande säkerhetspolis/utländsk partner** som världsaktörer. Det är okej i prompten, men i ett rum utan SÄPO/USA som bordslag kan det låta som att de sitter i salen. LLM måste instrueras av exportens laglista — vilket den gör — men färdiga exempel-JSON:er gör det inte.

**Färgnyckeln `"Säpo"` i teamöversikten** matchar inte lagnamnet `"SÄPO"`. Syns inte i det här spelet (SÄPO är borta), men ger fel färg i ett niolagsspel.

---

## Buggar som bör fixas

### 1. Orderkort visar alltid 25 HP (hög)

`orderkort.py` läser `poang[lag].max_hp`, ett fält som inte finns. Fallback blir 25 för alla.

I det här spelet skrevs korten ut så här:

| Lag | Faktisk bas-HP | Orderkortet visade |
|-----|----------------|--------------------|
| Alfa, Bravo | 25 | 25 (rätt av en slump) |
| STT | 30 | **25** |
| FM, BS | 10 | **25** |
| Media, Regeringen | 12 | **25** |

Samma fel i både `generate_orderkort_html` och `generate_team_orderkort_html`. Bör använda `bas` (eller `aktuell` + stöd), samma källa som konsolen.

### 2. Orderkortets “Påverkar/Vem” listar alla nio lag (hög för utskrift)

`generate_order_rows()` anropas utan roster och faller tillbaka på `models.TEAMS` (hela katalogen). Papper för Media och Regeringen får kryssrutor för **SÄPO** och **USA** även när de inte är med.

Åtgärd: skicka `data["lag"]` (eller `active_teams(data)`) in i `generate_order_rows`.

### 3. Auto-fyll / testdata förutsätter SÄPO och USA (medel, Testläge)

Inte en krasch, men en innehållsbugg mot valbar roster. `apply_test_orders` skippar riktigt frånvarande lags *egna* ordrar, men rensar inte `paverkar` eller aktivitetsnamn som pekar på dem.

Minst: filtrera `paverkar` mot aktiva lag, eller ha testdata per roster. Annars är Testläge missvisande just för det scenario ÖreDev/större rum vill köra.

### 4. Ingen sjulags-LLM-fil (medel för live)

Parsern är strikt, vilket är bra. Konsekvensen är att en GM som råkar klistra in ett niolagssvar får hela importen avvisad. Det finns idag ingen `rundaN.json` för 7 lag. Antingen dokumentera tydligt “skriv om svaret mot exportens laglista”, eller ta fram ett fryst sjulagsår om ni vill kunna öva Auto-fyll + import utan att sitta med en LLM.

---

## Ytor som var rena i det här spelet

| Yta | SÄPO/USA synliga som lag? |
|-----|---------------------------|
| GM-konsol (nyskapat spel) | Nej |
| GM live-JSON / överföring | Nej |
| Spelarskärm + publik HP | Nej (rätt HP: STT 30, FM/BS 10, Media/Regeringen 12) |
| Orderformulär (påverkar + bidrag) | Nej |
| Aktivitetskort-utskrift | Nej som lag; korten är omskrivna |
| Teambrief-URL | 404 |
| LLM-export laglista | Nej |
| Orderkort papper | **Ja, som kryssrutor** + fel HP |

---

## Designanteckning (inte motorfel)

Sjulagsspelet med Media + Regeringen är spelbart i mjukvaran. Spänningen i rummet ändras: SÄPO:s spionjakt och USA:s allianser försvinner, STT:s säkerhetsagenda går via Regeringen, och Media/Regeringen är de extra politiska borden. Det är ett rimligt ÖreDev-snitt om briefs och testdata städas. Det befintliga niolagsåret i `testdata/scenario_llm/` ska inte användas som facit för den här rosteren.

---

## Rekommenderad fixordning

1. Orderkort: rätt HP-fält + `Påverkar` från spelets `lag`.
2. Testdata/Auto-fyll: inga `paverkar` eller aktivitetsnamn mot inaktiva lag.
3. Valfritt: korta briefs för Bravo/STT/Media när SÄPO/USA saknas, samma mönster som aktivitetskorten.
4. ~~Valfritt: ett fryst sjulags-LLM-år~~ **Gjort:** `testdata/scenario_llm_7lag/` plus `variant="seven"` i `tests/scenario_runner.py`. Niolagsåret är orört.
