# Prompt per la prossima sessione

Scritto il 2026-09-26, dopo L13, L14 e R (il README). Si sostituisce a fine sessione.

---

Prima di tutto: **prima il modello, poi il sito** (Marcello). E **nessun limite dato per
scontato**: un'idea, per quanto assurda, si prova prima di giudicarla; se la matematica che serve
non c'è, si inventa (`CLAUDE.md`, lo spirito).

Dove siamo:
- **L13**: il metro è S con l'errore del GPS dentro (`proto/gps/classes.py`). Per gatti residenti
  il paesaggio di OSM dà al massimo 0,002-0,004 nat per posizione: regge solo la mappa per fasce
  di distanza dagli edifici, positiva in tutti e quattro gli insiemi. Tipo e superficie degli
  edifici non contano. La candidata della regola (la casa del gatto sfocata, +0,012) non ha
  passato il Regno Unito (−0,005): era il centro degli anelli, non il paesaggio.
- **L14**: la regola del gatto smarrito è nel codice come opzione (`PlaceParams(preference="lost")`:
  fuori le fasce di L13, dentro gli edifici diversi da casa il riparo di Huang, `hide` 3,58), ma
  **non è il motore**: con `hide` nella selezione nel passo `sel_ref` sale a 1,5-1,7, il gatto fuori
  (alla porta) si muove 1,5-1,7 volte più del tarato e il primo quartile delle distanze sale del
  13-28% (xfail stretto `test_the_lost_rule_keeps_the_walk_distances`). Con le sole ancore il
  passo da 10-25 m riporta i gatti negli edifici quasi al caso (0,34 contro 0,33).
- **R**: il README pubblico ha solo numeri di oggi (la tabella da `sim.baseline`, la figura da
  `sim.compare --readme`, le distanze e C1 da `MISURE.md` R). Se un cambio al motore ne muove uno,
  si rimisura e il README cambia nello stesso commit.

Leggi, in quest'ordine: `CLAUDE.md`, `docs/STATO.md` (prossimi passi 1-3), `docs/MISURE.md` L13 e
L14, `docs/lessons.md` #56-#60, `docs/simulatore.md` («La selezione nel passo» e la tabella dei
parametri), `docs/matematica.md` (la catena con attesa), `sim/engine.py` (`_attach`, `step`,
`_fit_steps`), `sim/place.py`.

Il compito, `STATO.md` passo 1: **il gatto smarrito che si nasconde senza cambiare le distanze**.
1. Smonta prima di progettare: sulla città sintetica fitta e sul luogo di prova misura dove nasce
   lo spostamento del primo quartile (ora per ora: quando i gatti lasciano la porta, con e senza
   `hide` nel passo). Il conto della catena con attesa (`matematica.md`) dice quale `sel_ref`
   terrebbe la media di `p_move` dove i gatti sono davvero.
2. Progetta il nascondersi come tempo passato fermo in un riparo che tenga le distanze di A5.
   Idee da provare, anche assurde: uno stato «nascosto» con entrata e uscita orarie (Huang: i
   gatti smarriti stanno nascosti e zitti); una `sel_ref` presa sulle posizioni della variante 1
   ora per ora invece che sulle ancore; la selezione solo sulla fine del passo (accettazione come
   in Metropolis) invece che su `p_move`. Scegli con i numeri.
3. Previsione scritta prima (in `MISURE.md`, L15): l'invariante delle distanze (±10% sui quartili,
   4 errori standard, città sintetica e luogo di prova), la quota dei gatti sciolti entro 200 m
   negli edifici, la regione al 50%, C1. Poi, se regge, `lost` diventa il motore: l'impronta senza
   luogo identica, l'xfail tolto, L2-L3 rifatti con `variants.py`.
4. Se avanza tempo: `STATO.md` passo 2 (il centro del gatto: porta, cella più densa o edificio) o
   3 (l'errore del GPS dalle righe nascoste dei gatti fermi).

Regole: previsione prima di ogni misura; ogni errore in `lessons.md`; test a 4 errori standard;
un «identico» si prevede solo se il cambio non tocca nessuna cella (#54); una mappa si giudica con
S accanto a ogni test di associazione (#55); un peso forte nel passo si prova sull'invariante delle
distanze prima (#58). Agenti mai Fable; lavora tu. Niente commit né push finché non li chiede
Marcello. Prima di un commit i documenti: `FATTO.md`, `STATO.md`, `simulatore.md`,
`riferimenti.md`, `CLAUDE.md`, README.

Aspetta Marcello: il nome del progetto.

A fine lavoro: resoconto in due punti (cosa è stato implementato, come lo provo) e il prompt
per la sessione dopo in `build/prompt-next.md`.
