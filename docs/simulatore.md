# Il simulatore

Progetto del prototipo v0, scritto il 2026-09-25 e corretto lo stesso giorno con il codice
in mano. I concetti stanno in `matematica.md`, i numeri con le fonti in `riferimenti.md`,
le previsioni e le misure in `MISURE.md`, gli errori in `lessons.md`.

## Cosa fa

Un simulatore **solo matematico**: dato un **caso** (animale, casa, zona, ora della
perdita) e un'ora «adesso», predice dove si trova l'animale, con la più alta accuratezza
possibile. Nessun ingresso esterno dopo la perdita. Produce:

1. la **mappa**: per ogni cella, la probabilità che l'animale sia lì, libero, adesso;
2. la probabilità di ogni **stato**: libero, raccolto da qualcuno, morto (tornato a casa è
   escluso: se fosse tornato chi chiede lo saprebbe) e la probabilità che **torni da solo
   entro 7 giorni**;
3. tre **consigli**: dove cercare adesso (e a che ora), in che raggio, se è ora di
   telefonare a canili e veterinari (e in quale raggio).

Niente interfaccia: una libreria Python con una riga di comando. Il sito arriva dopo e la
chiama.

## Il modello

### Particelle

N = 10.000 animali virtuali (parametro). Ognuna ha: posizione (x, y in metri, piano locale
centrato su casa), stato, direzione corrente, un'**ancora** (il nascondiglio scelto), il
peso. Passo temporale: **1 ora**. Orizzonte: fino a 90 giorni. Notte = dalle 20:00 alle
5:59.

Stati: `LOOSE` (libero), `HELD` (raccolto da una persona), `HOME` (tornato da solo),
`DEAD`. Gli ultimi tre sono assorbenti. Solo `LOOSE` ha una posizione che conta.

### Movimento (ogni ora, solo LOOSE)

Passeggiata casuale correlata con pause e attrazione verso l'ancora:

1. Con probabilità `p_move(categoria, giorno/notte) × stay(cella)` la particella si muove;
   altrimenti sta ferma.
2. Lunghezza del passo: lognormale con mediana `step × mobility(cella)` e dispersione
   `step_sigma`.
3. Direzione: von Mises attorno alla direzione precedente con concentrazione `kappa`.
4. Attrazione verso l'ancora, solo quando si muove: dopo il passo la posizione recupera una
   frazione `pull` della distanza dall'ancora (Ornstein-Uhlenbeck discreto).
5. Assestamento: dopo `t_settle` ore (esponenziale per particella) l'ancora diventa la
   posizione corrente e valgono i parametri «dopo» (passo, `kappa`, `pull`).
6. Ancora iniziale: `random` = a distanza lognormale da casa (mediana `anchor_med`,
   dispersione `anchor_sigma`) in direzione casuale; `home` = casa; `none` = nessuna finché
   non si assesta.

### L'ambiente: la zona

Ogni cella ha quattro moltiplicatori: `people` (sul rischio di essere raccolto), `traffic`
(sul rischio di morte), `stay` (su `p_move`: sotto 1 dove l'animale trova riparo e resta),
`mobility` (sul passo). Nel caso si dichiara la zona di casa, più toppe circolari
facoltative («qui c'è un parco»). Da v0.1 la stessa griglia la riempie OpenStreetMap.

| Zona | people | traffic | stay | mobility |
|---|---|---|---|---|
| `suburban_houses` (villette; **riferimento** della taratura) | 1 | 1 | 1 | 1 |
| `apartment_blocks` (palazzi) | 1,5 | 1,3 | 1 | 0,8 |
| `city_center` (centro città) | 2 | 1,5 | 1,1 | 0,7 |
| `rural` (campagna) | 0,3 | 0,7 | 0,9 | 1,5 |
| `park` (parco, giardini) | 0,8 | 0,2 | 0,6 | 1 |

Piano: un gatto che vive dal 2° piano in su ha l'ancora a 0,6 volte la distanza (si
nasconde nel palazzo o ai suoi piedi). **Tutti i numeri di questa sezione sono stime senza
fonte**; il riferimento è la villetta perché da lì vengono gli studi della taratura (Huang:
Australia e USA; Kremer: Dallas, dove la distanza cambia per quartiere).

### Transizioni di stato (ogni ora, solo LOOSE)

Un solo numero casuale decide fra raccolta, ritorno e morte:

| Transizione | Rischio orario | Fattori |
|---|---|---|
| LOOSE → HELD | `h_pickup` | × `people` × 1,5 se ha il collare × 0,2 di notte × (1 + 0,25 al giorno dopo il 3°, fino a 3) per il cane diffidente |
| LOOSE → HOME | `h_home` | solo dopo `home_from`; × `home_late` dopo `home_until`; × 2 di notte per i gatti; × exp(−(t − 30 g)/30 g) dopo 30 giorni |
| LOOSE → DEAD | `h_dead` | × `traffic` |

Di una particella HELD si tiene **dove** è stata raccolta: serve al raggio dei canili.

### Le categorie e i parametri

Valori tarati in fase A4 per i cani e A5 per i gatti (`sim/calibrated.json`); fra parentesi la stima di partenza quando
è cambiata. I numeri senza parentesi sono ancora stime.

| Parametro | gatto casa | gatto libero | cane socievole | cane diffidente | cane pauroso |
|---|---|---|---|---|---|
| `p_move` giorno / notte | 0,05 / 0,30 | 0,15 / 0,40 | 0,60 / 0,20 | 0,50 / 0,30 | 0,40 / 0,50 |
| passo (m) | **25** (15) | **3** (40) | **25,5** (150) | **595** (250) | **1.190** in fuga, **238** dopo (500 / 100) |
| `step_sigma` | 1,0 | 1,2 | 0,8 | 1,0 | 1,0 |
| `kappa` | 0,5 | 0,5 | 1,0 | 2,0 | 4,0 in fuga, 0,5 dopo |
| ancora iniziale | **lognormale, mediana 49,5 m, dispersione 2,1** (entro 60 m) | **lognormale, mediana 540 m, dispersione 2,2** (entro 300 m) | casa | nessuna | nessuna |
| `pull` | 0,5 | 0,2 | 0,1 | 0 → 0,3 dopo | 0 → 0,4 dopo |
| `t_settle` media (h) | 0 | 0 | 0 | 12 | 6 |
| `h_pickup` /h | **0,00014** (0,002) | **0,00015** (0,003) | 0,08 | 0,01 | 0,003 |
| `h_home` /h | **0,00014** dal giorno 2 (0,004) | **0,00014** (0,010) | **0,0044** nelle prime 12 h, poi × 0,1 (0,020) | **0,0022** (0,010) | **0,00044** (0,002) |
| `h_dead` /h | 0,0002 | 0,0003 | 0,0003 | 0,0005 | 0,0010 |

Categorie miste quando non si sa: `cat` = casa 28 / libero 46 (le quote del campione di
Huang), `dog` = 50 / 30 / 20 (stima senza fonte).

### Come si tara (fase A)

Bersagli (`riferimenti.md` §A):
- **gatti** (Huang 2018, trovati vivi): gatto casa p25 / p50 / p75 = 9 / 39 / 137 m; gatto
  libero 14 / 300 / 1.609 m. **Rischi in competizione** (`lessons.md` #8): ogni gatto esce
  dallo stato libero al primo dei suoi eventi e si legge in quell'ora. Gli eventi sono i
  tre del motore (a casa → trovato a casa, distanza 0; raccolto → trovato in casa d'altri,
  distanza del punto di raccolta; morto → escluso) più uno che esiste **solo nella
  taratura**: trovato fuori da chi lo cerca (Huang: il 69% dei trovati vivi), con un rischio
  uguale a ogni distanza e costante a tratti (giorni 0-7, 7-30, 30-61) → la sua posizione.
  Si tarano insieme: la curva dei trovati vivi (34 / 50 / 56% entro 7 / 30 / 61 giorni),
  le quote per luogo entro 61 giorni (a casa 20% = 4% in casa + 19% degli 83% trovati
  fuori, «aspettava fuori casa»; in casa d'altri 11%; fuori il resto) e i quantili della
  distanza. Passi: una corsa del motore dà l'ora e il tipo degli eventi; i tre rischi della
  ricerca si risolvono esatti da quella corsa (la ricerca non dipende dal posto); `h_home` e
  `h_pickup` si scalano finché le quote tornano (i rischi non dipendono dal movimento nella
  zona di riferimento); poi griglia su ancora (mediana, dispersione) e passo. I rischi della
  ricerca si salvano in `calibrated.json` (`_search`) e servono solo a leggere Huang: il
  simulatore non li usa.
- **cani** (Kremer 2021, luogo della raccolta): 42% entro 120 m, 70% entro 1.609 m, le tre
  categorie insieme 50 / 30 / 20. Due scale di passo (socievole; diffidente e pauroso);
  `h_home` scalato perché i tornati da soli siano l'11% (Lord 2007: 8% su 71% ritrovati).
- Accettato se ogni quantile è entro ±20%; griglia grossa, poi fine, poi i primi cinque
  validati a 20.000 particelle. Dopo ogni modifica al motore si rifà (`lessons.md` #17).
  Esito: gatto casa sì (A5, 0,05), cani sì (A4, 0,135), gatto libero no (A5, 0,28).

### Calcolo

A ogni richiesta si **risimula da t0**, seme fisso: deterministico. 10.000 particelle
costano circa 1 ms all'ora: 90 giorni in 2-3 secondi. Ogni fattore che dipende dal tempo
usa l'ora che si sta vivendo, [h, h+1); l'ora «adesso» si arrotonda per eccesso dalla
mezz'ora (`lessons.md` #14, #15). All'ora «adesso» le particelle HOME escono dal conto:
se fosse tornato, chi chiede lo saprebbe.

### Uscite

- **Mappa**: celle da 50 m **centrate su casa**; valore = P(libero e nella cella), stimata
  con la **densità a nucleo adattiva**: ogni particella libera si allarga come una gaussiana
  di σ = max(25 m, α · distanza dalla 10ª vicina), α = 1,0 (scelta con C1: la copertura è
  quasi piatta fra 0,5 e 2,0). Calcolo: σ in classi a passo 2^¼ (il peso di una particella
  si divide fra le due classi attorno al suo σ, varianza conservata), un filtro gaussiano per
  classe sul riquadro delle sue particelle, i σ grandi su griglie 2, 4, 8… volte più rade
  riportate su quella fine per interpolazione. Rettangolo: il 99% delle particelle su
  ciascun asse più 2 volte il σ mediano (almeno ±200 m); la massa oltre si perde (~2%).
  PNG; GeoJSON come **quadtree**: blocchi quadrati da 50 m a 3,2 km, divisi in quattro
  finché tengono più dello 0,1% della massa, dai più densi fino al 99% della massa (ogni
  blocco con `p` e `size_m`), più i punti di casa e di «cerca qui». Sui due esempi: 0,4 e
  0,5 s, GeoJSON 93 KB e 0,6 MB.
- **Stati**: P(LOOSE), P(HELD), P(HOME) = 0, P(DEAD); P(torna da solo entro 7 giorni),
  simulando 168 ore in avanti senza prove.
- **Cerca qui**: fino a 5 punti, i punti più probabili della mappa, ad almeno 150 m l'uno dall'altro,
  ciascuno con la massa delle celle attorno (ogni cella a un punto solo); ora consigliata:
  gatti dalle 20:00 (o subito se è notte), cani subito se è giorno, altrimenti alle 6:00.
- **Raggio**: distanza da casa che contiene il 50% e il 90% della massa LOOSE.
- **Chiama**: sì se P(HELD) > 0,3 (soglia da tarare), con raggio = 95° percentile della
  distanza dei punti di raccolta + 10 km. L'elenco di canili e veterinari viene da OSM in
  v0.1.

## Le prove del modello (il metodo genoma)

Ogni misura si annota in `MISURE.md` **con la previsione scritta prima del risultato**; ogni
errore in `lessons.md`. Senza prove esterne l'accuratezza si misura solo così: contro i
numeri pubblicati (A, B) e contro un modello più semplice (C).

**A — Taratura**: sopra. `python -m sim.calibrate …`.

**B — Controllo predittivo** (`python -m sim.validate`), su numeri non usati in A:
- B1: gatti mescolati 164:150 (i trovati vivi di Huang per gruppo) contro Huang complessivo
  (9 / 50 / 500 m, 75% entro 500 m);
- B2: P(HOME entro t) e P(HOME o HELD entro t) contro i gatti trovati vivi (34 / 50 / 56% a
  7 / 30 / 61 giorni). Attenzione: la stessa curva è l'ingresso di A (`lessons.md` #9);
- B3: cani raccolti entro 5 giorni contro «oltre il 90% dei riuniti entro 5 giorni»
  (Kremer; da verificare se contati dalla perdita);
- B4: I-CAD (4% dei cani e 0,5% dei gatti passano dal canile) contro la quota di HELD fra i
  ritrovati: passa sempre, non ha potere.

**C — Confronto con il modello ad anelli** (`python -m sim.baseline`): 40 casi sintetici per
categoria, 50 verità indipendenti per caso con parametri perturbati del ±30%, ora di
partenza e «adesso» (fra 12 ore e 10 giorni) casuali. Anelli ai quantili 25/50/75/95/99%
della distanza della categoria a quell'ora, sulla stessa griglia da 50 m. Misura: area da
cercare, dalla cella più probabile, prima di arrivare alla verità (mediana e 90°
percentile), e copertura al 50% e 90%; per verità, senza gradini (`lessons.md` #26): quota
dove il simulatore cerca meno e media geometrica del rapporto. Il simulatore **batte** se
mediana e 90° percentile sono tutti e due sotto gli anelli. Se non batte, ci si ferma e si decide con Marcello.
In una zona uniforme il simulatore è per costruzione radiale come gli anelli: può batterli
in distanza (una densità più fedele di quattro anelli) ma in direzione solo con la mappa
della zona.

**C1 — La mappa è una probabilità calibrata?** (`python -m sim.validate --coverage`): verità
dallo stesso modello (una seconda simulazione indipendente); nelle celle che tengono il 50%
e il 90% della massa devono cadere il 50% e il 90% delle verità. Isola lo stimatore della
mappa dalla dinamica in pochi secondi. La regione si prende sulla massa della griglia, il
~98% di quella libera: al 90% ci si aspetta ~0,88. Test: tutte le categorie, intervallo a 4
errori standard dentro 0,45-0,58 e 0,84-0,95.

## Cosa non so ancora (buchi dichiarati)

- `h_pickup` dei cani non ha una fonte diretta: si ricava da Lord 2007 e dai tempi di
  ingresso in canile di Austin e Dallas.
- I bersagli mescolano popolazioni (Australia, Ohio, Dallas); nessuno studio è di Napoli.
  Il luogo in 3D porta la geometria di Napoli, i numeri restano quelli degli studi.
- La direzione di fuga del cane pauroso è casuale; in v0.1 dipende dalle strade.
- Le proporzioni fra le tre categorie di cani (50/30/20) sono inventate.
- Moltiplicatori di zona e del piano: stime senza fonte.
- In una zona uniforme la mappa è radiale: batte gli anelli in distanza (C2, in tutte le
  categorie sulla media geometrica), non in direzione. Nei casi estremi (verità fuori da
  tutte e due le mappe) è pari.

## Stack e struttura

Python 3.12, `numpy`, `scipy`, `matplotlib`, `pytest`; ambiente in `.venv/`. Da v0.1:
`osmnx`, `shapely`, `geopandas`. Codice, identificatori e commenti in **inglese**.

```
sim/
  __init__.py, __main__.py
  categories.py    # the five categories, mixtures, calibrated overrides
  calibrated.json  # phase A output
  environment.py   # zones, patches, floor: per-cell multipliers
  engine.py        # particles, hourly step, state transitions, run_case
  case.py          # case JSON, local projection
  outputs.py       # grid, PNG/GeoJSON map, states, advice
  calibrate.py     # phase A
  validate.py      # phase B, and C1 (map calibration: --coverage)
  baseline.py      # phase C: ring model vs simulator
  compare.py       # before / rings / now, side by side (out/confronto-prima-dopo.png)
  cli.py           # python -m sim <case.json> --now <iso> --out <dir>
tests/             # pytest -q: about 30 s
  conftest.py      # distribution-free quantile interval (4 SE)
  test_engine.py   # behaviour: determinism, zone, grid, spots, CLI < 10 s
  test_integrity.py  # exact arithmetic and closed-form theory, piece by piece
  test_pressure.py   # 90 days, 100k particles, extremes, 40 random cases
  test_targets.py    # phase A: the whole 4-SE interval within +-20% of each target
  test_hypotheses.py # phases B and C1; known failures are strict xfails
cases/
  esempio-gatto.json, esempio-cane.json
```

Formato del caso (`cases/*.json`):

```json
{
  "category": "cat_indoor",
  "home": {"lat": 40.85, "lon": 14.27},
  "lost_at": "2026-09-20T19:00",
  "collar": false,
  "area": {"zone": "apartment_blocks", "floor": 3,
           "patches": [{"zone": "park", "center": {"lat": 40.8512, "lon": 14.2688}, "radius_m": 120}]}
}
```

`category`: una delle cinque (`cat_indoor`, `cat_outdoor`, `dog_friendly`, `dog_wary`,
`dog_fearful`) o `cat` / `dog` se non si sa.

## Quando v0 è finito

- ✅ `python -m sim` gira su un caso di esempio in meno di 10 secondi (0,5 s) e produce
  mappa, stati, consigli.
- ✅ Fase A fatta per le cinque categorie (rifatta dopo la correzione del motore, A4),
  parametri e scarti in `MISURE.md` (gatto libero fuori di poco).
- ✅ Fase B fatta, con previsioni e risultati.
- ✅ Fase C fatta (senza prove, C2) e **superata** con la mappa lisciata: 0,44 volte gli
  anelli sulla mediana dell'area da cercare, 0,42 sul 90° percentile (`MISURE.md`).
- ✅ `pytest` verde: integrità, pressione, ipotesi; i fallimenti noti sono dichiarati.
