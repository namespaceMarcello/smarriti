# Prompt per la prossima sessione

Scritto il 2026-09-26, dopo il primo prototipo del luogo in 3D (L1, L1b). Si sostituisce a
fine sessione.

---

Porta nel motore il luogo in 3D **secondo la variante scelta da Marcello** (1 oggi a cerchi,
2 con edifici e giardini, 3 con anche i dislivelli: `privato/luogo/varianti-24h.png`). Se la
sua scelta non è ancora nella conversazione, chiedigliela prima di toccare `sim/`.

Leggi, in quest'ordine: `CLAUDE.md`, `docs/STATO.md` (la decisione sulle fonti del
2026-09-26 e il problema «Il luogo in 3D aspetta la scelta»), `docs/simulatore.md` § «Il
luogo in 3D — progetto» (regole, parametri con fonte, prove 1-5, esito), `docs/MISURE.md`
L1 e L1b, `docs/lessons.md` #30-#36, `docs/riferimenti.md` §A (Huang Tabelle 4 e 6, Hanmer
2017, Fardell 2021, Bischof 2022) e §B (3D-GloBFP, TINITALY, WorldCover, ANNCSU, LiDAR), il
codice in `proto/luogo3d/`, e `privato/luogo-prova.md` (il luogo vero: **mai** nei
documenti, nei test, nei commit).

Stato: il prototipo sta fuori dal motore (`PlaceSimulation` è una sottoclasse di
`sim.engine.Simulation`). Sul luogo di prova, gatto di casa dal primo piano a 24 ore: le
distanze restano quelle di A5 (entro l'1%), C1 regge (0,48 / 0,74), la regione al 50% scende
da 1,04 a 0,72 ha; la selezione di Hanmer sceglie le ancore ma il passo attorno all'ancora la
diluisce (liberi 0,29 · 0,63 · 0,08 contro 0,25 · 0,66 · 0,09 senza luogo); la variante 3
differisce dalla 2 del 5% perché nessun tetto è a portata di salto con altezze a 8 m e
terreno a 10 m. `pytest -q`: i test di prima più `tests/test_place3d.py` (8, < 1 s).

Il lavoro, secondo la scelta:
1. **Variante 2 o 3**: spostare in `sim/` quello che serve (un modulo `sim/place.py` con
   mondo, superfici, uscite, raggiungibilità, ancore; il caso accetta un luogo), senza
   cambiare nulla per chi non passa un luogo. Dopo ogni modifica al motore si rifà la
   taratura (`lessons.md` #17) e si rilanciano A, B, C1, C2.
2. **La selezione nel passo**: il moltiplicatore `stay` del motore per tipo di posto, in
   modo che il tempo passato stia come i rapporti di Hanmer, normalizzato perché le
   distanze non cambino (prove 1-2). Previsione prima: di quanto sale la variazione totale
   contro la variante 1 (oggi 0,27) e se i liberi tornano con Hanmer letti contro la 1.
3. **Variante 1**: niente motore; si passa al punto 2 di `STATO.md` (Dallas e Austin).
4. Le fonti aperte al metro (niente email al Ministero, `lessons.md` #37): leggere il resoconto della
   ricerca in `docs/riferimenti.md` §B e portare in `proto/luogo3d/fetch.py` quelle verificate.

Regole: la previsione in `docs/MISURE.md` prima di ogni misura; ogni errore e ogni
previsione sbagliata subito in `docs/lessons.md` (cosa, perché, regola, controllo). Test
statistici sull'intervallo a 4 errori standard (#28); un controllo contro uno studio usa le
definizioni del modello (#34) e si legge contro la variante senza luogo (#36). Se esiste
`~/.claude/macchina-ferma` i comandi pesanti partono a priorità bassa. Agenti mai Fable;
lavora tu, al massimo un Sonnet per una lettura grossa, dicendo perché. Niente commit né push
finché non li chiede Marcello. Prima di un commit i documenti: `FATTO.md`, `STATO.md`,
`simulatore.md`, `CLAUDE.md` se cambiano i comandi.

Aspettano Marcello: la scelta della variante, il nome del progetto.

A fine lavoro: resoconto in due punti (cosa è stato implementato, come lo provo) e il
prompt per la sessione dopo in `build/prompt-next.md`.
