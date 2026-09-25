<!-- preferenze: 83d8c143 -->
# Smarriti (nome provvisorio)

Motore open source che dice a chi ha perso un animale **dove cercarlo adesso**: una
simulazione di migliaia di animali virtuali, aggiornata da avvistamenti, ricerche già fatte
e volantini, tarata sui casi reali. **Non è un'app**: un sito che si apre da un link o dal
QR del volantino. Nato il 2026-09-25; non c'è ancora codice.

**Lo spirito: leggere il problema come un genoma** (Marcello). Ogni avvistamento, ogni
strada già girata, ogni ritrovamento è un dato da sequenziare, dove gli altri lo buttano.
Misurare prima di credere; scrivere la previsione prima di misurare; inventare la prossima
idea dai numeri. Una premessa che dà zero è una scoperta: si scrive, si chiude, avanti.

Stack: simulatore in Python 3.12 (`numpy`, `scipy`, `matplotlib`, `pytest`; `osmnx` dalla
v0.1), codice e commenti in inglese. Il sito: da decidere (`docs/STATO.md`).

---

## Come lavorare

- A ogni avvio di sessione, senza che sia chiesto: leggi `build/prompt-next.md` (il compito
  lasciato per questa sessione: fallo), poi `docs/STATO.md`.
- A fine lavoro, senza che sia chiesto: scrivi il prompt della sessione dopo in
  `build/prompt-next.md` (cosa leggere, lo stato, il compito, come misurarlo, come
  riferire), così Marcello può fare `/clear` e ripartire.
- Marcello non tocca il codice: dirige e decide, Claude costruisce tutto. Quando serve
  un'azione sua (browser, telefono, persone da contattare), istruzioni passo per passo.
- Agenti: **mai Fable**. Haiku per il lavoro meccanico e verificabile, Sonnet per un lotto
  di dati su brief chiuso o un refactor delimitato, Opus per progettazione, debug oscuro e
  tutto ciò che tocca un'invariante. In parallelo solo su file disgiunti, con un brief
  scritto prima.
- **Fra agenti si parla inglese**, prompt e resoconti, anche quando Marcello scrive in
  italiano. Con Marcello si parla italiano.
- Il brief è conciso, semplice, dritto al punto — e completo: obiettivo, vincoli, file da
  toccare, forma della risposta, quando è finito. Nessun dettaglio che serve a fare il
  lavoro resta fuori; fuori invece il contesto incollato, la storia della sessione, i
  preamboli e le ripetizioni.
- Il resoconto dell'agente segue la stessa regola, in inglese: cosa ha fatto, file
  toccati, cosa resta aperto.
- Resoconto a Marcello in due punti: cosa è stato implementato, e come provarlo. Il perché
  delle decisioni e il racconto vanno in `docs/STATO.md` o `docs/archivio/FATTO.md`.
- Le domande si fanno prima di iniziare, non a metà.
- Lavoro visivo (UI, mappa, volantino): più varianti come PNG o GIF numerati, si aspetta
  la scelta, poi si implementa. Per logica, modello e bugfix: scegli, costruisci, consegna.

### Prima di ogni commit: documentare

| Se è cambiato… | Scrivi in… |
|---|---|
| una decisione, un problema aperto, un prossimo passo | `docs/STATO.md` — sostituisci la riga vecchia, non appendere; tetto 40 KB |
| un pezzo di lavoro finito | `docs/archivio/FATTO.md` — 2-5 righe: cosa, come si prova |
| un numero preso da uno studio, un dataset trovato | `docs/riferimenti.md` — con la fonte accanto |
| una previsione o una misura del modello | `docs/MISURE.md` — la previsione **prima** di lanciare, il risultato dopo, anche se negativo |
| un parametro, una regola o un'uscita del simulatore | `docs/simulatore.md` — si corregge la riga, non si appende |
| un concetto matematico usato, provato o scartato | `docs/matematica.md` |
| il prodotto: cosa fa, il giro, cosa non facciamo | `docs/progetto.md` |
| un documento nuovo in `docs/` | la tabella «Leggi prima di rispondere» qui sotto |

---

## Leggi prima di rispondere

| Domanda su… | Apri |
|---|---|
| cosa costruiamo, il giro volantino → QR → mappa, i due stati dell'animale, cosa non facciamo | `docs/progetto.md` |
| numeri sugli animali smarriti (distanze, giorni, percentuali), dataset aperti, cosa manca | `docs/riferimenti.md` §A, §B, §C |
| filtro particellare, teoria della ricerca, profilazione geografica, valori estremi, come si incastrano | `docs/matematica.md` |
| **come si costruisce il simulatore**: stati, movimento, categorie e parametri iniziali, prove, POD, uscite, fasi di verifica, struttura dei file, quando è finito | `docs/simulatore.md` |
| previsioni e misure fatte, in ordine | `docs/MISURE.md` |
| decisioni prese, problemi aperti, prossimi passi | `docs/STATO.md` |
| cosa è già stato fatto | `docs/archivio/FATTO.md` |
| TiTrovo, l'app già costruita (volantino PDF, QR sul collare, avvistamenti, Supabase) | `C:\Users\marce\Desktop\IoTiTrovo\CLAUDE.md` |

---

## Invarianti

- Ogni numero nei documenti ha la fonte accanto. Niente numeri a memoria.
- Prima di ogni misura si scrive la previsione; il risultato si registra anche se dà zero.
- Il modello si tara sui casi reali, non sulle opinioni: ogni ritrovamento è un dato.
- Facebook e gli altri social non si leggono in automatico: i post li portano le persone.
- I dati dei proprietari non sono mai pubblici; chi segnala un avvistamento resta anonimo.

---

## Manutenzione

Quando nasce un documento in `docs/`, aggiungi la sua riga alla tabella. Quello che è
successo va in `docs/STATO.md`, non qui.
