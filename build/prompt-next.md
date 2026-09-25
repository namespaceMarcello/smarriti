# Prompt per la prossima sessione

Scritto il 2026-09-25. Si sostituisce a fine sessione. Vale se Marcello ha scelto la
**strada consigliata** per la fase C (`docs/STATO.md`, «Da decidere»); se ha scelto altro,
si riscrive da lì.

---

Rendi la mappa del simulatore una probabilità calibrata, poi ripeti le fasi C1 e C2.

Leggi, in quest'ordine: `CLAUDE.md`, `docs/STATO.md`, `docs/MISURE.md` (le voci C1 e C2),
`docs/lessons.md`, `docs/simulatore.md` (§ Uscite e § Le prove del modello).

Il perimetro, deciso da Marcello: un simulatore **solo matematico**. Dati animale, casa,
zona e ora della perdita, predice dove si trova l'animale adesso. Dopo la perdita non
riceve niente: né avvistamenti, né ricerche, né volantini. Non si reintroducono.

Stato: il simulatore v0 esiste (`sim/`), `pytest -q` dà 47 passati e 7 `xfail` stretti in
~26 s. La fase C (C2, senza prove) non è superata: il simulatore perde contro gli anelli
(45 volte sulla mediana dell'area da cercare), vince sul gatto da appartamento (0,28) e
perde dove l'istogramma di particelle è rado. C1 lo isola: copertura al 90% 0,87-0,89 dove
le particelle sono fitte, 0,04-0,64 dove si spargono.

Il lavoro:
1. In `sim/outputs.py`, `make_grid` diventa una stima a nucleo adattiva: ogni particella
   libera si allarga come una gaussiana di raggio σᵢ = max(cella/2, α · dₖ(i)), con dₖ la
   distanza dalla k-esima vicina (`scipy.spatial.cKDTree`, k ≈ 10, α da scegliere con C1).
   Per la velocità: particelle raggruppate per classi di σ (potenze di 2), un istogramma
   per classe, `scipy.ndimage.gaussian_filter` per classe, somma. Il rettangolo si allarga
   di 2σ. Tutto il resto (PNG, GeoJSON, «cerca qui», raggio, `baseline.py`) usa la nuova
   griglia. Il comando resta sotto il secondo sui due esempi.
2. **Prima di misurare**, la previsione in `docs/MISURE.md`: copertura al 50% e al 90% per
   categoria (C1), rapporto simulatore / anelli su mediana e 90° percentile (C2). Poi
   `python -m sim.validate --coverage` e `python -m sim.baseline`, e il risultato, anche se
   smentisce.
3. Se C1 passa, i tre `xfail` stretti di `test_c1_sparse_maps_are_not_yet_calibrated`
   diventano rossi: si tolgono e si allarga `CALIBRATED_MAPS` a tutte le categorie.
4. Se C2 ora batte gli anelli (mediana **e** 90° percentile sotto): si scrive, e si passa
   ai rischi dei gatti in competizione (`STATO.md`, problemi aperti). Se non batte:
   scrivilo, fermati, si decide insieme.

Regole: ogni errore e ogni cosa che fallisce va subito in `docs/lessons.md` (cosa, perché,
regola, controllo). I test restano sotto i ~40 s; ogni test statistico passa solo se
l'intervallo a 4 errori standard sta nella tolleranza. Dopo ogni modifica al motore si
rifà la taratura. Agenti mai Fable; lavora tu, al massimo un Sonnet per una lettura
grossa, dicendo perché. Niente commit né push finché non li chiedo. Prima di un commit i
documenti: `docs/archivio/FATTO.md`, `docs/STATO.md`, `docs/simulatore.md` (si corregge la
riga), `CLAUDE.md` se cambiano i comandi.

A fine lavoro: resoconto in due punti (cosa è stato implementato, come lo provo) e il
prompt per la sessione dopo in `build/prompt-next.md`.
