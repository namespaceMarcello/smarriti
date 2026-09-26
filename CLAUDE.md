<!-- preferenze: 83d8c143 -->
# Smarriti (nome provvisorio)

Simulatore matematico open source che predice **dove si trova adesso** un animale
smarrito: migliaia di animali virtuali che partono da casa e si muovono nella zona, tarati
sugli studi pubblicati e sui dati aperti. **Solo matematica**: dopo la perdita non riceve niente
(né avvistamenti, né ricerche, né volantini). **Non è un'app**: un sito che si apre da un
link. Nato il 2026-09-25. Il simulatore v0 esiste (`sim/`) e con la mappa lisciata batte
gli anelli (fase C); il luogo in 3D è nel motore (`sim/place.py`), il mondo di un luogo si
costruisce con `proto/luogo3d/`; i prossimi passi sono in `docs/STATO.md`.

**Lo spirito: leggere il problema come un genoma** (Marcello). Ogni studio, ogni
dataset aperto è un dato da sequenziare, dove gli altri lo leggono da solo.
Misurare prima di credere; scrivere la previsione prima di misurare; inventare la prossima
idea dai numeri. Una premessa che dà zero è una scoperta: si scrive, si chiude, avanti.

Stack: simulatore in Python 3.12 (`numpy`, `scipy`, `matplotlib`, `pytest`; `pyshp` e
`tifffile` per il luogo in 3D), codice e commenti in inglese. Il sito: da decidere
(`docs/STATO.md`).

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
- **Ogni errore e ogni cosa che fallisce** va subito in `docs/lessons.md`: cosa, perché,
  la regola che ne esce, il controllo che adesso lo impedisce (un test, se si può).
- Test: `pytest -q` in circa 40 s, tre famiglie (integrità, pressione, ipotesi); quelli che
  per i 4 errori standard chiedono troppi campioni sono `slow` (`--runslow`). Un test
  statistico passa solo se l'intervallo a 4 errori standard sta nella tolleranza; un
  fallimento noto è un `xfail` stretto che cita la misura. Dopo ogni modifica al motore si
  rifà la taratura (`lessons.md` #17).
- Lavoro visivo (UI, mappa): più varianti come PNG o GIF numerati, si aspetta
  la scelta, poi si implementa. Per logica, modello e bugfix: scegli, costruisci, consegna.

### Prima di ogni commit: documentare

| Se è cambiato… | Scrivi in… |
|---|---|
| una decisione, un problema aperto, un prossimo passo | `docs/STATO.md` — sostituisci la riga vecchia, non appendere; tetto 40 KB |
| un pezzo di lavoro finito | `docs/archivio/FATTO.md` — 2-5 righe: cosa, come si prova |
| un numero preso da uno studio, un dataset trovato | `docs/riferimenti.md` — con la fonte accanto |
| una previsione o una misura del modello | `docs/MISURE.md` — la previsione **prima** di lanciare, il risultato dopo, anche se negativo |
| un errore, una cosa fallita | `docs/lessons.md` — una riga: cosa, perché, regola, controllo |
| un parametro, una regola o un'uscita del simulatore | `docs/simulatore.md` — si corregge la riga, non si appende |
| un concetto matematico usato, provato o scartato | `docs/matematica.md` |
| il prodotto: cosa fa, il giro, cosa non facciamo | `docs/progetto.md` |
| un documento nuovo in `docs/` | la tabella «Leggi prima di rispondere» qui sotto |

---

## Leggi prima di rispondere

| Domanda su… | Apri |
|---|---|
| cosa costruiamo, i due stati dell'animale, l'ordine di costruzione | `docs/progetto.md` |
| numeri sugli animali smarriti (distanze, giorni, percentuali), dataset aperti, cosa manca | `docs/riferimenti.md` §A, §B, §C |
| simulazione Monte Carlo, anelli di Koester, sopravvivenza, densità a nucleo, calibrazione, come si incastrano | `docs/matematica.md` |
| **come funziona il simulatore**: stati, movimento, zona, il luogo in 3D, categorie e parametri, taratura, uscite, fasi di verifica, struttura dei file, formato del caso | `docs/simulatore.md` |
| previsioni e misure fatte, in ordine | `docs/MISURE.md` |
| errori e fallimenti, con la regola e il controllo che ne sono usciti | `docs/lessons.md` |
| decisioni prese, problemi aperti, prossimi passi | `docs/STATO.md` |
| cosa è già stato fatto | `docs/archivio/FATTO.md` |
| TiTrovo, l'app separata (solo riferimento per le query geografiche) | `C:\Users\marce\Desktop\IoTiTrovo\CLAUDE.md` |

---

## Comandi

```bash
.venv/Scripts/python -m sim cases/esempio-gatto.json --now 2026-09-22T08:00 --out out/   # mappa, stati, consigli
.venv/Scripts/python -m sim.calibrate all         # fase A (o start, cat_indoor, cat_outdoor, dogs): ~5 min
.venv/Scripts/python -m sim.validate              # fase B; --coverage per C1 (mappa calibrata?)
.venv/Scripts/python -m sim.baseline              # fase C: anelli contro simulatore, ~45 s
.venv/Scripts/python -m sim.compare               # immagine prima / anelli / ora (out/confronto-prima-dopo.png), 2 s
.venv/Scripts/python -m pytest -q                 # ~50 s; --runslow aggiunge i test lenti (~20 s)
.venv/Scripts/python -m sim.fingerprint           # impronta del motore senza luogo: prima e dopo ogni modifica, 5 s
.venv/Scripts/python -m proto.luogo3d.fetch privato/luogo-prova.json privato/luogo      # dati aperti del luogo
.venv/Scripts/python -m proto.luogo3d.world privato/luogo-prova.json privato/luogo      # griglia da 2 m, 3 s
.venv/Scripts/python -m proto.luogo3d.variants privato/luogo-prova.json privato/luogo   # le tre mappe, 4 s
.venv/Scripts/python -m sim privato/caso-luogo-prova.json --now 2026-09-26T20:00 --out privato/out-caso  # caso con il luogo: mappa a 4 m
```

Per Marcello: doppio clic su `vedi-la-mappa.bat` (fuori da git) rifà e apre le mappe.

Ambiente: `py -3.12 -m venv .venv` e `pip install numpy scipy matplotlib pytest pyshp tifffile`
(niente `rasterio` né `pyproj`: Smart App Control blocca le loro DLL, `lessons.md` #31).

---

## Invarianti

- Ogni numero nei documenti ha la fonte accanto. Niente numeri a memoria.
- Prima di ogni misura si scrive la previsione; il risultato si registra anche se dà zero.
- Il modello si tara sugli studi pubblicati e sui dati aperti, non sulle opinioni: niente
  casi raccolti da noi (Marcello, 2026-09-26).
- Il simulatore predice solo dai dati del caso (animale, casa, zona, ora): nessun ingresso
  dopo la perdita, nessun volantino (Marcello, 2026-09-25).
- I dati dei proprietari non sono mai pubblici: stanno in `privato/` (fuori da git), mai
  nei documenti né nei test.

---

## Manutenzione

Quando nasce un documento in `docs/`, aggiungi la sua riga alla tabella. Quello che è
successo va in `docs/STATO.md`, non qui.
