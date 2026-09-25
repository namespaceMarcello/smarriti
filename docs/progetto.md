# Il progetto

Cosa costruiamo e in che ordine. Le decisioni vive stanno in `STATO.md`; qui c'è la forma
del prodotto.

## Il problema

Quando un animale si perde, nessuno sa dire **dove conviene cercarlo adesso**: si gira a
caso. Gli studi dicono dove finiscono gli animali smarriti (quanto lontano, dopo quanto,
secondo il temperamento), ma nessuno li ha mai trasformati in una mappa per il singolo
caso.

## Cosa facciamo

Un **simulatore matematico**: dati l'animale, la casa, la zona e l'ora della perdita,
predice dove si trova adesso, con la più alta accuratezza possibile. Non riceve niente
dopo la perdita: né avvistamenti, né ricerche, né volantini. Solo matematica e dati degli
studi.

## Due stati

Un animale smarrito è in uno di due stati, e ogni ora che passa il secondo diventa più
probabile:

| Stato | Cosa conta | Cosa serve |
|---|---|---|
| **Libero** | si muove: contano i luoghi | la mappa: dove cercare |
| **In mano a qualcuno** | raccolto, portato dal veterinario o al canile: i luoghi non contano più | trovare quella persona: canili, veterinari, microchip |

Il cane ritrovato a 30 km non ci è arrivato con le sue zampe: ce l'ha portato chi l'ha
raccolto. Peso e taglia non prevedono niente; il temperamento e il tempo passato sì
(`riferimenti.md` §A).

## Il motore

Una simulazione Monte Carlo (`matematica.md`, `simulatore.md`):

1. Da casa partono migliaia di animali virtuali.
2. Ogni ora si muovono con regole per categoria: il gatto resta entro poche case e si
   nasconde; il cane pauroso scappa lontano; il cane socievole va verso le persone.
3. Il luogo cambia le regole: edifici e altezze, il piano di casa, giardini, muri, scale,
   strade, dislivelli, presi da dati aperti (il luogo in 3D).
4. Ogni ora una parte viene «raccolta» da qualcuno: più spesso dove c'è gente, più spesso
   con il collare.
5. Dove ne restano di più, la mappa è scura. La quota «raccolti» dice quando smettere di
   girare e cominciare a telefonare.

Tre uscite, non un numero:
- «Cerca qui, a quest'ora.»
- «Entro questo raggio c'è metà delle probabilità; entro quest'altro, nove su dieci.»
- «Da oggi conviene chiamare: canili e veterinari entro N km.»

Le regole vengono dagli studi e dai dati aperti: ogni numero ha la sua fonte, ogni
previsione si scrive prima di misurarla.

## Perché sta in piedi da solo

- Serve già al primo utente: la mappa aiuta anche se la usa una persona sola.
- Non dipende da nessuna piattaforma e da nessun dato che arrivi dopo.
- Il genoma sono gli studi: ricerche sparse (distanze, tempi, temperamento, movimento
  GPS, dati dei canili) lette insieme per la prima volta in un solo modello, ciascuna per
  il pezzo che misura.

## Ordine di costruzione

1. **Il simulatore**, provato contro i numeri pubblicati prima di qualsiasi utente.
2. **Il luogo in 3D, al metro**: edifici con le altezze, il piano, giardini, muri, tetti,
   scale, strade, dislivelli, misurati in automatico da dati aperti. Quanto lontano va
   l'animale lo dicono gli studi; dove, fra i posti possibili, lo dice il 3D. Le regole
   fini vengono dagli studi sul movimento dei gatti; le distanze restano quelle tarate.
3. **Il sito**: si inseriscono animale, casa, zona e ora; esce la mappa.

## La forma: un sito, non un'app

Niente da scaricare. Chi ha perso l'animale apre un link, inserisce i dati del caso e ha la
mappa. Deve funzionare sul telefono di chiunque, anche vecchio, e su un computer.

## TiTrovo

Sul Desktop esiste `IoTiTrovo` (repo `petsuite-mono`, app TiTrovo, maggio 2026). Resta
separata; si può guardare come riferimento per le query geografiche.
