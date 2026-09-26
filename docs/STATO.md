# Stato

Le decisioni vive, i problemi aperti, i prossimi passi. Si sostituisce, non si appende:
un passo fatto si cancella (e va in `archivio/FATTO.md`), una decisione superata si corregge.

## Decisioni

| Data | Decisione | Perché |
|---|---|---|
| 2026-09-26 | **Prima il modello, poi il sito.** Nessun limite dato per scontato: un «limite» si scrive come il prossimo problema da attaccare; ogni idea, per quanto assurda, si prova prima di giudicarla; se la matematica che serve non c'è, si inventa | Marcello: «con i numeri, la matematica, tutto è possibile, anche al costo di inventare teoremi nuovi» |
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
- **Il luogo e i gatti veri: associazione sì, previsione quasi niente** (L7, L10b, L12, L13 in
  `MISURE.md`; 391 gatti di Stati Uniti, Australia e Nuova Zelanda, 46 del Regno Unito). L7 ha
  confermato un'associazione (le vere cadono dentro le impronte il 10% meno delle ruotate), ma
  come previsione la mappa del motore perde contro la radiale a ogni lisciatura (σ 10: −0,012;
  senza pavimento −∞, il 13,8% delle vere cade negli edifici, dove il motore dà zero): perdono lo
  zero dentro e i pesi di Hanmer. Il metro ora è S con l'errore del GPS dentro
  (`proto/gps/classes.py`). **Il paesaggio di OSM, per gatti residenti, dà al massimo 0,002-0,004
  nat per posizione**: il rapporto di selezione per fasce di distanza dagli edifici (dentro 0,91 ·
  0-3 m 1,02 · 3-6 1,07 · 6-12 1,11 · 12-24 1,02 · oltre 0,84) batte la radiale in tutti e quattro
  gli insiemi (fuori campione; +0,0028 ± 0,0039 nel Regno Unito), in nessuno da solo in modo
  significativo. Tipo e superficie degli edifici non cambiano niente. Il solo segnale più grande
  (+0,012) è la casa del gatto (le posizioni pendono verso l'edificio di casa) e nel Regno Unito
  non regge (−0,005): è il centro degli anelli, non il paesaggio. Lo 0,97 degli Stati Uniti viene
  per un terzo dalle impronte di Microsoft (1,11), il resto dai `yes` senza fonte. Dentro gli
  edifici le vere sono sparse su tutta l'impronta (profilo piatto entrando): non è l'errore di
  pochi metri a ridosso dei muri.
- **L'acqua** (L11): nel motore finiva in `open` (selezione 1,78), e in un caso vicino al mare o
  a un lago la mappa metteva gatti in acqua. Ora l'acqua di WorldCover (classe 80) non è un posto
  e fa da barriera, tranne sotto una strada (i ponti). I fiumi sotto i 10 m restano invisibili.
  Nei mondi dei gatti GPS l'acqua non c'è (`build_cats.py` non la disegna): L7 è per difetto,
  con l'acqua come muro D salirebbe di circa 0,03 negli Stati Uniti e in Nuova Zelanda
  (esplorativo, L10b).
- **I posti consigliati oltre il primo sono in parte rumore** (L11): sul caso privato il
  primo (casa, p 0,72) regge a ogni seme; degli altri quattro (p 0,01-0,03), cambiando solo il
  seme, uno non ha un corrispondente entro 85-121 m e un altro entro 45-49 m. Da misurare quanti
  gatti virtuali servono perché reggano, o da scegliere come zone invece che come celle.
- **Il GPS non vede come il gatto** (`riferimenti.md`, «Il GPS dei gatti»): sotto gli alberi
  il fix riesce (circa 100%, 2 m di errore in più), quindi la vegetazione evitata di Hanmer e
  di L6 è del gatto; a ridosso degli edifici si perde un fix su quattro e in casa quattro su
  cinque, quindi il bordo e l'edificio sotto 1 in L6 sono in parte del GPS. I ripari di Huang
  (garage e capanni 10%, sotto portico o veranda 10%, sotto casa 5%) il GPS non li vede, e nel
  motore gli edifici sono muri: un gatto nascosto in un capanno oggi non ha dove stare.
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
- **Il luogo al metro dalle fonti aperte** (`riferimenti.md` §B): il LiDAR a 1 m della Città
  Metropolitana di Napoli (2009, CC BY-SA 4.0) è nel mondo del luogo (`fetch.py ... lidar`,
  L8): il terreno a 1 m si scosta da TINITALY 2,6 m in mediana (quanto TINITALY dichiara);
  3D-GloBFP dà gli edifici 2,5 m più alti del LiDAR, per edificio e senza i bordi (L8b,
  correlazione 0,48): con le altezze, quelle del LiDAR. Le siepi a 5 m da Copernicus mancano
  ancora; muri e gronde in vettoriale non trovati aperti: restano OSM e DSM − DTM.
- Profilo orario dei gatti: Zhang 2022 dà picchi 6-10 e 17-21 (non «tutta la notte»).
- **Nome del progetto.**
- **Stack del sito**: da scegliere quando il simulatore regge.

## Prossimi passi

1. **Il gatto smarrito che si nasconde, senza cambiare le distanze** (L14). La regola è scritta
   e nel codice come opzione (`PlaceParams(preference="lost")`: fuori le fasce dei residenti di
   L13 al posto di Hanmer, dentro gli edifici diversi da casa il riparo di Huang, `hide` 3,58).
   Non è il motore perché con `hide` nella selezione nel passo il gatto fuori si muove 1,5-1,7
   volte di più (`sel_ref`) e il primo quartile delle distanze sale del 13-28% (xfail stretto in
   `test_place3d.py`); con le sole ancore, invece, il passo da 10-25 m riporta i gatti negli
   edifici quasi al caso (34% contro 33%). Da progettare, con una previsione scritta prima: il
   nascondersi come tempo passato fermo in un riparo che tenga le distanze di A5 (per esempio uno
   stato «nascosto» con l'entrata e l'uscita orarie, o una `sel_ref` presa dove i gatti sono ora e
   non sulle ancore); poi il motore con `lost`, l'impronta senza luogo identica, L2-L3 rifatti.
   Aperti di Huang: di chi sono casa, garage e capanno dei trovati «sotto casa» e «in garage»
   (con metà alla casa propria h scende a 2,5), e la casa del gatto in un condominio (la scala,
   la cantina, il cortile: oggi è un muro).
2. **Il centro del gatto** (L13): porta, cella più densa o edificio di casa? Nei tre paesi le
   posizioni fra 20 e 60 m pendono verso l'edificio di casa (coseno medio +0,2), nel Regno Unito
   no. Misurare quale centro rende le distanze più strette e le direzioni più uniformi, dove la
   definizione della casa cambia (righe nascoste o no, case singole o a schiera), prima di
   toccare il punto casa del motore.
3. **L'errore del GPS dai dati**: le righe nascoste dagli autori (circa il 90%) sono i periodi da
   fermo; la loro dispersione attorno alla mediana del periodo dà il nucleo dell'errore degli
   i-gotU sui gatti veri, in casa e fuori. Serve a leggere i rapporti dentro gli edifici (#56).
4. **Il luogo al metro, cosa resta** (il LiDAR a 1 m è nel mondo del luogo: `dtm1`, `dsm1`,
   `hmax1`, L8): le siepi a 5 m di Copernicus e un tipo di posto «sotto la vegetazione»
   (cespugli, siepi), dopo il passo 1 (che peso dare ai ripari di un gatto smarrito).
   La variante 3 con il LiDAR (9% dei tetti, un edificio su cinque entro 200 m a portata di
   salto) si accende solo con una prova che tetti e salti contino: sui gatti veri la
   raggiungibilità non porta segnale (L6). Dopo L9 un tetto raggiungibile pesa `sel` pieno,
   qualunque sia il giro per arrivarci: se la 3 si accende, questa regola va rivista.
5. Scaricare Dallas e Austin: posizioni di raccolta, tempi di rientro, quota «raccolti»;
   se ci sono punto di raccolta e indirizzo del proprietario, un banco di prova con dati
   pubblicati per misurare se il luogo (strade, edifici) migliora la mappa dei cani.
6. Il sito.
7. Leggere Lord 2007 alla fonte: tabelle complete.
8. Scegliere il nome.
