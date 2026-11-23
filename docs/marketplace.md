# Scelta dei marketplace per prodotti digitali

Responsabile: acquisizione. Dati in `config/canali_vendita.json`. Fase: Catalogo multicanale.

Stato dei dati: tutte le cifre e i punteggi attuali sono **ipotesi** (2026-11-23). Le pagine ufficiali delle tariffe non erano raggiungibili dalla sessione (host fuori dalla rete consentita) e una ricerca web ha dato solo fonti secondarie, non verificabili. Nulla qui è un fatto osservato. Prima di ogni decisione commerciale ogni cifra va verificata sulla pagina ufficiale (sola lettura, senza account) e la fonte portata a `osservata` con url e data.

## Ambito

Prodotti digitali scaricabili (PDF, template, pacchetti di file) venduti in più lingue. Il sito proprio (Shopify) è sempre nel catalogo. I marketplace sono canali aggiuntivi, ammessi solo se superano la soglia. Nessun account, listing o pubblicazione in questa fase.

## Criteri (punteggio intero 0-10)

| Criterio | Peso | Cosa si valuta |
|---|---|---|
| pubblico | 20 | Corrispondenza tra gli acquirenti del marketplace e il compratore del prodotto, per lingua e paese |
| domanda | 20 | Segnali osservabili: ricerche, recensioni, vendite visibili, numero di offerte concorrenti per la nicchia |
| regole_prodotto | 15 | La categoria e il formato sono ammessi dalle regole del venditore |
| regole_ai | 15 | Politiche sui contenuti generati con AI e obbligo di dichiararli |
| commissioni | 15 | Più il costo totale è basso, più il punteggio è alto |
| consegna | 5 | Il download è gestito dalla piattaforma (link, limiti, riemissione) |
| integrazione | 10 | API, feed, esportazione ordini, riconciliazione dei pagamenti |

I pesi sono in `config/canali_vendita.json` e sommano a 100.

### Guida ai punteggi

- 0: non ammesso o non verificabile in modo sfavorevole. 5: ammesso con vincoli o dati incerti. 10: pienamente adatto e verificato.
- regole_prodotto e regole_ai: 0 solo se la regola vieta il prodotto o l'uso dell'AI che il prodotto richiede. Se la regola non è stata letta, il punteggio non può superare 5 e la fonte resta `ipotesi`.
- regole_ai: 10 se l'AI è ammessa senza obblighi gravosi; 6-7 se ammessa con dichiarazione obbligatoria; 1-3 se ammessa solo in casi limitati.
- commissioni: calcolate sul costo totale per un ordine tipo (percentuale + quota fissa + canone ripartito), non sulla sola percentuale. Indicativo: sotto 5% = 9-10, 5-10% = 6-8, 10-20% = 4-5, oltre 30% = 0-3.
- consegna: 10 se la piattaforma consegna e riemette il download; 5 se serve un'app o un passaggio manuale.
- integrazione: 9-10 API completa con ordini e payout; 5 feed o esportazione CSV; 0-2 solo gestione manuale.

## Regole di ammissione

1. **Esclusione**: un candidato con `regole_prodotto` = 0 oppure `regole_ai` = 0 è escluso, qualunque sia il punteggio totale.
2. **Punteggio pesato** = somma(peso x punteggio) / 10, su scala 0-100.
3. **Ingresso**: il marketplace entra nel catalogo con punteggio pesato >= `soglia_minima` (60). Sotto soglia resta in elenco, non attivo.
4. Il sito proprio non è soggetto alla soglia ma ha gli stessi criteri, per confronto.
5. Un punteggio basato su `ipotesi` può portare a un'ammissione solo provvisoria: l'attivazione richiede la verifica delle regole su fonte `osservata`.

Esempio con i valori attuali (ipotesi): Etsy 75,5, Shopify 70, Gumroad 64 (ammessi); Creative Market 48 e Teachers Pay Teachers 47 (sotto soglia).

## Confronto con il sito proprio sul margine per ordine

Il punteggio decide l'ammissibilità; il margine decide dove spingere. Per ogni canale e per un ordine tipo (prezzo P, IVA esclusa, costo di produzione e AI per unità C):

- costo canale = P x commissione_pct_bp / 10000 + commissione_fissa_cents + canone_mensile_cents / ordini mensili previsti
- margine per ordine = P - costo canale - C - rimborsi attesi (tasso x P) - sconti medi
- delta rispetto al sito = margine marketplace - margine Shopify

Regole di lettura:

1. Si confrontano margini in centesimi interi, mai ricavi lordi.
2. Il canone del sito è ripartito sugli ordini mensili previsti: con pochi ordini il sito proprio costa di più per ordine. Il confronto va fatto con più volumi (basso, atteso, alto).
3. Il sito proprio ha costo di acquisizione del traffico (Ads, creator), il marketplace porta traffico organico incluso nella commissione. Il costo di acquisizione per ordine va sottratto dal sito, non dal marketplace, solo se il traffico del marketplace è dimostrato dai dati osservati.
4. Un marketplace con margine per ordine inferiore a quello del sito ma domanda dimostrata resta ammesso come canale di scoperta, con un tetto di quota di ordini.
5. Un margine per ordine <= 0 su un canale lo sospende, anche con punteggio >= 60.
6. Le valute diverse dall'euro vanno convertite con un cambio dichiarato e datato; finché non è verificato, la cifra è `ipotesi`.

## Qualità delle vendite per canale

Oltre al margine si registrano per canale: tasso di rimborso, sconti medi, ricorrenza degli acquirenti e ordini riconciliati con il pagamento. Un canale con rimborsi sopra la soglia di `config/policy.json` si ferma secondo le regole di stop, con il minimo di ordini per giudicare (D-007).

## Dichiarazione AI

Dove l'AI va dichiarata, la dichiarazione è un requisito di pubblicazione di ogni scheda e di ogni lingua. Il testo di ogni dichiarazione e la sua fonte vanno registrati nel catalogo. Nessuna scheda viene creata in questa fase.

## Verifica dei dati

Per ogni canale, in sola lettura: pagina tariffe, regole di categoria, politica AI, documentazione API. Per ogni dato: fonte `osservata` con url e data oppure `ipotesi`. I dati sono rivalutati almeno ogni 90 giorni o a ogni cambio di tariffa annunciato.

## Escalation

- Al Team Lead se un costo massimo non è noto o se un canale richiede un canone che supera il residuo della categoria.
- A QA se una regola AI o di prodotto è ambigua: nel dubbio il punteggio non supera 5 e il canale non si attiva.
- Account, pagamenti e accettazione dei termini restano al titolare (`AZIONI_TITOLARE.md`).
