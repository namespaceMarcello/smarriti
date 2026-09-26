# Misure

Ogni misura ha la **previsione scritta prima** del risultato. Un risultato negativo si
scrive uguale: una premessa che dà zero è una scoperta. In coda, in ordine di tempo.
Le fasi (A taratura, B controllo predittivo, C anelli) sono in
`simulatore.md`.

Formato di ogni voce:

```
### <data> — <fase> — <cosa si misura>
Previsione: <numero o intervallo, scritto prima di lanciare>
Comando: <come si riproduce>
Risultato: <numero>
Verdetto: <regge / non regge / da rifare> — <una riga sul perché>
```

Nessuna misura ancora.

### 2026-09-25 — A0 — i parametri di partenza di `simulatore.md` contro i bersagli
Previsione: i rischi orari di partenza sono troppo alti per i gatti. Gatto da appartamento:
al momento del ritrovamento più di metà risulta HOME (quota prevista 0,45-0,65 contro 0,20),
quindi p25 = p50 = 0 m e p75 fra 40 e 70 m (bersagli 9 / 39 / 137). Gatto libero: HOME
0,75-0,85, p25 = p50 = 0, p75 sotto i 200 m (bersagli 14 / 300 / 1.609). Cani insieme: il
42° percentile della distanza di raccolta fra 300 e 700 m (bersaglio 120), il 70° fra 0,8 e
2 km (bersaglio 1.609); quota tornati da soli fra 0,30 e 0,40 (bersaglio 0,11).
Comando: `python -m sim.calibrate start`
Risultato: gatto da appartamento p25/p50/p75 = 0 / 15,6 / 44 m, HOME 0,443, HELD 0,131.
Gatto libero 0 / 0 / 78 m, HOME 0,705, HELD 0,092. Cani: 42° percentile 400 m, 70° 795 m,
tornati da soli 0,369.
Verdetto: regge nel verso, sbaglia di poco tre numeri su dieci (mediana del gatto da
appartamento 15,6 m contro 0-10; HOME dei gatti 0,44 e 0,71, appena sotto gli intervalli;
70° dei cani 795 m contro 0,8-2 km) — i rischi di partenza fanno tornare a casa troppi
gatti, e i cani sono raccolti troppo lontano e troppo vicino insieme: la distribuzione è
troppo stretta (400 → 795 m contro 120 → 1.609).

### 2026-09-25 — A — taratura delle cinque categorie
Previsione: gatto da appartamento: h_home scende a 0,0010-0,0020 /h (da 0,004), ancora con
mediana 40-80 m e dispersione 1,0-1,5; i tre quantili entro ±20%. Gatto libero: h_home a
0,002-0,004 (da 0,010), ancora con mediana 400-900 m e dispersione 2-3; il 25° percentile
(14 m) è il più difficile: una possibilità su due di stare entro ±20%. Cani: passo ×0,2-0,5,
raccolta ×2 o più; errore massimo 0,1-0,3.
Comando: `python -m sim.calibrate all`
Risultato: gatto da appartamento p25/p50/p75 = 8,1 / 40,7 / 146,9 m (errore massimo 0,099;
16 insiemi accettati su 75), ancora mediana 52 m e dispersione 2,15, passo 25 m, h_home
0,00087, h_pickup 0,00093. Gatto libero **non accettato**: 29,6 / 146 / 653 m contro 14 /
300 / 1.609 (errore 1,11; 0 accettati su 165). Cani **non accettati**: 42° percentile 172 m,
70° 591 m contro 120 e 1.609 (errore 0,63; 0 su 65), con passo ×0,98 e raccolta ×6,4 (bordo
della griglia).
Verdetto: regge per il gatto da appartamento (ma h_home 0,00087 sotto l'intervallo previsto
e dispersione 2,15 sopra); non regge per gli altri due. Gatto libero: il passo minimo della
griglia era 20 m e l'agitarsi attorno all'ancora spinge i gatti vicini a 50-80 m: il 25°
percentile di 14 m resta irraggiungibile. Cani: un'unica scala di passo per le tre categorie
dà distanze di raccolta troppo omogenee; i dati chiedono cani raccolti quasi sulla porta
(42% entro 120 m) **e** una coda lunga, cioè categorie più diverse fra loro di quanto dice
la tabella di partenza.

### 2026-09-25 — A2 — seconda taratura: gatto libero con passi piccoli, cani con due scale
Previsione: gatto libero accettato (errore ≤ 0,20) con passo ≤ 10 m, ancora mediana
500-800 m, dispersione 2,0-2,6. Cani: una scala per il socievole (0,15-0,4) e una per
diffidente e pauroso insieme (1,5-3), raccolta ferma ai valori di partenza: accettati con
probabilità 0,6.
Comando: `python -m sim.calibrate cat_outdoor` e `python -m sim.calibrate dogs`
Risultato: gatto libero 17,1 / 256,6 / 1.440,5 m, errore massimo 0,221 sulla validazione a
20.000 particelle (2 insiemi accettati su 75 nella griglia fine, a 1.500 particelle):
ancora mediana 585 m, dispersione 2,1, passo 1,8 m. Cani **accettati**: 42° percentile
119,7 m, 70° 1.458,9 m (errore 0,093; 5 su 25), socievole ×0,2 (passo 30 m), diffidente e
pauroso ×2,8 (700 m; il pauroso 1.400 m in fuga, 280 m dopo), h_home ×0,216 perché i
tornati da soli siano l'11%.
Verdetto: regge per i cani (le tre previsioni giuste). Gatto libero: fuori per un soffio
(0,221 contro 0,20), con passo previsto giusto (≤ 10 m) e ancora nell'intervallo (585 m),
dispersione 2,1 dentro. Scoperta: il passo scende a 1,8 m, cioè il gatto libero **sta fermo
nel nascondiglio**; le distanze di Huang si spiegano con «un nascondiglio a distanza
lognormale, e lì resta». Il conto a mano (lognormale con il 20% a casa) dice che l'errore
minimo possibile è circa 0,11 con dispersione 2,35 e mediana 570 m: lo 0,221 è il vincitore
scelto su un campione piccolo, non un limite del modello.

### 2026-09-25 — A3 — gatto libero: griglia più fine, i primi cinque validati a 20.000
Previsione: accettato, errore massimo fra 0,12 e 0,20, dispersione 2,2-2,5, mediana
500-650 m.
Comando: `python -m sim.calibrate cat_outdoor`
Risultato: 14,2 / 230,5 / 1.426,4 m, errore massimo 0,232 (0 accettati su 75 a 2.500
particelle; il migliore dei primi cinque a 20.000): ancora mediana 540 m, dispersione 2,2,
passo 1,8 m.
Verdetto: non regge. Il conto a mano ignorava il **tragitto**: con `pull` 0,2 e `p_move`
0,15 / 0,40 il gatto impiega giorni a raggiungere il nascondiglio, e quelli trovati nei
primi giorni (Huang: 5% al giorno nella prima settimana) sono ancora a metà strada:
abbassano la mediana (230 contro 300) mentre il 25° torna giusto. Il gatto libero resta
tarato a 0,22-0,23 dai bersagli, con i parametri di A3 in `sim/calibrated.json`. Idea
successiva, non ancora provata: `pull` e `p_move` liberi nella griglia (il gatto raggiunge
il nascondiglio in ore, non in giorni).

### 2026-09-25 — B — controllo predittivo su numeri non usati nella taratura
Previsione:
- B1, gatti mescolati 164:150 contro Huang complessivo (9 / 50 / 500 m, 75% entro 500 m):
  p25 8-11 m, **mediana 70-110 m (fuori: il bersaglio è 50)**, p75 500-700 m, entro 500 m
  0,70-0,76.
- B2, gatti nel tempo: con i rischi tarati (h_home 0,00075-0,00087, h_pickup 0,00093) il
  limite stretto P(HOME entro t) ≤ trovati(t) regge a 7 giorni (HOME 0,10-0,18 contro 0,34)
  e **non regge a 30 e 61 giorni** (HOME 0,50-0,60 e 0,70-0,80 contro 0,50 e 0,56). Motivo
  previsto: leggere il gatto a un'ora di ritrovamento esterna lascia i rischi liberi di
  essere troppo alti, perché un gatto tornato al giorno 3 conta come «a casa» anche se lo si
  legge al giorno 20.
- B3, cani: raccolti entro 5 giorni 0,75-0,85 (**sotto** il 0,90 di Kremer); per categoria:
  socievole > 0,95, diffidente 0,5-0,7, pauroso 0,2-0,35.
- B4, I-CAD: passa, ma senza potere: i trattenuti sono la maggior parte dei cani ritrovati
  (> 0,8) e più dello 0,5% dei gatti; qualsiasi modello sensato passa.
Comando: `python -m sim.validate`
Risultato:
- B1: p25/p50/p75 = 10,1 / 72,0 / 469,2 m (errori 0,12 / 0,44 / 0,06); entro 500 m 0,757.
- B2: HOME entro 7 / 30 / 61 giorni = 0,155 / 0,452 / 0,535 (appartamento), 0,157 / 0,412 /
  0,486 (libero), 0,156 / 0,427 / 0,504 (misto 28:46), contro trovati vivi 0,34 / 0,50 /
  0,56: il limite stretto regge ovunque, per un soffio a 30 e 61 giorni. HOME o HELD: 0,24 /
  0,66 / 0,80 (misto): il limite largo non regge a 30 e 61 giorni.
- B3: cani raccolti entro 5 giorni 0,814 (socievole 0,999, diffidente 0,664, pauroso 0,344)
  contro > 0,90. Trattenuti a 60 giorni 0,81, tornati da soli 0,11.
- B4: trattenuti fra i ritrovati a 30 giorni 0,883 (cani), 0,354 (gatti): passa.
Verdetto:
- B1 regge su p25, p75 e quota entro 500 m; **non regge sulla mediana** (72 contro 50,
  previsto). Previsione giusta tranne il p75 (469, sotto l'intervallo 500-700).
- B2 **non regge nella sostanza**, anche se il limite stretto passa (previsto che
  saltasse: previsione sbagliata sul numero, giusta sul motivo). Il modello dice che a 61
  giorni metà dei gatti è tornata da sola, cioè quasi tutti i ritrovati; Huang dice che a
  casa ne è stato trovato circa il 20%, quindi circa 0,20 × 0,56 = 0,11 dei persi. **h_home
  dei gatti è 4-5 volte troppo alto.** La causa è il metodo della taratura: leggere la
  particella a un'ora di ritrovamento estratta da fuori conta come «trovato a casa» un gatto
  tornato al giorno 3 e letto al giorno 20. Correzione: tarare i rischi come rischi in
  competizione (a casa, raccolto, trovato cercando) sulla curva di Huang e sulle quote dei
  luoghi insieme; il ritrovamento avviene all'ora dell'evento, non a un'ora esterna.
- B3 non regge (0,81 contro > 0,90; previsione giusta in tutte e quattro le cifre): il
  pauroso e il diffidente vengono raccolti troppo tardi. Da verificare se i «5 giorni» di
  Kremer sono dalla perdita o dall'ingresso in canile.
- B4 passa senza potere, come previsto.

### 2026-09-25 — C — simulatore contro modello ad anelli, 200 casi sintetici
Casi: 40 per categoria; la verità si muove con parametri perturbati del ±30% rispetto a
quelli tarati; 0-4 avvistamenti (Poisson 1,5), il 20% falsi, credibilità 0,6, errore
100 m; metà dei casi con una ricerca negativa; «adesso» fra 12 ore e 10 giorni, con la
verità ancora libera. Anelli ai quantili 25/50/75/95/99% della distanza della categoria a
quell'ora, sulla stessa griglia da 50 m. Misura: area cercata cella per cella, dalla più
probabile, prima di arrivare alla posizione vera (mediana e 90° percentile sui casi); area
che tiene il 50% e il 90% della massa, e quante volte la verità ci cade dentro.
«Batte» vuol dire: su tutti i casi mediana **e** 90° percentile dell'area del simulatore
sotto quelli degli anelli.
Previsione: batte. Rapporto simulatore / anelli sulla mediana 0,4-0,7 su tutti i casi,
0,1-0,4 con almeno un avvistamento vero, 0,9-1,2 senza avvistamenti (lì sono due mappe di
sola distanza). Il simulatore senza prove ≈ anelli (0,9-1,1). Gatto da appartamento: nessun
guadagno (0,9-1,0), perché l'errore dell'avvistamento (100 m) è più largo del suo raggio.
Copertura al 90% del simulatore 0,75-0,90 (un po' troppo sicuro, per la perturbazione).
Comando: `python -m sim.baseline`
Risultato (area da cercare prima della verità, mediana / 90° percentile, ettari):

| Casi | Anelli | Simulatore senza prove | Simulatore | Rapporto sim/anelli (p50 · p90) |
|---|---|---|---|---|
| tutti (200) | 418 / 34.935 | 283 / 728.792 | **91** / 728.792 | 0,22 · 20,9 |
| con un avvistamento vero (145) | 447 / 53.364 | 317 / 736.755 | 91 / 736.755 | 0,20 · 13,8 |
| senza avvistamenti (45) | 45 / 17.849 | 297 / 710.985 | 295 / 710.985 | 6,6 · 39,8 |
| gatto da appartamento | 8,3 / 481 | 2,1 / 31.648 | 2,1 / 31.648 | 0,26 · 65,7 |
| gatto libero | 594 / 60.784 | 307 / 4,7 M | 96 / 4,7 M | 0,16 · 77,2 |
| cane socievole | 3,8 / 14,4 | 3,2 / 13,5 | 3,1 / 12,5 | 0,83 · 0,87 |
| cane diffidente | 6.795 / 44.458 | 250.680 / 280.080 | 250.680 / 280.079 | 36,9 · 6,3 |
| cane pauroso | 1.394 / 69.786 | 598.068 / 697.499 | 598.068 / 697.499 | 429 · 10,0 |

Copertura al 90% (la verità cade nell'area che tiene il 90% della massa): anelli 0,94,
simulatore 0,52 (cane diffidente 0,05, pauroso 0,30, socievole 0,875).
Verdetto: **non batte** secondo il criterio scritto prima (mediana sì, 0,22; 90° percentile
no, 20,9). Previsioni: con avvistamento 0,20 giusta (0,1-0,4); tutti 0,22 meglio del
previsto (0,4-0,7); senza avvistamenti, simulatore senza prove ≈ anelli, gatto da
appartamento senza guadagno e copertura 0,75-0,90 **sbagliate**.
Diagnosi: la mappa è un istogramma di 5.000 particelle su celle da 50 m. Dove le particelle
si spargono su più area di quanta ne possono riempire (N × 0,25 ha: cani diffidenti e
paurosi, la coda dei gatti) quasi tutte le celle restano vuote e la verità cade in una
cella vuota, che costa mezzo disco di ricerca. La prova: gli anelli sono costruiti dalle
**stesse** particelle della mappa senza prove, eppure coprono la verità nel 90% dei casi
contro il 5% (cane diffidente). Perde lo stimatore della mappa, non la dinamica: dove le
particelle sono fitte (cane socievole) il simulatore batte gli anelli su tutte e due le
misure. Correzione proposta, non ancora provata: lisciare la mappa (ogni particella si
allarga su un raggio pari alla distanza delle vicine) e ripetere C sugli stessi 200 casi.
Qui ci si ferma: si decide insieme.

### 2026-09-25 — C1 — la mappa è una probabilità calibrata?
Misura: la verità viene dallo **stesso** modello (particelle di una seconda simulazione
indipendente, 4.000, seme diverso); mappa da 10.000 particelle, celle da 50 m. Copertura =
quante verità libere cadono nelle celle che tengono il 50% e il 90% della massa. Una mappa
calibrata dà 0,50 e 0,90 (errore campionario ≈ 0,006).
Previsione: a 48 ore, copertura al 90%: cane socievole 0,85-0,92, gatto da appartamento
0,75-0,90, gatto libero 0,45-0,65, cane pauroso 0,15-0,40, cane diffidente 0,05-0,25; a
7 giorni più bassa per i tre che si spargono. Al 50% la stessa graduatoria.
Comando: `pytest -q tests/test_hypotheses.py -k coverage` (i numeri: `python -m sim.validate --coverage`)
Risultato (copertura al 50% / al 90%): gatto da appartamento 0,521 / 0,870 (48 h), 0,524 /
0,887 (7 g); gatto libero 0,487 / 0,635 e 0,490 / 0,602; cane socievole 0,530 / 0,891
(48 h; a 7 giorni nessuno è ancora libero); cane diffidente 0,118 / 0,118 e 0,035 / 0,035;
cane pauroso 0,251 / 0,251 e 0,214 / 0,214.
Verdetto: previsioni giuste tutte e dieci. La mappa è calibrata dove le particelle sono
fitte e non lo è dove si spargono: per i due cani lontani 50% e 90% coincidono, perché ogni
cella occupata ha una particella sola e la copertura è solo la probabilità che la verità
cada in una cella occupata. È il difetto di C isolato, in un test da pochi secondi
(`tests/test_hypotheses.py`), che passerà quando la mappa sarà lisciata.

### 2026-09-25 — A4 — ritaratura dopo la correzione dei tempi (`lessons.md` #15, #17)
Il motore è cambiato (i fattori che dipendono dal tempo usano l'ora d'inizio, le ore degli
eventi arrotondano per eccesso): con i parametri di A2/A3 e lo stesso seme, il 70°
percentile dei cani passa da 1.459 a 1.767 m.
Previsione: gatto da appartamento accettato con parametri entro il 15% di quelli di A
(l'assestamento non lo riguarda). Gatto libero di nuovo fuori, 0,20-0,25. Cani accettati,
con la scala «lontani» più bassa di prima: 2,0-2,6 (era 2,8), errore ≤ 0,12.
Comando: `python -m sim.calibrate all`
Risultato: gatto da appartamento 8,7 / 40,3 / 131,8 m (errore 0,038; ancora 49,5 m,
dispersione 2,0, passo 25 m, h_home 0,00088). Gatto libero 14,2 / 230,5 / 1.426 m (0,232,
parametri uguali ad A3). Cani 103,9 / 1.500 m (errore 0,135; socievole ×0,17, lontani
×2,38, h_home ×0,218).
Verdetto: regge. Previsioni giuste tranne l'errore dei cani (0,135 contro ≤ 0,12): il 42°
percentile è sceso a 104 m. I numeri di B e C più sopra sono del motore di prima.

### 2026-09-25 — B′ e C′ — ripetute con il motore corretto e i parametri di A4
Previsione: stessi verdetti di B e C. B1 mediana 65-80 m (fuori), p75 420-520 m; B2 HOME a
61 giorni 0,48-0,54 (limite stretto regge), HOME o HELD a 30 giorni > 0,6; B3 0,78-0,84.
C: mediana del rapporto 0,15-0,35, 90° percentile > 5 (non batte), copertura al 90% del
simulatore 0,45-0,60.
Comando: `python -m sim.validate` e `python -m sim.baseline`
Risultato: B1 10,5 / 70,2 / 432,5 m, entro 500 m 0,766. B2 (misto) HOME 0,156 / 0,428 /
0,505 a 7 / 30 / 61 giorni, HOME o HELD 0,243 / 0,662 / 0,797. B3 0,816 (0,999 / 0,670 /
0,347). B4 passa. C: rapporto simulatore / anelli 0,407 sulla mediana (78 contro 193 ha),
18,2 sul 90° percentile; con un avvistamento vero 0,29 · 12,3; senza 0,73 · 35,9; copertura
al 90% 0,51 contro 0,945; cane socievole 1,11 · 0,80.
Verdetto: stessi verdetti. Previsioni giuste tranne la mediana di C (0,41 contro 0,15-0,35).
C resta **non superata**: ci si ferma, si decide con Marcello.

### 2026-09-25 — C2 — simulatore contro anelli, **senza prove** (la nuova definizione)
Marcello, 2026-09-25: il simulatore non usa avvistamenti né ricerche; predice e basta. C
si ridefinisce: 40 casi per categoria, 50 verità indipendenti per caso (parametri
perturbati del ±30%, ora di partenza e «adesso» casuali), mappa del simulatore contro
anelli sulla stessa griglia. Le misure C e C′ più sopra (con avvistamenti) non valgono più
come criterio.
Previsione: in una zona uniforme e senza prove il simulatore è un modello radiale come gli
anelli; vince dove la densità è più appuntita di quattro anelli uniformi (gatti vicino a
casa) e perde dove l'istogramma è rado. Rapporto sulla mediana 0,5-0,9 (tutti), sul 90°
percentile > 5: **non batte**. Per categoria sulla mediana: gatto da appartamento 0,3-0,8,
cane socievole 0,8-1,2, gatto libero 0,4-1,0, cani diffidente e pauroso > 3. Copertura al
90%: simulatore 0,45-0,65, anelli 0,88-0,97.
Comando: `python -m sim.baseline`
Risultato (area prima della verità, mediana / 90° percentile in ettari; copertura al 90%):

| Categoria (verità) | Anelli | Simulatore | Rapporto p50 · p90 | Copertura anelli · sim |
|---|---|---|---|---|
| tutte (8.534) | 327 / 53.230 | 14.846 / 2,4 M | 45,4 · 45,9 | 0,94 · 0,48 |
| gatto da appartamento | 6,3 / 324 | **1,8** / 15.324 | **0,28** · 47,3 | 0,95 · 0,85 |
| gatto libero | 51 / 71.132 | 270 / 7,3 M | 5,3 · 102 | 0,95 · 0,57 |
| cane socievole (868; 12 casi senza particelle libere) | 2,3 / 10,8 | 2,4 / 12,2 | 1,06 · 1,13 | 0,94 · 0,87 |
| cane diffidente | 5.415 / 28.664 | 191.715 / 247.611 | 35,4 · 8,6 | 0,92 · 0,07 |
| cane pauroso | 7.628 / 58.723 | 485.671 / 579.629 | 63,7 · 9,9 | 0,94 · 0,19 |

Verdetto: **non batte**. Previsioni giuste sul 90° percentile, sulle coperture, su gatto
da appartamento (0,28, appena meglio dell'intervallo), cane socievole e cani lontani;
sbagliate su tutti i casi insieme (45 contro 0,5-0,9: nella mediana di tutte le verità
pesano i cani lontani, dove l'istogramma è vuoto) e sul gatto libero (5,3 contro 0,4-1,0).
Due fatti: (1) dove la mappa è fitta il simulatore vince (gatto da appartamento: la
densità vicino a casa è più appuntita di quattro anelli uniformi) o pareggia (cane
socievole); dove è rada perde, come in C1. (2) Senza prove e in una zona uniforme il
simulatore è, per costruzione, un modello radiale: il meglio che può fare è un anello
continuo e ben stimato. Per battere gli anelli in direzione, e non solo in distanza, serve
la mappa della zona (strade, palazzi, parchi): è l'unica cosa che rompe la simmetria
attorno a casa. Ci si ferma: si decide con Marcello.

### 2026-09-25 — C1″ e C2″ — la mappa lisciata (densità a nucleo adattiva)
La mappa non è più un istogramma: ogni particella libera si allarga come una gaussiana di
σᵢ = max(25 m, α · dᵢ), con dᵢ la distanza dalla 10ª vicina (`sim/outputs.py`,
`make_grid`). Il rettangolo tiene il 99% delle particelle più 2 volte il σ mediano. α si
sceglie con C1 su un seme diverso da quello della misura (seme 7 per la scelta, seme 0 per
C1, i semi di sempre per C2).
Previsione, scritta prima di ogni lancio:
- **Scelta di α** (0,5 / 0,7 / 1,0 / 1,4 / 2,0, a 48 ore): la copertura cresce con α (più
  liscio, regioni più larghe); α migliore fra 1,0 e 2,0; con α = 0,5 i cani lontani restano
  sotto (copertura al 90% 0,70-0,85), non più a 0,1-0,2.
- **C1** con l'α scelto, a 48 ore e a 7 giorni: copertura al 50% fra 0,46 e 0,56 e al 90%
  fra 0,86 e 0,93 per **tutte** le categorie, cani lontani compresi (prima 0,04-0,25). Il
  gatto da appartamento resta dov'era (0,52 / 0,87-0,89): le sue particelle sono già fitte e
  σ vale quasi sempre il minimo, mezza cella.
- **C2** (stessi 200 casi, stessi semi): copertura al 90% del simulatore 0,85-0,95 (era
  0,48). Rapporto simulatore / anelli su tutte le verità: mediana 0,6-1,0, 90° percentile
  0,9-1,4. Per categoria sulla mediana: gatto da appartamento 0,3-0,7, gatto libero
  0,6-1,1, cane socievole 0,9-1,2, cani diffidente e pauroso 0,7-1,2. Verdetto previsto:
  **non batte, per poco**: la mediana scende sotto gli anelli, il 90° percentile no. In una
  zona uniforme la verità è isotropa: gli anelli la mediano sull'angolo gratis, il nucleo
  con 5.000 particelle ci aggiunge rumore nella coda.
Comando: scelta di α con uno script sul seme 7 (`map_coverage(n, 48, seed=7)` con
`make_grid(alpha=…)`); `python -m sim.validate --coverage`; `python -m sim.baseline`
(risultato in `out/phase-c2-kde.json`, 41 s).
Risultato — scelta di α (copertura al 50% / al 90%, 48 ore, seme 7): quasi piatta. Cani
lontani 0,47-0,50 / 0,874-0,883 da α = 0,5 a 2,0; gatto da appartamento 0,549 / 0,873-0,880;
cane socievole sale da 0,899 a 0,94 con α = 2,0. Scelto **α = 1,0**.
Risultato — C1 (seme 0, 50% / 90%): gatto da appartamento 0,557 / 0,892 (48 h) e 0,559 /
0,892 (7 g); gatto libero 0,505 / 0,892 e 0,505 / 0,893; cane socievole 0,511 / 0,898 (48 h);
cane diffidente 0,467 / 0,882 e 0,453 / 0,869; cane pauroso 0,481 / 0,874 e 0,486 / 0,876.
Sul seme 35 dei test, con 2.500-45.000 verità per mappa: 50% fra 0,46 e 0,54, 90% fra
0,86 e 0,91. Il 90% sta a 0,87-0,89 e non a 0,90 perché la regione si prende sulla massa
della griglia, il ~98% di quella libera (il resto è oltre il rettangolo).
Risultato — C2 (area prima della verità, mediana / 90° percentile in ettari; copertura al 90%):

| Categoria (verità) | Anelli | Simulatore | Rapporto p50 · p90 | Copertura anelli · sim |
|---|---|---|---|---|
| tutte (8.534) | 327 / 53.230 | **143 / 22.120** | **0,44 · 0,42** | 0,94 · 0,87 |
| gatto da appartamento | 6,3 / 324 | 1,6 / 149 | 0,26 · 0,46 | 0,95 · 0,87 |
| gatto libero | 51 / 71.132 | 71 / 23.158 | 1,40 · 0,33 | 0,95 · 0,88 |
| cane socievole (868; 12 casi senza particelle libere) | 2,3 / 10,8 | 2,1 / 10,7 | 0,94 · 1,00 | 0,94 · 0,91 |
| cane diffidente | 5.415 / 28.664 | 3.398 / 34.205 | 0,63 · 1,19 | 0,92 · 0,84 |
| cane pauroso | 7.628 / 58.723 | 3.171 / 50.506 | 0,42 · 0,86 | 0,94 · 0,88 |

Il simulatore cerca meno area degli anelli sul 67% delle verità.
Verdetto: **C2 superata**: su tutte le verità mediana e 90° percentile sotto gli anelli
(0,44 e 0,42). C1 regge: la mappa è una probabilità calibrata per tutte le categorie.
Previsioni: C1 giusta (tutte dentro 0,46-0,56 e 0,86-0,93 tranne il cane diffidente a 7
giorni al 50%, 0,453, dentro l'errore: 574 verità); scelta di α **sbagliata** (piatta, non
crescente: `lessons.md` #23); C2 **sbagliata** nel verdetto (previsto «non batte», batte:
`lessons.md` #24), giusta su copertura (0,87), cane socievole (0,94); sbagliata per difetto
su tutti i casi, gatto da appartamento e cani lontani (meglio del previsto), per eccesso sul
gatto libero (1,40 contro 0,6-1,1). Due punti deboli per categoria, da capire: il gatto
libero perde sulla mediana (il nucleo mette rumore nel cuore della sua distribuzione, dove
gli anelli mediano sull'angolo) e il cane diffidente sul 90° percentile (1,19).

### 2026-09-25 — C2″ riletta — misure senza gradini (`lessons.md` #26)
La mediana degli anelli è instabile: il loro secondo confine sta al 50%. Sugli **stessi 200
casi** (stessi semi) si leggono misure che non hanno gradini. Non c'era una previsione
scritta prima: è una rilettura, non una misura nuova.
Comando: script con `sim.baseline.run_case`, aree per verità (40 s).
Risultato (area da cercare, ettari; ultime due colonne: quota di verità dove il simulatore
cerca meno, media geometrica del rapporto simulatore / anelli):

| Categoria | Anelli p25 / p50 / p75 / p90 / media | Simulatore p25 / p50 / p75 / p90 / media | Sim < anelli | Rapporto geometrico |
|---|---|---|---|---|
| tutte | 6,2 / 327 / 6.832 / 53.230 / 91.685 | 2,9 / 143 / 3.887 / 22.120 / 92.162 | 0,67 | **0,56** |
| gatto da appartamento | 0,8 / 6,2 / 224 / 324 / 1.168 | 0,4 / 1,6 / 14 / 149 / 1.107 | 0,56 | 0,57 |
| gatto libero | 2,6 / 51 / 1.056 / 71.132 / 343.837 | 4,4 / 71 / 1.402 / 23.159 / 346.797 | 0,80 | 0,33 |
| cane socievole | 0,6 / 2,2 / 5,2 / 10,8 / 5,7 | 0,9 / 2,1 / 5,4 / 10,7 / 5,3 | 0,54 | 0,84 |
| cane diffidente | 1.546 / 5.415 / 23.757 / 28.664 / 17.434 | 982 / 3.398 / 11.465 / 34.205 / 16.860 | 0,63 | 0,81 |
| cane pauroso | 1.081 / 7.628 / 11.950 / 58.723 / 31.688 | 275 / 3.171 / 14.973 / 50.506 / 31.305 | 0,74 | 0,55 |

Verdetto: il simulatore vince in **tutte** le categorie sulla media geometrica (0,33-0,84)
e sulla quota (0,54-0,80); gatto libero e cane diffidente, che perdevano su un solo
quantile, vincono qui. La **media aritmetica** è pari (92.000 contro 92.000 ha): la fanno
le poche verità lontanissime, fuori da tutte e due le mappe, che costano uguale.

### 2026-09-25 — A5 — gatti a rischi in competizione (`lessons.md` #8)
Il gatto si legge al primo dei suoi eventi: a casa, raccolto, morto (dal motore) o trovato
fuori da chi lo cerca (solo nella taratura, rischio uguale a ogni distanza, costante nei
tratti 0-7, 7-30, 30-61 giorni). Si tarano insieme la curva dei trovati vivi di Huang, le
quote per luogo (20% a casa, 11% in casa d'altri) e i quantili della distanza.
Previsione, scritta prima di lanciare (conto a mano: sopravvivenza media nei tre tratti
0,8 / 0,55 / 0,45, il × 2 notturno di `h_home` e il suo calo dopo 30 giorni):
- `h_home`: gatto casa 1,1-1,8 · 10⁻⁴ /h (da 8,8 · 10⁻⁴: 5-8 volte più basso), gatto libero
  1,0-1,6 · 10⁻⁴ (da 7,5 · 10⁻⁴: 5-7 volte). `h_pickup` 0,9-1,8 · 10⁻⁴ (da 9,3 · 10⁻⁴).
- Rischio della ricerca: 2-3 · 10⁻³ /h nella prima settimana, 1-5 · 10⁻⁴ fino al giorno 30,
  0-2 · 10⁻⁴ dopo: nell'ultimo mese i ritorni a casa e le raccolte bastano quasi da soli.
- A: gatto casa accettato (errore ≤ 0,10); gatto libero fuori come prima (0,18-0,28).
  Ancora e passo entro ±20% di A4: le quote per luogo non cambiano, cambia solo l'ora in cui
  si legge chi torna a casa.
- B1: mediana mista 60-85 m (resta fuori); p25, p75 ed entro 500 m reggono.
- B2 (il motore, senza ricerca, misto 28:46): HOME entro 7 / 30 / 61 giorni 0,02-0,04 /
  0,08-0,14 / 0,13-0,20; HOME o HELD 0,03-0,06 / 0,12-0,20 / 0,20-0,30: sotto i trovati
  (0,34 / 0,50 / 0,56), lo `xfail` stretto diventa rosso. Controllo debole: la curva di
  Huang ora è un bersaglio della taratura (`lessons.md` #9).
- C1 invariata entro il rumore (0,46-0,56 e 0,86-0,93). C2 regge: rapporto p50 e p90
  0,35-0,55 su tutte, media geometrica 0,50-0,65, quota «cerca meno» 0,62-0,72.
Comando: `python -m sim.calibrate cat_indoor` e `cat_outdoor`, `python -m sim.validate`,
`python -m sim.validate --coverage`, `python -m sim.baseline`.
Risultato — A5 (`out/a5-calibrate.txt`): `h_home` 1,39 · 10⁻⁴ (gatto casa, 6,3 volte più basso)
e 1,43 · 10⁻⁴ (gatto libero, 5,3 volte); `h_pickup` 1,38 e 1,51 · 10⁻⁴. Ricerca 2,26 / 0,28 /
0,009 · 10⁻³ /h (casa) e 2,25 / 0,30 / 0,033 · 10⁻³ (libero). Quote dalle letture: a casa
0,197 e 0,196, raccolti 0,108 e 0,117, trovati vivi 0,567 e 0,566. Gatto casa 9,4 / 40,6 /
142,4 m, errore 0,05, **accettato** (ancora 49,5 m, dispersione 2,1, passo 25 m). Gatto
libero 18,0 / 242,6 / 1.457,6 m, errore 0,283, non accettato (ancora 540 m, dispersione 2,2,
passo **3 m**, era 1,8).
Risultato — B (`out/a5-validate.json`): B1 11,0 / 72,1 / 462,6 m (errori 0,225 / 0,442 /
0,075), entro 500 m 0,759; su altri semi il p25 va da 10,5 a 11,0, e con 65.000 gatti
l'intervallo a 4 errori standard è 9,3-11,7 contro il limite di 10,8: **al limite**, non
dimostrabile. B2, misto 28:46: HOME 0,030 / 0,118 / 0,170, HOME o HELD 0,045 / 0,172 /
0,266 contro 0,34 / 0,50 / 0,56: passa, anche il limite largo. B3 e B4 invariati (i cani
non sono cambiati).
Risultato — C1 (`out/a5-coverage.json`): gatto casa 0,551 / 0,893 (48 h) e 0,551 / 0,891
(7 g); gatto libero 0,501 / 0,891 e 0,497 / 0,888; cani invariati. C2 (`out/a5-baseline.json`,
8.534 verità): anelli 422 / 54.983 ha, simulatore 164 / 23.180; rapporto **0,39 · 0,42**,
media geometrica 0,55, cerca meno sul 67% delle verità, copertura al 90% 0,94 · 0,87. Gatto
casa 0,30 · 0,48 (geometrica 0,55), gatto libero 1,41 · 0,34 (0,33).
Verdetto: **il difetto #8 è tolto**: B2 passa con i rischi 5-6 volte più bassi, e C2 regge
(0,39 · 0,42). Previsioni giuste: i rischi (tutti e sei i numeri), B2 (sei su sei), C1, C2,
la mediana di B1, il gatto casa. Sbagliate: il gatto libero peggiora un poco oltre
l'intervallo (0,283 contro 0,18-0,28), il suo passo sale da 1,8 a 3 m (previsto entro
±20%), il p25 di B1 passa da 10,1 a 10,5-11,0 m, al limite (previsto «regge»). Nei test:
lo `xfail` di B2 è tolto; il p25 del gatto casa si prova a 100.000 gatti (`--runslow`); il
p25 di B1 diventa uno `xfail` stretto (`lessons.md` #28, #29).

### 2026-09-26 — L1 — il luogo in 3D, tre varianti sul luogo di prova (gatto di casa, primo piano, 24 ore)
Cosa: `python -m proto.luogo3d.variants privato/luogo-prova.json privato/luogo` (50.000 gatti,
seme 0; verità di C1 dal seme 1000). Variante 1 = motore di oggi; 2 = edifici e giardini;
3 = anche dislivelli e tetti (`simulatore.md`, «Il luogo in 3D — progetto»; `sel` da Hanmer
2017, porta · finestra da Huang, Tabella 4). Mappa fine a 4 m su ±600 m.
Previsione (scritta prima di lanciare):
- P1, distanze delle ancore: 2 e 3 uguali alla 1 entro il 2% su p25/p50/p75/p90 (per
  costruzione); quota senza anello (oltre la griglia) 0,11-0,13 (P(r > 580 m) = 0,12).
- P2, distanze dei gatti liberi a 24 ore: p25/p50/p75 di 2 e 3 entro il ±10% della 1; il
  p50 più corto per i passi rifiutati: 2 fra −8% e +3%, 3 fra −10% e +3%.
- P3, area della regione al 50%: 2 fra 0,65 e 0,90 volte la 1; 3 fra 0,55 e 0,90.
- P4, tipi delle ancore contro Huang, Tabella 6 (entro un fattore 2): `veg` 0,15-0,25 (Huang
  0,25), `garden`+`open` 0,40-0,55 (cortile 0,27: al limite), `edge` 0,20-0,30 (0,38),
  `street` 0,05-0,12 (0,10).
- P5, Manly entro 200 m: ancore della 2 come Hanmer entro ±0,05 (0,553 · 0,311 · 0,136);
  nella 3 il costruito più basso (0,20-0,30: i tetti si raggiungono poco); gatti liberi a
  24 ore diluiti verso 1/3: giardino 0,40-0,50, costruito 0,30-0,40, naturale 0,17-0,27;
  variante 1 circa 1/3 ciascuno (0,30-0,37).
- P6, C1 sulla mappa fine: nella regione al 50% cade 0,45-0,58 delle verità, al 75%
  0,70-0,80, in tutte e tre.
- P7, direzione: centro di massa dei liberi a meno di 5 m da casa nella 1, a 5-30 m nella
  2, a 10-40 m nella 3, spostato in discesa (a est) rispetto alla 2.
- Tempo: meno di 60 s in tutto.
Risultato (`privato/luogo/varianti-24h.json`, 2,8 s in tutto): P(libero) 0,994.
- P1 ✓: ancore 12,0 / 48,9 / 203,2 / 719,6 m nella 1, 12,1 / 48,9 / 202,9 / 719,6 nella 2 e 3;
  senza anello 0,130.
- P2 ✗: liberi a 24 ore 24,8 / 57,9 / 177,9 m (1), 18,9 / 48,4 / 153,8 (2), 19,0 / 48,6 / 153,0
  (3): la mediana **−16%**, fuori dal ±10%. Il passo rifiutato quando finisce in un edificio
  lascia il gatto dietro le case, lontano dall'ancora (`lessons.md` #33).
- P3 ✗: regione al 50% 1,04 ha (1), 0,44 (2), 0,45 (3): 0,43 volte, sotto 0,65 (in parte
  per P2: le distanze più corte).
- P4: ancore della 2 `veg` 0,09 ✗ (Huang 0,25: fuori dal fattore 2), `garden`+`open` 0,49 ✓
  (0,27: 1,8 volte), `edge` 0,27 ✓ (0,38), `street` 0,15 ✗ sulla previsione, ✓ sul fattore 2
  (0,10). Nella 1 (direzione a caso) il 28% delle ancore cade dentro un edificio.
- P5 ✗: Manly delle ancore della 2: giardino 0,651, costruito 0,282, naturale 0,067 (Hanmer
  0,553 · 0,311 · 0,136); nella 3 0,647 · 0,283 · 0,070; liberi 0,585 · 0,295 · 0,120; la 1
  0,419 · 0,466 · 0,115, non 1/3 ciascuno. La disponibilità del controllo conta gli edifici
  come costruito, dove nella 2 il gatto non può stare: il controllo non misura la stessa
  cosa del modello (`lessons.md` #34).
- P6 ✓: C1 0,495 / 0,745 (1), 0,472 / 0,730 (2), 0,476 / 0,728 (3).
- P7: centro di massa 5,3 m (1, ✗ di poco), 8,0 m (2 ✓), 4,0 m (3 ✗, previsto 10-40); la 3 sta
  1,5 m più a est della 2 (verso giusto, misura trascurabile).
- La 3 è quasi uguale alla 2: **nessun tetto** raggiungibile entro 200 m (0 celle), finestra
  66 celle contro 87, raggiungibilità media a terra 0,74 contro 0,84. Con altezze a 8 m di
  mediana e terreno a 10 m un tetto non è mai a portata di salto: i dislivelli visibili nei
  dati aperti di oggi cambiano poco (una premessa che dà quasi zero, `lessons.md` #35).
Verdetto: giuste P1, P6, il tempo; sbagliate P2, P3, P5, P7 per la 3, P4 su `veg`. Si corregge
il passo (sotto, L1b) prima di mandare le immagini.

### 2026-09-26 — L1b — le tre varianti con il passo corretto (`lessons.md` #33)
Cosa: come L1; il punto d'arrivo di un passo che cade dove il gatto non può stare si
sposta sulla cella libera più vicina (prima: passo rifiutato). Ancore invariate.
Previsione (scritta prima di lanciare):
- P1, P4 invariate (le ancore non cambiano).
- P2: liberi a 24 ore, p25/p50/p75 di 2 e 3 entro il ±10% della 1; la mediana fra −5% e +5%
  (sul luogo sintetico fitto: entro il 3%).
- P3: regione al 50% della 2 fra 0,50 e 0,75 volte la 1 (L1 0,43 con le distanze accorciate;
  il solo togliere gli edifici vale circa 0,67).
- P5b, Manly con disponibile = dove il gatto può stare (senza edifici): ancore della 2
  giardino 0,50-0,62, costruito 0,28-0,38, naturale 0,06-0,14 (la raggiungibilità pesa
  ancora il naturale); liberi più vicini a 1/3.
- P6: C1 dentro 0,45-0,58 e 0,70-0,80 in tutte e tre.
- P7b: distanza di variazione totale fra le mappe: 3 contro 2 sotto 0,10; 2 contro 1 fra
  0,30 e 0,50.
Risultato (`privato/luogo/varianti-24h.json`):
- P2 ✓: liberi a 24 ore 24,8 / 57,9 / 177,9 m (1), 24,7 / 58,0 / 179,1 (2), 24,8 / 57,8 / 179,4 (3).
- P3 ✓: regione al 50% 1,04 ha (1), 0,72 (2), 0,73 (3): 0,69 volte. Al 75%: 9,8 · 7,9 · 8,0 ha.
- P5b ✗: ancore della 2, disponibile senza edifici: giardino 0,500, costruito 0,448, naturale
  0,052. Ma la stessa lettura nella 1 (direzione a caso) dà 0,280 · 0,644 · 0,077: le ancore
  stanno vicino a casa, dove c'è più costruito, e un disco di 200 m non è la disponibilità
  giusta. Letta **contro la 1** (stessa distanza, cambia solo la direzione: lettura fatta
  dopo, non prevista): 1,79 · 0,70 · 0,68, standardizzati **0,56 · 0,22 · 0,21** contro Hanmer
  0,553 · 0,311 · 0,136: il giardino torna, il naturale esce più alto (`lessons.md` #36).
- Gatti liberi a 24 ore: 0,29 · 0,63 · 0,08 nella 2 contro 0,25 · 0,66 · 0,09 nella 1: la
  selezione delle ancore quasi non arriva alla mappa. In 24 ore il gatto fa circa 4 passi di
  25 m di mediana (media 41 m) con richiamo 0,5: il rumore del passo è grande quanto la
  distanza dell'ancora (mediana 49 m) e il passo non guarda il tipo di posto.
- P6 ✓: C1 0,495 / 0,745 (1), 0,481 / 0,741 (2), 0,481 / 0,741 (3).
- P7b: variazione totale 2 contro 1 **0,27** (✗, previsto 0,30-0,50), 3 contro 2 **0,05** ✓.
Verdetto: il passo corretto tiene le distanze (A e B1 reggono) e la mappa con gli edifici è
calibrata e più stretta del 31%. La direzione pesa poco: le ancore scelgono, il passo
diluisce. La 3 aggiunge poco ai dati aperti di oggi (#35). Prossima idea dai numeri: la
selezione anche nel passo (il moltiplicatore `stay` del motore per tipo di posto, tempo ∝
selezione), con le distanze da ricontrollare.
