# Prompt per la prossima sessione

Scritto il 2026-09-26, dopo il commit di A5 e della decisione «niente casi raccolti da
noi». Si sostituisce a fine sessione.

---

Costruisci il primo prototipo del **luogo in 3D** e mostra a Marcello 3 varianti di mappa
**prima** di toccare il motore.

Leggi, in quest'ordine: `CLAUDE.md`, `docs/STATO.md` (le decisioni «Il luogo in 3D, al
metro» e «Niente casi raccolti da noi»), `docs/progetto.md` (tappa 2), `docs/simulatore.md`
(§ L'ambiente: la zona, § Movimento, § Come si tara), `docs/riferimenti.md` §A (Zhang 2022,
Xia & Zhao 2024, Bischof 2022) e §B (OpenStreetMap, GlobalBuildingAtlas, LiDAR del
Ministero), `docs/lessons.md` #20, e `privato/luogo-prova.md` (il luogo di prova: un
indirizzo vero di Napoli, fuori da git; **mai** nei documenti, nei test, nei commit).

Il perimetro, deciso da Marcello (non si ridiscute): dentro, la forma vera del luogo della
fuga (edifici con le altezze, il piano, giardini, muri, tetti, scale, strade, dislivelli),
misurata in automatico da dati aperti, che decide dove l'animale può andare e nascondersi;
fuori, studiare i posti uno per uno e qualsiasi informazione dopo la perdita. Niente casi
raccolti da noi: la risposta viene da matematica, studi pubblicati e dati aperti.

Stato: A5 fatta (gatti a rischi in competizione; B2 passa; C2 regge a 0,39 · 0,42 degli
anelli). `pytest -q`: 68 passati, 1 lento saltato, 4 `xfail` stretti in ~40 s
(`--runslow` per il lento). Oggi la mappa è a cerchi: la direzione la può dare solo il 3D.
Sul luogo di prova OpenStreetMap ha 478 edifici e **nessuna** altezza
(`privato/osm-luogo-prova.json`, già scaricato).

Il lavoro:
1. **Dati**, tutti aperti, per ~500 m attorno al luogo di prova, salvati in `privato/`:
   altezze da GlobalBuildingAtlas (prima la licenza: il progetto è AGPL; leggi solo il
   riquadro, per esempio GeoParquet su source.coop, non la piastrella da 5°); terreno da
   Tinitaly 10 m (INGV) o Copernicus DEM 30 m; verde da ESA WorldCover 10 m. Il LiDAR del
   Ministero (1 m) si chiede per email: prepara il testo per Marcello (area, uso, prodotto:
   DTM e DSM) con i passi per mandarla. Ogni dataset in `riferimenti.md` §B con la fonte,
   senza l'indirizzo.
2. **Studi per le regole fini**: cerca gli studi GPS su come i gatti usano l'ambiente
   (riparo, vegetazione, edifici, strade: funzioni di selezione dell'habitat) e prendi i
   numeri alla fonte, in `riferimenti.md` §A. Una regola senza studio resta una stima
   dichiarata in `simulatore.md`.
3. **Progetto prima del codice**, in `docs/simulatore.md` § L'ambiente: «quanto lontano
   dagli studi, dove dal 3D». L'ancora (il nascondiglio) si sceglie fra i posti veri con
   peso = densità della distanza tarata × qualità del riparo × raggiungibilità (salti dal
   piano, muri, strade larghe), normalizzata in modo che la distribuzione delle distanze
   resti quella di A5: cambia solo la direzione. Come si prova senza casi: A e B reggono
   ancora; C1 regge; le quote di tempo per tipo di posto tornano con gli studi GPS.
4. **Varianti**, per un gatto di casa scappato dal primo piano, a 24 ore: (1) oggi, a
   cerchi; (2) con edifici e giardini; (3) con anche i dislivelli. PNG numerati affiancati in
   `privato/` (mostrano il luogo vero), mandati a Marcello con `SendUserFile`. **Fermati e
   aspetta la sua scelta** prima di portarla nel motore.
5. Prima di ogni misura, la previsione in `docs/MISURE.md`.

Regole: ogni errore e ogni cosa che fallisce va subito in `docs/lessons.md` (cosa, perché,
regola, controllo); anche una previsione sbagliata. Test sotto i ~40 s (quelli che chiedono
troppi campioni diventano `slow`); ogni test statistico guarda l'intervallo a 4 errori
standard, mai un valore puntuale (#28). Dopo ogni modifica al motore si rifà la taratura.
Se esiste `~/.claude/macchina-ferma`, un'altra finestra misura tempi: i comandi pesanti
partono a priorità bassa. Agenti mai Fable; lavora tu, al massimo un Sonnet per una lettura
grossa, dicendo perché. Niente commit né push finché non li chiede Marcello. Prima di un
commit i documenti: `docs/archivio/FATTO.md`, `docs/STATO.md`, `docs/simulatore.md`,
`CLAUDE.md` se cambiano i comandi.

Aspettano Marcello: il nome del progetto e, se il LiDAR serve, l'email al Ministero.

A fine lavoro: resoconto in due punti (cosa è stato implementato, come lo provo) e il
prompt per la sessione dopo in `build/prompt-next.md`.
