# Prompt per la prossima sessione

Scritto il 2026-09-25. Si sostituisce a fine sessione.

---

Costruisci il simulatore v0 come descritto in `docs/simulatore.md`.

Leggi, in quest'ordine: `CLAUDE.md`, `docs/simulatore.md` (il progetto completo: modello,
categorie, parametri, prove, fasi di verifica, struttura, «quando è finito»),
`docs/MISURE.md` (il formato delle misure), `docs/STATO.md`. I numeri con le fonti sono in
`docs/riferimenti.md`; i concetti in `docs/matematica.md`. Non serve altro.

Stato: solo documenti, nessun codice. Repo pubblico su GitHub.

Il lavoro:
1. Il pacchetto `sim/` con la struttura di `simulatore.md`, in Python 3.12 con `numpy`,
   `scipy`, `matplotlib`, `pytest`. Niente OpenStreetMap in v0. Codice, nomi e commenti in
   inglese. Ambiente in `.venv/`.
2. `python -m sim cases/esempio-gatto.json --now … --out out/` produce mappa PNG e GeoJSON,
   probabilità dei quattro stati, i tre consigli. Sotto i 10 secondi.
3. Fase A (taratura delle cinque categorie), poi B e C, nell'ordine di `simulatore.md`.
   **Per ogni misura scrivi prima la previsione in `docs/MISURE.md`, poi lanci, poi
   scrivi il risultato**, anche se smentisce. Se il simulatore non batte il modello ad
   anelli (fase C), scrivilo e fermati: si decide insieme.
4. `pytest -q` verde.

Regole: agenti mai Fable; lavora tu, al massimo un Sonnet per una lettura grossa, uno alla
volta, dicendo perché. Niente commit né push finché non li chiedo. Prima di ogni commit i
documenti: `docs/archivio/FATTO.md` (cosa, come si prova), `docs/STATO.md` (solo se
cambia una decisione o un prossimo passo), `CLAUDE.md` (i comandi veri, la tabella).
Un parametro che cambia si corregge in `docs/simulatore.md`, non si appende.

A fine lavoro: resoconto in due punti (cosa è stato implementato, come lo provo) e il
prompt per la sessione dopo in `build/prompt-next.md`.
