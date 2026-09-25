# Stato

Le decisioni vive, i problemi aperti, i prossimi passi. Si sostituisce, non si appende:
un passo fatto si cancella (e va in `archivio/FATTO.md`), una decisione superata si corregge.

## Decisioni

| Data | Decisione | Perché |
|---|---|---|
| 2026-09-25 | Il cuore è il **motore** (simulazione + dati), non un'altra app di annunci | è l'unica cosa che non esiste; serve al primo utente da solo |
| 2026-09-25 | Si parte dal simulatore, provato contro i numeri pubblicati, prima di ogni interfaccia | misurare prima di credere |
| 2026-09-25 | Facebook e i social sono altoparlanti, non fonti: i post li portano le persone (QR, link, screenshot) | API dei gruppi chiusa; scraping bloccato |
| 2026-09-25 | Volantino con QR diverso per ogni copia; «visto qui» chiede dove e quando è stato visto, non dove sta il volantino | la scansione dice dov'è il volantino, non l'animale |
| 2026-09-25 | Ordine: simulatore → volantino+QR+mappa → screenshot dei post → riconoscimento del singolo animale → censimento randagi | |
| 2026-09-25 | **Non è un'app.** È un sito che si apre da un link o dal QR del volantino: niente store, niente installazione | deve essere alla portata di tutti; TiTrovo era nata come app e qui si è scelto qualcosa di più semplice |
| 2026-09-25 | TiTrovo (`IoTiTrovo`) resta separata: non è un cliente né una base di questo progetto. Si può guardare come riferimento (volantino PDF, query geografiche) | Marcello, stesso giorno |
| 2026-09-25 | Repo **pubblico** su GitHub (`namespaceMarcello/smarriti`) dal primo giorno; README in inglese, documenti in italiano finché non arrivano contributori | Marcello, stesso giorno |
| 2026-09-25 | Licenza **AGPL-3.0** | la scelta del manifesto di Marcello: i miglioramenti restano in comune. Cambiabile finché non c'è un contributore esterno |
| 2026-09-25 | Cartella e repo provvisori `smarriti`; nome del progetto da scegliere (`gh repo rename` quando c'è) | |

## Problemi aperti

- **Nome del progetto.**
- **Stack del sito** (il simulatore è deciso: Python, `simulatore.md`): da scegliere
  quando il simulatore regge.
- **Meta Content Library.** Servirebbe un'università o un ente di ricerca come partner per
  leggere i gruppi pubblici (solo per la misura). Nessun contatto ancora.
- **Casi reali.** Servono 5 casi veri a Napoli per la prima prova sul campo; li trova
  Marcello.

## Prossimi passi

1. Costruire il simulatore v0 come descritto in `simulatore.md` (progetto completo:
   modello, parametri, prove, fasi A-D, struttura, «quando è finito»). Le previsioni
   in `MISURE.md` **prima** di ogni misura.
2. Scaricare Austin e Dallas: tempi di rientro e quota «raccolti» reali.
3. Leggere Huang 2018 e Lord 2007 alla fonte: tabelle complete, non le sintesi.
4. Scegliere il nome.
