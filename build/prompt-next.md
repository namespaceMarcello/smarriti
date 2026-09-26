# Prompt per la prossima sessione

Scritto il 2026-09-26, dopo il test sui gatti GPS veri (L5). Si sostituisce a fine
sessione.

---

Prima di tutto: il luogo **non è dimostrato sui gatti veri** (L5 in `docs/MISURE.md`: 45 gatti
GPS del Regno Unito, effetto 2%, p = 0,030 contro la soglia 0,001). Il compito è capire quale
pezzo del luogo porta il segnale e quale lo toglie, poi preparare un test di conferma più
grande. Il LiDAR a 1 m viene dopo.

Leggi, in quest'ordine: `CLAUDE.md`, `docs/STATO.md` (decisioni del 2026-09-26, «Il luogo in
3D, cosa resta», prossimo passo 1), `docs/simulatore.md` § «Il luogo in 3D», `docs/MISURE.md`
L1b, L2, L3, **L5**, `docs/lessons.md` #33-#42, `docs/matematica.md` (punteggio logaritmico e test per rotazione), `proto/gps/`, `docs/riferimenti.md` §B (le righe «Cat Tracker», «LiDAR della Città
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
1. Esplorativo, sui 45 gatti (`python -m proto.gps.score privato/dati/cattracker`, dati già in
   `privato/dati/cattracker/`): lo stesso punteggio con un pezzo alla volta: solo gli edifici
   come muri (sel = 1 ovunque, niente raggiungibilità), solo la selezione di Hanmer, solo la
   raggiungibilità, senza lisciatura (σ del GPS 5, 10, 20 m). Si scrive che è esplorativo:
   non conferma niente.
2. Il test di conferma nuovo: protocollo scritto prima in `MISURE.md` (la mappa scelta al
   punto 1, soglia, previsione, numero di gatti calcolato con margine: `lessons.md` #42) sui
   gatti di Stati Uniti, Australia e Nuova Zelanda (Cat Tracker, Movebank, CC0: `move.885`,
   `move.876`, `move.879`), con `proto/gps/build_cats.py` esteso a quei dataset. Un solo
   lancio.
3. Se resta tempo: il LiDAR a 1 m della Città Metropolitana di Napoli nel mondo del luogo
   (`riferimenti.md` §B).

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
