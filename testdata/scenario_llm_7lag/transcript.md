# Stabsspel scenario transcript

Seed `20260901`. Seven teams (no SÄPO, no USA). Testdata orders, frozen D100, resolutions in `testdata/scenario_llm_7lag/rundaN.json`.

This is one scripted year, not live diplomacy.

## Runda 1

Wallets this round: Alfa 25, Bravo 25, STT 30, FM 10, BS 10, Media 12, Regeringen 12.
Queued HP: Bravo +4, Alfa -3, STT -2, Regeringen -3.
Wallets after apply: Alfa 22, Bravo 29, STT 28, FM 10, BS 10, Media 12, Regeringen 9.

### Orders

- `Alfa-1` Alfa [bygga] Inloggning val (15 HP) (10 HP, roll 59)
- `Alfa-2` Alfa [bygga] Back-end API för inskickade röster (25 HP) (9 HP, roll 3)
- `Alfa-3` Alfa [bygga] Kampanja mot Bravo i korridorerna (6 HP, roll 65)
- `Bravo-1` Bravo [bygga] Grafisk visning valet - Krav (10 HP) (12 HP, roll 93)
- `Bravo-2` Bravo [bygga] Kontakta regeringen för extra resurser (7 HP, roll 87)
- `Bravo-3` Bravo [bygga] Sprida rykten om Alfa (6 HP, roll 69)
- `STT-1` STT [bygga] Infrastruktur för val (setup, hardening, konfig) (20 HP) (15 HP, roll 40)
- `STT-2` STT [bygga] Infrastruktur för deklaration (20 HP) (8 HP, roll 38)
- `STT-3` STT [bygga] Förhandla om prioritet (7 HP, roll 77)
- `FM-1` FM [forstora] Massiv DDOS-attack mot valservern (7 HP, roll 41)
- `FM-2` FM [forstora] Desinformationskampanj på sociala medier (3 HP, roll 23)
- `BS-1` BS [forstora] Utpressa en STT-medlem (6 HP, roll 51)
- `BS-2` BS [forstora] Manipulera databasen (4 HP, roll 43)
- `Media-1` Media [bygga] Publicera artikel om misstänkt sabotage i Alfa (7 HP, roll 36)
- `Media-2` Media [bygga] Granskning av regeringens mörkläggning (5 HP, roll 13)
- `Regeringen-1` Regeringen [bygga] Fördela extra resurser till Bravo (7 HP, roll 48)
- `Regeringen-2` Regeringen [bygga] Mörka säkerhetsbrister (5 HP, roll 44)

### Utfall

- `Alfa-3` misslyckande (25% vs 65, 6 vs 13 HP): Alfas 6 HP möter Bravos rykte (6) och Medias artikel mot Alfa (7). Narrativet om Bravo som långsamt tar inte fäste.
- `Bravo-2` misslyckande (80% vs 87, 7 vs 0 HP): Välfinansierad lobbying utan motorder, men slaget ligger strax över. Bravo får inte igenom flytten från Alfa. Regeringens egen order om extra till Bravo löses separat.
- `Bravo-3` delvis framgång (75% vs 69, 6 vs 6 HP): Medias artikel (7 HP) förstärker ryktet, mot Alfas motkampanj (6). 6+7 mot 6 ger övertag, slaget är knappt under. Historien sprids men utan entydig evidens.
- `STT-3` misslyckande (40% vs 77, 7 vs 0 HP): Ingen betalar extra för förtur. 7 HP räcker inte för att tvinga fram en motprestation när både Alfa och Bravo prioriterar eget arbete.
- `FM-1` misslyckande (35% vs 41, 7 vs 15 HP): STT:s hardening (15) väger tyngre än 7 HP attack. Knapp förlust: kort belastningsspik syns, men front-end håller. STT:s backlog-arbete minskas inte.
- `FM-2` framgång (60% vs 23, 3 vs 5 HP): Regeringens mörkning (5) är motstånd, men Medias granskning förstärker tvivlet. Lågt slag: påståenden om röstmanipulation får spridning.
- `BS-1` delvis framgång (65% vs 51, 6 vs 0 HP): Ingen motorder. Utpressning är svårt men 6 HP är en tydlig satsning. Knapp framgång: personen skräms och läcker fragment, men går inte helt över.
- `BS-2` misslyckande (25% vs 43, 4 vs 15 HP): STT:s hardening är relevant försvar mot bakdörr i röstdatan. 4 mot 15 ger låg chans. Slaget missar: ingen bakdörr etableras.
- `Media-1` framgång (75% vs 36, 7 vs 6 HP): Bravos rykte stöttar publiceringen. Alfas motkampanj träffar Bravo, inte artikeln. 7+6 mot 6. Tydlig framgång: rubriken går ut.
- `Media-2` framgång (55% vs 13, 5 vs 5 HP): 5 mot regeringens 5 i mörkning. Lågt slag: granskningen får internationellt genomslag.
- `Regeringen-1` framgång (75% vs 48, 7 vs 0 HP): Regeringen styr sin egen tilldelning. Bravo-lobbyingen misslyckades, men beslutet går igenom på regeringens linje. Extra till Bravo, inte flytt från Alfa.
- `Regeringen-2` misslyckande (40% vs 44, 5 vs 5 HP): Medias granskning (5) tynger lika mycket som 5 HP PR. Slaget ligger över: mörkningen håller inte.

### News

- **Kort störning i valets testmiljö – myndigheterna talar om belastning**
  Tekniska miljöer kopplade till det kommande extravalet utsattes under förmiddagen för ovanligt hög trafik. Delar av testsystemen svarade långsammare innan läget stabiliserades. Driftansvariga vill inte kalla händelsen ett angrepp, men bekräftar att övervakningen har skärpts. Inga röstuppgifter uppges ha påverkats.
- **Frågetecken kring säkerheten i ett av utvecklingsteamen**
  Uppgifter om möjliga brister i arbetet med det nya valsystemet har fått spridning. Det är oklart var uppgifterna kommer ifrån, men ett av de två utvecklingsteamen pekas ut för ett mer experimentellt arbetssätt. Projektledningen säger att inget sabotage är belagt, samtidigt som mer tid nu går åt till att svara på frågor om kvalitet och kontroll.
- **Regeringskansliet anklagas för att tona ned IT-problem**
  En granskning gör gällande att allvarliga brister i valets IT-stöd har bagatelliserats för att inte oroa allmänheten. Regeringen avvisar att något har undanhållits, men flera källor talar om intern oro. Samtidigt cirkulerar påståenden på sociala medier om att röster skulle kunna manipuleras – något myndigheterna kallar spekulation.
- **Extra resurser till det mer planerade utvecklingsspåret**
  Regeringen har beslutat att skjuta till extra stöd till det utvecklingsteam som arbetar efter en mer dokumenterad plan. Syftet uppges vara att minska risken för kaos inför extravalet. Det andra teamet får inget motsvarande tillskott. Oppositionen frågar om politiken nu väljer metod före resultat.

### HP deltas

- Bravo +4: Regeringen skjuter till extra planeringsresurser efter det lyckade tilldelningsbeslutet.
- Alfa -3: Säkerhetsfrågor och mediedrev tvingar fram intern avstämning och förlorad arbetstid.
- STT -2: En medarbetare är skrämd och måste hanteras internt efter utpressningsförsöket.
- Regeringen -3: Misslyckad mörkning tvingar fram krishantering och mer tid mot medier.

### Milestones

- Alfa `alfa_1` +10: 10 HP utvecklingsarbete på inloggning. Ingen relevant attack träffade arbetet.
- Alfa `alfa_2` +9: 9 HP på röst-API. Bakdörrsförsöket mot databasen misslyckades.
- Bravo `bravo_1` +10: 12 HP satsades mot 10 HP kravfas. Överskottet förbrukas, 10 HP räknas.
- STT `stt_1` +15: 15 HP hardening. DDoS misslyckades och minskar inte progressen.
- STT `stt_2` +8: 8 HP planering av deklarationsinfrastruktur.

## Runda 2

Wallets this round: Alfa 22, Bravo 29, STT 28, FM 10, BS 10, Media 12, Regeringen 9.
Queued HP: Alfa -2, STT -2.
Wallets after apply: Alfa 23, Bravo 25, STT 28, FM 10, BS 10, Media 12, Regeringen 12.

### Orders

- `Alfa-1` Alfa [bygga] Sökfunktion (20 HP) (11 HP, roll 33)
- `Alfa-2` Alfa [bygga] Lobbya regeringen om extra HP (6 HP, roll 75)
- `Alfa-3` Alfa [bygga] Läcka Bravos förseningar till Media (5 HP, roll 56)
- `Bravo-1` Bravo [bygga] Grafisk visning valet - Design (10 HP) (12 HP, roll 47)
- `Bravo-2` Bravo [bygga] Kräva att STT flyttar resurser från Alfa (9 HP, roll 49)
- `Bravo-3` Bravo [bygga] Rykte: Alfa har en säkerhetsskuld (8 HP, roll 80)
- `STT-1` STT [bygga] Kapacitetstest (per gång) (10 HP) (11 HP, roll 26)
- `STT-2` STT [bygga] Penetrationstest (per gång) (15 HP) (10 HP, roll 13)
- `STT-3` STT [bygga] Vägra släppa Alfas sök utan motprestation (7 HP, roll 79)
- `FM-1` FM [forstora] Störa kapacitetstestet (6 HP, roll 89)
- `FM-2` FM [forstora] Mata Media med "läckt" valfusk (4 HP, roll 61)
- `BS-1` BS [forstora] Gemensam aktion med Främmande Makt (6 HP, roll 1)
- `BS-2` BS [forstora] Gömma bakdörr i sökfunktionen (4 HP, roll 97)
- `Media-1` Media [bygga] Skandal: pentest läckt innan rapport (6 HP, roll 91)
- `Media-2` Media [bygga] Rondsamtal med fyra lag (6 HP, roll 10)
- `Regeringen-1` Regeringen [bygga] Beställa positiva nyheter om valförberedelserna (5 HP, roll 72)
- `Regeringen-2` Regeringen [bygga] Flytta en resurs från Alfa till Bravo (4 HP, roll 55)

### Utfall

- `Alfa-2` misslyckande (30% vs 75, 6 vs 13 HP): Bravo (9) och regeringen (4) vill flytta resurser åt andra hållet. 6 mot 13. Tidigare tilldelning gick till Bravo. Tydligt nej.
- `Alfa-3` misslyckande (40% vs 56, 5 vs 8 HP): Bravos motrykte (8) tar mer plats än 5 HP läcka. Slaget ligger över. Storyn om designförsening tar inte fäste den här gången.
- `Bravo-2` delvis framgång (55% vs 49, 9 vs 6 HP): STT lyssnar när freeze närmar sig. Alfa lobbyar samtidigt. Knapp framgång: STT tar Bravos argument på allvar, men flyttar ingen kassa.
- `Bravo-3` misslyckande (60% vs 80, 8 vs 5 HP): 8 mot Alfas läcka (5) borde bära, men slaget missar tydligt. Ryktet fäster inte. Media jagar andra spår.
- `STT-3` misslyckande (70% vs 79, 7 vs 0 HP): STT äger grinden, men ingen betalar och slaget är över. De får ingen motprestation. Sök går ändå inte i produktion — freeze närmar sig — bara utpressningen misslyckas.
- `FM-1` misslyckande (40% vs 89, 6 vs 11 HP): BS erbjuder insiderstöd, men själva störningen (6) möter 11 HP test. Högt slag: lastsiffrorna håller. Testet är användbart.
- `FM-2` misslyckande (45% vs 61, 4 vs 5 HP): Regeringens positiva beställning (5) är motstånd. Andra vågen om riggade röster tar inte plats. Slaget missar.
- `BS-1` framgång (70% vs 1, 6 vs 0 HP): Kontakten blir reell. Insiderinfo går över. Själva slaget mot testfönstret misslyckas ändå — samarbetet finns, effekten i lastsiffrorna uteblir.
- `BS-2` misslyckande (25% vs 97, 4 vs 11 HP): Alfa bygger sök med 11 HP. Tidigare databasbakdörr misslyckades. 4 mot 11. Ingen bakdörr i sök.
- `Media-1` misslyckande (75% vs 91, 6 vs 0 HP): Pentestet pågår, men slaget är högt. Utkastet stannar i rummet. Ingen skandalrubrik den här gången.
- `Media-2` framgång (70% vs 10, 6 vs 0 HP): Lågt slag. Media får samtal med de fyra målen. Underlaget finns, även om skandalen inte går ut.
- `Regeringen-1` misslyckande (70% vs 72, 5 vs 0 HP): Ingen motskandal den här rundan, men slaget ligger strax över. Stabilitetsköpet går inte igenom. Studion tar inte beställningen.
- `Regeringen-2` misslyckande (50% vs 55, 4 vs 6 HP): Bravo hjälper (9) mot Alfas lobby (6). Politisk hetta efter förra rundans Bravo-stöd sänker chansen. Slaget missar: ingen flytt.

### News

- **Lasttest av valsystemet ger blandat betyg**
  Ett kapacitetstest av den planerade valinfrastrukturen har genomförts. Siffrorna uppges hålla för den simulerade belastningen, men flera källor säger att marginalerna är små. Inga störningar under testfönstret har bekräftats. Utvecklingsteamen tvistar om slutsatsen betyder grönt ljus eller krav på mer arbete före sommaren.
- **Ett utvecklingsspår ligger kvar i designfasen**
  Uppgifter gör gällande att det mer dokumenterade utvecklingsteamet fortfarande arbetar med design, medan det andra teamet redan bygger sökfunktioner. Projektledningen vill inte jämföra tidplaner. Frågan som ställs i kulisserna är om extravalet hinner få en färdig visning, eller om två spår nu kapplöper mot samma deadline.
- **Redaktionerna knyter fler källor i valprojektet**
  Flera nyhetsredaktioner uppges ha utökat sina kontakter i arbetet med det digitala valet. Inga namn nämns, men källor i både teknik- och politikspåret ska ha talat. Ingen ny skandal har publicerats. Oppositionen frågar ändå vem som egentligen styr informationen kring extravalet.
- **Regeringen får inte gehör för en linje om stabilitet**
  Regeringskansliet hade velat tala om lugn och kontroll i valförberedelserna. Budskapet tar inte fäste. Samtidigt har inget nytt larm om röstmanipulation fått genomslag den här veckan. Läget beskrivs som ett vakuum: varken trygga besked eller en ny krisrubrik.

### HP deltas

- Alfa -2: Misslyckad lobbying och intern avstämning efter Bravos påtryckningar binder tid.
- STT -2: Pentest och freeze-förhandlingar tar mer ledningstid än planerat, även utan läcka.

### Milestones

- Alfa `alfa_3` +11: 11 HP sökutveckling. Bakdörrsförsöket misslyckades. Ingen produktionssättning krävs för progress.
- Bravo `bravo_1` +10: 12 HP satsades mot 10 HP designfas. Överskottet förbrukas.
- STT `stt_4` +10: Kapacitetstestet genomfördes. Störningsförsöket misslyckades.
- STT `stt_5` +10: 10 HP pentest-arbete. Testet utfördes även om det inte läckte.

## Runda 3

Wallets this round: Alfa 23, Bravo 25, STT 28, FM 10, BS 10, Media 12, Regeringen 12.
Queued HP: Alfa +4, STT -2.
Wallets after apply: Alfa 29, Bravo 25, STT 28, FM 10, BS 10, Media 12, Regeringen 12.

### Orders

- `Alfa-1` Alfa [bygga] Admin-gränssnitt (20 HP) (11 HP, roll 49)
- `Alfa-2` Alfa [bygga] Köpa en lucka efter deklarationen (6 HP, roll 79)
- `Alfa-3` Alfa [bygga] Andra resurskravet mot regeringen (6 HP, roll 1)
- `Bravo-1` Bravo [bygga] Grafisk visning valet - Utveckling (20 HP) (15 HP, roll 10)
- `Bravo-2` Bravo [bygga] Andra ryktet: Alfa saboterar deklarationen (6 HP, roll 58)
- `Bravo-3` Bravo [bygga] Andra resursflytten från Alfa (4 HP, roll 90)
- `STT-1` STT [bygga] Ny säker arkitektur (poddar, WAF, brandväggar) (20 HP) (16 HP, roll 1)
- `STT-2` STT [bygga] Vägra båda leveranserna i deklarationsfönstret (7 HP, roll 78)
- `STT-3` STT [bygga] Ta Regeringen till WAF-arbetet (5 HP, roll 70)
- `FM-1` FM [forstora] Tyst påverkan medan systemet är låst (6 HP, roll 71)
- `FM-2` FM [forstora] Kräva lapp från infiltratören (4 HP, roll 11)
- `BS-1` BS [forstora] Utnyttja freeze till bakdörrsarbete (6 HP, roll 65)
- `BS-2` BS [forstora] Sälja insiderinfo till FM (4 HP, roll 50)
- `Media-1` Media [bygga] Skandal: hemlig freeze-pakt (6 HP, roll 58)
- `Media-2` Media [bygga] Fyra källor under deklarationen (6 HP, roll 45)
- `Regeringen-1` Regeringen [bygga] Andra positiva nyheten: deklarationen är under kontroll (7 HP, roll 82)
- `Regeringen-2` Regeringen [bygga] Hålla linjen: inga nödsättningar (5 HP, roll 35)

### Utfall

- `Alfa-2` misslyckande (50% vs 79, 5 vs 6 HP): STT:s vägran (6) och regeringens freeze-linje väger mer än 5 HP. Slaget missar: ingen garanterad julilucka.
- `Alfa-3` framgång (70% vs 1, 5 vs 5 HP): Bravos flyttförsök är 5 mot 5. Extremt lågt slag: regeringen ger Alfa ett tillskott under freeze, inte en flytt från Bravo.
- `Bravo-2` delvis framgång (60% vs 58, 7 vs 0 HP): Ingen motkampanj. Freeze-skandalen tar inte fäste. Ryktet sprids i korridorerna, inte som huvudnyhet.
- `Bravo-3` misslyckande (40% vs 90, 5 vs 5 HP): Alfa får samtidigt extra av regeringen. 5 mot 5 och högt slag. Ingen flytt.
- `STT-2` delvis framgång (80% vs 78, 6 vs 0 HP): Kalendern stoppar produktion. Knapp framgång: STT håller grinden utan att få betalt. Freeze bärs mer av regeringens linje än av en deal.
- `STT-3` misslyckande (65% vs 70, 5 vs 0 HP): Regeringen prioriterar freeze-linjen, inte STT:s arkitektur. 5 HP räcker inte. Ingen politisk välsignelse av WAF-arbetet.
- `FM-1` misslyckande (45% vs 71, 6 vs 7 HP): Regeringens positiva budskap är 7 mot 6. Freeze ger utrymme, men slaget missar. Tvivlet om att stoppet döljer valfusk tar inte fäste.
- `FM-2` framgång (70% vs 11, 4 vs 0 HP): Lågt slag. Lappen kommer. Infiltratören levererar Alfas planer under freeze.
- `BS-1` misslyckande (40% vs 65, 6 vs 10 HP): Alfa bygger admin med 10 HP. 6 mot 10. Ingen bakdörr i admin under freeze.
- `BS-2` framgång (70% vs 50, 4 vs 0 HP): Samarbetet från förra rundan består. 4 HP räcker. Info går över, utan att synas i produktion.
- `Media-1` misslyckande (50% vs 58, 6 vs 7 HP): Regeringens positiva budskap (7) plus linjen om inga nödsättningar. Slaget missar: storyn om olagligt stopp går inte.
- `Media-2` framgång (70% vs 45, 6 vs 0 HP): Lågt nog. Media får samtal med de fyra målen. Underlaget breddas även utan skandalrubrik.
- `Regeringen-1` misslyckande (55% vs 82, 7 vs 6 HP): Medias paktpåstående (6) tynger. Högt slag: stabilitetsbeställningen går inte ut som huvudnyhet.
- `Regeringen-2` framgång (75% vs 35, 5 vs 0 HP): Regeringen backar stoppet offentligt. Alfa får ingen lucka. Freeze håller som politisk linje, inte som STT-deal.

### News

- **Inget nytt får sättas i drift – extravalet väntar**
  Regeringen backar linjen att inget nytt får sättas i drift så länge deklarationsfönstret pågår. Driftansvariga bekräftar att utveckling fortsätter i testmiljö, men att skarpa släpp får vänta till sommaren. Oppositionen frågar vem som då bestämmer vad som släpps först.
- **Extra stöd till det mer iterativa utvecklingsspåret**
  Mitt i stoppet skjuter regeringen till mer resurser till det utvecklingsteam som arbetat mer iterativt. Det mer planerade teamet får ingen motsvarande flytt. Beskedet tolkas som ett försök att visa handlingskraft utan att släppa något skarpt.
- **Källor i projektet talar – men ingen ny skandal går ut**
  Flera redaktioner uppges ha talat med källor i både teknik- och politikspåret under deklarationsperioden. En uppgift om att stoppet skulle dölja något mer allvarligt får inte fäste. Stämningen beskrivs som spänd, med mer möten än rubriker.
- **Ett rykte pekar ut slarv som skäl till stoppet**
  I korridorerna cirkulerar påståenden om att ett av utvecklingsteamen skulle ha orsakat deklarationsstoppet genom slarv. Ingen myndighet bekräftar kopplingen. Projektledningen säger att stoppet är planerat. Ändå hörs frågan vem som bär ansvaret om extravalet blir försenat.

### HP deltas

- Alfa +4: Regeringen ger ett tillskott under freeze efter det lyckade resurskravet.
- STT -2: Att hålla freeze utan motprestation binder ledningstid mot två utvecklingsteam.

### Milestones

- Alfa `alfa_4` +10: 10 HP adminarbete. Bakdörrsförsöket misslyckades.
- Bravo `bravo_1` +17: 17 HP utveckling under freeze. Rent backlog-arbete.
- STT `stt_3` +15: 15 HP WAF-arkitektur. Ingen produktionssättning under deklarationen.

## Runda 4

Wallets this round: Alfa 29, Bravo 25, STT 28, FM 10, BS 10, Media 12, Regeringen 12.
Queued HP: STT +5, Alfa -5.
Wallets after apply: Alfa 20, Bravo 25, STT 35, FM 10, BS 10, Media 12, Regeringen 12.

### Orders

- `Alfa-1` Alfa [bygga] Driva admin-gränssnittet i mål (14 HP, roll 34)
- `Alfa-2` Alfa [bygga] Kräva produktionssättning nu (9 HP, roll 87)
- `Alfa-3` Alfa [bygga] Sista narrativet mot Bravo (6 HP, roll 54)
- `Bravo-1` Bravo [bygga] Grafisk visning valet - Test (10 HP) (10 HP, roll 27)
- `Bravo-2` Bravo [bygga] Loggning & felhantering - Krav (4 HP) (8 HP, roll 38)
- `Bravo-3` Bravo [bygga] Valrykte: Alfa är inte produktionsklart (7 HP, roll 15)
- `STT-1` STT [bygga] Produktionssättning (per gång) (10 HP) (11 HP, roll 37)
- `STT-2` STT [bygga] Kapacitetstest inför valet (10 HP) (11 HP, roll 18)
- `STT-3` STT [bygga] Inkassera motprestation för släppet (6 HP, roll 14)
- `FM-1` FM [forstora] Valnattens DDOS (7 HP, roll 52)
- `FM-2` FM [forstora] Sista desinformationen: valet är riggat (3 HP, roll 59)
- `BS-1` BS [forstora] Aktivera bakdörren på valnatten (6 HP, roll 11)
- `BS-2` BS [forstora] Gemensam valnattsaktion med FM (4 HP, roll 3)
- `Media-1` Media [bygga] Valsensation: spion i Alfa (6 HP, roll 54)
- `Media-2` Media [bygga] Valnattens fyra samtal (6 HP, roll 20)
- `Regeringen-1` Regeringen [bygga] Valbudskap: systemet håller (7 HP, roll 34)
- `Regeringen-2` Regeringen [bygga] Nödfördela HP till STT (5 HP, roll 96)

### Utfall

- `Alfa-2` misslyckande (35% vs 87, 8 vs 0 HP) — Släppa inloggning, API och sök: Inloggning 10/15, API 9/25 och sök 11/20 är inte klara. STT släpper bara det som är färdigt. Ingen lucka räddar ofärdig kod.
- `Alfa-3` misslyckande (35% vs 54, 5 vs 8 HP): 5 mot Bravos 8. Slaget missar. Storyn att Bravo bara testar tar inte över. Bravo:s motrykte om Alfas ofärdiga släpp löses separat.
- `Bravo-3` framgång (70% vs 15, 8 vs 5 HP): Alfas ofärdiga stack ger substans. Lågt slag: ryktet att det iterativa spåret inte är produktionsklart går ut.
- `STT-1` framgång (65% vs 37, 10 vs 0 HP) — Vad som faktiskt går live: Admin når taket denna runda. Inloggning, API, sök och Bravos visning är ofärdiga. STT släpper admin, inget röstflöde.
- `STT-3` framgång (70% vs 14, 5 vs 0 HP): Alfa ville betala för tre släpp och fick ett. STT tar betalt för admin, inte för det som inte gick ut.
- `FM-1` misslyckande (40% vs 52, 7 vs 9 HP): BS gemensamma aktion ger samordning, men lastsiffrorna (9) plus tidigare hardening väger mer. Slaget missar: valnatten håller.
- `FM-2` misslyckande (30% vs 59, 3 vs 7 HP): Regeringens valbudskap (7) plus att DDoS misslyckas. 3 HP räcker inte. Riggad-valet-spåret tar inte fäste.
- `BS-1` misslyckande (10% vs 11, 6 vs 0 HP): Ingen bakdörr etablerades i tidigare rundor. Att aktivera något som inte finns ger lägsta chans. Slaget ligger över.
- `BS-2` framgång (70% vs 3, 4 vs 0 HP): Samordningen blir av. DDoS-effekten uteblir ändå — kontakten finns, stilleståndet uteblir.
- `Media-1` framgång (70% vs 54, 6 vs 0 HP): Ingen myndighet motbevisar. 6 HP. Skandalen går ut som obekräftade uppgifter, utan att namnge dolda aktörer.
- `Media-2` framgång (70% vs 20, 6 vs 0 HP): Lågt slag. Media får samtal med drift, politik och de som vill så tvivel. Underlaget till valnatten blir brett.
- `Regeringen-1` framgång (65% vs 34, 7 vs 3 HP): DDoS misslyckas. 7 mot 3 i sista fuskläckan. Budskapet att driften klarade natten går ut, parallellt med spionuppgifter.
- `Regeringen-2` misslyckande (75% vs 96, 5 vs 0 HP): Politisk vilja finns, men slaget missar. STT får inget nöd tillskott. De klarar natten på befintlig kassa och lasttest.

### News

- **Bara administrationsytan gick live – röstflödet väntar**
  När deklarationsstoppet släppte sattes en administrativ yta i drift. Inloggning, röstinsamling och den grafiska visningen uppges inte vara klara. Driftansvariga säger att valet kan genomföras med befintliga rutiner. Oppositionen kallar det ett halvfärdigt system på valdagen.
- **Obekräftade uppgifter om infiltratör i ett utvecklingsteam**
  Uppgifter cirkulerar om att ett av utvecklingsteamen skulle ha en person med lojalitet någon annanstans. Inga namn har offentliggjorts och ingen myndighet bekräftar. Stämningen beskrivs som giftig. Projektledningen säger att arbetet fortsätter.
- **Ett spår kallas ofärdigt – det andra fast i test**
  Källor gör gällande att det mer iterativa teamet inte fick sina kärnfunktioner i drift, medan det mer planerade teamet fortfarande testar visningen. Båda sidor anklagar den andra för att sätta extravalet på spel. Väljarna ser bara att systemet inte är komplett.
- **Regeringen: driften klarade natten**
  Regeringen säger att valnattens drift höll, trots larm om överbelastning. Inga röstuppgifter uppges ha påverkats. Samtidigt får obekräftade uppgifter om intern infiltration mer utrymme än myndigheterna önskar. Förtroendet beskrivs som sårigt, men natten som tekniskt överlevd.

### HP deltas

- STT +5: Betalt för det enda släppet som faktiskt gick ut.
- Alfa -5: Betalning för admin-släpp plus intern kris efter obekräftade spionuppgifter.

### Milestones

- Alfa `alfa_4` +10: 11 HP satsades mot 10 HP kvar på admin. Uppgiften går i mål.
- Bravo `bravo_1` +10: 12 HP satsades mot 10 HP testfas. Visningen når test, inte produktion.
- Bravo `bravo_2` +4: Nödsäkring: kravfas för loggning. Överskottet förbrukas.
- STT `stt_6` +10: Produktionssättning av det som var redo: admin.
- STT `stt_4` +9: Andra kapacitetstestet inför valnatt. DDoS misslyckades.

## Final wallets

- Alfa: 20
- Bravo: 25
- STT: 35
- FM: 10
- BS: 10
- Media: 12
- Regeringen: 12
