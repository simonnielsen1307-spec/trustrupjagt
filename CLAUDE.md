# Hunting Trustrup – app

Jagt-app (PWA) for Hunting Trustrup. Database: `https://trustrup-jagt-default-rtdb.europe-west1.firebasedatabase.app/trustrup` (Firebase-projekt `trustrup-jagt`). Lokal lagring: `tj_`. Logo: skjold med "HT". Kort/vejr centreret på 56,3466 / 10,7802.

## Søster-app

Dystrup og Trustrup er **samme kode** med forskellige navne, logo, database og medlemmer.
En rettelse eller funktion i den ene skal næsten altid også i den anden.
De to grupper må **aldrig** kunne se hinandens data: separate repos, separate adresser, separate databaser.

- Dystrup: repo `simonnielsen1307-spec/dystrupjagt` → https://simonnielsen1307-spec.github.io/dystrupjagt/
- Trustrup: repo `simonnielsen1307-spec/trustrupjagt` → https://simonnielsen1307-spec.github.io/trustrupjagt/

## Opbygning

- Én fil: `index.html` (HTML + CSS + JS, intet byggetrin). `manifest.json`, `sw.js`, `icon-*.png`.
- Hostes på GitHub Pages fra `main` / root. Push til `main` = udgivet (1–2 min, telefoner kan cache op til 10 min).
- Data: Firebase Realtime Database via REST (`fetch(FB+'/sti.json')`), ingen Firebase-SDK. `fbWrite(sti, værdi)` laver PUT/DELETE og viser fejl-toast hvis det mislykkes.
- Polling: chat hvert 6. s, tårne hvert 20. s, jagter/vildt/positioner hvert 30. s (`startPolling`).
- Vejr/vind: open-meteo (`fetchWind`, cache 20 min). Vindvurdering i `windRating`: duften driver mod `fra+180°`; ≤45° fra skudretningen = rød, ≤100° = gul, ellers grøn.
- Jagttider: tabel `JT` i koden (BEK 470/2024, generelle + lokale for Djursland/Region Midtjylland: hare 1/11–15/1, agerhøne 16/9–15/10, kronhjort 1/10–30/11). Opdatér når der kommer ny jagttidsbekendtgørelse (revision 2026 er i gang).
- Offline-kort: `saveOfflineMap` henter kortfelter for arealer+tårne (zoom 11–17) i cachen `tiles-v1`; `sw.js` svarer kort/unpkg/fonte fra cache først og må aldrig slette `tiles-*` ved opdatering.
- Kort: Leaflet 1.9.4 fra unpkg. Korttyper i `BASES` (vej, satellit, hybrid, topo, terræn, lyst, mørkt).
- Login: navn + kode, SHA-256 af `kode + 'dystrup-jagt-salt-2024'` (samme salt i begge apps). Medlemmer i `DB.members`; `DEFAULT_MEMBERS` bruges kun når databasen ingen medlemmer har.
- Lokal lagring har præfiks pr. app (`dj_` / `tj_`), så begge apps kan køre på samme telefon. Cachen er bundet til database-adressen (`c.fb===FB`).
- Design "C – Nat & signal": mørk `#111311`, accent orange `#ff7a1a`, skrift Barlow / Barlow Condensed. Farver som CSS-variabler i `:root` (`--gold` er accenten, navnet er historisk).
- Rettigheder: kun admin kan oprette, placere og trække tårne, sætte skudretning og tegne arealer. `body.is-admin` sættes ved login; brug klassen `admin-only` på knapper.
- Layout følger skærmen: `--sat`/`--sab` = iPhone safe-area top/bund, `--navh` = menuhøjde. Kortet ligger under header, aldrig over.

## Databasestier

`members`, `stands` (tårne), `nextStandId`, `kills` (nedlagt vildt), `hunts` (jagter, `createdBy`, `signups` (kommer), `declines` (kan ikke), `extra/<navn>` = {guests:[{name}], dogs:[{name,type}], note}), `chat`, `vagtplan`, `kvoter`, `extraAreas` (tegnede arealer), `positions` (delt GPS mens man er tjekket ind), `activity`, `adminMsg`, `feeders` (foderpladser/vildtkameraer: interval i dage, `last`, `log`), `alerts` (nødalarmer, `active`). Tårne har `dir` (skudretning i grader, 0 = nord).
**Ikke i databasen:** "Mine andre jagter" (private jagter) ligger kun i telefonens localStorage under `pj_<brugernavn>` – uden app-præfiks, fordi begge apps ligger på samme domæne; så ser brugeren sine private jagter i begge apps. Må aldrig sendes til Firebase.
Engangs-flag: `cleanedDefaults` (kun Trustrup), `pwReset2026` (kun Dystrup).

## Fejl vi har lavet – undgå dem igen

1. **Medlemsliste blev slettet** når nogen skiftede kode: `DB.members={...DEFAULT_MEMBERS}` blev kun sat hvis `DB.members` var `undefined`, ikke når den var `{}`. Brug altid `if(!DB.members||!Object.keys(DB.members).length) DB.members=JSON.parse(JSON.stringify(DEFAULT_MEMBERS))` før skrivning af `members`.
2. **Firebase laver objekter med tal-nøgler om til arrays med `null`-huller** (fx `stands`, `kills`). Brug altid `Object.values(x||{}).filter(Boolean)`.
3. **Dobbeltklik ved arealtegning**: der var både `map.on('click',drawNewAreaClick)` og en generel klik-handler → hvert tryk gav 2 punkter. Kun én handler.
4. **Kort lå over headeren** og dækkede knapper; uret/batteriet dækkede toppen. Header skal have `padding-top:var(--sat)`, `#v-kort{position:relative;overflow:hidden}`, nav/toast/modaler skal tage højde for `--sab`.
5. **Gammel cache viste andres data** (Torn 1–10) efter databaseskift. Serverdata skal altid erstatte cachen, også når serveren er tom; cache bindes til `FB`.
6. **Telefoner viste gammel version**: service workeren hentede uden `cache:'no-cache'`. Hæv `CACHE`-versionen i `sw.js` ved større ændringer.
7. **Faste arealer i koden** (Nord-/Sydstykket i pixel-koordinater) passede ikke. Arealer tegnes nu kun i appen og ligger i `extraAreas`. Læg ikke koordinater i koden.
8. **Ikke vise placeringen før `cancelPlace()`** – `placingStand` er `null` bagefter.
9. Stille fejl ved gemning: tjek altid `r.ok` på fetch. En afvisning fra databasen (401/403) = Firebase **Rules** forkerte/udløbet ("test mode" udløber efter 30 dage).
10. Testede ikke på rigtig skærm med iPhone-kanter → knapper kunne ikke trykkes. Kør `test_layout.py` efter enhver layoutændring.
11. **Tårn-felter forsvandt**: flere steder skrev tårne som `{id,name,lat,lng,booking}` og smed andre felter væk (fx `dir`). Tilføj nye felter alle steder der skriver `stands/`.
12. Tests der læser tekst skal bruge `textContent`, ikke `innerText` – overskrifter er versaler via CSS.
13. **Kortlag-panelet kunne ikke rulle** på telefonen (sprang tilbage): `overflow:hidden` stod efter `overflow-y:auto` i samme regel. Paneler over kortet: `overflow-y:auto; overscroll-behavior:contain` og `L.DomEvent.disableScrollPropagation`. Test med rigtige touch-bevægelser (`test_v3.py`).
14. Vinddata kan mangle → tjek `typeof WIND.from==='number'` før brug, ellers går hele forsiden i stykker.
15. **Tilmeldinger forsvandt** når to tilmeldte sig samtidig: hele `signups`-listen blev skrevet fra telefonens gamle kopi. Brug `setResponse(h,'yes'|'no'|null)` (henter nyeste lister først). Gem data pr. bruger i egne stier (`extra/<navn>`) i stedet for at overskrive fælles lister.

## Sådan arbejder vi

- Læs denne fil først. Ret i begge apps når det er fælles kode.
- Kør testene før push: `sh tests/run.sh` (Playwright + falsk Firebase i hukommelsen; rigtig database bruges ikke). Alle skal give `FEJL: ingen`.
- Commit-beskeder på dansk. Bruger (Simon) er ikke-teknisk: forklar kort hvad han skal gøre på telefonen.
- Ting der kun kan gøres af Simon: oprette repos, slå GitHub Pages til, Firebase-konsollen (Rules, nye databaser).
- Koder/hashes skrives aldrig i klartekst i commit-beskeder eller denne fil.

## Historik

- 24-10-2026: Trustrup oprettet som kopi af Dystrup. Egen repo + egen Firebase (`trustrup-jagt`). Rettet fejl 1–8. Nyt design C, 7 korttyper, GPS-tjek-ind med delt position, beskeder (kun når appen er åben), kvoter pr. sæson (1/4–31/3), app-ikoner.
- 24-10-2026: Alt overført til Dystrup med eget logo (råbukhoved). Nord-/Sydstykket fjernet; arealer tegnes på ny. Alle Dystrup-koder nulstillet én gang.
- 25-10-2026: Denne fil + testpakke lagt i begge repos.
- 25-10-2026: "Mine andre jagter" (🔒 Mine under Jagter): private jagter kun på telefonen, advarsel ved overlap med fællesjagter/egne jagter, farver i kalender, spørger ved tilmelding på optaget dag. Test: `test_private.py`.
- 25-10-2026: Vind ved tårne (skudretning + grøn/gul/rød + sektorer på kort), jagttider (forside + egen side + advarsel ved registrering), offline-kort, nødknap (SOS til alle med position, banner, stop), foderpladser & vildtkameraer (kort, påmindelse, log). Test: `test_v2.py`.
- 25-10-2026: Kortlag-panel kan rulle på telefon; skudretning kan sættes direkte når man trykker på tårnet (admin). Test: `test_v3.py`.
- 25-10-2026: Gæster & hunde på fællesjagter (pr. jæger, med note), samlet antal jægere/gæster/hunde på kort og forside, frameld fjerner også gæster/hunde. Test: `test_v4.py`.
- 25-10-2026: Tårne låst (kun admin flytter/opretter). Svar på fællesjagt: Kommer / Kan ikke / Ikke svaret med samlet graf og navne i tre kolonner; næste jagt ligger øverst på forsiden. Test: `test_v5.py`.

## Idéer / ikke lavet endnu

- Synk af private jagter mellem egne enheder (krypteret med brugerens kode).
- Beskeder når appen er helt lukket (kræver Firebase Cloud Functions + web push).
- Strammere Firebase Rules (kræver Firebase Auth i stedet for egen login).
