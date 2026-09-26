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
