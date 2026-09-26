# Fatto

Storico del lavoro, in coda. Nessuno lo legge a ogni turno.

### 2026-09-25 — Nasce il progetto
Tre giri di idee (censimento randagi dalle foto, manifesto OpenPaw Vet, collegare i post di
Facebook) fino all'idea che regge: il motore che dice dove cercare, alimentato da volantini
con QR, avvistamenti e ricerche. Ricerca bibliografica in otto lingue (`docs/riferimenti.md`),
rassegna dei metodi (`docs/matematica.md`), repo impostato con CLAUDE.md, STATO e hook di
documentazione. Progetto completo del simulatore v0 in `docs/simulatore.md` (per una
sessione nuova, senza altra memoria) e `docs/MISURE.md` vuoto con il formato. Nessun codice.

### 2026-09-25 — Simulatore v0 e fasi A, B, C
Pacchetto `sim/`: simulazione Monte Carlo solo matematica (animale, casa, zona, ora della
perdita → mappa PNG e GeoJSON, stati, dove cercare, raggio, quando chiamare i canili),
sotto il secondo. Fase A tarata (gatto da appartamento e cani sì, gatto libero a 0,23), B
con tre scoperte (rischi dei gatti troppo alti, mediana mista, cani raccolti tardi), C non
superata (mappa troppo rada; C1 lo isola). Avvistamenti e ricerche costruiti e poi tolti
su richiesta di Marcello. 54 test in tre famiglie, ~26 s. Si prova: `pytest -q`, poi
`python -m sim cases/esempio-gatto.json --now 2026-09-22T08:00 --out out/`.

### 2026-09-25 — Mappa lisciata; C1 e C2 superate
`make_grid` è una densità a nucleo adattiva (σ dalla 10ª vicina, classi di σ, griglie
via via più rade per i σ grandi); il GeoJSON è un quadtree; «cerca qui» lavora su una
finestra. C1 regge per tutte le categorie, C2 batte gli anelli (0,44 · 0,42). Comando a
0,4-0,5 s sui due esempi. 63 test + 4 `xfail`, ~35 s. `python -m sim.compare` (o doppio clic su `vedi-la-mappa.bat`) mette prima, anelli e ora fianco a fianco. Si prova: `pytest -q`,
`python -m sim.validate --coverage`, `python -m sim.baseline`.

### 2026-09-25 — Gatti a rischi in competizione (A5); il luogo in 3D deciso
La taratura dei gatti legge ogni gatto al primo dei suoi eventi, con la ricerca del
padrone solo nella taratura (`sim/calibrate.py`: `found_by`, `solve_search`,
`solve_cat_hazards`): `h_home` 5-6 volte più basso, B2 passa, C2 regge (0,39 · 0,42).
`sim.baseline` stampa anche la quota «cerca meno» e la media geometrica. Deciso con
Marcello il luogo in 3D al metro e, il 2026-09-26, niente casi raccolti da noi: solo
matematica, studi e dati aperti (`STATO.md`); fonti aperte trovate (`riferimenti.md` §B).
Si prova: `pytest -q --runslow`, `python -m sim.calibrate cat_indoor`, `python -m sim.validate`,
`python -m sim.baseline`.

### 2026-09-26 — Il luogo in 3D, primo prototipo sul luogo di prova (fuori dal motore)
`proto/luogo3d/`: scarica da dati aperti un luogo (OSM, 3D-GloBFP per le altezze,
TINITALY, WorldCover, Copernicus; solo un riquadro arrotondato esce dal computer), lo mette
su una griglia da 2 m, e simula il gatto di casa con la distanza di A5 e la direzione dal
luogo (Huang Tabella 4 per porta e finestra, Hanmer 2017 per la selezione). Tre mappe
affiancate in `privato/luogo/varianti-24h.png`; L1 e L1b in `MISURE.md`; studi GPS dei gatti
in `riferimenti.md` §A; email per il LiDAR in `privato/email-lidar.md`. Si prova:
`python -m proto.luogo3d.variants privato/luogo-prova.json privato/luogo` (3 s),
`pytest -q tests/test_place3d.py`.

### 2026-09-26 — Il luogo in 3D nel motore (variante 2)
`sim/place.py` e `Simulation(place=...)`: le ancore dei gatti prendono la direzione dal
luogo, un gatto resta più a lungo dove gli piace stare (Hanmer), un passo che finisce dentro
un edificio si rilancia; il caso accetta `"place": {"world": ...}` e `python -m sim` disegna
la mappa a 4 m. Senza luogo il motore dà gli stessi bit (taratura, B, C1, C2 identici). Al
50% la mappa del luogo di prova passa da 1,04 a 0,59 ha. Si prova: `pytest -q
tests/test_place3d.py`, `python -m proto.luogo3d.variants privato/luogo-prova.json
privato/luogo`, `python -m sim privato/caso-luogo-prova.json --now 2026-09-26T20:00 --out
privato/out-caso`.
### 2026-09-26 — Il luogo contro i GPS di gatti veri (L5)
`proto/gps/`: scarica le tracce di Cat Tracker (Kays et al. 2020, Movebank, CC0), stima la
casa, costruisce il luogo di ogni gatto da OpenStreetMap e confronta la mappa con il luogo
con la stessa mappa ruotata (punteggio logaritmico, permutazione, protocollo scritto prima).
Su 45 gatti del Regno Unito: effetto 2%, p = 0,030, non significativo. Si prova: `python -m
proto.gps.build_cats 72`, `python -m proto.gps.score privato/dati/cattracker`, `pytest -q
tests/test_gps_score.py`.
### 2026-09-26 — Il luogo smontato sui gatti veri (L6) e la conferma preparata (L7)
`proto/gps/pieces.py`: il punteggio di L5 con un pezzo della mappa alla volta, appaiato sugli
stessi gatti e sulle stesse rotazioni. Il segnale sta negli edifici come muri e nella
selezione di Hanmer, senza lisciatura (D 0,11 contro 0,02 della mappa del motore); la
raggiungibilità toglie un poco, le strade niente. `build_cats.py` scarica anche Stati Uniti,
Australia e Nuova Zelanda (571 gatti, casa dalle righe nascoste comprese, due server
Overpass); `score.py` sceglie mappa e σ e non salta più gatti in silenzio. Si prova: `python
-m proto.gps.pieces privato/dati/cattracker`, `pytest -q tests/test_gps_score.py`.
### 2026-09-26 — Il LiDAR a 1 m nel mondo del luogo (L8)
`fetch.py ... lidar` scarica le 64 tessere del riquadro arrotondato (DTM e DSM, Città
Metropolitana di Napoli, CC BY-SA 4.0), `world.py` ne fa `dtm1`, `dsm1`, `hmax1` (il motore non
li legge: livelli vecchi identici al bit). `metre.py` misura: con il terreno a 1 m un edificio
su cinque entro 200 m ha il tetto a portata di salto. Si prova: `python -m proto.luogo3d.fetch
privato/luogo-prova.json privato/luogo lidar`, poi `world` e `metre` sugli stessi argomenti.

**2026-09-26 — Il motore dopo L7 (L9).** Le ancore pesano `sel` sulle celle dove il gatto può
stare, senza la raggiungibilità (`Place.weight`; la regola di prima con `reach_weight=True`).
Senza luogo l'impronta è identica; sul luogo di prova ogni numero cambia meno dell'1%. Si
prova: `python -m sim.fingerprint`, `python -m proto.luogo3d.variants privato/luogo-prova.json
privato/luogo` (e `--reach-weight` per la base), `pytest -q`.

**2026-09-26 — L'acqua non è un posto (L11) e la rilettura di L9-L10 (L9b, L10b).** Nel motore
l'acqua di WorldCover (classe 80) non è più `open`: non ci si sta e non ci si passa, tranne sotto
una strada (i ponti). In `score.py` la mappa `full` di L5 è scritta per esteso ed `engine` è la
mappa del motore; `pieces.py` dà in più le quote per distanza dagli edifici per paese e le celle
irraggiungibili. Si prova: `pytest -q` (`test_water_is_no_place_for_a_cat`,
`test_full_stays_the_map_of_L5_and_engine_follows_the_engine`), `python -m proto.gps.pieces
privato/dati/cattracker-conferma --households 20` (i numeri di L7 identici al bit).

**2026-09-26 — La mappa come previsione (L12).** `combine` di `score.py` restituisce anche il
punteggio proprio delle sole posizioni vere (`S_real`), e `pieces.py` lo stampa accanto a D: la
mappa del motore ha D > 0 ma S < 0 (perde contro la radiale). Si prova: `python -m
proto.gps.pieces privato/dati/cattracker-conferma --households 20` (S fra graffe), `pytest -q`
(`test_a_map_can_rank_the_real_fixes_higher_and_still_forecast_worse`).

**2026-09-26 — Dentro gli edifici per tipo, il metro con l'errore del GPS, la prova sul Regno Unito
(L13).** `proto/gps/classes.py`: per ogni gatto GPS i tag degli edifici dalla risposta di OSM
ridipinta (griglia identica, controllata), 31 classi fini (casa, edifici per tipo e impronta,
fasce di distanza per superficie), la mappa a classi nella posizione vera sfocata dall'errore del
GPS prima del punteggio, il fit dei pesi (Gibbs a σ 0), la prova a paese escluso e su un secondo
insieme. Risultato: tipo e superficie non contano, la candidata (la casa sfocata) non passa il
Regno Unito, regge solo la mappa per fasce (+0,002-0,004). Si prova: `python -m proto.gps.classes
build|inside|fit|pieces privato/dati/cattracker-conferma`, `... test privato/dati/cattracker-conferma
--test privato/dati/cattracker`, `pytest -q tests/test_gps_classes.py`.

**2026-09-26 — Il gatto smarrito che si nasconde negli edifici, come opzione (L14).**
`PlaceParams(preference="lost")`: fuori le fasce dei residenti di L13 al posto di Hanmer, dentro gli
edifici diversi da casa che toccano terreno raggiungibile il riparo di Huang (`hide` 3,58);
`Place.pref` è quello che pesano ancore e passo, `Place.sel` resta Hanmer per le mappe GPS. Il
motore resta Hanmer: con `lost` le distanze vicine si allungano (xfail stretto). Si prova:
`python -m proto.luogo3d.variants privato/luogo-prova.json privato/luogo --preference lost`
(`varianti-24h-lost.json`), `pytest -q tests/test_place3d.py -k lost`.

**2026-09-26 — Il README con i numeri di oggi (R).** Riscritto sulla forma della guida di
Trochilus: cosa fa, risultati contro gli anelli (area tipica per animale), cosa ha di diverso, come
si prova, cosa manca; in cima la figura anelli contro mappa. `sim.baseline` scrive l'area tipica di
ogni mappa; `sim.compare --readme` disegna la figura; `proto.luogo3d.fetch` salta il LiDAR fuori
dalla provincia di Napoli (#59). Si prova: il README su GitHub; `python -m sim.baseline` rifà la
tabella; `pytest -q tests/test_place3d.py -k lidar`.
