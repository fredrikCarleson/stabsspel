# **Stabsspel Traineeprogrammet**

Det här är **spelreglerna** (lag, HP, rundor, nyhetsstudio). Den digitala spelledarhjälpen — klocka, ordrar, projektor — beskrivs i [architecture.md](architecture.md). Hur LLM-underlag skapas, tolkas och påverkar HP/nyheter: [LLM_WORKFLOW.md](LLM_WORKFLOW.md). Spelledaren bedömer fortfarande rummet (spion, papper, studio); appen slår tärningen. Starta appen med `python app.py` och öppna http://localhost:5000 (inte `flask app.py`).

Stabsspel Traineeprogrammet är ett spel där olika lag spelar med eller mot varandra för att uppnå sina egna eller gemensamma mål. Spelarna delas upp i lag som var och en har olika antal spelare, handlingspoäng och mål. Spelet sker i realtid och består huvudsakligen av följande faser

1) Orderfas  
2) Diplomatifas  
3) Resultatfas

Under orderfasen skriver varje lag ner sina order och hur många handlingspoäng de vill lägga på olika order som sedan lämnas in till spelledaren.

Under Diplomatifasen pratar teamen sig samman med sig själva samt andra team de har intresse eller behov att koordinera sig med. Innan diplomatifasen är slut måste varje team ha lämnat in sina order med antalet poäng till spelledarna.

Spelledaren läser igenom alla order under diplomatifasen och bedömer sannolikheten att utfallet blir som önskat baserat på hur många handlingspoäng som satsats för eller emot att ett visst skeende ska hända. Efter diplomatifasen delges alla lagen resultatet av order som kommit in.

I den digitala spelledarhjälpen kopieras ordrarna till en LLM. **Appen slår tärningen** (ett tal 1–100 per inskickad order). LLM:en får inte hitta på egna slag; den bedömer sannolikhet och tolkar utfallet. Spelledaren ser slagen och motiveringen i spelledarpanelen. Nyheterna skrivs ut på papper och läses i TV-studion — spelarna ser inte slagen.

Spelet börjar med att ett scenario beskrivs nedan. Därefter får varje team bestämma hur de vill dela upp de komponenter eller uppgifter som ska göras. När uppgifterna har fördelats får alla spelarna gå in i sina rum där de dels får reda på sitt teams mål samt göra en plan för hur de ska klara sina uppgifter.

| Aktör | Orderfas (10 minuter) | Diplomatifas (10 minuter) | Resultatfas |
| :---- | :---- | :---- | :---- |
| Varje lag | Diskuterar internt vilka order de vill lägga | Diskuterar fritt med andra lag | Samlas i gemensamt rum för att delges resultatet |
|  |  |  |  |
| Spelledare | Tillgänglig för frågorUppdaterar tidslinje | Analyserar utfall från alla teams order | Berättar resultatet |

# **Spelets vision – Vad vi tränar här**

I en komplex värld kan vi aldrig förutse allt.  Planer slår fel. Händelser förändras.  Det perfekta svaret finns sällan – men vi måste ändå agera.

Det här spelet utmanar dig att:

* Samverka tvärs över gränser – även med dem du inte litar på.

* Leverera snabbt och våga testa innan allt är klart.

* Reflektera och förbättra längs vägen.

* Skapa snabba feedback-loopar där du lär och justerar.

* Ta beslut även när du inte har all information.

**Att vänta på perfekta förutsättningar är den största risken.**  Den som vågar agera, samarbeta och anpassa sig kommer lyckas.  Den som tvekar – eller försöker kontrollera allt – riskerar att misslyckas.

## **Lärandemål för spelet:**

- [ ] Förstå att världen är komplex och förändras snabbt.

- [ ] Träna på att samarbeta under osäkerhet och press.

- [ ] Öva på att fatta beslut utan att ha hela bilden.

- [ ] Skapa och använda snabba feedback-loopar.

- [ ] Utforska makt, beroenden och dolda agendor.

      # **💡 Vad spelarna ska ta med sig**

- [ ] Jag kan inte lösa allt själv – samarbete är avgörande.

- [ ] Jag måste våga prata med andra för att lyckas.

- [ ] Alla har intressen – vad är deras, vad är mitt?

- [ ] Att välja fel kan få stora konsekvenser, men att inte välja alls är sämre.

- [ ] Det går att vinna (eller göra skillnad) på många sätt – inte bara genom att lösa sin egen uppgift.

      # 

      # **Att göra innan spelet börjar**

* Bekräfta att alla förstått reglerna och hur spelmekaniken gått till. För att spara tid kan det vara bra att ha skickat ut spelreglerna till alla deltagare i förväg. Se ”*Stabspel Traineeprogrammet – Spelregler och Introduktion*”  
* Säkra att alla team vet sin hemvist. Det kan vara bra att sätta upp en lapp med varje teams lagnamn på den plats de har sin hemvist.   
* Säkra att alla vet vart återsamlingsplatsen är där teamen debriefas efter diplomatifasen  
* Visa på tidslinjen var vi är  
* Visa på whiteboard hur många handlingspoäng varje team har (observera att det kan förändras och behöver uppdateras varje runda)  
* Presentera de olika rollerna: spelledare, nyhetsankare och tidtagare.  
* Poängtera vikten av att lämna in order i tid.

  1. ## **Roller**

Det är svårt att leda spelet ensam, därför är det bra att ha fler personer som hjälper till. Nedan är förslag på olika roller:

**Spelledare**

Spelledaren är ansvarig för att hålla samman spelet och förklara reglerna. Spelledaren tar introduktionen och berättar om scenariot.

**Nyhetsankare**

Under diplomatifasen bestämmer nyhetsankaret och spelledaren konsekvenserna av de olika teamens order. När teamen samlas läser nyhetsankaret upp konsekvenserna i form av nyheter.  Se nyhetsrubriker i slutet av dokumentet som exempel på hur det kan se ut.

**Tidtagare**

För att säkra att spelet kan avslutas på den tid som avsatts är det viktigt att tidsfaserna hålls. Tidtagaren säkrar att alla vet hur lång tid det är kvar på orderfasen och diplomatifasen. Den viktigaste uppgiften är att säkra att teamen lämnar in sina order till spelledaren innan orderfasen är slut. Om ett team inte lämnat in sin order i tid har de inga ordrar och deras handlingspoäng förloras. Tidtagaren ser också till att teamen samlas i det gemensamma rummet när diplomatifasen är slut. 

# **Spelet börjar** 

Börja med att delge scenariot:

***Sverige befinner sig i kaos.***  
 *Regeringen har fallit efter en dramatisk misstroendeomröstning, och landet är på väg mot ett extraval – ett val som måste genomföras snabbt, säkert och utan skandaler. Blickarna från hela världen riktas nu mot Sverige.*

*Skatteverket har fått det livsfarliga uppdraget: att på rekordtid bygga de system som ska samla in och presentera röster i realtid efter att vallokalerna har stängt. Tiden är knapp och resurserna är begränsade. Det enda som finns tillgängligt är ett gammalt valhanteringssystem byggt med en teknologistack ingen längre använder – **Angular 1.2 – osäkert, föråldrat och fyllt av kända säkerhetshål.** Utvecklarna som en gång byggde systemet är borta. Kvar finns endast kryptisk dokumentation.*

*Det är nu september 2025 och **det är mindre än ett år kvar till valet.***  
 *Två utvecklingsteam – Alfa och Bravo – har tilldelats uppdraget, tillsammans med kritiska resurser från STT (Stödjande Tekniska Tjänster). Tillsammans ska ni leverera ett system som inte bara fungerar – det måste stå emot sabotage, hackerattacker och politisk granskning.*

*Men ni är långt ifrån ensamma.*  
 ***Främmande makter har redan börjat infiltrera och planera cyberattacker för att underminera valets legitimitet.** Organiserad brottslighet ser sin chans att tjäna pengar och manipulera systemet. **SÄPO jagar spioner.***  
 *Samtidigt har **USA visat ett oväntat intresse för valprocessen och driver sina egna dolda agendor.***  
 ***Regeringen kämpar för att hålla landet stabilt och pressas från flera håll att göra snabba – och kanske farliga – val.***

*Och mitt i allt:*  
 ***Media jagar sensationsrubriker.***  
 *Alla misstag, varje säkerhetsbrist, varje läcka kommer att blåsas upp och riskera att sänka allmänhetens förtroende för valet.*

***Det är nu upp till er.***  
 *Kan ni tillsammans – eller trots varandra – leverera ett fungerande och säkert valsystem? Eller kommer krafter utanför och innanför era organisationer att sabotera valet och splittra landet?* ”

Be alla team att ställa sig i sin teamtillhörighet. Dela sedan ut ett lagkort till varje spelare i varje lag. Lagkortet beskriver teamets mål och vad de ska leverera. De finns under rubriken handouts längre ner i dokumentet. Ge alla spelare tio minuter att läsa igenom kortet. 

Därefter börjar spelet. Be alla lag gå till sina teamytor och skriva ner sina första orders och komma tillbaka med dem inom tio minuter.

# **Faser**

Nedan är exempel på faser och de tider som måste hållas för ett spel på 160 minuter (två och halv timme).

| Fas | Tid (ungefärlig) | Händelser |
| :---- | :---- | :---- |
| Pre game |  | Skicka ut häfte med regler |
| Introduktion | 10 minuter | Briefing |
| 1 sep 2023Förberedelse | 10 minuter | Alla teamen får tilldelat sig sitt lagkort med instruktioner och arbetsplan och får läsa igenom  |
| Spelet börjar |  |  |
| September | 10 minuter | Varje team skriver ner handlingar och skickar till spelledarna |
| 1\. Okt –Dec | 10 minuter | Spelledarna sammanställer resultat Diplomatifas fortsätter för teamen |
| Vad hände? | 10 minuter | Presentation av händelser |
| 2\. Jan-Mar | 10 minuter | Varje team skriver ner handlingar och skickar till spelledarna |
| Diplomati | 10 minuter | Spelledarna sammanställer resultat Diplomatifas för team |
| Vad hände | 10 minuter | Presentation av händelser |
| 3\. Apr-Juni | 10 minuter | Varje team skriver ner handlingar och skickar till spelledarna |
| Diplomati | 10 minuter | Spelledarna sammanställer resultat Diplomatifas för team |
| Vad hände | 10 minuter | Presentation av händelser |
| 4\. Jul-Sep | 10 minuter | Varje team skriver ner handlingar och skickar till spelledarna SISTA RUNDAN |
| Spelet slut |  |  |
| Hur gick valet? | 20 minuter | Spelledarna sammanställer resultat Hur gick valet? |
| Avslutning | 20 minuter | Debriefing |
| Total tid | 160 minuter |  |

GLÖM inte att rita upp tidslinjen på White board så att det är tydligt för alla var vi är hela tiden. Sätt upp lappar med vad som hände på tidslinjen när spelledaren berättar resultaten från lagens order.

# **Backlog**

Tabellen nedan beskriver de aktiviteter som behöver vara på palts innan valet. De har i förväg delats upp mellan Alfa, Bravo och STT innan spelet börjar. De finns specificerade på lagkorten.

| Komponent | Estimerade handlingspoäng | Team |
| :---- | :---- | :---- |
| Infrastruktur för val (sätta upp, hardening, konfig m.m) | 20 | STT |
| Infrastruktur  för deklaration (sätta upp, hardening, konfig m.m) | 20 | STT |
| Inloggning val | 15 | ALPHA |
| Back-end API för inskickade röster | 25 | ALPHA |
| Pen-test | 15 per gång | STT |
| Kap-test | 10 per gång | STT |
| Grafisk visning valet | 50 | BRAVO |
| Loggning och felhantering | 20 | BRAVO |
| Nyhetsflöde | 15 | BRAVO |
| Sökfunktion | 20 | ALPHA |
| Ny säker arkitektur poddar, WAF och brandväggar | 20 | STT |
| Admin gränssnitt | 20 | ALPHA |
| Produktionssätta | 10 per gång | STT |
| Totalt | 250 poäng |  |

# **Laguppsättning**

Fem lag är alltid med: Alfa, Bravo, STT, FM och Brottssyndikatet.

Fyra lag är valfria extra: Media, Regeringen, SÄPO och USA.

- **Grundspel:** de fem kärnlagen.
- **Utökat spel:** kärnlagen plus minst ett extra lag. Giltiga spel har 6, 7, 8 eller 9 lag.

Det sparade spelets `lag`-lista är sanningen för HP, spelledarpanel, projektor, orderlänkar och LLM. Ett inaktivt lag ska inte synas.

Appen balanserar inte HP automatiskt efter hur många extra lag som valts. Grundspelets HP-tabell används för fem lag. Utökat spel använder samma HP-katalog som det fulla 9-lagsspelet för de lag som faktiskt är med.

# **Handlingspoäng per team**

För att klara av det som finns i backlog behöver varje team under perfekta förutsättningar spendera ca 21 handlingspoäng per runda. Det förutsätter att saker och ting går bra. Det finns alltså en liten övervikt för FM och BS att ställa till med problem om de samordnar.

Poängen per team ändras per runda baserat på händelser. Det är upp till spelledarna att bestämma fluktuationen.

| Team | Poäng per runda (fyra rundor totalt) |
| :---- | :---- |
| Alpha | 25 |
| Bravo | 25 |
| STT | 25 |
| Främmande makt | 12 |
| Brottsyndikatet | 12 |

| Team | Handlingspoäng per runda stora spel |
| :---- | :---- |
| Team Alfa | 25 HP |
| Team Bravo | 25 HP |
| STT | 30 HP |
| Främmande makt (FM) | 10 HP |
| Brottssyndikatet (BS) | 10 HP |
| Media | 12 HP |
| Regeringen | 12 HP |
| SÄPO | 15 HP |
| USA | 12 HP |

När **Regeringen** är ett spelande lag är dess 12 HP politiska resurser, inte teknisk backlog-kapacitet. Varje runda får de användas på två sätt:

1. Föras över till ett eller flera andra aktiva lag. Överförd HP lämnar regeringens kassa samma runda.
2. Satsas på politisk eller medial påverkan (opinion, media, motverka negativ press).

Samma HP kan inte både ges bort och läggas på en order. Kassan nästa runda är **bas + varaktigt**, plus tillfälliga justeringar från spelledare eller LLM den rundan. Det finns ingen dold extra bank på +10. Ett tillfälligt anslag (regering, spion, GM −/+) försvinner vid rundbyte. Varaktig inkomst (t.ex. DevOps +3 varje runda) stannar tills spelledaren tar bort den.

2. ## **Smarta saker för teamen att göra**

Det är fritt fram för spelarna att tänka utanför boxen för att öka sina handlingspoäng genom att t.ex. 

* Spendera handlingspoäng för att söka mer pengar från regeringen för att klara valet.  
* Investera tidigt i CI/CD för att minska antalet poäng STT måste spendera på produktionssättning (spendera 10 handlingspoäng för att få det på plats så är det gratis sedan t.ex.)

# **Plot twists**

## **Spion**

Brottssyndikatet strävar hela tiden efter att påverka och få in personer på viktiga platser i Skatteverket. De har lyckats infiltrera och få en av sina medlemmar anställda av Skatteverket i team Alfa. Den personen agerar utåt som en anställd på Skatteverket men informerar och styrs av Brottssyndikatet.

Främmande makt vet att BS har en spion i Alfa, men vet inte vem. Varje runda spionen är med förlorar team Alfa fem handlingspoäng och BS får fem poäng. **Observera att detta enbart sker om spionen fysiskt besöker Brottssyndikatets teamyta och pratar med dem.** Tidtagaren är bäst lämpad att observera om detta skett. Annars får spelledaren fråga Brottssyndikatet om de fått information.

Spionen tillhör BS och lämnar sin information till BS. Främmande makt vet att BS har en spion i Alfa, men vet inte vem och kan försöka förhandla med BS om att få del av informationen. Om spionen avslöjas stoppas framtida överlämningar och BS kan inte längre få bonusen på fem handlingspoäng.

Om det går för bra för spionen kan spelledare eller tidtagare informera team Alfa att SÄPO har fått indikationer på att de har en spion i sitt team.

## **Deklarationstider**

Under april-juni månad är det deklarationstider. Under dessa tider är det absolut förbjudet för STT att något produktionssätt något nytt i produktion då det kan påverka stabiliteten under deklarationstider.

Spelledare eller tidtagare kan informera om detta innan runda 3 börjar som t.ex. under resultatfasen för runda 2\.

## **Arbetssätt**

Team Alfa, Bravo och STT arbetar alla på olika sätt vilket kommer att skapa vissa problem under förutsättning att teamen följer instruktionerna på korten.

Alfa kommer att vilja sätta poäng på att göra en liten bit funktionalitet klar och få ut i produktion. Dock har de int CI/CD på plats utan all produktionssättning måste göras av STT. De har alltså ett beroende till STT.

Team Bravo arbetar enligt vattenfall. De kommer att vilja först spendera poäng på att först skapa alla krav för det de ska arbeta med, sedan design för alla sina delar, sedan utveckling och test för att till slut produktionssätta allt samtidigt två veckor innan valet. Team Bravo behöver också få hjälp av STT för att produktionssätta.

Både Alfa och Bravo behöver hjälp av STT för att få upp testmiljöer. STT prio är dock att säkra kapacitet och öka säkerheten för de nya hoten som Sverige utsätts för.

STT arbetar enligt principen att den som skriker högst får vad den vill. Det vill säga den som sätter högst handlingspoäng.

## **Action kort**

Det finns även andra plot twists i de action kort som två spelare i varje team får. Se “Aktivitetskort för teamen”.

# **Teammål**

# **Team Alfa**

#### **Utförliga Mål:**

1. **Leverera en fungerande version av valsystemets nyckelfunktioner i tid:**  
   * Se till att inloggningssystemet, röstinsamlingen och API för röstdata är fullt fungerande och säkra. Målet är att ha dessa funktioner operativa varje runda, med löpande förbättringar baserat på feedback.  
2. **Optimera utvecklingsprocessen genom CI/CD:**  
   * Implementera och utnyttja en CI/CD-pipeline för att snabbt kunna iterera och leverera funktionalitet. Säkerställ att varje leverans är testad och stabil för att minimera risken för buggar i produktion.  
3. **Samarbeta effektivt med STT för att säkra produktionssättningen:**  
   * Arbeta nära STT för att säkerställa att alla system kan produktionssättas utan förseningar. Se till att alla beroenden och säkerhetsaspekter hanteras i tid.

#### **Dolda Agendor:**

1. **Främja agila arbetsmetoder över traditionella modeller:**

   * Inom laget, och gärna genom att påverka andra lag, bör ni försöka visa överlägsenheten hos agila metoder. Detta kan innebära att fördröja eller kritisera Team Bravos traditionella arbetssätt för att framhäva agilitetens fördelar.  
2. **Implementera en specifik teknisk lösning:**

   * Ni har en stark preferens för en viss teknisk lösning (t.ex. ett specifikt ramverk eller molntjänst) och kommer att försöka få detta implementerat även om det inte är den mest optimala lösningen. Försök driva denna agenda utan att väcka misstankar från andra lag.  
3. **Övertyga regeringen om att ni behöver mer resurser:**

   * Försök övertyga regeringen om att ni behöver extra resurser för att möta ert mål. Om ni lyckas kan ni få extra handlingspoäng i en senare runda.

Tips:

* Skapa **snabba allianser** med STT för att få prioritet vid produktionssättning.

* Förhandla aktivt med Regeringen om mer resurser – Regeringen tenderar att lyssna på dem som pratar mest.

* Försök påverka Media att rapportera era snabba framgångar för att pressa Bravo.

![][image1]

**Teamet vill arbeta med att få funktioner klara direkt och få det i produktion och efter hand förbättra. Ovan är  de funktioner ni ska få klara med antal handlingspoäng som krävs.**

# **Team Bravo**

#### **Utförliga Mål:**

1. **Leverera ett komplett och stabilt valsystem enligt plan:**

   * Följ en noggrant utformad plan stegvis. Först all kravinsamling, sedan all design, sedan all utveckling, testning och till slut produktionssättning. Varje steg ska vara färdigt innan nästa påbörjas.  
2. **Säkerställ att projektet håller sig inom budget och tidsramar:**

   * Hantera resurser noggrant för att säkerställa att projektet inte överskrider de givna handlingspoängen. Allokeringen av resurser ska vara effektiv och kostnadsmedveten, och projektet ska avslutas inom den givna tidsramen.  
3. **Upprätthåll noggrann kontroll och dokumentation genom hela processen:**

   * Se till att varje beslut är väldokumenterat och att risker hanteras proaktivt. Systemet ska vara lätt att förstå och underhålla även efter att spelet är över.

#### **Dolda Agendor:**

1. **Bevisa överlägsenheten hos traditionella projektmetoder:**

   * Demonstrera att er metodik är mer pålitlig och stabil än agila metoder. Om möjligt, peka på problem som Team Alfa stöter på som bevis för att er metod är överlägsen.  
2. **Försök få kontroll över resurser från andra team:**

   * Om det finns möjlighet att omdirigera eller ta över resurser från andra team (t.ex. STT handlingspoäng), bör ni göra detta för att säkerställa att ert projekt är bäst försett.

Tips:

* Arbeta metodiskt men sök aktivt stöd från SÄPO och Regeringen för att få resurser i rätt tid.

* Skapa en **långsiktig berättelse** till Media om ert stabila arbetssätt – positionera Alfa som ett riskprojekt.

* Ha personer som lyssnar på Alfa för att samla in information om deras framfart och eventuella misstag.

![][image2] 

**Ovan är er projektplan med de leverabler ni ska leverera under projektet med estimat på hur många handlingspoäng varje ”task” tar.**

# 

# **Team STT**

#### **Utförliga Mål:**

1. **Upprätthåll en stabil och säker infrastruktur:**

   * Säkerställ att all infrastruktur är "härdad" mot attacker och att kapaciteten är tillräcklig för att hantera hög belastning. Målet är att inga system ska gå ner eller bli komprometterade under spelets gång.  
2. **Skydda systemet mot både interna och externa hot:**

   * Utför regelbundna säkerhetstester och övervaka alla system för potentiella hot. Om en säkerhetsbrist upptäcks, agera omedelbart.  
3. **Samarbeta med utvecklingsteamen för att säkerställa lyckad produktionssättning:**

   * Se till att ni har en tydlig bild av varje teams behov och beroenden så att alla system kan sättas i produktion utan problem. Prioritera produktionssättningar utifrån systemens kritikalitet.

#### **Dolda Agendor:**

1. **Säkra era egna intressen genom att prioritera säkerhet över allt annat:**

   * Om ni står inför valet mellan att uppfylla ett teams önskan om snabb produktionssättning och att säkerställa säkerheten, bör ni alltid välja säkerheten, även om det orsakar förseningar för andra team.  
2. **Underminerar arbetet i team som inte värderar säkerhet tillräckligt:**

   * Om ni märker att ett utvecklingsteam (t.ex. Alfa eller Bravo) ignorerar säkerhetsaspekter, bör ni försöka påverka teamet att förstå hotet från andra aktörer.  
3. **Försök påverka regeringen för att få ytterligare säkerhetsresurser:**

   * Om ni anser att ni inte har tillräckliga resurser för att säkerställa systemets säkerhet, försök få ytterligare medel från regeringen genom att förklara potentiella hot.

Tips:

* Var selektiv och kräva **handlingspoäng för att produktionssätta** – tvinga andra team att förhandla om prioritet.

* Håll tät kontakt med SÄPO och Regeringen – det kan ge politiskt skydd om ni saktar ner vissa team.

* Få Media att förstå vikten av säkerhet – annars riskerar ni att framstå som en bromskloss.

![][image3]  
**Ovan är de mål ni har tillsammans med hur många handlingspoäng det kostar. Notera att under deklarationstider (markerat i rött) produktionssätter ni ingenting.**

# **Främmande Makt (FM)**

#### **Utförliga Mål:**

1. **Underminera förtroendet för det svenska valsystemet:**

   * Genomföra cyberattacker, sprida desinformation och skapa kaos för att minska allmänhetens förtroende för valsystemet. Målet är att så många som möjligt ska ifrågasätta valets legitimitet.  
2. **Genomför framgångsrika attacker utan att bli upptäckta:**

   * Planera och utför hackerattacker, som DDOS eller phishing, för att störa systemet utan att avslöjas. Om möjligt, plantera en "backdoor" för framtida attacker.  
3. **Koordinera med Brottssyndikatet för att maximera skadan:**

   * Samarbeta med Brottssyndikatet för att utnyttja deras insikt och resurser. Detta kan innebära att ni delar information eller resurser för att genomföra en större attack. 

#### **Dolda Agendor:**

1. **Få tillgång till känslig information för framtida utpressning:**

   * Utöver era officiella mål, försök att stjäla känslig information som kan användas för framtida utpressning eller påverkan på politiska beslut i Sverige.  
2. **Sprid splittring och misstänksamhet mellan svenska myndigheter:**

   * Arbeta för att skapa splittring mellan olika svenska myndigheter och team genom att sprida rykten eller direkt påverka deras kommunikation. Målet är att försvaga deras samarbete och öka chanserna för era attacker att lyckas.  
3. **Stötta en specifik politisk agenda i Sverige:**

   * Om möjligt, använd er påverkan för att främja en politisk agenda som skulle gynna era intressen på lång sikt. Detta kan vara att gynna ett visst parti eller skapa kaos som leder till ett politiskt dödläge.

**Extra**: Ni har lyckats få reda på att Organiserad Brottslighet har en infiltratör i Team Alfa, men inte vem. Spionen lämnar information till BS. Ni kan försöka få del av den via BS.

Tips:

* Använd diplomatifasen för att diskret bygga relationer med Media och Brottssyndikatet.

* Håll ett öga på vilka team som får mest resurser – fokusera attacker där systemet är svagast.

* Försök styra Media till att ifrågasätta valets säkerhet och därmed skapa misstro även om era attacker misslyckas.

# **Brottssyndikatet (BS)**

#### **Utförliga Mål:**

1. **Maximera ekonomisk vinning genom att utnyttja systemet:**

   * Använd era resurser för att manipulera systemet så att ni kan tjäna pengar, till exempel genom att förfalska röster eller utnyttja välfärdssystem. Målet är att optimera era intäkter samtidigt som ni undviker upptäckt.  
2. **Påverka valresultatet för att gynna era intressen:**

   * Arbeta för att säkerställa att ett politiskt klimat som gynnar era affärsintressen, till exempel genom att påverka vilken kandidat eller parti som vinner valet. Detta kan innebära att ni samarbetar med Främmande Makt eller andra aktörer.  
3. **Håll er verksamhet dold och undvik upptäckt:**

   * Se till att era operationer inte avslöjas. Detta innebär att ni måste vara försiktiga med hur ni infiltrerar, manipulerar och kommunicerar inom spelet.

#### **Dolda Agendor:**

1. **Utöka er verksamhet till andra sektorer genom valpåverkan:**

   * Använd valet som ett tillfälle att utöka er kontroll och påverkan över andra sektorer, som energimarknaden eller byggsektorn, genom att placera er personal i nyckelpositioner.  
2. **Infiltrera nyckelpositioner i Skatteverket för framtida manipulation:**

   * Utöver den nuvarande infiltratören, försök placera fler individer inom Skatteverket som kan användas för framtida manipulation eller sabotage. Dessa individer bör hålla sig under radarn och bygga förtroende tills de aktiveras.  
3. **Skapa en långsiktig maktbas genom att påverka lagstiftning:**

   * Arbeta i bakgrunden för att påverka lagstiftning som skulle underlätta för er kriminella verksamhet på lång sikt. Detta kan innebära lobbying för mildare straff eller mindre reglering av vissa marknader.

**Extra**: Gruppen har en spion anställd i team Alfa. Denna person låtsas vara med i Alfa men rapporterar och utför brottsyndikatets önskningar. Varje runda den personen kontaktar er på er kontaktyta och berättar om Team Alfas planer får ni fem extra handlingspoäng och de förlorar fem poäng. Speltekniskt går det till så att personen i Alfra överlämnar en lapp med planer till er eller på bestämd plats så får ni de extra handlingspoängen.

Tips:

* Utnyttja er infiltratör maximalt – låt den vara aktiv och samla information direkt från Alfa.

* Ha ständig kontakt med Media – men var försiktiga med vad ni avslöjar. Ni kan också manipulera narrativet.

* Samarbeta taktiskt med FM – men var beredda att svika dem om det gynnar er mer.

  # **Vid stora spel (upp till 60 personer)**

| Nya Team | Motparter | Roller / Mål |
| ----- | ----- | ----- |
| **SÄPO** | Brottssyndikatet & Främmande Makt | Skydda valet, avslöja spioner, bygga motståndskraft |
| **Regeringen** | USA & Främmande Makt | Fördela resurser, balansera säkerhet vs. PR |
| **USA** | Regeringen, SÄPO | Främja sin politiska agenda, stötta utvalda svenska team |
| **Media**  | Alla | Letar skandaler, kan exponera eller skydda information beroende på vem som påverkar dem |

## **SÄPO**

### **Utförliga Mål:**

**Skydda valsystemet från sabotage och cyberattacker:**  
 Arbeta proaktivt för att identifiera och neutralisera hot från Främmande Makt, Brottssyndikatet och eventuella andra destabiliserande aktörer. Prioritera säkerhet även om det kan försena systemleveranser.

**Identifiera och eliminera infiltratörer:**  
 Genom underrättelsearbete, observationer och samverkan med andra team ska ni hitta spioner och individer som hotar valets säkerhet. Målet är att avslöja minst en infiltratör under spelets gång.

**Skydda förtroendet för valprocessen:**  
 Agera aktivt för att bemöta desinformation och bevara allmänhetens tilltro till valsystemet och myndigheterna.

### **Dolda Agendor:**

**Stärka SÄPO:s framtida mandat och resurser:**  
 Arbeta för att skapa ett narrativ där SÄPO framstår som avgörande för Sveriges säkerhet. Övertyga Regeringen om att ytterligare befogenheter och resurser behövs.

**Påverka Media att sprida SÄPO-vänliga narrativ:**  
 Försök påverka Media att lyfta SÄPO:s framgångar och tona ned eventuella misslyckanden.

**Underrapportera egna säkerhetsmissar:**  
 Om SÄPO själva misslyckas med att förhindra intrång eller sabotage, bör dessa händelser döljas eller förklaras som andras fel.

Tips:

* Utse **en eller två spelare som specialiserar sig på att bygga relationer med Regeringen** – det ökar chanserna att få resurser och inflytande.

* Skicka spanare till Media för att lyssna av vilken information som sprids – Media kan avslöja saker ni annars skulle missa.

* Ha koll på vilka personer som rör sig mellan team – vem pratar ofta med FM eller Brottssyndikatet?

## **Regeringen**

### **Utförliga Mål:**

**Genomför valet i tid och säkerställ politisk stabilitet:**  
 Ni ansvarar för att valet hålls enligt plan och att de system som krävs är klara. Arbeta för att undvika skandaler och stärka regeringens förtroende.

**Fördela resurser mellan teamen:**  
 Ni har tillgång till en resursbank om 10 handlingspoäng som kan fördelas till olika team varje runda. Resursfördelningen påverkar vilka insatser som kan genomföras och vilka team som får fördelar.

**Hantera internationell påverkan och inhemska konflikter:**  
 Regeringen behöver balansera mellan att samarbeta med SÄPO, tillmötesgå USA och bemöta Främmande Makt och Brottssyndikatet. Era beslut påverkar Sveriges framtida handlingsfrihet.

### **Dolda Agendor:**

**Stärka den sittande regeringens ställning:**  
 Använd resurstilldelning och mediapåverkan för att främja politiska beslut som gynnar den nuvarande regeringen.

**Tona ned säkerhetsrisker för att undvika negativ PR:**  
 Om allvarliga hot eller intrång uppstår, arbeta för att dämpa dessa i offentligheten – även om det innebär att ignorera säkerhetsrekommendationer från SÄPO eller STT.

**Undvik att bli beroende av USA:**  
 Även om USA kan erbjuda stöd, sträva efter att behålla svensk självständighet och motverka långsiktig amerikansk dominans.

Tips:

* Prata aktivt med alla team – men fördela resurser strategiskt till de team som kan gynna regeringens agenda.

* Använd Media för att forma bilden av regeringen som stabil och ansvarsfull.

* Låt er påverkas – men utnyttja USA och SÄPO:s lojalitetsspel för att pressa fram bättre villkor.

## **USA**

### **Utförliga Mål:**

**Främja en politisk riktning i Sverige som gynnar USA:**  
 Genom diplomati, resurser och mediapåverkan ska ni arbeta för att valet styrs mot en politisk agenda som är positiv för amerikanska intressen.

**Begränsa Främmande Makts inflytande:**  
 Identifiera och motverka Främmande Makts försök att påverka valet och svenska myndigheter.

**Bygg inflytande över svenska IT-system:**  
 Försök etablera tekniska eller organisatoriska beroenden där Sverige blir mer beroende av amerikansk teknologi och expertis.

### **Dolda Agendor:**

**Styr Media för att driva USA-vänliga narrativ:**  
 Påverka Media att rapportera nyheter som gynnar USA:s agenda och tona ned amerikansk inblandning.

**Etablera långsiktigt strategiskt samarbete:**  
 Försök skapa beroenden där Sverige i framtiden blir beroende av USA:s cybersäkerhet eller tekniska lösningar.

**Använd Regeringens svagheter för påtryckning:**  
 Om regeringen gör misstag, använd dessa som förhandlingsverktyg för att få igenom USA:s krav.

Tips:

* Sök tidigt kontakt med Media och Regeringen – ni vinner inflytande genom att erbjuda stöd och information.

* Skapa tillfälliga allianser med SÄPO för att bekämpa Främmande Makt – men använd det också som en väg in i svenska system.

* Bygg beroenden i tysthet – varje förtroende ni får är ett strategiskt verktyg.

## **Media**

### **Utförliga Mål:**

**Rapportera först och bredast om viktiga händelser:**  
 Målet är att vara den ledande nyhetskällan under hela spelet. Ju fler avslöjanden ni gör, desto större genomslag får ni.

**Forma den allmänna bilden av valet:**  
 Hur valet uppfattas beror i stor utsträckning på vad Media väljer att lyfta fram eller tona ned. Ni har makten att skapa förtroende eller misstro.

**Balansera tillgång till information:**  
 Samarbeta med olika aktörer (Regeringen, USA, SÄPO, Främmande Makt, Brottssyndikatet) för att få exklusiva tips och nyheter.

### **Dolda Agendor:**

**Prioritera de källor som ger bäst exklusivitet:**  
 Media kan välja att lyfta fram nyheter från den part som ger mest tillgång till information, även om det innebär att ni vinklar rapporteringen.

**Sprida panik om det ökar spridningen:**  
 Dramatiska nyheter om säkerhetsbrister eller valfusk ska alltid prioriteras – även om fakta är osäkra – om det ger klick och genomslag.

**Underminera SÄPO och andra säkerhetsaktörer om de begränsar informationsflödet:**  
 Om SÄPO eller andra försöker begränsa insynen, arbeta aktivt för att ifrågasätta deras agerande i era nyhetsflöden.

Tips:

* **Prata med så många team som möjligt i varje diplomatifas.** Ju fler källor ni har, desto mer makt får ni över narrativet.

* Hota med att avslöja team som inte samarbetar – det skapar press och förhandlingar.

* Skapa splittring mellan aktörer genom hur ni väljer att vinkla nyheterna – det gör er till spelets maktspelare.

  # **Uppdaterad teamstruktur (för ca 60 personer)**

| Team | Antal spelare | Handlingspoäng per runda | Kommentar |
| ----- | ----- | ----- | ----- |
| Team Alfa | 6-8 | 25 | Agilt utvecklingsteam |
| Team Bravo | 6-8 | 25 | Vattenfallsteam |
| STT | 6-8 | 25 | Infrastruktur och säkerhet |
| Främmande Makt | 6-8 | 12 | Cyberattacker, destabilisering |
| Brottssyndikatet | 6-8 | 12 | Infiltration, ekonomisk vinning |
| SÄPO | 6-8 | 12 | Skydd, spionjakt |
| Regeringen | 6-8 | 10 | Resurshantering och politik |
| USA | 6-8 | 12 | Påverkansoperationer |
| Media | 6-8 | 15 | Informationskontroll |

> **Tips:**  
>  Låt Regeringen ha en pott med extra handlingspoäng att fördela varje runda – t.ex. 10 extra poäng som de kan ge till team de vill gynna.

# **Exempel på teamindelning (22 stycken)**

| Person | Lag |
| :---- | :---- |
|  | Team Alfa |
|  | Team Alfa |
|  | Team Alfa |
|  | Team Alfa |
|  | Team Alfa (spion) |
|  | STT |
|  | STT |
|  | STT |
|  | STT |
|  | Team Bravo |
|  | Team Bravo |
|  | Team Bravo |
|  | Team Bravo |
|  | Team Bravo |
|  | Främmande makt |
|  | Främmande makt |
|  | Främmande makt |
|  | Främmande makt |
|  | Brottsyndikat |
|  | Brottsyndikat |
|  | Brottsyndikat |
|  | Brottsyndikat |

Orderkort

| Runda |  |
| :---- | :---- |
| Order 1 | Poäng |
|  |  |
| Order 2 | Poäng |
|  |  |
| Order 3 | Poäng |
|  |  |
| Order 4 | Poäng |
|  |  |

# **Aktivitetskort för teamen**

I varje team som är med för alla teammedlemmar ett aktivitetskort. Ofta är det blankt men för två spelare i varje team finns särskilda uppgifter. Dessa uppgifter är till för att främja spelets idé och vision. Alla aktivitetskort är HEMLIGA för alla utom spelaren.

### **🟢 Team Alfa – Aktivitetskort**

#### **Infiltratören (Spion från Brottssyndikatet)**

* **Uppdrag:** Du tillhör egentligen Brottssyndikatet. En gång per runda måste du diskret överlämna en fysisk lapp med Alfas planer till Brottssyndikatet. Lappen får inte lämnas öppet utan måste överlämnas personligen eller lämnas på en gemensam plats som spelledaren anvisar.

* **Mål:** Dela Team Alfas order eller strategier med Brottssyndikatet.

* **Belöning:** Varje diplomatifas du lyckas får Brottssyndikatet \+5 handlingspoäng och Alfa förlorar \-5 handlingspoäng.

* **Risk:** Om du blir upptäckt kan SÄPO försöka utesluta dig eller frysa dina handlingspoäng och Brottssyndikatet förlorar 5 poäng.

#### **Påverkaren**

* **Uppdrag:** Övertyga Regeringen att ge extra resurser (handlingspoäng) till Team Alfa minst två gånger under spelet.

* **Mål:** Säkra att Alfa prioriteras i resursfördelningen.

* **Belöning:** Varje gång Regeringen ger resurser till Alfa får ni lika många handlingspoäng.

---

### **🟦 Team Bravo – Aktivitetskort**

#### **Resursjägaren**

* **Uppdrag:** Få Regeringen eller STT att flytta över minst två resurser från Team Alfa till Bravo.

* **Mål:** Maximera Bravos tillgångar för att klara era deadlines.

* **Belöning:** För varje resurs som flyttas från Alfa till Bravo får ni \+5 handlingspoäng och Alfa får fem mindre.

#### **Rykesspridaren**

* **Uppdrag:** Sprid minst ett rykte per runda till Media som sätter Alfa i dålig dager och Bravo bra dager.

* **Mål:** Påverka opinionen till Bravos fördel.

* **Belöning:** Varje gång Media publicerar ett rykte som sänker Alfa men höjer Bravo får ni \+3 handlingspoäng.

---

### **🟡 STT – Aktivitetskort**

#### **Säkerhetsväktaren**

* **Uppdrag:** Övertyga SÄPO att prioritera minst två av era säkerhetsinsatser under spelet.

* **Mål:** STT:s säkerhetsfokus ska alltid stå i centrum.

* **Belöning:** STT får \+1 handlingspoäng per handlingspoäng som SÄPO spenderar för STT:s räkning.

#### **Produktionsvägraren**

* **Uppdrag:** Vägra produktionssätta minst två leveranser från andra team om de inte erbjuder er extra resurser eller hjälp.

* **Mål:** Tvinga andra att förhandla med STT.

* **Belöning:** Varje gång ni får en motprestation för en produktionssättning får ni lika många handlingspoäng som det andra teamet ger er.

---

### **🔴 Främmande Makt – Aktivitetskort**

#### **Kontaktpersonen**

* **Uppdrag:** Hitta infiltratören i Team Alfa. Du vet att BS har en spion där, men inte vem. Försök få Alfas planer via Brottssyndikatet. Spionens fysiska lapp går till BS, inte till er.

* **Mål:** Förhandla med BS om informationen. Ni styr inte spionen.

* **Belöning:** Ingen HP-bonus för spionens lapp. Den bonusen är alltid \+5 BS och \-5 Alfa, aldrig \+5 FM. Om BS säljer informationen till er är det en separat överenskommelse.

* **Bonus:** Om ni samtidigt lyckas få SÄPO att sätta dit en spion i Team Bravo får ni \+5 extra handlingspoäng.

#### **Mediaagenten**

* **Uppdrag:** Påverka Media att publicera minst två nyheter som undergräver tilliten till valsystemet.

* **Mål:** Främja misstro genom pressen.

* **Belöning:** Varje gång Media publicerar en nyhet som skadar systemets förtroende får ni handlingspoäng baserat på hur allvarligt förtroendet skadas.

---

### **⚫ Brottssyndikatet – Aktivitetskort**

#### **Resurskaparen**

* **Uppdrag:** Få minst ett team att omedvetet leverera funktioner som ni kan utnyttja, t.ex. backdoors.

* **Mål:** Skapa manipulationstillfällen i systemet.

* **Belöning:** Varje sådan funktion innebär att det teamet förlorar alla investerade handlingspoäng i den funktionen.

#### **Samarbetaren**

* **Uppdrag:** Samarbeta minst en gång med Främmande Makt för en gemensam aktion.

* **Mål:** Visa att Brottssyndikatet är en strategisk spelare även för andra makter.

* **Belöning:** Lyckad samverkan innebär att ni kan satsa handlingspoäng på gemensam handling vilket ger större chans att lyckas.

---

### **🟠 SÄPO – Aktivitetskort**

#### **Spionjägaren**

* **Uppdrag:** Identifiera och avslöja infiltratören i ett utvecklingsteam innan spelet är slut.

* **Mål:** Spionen ska bli offentligt avslöjad via en händelse eller Mediakanal.

* **Belöning:** Lyckas ni får ni \+10 handlingspoäng och Brottssyndikatet förlorar 5 poäng.

#### **Resurssamlaren**

* **Uppdrag:** Få Regeringen att tilldela extra resurser till SÄPO minst två gånger under spelet.

* **Mål:** Stärka SÄPO:s makt och inflytande.

* **Belöning:** Varje gång SÄPO får resurser från Regeringen får ni lika många handlingspoäng som tilldelats.

---

### **🏛 Regeringen – Aktivitetskort**

#### **Opinionsbyggaren**

* **Uppdrag:** Få Media att publicera minst två nyheter som gynnar Regeringen och framställer den som stabil.

* **Mål:** Bygg regeringens trovärdighet.

* **Belöning:** Varje positiv publicering ger er \+3 handlingspoäng som ni kan fördela direkt till andra team om ni vill..

#### **Maktdelaren**

* **Uppdrag:** Omfördela eller flytta minst en resurs eller teammedlem mellan lag under spelet.

* **Mål:** Visa prov på handlingskraft och styrning.

* **Belöning:** Varje gång en resurs eller spelare flyttas tar spelaren med sig \+5 handlingspoäng till det nya teamet och det gamla teamet förlorar \-5 poäng.

---

### **🇺🇸 USA – Aktivitetskort**

#### **Alliansbyggaren**

* **Uppdrag:** Skapa minst en tillfällig överenskommelse med Regeringen eller SÄPO som stärker USA:s position.

* **Mål:** Öka USA:s inflytande över valarbetet.

* **Belöning:** USA får inflytande över vilket parti som väljs..

#### **Informationsfördelaren**

* **Uppdrag:** Lämna minst två strategiska tips eller hotbilder till Regeringen eller Media, även om informationen är tveksam.

* **Mål:** Framstå som oumbärlig informationskälla.

* **Belöning:** USA får inflytande över valet.

---

### **📰 Media – Aktivitetskort**

#### **Klickjägaren**

* **Uppdrag:** Hitta och publicera minst en skandal eller säkerhetsbrist varje runda.

* **Mål:** Maximera spridning och påverkan, oavsett fakta.

* **Belöning:** Varje publicerad skandal ger Media något extra handlingspoäng.

#### **Källknytaren**

* **Uppdrag:** Ha direktkontakt med minst fyra olika team varje runda.

* **Mål:** Bygg Media som den centrala informationsnoden i spelet.

* **Belöning:** Tillgång till information.

  #  **Spelledaröversikt – Poänglogik per handling**

| Handling | Poängeffekt |
| ----- | ----- |
| Fysisk lapp till Brottssyndikatet (infiltratören) | \+5 BS, \-5 Alfa |
| Media publicerar rykte som sänker Alfa och höjer Bravo | \+3 Bravo |
| SÄPO prioriterar STT:s säkerhetsinsats | \+1 STT per SÄPO-poäng |
| STT får motprestation för produktionssättning | \+ lika många poäng som erbjudits |
| SÄPO anklagar falsk spion i Bravo | \+5 Främmande Makt |
| Media publicerar nyhet som sänker valförtroendet | \+X Främmande Makt |
| Upptäckt spion (infiltratören i Alfa) | \+10 SÄPO, \-5 BS |
| Regeringen ger resurser till team X | \+ lika många poäng som ges |
| Positiv publicering om Regeringen | \+3 Regeringen att fritt fördela |
| Regeringen flyttar spelare | \+5 till nytt team, \-5 från gammalt |
| USA ingår allians med Regeringen/SÄPO | \+X USA |
| USA lämnar tips som används | \+X USA |
| Media publicerar skandal | \+X Media |

# **Förberedda händelser**

Nedan är händelser som kan hända under spelet med förslag på vad verkan blir.

3. ## **Händelser Orsakade av Främmande Makt (FM)**

1. **Desinformationskampanj lyckas sprida falska rykten om valets säkerhet:**

   * FM har framgångsrikt spridit rykten på sociala medier om att valsystemet har allvarliga säkerhetsbrister. Detta har lett till en våg av misstro bland allmänheten, med många som uttrycker oro över att deras röster inte kommer att räknas korrekt.  
2. **DDOS-attack stör tillgången till valsystemet:**

   * FM genomför en lyckad DDOS-attack som tillfälligt tar ner valsystemets offentliga gränssnitt. Under attackens gång kan väljare inte komma åt systemet för att kontrollera sin röststatus, vilket skapar kaos och osäkerhet.  
3. **Läckage av känslig information från valsystemet:**

   * FM lyckas hacka sig in i en testmiljö och stjäla känslig information om väljare. De läcker sedan denna information på mörka webben, vilket skapar panik och skadar förtroendet för valprocessen.

   4. ## **Händelser Orsakade av Brottssyndikatet (BS)**

1. **Infiltratör saboterar utvecklingen av en kritisk komponent:**

   * BS infiltratör i Team Alfa saboterar kodbasen för en kritisk komponent i valsystemet. Detta orsakar betydande förseningar och tvingar teamet att omfördela resurser för att åtgärda problemet.  
2. **Utnyttjande av systemets sårbarheter för ekonomisk vinning:**

   * BS använder en svaghet i systemet för att skapa falska röster eller manipulera valresultatet i en specifik region. Detta går obemärkt förbi i början, men upptäcks senare av säkerhetsteamet, vilket leder till en utredning.  
3. **Kampanj för att påverka valresultatet:**

   * BS använder sin ekonomiska makt för att finansiera en massiv kampanj som påverkar opinionen i deras favoritriktning. Detta inkluderar allt från påverkanskampanjer till direkta betalningar till nyckelpersoner.

   5. ## **Händelser från Team Alfa och Team Bravo**

1. **Team Alfa lyckas snabba upp utvecklingen genom agil innovation:**

   * Team Alfa spenderar poäng på att snabbt utveckla en CI/CD-pipeline, vilket gör att de kan leverera funktionalitet i små inkrement och få omedelbar feedback. Detta leder till att de ligger före tidsplanen och kan fokusera på att förbättra systemets säkerhet i senare rundor.  
2. **Team Bravo hamnar efter på grund av överambitiös designfas:**

   * Team Bravo spenderar för mycket tid och poäng på att planera och designa systemet i detalj, vilket gör att de hamnar efter tidsplanen. När det väl är dags för implementering upptäcker de att vissa designbeslut inte är genomförbara och tvingas göra om stora delar av arbetet.

   6. ## **Händelser Orsakade av STT**

1. **STT upptäcker och åtgärdar en kritisk säkerhetsbrist i sista minuten:**

   * STT genomför ett penetrationstest som avslöjar en allvarlig sårbarhet i nätverksinfrastrukturen. Tack vare snabb mobilisering och omfördelning av resurser lyckas de täppa till hålet precis innan en planerad attack från FM.  
2. **STT nekas ytterligare resurser efter att ha äska från regeringen:**

   * STT ansöker om ytterligare resurser från regeringen för att stärka säkerheten, men ansökan avslås. Detta tvingar dem att omprioritera sina befintliga resurser och lämnar vissa områden av systemet mindre skyddade än vad de skulle önska.

- [ ] # **Nyhetsrubriker**

# **1\. "Misstro växer: Falska rykten om valsystemets säkerhet sprids på nätet"**

En våg av desinformation har spridits på sociala medier, där rykten om allvarliga säkerhetsbrister i det svenska valsystemet har fått fäste. Många väljare uttrycker nu oro över huruvida deras röster kommer att räknas korrekt, och förtroendet för valet är på väg att sjunka drastiskt. Myndigheter arbetar för att motverka dessa rykten, men skadan är redan påtaglig.

# **2\. "Nationell kaos efter massiv cyberattack mot valsystemet"**

Det svenska valsystemet utsattes idag för en massiv DDOS-attack, vilket ledde till att systemets offentliga gränssnitt blev otillgängligt under flera timmar. Väljare kunde inte kontrollera sina röststatusar, vilket skapade förvirring och osäkerhet. Myndigheterna arbetar febrilt för att återställa systemet och säkerställa att det inte sker fler attacker.

# **3\. "Läckta väljardata skapar panik – valprocessen ifrågasatt"**

Känslig information om väljare har läckt ut på mörka webben efter ett intrång i en testmiljö kopplad till det svenska valsystemet. Läckan har skapat panik bland både väljare och politiker, och många ifrågasätter nu valprocessens säkerhet. En omfattande utredning har påbörjats för att fastställa hur detta kunde ske och vilka åtgärder som behöver vidtas.

# **4\. "Kritisk komponent i valsystemet saboterad – utvecklingen kraftigt försenad"**

Utvecklingen av en kritisk komponent i valsystemet har drabbats av ett allvarligt bakslag efter att sabotage upptäckts i kodbasen. Incidenten har orsakat stora förseningar och teamet tvingas nu omfördela resurser för att rätta till problemet. Detta kan få allvarliga konsekvenser för den planerade lanseringen av systemet.

# **5\. "Valmanipulation upptäckt: Brottssyndikatet misstänks ligga bakom"**

Misstankar om valmanipulation har uppstått efter att oegentligheter upptäckts i rösträkningen i en specifik region. Det finns tecken på att röster har manipulerats, och brottssyndikatet misstänks ligga bakom. Myndigheterna har påbörjat en utredning för att fastställa omfattningen av manipuleringen och vilka som är ansvariga.

# **6\. "Team Alfa överträffar förväntningarna med snabb agil utveckling"**

Team Alfa har imponerat genom att leverera en fungerande version av inloggningsfunktionen för valsystemet långt före tidsplanen. Genom att snabbt implementera en CI/CD-pipeline har de kunnat få snabb feedback och iterera över sina lösningar, vilket har lett till betydande framsteg i utvecklingen.

# **7\. "Ambitiös design fasar ut Team Bravo – stora förseningar i systemutvecklingen"**

Trots ett gediget arbete med analys och design har Team Bravo nu hamnat efter i tidsplanen. Deras omfattande planeringsfas har visat sig vara överambitiös, och nu måste stora delar av arbetet göras om. Detta skapar oro för att de inte kommer att hinna leverera systemet i tid.

# **8\. "Säkerhetsbrist täppt i sista minuten – attack från främmande makt avvärjd"**

En allvarlig säkerhetsbrist i valsystemets infrastruktur upptäcktes och åtgärdades av STT precis innan en planerad cyberattack från en främmande makt kunde genomföras. Tack vare snabb insats lyckades säkerhetsteamet förhindra att attacken orsakade några skador, och systemet förblev säkert.

# **9\. "STT nekas resurser – säkerhetsförstärkningar uteblir i kritiska system"**

STT begäran om ytterligare resurser för att stärka säkerheten i valsystemet har avslagits av regeringen. Detta har tvingat teamet att omprioritera sina befintliga resurser, vilket innebär att vissa delar av systemet kommer att vara mindre skyddade än planerat. Oro växer nu för att systemet kan vara sårbart för framtida attacker.

# **10\. "Internationella konsekvenser: USA och andra länder drabbade av liknande valpåverkan"**

Flera länder, inklusive USA, rapporterar om liknande valpåverkan som den Sverige upplever. Desinformation och cyberattacker riktade mot valsystemen har skapat osäkerhet och ifrågasatt legitimiteten i flera pågående valprocesser. Sveriges säkerhetsmyndigheter undersöker nu om det finns kopplingar mellan attackerna och om en gemensam aktör ligger bakom. Sveriges internationella anseende riskerar att skadas då landet uppfattas som oförmöget att skydda sina kritiska system.

# **11\. "Sveriges anseende hotat: Utländska medier rapporterar om kaos i valsystemet"**

Utländska medier, inklusive några av världens största nyhetskanaler, har börjat rapportera om problemen med det svenska valsystemet. Rapporteringen betonar hur sårbart systemet verkar vara och hur det svenska samhället nu präglas av en växande misstro mot valprocessen. Flera analytiker varnar för att Sveriges anseende som en stabil demokrati är på väg att urholkas om inte situationen hanteras effektivt.

# **12\. "Infiltratör i Team Alfa avslöjad – sabotör med kopplingar till brottssyndikat"**

En infiltratör inom Team Alfa har avslöjats och misstänks ha samarbetat med ett brottssyndikat för att sabotera utvecklingen av det svenska valsystemet. Infiltratören, som har arbetat som utvecklare i teamet, har systematiskt fördröjt arbetet och stulit känslig information som nu tros ha använts för att manipulera delar av systemet. Upptäckten har skapat stor oro och en intern utredning har påbörjats för att förstå omfattningen av skadorna.

# **13\. "Säkerhetshaveri upptäckt: Valdeltagande i riskzonen efter avslöjad sårbarhet"**

En allvarlig sårbarhet har upptäckts i valsystemet, som skulle kunna utnyttjas för att förändra resultatet av valet. Sårbarheten blev offentlig när hacktivister publicerade detaljer om den online, vilket skapade panik och oro för valdeltagandet. STT har beordrats att omedelbart täppa till hålet, men skadan på förtroendet för systemet är redan betydande.

# **14\. "Sverige kritiseras internationellt: Hur kunde valets säkerhet bli så undermålig?"**

Internationell kritik riktas nu mot Sverige efter att flera säkerhetsincidenter kopplade till valet har avslöjats. Flera utländska experter ifrågasätter hur ett land med Sveriges teknologiska kapacitet kunde misslyckas så pass allvarligt med att skydda sitt valsystem. Den svenska regeringen står inför ett växande tryck att svara på dessa frågor och att återupprätta landets rykte som en säker och pålitlig demokrati.

# **15\. "Nya resurser beviljade efter akut ansökan från STT – men är det för sent?"**

Efter en akut ansökan har regeringen slutligen beviljat STT ytterligare resurser för att förstärka säkerheten i valsystemet. Detta kommer efter flera rapporterade incidenter som har satt hela valprocessen i fara. Frågan som nu ställs är om dessa resurser kommer i tid för att göra en verklig skillnad eller om skadorna redan är för stora.

[image1]: <data:image/png;base64,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>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAhoAAAFCCAYAAAC3jHQhAABLFElEQVR4Xu2dMY7rSpK1ax3d1rPlTq+ggTEH7cgdq42H584GCo3uRQwwQJsPEMabBZT72wOtYbZRvyKTwUwGk2LwkFQFxfMBcW8VxSAjRGbkYUqV+fHPf/7z+//+7/9W21bHodFoP2v/+7//G9L++7//exTrT9s71T0kF8Qnqp09F8THax//+Z//+U2j0Whqv/zHv4Y1GyuNRotvSWj8v3/+12r7+voabaPRaLStLGKNiRgTakguiE9UO3suiI/XKDRoNNohLGKNiRgTakguiE9UO3suiI/XKDRoNNohLGKNiRgTakguiE9UO3suiI/XKDRoNNohLGKNiRgTakguiE9UO3suiI/XKDRoNNohLGKNiRgTakguiE9UO3suiI/XKDRoNNohLGKNiRgTakguiE9UO3suiI/XKDRoNNohLGKNiRgTakguiE9UO3suiI/XKDRoNNohLGKNiRgTakguiE9UO3suiI/XKDRoNNohLGKNiRgTakguiE9UO3suiI/XKDRoNNohLGKNiRgTakguiE9UO3suiI/XKDRoNNohLGKNiRgTakguiE9UO3suiI/XKDRoNNohLGKNiRgTakguiE9UO3suiI/XKDRoNNohLGKNiRgTakguiE9UO3suiI/XeqHxjz99fH98FLM71pb2/eO/DbbtGSSNRqOtrzG/9rXtr398XuO8tj6mOIbkgvhEtbPngvh4zYxo/O3740+/9r//8kcRHX9IP//jL3/oG6kKjd8f2/78W953zyBpNBptdY357V++pcb94/FzXefWmI2pfljzPLRFMpuLxxCfqHb2XBAfrz0VGmIiKn6XHasGo0JDRYjYnkHSaDTaFjVG6pg8IP2/v//6qGEiPMb7LLEtYsLs18eD4PL4Pz6yT1271ZBcpnx++eMfvn/5kz8+RJD98pdtxKLaVC77Wx5pq+3Pv/2tsd/Y58+P97j13iG5ID5eeyI0JJE/9EIjNUx5Ex6v1x+zqO+eQdJoNNpWNUY6218etUvqmH1tqbVi6mvmP30dqO1k7MfSc/bXP8los6dT/zWN5ox/ztbKRT5i+uuj0/v979ns6y2fOpY/O/KXfufPjxxEnEjH+ec/efL/W9/Riun7PWUiyv4s4qc28163cpnLfxsbXhd5/+beN3l9ybUc3WON41ufLe2J0MgXUkxHNNKF/a36jsZv//L9179n3z2DpNFotG1qzK+pnkkH0iq2S60Z02+l42uNHMyaq0PLD4Lj7c8tda7Jxr7NXP7+b0878aGPjLJIJ/6ROnY5z5JRjVeYChOJc65zTjaT/1Zmr0vr+tQ2Ek3JynvdzGXGEB+vneSvTsYfCbWsfhIZ+HYFaYvCdBarv2y35AlN9q0/rhtfj3UmTwuRr6PE9/ujo/rlL3+buB+LTb3e2t7attS8X6Cs31/1+Ud66h77t7ZNWcQas1VM0tHUtcZjv//2b6mDkSdu+9qUZZ/HA2KjHiK5ID5jk7y7++Pv47imTGu6975MowTpezrt+26bXOzogUdoyYhOFkD+EZ3l11L2l4GBNJrXDRDM+Wxl5xMav+WOphYPYnIBWt9HSb4ypPdb2d7y7y11quUzt3Es57CR0Jh434uCL++fFRpz+3qOq08vnn319dfbsKPpY5l874axlqei4fsmoqXsi9+btqCXGPL7V5+/5aPbyz45LolPOgH5Wb9c3rKINaYdU64Z6UunM0+mdScj75+/o/m1H02Wp25fh5aH2PO+88PtYvJ9lv4++uM4l5ZPuo7Vtbavjy0LDb1XfLn8V1/T03duGq+PrBtpku/mtOJq5aL3pb2vvebNpTe5lg3hYE0/OvFey1rISP7yvz2m9dnSzic0HvaP36RhlmL8S9ewtdNq+Q5utL/nAlmLkvJ/99kfeGO+i42Exj/L+15vS78/Gpd2MFNCY2pfLQT/6Iabdd/0hFjvO3ftWvv+hOl3oR4FpB6FsPds2mZGKVrbZYi1fk/re/NZp96yltB49r/1mbsGava8ahFrTCum3Mnm4j/3WbvaX9Nw/rj4P7Na4HmvZR7Ry6LGvobk0vKRuJYJjWJ7fQ9Cv2NRm92nlUttrfxbVn+cYV9rWxGb8n6J8B7vYyw9fCy7lnMjYC2frex0QkMvihbe3/8uJt9Az8VYnhKGTyGdb/dUqR2SHf0o/+ON7J3MCg193/v3qRYa8tlualzlOkwKjX5feWosT35//mN7X73uSfk/vXbVcX/quj3i0yIjMdTiQLbZuKeEhtx/g/yq97S+N/snYqetExrd+/r0Gsj/08U5Yo2ZiknyEZv/6wHZtxYYv7pFA2L/+O0hGiZimsolPzl/pCdh+9qkj5yn0Zlbk/tRHvRyXGrzfr2/COnufrev1Sad7Nx+rVzq70JMddC1DcRM43WP/f7b/IjGnNlc6jbZ+r3ls6WdTmjol8D0pisFYVz8rG/eXoahJwtlGsqUfaaL5rubFRr1+67b0v/V+5dsVmgM9x0dV19rfnQyd+2Gx/oJ0/PL/ajD1q17VvbV19VXRyukKNb3trxP/b4r7s06Dv04RmOuz1/HNPBJ7Wh8DaR9qe8z8ROxxqyPaTzsPTfcLqMfg6Hw9N7N+KTrkK+5dIL1NVJDchn64J1r/ssZ/z2pAsM7ylAs594SDUj+Q/vbUDD9JX/Xarxf2zSnv874yHe4Wh8F12ZzsfdH632zPlvaU6GREyiFIReK8X5iewZJoxXrRimqp//aWo3OZ+W4+DFoe5qtMb2waTxpe8yOCKnVI2XWrI+NSTpLeV2/N+C5l+xn8q37umWpI3PmbjualsCxuQxHGfJHeva4Qx895vjYPst9jX6UPWW//yW3UflCY6vDfGbpnpn4SGOYixENE/k/Mx0pt9trqwWWNxe9luW7KeP3215LG7v9veWzpfmExuCJfryf2J5B0mg0Wl1j0pB71yGX71iVER55gu9/l489uw65HonpRUP3vRgZTdERmHwM+X5L10F3AvS50CgFX4/h7TxUNHk+bsjxtjvLKUOEhrVW/W/nPz72lKXr+HiP5SNs+5rLums3dz7Zx/45qPVB8t/C9GOd1nctWtb3y93+rS/DtnLJomZayLV8trJFQuPZG7FnkDQajVbXGBUG5fXh93FEMIggKN+7yrVLO1zpqO1Hpf33iNJTaPddib/nPwmshcO00Mj7lQ5JOgPbwcc1m4vHEJ+oFiKXh9D8ZYN7BskF8fHaIqHxTNHtGSSNRqPVNWY0omH+aki/I2TFRP3dIPuaWtqnOp7uXx+vFdPRDckF8YlqZ88F8fGaT2h0Kp3f0aDRaD9ltsZoXarFQxIQ/yxfRrZiQvep580pX2Idfq9C95Wf7Rdtp2I6siG5ID5R7ey5ID5eeyo0ltieQdJoNNoWNWbuy3lLbYuYohiSC+IT1c6eC+LjNQoNGo12CItYYyLGhBqSC+IT1c6eC+LjNQoNGo12CItYYyLGhBqSC+IT1c6eC+LjNQoNGo12CItYYyLGhBqSC+IT1c6eC+LjNQoNGo12CItYYyLGhBqSC+IT1c6eC+LjNQoNGo12CItYYyLGhBqSC+IT1c6eC+LjNQoNGo12CItYYyLGhBqSC+IT1c6eC+LjNQoNGo12CItYYyLGhBqSC+IT1c6eC+LjNQoNGo12CItYYyLGhBqSC+IT1c6eC+LjNQoNGo12CItYYyLGhBqSC+IT1c6eC+LjNQoNGo12CItYYyLGhBqSC+IT1c6eC+LjNQoNGo12CItYYyLGhBqSC+IT1c6eC+LjNQoNGo12CItYYyLGhBqSC+IT1c6eC+LjtSQ0tkCCJISQvYhYYyLGhILkgvhE5ey5ID5eKDQIIYcgYo2JGBMKkgviE5Wz54L4eKHQIIQcgog1JmJMKEguiE9Uzp4L4uOFQoMQcggi1piIMaEguSA+UTl7LoiPl0mh8Xn5SP/fPy/9tstH3taiBHn7/njsJ/YMOdb1dv++m+163inmXv+4fNpNCxnHJHw2Nl67PD+ut/S7J+8aeQ/m8hH0+IScmTWFsG6b2m6VNc1rTUzRQHJBfKJy9lwQHy8zQuPed7DSOJ91ihrkx8e135Y7yEfHfcvbrhdp4CJc7qmhS5cuh/+8XvqGr+eoj9OKQfa/phcedhdxkwVRFhrDbXJ+2X6p1IK+JsfMv398XzTe7JS2PbTQ9+1qClPvU2IUgaWUs0gcn49zV+9Jd0yhvB/5varPISLkrsfs3j9CzgxeCIdtU9utlINnD08e8JjigeSC+ETl7LkgPl6eCo2PSxnN0G1TaJDamecnCGnQfXeZEFEhv6vgSA2/eqRI5zWNX48j+6UYHp33ve/N9fjdqEInNOptevhaaOhITX3uXHRyTLpZ96tHNHTU5JIERI5LYlLKviV3+V+LmggXpbwfufilY6mw6AVGdXJCTgpcCG3b7B9CupqRHjLKPkuAYwoIkgviE5Wz54L4eHkqNIS60/cIjcGIRicQcjd565/krdBQZJuco+6IBfldTPatY5ARgfr4ggqNept2/LXQEOTVJCoGAqAbZTF9+0BomLHWnGfZVnYtP4m/jl5kAWHej068yLH7j6uqAmnCIeR04IWw1Ta7NqdtrGprS8BjigeSC+ITlbPngvh4mRUa0jS1k/UIDWnU+nlobt7a6eePS+RjhNLpdiMa3f79iIVsM9+16Ic70+v190DmhYbua4WGiigdRflMHbyJqdunFlz9xx3d63rUev/MPY1i9NvkI5z0e/n4qH8/KqGR/pfXrp1oA4sgIe/EmkI4apvVx5Gj1xawJqZoILkgPlE5ey6Ij5dJobGUPYNcS/ruxf02GqWAcXf8wxEbN/LR0HcRdhcdCSHkxESsMRFjQkFyQXyicvZcEB8vpxAahJDjE7HGRIwJBckF8YnK2XNBfLxQaBBCDkHEGhMxJhQkF8QnKmfPBfHxQqFBCDkEEWtMxJhQkFwQn6icPRfExwuFBiHkEESsMUhM//Pbv4c0JBfEJypnzwXx8UKhQQg5BBFrDBKT7eCjGJIL4hOVs+eC+Hih0CCEHIKINQaJyXbwUQzJBfGJytlzQXy8UGgQQg5BxBqDxGQ7+CiG5IL4ROXsuSA+XjYXGv3EU0sXN2vMTfFsgrCltObQ6GfqPDMyHXM3SZjMSKqTlZGfp3UddFtrjQ57P9fr/+hsu61jLsUeI094l8+ls+zOYeORBRbtjMCWNYXw8nkbnvNx3+e7fjjL71KQmGwHH8WQXBCfqJw9F8THy7zQ6Gez9BUBKWpl33taL0Vm9dRjSKemRTL9r8fv1lXR/WR67iw08syk8rPOMCr/X67Zr16JUX11//z7JRWYtI/JJf8/nAlUz6u+707KvRMael3qFXvJz/B5/WwI7WGnmGfYzffqM4E4XBZg3bVtxZXb5i3FUC9SqPHojLwtcTRY92eU7xC4EFYPMWm6f4mjExqLH4gMSEy2g49iSC6IT1TOngvi42VeaHwPi8YUvdCQzrovHiI0ckNOK6im41z7hi8FqBS+XER15EHXPdHXrdDon8LFpGOsRIT6Clr4ynE7QZF+LlOO2/MK3qezo0OhERO9D0v7GwoNuWyDNXjkfu7agS7Hk9cDqvdZf0/buLRtpvPK8avpvSW+dF/d8+rJw1oynK1XV3meAi6ERmiUzcOHGwQkJtvBRzEkF8QnKmfPBfHxMis0hguOTdMLDV3ZNFWQIjR0qXR9upIGn4vTc6Gh5/UIjRorFuS4dS4UGgV9L73XmryG1hN+3VHKzyOhMWA87f4WItLGpW1Tjt0SGvWiiDXjeIf5WPBCWN61+vA/taia7eCjGJIL4hOVs+eC+HiZFRp5VEEXHJvGCo1cjCqh0T01aHHpnyB0JKJbQKx/SrpXT05yjGpEpCk0Kt/0pGfEgj55aS5y/BzD8KOT+rxnExpSkNP7sHI4mWyD7dAFGaGw7UjbUt+mOvS1eqSj/hgFxcZVHgJKDHVc+ffhefUjz6n9W6wphKPj/+CiaraDj2JILohPVM6eC+LjZVZoeNkzSEIIiVhjkJhsBx/FkFwQn6icPRfExwuFBiHkEESsMUhMtoOPYkguiE9Uzp4L4uOFQoMQcggi1hgkJtvBRzEkF8QnKmfPBfHxkoSGnIBGo9FoNBpta+OIBiHkEESsMRFjQpFc7CjHnCE+iL2Cd7uWS0F8vFBoEEIOQcQaEzEmFEQ0ID6IvYJ3u5ZLQXy8UGgQQg5BxBoTMSYURDQgPoi9gne7lktBfLzMCg37N/NTaJD6N+mfMpf3U/L8FeTnKfNo5OvH6xKD+rrU6JTeHmxbbE0DvhQ76Vee4n84L4WHpbGtKYSf18v35drND3P//K4nC1szb8yamKKBiAbEB7FX8G7XcimIj5fthYbODDpTNEgQuKhaTKrrYvEKDbtwmf0ZxR6jX0uo4+KoGUhsawphpEXVooKIBsQHsVfwbtdyKYiPF5fQyKMUy2YGFVITTk8P6l+vdTCckTMLk/tgkTSyP/Usq1zrJA71dbEkoTFYIPB5uykd7GX1A0BrUbU0xbhO4f2Iq+7QNaa8uOL43EtigwthsEXVooKIBsQHsVfwbtdyKYiPF5fQSDgXPKobrk7zPSg4HzpcOlxjRIVG/rVdYMk+UGjERK+LtJlac+iIRi006nZTtzfZlnbXhQxnOnMP/dIA3Xl07SA5z+Ujr5YsyMhGel32NUsRZJbFBhfCYIuqRQURDYgPYq/g3a7lUhAfL26hMbfQ1khodMKkWTzSa7k4agFtFUzyGrRDO9saL9GxIxraGcpmbVf5Wk21m/tokbJme1xIc0TjW+K79ouolc59auRgeWx4IWy/P7XIeeWialFBRAPig9greLdruRTEx4tLaMhCTnPf7eyFRvd0UH/Jq/5dfr7mFp4avywNLV/Sel4wyZ7wy6AxsUJD2kd58u5+rkS7bTfScdun9bnO3MOU0NARgvqjE32YsEIDiW1NIRx8GfR7KKYlhvq1JayJKRqIaEB8EHsF73Ytl4L4eJkVGl7QILXYjIsqIYQU0BqzJxFjQkFEA+KD2Ct4t2u5FMTHy48LDUII8RCxxkSMCQURDYgPYq/g3a7lUhAfLxQahJBDELHGRIwJBRENiA9ir+DdruVSEB8vFBqEkEMQscZEjAkFyQXxQbDCYw+TXOy2OYsKcl0QHy8UGoSQQxCxxkSMCQXJBfFBsB38Hkah8WU3bQaFBiHkEESsMRFjQkFyQXwQbAe/h1FofNlNm0GhQQg5BBFrTMSYUJBcEB8E28HvYRQaX3bTZmwuNMrfy+ufqy6ZlaFeaK2bonw00Q/ZkqtMDX0ZLoi15IqRfbBz0eg2Reaq8FynwfWV9VNm5qpYz/jP1O28G604PH/dvqYQclG1eZBcEB8E28HvYRQaX3bTZuwuNJZNZz0WGmRP6om6rpwZNAj6/tvZeOUaaZuQdjbfPsr1TbNz6lTzdkpOgFqcDhkrBis0ytTqZfbgfYWGnaI9n7efxXQFeEzxQHJBfBBsB7+HUWh82U2bMSs0tOjZJxDLnNDQ4pIKXvc0Idv6opr2q6clLyMaUqjk57xP9r/fPjcpmOQ7PeHJe8m1TmJhZ8qUDrJfabcz7TSLUGwI9Gp67bl27Gd0lo6uM9e1Tbr22yK337z/rkLDrHVSL0C3toTAMQUEyQXxQbAd/B5GofFlN23GrNCYW7VVmRMaSSyYRYzk2MPj379llUf9uRYamSJWBAqNDbh3C1t9l46NQuPn6UeVulVaBRETsl2vTxYaH6nN1CNStU99fRUVJ+voDtqdqwiFCaFh9usfNvpa0BYjNXAhnFhULd3v9zwypA8xS4FjCgiSC+KDYDv4PYxC48tu2oxZoVFGNJ43RA1SO6txpyWfy5YRifx/LpxC/TSWi8600Ej+3VM4WUf9Fsq1Ku8/+SmmhF4SCPL9gq4T1/aRv/NQCY2K+vrmdnffaLr/cduTWOp1TtK5GiMarVriCWlNIbw8TjD8mETjv1FodCC5ID4ItoPfwyg0vuymzZgVGl72DHIKT3EihLwHP1Fj5ogYEwqSC+KDYDv4PYxC48tu2oxDCg35BnnrqYgQ8r68ssZ4iRgTCpIL4oNgO/g9jELjy27ajEMKDULI+YhYYyLGhILkgvgg2A5+D6PQ+LKbNoNCgxByCCLWmIgxoSC5ID4ItoPfwyg0vuymzaDQIIQcgog1JmJMKEguiE9UkFys8NjLloLkgvh4odAghByCiDUmYkwoSC6IT1SQXKwg2MuWguSC+Hih0CCEHIKINSZiTChILohPVJBcrCDYy5aC5IL4eKHQIIQcgog1JmJMKEguiE9UkFysINjLloLkgvh4cQsNOx2yRYP0zvQ3NSkReT1lAqe82NWaRabIdjxrR+PJ6szU42nhsKH/1LGW0q4FeXIuN0B8awphfa56CvL0+4r5eNbEFA0kF8QnKkguVhDsZUtBckF8vLiEhjTKdnEp1EEOCka9UmP1c2r4a1o42QTpHPQ6TC3mRX6Wkab4zkJDZ9ycXOPkuwh6uaZzbdiD3CN2pk9Btg3jKf/Lee8PETsWR8viwwthqTN55tuyqNrcOefAY4oHkgviExUkFysI9rKlILkgPl5mhYY2xCVPG0VYfFZrG1wHjZojGnHoV/Xsrg+vTRymVtL1Cg3tVOUKr+1UlbHQ0NGMfB8N4rp166o8/m8JjSXxwYWwWuskhZAeeOQe1yUNPsoS8guBYwoIkgviExUkFysI9rKlILkgPl5mhYbOwDlV8JSm0HgUl0ZtScdkZxYHjmjEpNXmtD16hIbuK21NPzpotcelWKEh94seX+6lOq6+nTfWJloaH14IhyMaSl4nphMYlRhZAh5TPJBcEJ+oILlYQbCXLQXJBfHxMis0tGhAIxrypNMVk7TEdbddfqbQiEO/9PgnF1WLRKvTzU/99/SaXcCs3r3VvuZGDLxYoVHfL/LzMK68eqycuxYaSHxrCiEXVZsHyQXxiQqSixUEe9lSkFwQHy+zQsPLnkESQg5O9TEqSsQaEzEmFCQXxCcqSC5WEOxlS0FyQXy8UGgQQnZFRjaunytVxnfMGhMxJhQkF8QnKkguVhDsZUtBckF8vFBoEEIOQcQaEzEmFCQXxCcqSC5WEOxlS0FyQXy8UGgQQg5BxBoTMSYUJBfEJypILlYQ7GVLQXJBfLxQaBBCDkHEGhMxJhQkF8QnKmfPBfHxQqFBCDkEEWtMxJhQkFwQn6icPRfExwuFBiHkEESsMRFjQkFyQXyicvZcEB8vFBqEkEMQscZEjAkFyQXxicrZc0F8vFBoEEIOwZoac/ksE3alicTut26+0HV/drsmpmgguSA+UTl7LoiPFwoNQsghwGsMF1XzgOSC+ETl7LkgPl4oNAghhwCuMVxUzQWSC+ITlbPngvh4odAghBwCvMZwUTUPSC6IT1TOngvi44VCgxByCNbUGF0dtkeXr2+9toA1MUUDyQXxicrZc0F8vFBoEEIOQcQaEzEmFCQXxCcqZ88F8fFCoUEIOQQRa0zEmFCQXBCfqJw9F8THC4UGIeQQRKwxEWNCQXJBfKJy9lwQHy9JaMgJaDQajUaj0bY2jmgQQg5BxBoTMSYUJBfEJypnzwXx8UKhQQg5BBFrTMSYUJBcEJ+onD0XxMcLhQYh5BBErDERY0JBckF8onL2XBAfLxQahJBDELHGRIwJBckF8YnK2XNBfLxMCo3PS57ARtcCyFP2drPpNdAgdR2Bn6YVZ2tSnpznfTBj4DP0fViLTIU8WOTpuyz8dPWu85RmM3REDs56SEgk1hRCLqo2D5IL4hOVs+eC+Hh5KjS0YdZMCYmm0LhdB7Pu6c+XRy97/7zkn9Nr9++Pa95XOmDt/K8t31os9MfP59R90sJJl3z8tLZB4l5e6/arzyXHtef6SD3+OI56n/SznutZ3CWQwayE+VcpfJ/97/V7WL8vU/lKnHLu/HsnCOXnR1x6Xrd4ISQocCGs2pY0g9Q2O6HReiBZAhxTQJBcEJ+onD0XxMfLU6EhXVTdQV27UY4WLaFRP/2nTr3ra6Xz09d6odE1eO00yyhDDqD37TpwoT++dNym866P12+T/SvxI7+3znUfdOjD1+wxJC49V+tYdc6KjhZlbt1CT1NCo5y3zld86jj1mCJyRMQlHsfU864tqIT8NHAhNEKjbK5EeVVXlgDHFBAkF8QnKmfPBfHx8lRoCNJx1b9P0RIatSiQBq59fhYa+bX8/7zQUN+6IOjxByMCXec6KTTMxwjPzzUhNMwxngmNOmelvJf3wYiL+g1j1tGL6yDf+v20QqMXXY//e6HBIQ1ycPBCOGyTykDggx8v4jHFA8kF8YnK2XNBfLzMCg1BOtJ6FKBFERrD/WQU5NJ1xPIELssx953fY78sZOaFhj69q/BRZNut66zTuT47QTAlNLr9VLC0zvV5vaQ4VQQNXrt0Iz1yjEsnAp4IDZtzJr+mH9f0sXTnrdH3vv+9yreO0wpDOfb9fuvPS5lBjs6aQmjbVl1HpP3YdudlTUzRQHJBfKJy9lwQHy+TQmMpniAHnWrX2XuftHsB49w/CnXOg+3OPLCPPPKIkZ639V0bQo6Gp8a8mogxoSC5ID5ROXsuiI+XlwoNQghBiVhjIsaEguSC+ETl7LkgPl4oNAghhyBijYkYEwqSC+ITlbPngvh44aJqNBqNRqPRdjOOaBBCDkHEGoPE9D+//XtIQ3JBfKJy9lwQHy8UGoSQQxCxxiAx2Q4+iiG5ID5ROXsuiI8XCg1CyCGIWGOQmGwHH8WQXBCfqJw9F8THy+ZCQ/8cc/GfVDYmzJmbJGwJg2ksOm7XekKu8zKY1p2EoZ/hdUD+02WdS6Um388V99toDpaG2yJKTMM/oa6R+2lqXgrbDtMcMF0yaR6cJ3/2vaYQDubRuMvcM+W9xf6EPIPEZDv4KIbkgvhE5ey5ID5edhIaumDRAn5AaExNPnYqZCbVRmdBfpb77bM55X8/8ZuZcl+w93OZvt7MHAsyiKlxfmEgbBqioW6HGkt+KNEXyiRzFrwQ2tl9c+xymsUPRAYkJtvBRzEkF8QnKmfPBfHxMis0tEB9zjTIWmiUgtc9fX3Kk1WZSluPKT9rsdH/s68sspZnCNVCoDNyatFIBU2eTB776eyi8mQkxVB9+/3E/z7MRUqOnivvNzxv7fvOSFGn0IjJWGgPO27px/W+LT+P6RfW+1iwMvAEfRvSCffMOWuRIPdVadelHVrK/Sd1op2DABdCs9ZJvehhK54lIDHZDj6KIbkgPlE5ey6Ij5dZoaGrrLqFhgiKR8NWUdBPBS6NO61ymj+uEKSRl8KSK6A2fNkuxUyL0EhodBVTfpYYNU4tfvYJTo5b52KFhj1v7fuu2PeMxKIIcu0Yhyohieeqo0zXUKfq73a113XtE7wVP+mjlOqcdsp/e/7c5ktH32pj9XpJNXAhnFhULdWWrlbdJA8AJCbbwUcxJBfEJypnzwXx8TIrNLSj18IwRS80KmExEBryf/rMOBeRyyU3bNup25GF9NotF8jr7V5GG4zQkJ/kdT2HPa4UuDoXKzSa553J+V3giEZMbKcuaDss93K+b4eiPVP/XouWNdi2YY+X2uddOu68wvCwXQ+F0fA7KHlEUjr81kcuwppCKN/9GIosDeRGodEZkgviE5Wz54L4eJkVGqnzlWIx8ZmsYoWG7C9deL/g2GChsmGBkp/v+qyRvqiVX7PFUYpr0hKybSQ08pfJdKGzdkEsuYh7Fi3d57eN81JokJ+kJTT0HtYvg6aPCrUT70S4Ivtly6/ndraOOqap49kvg9b71e1e9tMYhfxl0OJnWVMIIy2qZjv4KIbkgvhE5ey5ID5eHELDx55BEkJIxBqDxGQ7+CiG5IL4ROXsuSA+Xig0CCGHIGKNQWKyHXwUQ3JBfKJy9lwQHy8UGoSQQxCxxiAx2Q4+iiG5ID5ROXsuiI8XCg1CyCGIWGMixoQiuVjxMWeID2Kv4N2u5VIQHy8UGoSQQxCxxkSMCQURDYgPYq/g3a7lUhAfLxQahJBDELHGRIwJBRENiA9ir+DdruVSEB8vFBqEkEMQscZEjAkFEQ2ID2Kv4N2u5VIQHy+zQqP9t/xjNMjyt/tzflzMLAJ6rXgtAlHNZDnVlnR7a26r8cRdw5k4115vO++K1Aid18Y990w3b43GNZVnzZpC2HoPlNZ76GVNTNFARAPig9greLdruRTEx4tLaMhEOnNrAvRCo18JsQgJadQ6wVAqjulg+fW7TF/88MkF6i4bRoWS7IwsrDZ3gcmLkJkqy7Vo9YH1DJf6s052Jb9Pddj1JUavt7RT+/Ahv+vMmio06sm39FQtETKYHbSxsGINXgjLuyih1IuqWdG0FDymeCCiAfFB7BW827VcCuLjxSU0RCRMFS9lLDRyQ9aiVK8rkLeVqb/z7IZ5mzwZodMBEwQKu3ioCGgvxT7osFPnfOun7xaa19OMkqyhJTQkYhkZ0AcGWQ6gj6cbMmitYeJdUE2AC2GwRdWigogGxAexV/Bu13IpiI8Xl9BILJ2C/Ds3ai2U/bBlWlitCA191tACldt96zmO7EmrEyA/xbj3qxcjGwgNmerfCPPUYXcLnSXut1GHuuZ6a03QeHqh0cVWx6MPG7KtzkFojXA8a/lwIQy2qFpUENGA+CD2Ct7tWi4F8fHiEhp55GFcFGqs0KhXXRVkKFXFih3RKOuMUGi8lvmFrMhPoKqgG6m42k7w3n0sISMe8lrerwiA4f61yNBF2NZc76kRDUHbcT2i0RqtmFpQ7RlrCmGkRdWigogGxAexV/Bu13IpiI+XWaHhZW2Qaz8rJYS8N2trzB5EjAkFEQ2ID2Kv4N2u5VIQHy8/LjRkVcX0PQ37AiGEVKA1Zk8ixoSCiAbEB7FX8G7XcimIj5cfFxqEEOIhYo2JGBMKIhoQH8Rewbtdy6UgPl4oNAghhyBijYkYEwoiGhAfxF7Bu13LpSA+Xig0CCGHIGKNiRgTCpIL4oNghcceJrnYbXMWFeS6ID5eKDQIIYcgYo2JGBMKkgvig2A7+D2MQuPLbtoMCg1CyCGIWGMixoSC5IL4INgOfg+j0PiymzaDQoMQcggi1piIMaEguSA+CLaD38MoNL7sps3YXGiUmUHzhEB21sLn1Ks8dBN6VTONkn0okzfJxEoffM+DMDWplnudErNwmTA38d4cwynDx9OjC61tTRbGt6YQ2hlJ6/NMvM0u1sQUDSQXxAfBdvB7GIXGl920GS6hIY1yrrRNCY3UwK9lCuRUPNPCacPiojMdym71dORyPJl5UGYW1dkFdSE2d8Elk8j7aFfeHM6gSH6C+rpY9L7P7Ub2uXdtqi3qVezLdV0zMV69oNr0A4S0W31gkLgeeVzKjMCt83vjwwtheR9TTeGiak2QXBAfBNvB72EUGl9202bMCg1vQ5wSGlpEcuPO5Ufrp2wbHr+ehngoNDJdh9j5U2hsg3Zoei2mOxHySuaERvq5E+V5z/b+2rHKq972PIW2RZloT7AjEP006J0A0ojkfzt1ueKNDy6E1Von6a3rRVmOrjzoLAeOKSBILogPgu3g9zAKjS+7aTNmhcbUU5KlFxq6WFPXuOunFX1SHq+9oGRxkV+fFhrqT6GxDRzRiIkVGtpW5L4fXqvpNYL6UcDPvJih2JpmY8WCFaV6jixAyonknNZXaMU3VXPwQljelzr19FCkImRmifop8JjigeSC+CDYDn4Po9D4sps2Y1Zo6CqQtuhZNEgpfKXQpA2jZaL19bRZj98VJikErY9OuoMN/Ck0toHf0YiJbXPatpIYTx8lPkRD6ujbQkO/i9C3xe/nIwYe+rao7dbcK30EqeO+p/Pp+a3QWBrfmkJoz6MLPDZfW8CamKKB5IL4INgOfg+j0PiymzZjXmg42TNIS/pcurH0NSEkEvWXu9fzyhrjJWJMKEguiA+C7eD3MAqNL7tpMw4pNAgh5yNijYkYEwqSC+KDYDv4PYxC48tu2gwKDULIIYhYYyLGhILkgvgg2A5+D6PQ+LKbNiMJDTkBjUaj0Wg02tbGEQ1CyCGIWGMixoSC5IL4RAXJxY5w7GVLQXJBfLxQaBBCDkHEGhMxJhQkF8QnKkguVhDsZUtBckF8vFBoEEIOQcQaEzEmFCQXxCcqSC5WEOxlS0FyQXy8UGgQQg5BxBoTMSYUJBfEJypILlYQ7GVLQXJBfLy4hcaziXSEOkjP5Dd2RkHyM1xv9zQR1Mx8bOSF6KyfgswZU6blL0h79M4jI9dY1gfS3T3t8xl1fEP8N5HO/qkTfkk9mLsH1xTCy+etn/E25X+/PZ223cuamKKB5IL4RAXJxQqCvWwpSC6Ij5d5odHNAIgKDZ0ZUKcgTsd6/JJm45urLOQlyHXxdlpkb6RNdBfj/tktIFhmsVRyG+pm2r3mNqptTNpcq2WlbTIjJjjddqaKb0Q3c28nHnRW3zzz5lgsCfUCZ3PlAC6EVb5yilpo2JlNlwLHFBAkF8QnKkguVhDsZUtBckF8vMwKDS0Q008xmabQqKYXl+PoFMoCRzTikDqzuSpPXkgRGop2kLn9dM/i+oTeT/F/SR178u7antK346QT1nWufXzmHFNCQ9D6IfvrrSYrMgv6EDN3C8KF0LyPZXM3qtK/r8uBYwoIkgviExUkFysI9rKlILkgPl5mhYYWgbmG2BQa9/ZS7lL0KDQCUBXgfjE8EgBtM+X/uhXVoj8LEF1D6FqERsVoNGEroaE8BEctYJ4JDcWueyLsJjT69294glSauKhaD5IL4hMVJBcrCPaypSC5ID5eZoWGkJ5CEKEhPBpwER550a7ul9XDlmQ98lSJLpFN9qJ05LIc+8W0k7rdiLiQ37VdjYRG1/7Ees0PdqoFK2W6OLv7SD/ueSY0NKZaBO0nNIbxCXU8EgfaBtbEFA0kF8QnKkguVhDsZUtBckF8vLiEhoc9gySETHMWwR6xxkSMCQXJBfGJCpKLFQR72VKQXBAfLxQahJBDELHGRIwJBckF8YkKkosVBHvZUpBcEB8vFBqEkEMQscZEjAkFyQXxiQqSixUEe9lSkFwQHy9cVI1Go9FoNNpuxhENQsghiFhjIsaEguSC+EQFycWOPOxlS0FyQXy8UGgQQg5BxBoTMSYUJBfEJypILlYQ7GVLQXJBfLxQaBBCDkHEGhMxJhQkF8QnKkguVhDsZUtBckF8vFBoEEIOQcQaEzEmFCQXxCcqSC5WEOxlS0FyQXy8UGgQQg5BxBoTMSYUJBfEJypILlYQ7GVLQXJBfLxQaBBCDkHEGhMxJhQkF8QnKkguVhDsZUtBckF8vFBoEEIOQcQaEzEmFCQXxCcqSC5WEOxlS0FyQXy8UGgQQg5BxBoTMSYUJBfEJypILlYQ7GVLQXJBfLxQaBBCDkHEGhMxJhQkF8QnKkguVhDsZUtBckF8vFBoEEIOQcQaEzEmFCQXxCcqSC5WEOxlS0FyQXy8UGgQQg5BxBoTMSYUJBfEJypILlYQ7GVLQXJBfLxQaBBCDkHEGhMxJhQkF8QnKkguVhDsZUtBckF8vFBoEEIOQcQaEzEmFCQXxCcqZ88F8fFCoUEIOQQRa0zEmFCQXBCfqJw9F8THC4UGIeQQRKwxEWNCQXJBfKJy9lwQHy8UGoSQQxCxxkSMCQXJBfGJytlzQXy8TAqNz8tH//Pl8/79fb99f3yUbRYN8uPj0m259a8p9THH3O2G79v18jj3rfFKx/3Tbhlw7WMpSA7JruP41nD5uNpNhJANWVMIP6WWXLt68agbpU49asLleR15xpqYooHkgvhE5ey5ID5eZoXGR9eBasesv1uK0FAxMe7InwmN+2dLFMi2Oyw0lI9LiVk00z7sdmBCyPeaQqg1ZFjDpBbcrtM1yQMeUzyQXBCfqJw9F8THy1Oh0RrBSKMbDXqhcZGnBfHLjboWLPKzeOfX79+ft0cBuGWxoEJDRjBk9CTvV4SGPoHoscX32sXXv1aNUgwLiMZ870c06jQ0T/Ev8eYYe6E1iv+WjnGp3qOp94YQsh64EFYPJFIhpG5om1/bZOGYAoLkgvhE5ey5ID5engoNoR5WrIcbLbXQkOZ870c0yrOEHlMaugiLutNXoSHCo+/4K6HRF4TbtRr90CeU7uOQKj4VIZlxNRkMnfajNRJTt/2mAuNx3Itsz0JD0Pi7Hbv/h+8VIWRb4EJohIaSHhIer0l1uDVGVD3AMQUEyQXxicrZc0F8vMwKDe1Qn4kMYSg09Kk/c7lk37qjls7/ehOFcUuNX89z7b4PItumRzTyaMhoRKP6WKc9opFHQvJ3P4r4mBzRkM9yJZ/0/ZSh0OCIBiGvZU0hvDza9lRNoNDIILkgPlE5ey6Ij5dJobGUZ0HOiZSfZtVIRP+0RJFByJ48qzE/RcSYUJBcEJ+onD0XxMfL7kLj2RdA96b1VyctUKEhox5X+U7JN//qhJC9maoxP0nEmFCQXBCfqJw9F8THy+5CgxBCtiBijYkYEwqSC+ITlbPngvh4odAghByCiDUmYkwoSC6IT1TOngvi44VCgxByCCLWGCQmuzJnFENyQXyicvZcEB8vFBqEkEMQscYgMdkOPoohuSA+UTl7LoiPFwoNQsghiFhjkJhsBx/FkFwQn6icPRfExwuFBiHkEESsMUhMtoOPYkguiE9Uzp4L4uNlc6HRmrDLRWPdki3/NLY1l9bsWionQGdV3XiNObIB9WRwyrVbGqA1N43dJv7l2uZFEdE/5U5UbVTvm5q6vXoXLWzG2MhbWFMI6+PWU5Cn332hNkFish18FENyQXyicvZcEB8vLqEhjVJm1ntGLTRKwbmn38VXpxavZ/ksM3s+tmsRSysr5u2tdVJUGMgsnGk/nb3zOxfhS/ez7C+/y+yjMiOgHrPOJW/rhIY5r/qeBdtJkZ9F2kZLaNetMM2oO5iyf7y/UF/blnjxITNoltk0lbqFSLz9LL1VG0sTAH9eerHfEiGD+6/x0CHghXAYb72oGv5+ZJCYbAcfxZBcEJ+onD0XxMeLS2gIcw2yFxrSkff7lkXJ8q95Ku9+WvNHwen37dYW0Wm8VVzUnX8tNLK4yCuqpKmFB09bdrrw4YiGnNNOcW7PKwzXS3lfJM9x6Sc/zUhomA5Y+uvhVPotsZin8xfyk3xrHy/duao46naV4+0WRKzatk79nWtBLU0UG2O73cGF0Mab6pC8D0UM9UvILwSJyXbwUQzJBfGJytlzQXy8zAoN7WznllPuhUY3opALYB7RyNvLKqhCehpLv2vhy42+f+p5bJfCpecdCY3uqSidRYRLJ1QUKxbkuHUuVmjY89a+78wZcjwqI6HxXT+b55/rjn4sIvJ6PDVlMUAEPdhwhEDReKXjlvbZx9O1zdTuRnVkHKPQ2oYXwna8eR2jTmBMjKLMgcRkO/gohuSC+ETl7LkgPl5mhYaOKnzOFCgrNHLRqYRG96TSD61qB/coQrkwVaulyvnuVeGSY+h+MiIi26zQqHzlJSsW0jGrXOT4OQZdtG183vfvhMtn4uNOivw0LaFhv6Oh109/rhlc26r94JRuuj6vUuK95/bZn7PcW/b87RjHeQtrCuHouNWDyei1BSAx2Q4+iiG5ID5ROXsuiI+XWaHhZc8gCSEkYo1BYrIdfBRDckF8onL2XBAfLxQahJBDELHGIDHZDj6KIbkgPlE5ey6IjxcKDULIIYhYY5CYbAcfxZBcEJ+onD0XxMcLhQYh5BBErDFITLaDj2JILohPVM6eC+LjhUKDEHIIItaYiDGhSC5WfMwZ4oPYK3i3a7kUxMcLhQYh5BBErDERY0JBRAPig9greLdruRTExwuFBiHkEESsMRFjQkFEA+KD2Ct4t2u5FMTHC4UGIeQQRKwxEWNCQUQD4oPYK3i3a7kUxMfLrNBoTRrUQoPsZwYFJ8Ahr0XWc7nLRElrFtsimzKYKE6myx6tDXLv1uuRKf7HE63ZbXqNdWI68Rsd0kE/SVg9o6YhzeD7ONHt89qc3bPeVqYmz//rukRTsa0phJfP2/B8d532fOJkTtbEFA1ENCA+iL2Cd7uWS0F8vLiEhp3dr4UVGkJqwt1iZTrdd5mFbzgjZxYm96drHZD9sDM2kp8iCwilngVXGQiRboZLbUf1AoKW/ij39rTfXuRekfOkNYPMcepYB7N9PurCVGz1tORSb6ZigwthJYokulporBXYcEwBQUQD4oPYK3i3a7kUxMeLS2gkzFoilpbQ0Gm+i7jIv3+m6jRcY0SFRv513VMGWcaciCSvZtjT1iuhig1HPD5HbbPu4AfbKqx48SJToNckkdCdyy7ylpeAH563rgmZoehJo2sTscGF0AiNsnk8jftS4JgCgogGxAexV/Bu13IpiI+XHYWGjliMO7FcrCg0IvD+67kckbbQUOoRAO3oa2yba11ju4+P8UiIXaStHhmTn+15rL99fWqbgBfC8v7Vp/+pRdWigogGxAexV/Bu13IpiI8Xl9DIir/d+JVeaHRPB/0TwmChpLKIVxEi9VMahcZr4aJqMXkuNNI2bTfdS3Wb69teolzjejRhfMR5BvdK9ZHIkLqNy6+6aGIZlVH0Y9I67mexrSmEg5iEH1xULSqIaEB8EHsF73Ytl4L4eJkVGl7QINOX2uQLb+zoCCFPQGvMnkSMCQURDYgPYq/g3a7lUhAfLz8uNAghxEPEGhMxJhRENCA+iL2Cd7uWS0F8vFBoEEIOQcQaEzEmFEQ0ID6IvYJ3u5ZLQXy8JKEhJ6DRaDQajUbb2jiiQQg5BBFrTMSYUJBcEB8EO8Kxh0kudtucRQW5LoiPFwoNQsghiFhjIsaEguSC+CDYDn4Po9D4sps2g0KDEHIIItaYiDGhILkgPgi2g9/DKDS+7KbN2FxolL+r17+GNzP0PEXn0Sg/j/9On2zNcNroj0VXjOxHa/4MoZ59cw65nnkm3szaNYjKBF31cgJDWtumWBLfmkL4eb18X65dLUnLIpQ/p19TY9bEFA0kF8QHwXbwexiFxpfdtBm7Cw07c+BzxkKD7Ey1aJdcK51EjfwwzcXUMl6hYRctsz8j9P5PZtK8Xp/PIqwsjW9NIeSiavMguSA+CLaD38MoNL7sps2YFxqTMwAOmRIayfdRMLU4pvUQuiehtGkwc2g9bXkZ0Sizk5ZCIeYtuGSa9B53HZo+TS4Th2QP6utiSfe9aTfPFiMsHezl6YjBHJ/X3BaFqUXVVIB00nUQl7Zjizc+uBByUTUXSC6ID4Lt4PcwCo0vu2kzZoWGd8bOKaGhnVYqIF2D1wIpxx4ePw/H6s+10MjkY/bro1BobAKFRkzqabtrzaH3vRXoA3Hft6NufZKu7T3ryD2Utpixi6rpuip5zZPSPiUG9UXjgwshF1VzgeSC+CDYDn4Po9D4sps2Y1ZoaMN/VgCEXmiocOjWEug7rcfvWoTsCo+JVAzq72VMCw0tuhQa26Admr7PrUW4yOuxIxraGeqoYPo5/T+1RtB9tIjZXDueQ+8RPY4VHhpzHqW49xHJ/3bfpfHhhbD9/tQC59lHQc/AY4oHkgvig2A7+D2MQuPLbtqMWaEhSIGb69LrIGX/8gWvez/K0RfO9GWsUlDkZ/kMtS8ISaRMCw1ZSlq+2EWhsQ38MmhMrNBIbalvN93PVVuxHal+RFm3tWcduYdaLIzvlVv1u4iMR1zS1i/5ocMKjaXxrSmEgy+Dfg/FdKo/1WtLWBNTNJBcEB8E28HvYRQaX3bTZriEhoc9g7TY4kQIici2X+h+ZY3xEjEmFCQXxAfBdvB7GIXGl920GYcUGoSQ8xGxxkSMCQXJBfFBsB38Hkah8WU3bQaFBiHkEESsMRFjQkFyQXwQbAe/h1FofNlNm0GhQQg5BBFrTMSYUJBcEJ+oILlY4bGXLQXJBfHxQqFBCDkEEWtMxJhQkFwQn6gguVhBsJctBckF8fFCoUEIOQQRa0zEmFCQXBCfqCC5WEGwly0FyQXx8UKhQQg5BBFrTMSYUJBcEJ+oILlYQbCXLQXJBfHx4hYaz/6+XdAg9U9P5//8dMs/fCNrGM/XQKJwu176eShqlszeer1Ux5A1VGbbJsqC+6gRx9xtuKYQclG1eZBcEJ+oILlYQbCXLQXJBfHxsrnQEGwBabGkUJL9SJMmzVV48lKKsNB5KMbzUcgU374J68q1lZ/66eZdvm1awifjv4/K9Or5WHIfzt2GeCG0U7R3E4jddQZTHDymeCC5ID5RQXKxgmAvWwqSC+LjZVZolLULnjfIttCQ2Qu79QQeVUTFijxBUGjEgUIjGp0I6GbQbbU96ST79qT/P66jzL4pImIkI6optlvHW8bo6B1dR64zAXez+sreU+fMgif7zd2GcCE0a50MFnqbSsUJHFNAkFwQn6gguVhBsJctBckF8fEyKzRUKMytf9ESGiImykcp1QJGj4pCoREHCo1oFKGhSIfYi47Byq3l+kkb045d90ncu4XLKvSpHqM7WH2OvCH9a4WGUD+w6O02qAlVPlPAhXBiUbUk1B6vJakD1iM4poAguSA+UUFysYJgL1sKkgvi42VWaNQrLj6jJTQGIxofpSjJzxQacaDQiEZRBbIGkO0E67Yol64WHL3QqKhFRm6P95XX3JwhrWfyWS33Lv/nNY6s0FBaq0LPhbSmEF4eBx9+TKI55PVZ7HvsZU1M0UByQXyiguRiBcFethQkF8THy6zQ8LJnkISQadZ8mfFIRKwxEWNCQXJBfKKC5GIFwV62FCQXxMcLhQYhB4dC4+eIGBMKkgviExUkFysI9rKlILkgPl4oNAghhyBijYkYEwqSC+ITFSQXKwj2sqUguSA+Xig0CCGHIGKNiRgTCpIL4hMVJBcrCPaypSC5ID5ePn75j3+12yD2DJIQ8hq2qgd7EDG2d6p7SC6IT1TOngvi44VCgxDSs1U92IOIsb1T3UNyQXyicvZcEB8vFBqEkJ6t6sEeRIztneoekgviE5Wz54L4eKHQIIT0bFUP9iBibO9U95BcEJ+onD0XxMcLhQYhpGererAHa2KrZx6tpyBPv89MFPaMd6p7SC6IT1TOngvi44VCgxDSs1U92AM8tqIk8rorZVG1ucUi53inuofkgvhE5ey5ID5eKDQIIT1b1YM9gGMza8bkJeplynFdI+ajLCG/kHeqe0guiE9Uzp4L4uOFQoMQ0rNVPdgDPLbhiIaSZlRVEVKJkSW8U91DckF8onL2XBAfLxQahJCererBHqyJjYuqzYPkgvhE5ey5ID5eKDQIIT1b1YM9iBjbO9U9JBfEJypnzwXx8UKhQQjp2aoe7EHE2N6p7iG5ID5ROXsuiI8XCg1CSM9W9WAPIsb2TnUPyQXxicrZc0F8vFBoEEJ6tqoHexAxtneqe0guiE9Uzp4L4uOFq7cSQg4Bhca+ILkgPlF5VS52ZdY9DMkF8fFCoUEIOQQRa0zEmFCQXBCfqLwqFysK9jAkF8THC4UGIeQQRKwxEWNCQXJBfKLyqlysKNjDkFwQHy8UGoSQQxCxxkSMCQXJBfGJyqtysaJgD0NyQXy8PBcat7wmgFIvRGSpg2zul2beq+fl247PS+N8hjzl8L0RwXDbJc1RTMjPIgt/tbheh21yjuvtcX8/2rHe1c226aSOaWohMlk7ZEkTyu2ym6XzW8rEZTLGNYXw8lkm7ErHv9+6+UInEnGyJqZoILkgPlF5VS5WFOxhSC6Ijxe30JAi86xDbwuNeyogMivf/faZtksNkuNcxW5p4YHGtlyw7rYI3PMxlPbxFBUQ+f/s9/hZ1jm4dIsqpXzy61KMZb0DERr2eJKD3daMj5BNkNkqW721bB3e1/X9m9raRC+vm+/gVNs2pqk7X2JQ0WD/f9ZmasExtdAZXgi5qJoHJBfEJyqvysWKgj0MyQXx8eIWGgIkNLpGnX+VxYyu/XHyE1IRGv02PW99/nsponKMukAMj6dYoZFHNLTgljjy63psFRqCHk+FRr+tFR8hmzIWDHoPfqThhOH9rSMMLaHR38fSFmGhIeixH3Lh3pq2u4ulajf6f18Tmm0mjy7oiMNU5w8XQi6q5gLJBfGJyqtysaJgD0NyQXy87C80+mKTj+URGjJ8mqiL4iOWIhJkeLUUOSsMMm2hoaVSfq+Fhh7bIzSa8RGyKWPBIO1Kzd7f9f1bU7eJ4m8FgpdxTPX4hAiFEp8VGlNt5la16+Lf0EsrCiEXVfOA5IL4ROVVuVhRsIchuSA+Xl4nNKoiNyc0+v3N59GDIiRDxWmf28h3uH/+fFqLszwt6TFqoaHH9giN/tgLPy8nxM+wp5VOvO8uu07R3t96/xbkyd103GCHminH1uPW1KOX0i51n1QD+vbabtO1+Nl8ROO7EW9V20avLWBNTNFAckF8ovKqXKwo2MOQXBAfL8+FxgI2DfJRDGvxEY7o8ZHTId+Dko8EWiMBEcjfz1jXZjatMRsRMSYUJBfEJyqvysWKgj0MyQXx8RJTaBBCiCFijYkYEwqSC+ITlVflYkXBHobkgvh4odAghByCiDUmYkwoSC6IT1RelYsVBXsYkgvi4yUJDTkBjUaj0Wg02tbGEQ1CyCGIWGMixoSC5IL4RCVyLnbEYs4kF7ttzhAfLxQahJBDELHGRIwJBckF8YlK5FxsBz9niGhAfLxQaBBCDkHEGhMxJhQkF8QnKpFzsR38nCGiAfHxQqFBCDkEEWtMxJhQkFwQn6hEzsV28HOGiAbEx8uk0NDpgGueTWqjF2kw5Xg1YVe/pZtVs56gR7aVv//vJtAyfl7szIhCfSx8VsT3RBebGiyS1U3qJHMe3O8yPcO1nyxK/6/vBTlGmgxN3vuHb+MSEC8yPXZ3MaYmrpL3eMl9PFhMrONZW57D+kr7HdwDDpCY1nQEXFRtHiQXxCcqkXOxHfycIaIB8fHiFhqf1zI7ZotnQkMLps7KqbMGKjoz32CmzlocXLtZBbtpxOU4Uh7qGf3051zozPTj1cyeef9OAOlshSnme5r1c67YvRXVLJGDWR27Tkw7vJqW0LCicLKDJLOk+7V73/PU3eP3Mk1+1Ql2va/r+7u0gyGlo73A16hVB9KKq/U9kIRQaa/arhohLYoJ7giq+1zrhgoNe+8uBY4pIEguiE9UIudiO/g5Q0QD4uPFLTQEW2BqngkNbehp8sInIxrTQqPr3tK0wZ2IqKYQTr5dEWsKjarIafHLRbyLoT7uyiecQzElNPSJunvTihhrCw0hr2ybf27dO8SPFXjy3quAEPS6yF610OjX4On2qX1k79w08jWf69SfYUWNoveAbs+vFXUh7W1NTHBHYIRG2ay1CH/AgGMKCJIL4hOVyLnYDn7OENGA+Hh5jdD4FpGR/4eEhnZyKaZOEJjiUa++WosGPVZZo6QIDS1sg+OeSWhUOdedm773dfGdFBoDsTJ8yiYYI6E3eOqurpNdoLAS38MRjbJqsTLXqT/DXt/6WOORibIwvK0NS2PCO4J2265FTn0fLwGPKR5ILohPVCLnYjv4OUNEA+Lj5WVCo3RaeVt6Aqv3+3jy0Uk3hCxLU5eikZ+gLrqfDNeKeFDB0e1fH0vqdz7vMK7hcc8kNGQo/DJaIrtenO7yeL8+LkUUjoTGdz5GS5QQDBUa91u+72vqa1OPLGh7lftermctNPqPLOvrOtOpP6NVB8b3wKM9p4b1aFepbQ7vCSSmNR2Bvc/tqra2DXhZE1M0kFwQn6hEzsV28HOGiAbEx8uk0FjKs4skhanxcb+b4RMdiUxLoJJXYT8uiUB5MFjLsxrzU0SMCQXJBfGJSuRcbAc/Z4hoQHy8vERoEELIWiLWmIgxoSC5ID5RiZyL7eDnDBENiI8XCg1CyCGIWGMixoSC5IL4RCVyLraDnzNENCA+XrioGo1Go9FotN2MIxqEkEMQscZEjAkFyQXxicrZc0F8vFBoEEIOQcQaEzEmFCQXxCcqZ88F8fFCoUEIOQQRa0zEmFCQXBCfqJw9F8THy1OhYf++vJ550FKCzH9i1/qTttbf31ue/Snr7bp8foZnx5tnPKmQZe716Nj5BfrtXV55Ho3yvstfKeufUOqfUeY5FPK9ceEcGruy9E9XrxeZHry6JuDEVJapP6N9ViOayNou5jhT82msKYSD+9ysFbOmRqyJKRpILohPVM6eC+LjZVJolPkQ8t/By+RBMkHWFBqkNtqWqGhtszxr9EsWklKeHW+O4WJvbeZej017ZtDWglf1tNf2NX0L8nt9H02hTZZjJ7hSbvcl7211Tbv/r594e6hjmrrvZbK21jorU/TrunQCNU04trnQGE7Gp+eSMNfO+4LHFA8kF8QnKmfPBfHxMik0dGSi5plQ0CBln1KQ5Bj5Z50uWRu2HisXlXyu22d5upFiNdynExqPpxEpGnUs9QyJqdPsphnXdReEuvilc931tXuawVCEVDlGXoVyODV6F4c5/4KaGo+ptU46cdbqMFpCQ37Os0Bm6lkXCcr4vdfRgtw3a+fZzaT7uOflHm5dM73O6bqsGtHQY09PDCan79urzr57yUsA1K9Zctz57praBy6EZrmCevHE1tu1BDimgCC5ID5ROXsuiI+XJ0Kjo19O2Sc0lLK2SJ7CWoVGEQ318Hs1Jbj+f82ioy5oOqKRhoOrYlQvjmZHIerj9dvK6l9pfz2H+NX767FsHPX51xaqH2VKaOhTZv2eTa11UjFck4aso7uxuhWGBdtmaqGh1yV12JWPtF+9R4v/8pHBzPhmr9uHnrePt2rT5f7SUYUyW7DGU+fXale2xriZWFStfnC4Lf3IpwOOKSBILohPVM6eC+LjZVJoiCiQBihPSUuEhhYZbcSp2KTPYasFoG7lWPnjmLbQGO7TFaRu4SjPiIYVDorsJ7lpwb6mRVGGy0bXQmMQhzl/qyAeicsjTxEG9acd+h5Ijumt6a6fMBYaMvqjnUfehyMaW2BurMd9p9eojGzkUb98L+fRPjuiMbo/NxnRuKURrNt12DmXeyK3cW1fz0Y0WqLH7qOsKYR6nxdKLhQaGSQXxCcqZ88F8fEyKTSE9Hlp/bmsQ2jol7t0KF2/hJW2DQRB/l8XXmoJjeE+RfykpyFTQWWbjt7nxai6p6SW0JDC13WigvysH/cM9y8fH9Vx1Oevi+sRaX0ZlIuqRWB4f8s1KVvyiqjSPnXhwPtDiNjF1JLQ/zAjBJsIjdxm7H2jbSf9/LgHJCZpV7pd4hXRWqPx1YJjD6Fh73MuqjYGyQXxicrZc0F8vDwVGkvYM8itqQsi2RZ+bPIzaIcdFXlIWBtjxBoTMSYUJBfEJypnzwXx8XJKoUEIOR4Ra0zEmFCQXBCfqJw9F8THC4UGIeQQRKwxEWNCQXJBfKJy9lwQHy8UGoSQQxCxxkSMCQXJBfGJytlzQXy8UGgQQg5BxBoTMSYUJBfEJypnzwXx8UKhQQg5BBFrTMSYUJBcEJ+onD0XxMcLhQYh5BBErDERY0JBckF8onL2XBAfLxQahJBDELHGRIwJBckF8YnK2XNBfLxQaBBCDkHEGhMxJhQkF8QnKmfPBfHxQqFBCDkEEWtMxJhQkFwQn6icPRfExwuFBiHkEESsMRFjQkFyQXyicvZcEB8vFBqEkEMQscZEjAkFyQXxicrZc0F8vFBoEEIOQcQaEzEmFCQXxCcqZ88F8fFCoUEIOQQRa0zEmFCQXBCfqJw9F8THy/8HDo64vz8TYXgAAAAASUVORK5CYII=>

[image3]: <data:image/png;base64,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>
