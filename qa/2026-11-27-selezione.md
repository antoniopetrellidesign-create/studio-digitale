# QA T-033 — Verifica prima della selezione: V2-T031-3-44 e V2-T031-1-007

Data: 2026-11-27 · Agente: qa-indipendente · Ambito: sola lettura di `research/`, `studio/phases.py`, `config/policy.json`, `docs/metodo-ricerca.md` §0, `DECISIONI.md` D-028/D-038.

## Verdetto

| Scheda | Motore (punteggio, fonti_osservate) | Verdetto QA |
|---|---|---|
| research/V2-T031-3-44.json (Wareneinsatz DE) | 65, 2 | **NON SELEZIONABILE** (BLOCCATO) |
| research/V2-T031-1-007.json (ISO 9001 DE) | 60, 2 | **NON SELEZIONABILE** (BLOCCATO) + escalation al Team Lead |

Comando eseguito (richiesto):
```
python3 -c "import json; from studio.phases import punteggio, fonti_osservate; [print(f, punteggio(json.load(open(f))), fonti_osservate(json.load(open(f)))) for f in ['research/V2-T031-3-44.json','research/V2-T031-1-007.json']]"
research/V2-T031-3-44.json 65 2
research/V2-T031-1-007.json 60 2
```
Ricalcolo manuale con PESI_V2 (20/20/15/15/15/8/7): Wareneinsatz 140+100+120+90+90+64+49 = 653 → 65; ISO 140+100+105+90+90+40+35 = 600 → 60. Il motore è aritmeticamente corretto. Con soglia 60 e minimo 2 fonti (`config/policy.json` → `selezione`), `h_selezione` (studio/phases.py:142-144) le dichiarerebbe **entrambe idonee**: il blocco serve proprio a impedirlo.

## Causa principale del blocco (comune alle due schede)

`fonti_osservate` (studio/phases.py:81-82) conta ogni fonte con `tipo == "osservata"` + url + data, **senza guardare `livello` né l'indipendenza**. In entrambe le schede il conteggio 2 = 1 pagina letta (Amazon.de) + 1 estratto di scansione mai letto:
- V2-T031-3-44.json:14 — softguide.de, `risultato_di_ricerca`, "Pagina non letta integralmente".
- V2-T031-1-007.json:14 — digistore24.com, `risultato_di_ricerca`, "Prezzi non letti".

Prove: `grep -n "softguide\|473973" research/fonti/indice.jsonl` → nessuna riga; nessun file in `research/fonti/`. L'unica origine è la scansione (`research/scansione/T031-3.jsonl:44`, `research/scansione/T031-1.jsonl:7`), cioè un riepilogo del risultato di ricerca. Inoltre ciascun estratto attribuisce a **un solo URL** affermazioni di editori diversi (softguide: anche "WKW Kalkulationshandbuch gratuito"; digistore24: anche Forum Verlag, Etsy 132 documenti, WEKA), quindi il contenuto non è riconducibile alla fonte citata.

Criterio violato: metodo v2 §0, stadio (d) "almeno 2 fonti osservate **indipendenti**". Un estratto non salvato non permette di dimostrare l'indipendenza né l'assenza di contenuto ripetuto (controllo 2 non superabile). Le schede lo dichiarano da sole: V2-T031-3-44.json:38 "Non candidata: ... la fonte letta e una sola"; V2-T031-1-007.json:38 "non candidata finche non ci sono 2 fonti osservate indipendenti". Il motore porta sopra soglia schede che i ricercatori stessi qualificano come non candidate.

## Controlli per scheda

### A. V2-T031-3-44 — Wareneinsatz DE

1. **Fonte letta: integrità OK.** `research/fonti/indice.jsonl:15` ha stesso URL, `livello: letta_integralmente`, impronta `1d755b27…6eadd7`, file `2026-11-27-1d755b27fb09.txt`, 10817 caratteri. Lo SHA-256 del corpo del file (dopo l'intestazione, come in `studio/fonti.py:117-120`) ricalcolato = `1d755b27fb0973b93939ad1658ab82c5d04e30cb674b2ecda91a8ace2b6eadd7`, 10817 caratteri: coincide. (Lo sha256sum dell'intero file differisce solo per l'intestazione: atteso.)
   **Dati citati: tutti presenti** nel file `research/fonti/2026-11-27-1d755b27fb09.txt`:
   - r.198 "1-16 of 120 results"
   - r.268-277 Graf 2018 "Praxisbuch mit Beispielen & Excel Tools", 4.1, (32), Paperback, USD 58.54
   - r.300-309 Graf 2019 "Download von 7 Excel Tools", 4.5, (32), USD 61.58
   - r.464-473 "Mein Gastronomie Businessplan … Ausfüllbuch mit Beispielen & Excel-Tools", 4.2, (44), USD 60.60
   - r.236-245 "Wo dein Geld hingeht" (5 Aug 2026), 5.0, (1), USD 35.95
   - r.228-230 "Delivers to United States": giustifica i prezzi in USD.
   Osservazione: 3 dei 16 risultati non sono pertinenti (edilizia: r.247 "Kalkulation kompakt … Baupraxis", r.316 "Kostenermittlung … Bauprojekt"); la scheda non lo dice.
2. **Indipendenza: NON DIMOSTRATA** (vedi causa principale). Domini diversi (amazon.de / softguide.de), ma la seconda fonte non è letta.
3. **Ipotesi/osservata: OK.** Fonte 1 dichiara "vetrina di libri fisici, prova di domanda e di disponibilita a pagare, NON prova di vendite di prodotti digitali"; prezzo 69 €, costi, margine, rimborsi marcati ipotesi (fonte 3, `accesso_pubblico.natura`). Limite non dichiarato: i prezzi USD sono per consegna verso gli USA, non i prezzi pagati da compratori DE; usarli come disponibilità a pagare in Germania è un'ipotesi.
4. **Punteggi.** `problema` 7: al limite. La pagina mostra libri generali su Gastronomie con 32-44 valutazioni accumulate in 7-8 anni; la nota stessa (r.29) ammette "non conferma dolore ricorrente". Accettabile come 6-7; con 6 il punteggio sarebbe 63, quindi non cambia il superamento della soglia. `concorrenza` 6: non > 6, coerente. `offerta` 8: nessuna promessa di utile o di calo dei costi, nessuna urgenza; garanzia legata a un esito verificabile dal compratore (calcolo di 10 piatti). **Rilievo:** "ancoraggio … confronto con il prezzo reale di un libro" (r.31) confronta un Excel da 69 € con un libro cartaceo da USD 58.54 venduto verso gli USA: non è un prezzo di riferimento omogeneo per il compratore DE (D-038 punto 2, pubblicità comparativa). Va tolto o riformulato prima della pagina di vendita.
5. **Regolamentazione:** nessuna categoria regolamentata. Esclusioni adeguate (r.37: niente consulenza fiscale/HACCP). Nessuna escalation.

**Verdetto A: NON SELEZIONABILE** finché non c'è una seconda fonte indipendente letta e salvata (es. `python3 -m studio fonti leggi https://www.softguide.de/programm/rezeptrechner-pro` se l'host è consentito, oppure una pagina di un concorrente digitale).

### B. V2-T031-1-007 — ISO 9001 DE

1. **Fonte letta: integrità OK.** `research/fonti/indice.jsonl:24`: stesso URL, `letta_integralmente`, impronta `3a663ccc…387f9df`, file `2026-11-27-3a663ccc2035.txt`, 12820 caratteri; SHA-256 del corpo ricalcolato identico, 12820 caratteri.
   **Dati citati: tutti presenti** in `research/fonti/2026-11-27-3a663ccc2035.txt`:
   - r.198 "1-16 of 608 results"
   - r.268-295 Dokumentations-Paket (Ibrahim), 5.0, (2), Hardcover USD 234.77, Paperback 232.34
   - r.563-572 Dokumentationspaket für Kleinunternehmen, 1.0, (1), Hardcover 229.99
   - r.376-391 Audit-Kit, 2.4, (2), Kindle USD 187.79
   - r.222-233 "Best Seller in Quality Assurance", "… ISO 9001:2026 für Dummies", (1), USD 32.31
   - r.541-550 "ISO 9001 einfach einführen", USD 20.53
   - r.420 / r.252 guide di transizione USD 15.40 / 26.69
   - r.482-491 "DIN EN ISO 9001:2026 - was sich bald ändert", 2.0, (2), USD 69.84
   - r.527-533 "DIN EN ISO 9001:2026 - Vergleich", 15 Feb 2027, USD 267.05
   Omissione: la pagina mostra anche titoli con molte più valutazioni (r.502-507 "Audits nach ISO 9001:2015 einfach erklärt", 4.6, (88); r.446-451 Kamiske, 4.7, (44)). Non cambia il quadro, ma "valutazioni molto poche" vale per i pacchetti, non per tutta la pagina.
2. **Indipendenza: NON DIMOSTRATA** (vedi causa principale). La fonte Digistore24 è un estratto che aggrega 4 editori sotto un URL.
3. **Ipotesi/osservata: OK.** La fonte 1 dichiara "libri fisici = domanda e disponibilita a pagare, NON vendite di prodotti digitali"; l'effetto della nuova edizione sulla domanda e i requisiti ISO 9001:2026 sono marcati come ipotesi (r.10, fonte 3).
4. **Punteggi: problema 7 non giustificato dalla pagina letta.** La nota stessa (r.29) dice "valutazioni e recensioni pero molto poche"; i pacchetti più vicini all'offerta hanno 1-2 valutazioni (r.273, r.381, r.568) e il "Best Seller" ha 1 valutazione (r.229). 608 risultati e molte uscite 2026 indicano **offerta** editoriale in aumento, non dolore dei compratori. Con `problema` = 6 il punteggio scende a 580 → **58 < 60**. La scheda supera la soglia solo grazie a un voto contestabile: criterio "punteggi coerenti con le evidenze" non soddisfatto. `concorrenza` 6: coerente. `offerta` 7: nessuna urgenza finta; la scheda esclude esplicitamente la garanzia di certificazione e di esito dell'audit (r.31). La promessa "in un fine settimana" è marcata come ipotesi da testare: non va usata in pubblicità prima del test.
5. **Regolamentazione: SERVE ESCALATION al Team Lead.** Una norma ISO volontaria non è una "categoria regolamentata" in senso stretto, ma il prodotto: (a) promette una "gap analysis per la transizione" verso ISO 9001:2026, il cui testo non è stato letto da fonte ufficiale (r.15, fonte 3; la pagina mostra il confronto DIN in uscita il 15 Feb 2027, r.529): rischio di contenuti errati e di affermazioni ingannevoli (UWG/norme UE richiamate da D-038 punto 2); (b) il testo delle norme ISO/DIN è protetto da diritto d'autore (già annotato, r.37); (c) l'uso del nome ISO va limitato al riferimento descrittivo, senza loghi né formule tipo "zertifizierungsfähig" (ipotesi da verificare sulle condizioni d'uso di ISO/DIN); (d) l'assistenza è "media" e richiede competenza tecnica (costo_sviluppo 5). Servono una verifica dello stato ufficiale della norma e una revisione di un esperto prima di qualsiasi pagina di vendita.

**Verdetto B: NON SELEZIONABILE**: seconda fonte indipendente non letta; punteggio 60 dipendente da un `problema` 7 non sostenuto (58 con 6); rischio di conformità e diritto d'autore da sottoporre al Team Lead.

## Altri controlli
- Credenziali: `grep -i -E "password|token|api[_-]?key|sk_|shpat|secret"` sulle due schede → 0 righe.
- Spesa e azioni esterne: nessuna spesa né azione esterna nelle schede; costi solo ipotetici. Nessuna lettura di rete fatta dal QA.

## Proposte (ai responsabili, tramite coda)
1. **team-lead** (`studio/phases.py`): per `metodo_versione` = 2, `fonti_osservate` (o un nuovo controllo usato da `h_selezione` e da Q4) dovrebbe contare solo fonti `letta_integralmente` presenti in `research/fonti/indice.jsonl` con stessa impronta, e con host distinti. Oggi un estratto non letto completa il minimo di 2.
2. **ricerca-mercato**: leggere e salvare una seconda pagina indipendente per ciascuna scheda; dividere gli estratti che aggregano più editori sotto un solo URL; per ISO portare `problema` a 6 o motivare il 7 con una pagina che mostri domanda (non offerta editoriale); togliere l'ancoraggio al prezzo del libro nella scheda Wareneinsatz.
3. **team-lead**: decidere sull'escalation ISO 9001 (verifica ufficiale della norma 2026, revisione di un esperto, limiti d'uso del nome).

Nota di processo: T-033 non compare in `python3 -m studio queue list`; il QA non ha modificato la coda perché il mandato di questo incarico limita la scrittura a `qa/`. Nessun test `tests/test_qa_*.py` aggiunto per lo stesso motivo; il test proposto: due schede v2 con 1 fonte letta + 1 `risultato_di_ricerca` non devono risultare idonee in `h_selezione`.

---

## Riverifica T-035 — V2-T031-3-44 (Wareneinsatz DE), dopo D-039

**Verdetto: SELEZIONABILE** — al limite (60,3 su soglia 60), solo per il test di validazione STRATEGIA.md §9.5, non per lo sviluppo.

1. **Fonte softguide.de: dati presenti.** Indice `research/fonti/indice.jsonl:28`: stesso URL, host `www.softguide.de`, `letta_integralmente`, impronta `06ddd0a4…5a969`, 11589 caratteri. SHA-256 del corpo ricalcolato (come `studio/fonti.py:117-120`) = `06ddd0a4b7e1d4782bdb7d7b85c403ed0803f5014ac86f53090ff733b9f5a969`, 11589 caratteri: coincide (idem Amazon, `1d755b27…6eadd7`, 10817). Righe di `research/fonti/2026-11-27-06ddd0a4b7e1.txt`:
   - prezzi: r.341 "ab 150,-", r.344 "zzgl. 19% MwSt", r.346 "jährlich", r.348 "50 Rezepte & Zutaten, Verwaltung & Etiketten Kennzeichnung"; r.350 "290,-", r.353, r.355, r.357 "250 Rezepte & Zutaten, + Preiskalkulation"; r.359 "500,-", r.362, r.364, r.366 "500 Rezepte & Zutaten; weitere Funktionen".
   - funzioni: r.147 "Kalkulation (Wareneinsatz, Verkaufspreise pro Mahlzeit, pro 100g)"; r.169 "Wareneinsatz berechnen für Gastronomie (Restaurants, Bistros, Pizzeria)"; r.155/159 Speiseplan, Einkaufslisten "(Paket L)"; r.207 "CSV und Excel-Export (Paket L)"; r.427 import ricette e "Rohstoffpreise … per Excel hochladen"; r.423 registrazione gratuita, funzioni di base, Jahreslizenz; r.439 risposta "innerhalb von 24 Stunden"; r.410 "Vom Einzelbetrieb bis zum Team"; r.115 "Aktualisiert am 06. Nov 2026".
   - Due rilievi minori (non bloccanti): "150 EUR … senza Preiskalkulation" è una deduzione da r.357 ("+ Preiskalkulation"), non un testo letto; la nota `problema` dice che softguide "mostra spesa esistente", ma la pagina mostra un'**offerta** a pagamento (scheda redatta dal venditore, r.115), non acquisti. Da riformulare.
2. **Indipendenza: OK.** Host diversi (`www.amazon.de`, `www.softguide.de`), editori diversi (vetrina libri / catalogo software con testo del produttore), nessun contenuto ripetuto. `phases.fonti_osservate` = 2.
3. **Punteggi.** Somma pesata (`PESI_V2`): 6·20 + 5·20 + 8·15 + 6·15 + 4·15 + 8·8 + 7·7 = 603 → 60. Margine sulla soglia: 3 punti su 1000. **Qualsiasi** criterio ridotto di 1 porta sotto soglia: problema 5 / accesso 4 → 583 → 58; offerta 7 / margine 5 / concorrenza 3 → 588 → 58; costo_sviluppo 7 → 595 → 59; assistenza 6 → 596 → 59 (riprodotto in `tests/test_qa_selezione_wareneinsatz.py`).
   - `problema` 6: sostenuto per "già pagato" (libri 58-62 USD, 32-44 valutazioni; SaaS a 150-500 €/anno); frequenza e dolore non provati (la scheda lo dice). È il massimo difendibile, non sovrastimato.
   - `accesso` 5: nessuna evidenza sul canale; è esattamente il tetto "senza evidenza, massimo 5" (`docs/metodo-ricerca.md:101`). Consentito, ma è il voto più generoso possibile: il CPA 20 € è un'ipotesi.
   - `offerta` 8: rispetta la fascia 7-10 (`docs/metodo-ricerca.md:29`): risultato verificabile (10 piatti calcolati), 2 bonus a costo ~0, garanzia sostenibile: r* = 1 − (2,30 + 20)/57,98 = 61,5% a 69 €. Nessuna fonte distingue 8 da 7: è il voto meno sostenuto; con 7 → 58.
   - `concorrenza` 4: coerente (concorrente diretto letto, prezzo annuo 178,50 € IVA incl. contro 69 € una tantum; lacune solo ipotizzate).
   Conclusione: nessun criterio viola la rubrica scritta, quindi non c'è base verificabile per un blocco; ma il superamento dipende da `offerta` 8 e da `accesso` al tetto. Il Team Lead deve trattare 60 come "candidata per validazione", non come prova.
4. **Correzioni: applicate.** `note_punteggi.offerta` (r.31): "nessun ancoraggio di prezzo al costo di libri (rimosso su indicazione QA)", "Nessuna promessa di utile o di calo costi, nessuna urgenza finta"; il tempo "2 ore" marcato ipotesi; `esclusioni` (r.37) "Nessuna promessa di guadagno". I prezzi dei libri restano solo come evidenza di disponibilità a pagare (r.11, r.13), non come ancoraggio.
5. **Motore e test.** `python3 -c "…phases.punteggio(o), phases.fonti_osservate(o)…"` → `60 2`, soglie `config/policy.json` `punteggio_minimo` 60, `fonti_osservate_minime` 2 → idonea `True`. `timeout 300 python3 -W ignore -m unittest discover -s tests` → `Ran 210 tests … OK` (prima dell'aggiunta del test QA); `python3 -m unittest tests.test_qa_selezione_wareneinsatz` → 4 test OK. Credenziali nella scheda: 0 righe con il grep di cui sopra. Nessuna spesa, nessuna lettura di rete eseguita dal QA.

**Condizioni** (ai responsabili via coda): ricerca-mercato riformula "spesa esistente" → "offerta a pagamento esistente" e marca la deduzione sul pacchetto da 150 €; la pagina di vendita del test §9.5 non usa la promessa "2 ore" né confronti con prezzi di libri o del SaaS; se il test non misura accesso (CPA reale) e disponibilità a 69 €, la scheda non passa allo sviluppo.
