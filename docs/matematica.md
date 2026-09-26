# La matematica

I concetti che usiamo, cosa danno, e da dove vengono. Nessuno è inventato da noi: sono
validati per persone disperse e animali selvatici. Le fonti complete stanno in
`riferimenti.md` §C.

## I concetti

| Concetto | Cosa ci dà | Fonte | Stato |
|---|---|---|---|
| **Simulazione Monte Carlo** di dispersi | migliaia di animali virtuali mossi ora per ora: la distribuzione di dove può essere, non un punto | Lin & Goodrich 2010; Hashimoto 2022 (persone, sul terreno) | in uso |
| **Lost Person Behavior** (Koester, ISRID) | il modello da battere: per categoria «il 50% entro X, il 95% entro Y», cioè anelli attorno al punto di partenza | Koester 2008; Sava 2015 | in uso come confronto (fase C) |
| **Ecologia del movimento** | passeggiate casuali correlate con pause, code «grasse» (i salti lunghi rari), attrazione verso un nascondiglio (Ornstein-Uhlenbeck) | Tilles 2016; Patterson 2017 | in uso |
| **Analisi di sopravvivenza** | la curva «probabilità che sia ancora libero dopo N giorni», con uscite diverse: raccolto, tornato, morto | Huang 2018 per i gatti | in uso (rischi orari) |
| **Rischi in competizione** | le uscite dallo stato libero si tarano insieme, all'ora dell'evento, sulla curva dei ritrovamenti | — | in uso: taratura dei gatti (A5, `lessons.md` #8) |
| **Stima della densità a nucleo adattiva** | da punti a mappa: ogni particella si allarga quanto la distanza dalla 10ª vicina, stretta dove sono fitte, larga dove sono rade; si calcola per classi di σ su griglie via via più rade | Breiman, Meisel & Purcell 1977 (da verificare alla fonte) | in uso: la mappa (C1 e C2 superate, `MISURE.md`) |
| **Calibrazione della previsione** | una mappa è una probabilità solo se la verità cade nel suo 90% nove volte su dieci; si misura con verità estratte dallo stesso modello | — | in uso (C1) |
| **Intervalli dei quantili senza ipotesi** | l'intervallo di un quantile dalle statistiche d'ordine (binomiale): un test passa solo se tutto l'intervallo sta nella tolleranza | — | in uso (`tests/conftest.py`) |
| **Funzione di selezione delle risorse** (rapporti di Manly) | quanto un animale usa un tipo di posto rispetto a quanto ce n'è: uso / disponibilità, standardizzato a somma 1. Nel luogo in 3D è il peso di ogni tipo di posto | Hanmer 2017 (gatti: giardino 0,553, costruito 0,311, naturale 0,136) | in uso nel prototipo; si legge contro il modello senza luogo alla stessa distanza (`lessons.md` #36) |
| **Cammino minimo su una griglia di costi** (Dijkstra) | quanto costa arrivare a ogni posto dalle uscite di casa: edifici e tetti alti sono muri, le strade grandi costano, la salita costa; `reach = distanza in linea d'aria / costo` | — | in uso nel prototipo (`scipy.sparse.csgraph.dijkstra`, 360.000 celle in 0,2 s) |
| **Campionamento condizionato all'anello** | si estrae prima la distanza (dalla taratura), poi la direzione fra le celle a quella distanza con i pesi del luogo: la distribuzione delle distanze resta esatta, cambia solo la direzione | — | in uso nel motore, `sim/place.py` (prova: `test_place3d.py`) |
| **Catena con attesa** | una particella che a ogni ora si muove con probabilità q(x), altrimenti resta: l'occupazione è la distribuzione dei punti d'arrivo per 1/q(x). Con q ∝ 1/sel il tempo passato in un tipo di posto va con la sua selezione; dividere per la media di sel dove arrivano i passi tiene il numero di passi, quindi le distanze. Se un passo che cade fuori si rilancia (nucleo K ristretto al libero e rinormalizzato), con K simmetrico l'occupazione va con Z(x), la parte di K che cade nel libero: un po' meno dove è fitto; se invece si resta fermi (Metropolis) l'occupazione è uniforme ma si perdono passi | — | in uso nel motore: la selezione nel passo e il rilancio (L2, L3 in `MISURE.md`) |
| **Valori estremi** (Gumbel) | la coda delle distanze: fino a dove può arrivare. In Python `scipy.stats.genextreme` | — | da provare |

## Come si incastrano

```
categorie (Koester → animali)
   → movimento (ecologia) dentro il luogo in 3D
   → simulazione Monte Carlo, uscite in competizione (sopravvivenza)
   → mappa (densità a nucleo) · raggio · «chiama i canili»
provata contro i numeri pubblicati (A, B) e contro gli anelli (C)
```

## Cosa non è vago

- Peso e taglia non prevedono la distanza; il **temperamento** e il **tempo** sì
  (`riferimenti.md`: Albrecht; Huang 2018; Kremer 2021).
- Il cane a 30 km è la **coda** della distribuzione, oppure è stato trasportato: due
  spiegazioni diverse, due stati diversi nel modello.
- In una zona uniforme la simulazione è radiale come gli anelli: batte gli anelli in
  direzione solo con la mappa della zona (C2).

## Strumenti pronti

Python: `scipy.spatial.cKDTree` e `scipy.ndimage` (densità a nucleo), `scipy.stats`
(valori estremi), `scipy.sparse.csgraph` (cammini minimi), `lifelines` (sopravvivenza),
`pyshp` e `tifffile` (shapefile e GeoTIFF in Python puro: `lessons.md` #31). R: `ctmm`,
`moveHMM` (ecologia del movimento).
