# Stato

Le decisioni vive, i problemi aperti, i prossimi passi. Si sostituisce, non si appende:
un passo fatto si cancella (e va in `archivio/FATTO.md`), una decisione superata si corregge.

## Decisioni

| Data | Decisione | Perché |
|---|---|---|
| 2026-09-26 | **Il luogo in 3D è nel motore, variante 2** (edifici e giardini, senza altezze; le altezze restano un'opzione del caso). Un gatto resta più a lungo dove gli piace stare (selezione nel passo, Hanmer) e un passo che finisce dentro un edificio si rilancia | Marcello, su consiglio: la 3 oggi cambia il 5% (nessun tetto a portata di salto) e aggiunge regole senza studio; L2-L3 in `MISURE.md` |
| 2026-09-26 | **Il luogo al metro senza richieste**: niente email, moduli firmati o pagamenti per avere dati. Si leggono e si incrociano le fonti aperte che si scaricano da sole (altezza della chioma a 1 m da satellite, siepi, database topografici con muri e gronde, i servizi di mappe pubblici), come letture di un genoma: tante letture corte e rumorose, allineate, al posto di una lettura lunga da chiedere | Marcello; `lessons.md` #37 |
| 2026-09-26 | Le altezze degli edifici da **3D-GloBFP** (CC BY 4.0), non da GlobalBuildingAtlas (CC BY-NC 4.0); il terreno da TINITALY (CC BY 4.0), il verde da WorldCover (CC BY 4.0). Dal computer esce solo un riquadro arrotondato a 0,01°; il punto della casa si trova in locale nell'ANNCSU | un progetto AGPL non usa dati «non commerciali» (`lessons.md` #32); l'indirizzo non esce |
| 2026-09-26 | **Niente casi raccolti da noi.** La risposta viene da matematica, studi pubblicati e dati aperti (Dallas, Austin, OpenStreetMap, rilievi). Le regole fini del 3D si prendono dagli studi sul movimento dei gatti (GPS, uso dell'habitat) o restano stime dichiarate; si provano con i controlli che non chiedono casi: le distanze restano quelle degli studi (A, B), la mappa resta calibrata (C1) e batte gli anelli (C2) | Marcello: con la matematica e gli studi si può dare la risposta |
| 2026-09-25 | **Il luogo in 3D, al metro.** Dentro: la forma vera del luogo della fuga (edifici con le altezze, il piano da cui scappa, giardini, muri, tetti, scale, strade, dislivelli), misurata in automatico da un modello 3D, che decide dove l'animale può andare e nascondersi. Fuori: studiare i posti uno per uno, e qualsiasi informazione che arrivi dopo la perdita. **Quanto lontano** lo dicono gli studi (tarato), **dove fra i posti possibili** lo dice il 3D. Dati aperti, non Google (condizioni d'uso, costo, dipendenza di un progetto open source) | Marcello: un gatto che scappa da un primo piano accanto alle villette (Napoli, collina) non è quello di un appartamento; il gatto di casa sta a 39 m di mediana (Huang) e la mappa ha celle da 50 m |
| 2026-09-25 | La taratura dei gatti tiene conto del padrone che cerca (un rischio uguale a ogni distanza), **solo** per leggere Huang: il 69% dei trovati vivi è stato trovato fuori da chi cercava. Il simulatore non ha ricerche né in ingresso né in uscita | senza, `h_home` esce sbagliato: un gatto trovato il giorno 3 non torna da solo il giorno 10 |
| 2026-09-25 | **Il progetto è un simulatore solo matematico** che predice dove si trova l'animale, con la più alta accuratezza possibile. Dopo la perdita non riceve niente: né avvistamenti, né ricerche, né volantini. Escono con loro il QR, la pagina «visto qui», la lettura dei post e le idee che ne dipendevano (riconoscimento del singolo animale, censimento dei randagi) | Marcello |
| 2026-09-25 | La **zona** (centro, palazzi, villette, campagna, parco; piano di casa) entra come ambiente per cella: in v0 dichiarata nel caso con toppe circolari, da v0.1 da OpenStreetMap, stesso motore | Marcello: le variabili della zona fanno l'indice di dove può essere; è anche l'unica cosa che rompe la simmetria attorno a casa (C2) |
| 2026-09-25 | Si parte dal simulatore, provato contro i numeri pubblicati, prima di ogni interfaccia | misurare prima di credere |
| 2026-09-25 | Strada per la fase C: mappa lisciata con la densità a nucleo adattiva, poi dati veri di ritrovamento, poi la zona da OpenStreetMap. La mappa lisciata ha superato C2 (0,44 · 0,42 degli anelli) | Marcello, strada consigliata |
| 2026-09-25 | All'ora «adesso» lo stato HOME è escluso (chi chiede lo saprebbe); al suo posto P(torna da solo entro 7 giorni) | un «tornato a casa» sarebbe un numero senza senso per chi cerca |
| 2026-09-25 | Ogni errore e ogni fallimento va in `docs/lessons.md`, con la regola e il controllo che ne escono | Marcello: imparare man mano dai propri errori |
| 2026-09-25 | Test in tre famiglie (integrità, pressione, ipotesi), veloci (~30 s); un test statistico passa solo se l'intervallo a 4 errori standard sta nella tolleranza; i fallimenti noti sono `xfail` stretti | Marcello: test rigorosi, veloci, dati attendibili |
| 2026-09-25 | Ordine: simulatore → mappa della zona da OpenStreetMap → sito (si inserisce il caso, esce la mappa) | |
| 2026-09-25 | **Non è un'app.** È un sito che si apre da un link: niente store, niente installazione | alla portata di tutti |
| 2026-09-25 | TiTrovo (`IoTiTrovo`) resta separata: solo riferimento | Marcello |
| 2026-09-25 | Repo **pubblico** su GitHub (`namespaceMarcello/smarriti`); README in inglese, documenti in italiano | Marcello |
| 2026-09-25 | Licenza **AGPL-3.0** | i miglioramenti restano in comune; cambiabile finché non c'è un contributore esterno |
| 2026-09-25 | Cartella e repo provvisori `smarriti`; nome da scegliere (`gh repo rename` quando c'è) | |

## Problemi aperti

- **Come si legge C2**: la mediana degli anelli è un gradino (`lessons.md` #26). Con misure
  senza gradini il simulatore vince in tutte le categorie (media geometrica del rapporto
  0,55, meno area sul 67% delle verità; A5), pari sulla media aritmetica (le verità
  lontanissime); `sim.baseline` le stampa. In una zona uniforme la mappa è radiale: la
  direzione la può dare solo il luogo in 3D.
- **PNG della mappa**: lisciata, colora tutto il rettangolo (fino a ±25 km per il cane
  pauroso). Ritagliarla alla regione del 99% è lavoro visivo: varianti prima.
- **Gatto libero** a 0,28 dai bersagli (A5; era 0,23): il p25 è 18 m contro 14. Idea non
  provata: `pull` e `p_move` liberi nella griglia.
- **B1, p25 dei gatti mescolati** al limite dopo A5: 10,5-11,0 m contro 9 (limite 10,8),
  non dimostrabile a 4 errori standard; la mediana resta fuori (72 contro 50). Causa del
  p25 salito non misurata (`lessons.md` #29).
- **Cani**: raccolti entro 5 giorni 0,82 contro > 0,90 (B3); da verificare se i 5 giorni di
  Kremer si contano dalla perdita o dall'ingresso in canile.
- Moltiplicatori di zona e del piano: stime senza fonte, da tarare sui casi. Con il luogo
  in 3D li sostituisce la geometria; ogni regola fine viene da uno studio o resta una stima
  dichiarata.
- **Il luogo in 3D, cosa resta** (L3 in `MISURE.md`): la vegetazione di Huang (sotto i
  cespugli il 16% dei trovati) a 10 m non si vede, i gatti in `veg` sono 0,04 contro 0,25; le
  strade escono un po' alte (0,21 contro 0,10 di Huang); il rilancio del passo mette un po'
  meno gatti dove è fitto (0,91 della disponibilità a ridosso dei muri); il quadrato di
  ±600 m tiene il 90% della massa a 24 ore (`map_share_in_place`), meno nei giorni dopo.
- **Giardini privati**: WorldCover a 10 m non li vede (finiscono nel «costruito»); OSM ne ha
  quasi nessuno. Li vedono il LiDAR a 1 m (DSM − DTM) e le siepi a 5 m di Copernicus.
- **Regole senza studio** (stime dichiarate in `simulatore.md`): attraversare le strade,
  salto in su, salita e discesa, riparo sotto le auto contro i bordi degli edifici.
- **Luogo di prova**: un indirizzo vero di Napoli dato da Marcello, in `privato/` (fuori da
  git), con il punto del portone trovato nell'ANNCSU. Mai nei documenti né nei test.
- **Il luogo al metro dalle fonti aperte** (`riferimenti.md` §B, 2026-09-26): il LiDAR a 1 m
  della Città Metropolitana di Napoli (terreno e superficie, del 2009, CC BY-SA 4.0) si
  scarica senza richieste; le siepi a 5 m da Copernicus; muri e gronde in vettoriale non
  trovati aperti (Regione e Comune): restano OSM e l'altezza DSM − DTM.
- Profilo orario dei gatti: Zhang 2022 dà picchi 6-10 e 17-21 (non «tutta la notte»).
- **Nome del progetto.**
- **Stack del sito**: da scegliere quando il simulatore regge.

## Prossimi passi

1. **Il luogo al metro**: in `proto/luogo3d/fetch.py` le tessere LiDAR a 1 m della Città
   Metropolitana (DTM e DSM) e le siepi a 5 m di Copernicus; in `world.py` terreno a 1-2 m,
   altezza sopra il suolo (DSM − DTM), un tipo di posto «sotto la vegetazione» (cespugli,
   siepi). Previsioni prima: quanto sale `veg` verso lo 0,25 di Huang, quanto si stringe la
   mappa, quanti tetti, muri e terrazzamenti diventano raggiungibili (se tanti, le altezze:
   variante 3).
2. Scaricare Dallas e Austin: posizioni di raccolta, tempi di rientro, quota «raccolti»;
   se ci sono punto di raccolta e indirizzo del proprietario, un banco di prova con dati
   pubblicati per misurare se il luogo (strade, edifici) migliora la mappa dei cani.
3. Il sito.
4. Leggere Huang 2018 e Lord 2007 alla fonte: tabelle complete.
5. Scegliere il nome.
