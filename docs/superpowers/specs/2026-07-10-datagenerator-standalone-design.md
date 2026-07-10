# Datagenerator — standalone HTML-side (design)

**Dato:** 2026-07-10
**Status:** Godkjent av Hans (design-samtale samme dag)
**Erstatter:** Anvil-appen i dette repoet (som beholdes urørt som referanse)

## Mål

En brukervennlig, selvstendig HTML-side som genererer syntetiske tabulære data —
med norske helseregistre som førsteprioritet, men også som generelt verktøy.
Nybegynner skal få koblbare, realistisk utseende registerdata på under et minutt;
avansert bruker skal kunne bygge egne datasett kolonne for kolonne.

## Avklarte valg

- **Bruksområde:** Både generelt og helse; helse-presets er førsteprioritet.
- **Distribusjon:** Én fil (`datagenerator.html`) + CDN-biblioteker.
- **UI-språk:** Norsk som standard, med no/en-språkbryter (som i safestat).
- **Realisme:** Form-realisme pluss enkel samvariasjon (håndlagde regler).
- **Kobling:** Felles populasjon; alle register-filer koblbare på `lopenr`.
- **Brukervennlighet er et hovedkrav** (eksplisitt fra Hans).

## 1. Arkitektur og filer

Én fil: `datagenerator.html` i rot av datagenerator-repoet.

CDN-avhengigheter:

| Bibliotek | Formål |
|---|---|
| Tabulator | Tabellvisning/forhåndsvisning |
| randexp.js | Generere strenger fra regex (erstatter server-side `rstr`) |
| JSZip | «Last ned alle» som én zip |

Seeded RNG (mulberry32) implementeres selv (~5 linjer). Ingen andre avhengigheter.

Tre logiske lag inne i filen, i denne rekkefølgen:

1. **Datalag** — innebygde kodelister (ICD-10-utvalg, ICPC-2-utvalg, ATC-utvalg,
   kommunenummer, ytelser, NUS-nivåer, sivilstand) og preset-definisjoner som
   deklarative JS-objekter.
2. **Generatormotor** — rene funksjoner, ingen DOM-avhengighet, testbare.
3. **UI** — DOM-bygging, hendelseshåndtering, Tabulator, eksport.

## 2. Generatormotoren

All tilfeldighet trekkes fra én seeded RNG → **samme seed gir identisk
datasett** (reproduserbarhet; nytt i forhold til Anvil-appen).

Kolonnetyper:

| Type | Beskrivelse | Eksempel |
|---|---|---|
| oppskrift | Minispråket fra Anvil-appen, med bugfikser | `[A,B][x,y;p=(0.8,0.2)][1-3]` |
| eksempel | Etterlign formen på et eksempel | `K50.1` → stor bokstav, siffer, siffer, punktum, siffer |
| regex | Via randexp.js | `[A-Z]\d{2}\.\d` |
| liste | Trekk fra innebygd eller egen liste, valgfrie vekter | ICD-10-utvalget |
| tall | Uniform eller normal; heltall/desimal; min/maks/avrunding | alder, inntekt |
| dato | Uniform i intervall, valgfritt format | 2015-01-01 – 2024-12-31 |
| sekvens | 1, 2, 3, … | id-er |
| konstant | Samme verdi i alle rader | årstall |

Oppskriftsspråket beholder syntaksen fra Anvil-appen (bakoverkompatibel), men:
range-slutt er inklusiv (`[a-f]` inkluderer f), og parse-feil gir presise
feilmeldinger i stedet for stille feil.

Tverrgående egenskaper per kolonne:

- **tie-to-key**: verdien er stabil per verdi i en nøkkelkolonne
  (f.eks. fødselsår konstant per lopenr). Som i Anvil-appen.
- **% missing**: andel tomme/NA-verdier injiseres (nyttig for undervisning
  i datavask). Ny.

## 3. Populasjon og register-presets

### Populasjon

Fane 1 genererer først én **populasjon**; hvert register trekker personer og
hendelser fra den. Alle filer blir dermed **koblbare på `lopenr`**.

Populasjonens variabler: `lopenr`, `kjonn`, `fodselsaar`, `bostedskommune`,
`dodsdato` (bare et lite, aldersavhengig mindretall har verdi).

### Presets (konvensjonelle variabelnavn)

| Register | Variabler |
|---|---|
| NPR | lopenr, innDato, utDato, hoveddiagnose (ICD-10), bidiagnose1, omsorgsnivaa, institusjonID |
| Legemiddelregisteret | lopenr, utleveringsDato, atcKode, ddd, antallPakninger |
| KUHR (HELFO) | lopenr, dato, diagnoseICPC2, takstkode, refusjonsbelop |
| SSB (demografi/sosioøk.) | lopenr, fodselsaar, kjonn, bostedskommune, sivilstand, utdanningsnivaa (NUS), samletInntekt |
| FD-trygd | lopenr, fomDato, tomDato, ytelse (sykepenger/uføretrygd/dagpenger/AAP), uforegrad |

Kodeverdiene trekkes fra innebygde utvalg av **ekte koder** (~50–150 per
kodeverk) — ikke bare format-gyldige tilfeldige strenger.

### Enkel samvariasjon

Håndlagde regler, deklarert i preset-definisjonene (ikke spredt i koden):

- Alder → innleggelsessannsynlighet og diagnosemiks (NPR).
- Kjønn → utelukker/vekter koder (svangerskapskoder kun kvinner).
- Alder → sannsynlighet for uføretrygd (FD-trygd) og inntektsnivå (SSB).
- Antall hendelser per person ~ aldersavhengig Poisson.
- Datoer respekterer `dodsdato` (ingen hendelser etter død) og `fodselsaar`.

Ambisjonsnivå: reglene skal gjøre data *plausible for undervisning og demo*,
ikke statistisk kalibrert mot ekte registre.

## 4. UI og layout

**Toppbanner:** antall personer + seed (globalt), språkbryter no/en.

**Fane 1 «Ferdige datasett»:**

- Kort per register med avkrysning og 1–2 parametre (f.eks. hendelser per person).
- Én «Generer»-knapp → Tabulator-forhåndsvisning (første 50 rader, én
  underfane per register).
- Eksport: «Last ned CSV» per register, «Last ned alle (zip)», «Kopier til
  utklippstavle». CSV: semikolonseparert, UTF-8.

**Fane 2 «Bygg selv»:**

- Kolonneliste som kort: navn, type (dropdown), typeparametre, live-eksempel
  på 5 verdier som oppdateres mens man skriver.
- Tabulator-forhåndsvisning av hele datasettet.
- Eksport: CSV, JSON, utklippstavle.
- **Lagre/last oppskrift som JSON** (fildownload + localStorage) — erstatter
  Anvil-appens Google-Drive-deling og delte mønsterdatabase.
- Hvert preset i fane 1 har en «Tilpass»-knapp som åpner preset-et her som
  redigerbar kolonneliste (broen mellom fanene).

**Droppes fra Anvil-appen:** Google Drive-lagring, brukerkontoer, delt
mønsterdatabase på server. JSON-eksport/-import dekker behovene uten server.

## 5. Feilhåndtering og verifisering

- Parse-feil i oppskrift/regex vises inline ved kolonnen (rød tekst; kolonnen
  genereres ikke). Aldri alert-bokser.
- Motoren er rene funksjoner samlet i én blokk.
- `datagenerator.html?selftest` kjører innebygd assertion-suite i konsollen:
  oppskriftsspråket (alle syntaksvarianter), fordelinger (grove
  sanity-sjekker), tie-to-key, seed-determinisme, samvariasjon-regler
  (ingen hendelser etter død, svangerskapskoder kun kvinner).
- Manuell verifisering i nettleser før ferdigstilling: begge faner, begge
  språk, alle eksportveier.

## Suksesskriterier

1. Ny bruker kan laste ned koblbare NPR + SSB-filer på under ett minutt.
2. Samme seed → byte-identiske CSV-filer.
3. Anvil-appens oppskrifts-syntaks fungerer uendret i «Bygg selv».
4. Siden fungerer fra `file://` og fra GitHub Pages/Netlify uten endringer.
