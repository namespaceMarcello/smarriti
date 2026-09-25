# Stato

Le decisioni vive, i problemi aperti, i prossimi passi. Si sostituisce, non si appende:
un passo fatto si cancella (e va in `archivio/FATTO.md`), una decisione superata si corregge.

## Decisioni

| Data | Decisione | Perché |
|---|---|---|
| 2026-09-25 | **Il progetto è un simulatore solo matematico** che predice dove si trova l'animale, con la più alta accuratezza possibile. Dopo la perdita non riceve niente: né avvistamenti, né ricerche, né volantini. Escono con loro il QR, la pagina «visto qui», la lettura dei post e le idee che ne dipendevano (riconoscimento del singolo animale, censimento dei randagi) | Marcello |
| 2026-09-25 | La **zona** (centro, palazzi, villette, campagna, parco; piano di casa) entra come ambiente per cella: in v0 dichiarata nel caso con toppe circolari, da v0.1 da OpenStreetMap, stesso motore | Marcello: le variabili della zona fanno l'indice di dove può essere; è anche l'unica cosa che rompe la simmetria attorno a casa (C2) |
| 2026-09-25 | Si parte dal simulatore, provato contro i numeri pubblicati, prima di ogni interfaccia | misurare prima di credere |
| 2026-09-25 | All'ora «adesso» lo stato HOME è escluso (chi chiede lo saprebbe); al suo posto P(torna da solo entro 7 giorni) | un «tornato a casa» sarebbe un numero senza senso per chi cerca |
| 2026-09-25 | Ogni errore e ogni fallimento va in `docs/lessons.md`, con la regola e il controllo che ne escono | Marcello: imparare man mano dai propri errori |
| 2026-09-25 | Test in tre famiglie (integrità, pressione, ipotesi), veloci (~30 s); un test statistico passa solo se l'intervallo a 4 errori standard sta nella tolleranza; i fallimenti noti sono `xfail` stretti | Marcello: test rigorosi, veloci, dati attendibili |
| 2026-09-25 | Ordine: simulatore → mappa della zona da OpenStreetMap → sito (si inserisce il caso, esce la mappa) | |
| 2026-09-25 | **Non è un'app.** È un sito che si apre da un link: niente store, niente installazione | alla portata di tutti |
| 2026-09-25 | TiTrovo (`IoTiTrovo`) resta separata: solo riferimento | Marcello |
| 2026-09-25 | Repo **pubblico** su GitHub (`namespaceMarcello/smarriti`); README in inglese, documenti in italiano | Marcello |
| 2026-09-25 | Licenza **AGPL-3.0** | i miglioramenti restano in comune; cambiabile finché non c'è un contributore esterno |
| 2026-09-25 | Cartella e repo provvisori `smarriti`; nome da scegliere (`gh repo rename` quando c'è) | |

## Da decidere con Marcello (subito)

**Fase C non superata** (`MISURE.md`, C2, senza prove): il simulatore perde contro gli
anelli, 45 volte sulla mediana dell'area da cercare. Vince dove la mappa è fitta (gatto da
appartamento: 0,28, cioè un quarto dell'area) e perde dove l'istogramma di particelle è
rado (cani diffidente e pauroso, gatto libero). Due fatti misurati:
- lo **stimatore della mappa** è il difetto: C1 mostra che l'istogramma non è una
  probabilità calibrata dove le particelle si spargono;
- in una zona uniforme il simulatore è **radiale come gli anelli**: può batterli in
  distanza (una densità più fedele di quattro anelli uniformi), in direzione solo con la
  **mappa della zona**.

Strada consigliata, in quest'ordine: (1) mappa lisciata con la densità a nucleo adattiva,
poi C1 e C2 ripetute (poche ore di lavoro, misura in un minuto); (2) dati veri di
ritrovamento con la posizione (Dallas: punto di raccolta e indirizzo del proprietario, se
i campi ci sono) per avere un banco di prova reale; (3) la zona da OpenStreetMap, provata
su quei dati contro gli anelli. L'alternativa è fermarsi agli anelli ben stimati per
categoria e zona (più semplice, niente direzione).

## Problemi aperti

- **Rischi dei gatti 4-5 volte troppo alti** (B2, `lessons.md` #8): la taratura legge le
  particelle a un'ora esterna. Correzione: rischi in competizione sulla curva di Huang e
  sulle quote dei luoghi insieme.
- **Gatto libero** a 0,23 dai bersagli (A3, A4). Idea non provata: `pull` e `p_move` liberi.
- **Cani**: raccolti entro 5 giorni 0,82 contro > 0,90 (B3); da verificare se i 5 giorni di
  Kremer si contano dalla perdita o dall'ingresso in canile.
- Moltiplicatori di zona e del piano: stime senza fonte, da tarare sui casi.
- Profilo orario dei gatti: Zhang 2022 dà picchi 6-10 e 17-21 (non «tutta la notte»).
- **Nome del progetto.**
- **Stack del sito**: da scegliere quando il simulatore regge.
- **Casi reali**: 5 casi veri a Napoli per la fase D (animale, casa, zona, ora della
  perdita; alla chiusura punto e ora del ritrovamento); li trova Marcello.

## Prossimi passi

1. Marcello sceglie la strada per C (sopra).
2. Con la strada consigliata: mappa lisciata, poi C1 e C2 ripetute.
3. Rischi dei gatti in competizione; poi A e B rifatti.
4. Scaricare Dallas e Austin: posizioni di raccolta, tempi di rientro, quota «raccolti».
5. Leggere Huang 2018 e Lord 2007 alla fonte: tabelle complete.
6. Scegliere il nome.
