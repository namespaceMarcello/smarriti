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

### 2026-09-26 — L2 — il luogo nel motore (variante 2) e la selezione anche nel passo
Cosa: il luogo passa da `proto/luogo3d/place3d.py` a `sim/place.py` e nel motore
(`Simulation(place=...)`, il caso accetta `"place": {"world": ...}`). Nuovo: la selezione nel
passo, `p_move × sel_ref / sel(tipo)` per i gatti, con `sel_ref` la media di `sel` sulle ancore
estratte con la direzione a caso (tiene la media di `p_move`); il tempo passato in un tipo di
posto va con `sel` (catena con attesa: occupazione ∝ disponibilità × 1 / `p_move`). Stesso luogo,
gatto, semi e 50.000 particelle di L1b.
Previsione (scritta prima di lanciare):
- L2a, senza luogo: il motore dà gli stessi bit di prima (impronta di 7 corse: 2 casi, 5
  categorie); la taratura A rifatta dà lo stesso `calibrated.json`; B, C1, C2 gli stessi numeri.
- L2b, `--no-step-selection`: identica a L1b alla cifra (stesso codice, stessi semi).
- L2c, con la selezione nel passo, variante 2:
  - P2: liberi a 24 ore entro il ±10% della 1, la mediana entro il ±5%;
  - P3: regione al 50% fra 0,60 e 0,72 ha (L1b 0,72);
  - P5c: posizioni dei liberi lette contro la 1, standardizzate: giardino 0,48-0,60,
    costruito 0,26-0,36, naturale 0,10-0,18 (Hanmer 0,553 · 0,311 · 0,136; L1b 0,38 · 0,32 ·
    0,30 circa). Il conto: le quote di L1b per `sel / sel_ref` per classe (1,45 · 1 · 0,44)
    danno 0,55 · 0,32 · 0,13;
  - P6: C1 dentro 0,45-0,58 e 0,70-0,80;
  - P7c: variazione totale 2 contro 1 fra 0,30 e 0,40 (L1b 0,27);
  - ancore lette contro la 1 come L1b (0,56 · 0,22 · 0,21): le ancore non cambiano.
Risultato (`privato/luogo/varianti-24h.json`, `-ancore.json`):
- L2a ✓: impronta uguale nelle 7 corse; `sim.calibrate all` rifà `calibrated.json` identico
  byte per byte; `validate`, `validate --coverage`, `baseline` identici a `out/a5-*.json`.
- L2b ✓: identica a L1b in ogni numero (distanze, C1, regioni, Manly, variazione totale).
- L2c, prima corsa (selezione anche sul posto di partenza): liberi 22,1 / 53,5 / 170,1 m
  contro 24,8 / 57,9 / 177,9 della 1: mediana −7,6%, p25 −11% (✗ P2). La porta cade su una
  cella `open` (sel 1,33): il gatto parte più tardi, chi non si è mai mosso in 24 ore sale
  dall'1,4% al 4,1%, i passi da 3,68 a 3,53 (`lessons.md` #38). Correzione: la selezione
  vale dal primo passo in poi.
- L2c, con la correzione (variante 2):
  - P2 ✓: 24,2 / 57,0 / 180,3 m (−2,4%, −1,6%, +1,3%); passi a testa 3,82 contro 3,68;
  - P3 ✓: regione al 50% 0,67 ha (0,72 con le sole ancore, 1,04 nella 1); al 75% 7,5 ha;
  - P5c ✗ sul giardino e sul costruito, ✓ sul naturale: posizioni contro la 1 **0,39 · 0,48 ·
    0,13** (Hanmer 0,553 · 0,311 · 0,136). La base scritta nella previsione era sbagliata:
    L1b letta con le stesse definizioni dà 0,30 · 0,47 · 0,24, non 0,38 · 0,32 · 0,30
    (`lessons.md` #39); dalla base giusta il conto (× 1,45 · 1 · 0,44) dà 0,43 · 0,47 · 0,10,
    vicino a quello misurato. Il costruito alto viene dai muri: il 42% dei gatti sta su una
    cella che tocca un edificio, contro il 21% della disponibilità entro 200 m;
  - P6 ✓: C1 0,474 / 0,739;
  - P7c ✗ di poco: variazione totale 2 contro 1 **0,29** (previsto 0,30-0,40); 3 contro 2 0,05;
  - ancore contro la 1 (quote a terra entro 200 m, la lettura nuova): 0,48 · 0,34 · 0,18;
    L1b le aveva lette su tutta la griglia (0,56 · 0,22 · 0,21): stesse ancore, due letture.
  - Quote per tipo delle posizioni entro 200 m contro Huang, Tabella 6 (prova 4, fattore 2):
    `edge` 0,45 (Huang 0,38 ✓), `open` + `garden` 0,36 (0,27 ✓), `street` 0,16 (0,10 ✓),
    `veg` 0,03 (0,25 ✗): il «sotto la vegetazione» di Huang sono cespugli nei giardini, che a
    10 m finiscono in `open`.
- `python -m sim` su un caso con il luogo (privato): mappa a 4 m, 0,90 della massa dei liberi
  nel quadrato di ±600 m a 24 ore, 0,8 s.
Verdetto: il luogo è nel motore e senza luogo il motore non cambia. La selezione nel passo
stringe la mappa di un altro 7% (0,72 → 0,67 ha) tenendo distanze e calibrazione; il
naturale torna con Hanmer. Restano due scarti, tutti e due di dati o di regola, non di
studio: i muri (la regola del passo contro gli edifici raddoppia la massa a ridosso) e la
vegetazione di Huang (cespugli che a 10 m non si vedono). Prossima idea dai numeri: il passo
che finisce dentro un edificio si rilancia invece di fermarsi al muro (misura: la quota a
ridosso dei muri e le distanze), e la chioma a 1 m da satellite per vedere i cespugli.

### 2026-09-26 — L3 — il passo che finisce dentro un edificio si rilancia
Cosa: come L2c (con la selezione nel passo); un passo che finisce dove il gatto non può stare
si rilancia (nuova lunghezza e nuova svolta dalla stessa posizione, con il richiamo
all'ancora) fino a 5 volte, su un flusso di numeri separato; se non basta, la cella libera
più vicina come in L2. Perché: in L2 il 42% dei gatti sta a ridosso di un edificio contro il
21% della disponibilità, e il costruito esce 0,48 contro 0,31 di Hanmer (GPS, il tempo vero);
Huang (dove sono stati trovati, cioè dove si cerca) dà `edge` 0,38.
Previsione (scritta prima di lanciare):
- a ridosso di un edificio (entro 200 m): da 0,42 a 0,22-0,30;
- posizioni contro la 1: giardino 0,45-0,52, costruito 0,33-0,42, naturale 0,12-0,16;
- liberi a 24 ore: mediana entro il ±5% della 1, p25 e p75 entro il ±10%;
- C1 dentro 0,45-0,58 e 0,70-0,80; regione al 50% fra 0,60 e 0,70 ha; variazione totale 2
  contro 1 fra 0,28 e 0,35.
Risultato (`privato/luogo/varianti-24h.json`), variante 2:
- a ridosso di un edificio entro 200 m **0,19** (✗ di poco, previsto 0,22-0,30; la
  disponibilità è 0,21; in L2 0,42);
- posizioni contro la 1 **0,50 · 0,34 · 0,16** ✓ ✓ ✓ (Hanmer 0,553 · 0,311 · 0,136);
- liberi a 24 ore 23,4 / 56,6 / 180,9 m: mediana −2,2% ✓, p25 −5,6% ✓, p75 +1,7% ✓;
- C1 0,472 / 0,731 ✓; regione al 50% **0,59 ha** (✗ di poco, previsto 0,60-0,70); al 75%
  6,5 ha; variazione totale 2 contro 1 **0,33** ✓; 3 contro 2 0,07;
- quote per tipo entro 200 m contro Huang, Tabella 6 (fattore 2): `edge` 0,25 (0,38 ✓),
  `open` 0,50 (0,27 ✓), `street` 0,21 (0,10: fattore 2,1 ✗), `veg` 0,04 (0,25 ✗, i cespugli).
- Sul paese sintetico fitto (`test_place3d.py`): a ridosso dei muri 1,36 volte la
  disponibilità con la cella libera più vicina, 0,76 con il rilancio. Rilanciare dal punto di
  partenza dà un'occupazione proporzionale alla parte libera a portata di un passo (catena con
  il nucleo ristretto: `matematica.md`), un po' sotto la disponibilità dove è fitto; sul luogo
  di prova 0,91.
Verdetto: il rilancio toglie l'ammucchiamento contro i muri e porta le posizioni sui numeri di
Hanmer (GPS: il tempo vero), tenendo distanze e calibrazione. Entra nel motore come regola
(`redraw` = 5). La mappa si stringe ancora: al 50% da 1,04 (la 1) a 0,59 ha. Restano la
vegetazione di Huang (cespugli nei giardini, invisibili a 10 m) e le strade un po' alte.

### 2026-09-26 — L5 — il luogo punta dove stanno i gatti veri? (protocollo, scritto prima dei dati)
Cosa: la parte «direzione» del modello (la stessa del motore: a distanza r, la densità
sull'anello va con `w = sel(tipo) × reach`, `Place.weight`) contro le posizioni GPS di gatti
di casa veri: Cat Tracker (Kays et al. 2020, Movebank, CC0; `riferimenti.md` §B). Gatti
residenti, non smarriti: si prova solo la direzione (edifici, giardini, strade), non le
distanze. Prova pilota: il dataset del Regno Unito (se non va, gli Stati Uniti), fino a 40
gatti con almeno 100 posizioni, scelti per numero di posizioni. Il luogo di ogni gatto da
OpenStreetMap, ±300 m, celle da 2 m; la casa dalla posizione di partenza del dataset o,
se manca, dalla cella da 10 m con più posizioni.
Unità: il **gatto** (le posizioni dello stesso gatto non sono indipendenti).
Punteggio: per ogni posizione a 20-280 m da casa, `G = log(w_s(x) / w̄_s(r))`, il guadagno
in logaritmo della mappa con il luogo sulla mappa radiale alla stessa distanza (`w_s`: `w`
lisciato con σ = 10 m per l'errore del GPS, stima; più l'1% della media dell'anello, così
nessuna posizione vale −∞; `w̄_s`: la media sull'anello da 2 m). `S_c` = media di G sulle
posizioni del gatto c, in nat per posizione.
Nullo: la stessa mappa ruotata attorno a casa di un angolo a caso (999 angoli per gatto): le
distanze restano identiche, si perde solo la direzione.
Test: `D` = media sui gatti di (`S_c` − media delle `S_c` ruotate); p per permutazione (9.999
estrazioni, un angolo a caso per gatto): p = (1 + #{D* ≥ D}) / 10.000. **Significativo se
p < 0,001** (una coda). Si riportano anche la quota di gatti con il proprio p < 0,05 (5% se il
luogo non conta) e le quote per classe di Hanmer delle posizioni contro le ruotate.
Previsione:
- D fra 0,05 e 0,30 nat per posizione, p < 0,001;
- gatti con il proprio p < 0,05: fra il 30% e il 60%;
- quote contro le ruotate, standardizzate: giardino 0,40-0,55, costruito 0,25-0,40, naturale
  0,15-0,30.
Se p ≥ 0,001: il luogo, così com'è, non punta dove stanno i gatti; si scrive e si smonta
pezzo per pezzo (edifici come muri, selezione, raggiungibilità) prima di scartarlo.
Risultato del pilota (`privato/dati/cattracker/score.json`): dal dataset del Regno Unito
(101 gatti, posizioni ogni 3 minuti, nessuna colonna di errore del GPS, nessun punto di
casa: la casa è la cella da 10 m con più posizioni) sono stati costruiti 6 luoghi su 14
candidati (8 senza un edificio di OSM entro 30 m dalla casa stimata; Overpass ha smesso di
rispondere dopo 14 richieste); un gatto ha meno di 20 posizioni fra 20 e 280 m. **5 gatti.**
- D = **0,030** nat per posizione (✗, previsto 0,05-0,30); **p = 0,053** (✗, soglia 0,001):
  **non significativo**. Il segno va nel verso previsto: 4 gatti su 5 sopra la media delle
  proprie rotazioni (Teddy sotto, p proprio 0,89);
- gatti con il proprio p < 0,05: 1 su 5 (✗, previsto 30-60%);
- quote contro le ruotate, standardizzate: giardino 0,39 (✗ di poco, previsto 0,40-0,55),
  costruito 0,36 ✓, naturale 0,25 ✓.
Verdetto: il pilota non dimostra niente, né a favore né contro: 5 gatti sono troppo pochi.
La dispersione fra gatti (scarto tipo delle differenze 0,056) dice che per un effetto di 0,03
a p < 0,001 servono circa 35 gatti, circa 55 con la regola dei 4 errori standard.

**Il test vero, fissato prima di scaricare altri gatti**: tutti i gatti del Regno Unito con
almeno 100 posizioni (72), con il luogo costruito dove c'è un edificio di OSM entro 30 m
dalla casa stimata, stesso punteggio, stesse rotazioni, stessa soglia p < 0,001; **un solo
lancio**, qualunque sia il numero di gatti che ne esce, e il risultato si scrive comunque.
Niente aggiunte dopo aver visto il risultato (fermarsi quando torna significativo gonfia il
falso positivo). Previsione: D fra 0,01 e 0,06, p < 0,001 se i gatti sono almeno 35.
Risultato del test vero (`privato/dati/cattracker/score-confirmatory.json`, un solo lancio):
72 gatti controllati, 46 luoghi costruiti (26 senza un edificio di OSM entro 30 m dalla casa
stimata), 45 con almeno 20 posizioni fra 20 e 280 m.
- D = **0,021** nat per posizione ✓ (previsto 0,01-0,06): alle posizioni vere la mappa con il
  luogo dà in media il 2% di densità in più della stessa mappa ruotata;
- **p = 0,030** ✗ (soglia 0,001): **non significativo**;
- gatti con il proprio p < 0,05: 11% (5% se il luogo non conta);
- quote contro le ruotate, standardizzate: giardino 0,38, costruito 0,34, naturale 0,29
  (quasi neutre: un terzo ciascuna);
- scarto fra gatti 0,088: per dimostrare un effetto di 0,021 a p < 0,001 servono circa 165
  gatti.
Verdetto: **il luogo, così com'è, non è dimostrato sui gatti veri.** Se c'è, l'effetto è
piccolo (2% di densità in più). Quindi la mappa più stretta di L3 (al 50% 0,59 ha invece
di 1,04) non è sostenuta dai dati veri: è coerente con il modello (C1), non con i gatti.
**Correzione (2026-09-26, dopo L6)**: i gatti con almeno 20 posizioni erano 46, non 45. Uno
(247 posizioni utili) è stato saltato in silenzio da un difetto: il nome con uno spazio, la
cartella con il trattino basso (`lessons.md` #45). Riletto con lui, non un secondo lancio:
D = 0,028, p = 0,009 (`score-L5-46cats.json`): il verdetto non cambia.
Prossimo, dichiarato esplorativo (non un altro test di conferma sugli stessi gatti): smontare
il luogo pezzo per pezzo sui 45 gatti (solo edifici come muri, solo la selezione, solo la
raggiungibilità, senza la lisciatura) per vedere quale pezzo porta il segnale e quale lo
toglie; poi un test di conferma nuovo, con il suo protocollo, sui gatti di Stati Uniti,
Australia e Nuova Zelanda (gli stessi dati CC0), con il numero di gatti calcolato prima.

### 2026-09-26 — L6 — smontare il luogo sui gatti veri (**esplorativo**, scritto prima di lanciare)
Cosa: il punteggio di L5 sugli stessi 45 gatti, con le stesse rotazioni e le stesse estrazioni
del nullo (seme 0), un pezzo della mappa alla volta (`proto/gps/pieces.py`). Le mappe, prima
della lisciatura: `walls` (1 fuori dagli edifici, 0 dentro), `sel` (la selezione di Hanmer
ovunque, l'edificio vale 1), `walls_sel`, `reach` (la raggiungibilità: gli edifici sono già
irraggiungibili), `reach_noroads` (ogni strada costa la sua lunghezza: restano solo i giri
attorno agli edifici), `full_noroads`, `full` (la mappa di L5 e del motore); ognuna lisciata
con σ 0, 5, 10, 20 m. In più le quote delle posizioni per tipo di posto e per distanza
dall'edificio più vicino, contro le ruotate. Sono 28 mappe sugli stessi gatti: **nessun p di
questa voce conferma niente**, serve a scegliere la mappa per la conferma (L7).
Base (`privato/dati/cattracker/score-confirmatory.json`): `full` a 10 m D = 0,0212, p = 0,030,
scarto fra gatti 0,088; quote vere contro ruotate: giardino e aperto 0,558 contro 0,521,
costruito (bordo, strada, edificio) 0,367 contro 0,385, naturale 0,075 contro 0,094.
Previsioni:
- P1 (integrità): `full` a 10 m ridà L5 al bit: D = 0,0212, p = 0,0302;
- P2 (i pezzi a 10 m, D in nat per posizione): `walls` 0,000-0,025; `sel` 0,000-0,025;
  `walls_sel` 0,005-0,030; `reach` 0,000-0,030; senza le strade entro 0,010 dalle stesse
  mappe con le strade; nessuna mappa a p < 0,001;
- P3 (la lisciatura, `full`): σ 20 m 0,010-0,035; σ 5 m da −0,02 a 0,03; σ 0 da −0,05 a
  +0,15, deciso dalle posizioni dentro gli edifici (−4,6 nat l'una): sale se i gatti veri ci
  cadono meno delle ruotate; lo scarto fra gatti a σ 0 almeno il doppio di quello a 10 m;
- P4 (tipi di posto, vere su ruotate): `veg` 0,80 (è il naturale di L5); edificio (`roof`)
  0,80-1,00; strada 0,75-0,95; bordo 0,90-1,10; aperto 1,00-1,12; giardino di OSM (parchi
  compresi) 0,80-1,30;
- P5 (distanza dall'edificio più vicino, vere su ruotate): dentro 0,80-1,00; 3-6 e 6-12 m
  1,00-1,15; oltre 24 m 0,70-1,00.
Regola per la mappa della conferma, fissata prima: resta `full` a 10 m (la mappa del motore)
a meno che un'altra la superi di più di 2 errori standard appaiati (`vs_full10`); allora si
prende quella con lo scarto appaiato più alto, e il motore cambia solo se L7 la conferma.
Comando: `python -m proto.gps.pieces privato/dati/cattracker` (scrive `pieces.json`).
Risultato (`privato/dati/cattracker/pieces-L6.json`, 45 gatti, 7 s; D in nat per posizione):
- P1 ✓: `full` a 10 m ridà L5 al bit (D 0,0212, p 0,0302);
- P2 ✓: a 10 m `walls` 0,0074, `sel` 0,0192, `walls_sel` 0,0259, `reach` 0,0028; senza le
  strade 0,0014 e 0,0199; a 10 m nessuna mappa sotto p 0,001 (la più bassa 0,0055);
- P3: σ 20 m 0,0135 ✓; **σ 5 m 0,0383 ✗** (previsto fino a 0,03); σ 0 0,1057 ✓, scarto fra
  gatti 0,226 contro 0,088 ✓. **Meno lisciatura, più segnale**, fino a σ 0: l'errore del GPS
  non cancella la forma degli edifici a 2 m;
- P4: `veg` 0,81 ✓; edificio 0,88 ✓ (z −2,9); bordo 0,92 ✓; aperto 1,07 ✓ (z +2,4); **strada
  1,09 ✗** (previsto 0,75-0,95); giardino 1,32 ✗ di poco (lo 0,4% delle posizioni: rumore);
- P5 ✓: dentro 0,88; 0-3 m 0,94; 3-6 m 1,10; 6-12 m 1,06; 12-24 m 1,00; oltre 24 m 0,98. Le
  posizioni vere stanno a 3-12 m dagli edifici (i giardini accanto alle case), meno dentro e
  a ridosso;
- i pezzi appaiati sugli stessi gatti: gli edifici come muri, data la selezione, +0,086 a
  σ 0 (z 2,9), +0,021 a 5 m (z 2,7), +0,007 a 10 m; la raggiungibilità **toglie** 0,005 a
  ogni σ (z da −0,5 a −1,1); il costo delle strade 0,000 (z 0);
- la regola: superano `full` a 10 m di più di 2 errori standard appaiati 9 mappe; lo scarto
  appaiato più alto è `walls_sel` a σ 0 (+0,090, z 3,1), che ha anche l'effetto per gatto
  più alto (D sullo scarto fra gatti 0,50, contro 0,24 della mappa del motore). **Per L7:
  `walls_sel`, σ 0.** Con il gatto recuperato (46, `pieces.json`) la scelta non cambia:
  `walls_sel` σ 0 D 0,113 (errore 0,032, scarto 0,217), +0,084 su `full` a 10 m.
Verdetto: sui gatti veri il segnale del luogo sta negli **edifici come muri** e nella
**selezione di Hanmer**; la raggiungibilità (i giri attorno agli edifici, il costo delle
strade) non ne porta, anzi ne toglie un poco. Esplorativo: la conferma è L7. Una riserva
sulla lettura, **corretta lo stesso giorno** dagli studi sul GPS (`riferimenti.md`, «Il GPS dei
gatti»): sotto gli alberi il fix riesce (circa 100%, 2 m di errore in più), quindi la quota di
`veg` sotto 1 è del gatto; a ridosso degli edifici si perde un fix su quattro e in casa
quattro su cinque, quindi il bordo (0,92) e l'edificio (0,88) sotto 1 possono essere in parte
del GPS. Per un gatto smarrito nascosto in un garage o sotto un portico conta il gatto.

### 2026-09-26 — L7 — il luogo sui gatti di Stati Uniti, Australia e Nuova Zelanda (conferma; protocollo scritto prima del punteggio)
Cosa: la mappa scelta in L6 (`walls_sel`: la selezione di Hanmer sulle celle fuori dagli
edifici, 0 dentro, senza raggiungibilità; σ 0; il pavimento all'1% della media dell'anello
come in L5) contro le posizioni GPS di gatti di casa che non hanno toccato la scelta: Cat
Tracker di Stati Uniti (`move.885`), Australia (`move.876`) e Nuova Zelanda (`move.879`), CC0.
Dati (scaricati e in costruzione mentre si scrive; nessun punteggio calcolato): i gatti con
almeno 100 posizioni tenute dagli autori sono 571 (135 · 300 · 136). Nei tre file circa il 90%
delle righe è nascosto dagli autori (`visible` falso): sono più vicine a casa (mediana 18-22 m
contro 26-30 delle visibili) e in un gatto guardato ora per ora sono i periodi da fermo, in
grappoli di ±20 m; il file del Regno Unito era già pubblicato senza (98% visibili, ~180 righe
per gatto). Si punteggiano **solo le posizioni visibili**; **la casa è la cella da 10 m con più
righe, nascoste comprese** (il gatto fermo in casa: con le sole visibili la casa si sposta di
10 m in mediana e di 30-48 m in un gatto su dieci). Il luogo da OSM come per il Regno Unito
(±320 m, celle da 2 m); si tiene il gatto se c'è un edificio di OSM entro 30 m dalla casa e
se ha almeno 20 posizioni fra 20 e 280 m.
Test: come L5 (999 rotazioni per gatto, 9.999 permutazioni, seme 0), **significativo se
p < 0,001**, una coda. **Un solo lancio**, con tutti i gatti che passano i filtri, qualunque
sia il loro numero; niente aggiunte né cambi dopo il risultato. Il JSON registra l'impronta
dei dati letti (`inputs_sha1`).
Numero di gatti, con il margine di #42 (sui 46 gatti di L6): l'effetto al limite basso del suo
intervallo al 95% (0,113 − 1,96 × 0,032 = 0,050: assorbe anche parte del vantaggio di aver
scelto la migliore fra 28 mappe), lo scarto fra gatti al limite alto (0,217 → 0,273): per
l'80% di potenza a p < 0,001 servono **464 gatti** (con i valori puntuali 58). Se ne
aspettano 350-450 buoni: potenza al margine 63-78%, ai valori puntuali ~100%. Un risultato
non significativo quindi non basta a dire che il luogo non conta: si leggerà con
l'intervallo di D.
Previsione:
- D fra 0,03 e 0,12 nat per posizione, **p < 0,001** (la scelta fra 28 gonfia lo 0,113 di L6;
  nei quartieri con lotti più larghi gli edifici sono meno e il segnale dei muri scende con
  loro);
- gatti con il proprio p < 0,05: 10-30%;
- secondari, solo descrittivi (`pieces.py` sulla stessa cartella, e D per paese): la mappa del
  motore (`full`, 10 m) D 0,005-0,04; la raggiungibilità di nuovo sotto zero appaiata; le
  posizioni dentro gli edifici 0,80-0,95 delle ruotate.
Cosa segue: p < 0,001 → il luogo punta dove stanno i gatti veri; nel motore le ancore pesano
`sel` sulle celle libere, senza la raggiungibilità (si rifanno L2-L3 e l'impronta senza luogo).
p ≥ 0,001 → non confermato: la mappa più stretta non si presenta come più precisa.
**Correzione al protocollo (stesso giorno, prima del lancio, nessun punteggio visto)**: i gatti
non sono indipendenti. Fra i 571 candidati le case sono 497 (case a meno di 20 m: 53 coppie,
7 terne, una da 4, una da 5), e i gatti di una casa girano negli stessi giardini: ruotarli
separatamente stringe il nullo e dà p troppo piccoli (`lessons.md` #48). Quindi **i gatti
della stessa casa ruotano insieme**, con gli stessi angoli, e il nullo estrae un angolo per
casa; D resta la media sui gatti. Riletto così il Regno Unito (46 gatti, 37 case): mappa del
motore p 0,011 invece di 0,009; `walls_sel` σ 0 p 0,0015 invece di 0,001, errore di D con le
case come unità 0,030 invece di 0,032: la potenza calcolata sopra regge.
Comando: `python -m proto.gps.score privato/dati/cattracker-conferma --map walls_sel --sigma 0
--households 20`.
Risultato (un solo lancio, `privato/dati/cattracker-conferma/score.json`, `inputs_sha1`
25233a1c…): 571 gatti, 399 luoghi costruiti (172 senza un edificio di OSM entro 30 m),
nessun errore del server, nessuna risposta con `remark`; **391 gatti in 345 case**.
- D = **0,076** nat per posizione ✓ (previsto 0,03-0,12); **p = 0,0001** ✓ (soglia 0,001):
  **significativo**. Errore di D con le case come unità 0,014;
- gatti con il proprio p < 0,05: 10,0% ✓ (al limite basso di 10-30%);
- secondari (`pieces.json`, descrittivi): la mappa del motore (`full`, 10 m) D 0,009 ✓
  (0,005-0,04), p 0,007; la raggiungibilità appaiata a 10 m +0,002 ± 0,002 ✗ (prevista sotto
  zero: qui è neutra); dentro gli edifici 0,90 delle ruotate ✓ (0,80-0,95). Quasi tutto il
  segnale viene dai muri: `walls` da sola a σ 0 dà 0,074, `sel` da sola 0,005. Per paese:
  Australia 0,138 ± 0,022 (148 gatti), Nuova Zelanda 0,061 ± 0,027 (123), **Stati Uniti
  0,016 ± 0,016 (120), non distinguibile da zero** (lotti larghi, pochi edifici vicini).
Verdetto: **il luogo punta dove stanno i gatti veri**, confermato su gatti che non hanno
toccato la scelta: alle posizioni vere la mappa con edifici come muri e selezione dà l'8% di
densità in più della stessa mappa ruotata. Il segnale è soprattutto «non dentro gli edifici»
(con l'errore del GPS a ridosso dei muri, `riferimenti.md`), la selezione aggiunge poco, e
negli Stati Uniti non si vede. La raggiungibilità: in L6 toglieva un poco, qui è neutra.

### 2026-09-26 — L8 — cosa aggiunge il LiDAR a 1 m sul luogo di prova (scritto prima di lanciare)
Cosa: il LiDAR della Città Metropolitana (2009, 32 tessere DTM e 32 DSM del riquadro
arrotondato) nel mondo del luogo (`dtm1`, `dsm1`, `hmax1`: il motore non li legge), entro
200 m da casa: il terreno contro TINITALY a 10 m, l'altezza delle cose sopra il suolo fuori
dagli edifici (`hmax1`, la più alta dei quattro pixel della cella), e quanto del luogo si
raggiunge con le altezze (variante 3) quando il terreno è quello a 1 m e ogni tetto sta alla
sua superficie misurata.
Base (L1, variante 3 con TINITALY e 3D-GloBFP): nessun tetto raggiungibile entro 200 m,
raggiungibilità media a terra 0,74 (0,84 nella variante 2); altezza mediana degli edifici
8,0 m (`world.npz`).
Previsioni:
- P1 (integrità): variante 2 0,84 ± 0,02, variante 3 con TINITALY 0,74 ± 0,02, tetti 0;
- P2 (terreno): scarto mediano da TINITALY 0,3-1,5 m, al 95° percentile 2-6 m; celle libere
  vicine con più di 1,5 m di salto: 0,5-5% con il LiDAR, sotto lo 0,1% con TINITALY;
- P3 (sopra il suolo, fuori dagli edifici): sotto 0,3 m 25-45%; 0,3-1,5 m 10-20%; 1,5-4 m
  10-25%; da 4 m 20-40%;
- P4: altezza mediana degli edifici dal LiDAR entro 2 m da 8,0;
- P5 (variante 3 con il LiDAR): tetti raggiungibili 2-20%; terra raggiungibile 85-100%;
  raggiungibilità media a terra da 0,59 a 0,74.
Comando: `python -m proto.luogo3d.metre privato/luogo-prova.json privato/luogo` (scrive
`metre.json`).
Risultato (`privato/luogo/metre.json`; i livelli che il motore legge restano identici al bit):
- P1 ✓: variante 2 0,835, variante 3 con TINITALY 0,736, tetti 0;
- P2: scarto mediano da TINITALY **2,6 m ✗** (previsto 0,3-1,5), al 95° percentile **10,1 m
  ✗** (previsto 2-6); non è uno spostamento (spostando TINITALY fino a ±8 m scende solo a
  2,3 m, senza un minimo): è TINITALY in collina, che a 10 m non vede tagli, terrazzamenti e
  riempimenti. Salti di oltre 1,5 m fra celle libere vicine 1,6% ✓ (0 con TINITALY ✓);
- P3: sotto 0,3 m 22% ✗ (previsto 25-45), 0,3-1,5 m 14% ✓, 1,5-4 m 29% ✗ (previsto
  10-25), da 4 m 35% ✓: fuori dagli edifici due celle su tre hanno qualcosa sopra 1,5 m
  (alberi, muri, siepi, tettoie). `hmax1` prende il più alto dei quattro pixel: sta in alto;
- P4 ✓ alla lettera, non nella sostanza: 7,7 m contro 8,0, ma 8,0 è la mediana per edificio e
  la misura è per cella; sulle stesse celle 3D-GloBFP e OSM danno 10,7 m. Il LiDAR vede gli
  edifici 3 m più bassi (i bordi mezzo tetto e mezzo suolo abbassano; nel 2009 mancano i piani
  aggiunti dopo). Base con un'altra definizione: `lessons.md` #39 di nuovo;
- P5: tetti raggiungibili per cella **23% ✗** (previsto 2-20%), gonfiato dai bordi: una cella
  da 2 m sul bordo di un'impronta mescola tetto e suolo e fa scalini che non ci sono. Con ogni
  tetto piano alla quota mediana del suo edificio (`variant3_lidar_flat_roofs`) **9%** delle
  celle (5,7% di quelle interne), **49 edifici su 221** ✓; terra raggiungibile 99,97% ✓;
  raggiungibilità media a terra 0,68 ✓.
Verdetto: il LiDAR rimette in gioco la variante 3 (`lessons.md` #35): con il terreno a 1 m un
edificio su cinque entro 200 m ha il tetto a portata di salto, e la raggiungibilità a terra
scende da 0,74 a 0,68 (i terrazzamenti si scendono, non si salgono). Ma sui gatti veri la
raggiungibilità non porta segnale (L6): prima di accendere la 3 serve una prova che tetti e
salti contino (uno studio, o gatti GPS in collina). I dati derivati restano in `privato/`
(CC BY-SA 4.0).
**L8b — le altezze degli edifici, per edificio** (previsione scritta prima): entro 200 m,
esclusa la casa, per ogni edificio con almeno 4 celle interne (l'impronta ristretta di una
cella, niente bordi), l'altezza del mondo (`bh`: 3D-GloBFP, o per quelli aggiunti da OSM i
piani × 3 m o la mediana del posto) meno la mediana di `dsm1 − dtm1` sulle celle interne.
Previsione: mediana della differenza da +1 a +4 m per gli edifici di 3D-GloBFP (i 3 m di P4
vengono in parte dai bordi, che qui non ci sono); correlazione fra le due altezze 0,3-0,7;
per quelli aggiunti da OSM la dispersione più larga.
Risultato (`metre.json`, `building_height_per_building`): 119 edifici di 3D-GloBFP, mediana
**+2,5 m** ✓ (quartili −0,1 e +4,4), correlazione **0,48** ✓; 8 aggiunti da OSM, mediana
+0,9 m, quartili −2,4 e +4,5 ✓ (più larghi; tutti con la stessa altezza, la mediana del
posto, quindi nessuna correlazione). Verdetto: dove il LiDAR c'è, le altezze di 3D-GloBFP
sono alte di 2,5 m e spiegano meno di un quarto della varianza (0,48²): per la variante 3 le
altezze si prendono dal LiDAR (misura diretta, del 2009), 3D-GloBFP resta per gli edifici
nuovi e fuori provincia.

### 2026-09-26 — L9 — il motore dopo L7: le ancore pesano `sel` sulle celle libere, senza la raggiungibilità (scritto prima di lanciare)
Cosa: `Place.weight` passa da `sel × reach` sulle superfici a `sel` sulle celle dove il gatto
può stare (`ok`); la vecchia regola resta con `PlaceParams(reach_weight=True)`. Stesso banco di
L2-L3 (`proto.luogo3d.variants`, 50.000 gatti, 24 ore, primo piano, semi 0 e 1000).
Base, letta ora con le stesse definizioni (`--reach-weight`, identica a L3 al bit, #39):
variante 2 liberi 23,4 / 56,6 / 180,9 m; C1 0,472 / 0,731; regione al 50% 0,59 ha, al 75%
6,5 ha; contro la 1 0,503 · 0,337 · 0,160; tipi entro 200 m `veg` 0,035 · `edge` 0,250 ·
`open` 0,503 · `street` 0,212; a ridosso di un muro (cella libera che tocca un edificio, 8
vicini) 0,275 contro 0,280 di disponibilità; variazione totale 2 contro 1 0,329. Variante 3:
regione al 50% 0,59 ha, a ridosso 0,280.
Previsioni:
- P1: senza luogo l'impronta (`sim.fingerprint`) identica nelle 7 corse;
- P2: distanze dei liberi entro ±3% della base (le ancore restano sull'anello: cambia solo la
  direzione); C1 dentro 0,45-0,58 e 0,70-0,80;
- P3: la mappa si allarga un poco (le celle raggiunte solo con giri, reach < 1, pesano di più):
  regione al 50% 0,59-0,70 ha; variazione totale 2 contro 1 fra 0,26 e 0,33;
- P4: quote per tipo e contro la 1 ciascuna entro ±0,03 della base; a ridosso 0,26-0,30;
- P5: variante 3 (reach media a terra 0,74 contro 0,84) cambia più della 2: variazione totale
  3 contro 2 sopra 0,068.
Risultato (`privato/luogo/varianti-24h.json`; la base in `varianti-24h-reach.json`):
- P1 ✓: impronta identica nelle 7 corse;
- P2 ✓: variante 2 liberi 23,4 / 56,7 / 180,6 m (0%, +0,2%, −0,2%); C1 0,472 / 0,731;
- P3 ✓ al limite: regione al 50% 0,590 ha (base 0,586), al 75% 6,47; variazione totale 2
  contro 1 0,328;
- P4 ✓: contro la 1 0,500 · 0,339 · 0,161; tipi `veg` 0,035 · `edge` 0,252 · `open` 0,501 ·
  `street` 0,213; a ridosso 0,277;
- P5 ✗: variazione totale 3 contro 2 **0,056** (prevista sopra 0,068): senza la raggiungibilità
  la 3 si avvicina alla 2 invece di allontanarsene (la differenza fra le due stava soprattutto
  nella raggiungibilità, e ora nessuna delle due la usa nelle ancore).
Verdetto: sul luogo di prova togliere la raggiungibilità non cambia quasi niente (ogni numero
entro l'1%): la regola del motore si semplifica come dice L7 senza perdere nulla. La
raggiungibilità resta calcolata (dice dove un gatto può stare, `ok`) ma non pesa più.

### 2026-09-26 — L10 — perché gli Stati Uniti non danno segnale in L7 (**esplorativo**, scritto prima di guardare)
Cosa: sui 391 gatti di L7 (`privato/dati/cattracker-conferma/pieces.json`, nessun lancio nuovo),
per paese: la quota delle posizioni ruotate dentro un edificio (quanto costruito c'è attorno:
la copertura di OSM alle distanze del gatto), la stessa per le posizioni vere, il loro
rapporto, e quanto di D viene dai gatti con poco costruito attorno.
Previsione: negli Stati Uniti le ruotate dentro gli edifici sono meno della metà che in
Australia (lotti larghi, o OSM con meno edifici); il rapporto vere/ruotate è simile nei tre
paesi (0,8-0,95: il gatto evita gli edifici ovunque), quindi il segnale basso degli Stati Uniti
viene dal poco costruito, non da gatti diversi; D per gatto cresce con la quota ruotata dentro.
Risultato (D = `walls_sel 0` per gatto, media per gruppo):
- ruotate dentro gli edifici: Stati Uniti **0,101**, Australia 0,168, Nuova Zelanda 0,185 ✗ (0,6
  volte l'Australia, non meno della metà); gatti con meno del 5%: 23% · 9% · 5%;
- vere/ruotate: 0,97 · 0,84 · 0,93 ✗ (non simile: l'Australia evita gli edifici più degli altri);
- D cresce con il costruito attorno ✓ (Spearman 0,27 sui 391, p 7·10⁻⁸). A pari costruito:
  fra 0,12 e 0,25 Stati Uniti 0,073 (39 gatti), Nuova Zelanda 0,066 (79), Australia 0,179 (85);
  fra 0,05 e 0,12: 0,004 · 0,012 · 0,017; sotto 0,05 **negativo**: −0,056 · +0,009 · −0,083.
Lettura: gli Stati Uniti non hanno gatti diversi, hanno meno costruito attorno (due gatti su
tre sotto 0,12, contro uno su tre in Australia e uno su cinque in Nuova Zelanda); a pari
costruito stanno con la Nuova Zelanda. È l'Australia a fare più segnale. Dove il costruito è
quasi niente la mappa con i muri perde: poche posizioni vere dentro un edificio (GPS, o un
edificio di OSM che non c'è più) pagano il pavimento all'1% (−4,6 nat) e pesano più del
guadagno sul resto. Da provare, prima di cambiarlo: il pavimento (1% → 5-10%) sui gatti di L6.

### 2026-09-26 — L9b, L10b — rilettura di L9 e L10 (scritto prima di calcolare)
Perché: rileggendo, tre cose non erano misurate. (1) In L9 le mappe si sono confrontate solo con
la 1, mai la nuova con la vecchia, e senza il rumore del seme: «la mappa si allarga un poco» non
è dimostrato. (2) La spiegazione di P5 (la 3 si avvicina alla 2 perché le separava la
raggiungibilità) è scritta, non misurata. (3) Il motore ora pesa `sel` sulle celle dove il gatto
può stare (`ok`: libere **e raggiungibili**), mentre la mappa confermata in L7 (`walls_sel`)
pesa `sel` su tutte le celle libere, anche quelle che il grafo dice irraggiungibili (cortili
chiusi da edifici). Inoltre in `proto/gps/score.py` la mappa `full` (quella di L5, `sel × reach`,
e la predefinita del comando) era `Place.weight`: dopo L9 sarebbe cambiata in silenzio.
Previsioni:
- L9b-1: rifatto `pieces` sui dati di L7 con `full` scritta per esteso (`sel × reach`), ogni
  numero già in `pieces.json` identico al bit;
- L9b-2 (luogo di prova, variante 2, entro 200 m): celle libere irraggiungibili 1-5% delle
  libere; la direzione delle ancore fra regola vecchia e nuova, distanza di variazione totale
  per anello mediata sulle distanze delle ancore, 0,03-0,12; fra variante 2 e 3 con la regola
  vecchia più del doppio che con la nuova (la spiegazione di P5);
- L9b-3: con il seme 1 la differenza vecchia/nuova della regione al 50% ha lo stesso ordine
  (sotto 0,02 ha) e segno qualsiasi: nessun allargamento misurabile;
- L10b-1: a σ 0 la mappa con i soli muri dà per ogni gatto `D ≈ k × (dentro ruotate − dentro
  vere)`, con `k = G(fuori) − G(dentro) ≈ 4,7` (il pavimento all'1% vale −4,6 nat): pendenza
  fra 4,5 e 4,9, R² sopra 0,9. Quindi il pavimento cambia solo la scala di D, e l'idea di
  provarlo all'1-5-10% (L10) non porta niente;
- L10b-2: per paese `walls_sel 0` ≈ 4,7 × (dentro ruotate − dentro vere) entro ±0,02; e il
  paese pesa più per quanto il gatto evita gli edifici che per quanti ce ne sono: gli Stati
  Uniti con il rapporto vere/ruotate dell'Australia darebbero D ≈ 0,07, con il costruito
  dell'Australia e il loro rapporto ≈ 0,02;
- L10b-3: il D negativo dei gatti con meno del 5% di costruito è rumore (|z| < 2);
- L10b-4 (rifatto `pieces`, descrittivo): posizioni vere su celle libere irraggiungibili come
  le ruotate entro ±50%, e sotto l'1% delle posizioni; la mappa `engine` (quella del motore
  dopo L9) a σ 0 entro ±0,005 da `walls_sel`; per paese, vere/ruotate per distanza dal
  primo edificio: negli Stati Uniti fra 0,93 e 1,07 in ogni fascia, in Australia dentro
  sotto 0,88 e a 6-12 m sopra 1,05.

### 2026-09-26 — L11 — l'acqua non è un posto dove il gatto può stare (scritto prima di cambiare il motore)
Cosa: nel motore l'acqua (WorldCover classe 80) finiva nel tipo `open`, cioè giardino e prato
per Hanmer, con la selezione più alta (1,78). Il gatto ci poteva stare e ci si ancorava più
volentieri: in un caso vicino al mare, a un lago o a un fiume largo la mappa metteva gatti in
acqua. Si corregge: l'acqua esce dalle superfici (come gli edifici nella variante 2, quindi fa
anche da barriera), tranne dove c'è una strada sopra (un ponte).
Previsione:
- impronta senza luogo identica;
- luogo di prova: nel quadrato non c'è acqua di WorldCover (0 celle), quindi ogni numero di
  `variants` e del caso privato identico a prima della correzione;
- test sul luogo sintetico con un fiume e un ponte: nessuna cella d'acqua dove il gatto può
  stare, la riva di là raggiungibile solo dal ponte (costo sopra la distanza in linea d'aria),
  senza ponte irraggiungibile; a 24 ore nessun gatto libero in acqua.
Risultato L9b, L10b:
- L9b-1 ✓: `pieces` rifatto sui dati di L7 (72 s): i 12.427 numeri già in `pieces.json`
  identici al bit. In `score.py` ora `full` è scritta per esteso (`sel × reach`) ed `engine` è
  `Place.weight` (`lessons.md` #53);
- L9b-2: celle libere irraggiungibili entro 200 m **0,03%** ✗ (previste 1-5%: i cortili del
  luogo di prova non sono chiusi dalle impronte). Direzione delle ancore vecchia/nuova (variazione
  totale per anello, mediata sulle distanze delle ancore): variante 2 **0,049** ✓, variante 3
  0,069; fra 2 e 3 con la regola vecchia 0,037, con la nuova **0,000** ✓: le ancore delle due
  varianti ora coincidono, la spiegazione di P5 è misurata. Perché cambia poco: sulle celle
  dove il gatto può stare, entro 200 m, la raggiungibilità va da 0,74 (10° percentile) a 0,94
  (90°). Lo spostamento c'è, ed è lo stesso con ogni seme: ancore su `street` da 0,150 a 0,168,
  su `open` da 0,481 a 0,468 (nel grafo le strade costano di più, e la raggiungibilità le
  abbassava);
- L9b-3 ✓ (rifatto dopo L11, due semi): regione al 50% vecchia → nuova +0,000 e −0,003 ha
  (seme 0, varianti 2 e 3), −0,006 e +0,003 (seme 1). Segno qualsiasi, sotto 0,01 ha: la mappa
  non si allarga. La P3 di L9 era ✓ alla lettera, non nella sostanza;
- L10b-1 ✓: `walls 0` per gatto = 4,87 × (dentro ruotate − dentro vere) + 0,0004, R²
  **0,9993** su 391 gatti; `walls_sel 0` pendenza 4,91, R² 0,965 (la selezione aggiunge 0,003).
  Il conto sta in `matematica.md`: k = log(1 + 1/(f(1 − a))), con f il pavimento e a la quota
  di edifici nell'anello, fra 4,7 e 5,0. **Il D di L7 è un numero solo per gatto: di quanto le
  posizioni cadono dentro le impronte di OSM meno del caso** (0,138 contro 0,153). Il pavimento
  cambia solo la scala: l'idea di L10 (provarlo all'1, 5 e 10%) cade;
- L10b-2 ✓: per paese 4,7 × Δdentro dà Stati Uniti 0,016 (D 0,016), Australia 0,124 (0,138),
  Nuova Zelanda 0,060 (0,061). Vere/ruotate dentro: 0,966 ± 0,033 · 0,843 ± 0,025 · 0,931 ±
  0,029; Δdentro Australia − Stati Uniti 0,023, z 4,2. Gli Stati Uniti con il rapporto
  dell'Australia darebbero 0,075; con il costruito dell'Australia e il loro rapporto 0,027:
  **pesa più quanto il gatto evita le impronte che quante ce ne sono**. La lettura di L10
  («non hanno gatti diversi, hanno meno costruito») era sbagliata (`lessons.md` #52);
- L10b-3 ✗ al limite: gatti con meno del 5% di costruito, Stati Uniti D −0,056 ± 0,028 (z
  −2,0; dentro vere 0,038 contro 0,028 ruotate), tutti i 46 −0,041 (z −2,0). Fra 12 celle
  guardate (4 fasce × 3 paesi) una a z 2 se ne aspetta per caso: non è dimostrato né il rumore
  né l'effetto;
- L10b-4 (descrittivo): celle libere irraggiungibili 0,025% delle posizioni vere e 0,022% delle
  ruotate ✓ (troppo poche per dire altro). `engine` a σ 0 contro `walls_sel` −0,0002 ± 0,0006
  ✓; `full` (con la raggiungibilità) contro `engine` +0,003 ± 0,002 a σ 0, +0,002 ± 0,002 a 10
  m: neutra anche a σ 0. Vere/ruotate per distanza dal primo edificio (dentro · 0-3 · 3-6 ·
  6-12 · 12-24 · oltre 24 m): Stati Uniti 0,97 · 1,05 · 1,09 · 1,10 · 1,00 · **0,83** ✗
  (previsto 0,93-1,07 in ogni fascia); Australia 0,84 ✓ · 1,01 · 1,04 · 1,09 ✓ · 1,05 · 0,93;
  Nuova Zelanda 0,93 · 0,99 · 1,02 · 1,08 · 0,99 · 0,95. I gatti degli Stati Uniti hanno la
  stessa forma degli altri (vicino agli edifici sì, lontano no) **tranne dentro**, dove cadono
  quanto il caso;
- l'acqua nei mondi dei gatti GPS (non prevista: trovata rileggendo, descrittiva). `build_cats.py`
  non la disegna, quindi è `open` con selezione 1,78. Acqua interna di OSM (`natural=water`,
  bacini, zone umide) entro 280 m: 40 gatti su 120 negli Stati Uniti, 14 in Australia, 20 in
  Nuova Zelanda. Il mare, ricostruito dalla linea di costa di OSM (terra a sinistra, acqua a
  destra): 8, 3 e 17 gatti. Posizioni in acqua: vere 0,05%, ruotate 0,40%; in Nuova Zelanda
  fino al 36% delle ruotate di un gatto di costa, mai una vera (un gatto degli Stati Uniti ha il
  3,6% delle vere «in mare»: spiaggia, pontile, o costa ricostruita male, da guardare). Con
  l'acqua come muro (stessa identità) D salirebbe di circa 0,029 negli Stati Uniti, 0,025 in
  Nuova Zelanda, 0,001 in Australia. **L7 non vedeva l'acqua, e il suo D è per difetto**:
  calcolato dopo aver visto i dati, non cambia il verdetto di L7.
Risultato L11:
- impronta senza luogo identica ✓;
- luogo di prova ✗: nel quadrato ci sono 101 celle d'acqua (0,03% della griglia), tutte negli
  angoli, a 710-720 m da casa. La base era stata letta in un cerchio di 600 m (`lessons.md` #54).
  Cambiano i passi rilanciati laggiù, e con loro il flusso dei numeri casuali: ogni numero si
  muove dentro il rumore del seme (regione al 50% 0,590 → 0,587 ha; liberi 23,4 / 56,7 / 179,9
  m; C1 0,471 / 0,731). Nel caso privato il primo posto consigliato (la casa, p 0,72) resta
  identico; degli altri quattro (p 0,01-0,03) due restano, due si spostano di 13 e 39 m. Lo
  stesso però fa il seme da solo: con i semi 1 e 2 uno dei quattro non ha un posto entro 85-121
  m, un altro entro 45-49 m. **Oltre il primo, i posti consigliati sono in parte rumore del
  Monte Carlo** (`STATO.md`). I `varianti-24h*.json` ora sono quelli
  dopo L11 (`water_cells` 101);
- test ✓: `test_water_is_no_place_for_a_cat` (un fiume di 16 m con un ponte: nessuna cella
  d'acqua dove stare, la riva di là solo dal ponte, senza ponte irraggiungibile, a 24 ore nessun
  gatto in acqua). Con la correzione spenta il test cade (provato).
Verdetto: il motore non mette più gatti in acqua. Sul luogo di prova non cambia niente di
misurabile; conta nei casi vicino al mare, ai laghi e ai fiumi larghi. I fiumi sotto i 10 m di
WorldCover restano invisibili: da OSM (`waterway=river`, `natural=water`) si aggiungono quando
serve.

### 2026-09-26 — L12 — la mappa come previsione, non come test (scritto prima di calcolare)
Perché: il D di L5-L7 è la differenza fra il punteggio delle posizioni vere e quello delle
ruotate: dice se la mappa mette le vere più in alto delle ruotate (un'associazione), non se è
una buona previsione. Per una mappa costante su classi (dentro gli edifici, fasce di distanza,
tipi) D = Σ_c (u_c − a_c) log w_c, con u la quota delle vere e a quella delle ruotate: è lineare
in log w e cresce senza fine spingendo a zero una classe poco usata. Il metro del prodotto è il
punteggio proprio delle sole posizioni vere contro la mappa radiale, S = Σ_c u_c log(w_c / Σ_d
a_d w_d). Per la disuguaglianza di Gibbs S ≤ KL(u‖a), con l'uguaglianza solo per w_c ∝ u_c / a_c:
**la mappa migliore su quelle classi è il rapporto di selezione**, e nessuna mappa su quelle
classi guadagna più di KL(u‖a). (In ecologia è la massima verosimiglianza di una funzione di
selezione a categorie: nuovo per noi è usarlo come metro della mappa.)
Previsioni (391 gatti di L7, pavimento all'1% come in L5; S in nat per posizione, media sui gatti):
- `walls` a σ 0: S ≈ −0,49 (il conto: 0,138 × (−4,62) + 0,862 × 0,17): come previsione la mappa
  a muri è **peggio della mappa radiale**, pur con D = +0,074; a σ 5 fra −0,10 e −0,02, a σ 10
  fra −0,02 e +0,01, a σ 20 entro ±0,005;
- la mappa del motore (`engine`, senza pavimento: zero dentro gli edifici): posizioni vere su
  celle a peso zero circa 14%, gatti con almeno una posizione lì oltre il 90%: S = −∞;
- limite di ogni mappa costante sulle 6 fasce di distanza dagli edifici: KL ≈ 0,003 (dalle quote
  di `pieces.json`); sui 6 tipi di posto sotto 0,005; tarata su due paesi e provata sul terzo:
  fra 0 e 0,003.
Risultato (391 gatti, S media sui gatti ± errore; calcolato con `score.gain_map` sulle sole posizioni vere):
- `walls`: σ 0 **−0,498 ± 0,018** ✓; σ 5 −0,023 ± 0,003 ✓; σ 10 −0,006 ± 0,002 ✓; σ 20 −0,002 ±
  0,001 ✓. Per paese a σ 0: Stati Uniti −0,36, Australia −0,50, Nuova Zelanda −0,63;
- `walls_sel` e `engine` (identiche entro 0,001): σ 0 −0,513; σ 5 −0,036 ± 0,004; **σ 10 −0,012
  ± 0,003**; σ 20 −0,005 ± 0,002. `full` (con la raggiungibilità) ancora un poco peggio (σ 10
  −0,016). **A ogni lisciatura la mappa del motore prevede le posizioni vere peggio della mappa
  radiale**; la selezione di Hanmer toglie invece di aggiungere (`walls_sel` sotto `walls` a
  ogni σ);
- `engine` senza pavimento: posizioni vere su celle a peso zero **13,8%** ✓, gatti con almeno
  una **97%** ✓: come previsione vale −∞;
- limiti delle mappe a classi: 6 fasce di distanza dagli edifici KL 0,0028 ✓; 6 tipi di posto
  0,0011 ✓. Il rapporto di selezione per fasce, tarato su due paesi e provato sul terzo (quote
  per paese di `pieces.json`): Stati Uniti +0,0025, Australia +0,0024, Nuova Zelanda +0,0006 ✓,
  **positivo in tutti e tre**: la prima mappa che batte la radiale fuori campione. I suoi pesi
  (tutti i gatti): dentro 0,90 · 0-3 m 1,01 · 3-6 m 1,05 · 6-12 m 1,09 · 12-24 m 1,02 · oltre 0,90.
Verdetto: L7 ha confermato un'associazione (le vere cadono dentro gli edifici meno delle
ruotate), non una previsione. Come previsione delle posizioni di gatti residenti la mappa del
motore **perde** contro quella radiale, per due pezzi: lo zero dentro gli edifici (dove cade il
14% delle posizioni vere, errore del GPS e ripari insieme) e i pesi di Hanmer (gatti del Regno
Unito accanto al verde), che qui non reggono. Quello che una mappa a classi può guadagnare è
piccolo (al massimo 0,003 nat per posizione), ma c'è, e si ottiene con i rapporti di selezione
misurati. Per un gatto smarrito il punto non è chiuso: Huang dice che si nasconde anche in
garage, capanni e sotto i portici (25%), cioè proprio dentro le impronte a cui il motore dà zero.
Riproducibile: `python -m proto.gps.pieces privato/dati/cattracker-conferma --households 20`
stampa ora S accanto a D (fra graffe) e le scrive in `pieces.json` (`S_real`); gli altri 14.904
numeri restano identici al bit. Tutte le 8 mappe, a ogni σ, hanno S sotto zero.

### 2026-09-26 — L13 — dentro gli edifici per tipo, il metro con l'errore del GPS, una mappa che batta la radiale fuori campione (scritto prima di calcolare)
Cosa: sui 391 gatti di L7 (66.526 posizioni vere fra 20 e 280 m, 345 case) le tabelle di
`proto/gps/classes.py` (`classes.npz`): per ogni posizione la classe della sua cella fra 31 classi
fini. Dentro: la casa del gatto; gli altri edifici per gruppo del tag `building` di OSM
(abitazione: `house`, `detached`, `residential`, `apartments`…; garage: `garage`, `garages`,
`carport`; capanno: `shed`, `hut`, `barn`, `greenhouse`…; `yes`; altro) e impronta sotto o sopra i
40 m². Fuori: fascia di distanza dal primo edificio (0-3, 3-6, 6-12, 12-24, oltre 24 m) per
superficie (strada, giardino, vegetazione, aperto). La disponibilità è la media esatta sull'anello
da 2 m della cella (le ruotate di `pieces.py` senza Monte Carlo). I tag vengono dalla risposta di
OSM da cui è stato costruito ogni mondo, ridipinta: la griglia degli edifici torna identica in
tutti i 391 (controllo nel codice). Il punteggio dalle tabelle coincide con `score.gain_map` a
pavimento 0 entro 5·10⁻⁸ (σ 0 e 10, tre gatti).
Il metro: S = media sui gatti della media sulle loro posizioni di log(m(x) / m̄(x)), con m la mappa
**nella posizione vera** (costante sulle classi) sfocata da una gaussiana di σ m prima del
punteggio, e m̄ la media di m sull'anello da 2 m della cella: l'errore del GPS sta nel punteggio,
non nella mappa. A σ 0 è il punteggio di L12. I pesi che massimizzano S (la massima
verosimiglianza della selezione, per Gibbs il rapporto di selezione a σ 0) danno il massimo che
una famiglia può dare in campione; il numero che conta è fuori campione.
Letto prima di prevedere (solo disponibilità, nessuna posizione vera): dentro gli edifici Stati
Uniti 0,101, Australia 0,168, Nuova Zelanda 0,185 (come L10). Sotto i 40 m² è l'1-4% dell'area
dentro (0,0022 · 0,0015 · 0,0066). In Australia l'area dentro è per il 58% `house` e simili, negli
Stati Uniti e in Nuova Zelanda per il 62-68% `yes`. Impronte di Microsoft (da immagini): 23%
dell'area dentro negli Stati Uniti, 15% in Australia, nessuna in Nuova Zelanda (LINZ e comune di
Wellington). Più di 8 m dentro un muro: 0,1-0,2% dell'anello; quasi tutto il dentro è entro 4 m da
un muro.
Previsioni, parte 1 (σ 0, rapporto vere/disponibili, media sui gatti; `classes inside`):
- P1 (controllo): la quota delle vere dentro gli edifici è quella di `pieces.json` (`inside_real`)
  per ogni gatto alla quarta decimale; la disponibilità dentro è `inside_rotated` entro ±0,01 per
  gatto ed entro ±0,001 in media;
- P2 (impronta): sotto i 40 m² (casa esclusa) il rapporto è più alto che sopra: sotto 0,9-1,4,
  sopra 0,80-0,95;
- P3 (tipo): lo 0,97 degli Stati Uniti non viene dal miscuglio dei tag: dentro `yes` ≥ 40 e dentro
  abitazione ≥ 40 il rapporto degli Stati Uniti supera quello dell'Australia di almeno 0,05 in
  tutti e due. Garage ≥ 40 sopra abitazione ≥ 40 (poche posizioni, bassa fiducia);
- P4 (fonte): le impronte di Microsoft hanno il rapporto degli altri edifici dello stesso paese
  entro ±0,1: la fonte non spiega lo 0,97;
- P5 (profondità): il rapporto scende entrando, in ogni paese: entro 2 m dal muro > 2-4 > 4-8 m;
  a 4-8 m fra 0,5 e 0,8 (la sola sfocatura con σ 5-6 m, l'errore degli i-gotU di Morris e Conner,
  darebbe 0,3-0,5); gli Stati Uniti sopra l'Australia a ogni profondità;
- P6 (la casa del gatto oltre i 20 m): rapporto sopra 1,5 (descrittivo, pochi gatti).
Parte 2, in campione (S in nat per posizione, `classes fit`):
- P7: 6 fasce (`bands6`) a σ 0: 0,0025-0,0035 (L12: KL 0,0028 dalle quote medie);
- P8: dentro per tipo e impronta più 5 fasce (`inside11+bands5`, 16 classi) a σ 0: 0,003-0,006;
  tutte le 31 (`fine31`): 0,005-0,012;
- P9 (l'errore nel punteggio): per `bands6` e `inside11+bands5` il massimo di S sta a σ fra 5 e
  15 m e supera σ 0 di 0,0005-0,003; lì il peso dentro gli edifici nella posizione vera è più
  basso del rapporto a σ 0 (la sfocatura tolta): 0,4-0,8 invece di ~0,9;
- P10: per paese il σ del massimo (`bands6`) è più grande negli Stati Uniti che in Australia (più
  alberi sopra il GPS).
Parte 3, fuori campione (tarata su due paesi, provata sul terzo; σ scelto dalla S di taratura fra
0, 5, 10, 15, 20 m):
- P11: `bands6` a σ 0 positiva nei tre paesi, entro ±0,001 da L12 (+0,0025 · +0,0024 · +0,0006);
- P12: `inside11+bands5` positiva nei tre e sopra `bands6` σ 0 in almeno due; `fine31` sotto
  `inside11+bands5` in almeno un paese (strade, giardini e vegetazione sono disegnati in modo
  diverso dall'OSM di ogni paese).
Regola di scelta, scritta ora: la candidata è la famiglia (con la sua regola per σ) con la S media
più alta sui 391 gatti provati fuori campione (ognuno con i pesi tarati sugli altri due paesi),
purché positiva in tutti e tre; entro 0,0002 vince quella con meno classi. La candidata si tara
poi su tutti e tre i paesi e si prova sul Regno Unito di L5, con una previsione scritta prima.
Comandi: `python -m proto.gps.classes build|inside|fit privato/dati/cattracker-conferma`.
Risultato, parte 1 (`classes-inside.json`; rapporto vere/disponibili; Australia · Nuova Zelanda ·
Stati Uniti):
- P1 ✓: quota delle vere dentro identica a `inside_real` in tutti i 391 (differenza massima 0);
  disponibilità contro `inside_rotated` in media +0,0002 ✓, al massimo 0,0104 ✗ al limite (un
  gatto: l'anello di celle contro il cerchio delle ruotate);
- P2 ✗: sotto i 40 m² 0,83, sopra 0,89 (per paese sotto 0,92 · 0,73 · 1,06, sopra 0,81 · 0,93 ·
  0,94): l'impronta piccola non si distingue, ed è l'1-4% dell'area;
- P3 ✗ a metà: dentro `yes` ≥ 40 gli Stati Uniti 0,98 contro 0,86 dell'Australia (+0,12 ✓), dentro
  abitazione ≥ 40 0,84 contro 0,80 (+0,04, soglia 0,05 ✗). Garage ≥ 40 0,95, abitazione 0,86 ✓;
- P4 ✗: negli Stati Uniti le impronte di Microsoft hanno **1,11** (le vere ci cadono più del caso),
  le altre 0,89; in Australia 0,80 contro 0,82. Con quelle di Microsoft come le altre, gli Stati
  Uniti darebbero 0,92 invece di 0,97: **un terzo della distanza dall'Australia viene da lì**, il
  resto dai `yes` senza fonte (0,88 contro 0,82) e dalla casa;
- P5 ✗: il rapporto **non scende entrando**. Tutti i gatti: entro 2 m dal muro 0,92, 2-4 m 0,91,
  4-8 m 0,82, oltre 8 m 0,74; a 4-8 m per paese 0,75 · 0,88 · 0,90 (previsto 0,5-0,8; la sola
  sfocatura con σ 5-6 m darebbe 0,3-0,5). Stati Uniti sopra l'Australia a 3 profondità su 4. Le
  vere che cadono dentro sono sparse su tutta l'impronta, non ammucchiate ai muri;
- P6 ✗ al limite: la casa del gatto oltre i 20 m 1,42 (1,43 · 1,24 · 1,56).
Parte 2, in campione (`classes-fit.json`): P7 ✓ `bands6` σ 0 0,0034. P8 ✓ `inside11+bands5` σ 0
0,0042, `fine31` 0,0056. P9 ✗ a metà: `bands6` ha il massimo a σ 5 m (0,0047, +0,0013 ✓; peso dentro
0,67 invece di 0,91 ✓), `inside11+bands5` cresce fino al bordo (σ 20 0,0193; 30 m 0,0206) ✗, e non
per l'errore del GPS (sotto). P10 ✓: il massimo di `bands6` per paese a 5 · 10 · 20 m (il bordo).
Parte 3, fuori campione: P11 ✓ `bands6` σ 0 +0,0023 · +0,0005 · +0,0035 (L12 +0,0024 · +0,0006 ·
+0,0025; gli Stati Uniti a +0,0010, al limite); con la sua regola (σ 5) la Nuova Zelanda va a
−0,0002. P12 ✓: `inside11+bands5` (σ 20 scelto in tutti e tre) +0,0127 · +0,0103 · +0,0127, sopra
`bands6` in tutti e tre; `fine31` sotto in Australia e Nuova Zelanda. **La regola sceglie
`inside11+bands5` a σ 20: +0,0119 ± 0,0041** sui 391 gatti provati fuori campione, positiva in
tutti e tre i paesi.
Smontata (esplorativo, `classes pieces`, la candidata non cambia): il guadagno è quasi tutto **la
casa del gatto**. La casa come classe e gli altri edifici insieme (`home+bands6`) danno a σ 20
0,0185 in campione contro 0,0193; gli edifici piccoli non aggiungono niente (`small+bands6` =
`bands6` a ogni σ: i loro pesi 5-24 a σ 20 erano rumore di classi quasi collineari). Perché: il
punto casa dei gatti GPS (la cella da 10 m con più righe) sta in mediana a 7,9 m dal centro
dell'edificio di casa (90° percentile 17,6 m), e le posizioni fra 20 e 60 m pendono verso quel
centro: coseno medio +0,20 ± 0,02 con lo scarto fra 6 e 20 m, +0,08 ± 0,05 sotto i 3 m (Spearman
0,17, p 0,0006). La casa sfocata a 20-30 m dice che **il gatto gira attorno all'edificio di casa,
non attorno al punto casa**: è il centro degli anelli, non il paesaggio. Con σ fino a 40 la regola
diventa instabile (Nuova Zelanda −0,0011).
Prova finale sul Regno Unito (scritta prima di costruirne le tabelle): la candidata
(`inside11+bands5`, σ 20, tarata sui 391) sui gatti di L5 (`privato/dati/cattracker`, case a 20 m).
Previsione: S fra 0 e +0,02 (fuori campione nei tre paesi +0,010-0,013); con ~46 gatti l'errore è
~0,009 e la potenza a p < 0,05 sotto il 30%: un S positivo non significativo è il risultato
atteso e da solo non dice nulla, un S sotto zero sarebbe contro. Secondari: `bands6` σ 0 fra
−0,002 e +0,004; `home+bands6` σ 20 entro ±0,003 dalla candidata. Nel Regno Unito il punto casa
viene dalle sole visibili (98% delle righe): lo scarto dal centro dell'edificio può essere diverso.
Risultato della prova finale (`privato/dati/cattracker/classes-test.json`; 46 gatti, 37 case,
5.918 posizioni; le tabelle del Regno Unito rifanno la griglia degli edifici identica in tutti):
la candidata dà **S = −0,0053 ± 0,0093** ✗ (sotto zero, dentro il rumore: z −0,6); `home+bands6`
σ 20 −0,0052 ✓ (come la candidata); `bands6` σ 0 **+0,0028 ± 0,0039** ✓. Nel Regno Unito il punto
casa sta come altrove a 8,1 m (mediana) dal centro dell'edificio di casa, ma le posizioni fra 20 e
60 m non pendono verso quel centro (Spearman −0,08, p 0,61; case di 94 m² in mediana contro 184,
spesso file di villette che OSM disegna come un edificio solo).
Verdetto: **la candidata non passa la prova finale e non va nel motore.** Il suo guadagno era la
casa, cioè il centro degli anelli, e dipende da come i dati definiscono il punto casa (la cella più
densa di tutte le righe) e da come OSM disegna la casa: non passa da un insieme all'altro. Quello
che regge in tutti e quattro gli insiemi è la mappa per fasce di distanza dagli edifici a σ 0
(`bands6`: +0,0023 · +0,0005 · +0,0035 fuori campione, +0,0028 nel Regno Unito), piccola: il
paesaggio di OSM, per gatti residenti, dà al massimo 0,002-0,004 nat per posizione. Tipo e
superficie degli edifici non la cambiano. Lo 0,97 degli Stati Uniti viene per un terzo dalle
impronte di Microsoft (1,11) e per il resto dai `yes` senza fonte; non dalla profondità: le
posizioni dentro sono sparse su tutta l'impronta. Aperti: il centro del gatto (porta, cella più
densa o edificio) come domanda a sé, e l'errore del GPS letto dai dati (le righe nascoste dei gatti
fermi), non dalla prova statica di Morris e Conner.

### 2026-09-26 — L14 — dal residente allo smarrito: le fasce fuori, i ripari di Huang negli edifici (regola scritta prima di cambiare il motore)
Perché: il motore pesa le ancore con la selezione di Hanmer (gatti residenti del Regno Unito
accanto al verde) e dà zero dentro gli edifici. Sui residenti col GPS tutte e due perdono (L12):
il paesaggio misurato dei residenti sono le fasce di distanza dagli edifici (L13, quasi radiali).
Per uno smarrito Huang (Tabella 6 e il paragrafo dei luoghi, `riferimenti.md`) trova un quarto
dei gatti dentro le impronte degli edifici: garage, capanni, sotto casa, case d'altri. Hanmer dice
anche di evitare la vegetazione, dove Huang trova il 16% degli smarriti fuori.
La regola (scritta prima di calcolarne i numeri):
1. fuori dagli edifici il peso è quello dei residenti per fascia di distanza dal primo edificio
   (`bands6` σ 0 tarata sui 391 gatti di L13: 0-3 m 1,023 · 3-6 1,067 · 6-12 1,112 · 12-24 1,024
   · oltre 24 m 0,837), diviso per la sua media sulla disponibilità fuori: niente più Hanmer, né
   per tipo di posto né per la vegetazione (quella di Huang, i cespugli, a 10 m non si vede);
2. dentro un edificio diverso dalla casa il gatto smarrito può stare, se l'edificio tocca una
   cella libera raggiungibile, con il peso h = (s/a) / ((1 − s)/(1 − a)) rispetto a fuori. s è la
   quota di Huang dei trovati vivi (casa propria esclusa, è lo stato «a casa») che erano dentro
   un'impronta: case d'altri 11%, edifici pubblici 2%, e fra i trovati fuori (83%) sotto casa,
   garage, capanno o stalla, sotto un capanno, sotto un garage, balcone (72 risposte su 468). Sotto
   portico, veranda o terrazza (47) resta fuori: è a ridosso del muro, la fascia 0-3 m. a è la
   quota delle impronte diverse dalla casa nei quartieri dei gatti di Cat Tracker di Stati Uniti e
   Australia (i paesi del sondaggio), anelli pesati con la lognormale delle ancore del gatto di
   casa (mediana 49,5 m, dispersione 2,1, fino a 284 m), ogni paese a metà;
3. la casa resta un muro; l'acqua resta zero (L11); tipo e superficie degli edifici non si
   distinguono (L13: nei residenti non contano; in OSM garage e capanni sono troppo pochi per
   stimarne la disponibilità);
4. la selezione nel passo usa gli stessi pesi (il tempo va col peso): nascosto, il gatto si muove
   meno; il grafo della raggiungibilità non cambia (gli edifici non si attraversano);
5. `PlaceParams.preference`: `"lost"` (questa regola, il motore) o `"hanmer"` (fino a L13, per
   rifare le misure vecchie). `Place.sel` resta Hanmer per tipo: lo leggono le mappe di L5-L7
   (`score.MAPS`, `lessons.md` #53).
I numeri della regola (calcolati dopo averla scritta, prima di toccare il motore): s = **0,268**
(fuori, 72/468 = 0,154 dentro un'impronta); a = **0,093** (Stati Uniti 0,068, Australia 0,117;
Nuova Zelanda 0,137, non usata); **h = 3,58** (con un paese solo: Stati Uniti 4,99, Australia
2,76, Nuova Zelanda 2,30: è l'incertezza di h). Le fasce fuori, divise per la loro media sulla
disponibilità fuori (1,021): 1,002 · 1,045 · 1,089 · 1,003 · 0,819. Un limite scritto ora: Huang non
dice di chi sono la casa, il garage e il capanno dei trovati «sotto casa», «in garage»,
«nel capanno»; se in parte sono quelli del gatto (che qui restano un muro), s e h sono troppo alti
(metà di quelle risposte alla casa propria darebbe s 0,20 e h 2,5).
Previsioni (luogo di prova, variante 2, 24 ore, 50.000 gatti, seme 0, `variants.py`; sul luogo di
prova le impronte diverse dalla casa sono il 29% delle celle fra 20 e 200 m, 0,17 con il peso
delle distanze del motore):
- l'impronta del motore senza luogo (`sim.fingerprint`) identica al bit prima e dopo;
- gatti sciolti entro 200 m dentro un edificio (`loose_type_share_200m`, `roof` nella variante 2):
  da 0 a **0,55-0,85** (con le sole ancore sarebbe h·a/(h·a + 1 − a) ≈ 0,5-0,6; la selezione nel
  passo lo alza verso h²·a/(h²·a + 1 − a) ≈ 0,8);
- distanze dei gatti sciolti (quartili 23 · 57 · 180 m) entro ±5 m sulla mediana: la regola cambia
  la direzione, non la distanza;
- regione al 50% da 0,59 ha a 0,35-0,55 ha (la massa si stringe sugli edifici, più densi di gatti);
- distanza di variazione totale fra variante 2 e variante 1 (senza luogo) fra 0,20 e 0,45 (era
  0,33: prima la 2 toglieva gli edifici, ora li riempie);
- quota di massa nel quadrato (`mass_in_grid`, 0,899) entro ±0,01; ricadute sulla direzione a caso
  (`fallback_share`, 0,130) non sopra;
- i test di `test_place3d.py` che dicono «le ancore stanno fuori dagli edifici» cambiano con la
  regola (si riscrivono: le ancore stanno dove il gatto può stare, edifici diversi dalla casa
  compresi); nessun altro test cambia.
Risultato (`privato/luogo/varianti-24h-lost.json` e `-lost-seed1.json`; con `--preference hanmer`
il luogo di prova rifà i numeri di prima al bit, `varianti-24h.json`):
- impronta del motore senza luogo identica al bit ✓;
- gatti sciolti entro 200 m dentro un edificio (misura nuova `loose_in_building_200m`: il conteggio
  per tipo di `variants.py` è solo a terra) **0,484** e 0,481 con il seme 1 ✗ (previsto
  0,55-0,85); senza luogo 0,33. Ancore dentro un edificio 0,345;
- distanze dei gatti sciolti 30,0 · 60,3 · 176,4 m: la mediana a +3,6 m ✓, ma **il primo quartile
  sale da 23,4 a 30,0 m**;
- regione al 50% **1,01 ha** ✗ (prevista 0,35-0,55, era 0,59): la massa si allarga, perché vicino
  alla porta resta meno gente; C1 0,50 / 0,75 (era 0,47 / 0,73);
- variazione totale fra 2 e 1: 0,212 ✓; massa nel quadrato 0,900 ✓; ricadute 0,130 ✓;
- i test: nella città sintetica fitta il primo quartile sale del 13% (28,2 m contro 24,9 senza
  luogo), fuori dal ±10% di `test_place_keeps_the_walk_distances`. Smontato: con Hanmer 24,1;
  `lost` senza selezione nel passo 26,2 (gatti negli edifici 0,34, quasi il caso); `lost` con
  `hide` 1 26,3; `lost` pieno 28,2 (negli edifici 0,60, `sel_ref` 1,72).
Verdetto: **la regola non diventa il motore.** Con le sole ancore il passo (10-25 m all'ora) porta
i gatti fuori dalla cella dell'ancora e la preferenza per gli edifici quasi sparisce; con la
selezione nel passo ci resta, ma la normalizzazione `sel_ref` (la media sulle ancore a caso, 1,5
sul luogo di prova e 1,7 nella città sintetica) fa muovere il gatto fuori, cioè alla porta, 1,5-1,7
volte più del tarato, e le distanze vicine si allungano. Il motore resta Hanmer (`preference`
predefinita `"hanmer"`); `"lost"` è un'opzione con i suoi test, e il fallimento è un xfail
stretto (`test_the_lost_rule_keeps_the_walk_distances`). Prossimo: il nascondersi come tempo
passato fermo in un riparo che tenga le distanze di A5.

### 2026-09-26 — R — i numeri del README, rimisurati a macchina libera (scritto prima di lanciare)
Perché: il README mostra solo numeri di oggi. L'ultima misura di B, C1 e C2 è A5; dopo sono
cambiati solo il luogo (L2-L14, con l'impronta senza luogo identica al bit a ogni passo) e
l'uscita di `sim.baseline`, che ora scrive anche l'area tipica (media geometrica) di ogni mappa.
Previsione:
- `sim.fingerprint` identica a L14;
- C2 (`sim.baseline`, stessi semi) identica ad A5 al bit: rapporto 0,388 · 0,422, cerca meno 0,674,
  media geometrica 0,548; il rapporto fra le aree tipiche nuove è uguale alla media geometrica
  del rapporto di A5 in ogni categoria (0,549 · 0,329 · 0,835 · 0,814 · 0,546);
- B e C1 (`sim.validate`, `--coverage`) identiche ad A5 (B1 11,0 / 72,1 / 462,6 m, B3 0,814);
- distanze contro gli studi, come `tests/test_targets.py` ma con 100.000 gatti e 40.000 cani
  (seme 21): gatto casa 9-10 / 40-42 / 138-146 m (A5 9,4 / 40,6 / 142,4), errore ≤ 0,08; gatto
  libero errore 0,25-0,30 (A5 0,283); cani 98-110 m e 1.420-1.580 m (A4 103,9 / 1.500), errore
  0,12-0,16;
- `pytest -q` verde, con il test nuovo del LiDAR (#59) e gli xfail stretti di prima.
Comando: `python -m sim.fingerprint`, `python -m sim.baseline`, `python -m sim.validate`,
`python -m sim.validate --coverage`, `python -m pytest -q`; le distanze con `cat_readings` e
`dog_run` di `sim.calibrate`.
Risultato (22:38-23:16, macchina libera):
- C2 **identica ad A5 al bit** ✓ (0,388 · 0,422, cerca meno 0,674, geometrica 0,548, ogni
  categoria uguale). Aree tipiche nuove, anelli → simulatore (ha): tutte 221 → 121; gatto casa 5,88
  → 3,23; gatto libero 317 → 104; cane socievole 2,52 → 2,10; diffidente 4.169 → 3.393; pauroso
  3.497 → 1.908. I rapporti sono le medie geometriche di A5 ✓ (socievole 0,833 contro 0,835:
  l'arrotondamento delle aree).
- B e C1 identiche ad A5 al bit ✓. Nella previsione ho scritto B3 0,814, il numero di B: A5 aveva
  già 0,816, ed esce 0,816. C1: al 50% fra 0,453 e 0,551, al 90% fra 0,869 e 0,898.
- Distanze (seme 21): gatto casa 8,7 / 40,3 / 140,3 m, errore 0,032 (il primo quartile appena sotto
  il 9-10 previsto ✗, il resto ✓); gatto libero 17,0 / 231,1 / 1.410,5 m, errore 0,23 ✗ (previsto
  0,25-0,30: il primo quartile a 17 invece di 18); cani 105,8 m e 1.504 m ✓, errore 0,119 (appena
  sotto lo 0,12-0,16 previsto ✗).
- `pytest -q`: 96 passati, 1 saltato, 5 xfail, 37,8 s ✓. Gli esempi: 0,39 s (gatto), 0,49 s (cane).
- Impronta senza luogo: `12123784d829603c` (gatto) · `4b3a77e8efba350d` (cane) · `2c6e9e97540002f9`
  · `89c6eef0f37ef87c` · `1da15345bf955a4c` · `748d473eb93d119c` · `d431b1dcc9647eaa` (le cinque
  categorie). Quella di L14 non era scritta: da qui c'è un riferimento.
Verdetto: il README porta numeri di oggi, e il motore senza luogo non si è mosso da A5. Gli scarti
delle distanze da A5 vengono da un altro seme e da un altro campione (A5 le leggeva nella
taratura): non misurati oltre. Le previsioni «al limite» sbagliate di poco dicono che gli
intervalli erano scritti senza l'errore del campione (`lessons.md` #60).
