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
