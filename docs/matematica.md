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
| **Rischi in competizione** | le uscite dallo stato libero si tarano insieme, all'ora dell'evento, sulla curva dei ritrovamenti | — | da provare (`lessons.md` #8) |
| **Stima della densità a nucleo adattiva** | da punti a mappa: ogni particella si allarga quanto la distanza dalle vicine, stretta dove sono fitte, larga dove sono rade | — | da provare (C1, C2) |
| **Calibrazione della previsione** | una mappa è una probabilità solo se la verità cade nel suo 90% nove volte su dieci; si misura con verità estratte dallo stesso modello | — | in uso (C1) |
| **Intervalli dei quantili senza ipotesi** | l'intervallo di un quantile dalle statistiche d'ordine (binomiale): un test passa solo se tutto l'intervallo sta nella tolleranza | — | in uso (`tests/conftest.py`) |
| **Valori estremi** (Gumbel) | la coda delle distanze: fino a dove può arrivare. In Python `scipy.stats.genextreme` | — | da provare |

## Come si incastrano

```
categorie (Koester → animali)
   → movimento (ecologia) dentro la zona (OpenStreetMap da v0.1)
   → simulazione Monte Carlo, uscite in competizione (sopravvivenza)
   → mappa (densità a nucleo) · raggio · «chiama i canili»
provata contro gli anelli (C) e sui ritrovamenti veri (D): ogni ritrovamento corregge
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
(valori estremi), `lifelines` (sopravvivenza), `osmnx` (OpenStreetMap). R: `ctmm`,
`moveHMM` (ecologia del movimento).
