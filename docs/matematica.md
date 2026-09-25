# La matematica

I concetti che usiamo, cosa danno, e da dove vengono. Nessuno è inventato da noi: sono
validati per persone disperse, aerei caduti e animali selvatici. Le fonti complete stanno in
`riferimenti.md` §C.

## I concetti

| Concetto | Cosa ci dà | Fonte |
|---|---|---|
| **Filtro particellare** (ricerca bayesiana di un bersaglio mobile) | Le migliaia di animali virtuali hanno un nome e quarant'anni di teoria dietro. È il metodo della Guardia Costiera USA (SAROPS) | Stone 2021 |
| **Teoria della ricerca** (Koopman, Stone) | Ogni ricerca ha una probabilità di scoperta (POD) tabellata: a piedi, in auto, di notte. Formula per decidere dove conviene cercare per primo: probabilità di area × POD | Koopman 1946; Frost & Stone 2001 |
| **Lost Person Behavior** (Koester, ISRID) | Il modello da copiare: 41 categorie di dispersi, per ognuna «il 50% entro X, il 95% entro Y». Noi lo facciamo con le categorie di animali | Koester 2008; Sava 2015 |
| **Simulazione dei dispersi sul terreno** | La nostra idea già fatta per le persone e verificata sui casi reali: particelle che si muovono secondo pendenza, vegetazione, sentieri | Lin & Goodrich 2010; Hashimoto 2022 |
| **Ecologia del movimento** | Come si muove la particella ora per ora: passeggiate casuali con pause, code «grasse» (i salti lunghi rari) | Tilles 2016; Patterson 2017 |
| **Profilazione geografica** (Rossmo) | Da più avvistamenti si ricava la **tana**. Nato per i serial killer, ha trovato gli alberi-dormitorio dei tarsi cercando nel 5% dell'area. Per gatti e cani paurosi che si sistemano in un nascondiglio | Le Comber 2006; Rossmo |
| **Valori estremi** (Gumbel) | Dalla coda delle distanze: quando allargare il raggio e chiamare i canili lontani. In Python `scipy.stats.genextreme` | — |
| **Analisi di sopravvivenza** | La curva «probabilità di ritrovarlo dopo N giorni», separata per stato: libero, raccolto, morto | Huang 2018 la dà per i gatti |
| **Affidabilità dei testimoni** | Un avvistamento ha un peso, non è verità: gli avvistamenti falsi non uccidono tutte le particelle | Stone 2014 (AF447) |
| **Cattura-ricattura** (Lincoln-Petersen) | Da due liste che si sovrappongono (gruppi Facebook, ingressi in canile) si stima quanti smarriti non segnala nessuno | — |

## Come si incastrano

```
categorie (Koester → animali)
   → movimento (ecologia)
   → simulazione (filtro particellare)
   → aggiornata da avvistamenti (testimoni) e ricerche (POD)
   → uscite: mappa · tana (Rossmo) · raggio (valori estremi) · «chiama i canili» (sopravvivenza)
ogni ritrovamento corregge categorie e code
cattura-ricattura misura quanto non vediamo
```

## Cosa non è vago

- Peso e taglia non prevedono la distanza; il **temperamento** e il **tempo** sì
  (`riferimenti.md`: Albrecht; Huang 2018; Kremer 2021).
- «Già cercato» non azzera la zona: si moltiplica per (1 − POD) del metodo usato.
- Il cane a 30 km è la **coda** della distribuzione, oppure è stato trasportato: due
  spiegazioni diverse, due stati diversi nel modello.

## Da provare per primo

Il simulatore contro i numeri pubblicati, con la previsione scritta prima:
- gatti: 75% entro 500 m, mediana 50 m; da appartamento 39 m in media (Huang 2018);
- cani: 70% entro 1,6 km, 42% entro 120 m (Kremer 2021, Dallas);
- tempi: un terzo dei gatti in 7 giorni, metà in 30 (Huang 2018); oltre il 90% dei cani
  riuniti entro 5 giorni (Kremer 2021).

Se le particelle non finiscono lì, le regole sono sbagliate e si corregge prima di
scrivere qualsiasi interfaccia.

## Strumenti pronti

Python: `filterpy` / `particles` (filtro particellare), `scipy.stats` (valori estremi),
`lifelines` (sopravvivenza), `osmnx` (rete stradale da OpenStreetMap).
R: `ctmm`, `moveHMM` (ecologia del movimento). Da scegliere in `STATO.md`.
