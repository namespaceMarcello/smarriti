# Il progetto

Cosa costruiamo, in che ordine, e cosa abbiamo scartato. Le decisioni vive stanno in
`STATO.md`; qui c'è la forma del prodotto.

## Il problema

Quando un animale si perde, oggi succede questo: il proprietario scrive nei gruppi Facebook,
attacca volantini, gira a caso. Chi lo vede lo scrive in un altro gruppo, e i due post non
si incontrano. Nessuno sa dire **dove conviene cercare adesso**, e nessuno raccoglie i dati
dei ritrovamenti: dove era, dopo quanto, come è stato trovato.

## L'idea centrale: due stati

Un animale smarrito è in uno di due stati, e ogni ora che passa il secondo diventa più
probabile:

| Stato | Cosa conta | Cosa serve |
|---|---|---|
| **Libero** | si muove: contano i luoghi | la mappa: dove cercare, dove mettere volantini |
| **In mano a qualcuno** | raccolto, portato dal veterinario o al canile: i luoghi non contano più | trovare quella persona: canili, veterinari, microchip |

Il cane ritrovato a 30 km non ci è arrivato con le sue zampe: ce l'ha portato chi l'ha
raccolto. Peso e taglia non prevedono niente; il temperamento e il tempo passato sì
(vedi `riferimenti.md` §A).

## Il motore

Una simulazione (filtro particellare, `matematica.md`):

1. Da casa partono migliaia di animali virtuali.
2. Ogni ora si muovono con regole per categoria: il gatto resta entro poche case e si
   nasconde; il cane pauroso scappa lungo le strade lontano dal rumore; il cane socievole
   va verso le persone. Strade, fiumi e ferrovie vengono da OpenStreetMap.
3. Ogni ora una parte viene «raccolta» da qualcuno: più spesso in città, più spesso con
   il collare.
4. Ogni avvistamento vero elimina le particelle che non potevano essere lì (con un peso:
   un avvistamento non è una certezza).
5. Ogni ricerca fatta elimina una parte delle particelle nella zona: poche se in auto,
   molte se a piedi con la torcia. «Già cercato» non vuol dire «non c'è».
6. Dove ne restano di più, la mappa è scura. La quota «raccolti» dice quando smettere di
   girare e cominciare a telefonare.

Tre ordini in uscita, non un numero:
- «Cerca qui, a quest'ora.»
- «Manca un volantino qui.»
- «Da oggi conviene chiamare: ecco i canili e i veterinari entro N km, con il messaggio pronto.»

Le regole dei punti 2 e 3 all'inizio vengono dagli studi. Ogni ritrovamento vero le
corregge: dove diceva la simulazione contro dove era davvero.

## Il giro (come arrivano i dati)

Non leggiamo Facebook: lo usiamo come altoparlante. Ogni annuncio si porta dietro una
strada per tornare da noi.

1. Chi ha perso l'animale carica una foto: in 30 secondi ha il volantino da stampare e il
   testo del post, entrambi con un QR code e un link «L'hai visto? Tocca qui».
2. Li mette dove vuole: Facebook, WhatsApp, pali, veterinari. Nessun permesso di Meta.
3. Chi lo vede inquadra il QR o apre il link e tocca «visto qui», indicando **dove e
   quando l'ha visto** (non dove sta il volantino).
4. Chi cerca con il telefono in tasca lascia le strade già girate come «qui ho cercato».
5. Gli avvistamenti che arrivano per telefono li segna il proprietario a mano.

Tre tipi di punto sulla mappa:

| Punto | Da dove | Dice |
|---|---|---|
| 🔴 avvistamento | «visto qui» | «è passato di qui» — il dato più prezioso |
| ⚪ ricerca | il telefono di chi cerca | «qui ho cercato» (pesato per il metodo) |
| 🟡 volantino | dove è stato attaccato | quanta gente lo vede; ogni QR è diverso |

Ogni volantino ha un QR diverso: si sa quale porta avvistamenti e quale non lo guarda
nessuno.

## Perché sta in piedi da solo

- Serve già al primo utente: la mappa aiuta anche se la usa una persona sola.
- Nessuna piattaforma può chiuderci: Facebook, WhatsApp e la carta sono altoparlanti.
- Si diffonde da solo: ogni volantino in strada fa pubblicità al progetto.
- Il genoma lo costruiamo noi: ogni ritrovamento è un dato che oggi non raccoglie nessuno.
  Dopo cento casi è la prima banca dati del genere (per le persone esiste ISRID, per gli
  animali no).

## Ordine di costruzione

1. **Il simulatore**, provato contro i numeri pubblicati prima di qualsiasi utente.
2. Volantino con QR, pagina «visto qui», mappa.
3. Il resto, dopo: lettura degli screenshot dei post, riconoscimento del singolo animale
   dalla foto, censimento dei randagi.

## Scartato o rimandato

- Leggere i gruppi Facebook in automatico: l'API dei gruppi è chiusa dall'aprile 2024
  senza alternative; lo scraping viene bloccato. La Meta Content Library dà i post dei
  gruppi pubblici ma solo per ricerca e tramite un'università (`riferimenti.md` §B).
- Il manifesto «OpenPaw Vet» (sette moduli: cartella clinica, AI diagnostica, IPFS…): troppo
  per partire, e alcuni pezzi violerebbero la privacy o esistono già (ASM3, elencocras.it).
  Restano i principi: gratis, aperto, funziona anche senza rete.
- L'app «post che si incontrano» (collegare «ho perso» con «ho visto»): è la parte
  intuitiva che altri hanno già tentato. La mappa è l'invenzione; il collegamento dei post
  è un ingresso in più, dopo.

## La forma: un sito, non un'app

Niente da scaricare. Chi ha perso l'animale apre un link; chi lo vede inquadra il QR del
volantino e si apre una pagina con un gesto solo: «Dove l'hai visto?». Deve funzionare sul
telefono di chiunque, anche vecchio, e su un computer. Uno store in mezzo è un ostacolo
inutile.

## TiTrovo

Sul Desktop esiste già `IoTiTrovo` (repo `petsuite-mono`, app TiTrovo, maggio 2026): app
mobile per animali smarriti con volantino PDF, QR sul collare, avvistamenti su mappa,
backend Supabase vivo. Resta separata: era nata come app, qui si è scelto qualcosa di più
semplice. Si può guardare come riferimento (generazione del volantino, query geografiche).
