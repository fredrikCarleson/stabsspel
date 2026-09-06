# Stabsspel scenario transcript

Seed `20260901`. Nine teams. Testdata orders, frozen D100, resolutions in `testdata/scenario_llm/rundaN.json`.

This is one scripted year, not live diplomacy.

## Runda 1

Wallets this round: Alfa 25, Bravo 25, STT 30, FM 10, BS 10, Media 12, SÄPO 15, Regeringen 12, USA 12.
Queued HP: Bravo +4, Alfa -3, STT -2, Regeringen -3.
Wallets after apply: Alfa 22, Bravo 29, STT 28, FM 10, BS 10, Media 12, SÄPO 15, Regeringen 9, USA 12.

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
- `SÄPO-1` SÄPO [bygga] Spaning på Alfa (9 HP, roll 48)
- `SÄPO-2` SÄPO [bygga] Samarbete med Media (6 HP, roll 44)
- `Regeringen-1` Regeringen [bygga] Fördela extra resurser till Bravo (7 HP, roll 33)
- `Regeringen-2` Regeringen [bygga] Mörka säkerhetsbrister (5 HP, roll 75)
- `USA-1` USA [bygga] Pressa regeringen att gynna ett extremparti (8 HP, roll 56)
- `USA-2` USA [bygga] Erbjuda säkerhetsinformation till STT (4 HP, roll 47)

### Utfall

- `Alfa-3` misslyckande (25% vs 65, 6 vs 13 HP): Alfas 6 HP möter Bravos rykte (6) och Medias artikel mot Alfa (7). Narrativet om Bravo som långsamt tar inte fäste.
- `Bravo-2` misslyckande (80% vs 87, 7 vs 0 HP): Välfinansierad lobbying utan motorder, men slaget ligger strax över. Bravo får inte igenom flytten från Alfa. Regeringens egen order om extra till Bravo löses separat.
- `Bravo-3` delvis framgång (75% vs 69, 6 vs 6 HP): Medias artikel (7 HP) förstärker ryktet, mot Alfas motkampanj (6). 6+7 mot 6 ger övertag, slaget är knappt under. Historien sprids men utan entydig evidens.
- `STT-3` misslyckande (40% vs 77, 6 vs 0 HP): Ingen betalar extra för förtur. 6 HP räcker inte för att tvinga fram en motprestation när både Alfa och Bravo prioriterar eget arbete.
- `FM-1` misslyckande (35% vs 41, 8 vs 12 HP): STT:s hardening (12) väger tyngre än 8 HP attack. Knapp förlust: kort belastningsspik syns, men front-end håller. STT:s backlog-arbete minskas inte.
- `FM-2` framgång (60% vs 23, 4 vs 4 HP): Regeringens mörkning (4) är motstånd, men Medias granskning förstärker tvivlet. 4 mot 4 justeras uppåt. Lågt slag: påståenden om röstmanipulation får spridning.
- `BS-1` delvis framgång (65% vs 51, 7 vs 0 HP): Ingen motorder. Utpressning är svårt men 7 HP är en tydlig satsning. Knapp framgång: personen skräms och läcker fragment, men går inte helt över.
- `BS-2` misslyckande (25% vs 43, 5 vs 12 HP): STT:s hardening är relevant försvar mot bakdörr i röstdatan. 5 mot 12 ger låg chans. Slaget missar: ingen bakdörr etableras.
- `Media-1` framgång (75% vs 36, 7 vs 6 HP): Bravos rykte stöttar publiceringen. Alfas motkampanj träffar Bravo, inte artikeln. 7+6 mot 6. Tydlig framgång: rubriken går ut.
- `Media-2` framgång (55% vs 13, 5 vs 4 HP): 5 mot regeringens 4 i mörkning. Lågt slag: granskningen får internationellt genomslag.
- `SÄPO-1` delvis framgång (50% vs 48, 7 vs 0 HP): Ingen motspaning, men att identifiera en infiltratör är svårt. Knapp framgång: SÄPO får en misstanke och mönster, inte ett namn.
- `SÄPO-2` delvis framgång (55% vs 44, 5 vs 0 HP): Media har redan två starkare spår. 5 HP räcker för att SÄPO syns som säkerhetsröst, men de äger inte narrativet.
- `Regeringen-1` framgång (75% vs 33, 6 vs 0 HP): Regeringen styr sin egen tilldelning. Bravo-lobbyingen misslyckades, men beslutet går igenom på regeringens linje. Extra till Bravo, inte flytt från Alfa.
- `Regeringen-2` misslyckande (40% vs 75, 4 vs 5 HP): Medias granskning (5) tynger mer än 4 HP PR. Tydligt misslyckande: mörkningen håller inte.
- `USA-1` misslyckande (40% vs 56, 8 vs 0 HP): Hög satsning men extremt svårt politiskt mål. Ingen direkt motorder, ändå låg baschans. Slaget missar: regeringen ger inte efter.
- `USA-2` framgång (60% vs 47, 4 vs 0 HP): Rimligt erbjudande utan motstånd. STT tar emot tipset. Inget kassa-HP: det skapar beroende, inte extra kapacitet.

### News

- **Kort störning i valets testmiljö – myndigheterna talar om belastning**
  Tekniska miljöer kopplade till det kommande extravalet utsattes under förmiddagen för ovanligt hög trafik. Delar av testsystemen svarade långsammare innan läget stabiliserades. Driftansvariga vill inte kalla händelsen ett angrepp, men bekräftar att övervakningen har skärpts. Inga röstuppgifter uppges ha påverkats.
- **Frågetecken kring säkerheten i ett av utvecklingsteamen**
  Uppgifter om möjliga brister i arbetet med det nya valsystemet har fått spridning. Det är oklart var uppgifterna kommer ifrån, men ett av de två utvecklingsteamen pekas ut för ett mer experimentellt arbetssätt. Projektledningen säger att inget sabotage är belagt, samtidigt som mer tid nu går åt till att svara på frågor om kvalitet och kontroll.
- **Regeringskansliet anklagas för att tona ned IT-problem**
  En granskning gör gällande att allvarliga brister i valets IT-stöd har bagatelliserats för att inte oroa allmänheten. Regeringen avvisar att något har undanhållits, men flera källor talar om intern oro. Internationella medier har hakat på. Samtidigt cirkulerar påståenden på sociala medier om att röster skulle kunna manipuleras – något myndigheterna kallar spekulation.
- **Extra resurser till det mer planerade utvecklingsspåret**
  Regeringen har beslutat att skjuta till extra stöd till det utvecklingsteam som arbetar efter en mer dokumenterad plan. Syftet uppges vara att minska risken för kaos inför extravalet. Det andra teamet får inget motsvarande tillskott. Oppositionen frågar om politiken nu väljer metod före resultat.
- **Säkerhetspolisen syns oftare kring valprojektet**
  Säkerhetspolisen har ökat sin närvaro kring arbetet med det digitala valet. Myndigheten talar allmänt om skydd mot otillbörlig påverkan och vill inte kommentera enskilda personer. Flera medarbetare i projektet beskriver en mer spänd stämning. Samtidigt hörs krav på att någon måste kunna garantera att systemet inte är infiltrerat.
- **Utländsk partner kopplar IT-stöd till politiska önskemål**
  En nära partner har enligt uppgifter kopplat fortsatt tekniskt stöd till politiska krav på den svenska regeringen. Regeringskansliet säger att Sverige inte låter utomstående styra partipolitiken. Samtidigt bekräftas att tekniska råd har tagits emot i valets IT-miljö. Det är oklart hur beroende projektet blir av den hjälpen.

### HP deltas

- Bravo +4: Regeringen skjuter till extra planeringsresurser efter det lyckade tilldelningsbeslutet.
- Alfa -3: Säkerhetsfrågor och mediedrev tvingar fram intern avstämning och förlorad arbetstid.
- STT -2: En medarbetare är skrämd och måste hanteras internt efter utpressningsförsöket.
- Regeringen -3: Misslyckad mörkning tvingar fram krishantering och mer tid mot medier.

### Milestones

- Alfa `alfa_1` +10: 10 HP utvecklingsarbete på inloggning. Ingen relevant attack träffade arbetet.
- Alfa `alfa_2` +9: 9 HP på röst-API. Bakdörrsförsöket mot databasen misslyckades.
- Bravo `bravo_1` +10: 12 HP satsades mot 10 HP kravfas. Överskottet förbrukas, 10 HP räknas.
- STT `stt_1` +12: 12 HP hardening. DDoS misslyckades och minskar inte progressen.
- STT `stt_2` +7: 7 HP planering av deklarationsinfrastruktur.

## Runda 2

Wallets this round: Alfa 22, Bravo 29, STT 28, FM 10, BS 10, Media 12, SÄPO 15, Regeringen 9, USA 12.
Queued HP: SÄPO +3, STT -3, Alfa -2.
Wallets after apply: Alfa 23, Bravo 25, STT 27, FM 10, BS 10, Media 12, SÄPO 18, Regeringen 12, USA 12.

### Orders

- `Alfa-1` Alfa [bygga] Sökfunktion (20 HP) (11 HP, roll 49)
- `Alfa-2` Alfa [bygga] Lobbya regeringen om extra HP (6 HP, roll 80)
- `Alfa-3` Alfa [bygga] Läcka Bravos förseningar till Media (5 HP, roll 26)
- `Bravo-1` Bravo [bygga] Grafisk visning valet - Design (10 HP) (12 HP, roll 13)
- `Bravo-2` Bravo [bygga] Kräva att STT flyttar resurser från Alfa (9 HP, roll 79)
- `Bravo-3` Bravo [bygga] Rykte: Alfa har en säkerhetsskuld (8 HP, roll 89)
- `STT-1` STT [bygga] Kapacitetstest (per gång) (10 HP) (11 HP, roll 61)
- `STT-2` STT [bygga] Penetrationstest (per gång) (15 HP) (10 HP, roll 1)
- `STT-3` STT [bygga] Vägra släppa Alfas sök utan motprestation (7 HP, roll 97)
- `FM-1` FM [forstora] Störa kapacitetstestet (6 HP, roll 91)
- `FM-2` FM [forstora] Mata Media med "läckt" valfusk (4 HP, roll 10)
- `BS-1` BS [forstora] Gemensam aktion med Främmande Makt (6 HP, roll 72)
- `BS-2` BS [forstora] Gömma bakdörr i sökfunktionen (4 HP, roll 55)
- `Media-1` Media [bygga] Skandal: pentest läckt innan rapport (6 HP, roll 49)
- `Media-2` Media [bygga] Rondsamtal med fyra lag (6 HP, roll 79)
- `SÄPO-1` SÄPO [bygga] Fördjupad spaning mot infiltratören (9 HP, roll 1)
- `SÄPO-2` SÄPO [bygga] Begära extra resurser av regeringen (6 HP, roll 10)
- `Regeringen-1` Regeringen [bygga] Beställa positiva nyheter om valförberedelserna (5 HP, roll 58)
- `Regeringen-2` Regeringen [bygga] Flytta en resurs från Alfa till Bravo (4 HP, roll 90)
- `USA-1` USA [bygga] Tillfällig överenskommelse med SÄPO (7 HP, roll 1)
- `USA-2` USA [bygga] Lämna tveksam hotbild till Media (5 HP, roll 78)

### Utfall

- `Alfa-2` misslyckande (30% vs 80, 7 vs 12 HP): Bravo (8) och regeringen (4) vill flytta resurser åt andra hållet. 7 mot 12. Tidigare tilldelning gick till Bravo. Tydligt nej.
- `Alfa-3` framgång (45% vs 26, 6 vs 7 HP): 6 mot Bravos motrykte (7) är nästan lika. Lågt slag: storyn om att Bravo fortfarande är i design tar fäste.
- `Bravo-2` misslyckande (50% vs 79, 8 vs 7 HP): STT jagar egen motprestation, inte Bravos resursflytt. Alfa lobbyar samtidigt. 8 mot 7 räcker inte när slaget är högt.
- `Bravo-3` misslyckande (55% vs 89, 7 vs 6 HP): Alfas läcka om Bravo tar Medias syre. 7 mot 6 borde bära, men slaget missar tydligt. Ryktet fäster inte den här gången.
- `STT-3` misslyckande (70% vs 97, 6 vs 0 HP): STT äger grinden, men ingen betalar och slaget är extremt. De får ingen motprestation. Sök går ändå inte i produktion — freeze närmar sig — bara utpressningen misslyckas.
- `FM-1` misslyckande (55% vs 91, 7 vs 10 HP): BS gemensamma aktion (7) lyfter 7 mot 10 mot cirka 55 %. Högt slag: störningen syns inte i lastsiffrorna. Testet är användbart.
- `FM-2` framgång (50% vs 10, 5 vs 6 HP): Regeringens positiva beställning (6) är motstånd. Tidigare desinformation hjälper. Lågt slag: andra vågen om riggade röster går ut.
- `BS-1` misslyckande (55% vs 72, 7 vs 10 HP): Samma händelse som FM:s störning av testet. 7+7 mot 10. Slaget 72 ligger över. Insiderstödet ger ingen effekt i testfönstret.
- `BS-2` misslyckande (25% vs 55, 5 vs 12 HP): Alfa bygger sök med 12 HP. Tidigare databasbakdörr misslyckades. 5 mot 12. Ingen bakdörr i sök.
- `Media-1` framgång (75% vs 49, 8 vs 0 HP): Ingen motpublicering. Pentest pågår samtidigt. 8 HP räcker. Rapporten läcker innan den är klar.
- `Media-2` misslyckande (70% vs 79, 7 vs 0 HP): Knapp miss. Tre av fyra samtal blir av, men en källa tiger. Ronden ger inte den avsedda bredden.
- `SÄPO-1` framgång (60% vs 1, 7 vs 0 HP): Föregående runda gav ett spår. 7 HP och extremt lågt slag: SÄPO får en tydlig bild av mönstret, inte ett offentligt namn ännu.
- `SÄPO-2` framgång (60% vs 10, 5 vs 0 HP): Regeringen har dålig press och vill visa handlingskraft på säkerhet. Lågt slag: SÄPO får ett tillskott.
- `Regeringen-1` misslyckande (25% vs 58, 6 vs 13 HP): Pentestläcka (8) och fuskläcka (5) tynger mer än 6 HP. Stabilitetsköpet går inte igenom.
- `Regeringen-2` misslyckande (55% vs 90, 4 vs 7 HP): Bravo hjälper (8) mot Alfas lobby (7). Politisk hetta efter förra rundans Bravo-stöd sänker chansen. Högt slag: ingen flytt.
- `USA-1` framgång (70% vs 1, 7 vs 0 HP): SÄPO har just fått ett starkt spår och tar emot hjälp. Extremt lågt slag: pakten blir reell. Tidigare tekniska råd till STT fördjupas till underrättelsesamarbete.
- `USA-2` misslyckande (50% vs 78, 5 vs 0 HP): Media har redan en pentestskandal. Tveksam hotbild tar inte plats. Slaget missar.

### News

- **Säkerhetstest läckt innan rapporten är klar**
  Utkast från ett pågående penetrationstest mot valets IT-miljö har nått redaktionerna innan myndigheterna hunnit sammanställa slutsatserna. Det är oklart hur materialet lämnade rummet. Driftansvariga säger att testet är en planerad övning, inte ett bevis på intrång. Oppositionen kräver besked om hur många som hade tillgång till utkastet.
- **Lasttest av valsystemet ger blandat betyg**
  Ett kapacitetstest av den planerade valinfrastrukturen har genomförts. Siffrorna uppges hålla för den simulerade belastningen, men flera källor säger att marginalerna är små. Inga störningar under testfönstret har bekräftats. Utvecklingsteamen tvistar om slutsatsen betyder grönt ljus eller krav på mer arbete före sommaren.
- **Ett utvecklingsspår ligger kvar i designfasen**
  Uppgifter gör gällande att det mer dokumenterade utvecklingsteamet fortfarande arbetar med design, medan det andra teamet redan bygger sökfunktioner. Projektledningen vill inte jämföra tidplaner. Frågan som ställs i kulisserna är om extravalet hinner få en färdig visning, eller om två spår nu kapplöper mot samma deadline.
- **Nya påståenden om att röster kan manipuleras**
  För andra gången på kort tid sprids uppgifter om att det digitala valet skulle kunna påverkas. Myndigheterna kallar det spekulation och pekar på att inga skarpa röstdata finns i testmiljön. Regeringskansliet hade velat tala om stabilitet, men den linjen får litet utrymme. Allmänhetens förtroende uppges svaja i mätningar.
- **Säkerhetspolisen utreder oegentliga kontakter i projektet**
  Säkerhetspolisen har enligt uppgifter fått ett tydligare spår kring otillbörliga kontakter i ett av utvecklingsteamen. Inga namn har offentliggjorts och ingen är formellt misstänkt. Stämningen i projektet beskrivs som mer misstänksam. Samtidigt bekräftas ett fördjupat samarbete med en nära internationell partner kring skyddet av valet.

### HP deltas

- SÄPO +3: Regeringen ger ett begränsat resurstillskott efter den lyckade begäran.
- STT -3: Läckt pentest tvingar fram intern utredning och omplanering av testhantering.
- Alfa -2: Fördjupad spaning skapar intern misstänksamhet och extra möten.

### Milestones

- Alfa `alfa_3` +12: 12 HP sökutveckling. Bakdörrsförsöket misslyckades. Ingen produktionssättning krävs för progress.
- Bravo `bravo_1` +10: 10 HP designarbete. Rent backlog-arbete.
- STT `stt_4` +10: Kapacitetstestet genomfördes. Störningsförsöket misslyckades.
- STT `stt_5` +9: 9 HP pentest-arbete. Läckan påverkar förtroendet, inte att testarbetet utfördes.

## Runda 3

Wallets this round: Alfa 23, Bravo 25, STT 27, FM 10, BS 10, Media 12, SÄPO 18, Regeringen 12, USA 12.
Queued HP: Alfa +3, SÄPO +3, STT +2.
Wallets after apply: Alfa 28, Bravo 25, STT 32, FM 10, BS 10, Media 12, SÄPO 18, Regeringen 12, USA 12.

### Orders

- `Alfa-1` Alfa [bygga] Admin-gränssnitt (20 HP) (11 HP, roll 70)
- `Alfa-2` Alfa [bygga] Köpa en lucka efter deklarationen (6 HP, roll 71)
- `Alfa-3` Alfa [bygga] Andra resurskravet mot regeringen (6 HP, roll 11)
- `Bravo-1` Bravo [bygga] Grafisk visning valet - Utveckling (20 HP) (15 HP, roll 65)
- `Bravo-2` Bravo [bygga] Andra ryktet: Alfa saboterar deklarationen (6 HP, roll 50)
- `Bravo-3` Bravo [bygga] Andra resursflytten från Alfa (4 HP, roll 58)
- `STT-1` STT [bygga] Ny säker arkitektur (poddar, WAF, brandväggar) (20 HP) (15 HP, roll 45)
- `STT-2` STT [bygga] Vägra båda leveranserna i deklarationsfönstret (7 HP, roll 82)
- `STT-3` STT [bygga] Ta SÄPO till WAF-arbetet (5 HP, roll 35)
- `FM-1` FM [forstora] Tyst påverkan medan systemet är låst (6 HP, roll 34)
- `FM-2` FM [forstora] Kräva lapp från infiltratören (4 HP, roll 87)
- `BS-1` BS [forstora] Utnyttja freeze till bakdörrsarbete (6 HP, roll 54)
- `BS-2` BS [forstora] Sälja insiderinfo till FM (4 HP, roll 27)
- `Media-1` Media [bygga] Skandal: hemlig freeze-pakt (6 HP, roll 38)
- `Media-2` Media [bygga] Fyra källor under deklarationen (6 HP, roll 15)
- `SÄPO-1` SÄPO [bygga] Förbereda offentligt avslöjande (11 HP, roll 37)
- `SÄPO-2` SÄPO [bygga] Andra resurskravet mot regeringen (7 HP, roll 18)
- `Regeringen-1` Regeringen [bygga] Andra positiva nyheten: deklarationen är under kontroll (7 HP, roll 14)
- `Regeringen-2` Regeringen [bygga] Hålla linjen: inga nödsättningar (5 HP, roll 52)
- `USA-1` USA [bygga] Erbjudande: molnkapacitet mot inflytande (8 HP, roll 59)
- `USA-2` USA [bygga] Andra tipset: "FM förbereder valnatt" (4 HP, roll 11)

### Utfall

- `Alfa-2` delvis framgång (75% vs 71, 7 vs 6 HP): Alfa betalar för juli, inte för att bryta freeze nu. STT:s vägran gäller fönstret. Knapp framgång: en preliminär lucka, ingen garanti.
- `Alfa-3` framgång (60% vs 11, 6 vs 4 HP): Bravos flyttförsök är bara 4 HP. Lågt slag: regeringen ger Alfa ett tillskott under freeze, inte en flytt från Bravo.
- `Bravo-2` delvis framgång (60% vs 50, 6 vs 0 HP): Ingen motkampanj. Media är upptagen med freeze-pakten. Ryktet sprids i korridorerna, inte som huvudskandal.
- `Bravo-3` misslyckande (35% vs 58, 4 vs 6 HP): Alfa får samtidigt extra av regeringen. 4 mot 6. Ingen flytt.
- `STT-2` misslyckande (80% vs 82, 6 vs 0 HP): Kalendern stoppar ändå produktion. Slaget missar den politiska utpressningen: STT får ingen motprestation nu. Freeze hålls av regeringens linje, inte av STT:s deal.
- `STT-3` delvis framgång (45% vs 35, 5 vs 0 HP): SÄPO förbereder avslöjande och har begränsad tid. Knapp framgång: de tittar förbi WAF, prioriterar inte STT:s arkitektur.
- `FM-1` framgång (55% vs 34, 7 vs 6 HP): Regeringens positiva budskap är 6 HP mot 7. Freeze ger utrymme för tvivel om att stoppet döljer något. Slaget bär.
- `FM-2` misslyckande (40% vs 87, 5 vs 0 HP): SÄPO förbereder offentligt avslöjande. Infiltratören fryser. Ingen lapp den här rundan.
- `BS-1` misslyckande (35% vs 54, 7 vs 12 HP): Alfa lägger 12 HP på admin. 7 mot 12. Ingen bakdörr i admin under freeze.
- `BS-2` framgång (70% vs 27, 5 vs 0 HP): FM är köpare. Tidigare fragment från STT-utpressningen finns kvar. Lappen uteblev, men äldre insiderinfo byter ägare.
- `Media-1` delvis framgång (40% vs 38, 8 vs 10 HP): Regeringens budskap (6) plus linjen om inga nödsättningar (4). Knapp framgång: storyn om samordnat stopp går, utan att stoppet framstår som olagligt.
- `Media-2` framgång (70% vs 15, 7 vs 0 HP): Lågt slag. Media får samtal med de fyra målen. Underlaget till freeze-storyn blir bredare.
- `SÄPO-1` framgång (70% vs 37, 7 vs 0 HP): Föregående runda gav ett starkt spår. Dossiern blir klar. Inget namn offentliggörs ännu.
- `SÄPO-2` framgång (70% vs 18, 5 vs 0 HP): Andra tillskottet. Lågt slag och freeze som argument. SÄPO får mer kapacitet mot valnatt.
- `Regeringen-1` delvis framgång (20% vs 14, 6 vs 15 HP): 8+7 mot 6 i motpublicering. Knapp framgång: en lugn notis går ut, men den drunknar i freeze-storyn.
- `Regeringen-2` framgång (80% vs 52, 4 vs 0 HP): Deklarationsregeln är etablerad. 4 HP plus STT:s grind. Inget team bryter freeze. Alfa får bara en julilucka, inte ett släpp nu.
- `USA-1` misslyckande (55% vs 59, 8 vs 0 HP): Hög satsning men suveränitetsfråga. Knapp miss: samtalen fortsätter, inget avtal om juli-släppet.
- `USA-2` framgång (60% vs 11, 4 vs 0 HP): SÄPO-pakten från förra rundan gör tipset trovärdigt. Lågt slag: varningen om störning kring valet tas på allvar.

### News

- **Inga nya valsystem i produktion under deklarationen**
  Regeringen backar linjen att inget nytt får sättas i drift så länge deklarationsfönstret pågår. Driftansvariga bekräftar att utveckling fortsätter i testmiljö, men att skarpa släpp får vänta till sommaren. Ett av utvecklingsteamen uppges ha fått ett villkorat löfte om en lucka i juli. Oppositionen frågar vem som då bestämmer vad som släpps först.
- **Påstådd uppgörelse bakom produktionsstoppet**
  Uppgifter gör gällande att stoppet samordnades tätare än vad som sagts offentligt. Myndigheterna säger att det är en känd deklarationsregel, inte en hemlig pakt. Samtidigt har flera källor i projektet talat med medier under tystnaden. En notis om att läget är under kontroll publiceras, men får litet genomslag.
- **Tyst period föder nya tvivel om valsystemet**
  Medan inget nytt går ut i produktion sprids påståenden om att tystnaden döljer mer än skatteteknik. Myndigheterna upprepar att freeze skyddar deklarationen, inte valet. I kulisserna talas det om att ett utvecklingsteam skulle ha orsakat stoppet genom slarv. Inget av det är belagt.
- **Extra stöd till både säkerhet och det agila spåret**
  Regeringen skjuter till mer resurser till säkerhetsarbetet kring valet, och ger också ett tillskott till det utvecklingsteam som arbetat mer iterativt. Det mer planerade teamet får ingen motsvarande flytt. Beskedet kommer mitt i freeze och tolkas som ett försök att visa handlingskraft utan att släppa något skarpt.
- **Varning om störningar när valet närmar sig**
  Säkerhetspolisen uppges förbereda ett mer konkret besked om otillbörlig påverkan, utan att namnge personer. Samtidigt har en internationell partner varnat för störningar kring själva valdagen. Driftansvariga säger att arkitekturarbete pågår men att inget nytt släpps nu. I projektet beskrivs stämningen som tystare – och mer rädd.

### HP deltas

- Alfa +3: Andra tillskottet från regeringen under freeze.
- SÄPO +3: Andra resurstillskottet med freeze och valnatt som argument.
- STT +2: Preliminär juli-lucka ger STT ett litet förskott i förhandlingen, inte full motprestation.

### Milestones

- Alfa `alfa_4` +12: 12 HP admin. Bakdörrsförsöket under freeze misslyckades.
- Bravo `bravo_1` +15: 15 HP av 20 i utvecklingsfasen. Rent backlog-arbete under freeze.
- STT `stt_3` +14: 14 HP ny säker arkitektur. Ingen produktionssättning under deklarationen.

## Runda 4

Wallets this round: Alfa 28, Bravo 25, STT 32, FM 10, BS 10, Media 12, SÄPO 18, Regeringen 12, USA 12.
Queued HP: STT +7, Alfa -5.
Wallets after apply: Alfa 20, Bravo 25, STT 37, FM 10, BS 10, Media 12, SÄPO 15, Regeringen 12, USA 12.

### Orders

- `Alfa-1` Alfa [bygga] Driva admin-gränssnittet i mål (13 HP, roll 3)
- `Alfa-2` Alfa [bygga] Kräva produktionssättning nu (9 HP, roll 54)
- `Alfa-3` Alfa [bygga] Sista narrativet mot Bravo (6 HP, roll 20)
- `Bravo-1` Bravo [bygga] Grafisk visning valet - Test (10 HP) (10 HP, roll 34)
- `Bravo-2` Bravo [bygga] Loggning & felhantering - Krav (4 HP) (8 HP, roll 96)
- `Bravo-3` Bravo [bygga] Valrykte: Alfa är inte produktionsklart (7 HP, roll 56)
- `STT-1` STT [bygga] Produktionssättning (per gång) (10 HP) (13 HP, roll 51)
- `STT-2` STT [bygga] Kapacitetstest inför valet (10 HP) (13 HP, roll 33)
- `STT-3` STT [bygga] Inkassera motprestation för släppet (6 HP, roll 34)
- `FM-1` FM [forstora] Valnattens DDOS (7 HP, roll 96)
- `FM-2` FM [forstora] Sista desinformationen: valet är riggat (3 HP, roll 79)
- `BS-1` BS [forstora] Aktivera bakdörren på valnatten (6 HP, roll 18)
- `BS-2` BS [forstora] Gemensam valnattsaktion med FM (4 HP, roll 49)
- `Media-1` Media [bygga] Valsensation: spion i Alfa (6 HP, roll 30)
- `Media-2` Media [bygga] Valnattens fyra samtal (6 HP, roll 71)
- `SÄPO-1` SÄPO [bygga] Offentligt avslöjande av infiltratören (12 HP, roll 83)
- `SÄPO-2` SÄPO [bygga] Skydda valnattens drift (6 HP, roll 27)
- `Regeringen-1` Regeringen [bygga] Valbudskap: systemet håller (7 HP, roll 37)
- `Regeringen-2` Regeringen [bygga] Nödfördela HP till STT (5 HP, roll 66)
- `USA-1` USA [bygga] Sista avtalet: stöd mot inflytande över utfallet (8 HP, roll 83)
- `USA-2` USA [bygga] Offentlig varning via Media (4 HP, roll 59)

### Utfall

- `Alfa-2` misslyckande (35% vs 54, 8 vs 0 HP) — Släppa inloggning, API och sök: Inloggning 10/15, API 9/25 och sök 12/20 är inte klara. STT släpper bara det som är färdigt. Juli-luckan gäller inte ofärdig kod.
- `Alfa-3` framgång (35% vs 20, 5 vs 7 HP): 5 mot Bravos 7. Lågt slag: storyn att Bravo fortfarande testar går ut. Bravo:s motrykte löses separat.
- `Bravo-3` delvis framgång (60% vs 56, 7 vs 5 HP): Knapp framgång. Alfa:s ofärdiga stack ger ryktet substans, men Alfa vinner samtidigt narrativet om Bravos test. Båda ser ofärdiga ut.
- `STT-1` framgång (65% vs 51, 10 vs 0 HP) — Vad som faktiskt går live: Admin når 20/20 denna runda. Inloggning, API, sök och Bravos visning är ofärdiga. STT släpper admin, inget röstflöde.
- `STT-3` delvis framgång (60% vs 34, 5 vs 0 HP): Alfa ville betala för tre släpp och fick ett. STT tar betalt för admin, inte för det som inte gick ut.
- `FM-1` misslyckande (35% vs 96, 8 vs 14 HP): BS gemensamma aktion (5) ger 13 mot STT:s lasttest (10) plus SÄPO (4). Tidigare hardening och valnattsvarning sänker chansen. Extremt högt slag: valnatten håller.
- `FM-2` misslyckande (40% vs 79, 4 vs 6 HP): Regeringens valbudskap (6) plus att DDoS misslyckas. Högt slag: riggad-valet-spåret tar inte fäste den här gången.
- `BS-1` misslyckande (10% vs 18, 7 vs 0 HP): Ingen bakdörr etablerades i runda 1–3. Minsta chans 10 %. Det finns inget att aktivera.
- `BS-2` misslyckande (35% vs 49, 5 vs 14 HP): Samma händelse som DDoS. 8+5 mot 14. Slaget 49 ligger över. Ingen gemensam effekt på valnatten.
- `Media-1` framgång (80% vs 30, 8 vs 0 HP): SÄPO:s offentliga avslöjande misslyckas, vilket gör obekräftade uppgifter starkare. 8 HP. Skandalen går ut utan myndighetsnamn.
- `Media-2` misslyckande (70% vs 71, 7 vs 0 HP): Knapp miss. Spionstoryn tar hela rundan. Fyra samtal blir inte den breda valnattsbilden.
- `SÄPO-1` misslyckande (75% vs 83, 8 vs 0 HP): Dossiern fanns. 8 HP borde räcka. Slaget ligger över: det formella avslöjandet stoppas. Media kör storyn obekräftad.
- `SÄPO-2` framgång (70% vs 27, 4 vs 0 HP): Försvar av samma händelse som DDoS. Lågt slag. SÄPO:s 4 HP räknas in i motståndet. Drift håller.
- `Regeringen-1` delvis framgång (50% vs 37, 6 vs 4 HP): DDoS misslyckades, vilket stöder budskapet. Spionrubriken tar syret. Knapp framgång: en notis om att systemen höll, inte hela narrativet.
- `Regeringen-2` framgång (75% vs 66, 4 vs 0 HP): Regeringen styr sin tilldelning. STT får ett nöd tillskott till valnattsdriften.
- `USA-1` misslyckande (40% vs 83, 8 vs 0 HP): Suveränitetsfråga. Hög satsning, högt slag. Inget grepp över valresultatet.
- `USA-2` misslyckande (50% vs 59, 4 vs 0 HP): Media kör spionskandal. 4 HP räcker inte för att äga valnatten. Tidigare varning står kvar, ingen ny rubrik.

### News

- **Valnattens system höll – men bara en del gick live**
  Den skarpa valmiljön utsattes för kraftig belastning under kvällen. Trafiken kunde hanteras. Det skarpa röstflödet släpptes aldrig, och påverkades därför inte. Driftansvariga bekräftar att ett administrationsgränssnitt har satts i produktion. Inloggning, röst-API och sökfunktion är däremot kvar i test. Frågan som ställs i studion är hur valet ska räknas om visningen inte är färdig.
- **Obekräftade uppgifter om infiltratör i utvecklingsteam**
  Uppgifter gör gällande att en person i ett av utvecklingsteamen ska ha arbetat för andra intressen. Säkerhetspolisen vill varken bekräfta eller dementera. Ingen har gripits. I projektet beskrivs stämningen som isande. Flera medarbetare säger att de inte längre vet vem de kan tala med i rummet.
- **Två spår, ingen färdig visning**
  Det mer planerade teamet uppges fortfarande testa sin grafiska visning, med utveckling kvar på den sista biten. Det andra teamet anklagas för att inte vara produktionsklart – och har i praktiken bara fått ut admin. Båda bilderna har fått spridning. Väljare möter därmed ett val där varken sök, röst-API eller resultattavla är bevisat skarpa.
- **Regeringen: driften klarade natten**
  Regeringskansliet säger att de tekniska system som faktiskt kördes höll, och att extra stöd gick till driftlaget under kvällen. Budskapet konkurrerar med rubrikerna om en möjlig infiltratör. En nära internationell partner får inget nytt avtal om inflytande över processen. Extravalet genomförs, men förtroendet är skadat.

### HP deltas

- STT +4: Nödtillskott från regeringen till valnattsdriften.
- STT +3: Delvis motprestation för admin-släppet.
- Alfa -2: Betalning för det släpp som faktiskt gick ut, inte för hela stacken.
- Alfa -3: Obekräftad spionrubrik tvingar fram intern kris och tystnad i teamet.

### Milestones

- Alfa `alfa_4` +8: 12 HP satsades, 8 HP återstod. Admin når taket.
- Bravo `bravo_1` +10: 10 HP test. Utveckling är 15/20 så visningen är inte färdig att släppas.
- Bravo `bravo_2` +4: 8 HP mot 4 HP kravfas. Överskottet förbrukas.
- STT `stt_6` +10: Produktionssättningsarbetet utförs. Utfallet avgör vad som gick live, inte om 10 HP arbete hände.
- STT `stt_4` +10: Andra kapacitetstestet. Återkommande uppgift startar en ny förekomst efter 10/10.

## Final wallets

- Alfa: 20
- Bravo: 25
- STT: 37
- FM: 10
- BS: 10
- Media: 12
- SÄPO: 15
- Regeringen: 12
- USA: 12
