# Il simulatore

Progetto del prototipo v0, scritto il 2026-09-25 e corretto lo stesso giorno con il codice
in mano. I concetti stanno in `matematica.md`, i numeri con le fonti in `riferimenti.md`,
le previsioni e le misure in `MISURE.md`, gli errori in `lessons.md`.

## Cosa fa

Un simulatore **solo matematico**: dato un **caso** (animale, casa, zona, ora della
perdita) e un'ora «adesso», predice dove si trova l'animale, con la più alta accuratezza
possibile. Nessun ingresso esterno dopo la perdita. Produce:

1. la **mappa**: per ogni cella, la probabilità che l'animale sia lì, libero, adesso;
2. la probabilità di ogni **stato**: libero, raccolto da qualcuno, morto (tornato a casa è
   escluso: se fosse tornato chi chiede lo saprebbe) e la probabilità che **torni da solo
   entro 7 giorni**;
3. tre **consigli**: dove cercare adesso (e a che ora), in che raggio, se è ora di
   telefonare a canili e veterinari (e in quale raggio).

Niente interfaccia: una libreria Python con una riga di comando. Il sito arriva dopo e la
chiama.

## Il modello

### Particelle

N = 10.000 animali virtuali (parametro). Ognuna ha: posizione (x, y in metri, piano locale
centrato su casa), stato, direzione corrente, un'**ancora** (il nascondiglio scelto), il
peso. Passo temporale: **1 ora**. Orizzonte: fino a 90 giorni. Notte = dalle 20:00 alle
5:59.

Stati: `LOOSE` (libero), `HELD` (raccolto da una persona), `HOME` (tornato da solo),
`DEAD`. Gli ultimi tre sono assorbenti. Solo `LOOSE` ha una posizione che conta.

### Movimento (ogni ora, solo LOOSE)

Passeggiata casuale correlata con pause e attrazione verso l'ancora:

1. Con probabilità `p_move(categoria, giorno/notte) × stay(cella)` la particella si muove;
   altrimenti sta ferma.
2. Lunghezza del passo: lognormale con mediana `step × mobility(cella)` e dispersione
   `step_sigma`.
3. Direzione: von Mises attorno alla direzione precedente con concentrazione `kappa`.
4. Attrazione verso l'ancora, solo quando si muove: dopo il passo la posizione recupera una
   frazione `pull` della distanza dall'ancora (Ornstein-Uhlenbeck discreto).
5. Assestamento: dopo `t_settle` ore (esponenziale per particella) l'ancora diventa la
   posizione corrente e valgono i parametri «dopo» (passo, `kappa`, `pull`).
6. Ancora iniziale: `random` = a distanza lognormale da casa (mediana `anchor_med`,
   dispersione `anchor_sigma`) in direzione casuale; `home` = casa; `none` = nessuna finché
   non si assesta.

### L'ambiente: la zona

Ogni cella ha quattro moltiplicatori: `people` (sul rischio di essere raccolto), `traffic`
(sul rischio di morte), `stay` (su `p_move`: sotto 1 dove l'animale trova riparo e resta),
`mobility` (sul passo). Nel caso si dichiara la zona di casa, più toppe circolari
facoltative («qui c'è un parco»). Il luogo vero, da dati aperti, è il luogo in 3D (sotto),
per i casi che lo passano.

| Zona | people | traffic | stay | mobility |
|---|---|---|---|---|
| `suburban_houses` (villette; **riferimento** della taratura) | 1 | 1 | 1 | 1 |
| `apartment_blocks` (palazzi) | 1,5 | 1,3 | 1 | 0,8 |
| `city_center` (centro città) | 2 | 1,5 | 1,1 | 0,7 |
| `rural` (campagna) | 0,3 | 0,7 | 0,9 | 1,5 |
| `park` (parco, giardini) | 0,8 | 0,2 | 0,6 | 1 |

Piano: un gatto che vive dal 2° piano in su ha l'ancora a 0,6 volte la distanza (si
nasconde nel palazzo o ai suoi piedi). **Tutti i numeri di questa sezione sono stime senza
fonte**; il riferimento è la villetta perché da lì vengono gli studi della taratura (Huang:
Australia e USA; Kremer: Dallas, dove la distanza cambia per quartiere).

#### Il luogo in 3D (nel motore: `sim/place.py`; il mondo si costruisce con `proto/luogo3d/`)

**Quanto lontano lo dicono gli studi, dove lo dice il 3D.** La distanza dell'ancora resta
quella tarata in A5; il luogo sceglie solo **in quale direzione**, fra i posti veri a quella
distanza. Le ancore e la selezione nel passo valgono per i gatti (gli studi sono su gatti);
per tutti, cani compresi, nessun passo finisce dove l'animale non può stare. Senza luogo il
motore dà gli stessi bit di prima. **In uso la variante 2**, edifici e giardini senza altezze
(Marcello, 2026-09-26); le altezze restano un'opzione del caso (`"heights": true`), da
accendere quando i dati al metro le distinguono (`lessons.md` #35).

**Il mondo** (`proto/luogo3d/fetch.py`, `world.py`): una griglia da 2 m, ±600 m attorno a
casa, nello stesso piano di `sim/case.py`, riempita in automatico da dati aperti
(`riferimenti.md` §B): terreno (TINITALY 10 m), edifici con l'altezza (3D-GloBFP; quelli che
mancano da OpenStreetMap, con `building:levels` × 3 m o la mediana del posto), copertura del
suolo (ESA WorldCover 10 m), strade, muri e giardini (OpenStreetMap). Esce dal computer solo
un riquadro arrotondato a 0,01° (qualche km), mai l'indirizzo né il punto.

**I tipi di posto** (per cella da 2 m), sulle tre classi di Hanmer 2017 (§A): **naturale**
= `veg` (alberi, arbusti, prato, coltivi: WorldCover 10-40; bosco, prato, orti di OSM);
**giardino** = `garden` (giardini e parchi di OSM) e `open` (il costruito lontano da edifici
e strade: cortili e giardini privati, che a 10 m non si distinguono dal lastrico);
**costruito** = `edge` (a meno di 3 m da un edificio: portici, scale, garage, cantine),
`street` (carreggiata) e, con i dislivelli (variante 3), `roof` (il tetto di un edificio,
raggiungibile a salti).

**Da dove esce il gatto** (Huang 2018, Tabella 4, 368 gatti di casa con la risposta): dalla
porta 74% (272), da finestra o balcone 16% (42 + 19), da una zanzariera rotta 6% (21),
altro 4%. Normalizzate: **porta 0,77, finestra 0,23**. La porta è il punto dell'accesso a
terra; la finestra è il perimetro della casa. Senza dislivelli (variante 2) il gatto scende
da tutto il perimetro; con i dislivelli (variante 3) solo dove il salto dal piano, alto
`piano × 3 m` sopra la porta, arriva su una superficie (terra o tetto) non più di `H_down`
più in basso né più di `H_up` più in alto: su una casa in pendio il primo piano può stare
a livello del terreno da un lato e a 6 m dall'altro.

**Raggiungibilità**: il costo di cammino più corto (Dijkstra, 8 vicini) dalle uscite a ogni
cella, fra celle dove il gatto può stare: gli edifici sono muri (variante 2) o tetti da
raggiungere a salti (variante 3); una cella di strada costa `c_road(classe)` volte la sua
lunghezza (il gatto evita le strade grandi); in salita ogni metro di dislivello costa
`k_up` metri in più. `reach(c) = min(1, d(c) / D(c))`, con `d` la distanza in linea d'aria
da casa e `D` il costo: 1 se il posto si raggiunge diritto, meno se c'è da girare attorno,
0 se non si raggiunge. Le due uscite si mescolano con i pesi di Huang (0,77 · 0,23).

**L'ancora**: per ogni gatto si estrae la distanza `r` dalla lognormale di A5 (mediana 49,5 m,
dispersione 2,1), poi una cella nell'anello `[r − Δ/2, r + Δ/2]` (Δ = max(2 m, 0,05 r)) con
peso `sel(tipo) × reach(c)`. Se l'anello è tutto a peso zero, o esce dalla griglia, la
direzione resta a caso (la regola di oggi). La distribuzione delle distanze resta quella di
A5 per costruzione: cambia solo la direzione.

**La selezione `sel(tipo)`**: il rapporto fra uso e disponibilità di un tipo di posto, dai
rapporti di selezione standardizzati di Manly di Hanmer 2017 (gatti accanto a grandi aree
verdi, come il luogo di prova): giardino 0,553, costruito 0,311, naturale 0,136; riportati
al costruito = 1: `garden` 1,78, `edge` = `street` = `roof` 1, `veg` 0,44 (Fardell 2021 va
nello stesso verso: la vegetazione è il 20% dell'area e il 7% delle posizioni). `open` sta a
metà fra giardino e costruito (media geometrica, 1,33): stima. Sono gatti residenti, non
smarriti: nessuno studio GPS su gatti smarriti è stato trovato. La prova è Huang, Tabella 6
(485 gatti trovati fuori): sotto la vegetazione 16%, in un cortile 20%, sotto portico o veranda 10%,
sotto casa 5%, garage, capanno e sotto 10%, sotto o dentro un veicolo 3%, tombino 4%,
aspettava fuori casa 19% (è la distanza zero, già in A). Raggruppate sui nostri tipi (senza
«fuori casa», trappola, colonia): `veg` 0,25, `garden` 0,27, `edge` 0,38, `street` 0,10.

**Il movimento attorno all'ancora**: quello di oggi; un passo di un'ora è un percorso, conta
dove arriva. Un passo che finisce dove l'animale non può stare (dentro un edificio, o fuori
dalle superfici raggiungibili con le altezze) **si rilancia** dallo stesso punto con la
stessa regola, fino a 5 volte, su un flusso di numeri separato; se non basta, finisce sulla
cella libera più vicina. Rifiutarlo accorciava le distanze del 16% (`lessons.md` #33);
mandarlo subito sulla cella più vicina raddoppiava la massa a ridosso dei muri (42% contro
21% di disponibilità, L2); rilanciato, 19% (L3), un po' sotto perché l'occupazione va con la
parte libera a portata di un passo.

**La selezione nel passo**: dopo il primo passo un gatto si muove con `p_move × sel_ref /
sel(tipo)`: resta più a lungo dove gli piace stare, e il tempo passato in un tipo di posto va
con `sel` (catena con attesa: l'occupazione è la disponibilità per 1 / `p_move`). `sel_ref` è
la media di `sel` sulle ancore estratte con la direzione a caso, prima che il luogo la scelga:
tiene la media di `p_move`, quindi le distanze. Prima del primo passo niente selezione: la
porta è il posto da cui il gatto fugge, non uno che ha scelto (senza questa regola la
mediana a 24 ore scende del 7,6%: `lessons.md` #38). Senza la selezione nel passo le ancore
scelgono e il passo diluisce (L1b).

**La mappa fine** (`make_place_grid` in `sim/outputs.py`; la usa `python -m sim` quando il
caso ha un luogo): la densità a nucleo adattiva di oggi su celle da 4 m sul quadrato del
luogo, azzerata dove il gatto non può stare e riportata alla massa che il quadrato teneva. La
massa fuori dal quadrato si perde: il riassunto la dice (`map_share_in_place`, 0,90 a 24 ore
sul luogo di prova).

**Come si prova senza casi**:
1. le distanze delle ancore restano quelle di A5 (quantili entro il 2%);
2. le distanze dei gatti liberi a 24 ore e a 7 giorni restano entro il ±10% di quelle
   della variante 1 (A e B1 reggono; B2 non cambia: i rischi non dipendono dal luogo);
3. C1: la mappa fine è calibrata (50% e 75% delle verità di una seconda corsa
   indipendente nelle regioni al 50% e al 75%; la griglia di ±600 m tiene l'88% della
   massa a 24 ore, il 90% non ci sta);
4. le quote per tipo di posto delle ancore tornano con Huang, Tabella 6, entro un fattore 2
   per tipo (la disponibilità del luogo di prova non è quella delle villette di Huang);
5. i rapporti di selezione di Manly sulle tre classi di Hanmer tornano con Hanmer (0,553 ·
   0,311 · 0,136), letti **contro la variante 1** alla stessa distanza (un disco attorno a
   casa non è la disponibilità giusta: `lessons.md` #36).

Esito (L1, L1b, L2 in `MISURE.md`), gatto di casa dal primo piano a 24 ore, variante 2 con
la selezione nel passo e il rilancio (L3): regge 1-3 (distanze dei liberi entro il 6% della variante 1, C1
0,47 / 0,73); la regione al 50% scende da 1,04 a 0,59 ha (0,72 con le sole ancore, 0,67
con la selezione nel passo, 0,59 con il rilancio); le posizioni lette contro la 1 danno
giardino 0,50 · costruito 0,34 · naturale 0,16 (Hanmer 0,553 · 0,311 · 0,136). La variante 3
differisce dalla 2 del 7% (`lessons.md` #35). `python -m sim` con il luogo: meno di 1 s.
**Sui gatti veri non è dimostrato** (L5, 45 gatti di casa del Regno Unito con il GPS): alle
posizioni vere la mappa con il luogo dà il 2% di densità in più della stessa mappa ruotata,
p = 0,030 contro la soglia 0,001. La mappa più stretta è coerente con il modello, non ancora
con i gatti.

| Parametro | Valore | Fonte |
|---|---|---|
| porta · finestra | 0,77 · 0,23 | Huang 2018, Tabella 4 |
| altezza di un piano | 3 m | stima (Whitney & Mehlhaff 1987 usano 3,66 m a New York) |
| `H_down` (salto in giù volontario) | 4 m | stima: la finestra del primo piano resta una via (Huang, Tabella 4: 16% da finestre e balconi); nessuno studio sul salto volontario, le cadute da 2 a 32 piani sono incidenti (Whitney & Mehlhaff: 90% sopravvive) |
| `H_up` (salto in su) | 1,5 m | stima: nessuno studio trovato |
| `sel`: `garden` · `open` · `edge` · `street` · `roof` · `veg` | 1,78 · 1,33 · 1 · 1 · 1 · 0,44 | Hanmer 2017; `open` stima |
| `c_road`: pedonale · servizio · residenziale · terziaria e oltre | 1 · 2 · 3 · 10 | stima: nessuno studio su attraversamento e larghezza |
| `k_up` (metri in più per metro salito) | 5 | stima: nessuno studio su salita e discesa |
| distanza di `edge` da un edificio | 3 m | stima |
| selezione nel passo | `p_move × sel_ref / sel(tipo)`, dal primo passo in poi | Hanmer 2017 (il tempo va con la selezione); `sel_ref` dalle ancore a caso (tiene le distanze) |
| `redraw` (rilanci di un passo che finisce dentro un edificio) | 5, poi la cella libera più vicina | scelta su L2-L3: con 0 la massa a ridosso dei muri raddoppia |

### Transizioni di stato (ogni ora, solo LOOSE)

Un solo numero casuale decide fra raccolta, ritorno e morte:

| Transizione | Rischio orario | Fattori |
|---|---|---|
| LOOSE → HELD | `h_pickup` | × `people` × 1,5 se ha il collare × 0,2 di notte × (1 + 0,25 al giorno dopo il 3°, fino a 3) per il cane diffidente |
| LOOSE → HOME | `h_home` | solo dopo `home_from`; × `home_late` dopo `home_until`; × 2 di notte per i gatti; × exp(−(t − 30 g)/30 g) dopo 30 giorni |
| LOOSE → DEAD | `h_dead` | × `traffic` |

Di una particella HELD si tiene **dove** è stata raccolta: serve al raggio dei canili.

### Le categorie e i parametri

Valori tarati in fase A4 per i cani e A5 per i gatti (`sim/calibrated.json`); fra parentesi la stima di partenza quando
è cambiata. I numeri senza parentesi sono ancora stime.

| Parametro | gatto casa | gatto libero | cane socievole | cane diffidente | cane pauroso |
|---|---|---|---|---|---|
| `p_move` giorno / notte | 0,05 / 0,30 | 0,15 / 0,40 | 0,60 / 0,20 | 0,50 / 0,30 | 0,40 / 0,50 |
| passo (m) | **25** (15) | **3** (40) | **25,5** (150) | **595** (250) | **1.190** in fuga, **238** dopo (500 / 100) |
| `step_sigma` | 1,0 | 1,2 | 0,8 | 1,0 | 1,0 |
| `kappa` | 0,5 | 0,5 | 1,0 | 2,0 | 4,0 in fuga, 0,5 dopo |
| ancora iniziale | **lognormale, mediana 49,5 m, dispersione 2,1** (entro 60 m) | **lognormale, mediana 540 m, dispersione 2,2** (entro 300 m) | casa | nessuna | nessuna |
| `pull` | 0,5 | 0,2 | 0,1 | 0 → 0,3 dopo | 0 → 0,4 dopo |
| `t_settle` media (h) | 0 | 0 | 0 | 12 | 6 |
| `h_pickup` /h | **0,00014** (0,002) | **0,00015** (0,003) | 0,08 | 0,01 | 0,003 |
| `h_home` /h | **0,00014** dal giorno 2 (0,004) | **0,00014** (0,010) | **0,0044** nelle prime 12 h, poi × 0,1 (0,020) | **0,0022** (0,010) | **0,00044** (0,002) |
| `h_dead` /h | 0,0002 | 0,0003 | 0,0003 | 0,0005 | 0,0010 |

Categorie miste quando non si sa: `cat` = casa 28 / libero 46 (le quote del campione di
Huang), `dog` = 50 / 30 / 20 (stima senza fonte).

### Come si tara (fase A)

Bersagli (`riferimenti.md` §A):
- **gatti** (Huang 2018, trovati vivi): gatto casa p25 / p50 / p75 = 9 / 39 / 137 m; gatto
  libero 14 / 300 / 1.609 m. **Rischi in competizione** (`lessons.md` #8): ogni gatto esce
  dallo stato libero al primo dei suoi eventi e si legge in quell'ora. Gli eventi sono i
  tre del motore (a casa → trovato a casa, distanza 0; raccolto → trovato in casa d'altri,
  distanza del punto di raccolta; morto → escluso) più uno che esiste **solo nella
  taratura**: trovato fuori da chi lo cerca (Huang: il 69% dei trovati vivi), con un rischio
  uguale a ogni distanza e costante a tratti (giorni 0-7, 7-30, 30-61) → la sua posizione.
  Si tarano insieme: la curva dei trovati vivi (34 / 50 / 56% entro 7 / 30 / 61 giorni),
  le quote per luogo entro 61 giorni (a casa 20% = 4% in casa + 19% degli 83% trovati
  fuori, «aspettava fuori casa»; in casa d'altri 11%; fuori il resto) e i quantili della
  distanza. Passi: una corsa del motore dà l'ora e il tipo degli eventi; i tre rischi della
  ricerca si risolvono esatti da quella corsa (la ricerca non dipende dal posto); `h_home` e
  `h_pickup` si scalano finché le quote tornano (i rischi non dipendono dal movimento nella
  zona di riferimento); poi griglia su ancora (mediana, dispersione) e passo. I rischi della
  ricerca si salvano in `calibrated.json` (`_search`) e servono solo a leggere Huang: il
  simulatore non li usa.
- **cani** (Kremer 2021, luogo della raccolta): 42% entro 120 m, 70% entro 1.609 m, le tre
  categorie insieme 50 / 30 / 20. Due scale di passo (socievole; diffidente e pauroso);
  `h_home` scalato perché i tornati da soli siano l'11% (Lord 2007: 8% su 71% ritrovati).
- Accettato se ogni quantile è entro ±20%; griglia grossa, poi fine, poi i primi cinque
  validati a 20.000 particelle. Dopo ogni modifica al motore si rifà (`lessons.md` #17).
  Esito: gatto casa sì (A5, 0,05), cani sì (A4, 0,135), gatto libero no (A5, 0,28).

### Calcolo

A ogni richiesta si **risimula da t0**, seme fisso: deterministico. 10.000 particelle
costano circa 1 ms all'ora: 90 giorni in 2-3 secondi. Ogni fattore che dipende dal tempo
usa l'ora che si sta vivendo, [h, h+1); l'ora «adesso» si arrotonda per eccesso dalla
mezz'ora (`lessons.md` #14, #15). All'ora «adesso» le particelle HOME escono dal conto:
se fosse tornato, chi chiede lo saprebbe.

### Uscite

- **Mappa**: celle da 50 m **centrate su casa**; valore = P(libero e nella cella), stimata
  con la **densità a nucleo adattiva**: ogni particella libera si allarga come una gaussiana
  di σ = max(25 m, α · distanza dalla 10ª vicina), α = 1,0 (scelta con C1: la copertura è
  quasi piatta fra 0,5 e 2,0). Calcolo: σ in classi a passo 2^¼ (il peso di una particella
  si divide fra le due classi attorno al suo σ, varianza conservata), un filtro gaussiano per
  classe sul riquadro delle sue particelle, i σ grandi su griglie 2, 4, 8… volte più rade
  riportate su quella fine per interpolazione. Rettangolo: il 99% delle particelle su
  ciascun asse più 2 volte il σ mediano (almeno ±200 m); la massa oltre si perde (~2%).
  PNG; GeoJSON come **quadtree**: blocchi quadrati da 50 m a 3,2 km, divisi in quattro
  finché tengono più dello 0,1% della massa, dai più densi fino al 99% della massa (ogni
  blocco con `p` e `size_m`), più i punti di casa e di «cerca qui». Sui due esempi: 0,4 e
  0,5 s, GeoJSON 93 KB e 0,6 MB.
- **Stati**: P(LOOSE), P(HELD), P(HOME) = 0, P(DEAD); P(torna da solo entro 7 giorni),
  simulando 168 ore in avanti senza prove.
- **Cerca qui**: fino a 5 punti, i punti più probabili della mappa, ad almeno 150 m l'uno dall'altro,
  ciascuno con la massa delle celle attorno (ogni cella a un punto solo); ora consigliata:
  gatti dalle 20:00 (o subito se è notte), cani subito se è giorno, altrimenti alle 6:00.
- **Raggio**: distanza da casa che contiene il 50% e il 90% della massa LOOSE.
- **Chiama**: sì se P(HELD) > 0,3 (soglia da tarare), con raggio = 95° percentile della
  distanza dei punti di raccolta + 10 km. L'elenco di canili e veterinari viene da OSM in
  v0.1.

## Le prove del modello (il metodo genoma)

Ogni misura si annota in `MISURE.md` **con la previsione scritta prima del risultato**; ogni
errore in `lessons.md`. Senza prove esterne l'accuratezza si misura solo così: contro i
numeri pubblicati (A, B) e contro un modello più semplice (C).

**A — Taratura**: sopra. `python -m sim.calibrate …`.

**B — Controllo predittivo** (`python -m sim.validate`), su numeri non usati in A:
- B1: gatti mescolati 164:150 (i trovati vivi di Huang per gruppo) contro Huang complessivo
  (9 / 50 / 500 m, 75% entro 500 m);
- B2: P(HOME entro t) e P(HOME o HELD entro t) contro i gatti trovati vivi (34 / 50 / 56% a
  7 / 30 / 61 giorni). Attenzione: la stessa curva è l'ingresso di A (`lessons.md` #9);
- B3: cani raccolti entro 5 giorni contro «oltre il 90% dei riuniti entro 5 giorni»
  (Kremer; da verificare se contati dalla perdita);
- B4: I-CAD (4% dei cani e 0,5% dei gatti passano dal canile) contro la quota di HELD fra i
  ritrovati: passa sempre, non ha potere.

**C — Confronto con il modello ad anelli** (`python -m sim.baseline`): 40 casi sintetici per
categoria, 50 verità indipendenti per caso con parametri perturbati del ±30%, ora di
partenza e «adesso» (fra 12 ore e 10 giorni) casuali. Anelli ai quantili 25/50/75/95/99%
della distanza della categoria a quell'ora, sulla stessa griglia da 50 m. Misura: area da
cercare, dalla cella più probabile, prima di arrivare alla verità (mediana e 90°
percentile), e copertura al 50% e 90%; per verità, senza gradini (`lessons.md` #26): quota
dove il simulatore cerca meno e media geometrica del rapporto. Il simulatore **batte** se
mediana e 90° percentile sono tutti e due sotto gli anelli. Se non batte, ci si ferma e si decide con Marcello.
In una zona uniforme il simulatore è per costruzione radiale come gli anelli: può batterli
in distanza (una densità più fedele di quattro anelli) ma in direzione solo con la mappa
della zona.

**C1 — La mappa è una probabilità calibrata?** (`python -m sim.validate --coverage`): verità
dallo stesso modello (una seconda simulazione indipendente); nelle celle che tengono il 50%
e il 90% della massa devono cadere il 50% e il 90% delle verità. Isola lo stimatore della
mappa dalla dinamica in pochi secondi. La regione si prende sulla massa della griglia, il
~98% di quella libera: al 90% ci si aspetta ~0,88. Test: tutte le categorie, intervallo a 4
errori standard dentro 0,45-0,58 e 0,84-0,95.

## Cosa non so ancora (buchi dichiarati)

- `h_pickup` dei cani non ha una fonte diretta: si ricava da Lord 2007 e dai tempi di
  ingresso in canile di Austin e Dallas.
- I bersagli mescolano popolazioni (Australia, Ohio, Dallas); nessuno studio è di Napoli.
  Il luogo in 3D porta la geometria di Napoli, i numeri restano quelli degli studi.
- La direzione di fuga del cane pauroso è casuale; in v0.1 dipende dalle strade.
- Le proporzioni fra le tre categorie di cani (50/30/20) sono inventate.
- Moltiplicatori di zona e del piano: stime senza fonte.
- In una zona uniforme la mappa è radiale: batte gli anelli in distanza (C2, in tutte le
  categorie sulla media geometrica), non in direzione. Nei casi estremi (verità fuori da
  tutte e due le mappe) è pari.
- Luogo in 3D: la selezione dei posti viene da gatti residenti (Hanmer 2017), non smarriti:
  nessuno studio GPS su gatti smarriti è stato trovato. Nessuno studio per attraversare le
  strade, il salto in su, la salita e la discesa: stime dichiarate nella tabella.
- Luogo in 3D: non dimostrato sui gatti veri (L5: effetto 2%, p = 0,030 su 45 gatti; ne
  servono circa 165). Quale pezzo porta il segnale non si sa ancora.
- Luogo in 3D: il rilancio del passo mette un po' meno gatti dove è fitto (0,91 della
  disponibilità a ridosso dei muri sul luogo di prova, L3); il «naturale» di Hanmer (grandi aree verdi) non è il
  «sotto la vegetazione» di Huang (cespugli nei giardini), che a 10 m non si vede; i
  giardini privati a 10 m non si vedono; con il terreno a 10 m nessun tetto è a portata di
  salto (`lessons.md` #35).

## Stack e struttura

Python 3.12, `numpy`, `scipy`, `matplotlib`, `pytest`; per il luogo in 3D `pyshp` e
`tifffile`, in Python puro (niente `rasterio`, `pyproj`, `geopandas`: Smart App Control
blocca le loro DLL, `lessons.md` #31); ambiente in `.venv/`. Codice, identificatori e commenti in **inglese**.

```
sim/
  __init__.py, __main__.py
  categories.py    # the five categories, mixtures, calibrated overrides
  calibrated.json  # phase A output
  environment.py   # zones, patches, floor: per-cell multipliers
  engine.py        # particles, hourly step, state transitions, run_case
  place.py         # the place in 3D: world, cell types, exits, reachability, anchors, steps
  case.py          # case JSON, local projection
  outputs.py       # grid (and the 4 m map of a place), PNG/GeoJSON map, states, advice
  calibrate.py     # phase A
  validate.py      # phase B, and C1 (map calibration: --coverage)
  baseline.py      # phase C: ring model vs simulator
  compare.py       # before / rings / now, side by side (out/confronto-prima-dopo.png)
  cli.py           # python -m sim <case.json> --now <iso> --out <dir>
  fingerprint.py   # hashes of 7 runs without a place: before and after an engine change
tests/             # pytest -q: about 30 s
  conftest.py      # distribution-free quantile interval (4 SE)
  test_engine.py   # behaviour: determinism, zone, grid, spots, CLI < 10 s
  test_integrity.py  # exact arithmetic and closed-form theory, piece by piece
  test_pressure.py   # 90 days, 100k particles, extremes, 40 random cases
  test_targets.py    # phase A: the whole 4-SE interval within +-20% of each target
  test_hypotheses.py # phases B and C1; known failures are strict xfails
  test_place3d.py    # the place in 3D on a synthetic place (no private data)
  test_gps_score.py  # the rotation test finds a place cats follow, and nothing in random directions
cases/
  esempio-gatto.json, esempio-cane.json
proto/luogo3d/     # builds the world of a place (docs: "Il luogo in 3D")
  fetch.py         # open data for one place: OSM, 3D-GloBFP, TINITALY, WorldCover, Copernicus
  world.py         # layers on a 2 m grid centred on home -> world.npz
  variants.py      # the three maps side by side and the checks (L1, L1b, L2)
  utm.py, cogread.py  # pure-Python UTM and GeoTIFF windows (lessons.md #31)
proto/gps/         # the place against real cats: GPS of pet cats (Cat Tracker), L5
  build_cats.py    # download, home point, world.npz per cat from OpenStreetMap
  score.py         # log score of the place map vs the same map rotated; permutation test
```

Formato del caso (`cases/*.json`):

```json
{
  "category": "cat_indoor",
  "home": {"lat": 40.85, "lon": 14.27},
  "lost_at": "2026-09-20T19:00",
  "collar": false,
  "area": {"zone": "apartment_blocks", "floor": 3,
           "patches": [{"zone": "park", "center": {"lat": 40.8512, "lon": 14.2688}, "radius_m": 120}]}
}
```

`category`: una delle cinque (`cat_indoor`, `cat_outdoor`, `dog_friendly`, `dog_wary`,
`dog_fearful`) o `cat` / `dog` se non si sa.

Con il luogo in 3D si aggiunge `"place": {"world": "luogo/world.npz", "heights": false}`: il
percorso parte dalla cartella del caso, il mondo deve essere centrato sulla casa del caso
(entro 1 m, altrimenti errore). Con un luogo la zona resta quella di riferimento (villette):
i moltiplicatori di zona sono stime che il luogo sostituisce.

## Quando v0 è finito

- ✅ `python -m sim` gira su un caso di esempio in meno di 10 secondi (0,5 s) e produce
  mappa, stati, consigli.
- ✅ Fase A fatta per le cinque categorie (rifatta dopo la correzione del motore, A4),
  parametri e scarti in `MISURE.md` (gatto libero fuori di poco).
- ✅ Fase B fatta, con previsioni e risultati.
- ✅ Fase C fatta (senza prove, C2) e **superata** con la mappa lisciata: 0,44 volte gli
  anelli sulla mediana dell'area da cercare, 0,42 sul 90° percentile (`MISURE.md`).
- ✅ `pytest` verde: integrità, pressione, ipotesi; i fallimenti noti sono dichiarati.
