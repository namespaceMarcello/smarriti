# Prompt per la prossima sessione

Scritto il 2026-09-26, dopo il luogo in 3D nel motore (L2, L3). Si sostituisce a fine
sessione.

---

Porta nel mondo del luogo i dati aperti al metro: il LiDAR a 1 m della Città Metropolitana di
Napoli (terreno e superficie) e le siepi a 5 m di Copernicus. Niente email né richieste a enti
(`lessons.md` #37).

Leggi, in quest'ordine: `CLAUDE.md`, `docs/STATO.md` (decisioni del 2026-09-26, «Il luogo in
3D, cosa resta», prossimo passo 1), `docs/simulatore.md` § «Il luogo in 3D», `docs/MISURE.md`
L1b, L2, L3, `docs/lessons.md` #33-#40, `docs/riferimenti.md` §B (le righe «LiDAR della Città
Metropolitana», «Copernicus HRL Small Woody Features», «Altezza della chioma a 1 m»), il codice
in `sim/place.py` e `proto/luogo3d/` (`fetch.py`, `world.py`, `variants.py`), e
`privato/luogo-prova.md` (il luogo vero: **mai** nei documenti, nei test, nei commit).

Stato: il luogo è nel motore (`Simulation(place=...)`, il caso accetta `"place"`, `python -m
sim` disegna la mappa a 4 m). Variante 2 (edifici e giardini, senza altezze). Senza luogo il
motore dà gli stessi bit di prima. Sul luogo di prova, gatto di casa dal primo piano a 24 ore:
regione al 50% 0,59 ha (1,04 senza luogo), posizioni contro la variante 1 0,50 · 0,34 · 0,16
(Hanmer 0,553 · 0,311 · 0,136), C1 0,47 / 0,73, distanze entro il 6%. Resta fuori la
vegetazione di Huang: gatti in `veg` 0,04 contro 0,25 (i cespugli dei giardini a 10 m non si
vedono). `pytest -q`: 82 passano in ~50 s.

Il compito:
1. `fetch.py`: le tessere LiDAR per il riquadro (WFS `sit:quadro_unione_lidar_dtm` e `_dsm` su
   `https://sit.cittametropolitana.na.it/geoserver/ows`, campo `url`; ASCII 500 × 500 a 1 m,
   EPSG:32633) e la maschera Copernicus a 5 m (`exportImage` sul server EEA). Solo il riquadro
   arrotondato a 0,01° esce dal computer. Cache in `privato/luogo/cache/`.
2. `world.py`: il terreno dal DTM a 1 m (medio sulla cella da 2 m), l'altezza sopra il suolo
   (DSM − DTM), uno strato «cespugli e siepi» (altezza 0,3-3 m fuori dagli edifici, o la
   maschera di Copernicus). Controllo prima: le quote LiDAR contro TINITALY sul luogo (scarto
   atteso di pochi metri) e contro il servizio del Ministero in 3 punti (`GetFeatureInfo`).
3. `sim/place.py`: un tipo di posto per i cespugli, con `sel` da uno studio (Hanmer: il
   naturale; Huang Tabella 6: sotto la vegetazione 16%); se non c'è, stima dichiarata.
4. Misura L4 con `proto.luogo3d.variants`: prima la previsione in `MISURE.md` (quanto sale
   `veg` verso 0,25, quanto cambia la regione al 50%, distanze entro il ±10%, C1 regge). Poi
   quanti tetti, muri e terrazzamenti sono a portata di salto con il terreno a 1 m: se tanti,
   la previsione e la misura della variante 3 con i dati nuovi.

Regole: la previsione prima di ogni misura, con la base letta dal JSON della misura
precedente (#39); ogni errore e ogni previsione sbagliata subito in `lessons.md`. Test
statistici a 4 errori standard (#28). Senza luogo il motore non deve cambiare: `python -m sim.fingerprint`
prima e dopo (L2a); se cambia, si rifà la taratura (#17). Licenza del LiDAR CC
BY-SA 4.0: i dati derivati restano in `privato/`. Agenti mai Fable; lavora tu, al massimo un
Sonnet per una lettura grossa, dicendo perché. Niente commit né push finché non li chiede
Marcello. Prima di un commit i documenti: `FATTO.md`, `STATO.md`, `simulatore.md`,
`riferimenti.md`, `CLAUDE.md` se cambiano i comandi.

Aspetta Marcello: il nome del progetto.

A fine lavoro: resoconto in due punti (cosa è stato implementato, come lo provo) e il
prompt per la sessione dopo in `build/prompt-next.md`.
