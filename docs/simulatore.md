# Il simulatore

Progetto completo del prototipo v0. Scritto il 2026-09-25 perché una sessione nuova possa
costruirlo senza altra memoria. I concetti stanno in `matematica.md`, i numeri con le fonti
in `riferimenti.md`, le previsioni e le misure in `MISURE.md`.

## Cosa fa

Dato un **caso** (animale, casa, ora della perdita, avvistamenti, ricerche fatte, volantini)
e un'ora «adesso», produce:

1. la **mappa**: per ogni cella, la probabilità che l'animale sia lì, libero, adesso;
2. la probabilità di ogni **stato**: libero, raccolto da qualcuno, tornato a casa, morto;
3. tre **consigli**: dove cercare adesso (e a che ora), dove mancano i volantini, se è ora
   di telefonare a canili e veterinari (e in quale raggio).

Niente interfaccia: una libreria Python con una riga di comando. Il sito arriva dopo e la
chiama.

## Il modello

### Particelle

N = 10.000 animali virtuali (parametro). Ognuna ha: posizione (x, y in metri, piano locale
centrato su casa), stato, direzione corrente, un'**ancora** (il nascondiglio scelto), il
peso. Passo temporale: **1 ora**. Orizzonte: fino a 90 giorni.

Stati: `LOOSE` (libero), `HELD` (raccolto da una persona), `HOME` (tornato da solo),
`DEAD`. Gli ultimi tre sono assorbenti. Solo `LOOSE` ha una posizione che conta.

### Movimento (ogni ora, solo LOOSE)

Passeggiata casuale correlata con pause e attrazione verso l'ancora:

1. Con probabilità `p_move(categoria, ora del giorno)` la particella si muove; altrimenti
   sta ferma (i gatti si nascondono di giorno, i cani si muovono di giorno).
2. Lunghezza del passo: lognormale con mediana `step_med` e dispersione `step_sigma`
   (coda grassa: i salti lunghi rari esistono).
3. Direzione: von Mises attorno alla direzione precedente con concentrazione `kappa`
   (alto = va dritto, come il cane in fuga; basso = gironzola).
4. Attrazione verso l'ancora: la posizione viene tirata verso l'ancora di una frazione
   `pull` della distanza (processo di Ornstein-Uhlenbeck discreto). Il gatto da
   appartamento ha ancora vicina e `pull` forte; il cane in fuga ha `pull` zero finché
   non si **assesta**.
5. Assestamento: dopo `t_settle` ore (estratto per particella da un'esponenziale), la
   particella sceglie come ancora la posizione corrente e da lì in poi fa escursioni
   locali. È quello che genera «cane trovato a 20 km, fermo nella stessa zona da giorni».
6. Ambiente (**v0.1, non v0**): barriere e permeabilità per cella da OpenStreetMap
   (autostrade, ferrovie, fiumi = barriera; parchi e giardini = attraenti per i gatti;
   densità di edifici = densità di persone). In v0 lo spazio è omogeneo.

### Transizioni di stato (ogni ora, solo LOOSE)

Rischi orari indipendenti (probabilità piccole, moltiplicate per i fattori):

| Transizione | Rischio base per ora | Fattori |
|---|---|---|
| LOOSE → HELD (raccolto) | `h_pickup(categoria)` | × densità di persone nella cella (v0: 1) × `1.5` se ha il collare × attività umana per ora del giorno (0.2 di notte) × crescente con la fame dopo il giorno 3 per i diffidenti |
| LOOSE → HOME | `h_home(categoria)` | × 2 di notte per i gatti; decade dopo 30 giorni |
| LOOSE → DEAD | `h_dead(categoria)` | × 5 vicino alle strade grandi (v0.1) |

Una particella HELD non ha più posizione utile: chi l'ha raccolta può essere ovunque. Si
registra però **dove** è stata raccolta: serve al raggio dei canili da chiamare.

### Le categorie e i parametri iniziali

Tutti i numeri qui sotto sono **stime di partenza** da tarare (fase A). Le fonti dei
bersagli stanno in `riferimenti.md`.

| Parametro | gatto casa | gatto libero | cane socievole | cane diffidente | cane pauroso |
|---|---|---|---|---|---|
| `p_move` giorno / notte | 0,05 / 0,30 | 0,15 / 0,40 | 0,60 / 0,20 | 0,50 / 0,30 | 0,40 / 0,50 |
| `step_med` (m) | 15 | 40 | 150 | 250 | 500 in fuga, 100 dopo |
| `step_sigma` | 1,0 | 1,2 | 0,8 | 1,0 | 1,0 |
| `kappa` | 0,5 | 0,5 | 1,0 | 2,0 | 4,0 in fuga, 0,5 dopo |
| ancora iniziale | entro 60 m da casa | entro 300 m | casa | nessuna | nessuna |
| `pull` | 0,5 | 0,2 | 0,1 | 0 → 0,3 dopo l'assestamento | 0 → 0,4 |
| `t_settle` media (h) | 0 (già ferma) | 0 | — | 12 | 6 (fine della fuga) |
| `h_pickup` /h | 0,002 | 0,003 | 0,08 | 0,01 | 0,003 |
| `h_home` /h | 0,004 dal giorno 2 | 0,010 | 0,020 nelle prime 12 h | 0,010 | 0,002 |
| `h_dead` /h | 0,0002 | 0,0003 | 0,0003 | 0,0005 | 0,0010 |

Bersagli per la taratura (`riferimenti.md` §A):
- gatto casa: media 39 m, 75° percentile 137 m (Huang 2018);
- gatto libero: media 300 m, 75° percentile 1.609 m; tutti i gatti: 75% entro 500 m,
  mediana 50 m (Huang 2018);
- cani (tutte le categorie insieme, luogo della **raccolta**): 42% entro 120 m, 70% entro
  1,6 km (Kremer 2021). Le proporzioni fra le tre categorie di cani non sono note: si
  parte da 50 / 30 / 20 e si segna come stima.

La distanza «al ritrovamento» dei gatti dipende da quando vengono trovati: per
confrontarla si estrae per ogni particella un'ora di ritrovamento dalla curva di Huang
(34% entro 7 giorni, ~50% entro 30, 56% entro 61) e si legge la posizione a quell'ora.

### Le prove (aggiornamento dei pesi)

Ogni prova moltiplica il peso delle particelle; poi si normalizza. Quando la dimensione
effettiva del campione scende sotto N/2 si ricampiona (filtro particellare standard).

**Avvistamento** a (xs, ys) all'ora ts, con credibilità c (0,6 se sconosciuta, 0,9 se c'è
una foto, 0,3 se vago) e incertezza σ (100 m di base, più quella dichiarata):
- particella LOOSE all'ora ts: peso × [(1 − c) + c · exp(−d² / 2σ²)], con d la distanza
  fra particella e avvistamento all'ora ts (tolleranza ±1 h: si prende la posizione più
  vicina);
- particella HELD/HOME/DEAD all'ora ts: peso × (1 − c).
Un avvistamento falso non azzera niente: abbassa.

**Ricerca** in un'area A (poligono o cerchio) fra t1 e t2 con metodo m, esito negativo:
- particella LOOSE dentro A in quell'intervallo: peso × (1 − POD_m · vis(categoria, ora));
- fuori: invariato.
POD iniziali (stime; da derivare da Koester 2014 e tarare sui casi):

| Metodo | POD |
|---|---|
| in auto | 0,10 |
| a piedi di giorno, chiamando | 0,30 cani · 0,15 gatti |
| a piedi di notte con torcia (gatti) | 0,50 |
| con cane da ricerca o termocamera | 0,60 |

`vis` = 1 per i cani; per i gatti 0,5 di giorno (nascosti), 1 di notte.

**Volantini**: in v0 **non** aggiornano i pesi (la scansione dice dov'è il volantino, non
l'animale). Servono solo ai consigli. Ogni volantino ha un id: si contano gli avvistamenti
arrivati da ciascuno.

**Ordine di calcolo**: a ogni richiesta si **risimula da t0** con tutte le prove, seme
fisso. Niente stato incrementale: più semplice, deterministico, e 10.000 × 2.000 ore in
numpy sono secondi.

### Uscite

- **Mappa**: griglia di celle da 50 m nel rettangolo che contiene il 99% delle particelle
  LOOSE; valore = massa di peso LOOSE nella cella. Formati: PNG (matplotlib) e GeoJSON.
- **Stati**: P(LOOSE), P(HELD), P(HOME), P(DEAD).
- **Cerca qui**: le celle con più massa entro il raggio raggiungibile, con l'ora consigliata
  (i gatti: crepuscolo e notte).
- **Manca un volantino**: celle con più massa cumulata nelle prossime 48 ore, meno quelle
  già coperte da un volantino entro 300 m.
- **Chiama**: se P(HELD) > 0,3 (soglia da tarare): sì, con raggio = 95° percentile della
  distanza dei punti di raccolta + 10 km (il trasporto umano). L'elenco di canili e
  veterinari viene da OSM (`amenity=veterinary`, `amenity=animal_shelter`) in v0.1.

## Le prove del modello (il metodo genoma)

Ogni misura si annota in `MISURE.md` **con la previsione scritta prima del risultato**.
Un risultato che smentisce si scrive uguale.

**A — Taratura.** Per categoria, ricerca sui parametri (griglia grossolana, poi ABC
semplice: accetta i parametri che portano i quantili entro ±20% dei bersagli). Si registrano
i parametri trovati e quanto restano lontani dai bersagli.

**B — Controllo predittivo** su numeri **non usati** in A:
- gatti: la curva di ritrovamento nel tempo di Huang, separata casa/libero;
- cani: oltre il 90% dei rientri entro 5 giorni (Kremer): confrontare con la distribuzione
  dell'ora di raccolta del modello;
- I-CAD: passano dal canile il 4% dei cani ritrovati e lo 0,5% dei gatti: confrontare con
  P(HELD) a 30 giorni, sapendo che HELD include chi tiene l'animale senza canile.

**C — Confronto con il modello ad anelli** (Koester): sulla stessa serie di casi sintetici
con avvistamenti, misurare la **frazione di area da cercare** per includere la posizione
vera al 50% e al 90% di massa. Se il simulatore non batte gli anelli, il simulatore non
vale la complessità: si scrive e si cambia strada. I casi sintetici si generano con
parametri perturbati del ±30% rispetto a quelli tarati, per non premiare il modello che
si confronta con sé stesso.

**D — Casi reali.** Per ogni caso a Napoli: a ogni prova nuova si salva la mappa; alla
chiusura si registrano punto e ora del ritrovamento e come è stato trovato. Metrica: la
frazione di area con probabilità più alta della cella del ritrovamento (0 = perfetto,
0,5 = a caso). Bersaglio: mediana ≤ 0,10. **Prima** della chiusura del caso si scrive la
previsione.

## Cosa non so ancora (buchi dichiarati)

- I POD sono stime; la letteratura SAR (Koester 2014) dà larghezze di sweep per persone,
  non per animali.
- `h_pickup` non ha una fonte diretta: si ricava da Lord 2007 (chi trova un animale) e dai
  tempi di ingresso in canile di Austin e Dallas.
- I bersagli mescolano popolazioni (Australia, Ohio, Dallas). La taratura vera arriva dai
  casi nostri.
- La direzione di fuga del cane pauroso in v0 è casuale; in v0.1 dipende dalle strade.
- Le proporzioni fra le tre categorie di cani sono inventate (50/30/20).
- La quota di gatti da appartamento fra gli smarriti non è nota.

## Stack e struttura

Python 3.12, `numpy`, `scipy`, `matplotlib`, `pytest`. Da v0.1: `osmnx`, `shapely`,
`geopandas`. Niente GPU, niente servizi esterni in v0. Codice, identificatori e commenti
in **inglese** (il progetto sarà pubblico); documenti in italiano finché è privato.

```
sim/
  __init__.py
  categories.py   # the five categories and their parameters (one dataclass each)
  engine.py       # particles, hourly step, state transitions, evidence weighting, resampling
  evidence.py     # Sighting, Search, Flyer dataclasses + JSON loading
  outputs.py      # grid, PNG/GeoJSON map, recommendations
  calibrate.py    # phase A: parameter search against the targets
  baseline.py     # ring model (Koester-style) for phase C
  cli.py          # python -m sim <case.json> --now <iso> --out <dir>
tests/
  test_engine.py  # determinism, weights sum to 1, a sighting pulls mass, a search removes mass
  test_targets.py # calibrated categories hit the quantiles within tolerance
cases/
  esempio-gatto.json, esempio-cane.json
docs/MISURE.md    # predictions and measurements, in order
```

Formato del caso (`cases/*.json`):

```json
{
  "category": "cat_indoor",
  "home": {"lat": 40.85, "lon": 14.27},
  "lost_at": "2026-09-20T19:00",
  "collar": false,
  "sightings": [{"lat": 40.851, "lon": 14.272, "at": "2026-09-21T06:30", "credibility": 0.6, "sigma_m": 100, "flyer_id": null}],
  "searches": [{"center": {"lat": 40.85, "lon": 14.27}, "radius_m": 200, "from": "2026-09-20T21:00", "to": "2026-09-20T23:00", "method": "foot_night_torch"}],
  "flyers": [{"id": "A1", "lat": 40.8505, "lon": 14.2705, "at": "2026-09-21T09:00"}]
}
```

Comandi previsti (entrano nel `CLAUDE.md` quando esistono):

```bash
python -m sim cases/esempio-gatto.json --now 2026-09-22T08:00 --out out/   # mappa + consigli
python -m sim.calibrate cat_indoor        # fase A per una categoria, scrive i parametri
python -m sim.baseline cases/…            # anelli vs simulatore (fase C)
pytest -q
```

## Quando v0 è finito

- `python -m sim` gira su un caso di esempio in meno di 10 secondi e produce mappa, stati,
  consigli.
- Fase A fatta per le cinque categorie, parametri e scarti in `MISURE.md`.
- Fase B e C fatte, con previsione scritta prima e risultato dopo, anche se negativo.
- `pytest` verde.
- `CLAUDE.md` aggiornato con i comandi veri e `STATO.md` con quello che resta aperto.
