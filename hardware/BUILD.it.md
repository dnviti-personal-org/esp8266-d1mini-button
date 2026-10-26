# Guida di montaggio — millefori (rev C)

Tutto quello che c'è in questa guida deriva da `layout/layout.json`
(generato da `layout/gen_layout.py`); i disegni in `schematic/` e il modello 3D
in `enclosure/` usano gli stessi nomi dei fori, quindi basta seguire le
tabelle. **Nomi dei fori**: tieni la millefori con il **lato componenti in
alto** e il bordo che ospiterà le prese USB **verso di te**; le colonne vanno
**da A a X da sinistra a destra**, le righe **da 1 a 18 dal vicino al
lontano**. Segna A1 con un pennarello prima di iniziare. Quando giri la
scheda per saldare, destra e sinistra si scambiano: il disegno
`perfboard-solder-side.svg` è già specchiato per te.

Si saldano solo componenti a foro passante; i tre moduli (D1 mini, caricatore
TP4056, microfono INMP441) arrivano già montati.

## Attrezzi e materiali

- Saldatore (≤ 350 °C), stagno 0.5–0.8 mm, flussante, tronchesine.
- Filo nudo stagnato 0.6 mm per i ponticelli corti; filo isolato flessibile
  26 AWG nei colori della tabella (vanno bene altri colori, ma un colore per
  ogni net: scrivi le sostituzioni nella tabella).
- Biadesivo in schiuma da 1 mm (per il modulo caricatore), nastro kapton o PVC.
- Punta da 2.2 mm (4 fori di fissaggio), limetta o tronchesine per gli angoli.
- Multimetro.

## 1. Preparare la scheda

1. Taglia i quattro angoli della millefori a **5 × 5 mm** (liberano le colonnette delle viti del coperchio).
2. Allarga a Ø2.2 mm i quattro **fori di fissaggio** sui fori di griglia **L1, L18, C17, X11**.
   Sugli 8 fori attorno a ciascuno non va saldato nulla (sotto c'è il
   distanziale Ø5 mm).
3. Con il bordo USB verso di te, segna **A1** (vicino a sinistra) e **X18** (lontano a destra).

## 2. Saldare i componenti (lato componenti), prima i più bassi

| Passo | Sigla | Componente | Reofori nei fori | Note |
|---|---|---|---|---|
| 1 | D2 | 1N5819 Schottky, DO-41 | A → **O3**, K → **K3** | band (cathode) toward column K, next to U1's 5V pin |
| 2 | R2 | 10 kΩ 1/4 W | 1 → **K5**, 2 → **O5** | BTN pull-up |
| 3 | R3 | 10 kΩ 1/4 W | 1 → **K7**, 2 → **O7** | CHRG pull-up |
| 4 | C3 | 100 nF ceramic disc, 2.54 mm | 1 → **Q11**, 2 → **Q12** | any orientation |
| 5 | C4 | 100 µF 10 V electrolytic Ø5x11 | - → **Q14**, + → **Q15** | leads bent 90°, body lying flat toward column X; stripe (−) toward row 14 |
| 6 | J2 | 1x6 right-angle male header | SCK → **Q17**, WS → **R17**, SD → **S17**, VDD → **T17**, L/R → **U17**, GND → **V17** | bent pins point toward row 18 (board edge), plastic body on rows 17 |
| 7 | J1 | JST-PH 2-pin right-angle (S2B-PH-K-S) | 1 (+) → **X14**, 2 (−) → **X15** | opening toward the board edge (column X side); 2.0 mm pins spread to 2.54 mm |
| 8 | SW1 | tactile 12x12, 7.3 mm actuator (B3F-4000) | 1a → **K9**, 1b → **P9**, 2a → **K11**, 2b → **P11** | pins 12.5 mm apart go into holes 12.7 mm apart: spread them 0.1 mm each; pins on the same row are joined inside the switch |

## 3. Ponticelli nudi e ponte di stagno (lato saldature)

| # | Net |  |  | mm |
|---|---|---|---|---|
| 1 | 5V | K3 | J3 | 2.5 |
| 2 | RST | A10 | A11 | 2.5 |
| 11 | GND | U17 | V17 | 2.5 |

## 4. Fili isolati (lato saldature)

Taglia ogni filo alla lunghezza **Taglio** (= distanza in linea retta + 8 mm),
spela 3 mm alle due estremità, stagna, poi salda ogni capo nel suo foro
**insieme al reoforo già presente** (o da solo dove il foro è vuoto). I fili
stanno distesi sul lato saldature; possono incrociarsi e passare sopra altre
saldature, sono isolati. Falli in quest'ordine.

| # | Net | Colore | Da | A | Lunghezza | Taglio |
|---|---|---|---|---|---|---|
| 3 | BTN | white | K5 | K9 | 10.2 mm | 18 mm |
| 4 | BTN | white | J8 | K9 | 3.6 mm | 12 mm |
| 5 | BTN | white | Q11 | P9 | 5.7 mm | 14 mm |
| 6 | BTN | white | A11 | P9 | 38.4 mm | 46 mm |
| 7 | GND | black | J4 | K11 | 18.0 mm | 26 mm |
| 8 | GND | black | P11 | Q12 | 3.6 mm | 12 mm |
| 9 | GND | black | Q12 | Q14 | 5.1 mm | 13 mm |
| 10 | GND | black | Q14 | V17 | 14.8 mm | 23 mm |
| 12 | GND | black | M1:OUT- | P11 | 21.0 mm | 29 mm |
| 13 | 3V3 | red | A3 | O5 | 35.9 mm | 44 mm |
| 14 | 3V3 | red | O5 | O7 | 5.1 mm | 13 mm |
| 15 | 3V3 | red | O7 | Q15 | 20.9 mm | 29 mm |
| 16 | CHRG | violet | A8 | K7 | 25.5 mm | 34 mm |
| 17 | CHRG | violet | K7 | M1:CHRG | 22.7 mm | 31 mm |
| 18 | VSW | yellow | O3 | A15 | 46.8 mm | 55 mm |
| 19 | VSW | yellow | M1:OUT+ | A16 | 47.4 mm | 55 mm |
| 20 | VBAT | brown | M1:B+ | X14 | 19.6 mm | 28 mm |
| 21 | BAT- | grey | M1:B- | X15 | 15.3 mm | 23 mm |
| 22 | MICPWR | green | J7 | T17 | 35.9 mm | 44 mm |
| 23 | I2S_SCK | blue | A5 | Q17 | 50.8 mm | 59 mm |
| 24 | I2S_WS | pink | A7 | R17 | 50.1 mm | 58 mm |
| 25 | I2S_SD | turquoise | A6 | S17 | 53.6 mm | 62 mm |

## 5. Modulo caricatore M1

1. Incolla il biadesivo da 1 mm sulla millefori sopra le colonne **R..X,
   righe 1..9** (x 46.3–63.8 mm, y −0.5–25.5 mm dall'angolo A1: il modulo
   sporge di 0.5 mm dal bordo USB così la USB-C arriva alla parete).
2. Premi sopra il modulo TP4056, **USB-C verso il bordo USB**, centrato a
   **x = 55.0 mm** (= 1.1 mm a destra della colonna T).
3. Salda ai suoi pad i cinque fili della tabella 4 che iniziano con `M1:`:
   `B+`, `B−` (pad batteria, estremità lontana), `OUT+`, `OUT−` (pad carico)
   e `CHRG` = il pad del LED di carica che va al pin 7 del TP4056 (il pad del
   LED **non** collegato al lato 5 V/resistenza; verifica col multimetro in
   modalità diodo: il pin 7 è il secondo pin dalla USB-C sul lato del chip
   rivolto verso i LED). Lascia liberi `IN+`/`IN−`.

## 6. Interruttore SW2

Piega i tre pin dell'SS12D00 a 90° a 1 mm dal corpo, così l'interruttore
sta sdraiato su un fianco con la **levetta verso il bordo della scheda**
(bordo sinistro, lato colonna A) e i pin scendono in **A15, A16, A17** (pin
centrale = A16, il comune). Salda; il corpo appoggia sulla scheda e la
levetta uscirà dalla feritoia nella parete della custodia.

## 7. D1 mini U1

1. Infila le due strip maschio da 8 pin nella millefori in **A3..A10** e
   **J3..J10** con i **pin LUNGHI verso il basso** attraverso la millefori e i
   corti verso l'alto; il distanziale di plastica appoggia sulla millefori.
2. Calza il D1 mini sui pin corti: **micro-USB verso il bordo USB**, 3V3 in A3
   e 5V in J3 (RST in A10, TX in J10). Salda i 16 pin sopra il D1 mini.
3. Gira la scheda, salda i 16 pin sul lato saldature (insieme ai fili della
   tabella 4 che arrivano in A3..A10 / J3..J10) e **taglia i pin lunghi a
   filo**: più di 1 mm toccherebbero la batteria sotto.

## 8. Verifiche prima di alimentare

Col multimetro (senza batteria né USB):
- `GND` (J4) – `3V3` (A3): > 10 kΩ, nessun corto. `GND` – `5V` (J3): nessun corto.
- `BTN` (K9) – `3V3`: ≈ 10 kΩ (R2). Premendo SW1: `BTN` – `GND` ≈ 0 Ω.
- `RST` (A10) – `BTN` (K9): 0 Ω se JP1 è ponticellato.
- `CHRG` (K7) – `3V3`: ≈ 10 kΩ (R3).
- J1 pin 1 (X14) – M1 `B+`: 0 Ω; J1 pin 2 (X15) – M1 `B−`: 0 Ω.
- SW2 ON: M1 `OUT+` – anodo D2 (O3): 0 Ω; SW2 OFF: aperto.
Poi collega la batteria a J1 (rosso = +, verso la riga 14), accendi SW2: il
LED del D1 mini lampeggia all'avvio; apri la console seriale (vedi README) e
configura il Wi-Fi. Collega la USB-C a M1 solo per caricare (LED rosso =
in carica, blu = carica completa).

## 9. Cavetto del microfono

Prepara un cavetto a 6 fili da 90 mm con un connettore femmina DuPont 1×6
sul lato J2: J2 **SCK → M2 SCK**, **WS → WS**, **SD → SD**, **VDD → VDD**,
**L/R → L/R**, **GND → GND**. Salda le altre estremità ai pad del modulo
INMP441; va nella tasca del coperchio, foro acustico sopra il foro Ø2 mm,
lato componenti verso il coperchio. `L/R` è a GND (canale sinistro) tramite
il ponticello nudo U17–V17.
