# Operazioni Shopify — procedura (T-005)

Responsabile: shopify-operazioni. Stato: procedura scritta, **nessuna azione reale eseguita**. In fase di collaudo si usa solo l'adattatore simulato (`studio/adapters/mock.py`). Importi in centesimi di euro. I valori di commissione sono **ipotesi** (`config/policy.json`, stato `da_verificare`) finché non verificati sul gateway reale.

## 1. Scheda prodotto

Campi obbligatori (dal manifest approvato dal QA):
- titolo, sottotitolo, descrizione (cosa contiene, formato, requisiti, cosa NON include)
- handle/URL, categoria, tag, SKU = id prodotto del manifest
- prezzo e valuta; nessuna "variante" fisica; prodotto marcato come digitale (nessuna spedizione)
- file consegnato: nome, dimensione, **checksum SHA-256** (dal manifest)
- immagini con testo alternativo; politica rimborsi e contatto assistenza collegati
- metadati SEO (titolo, descrizione) per lingua

Multilingua:
- una versione per lingua di mercato, tradotta e rivista (non solo automatica); stesso SKU, handle per lingua
- le lingue pubblicate sono solo quelle con QA superato
- valuta e formato prezzo coerenti con il mercato

Prezzo IVA inclusa (mercati UE, regime OSS):
- il prezzo mostrato al consumatore UE è **IVA inclusa**; l'IVA si calcola in base al paese del cliente, con le aliquote vigenti (da verificare con il consulente/titolare, non da memoria)
- il netto = prezzo / (1 + aliquota); l'economia (`studio/economics.py`) lavora sul netto
- registrare paese, base imponibile e IVA per ordine (serve all'OSS)

Immagini e diritti:
- solo immagini create dallo studio o con licenza verificata; per ognuna: fonte, licenza, data, prova archiviata
- nessun marchio, volto o opera altrui senza liberatoria
- immagine senza diritti verificati = non caricata

Stato: ogni scheda nasce in **BOZZA** (non pubblicata, non visibile). Passa a pubblicata solo dopo verdetto QA approvato **e** decisione del titolare; la pubblicazione non è nel mandato di questo agente.

## 2. Checkout e pagamento

Impostazioni da predisporre (in bozza/test):
- paese e valuta del negozio EUR; solo prodotti digitali, spedizione disattivata
- checkout con email obbligatoria, consenso a condizioni, privacy e informativa sul diritto di recesso per contenuti digitali (consenso esplicito alla fornitura immediata e perdita del recesso, ove applicabile)
- prezzi IVA inclusa; riepilogo con IVA separata; fattura/ricevuta con dati fiscali del titolare
- IVA digitale UE: calcolo per paese del cliente, OSS, conservazione delle prove di localizzazione
- metodi di pagamento: carta e wallet del gateway; email di conferma con link di consegna
- pagina di ringraziamento con link download

Ordine di prova (senza spesa reale):
- negozio e gateway in **modalità test**, oppure codice sconto 100% usato solo internamente
- gateway di test: carte di prova fornite dal gateway; nessuna carta reale
- passi: aggiungi al carrello -> checkout -> ordine pagato (test) -> email -> link firmato -> download -> verifica checksum -> rimborso di prova
- l'ordine di prova è marcato `test: true` ed escluso da KPI e riconciliazione contabile reale
- il codice sconto 100% non va mai esposto ai creator né al pubblico; scadenza breve, uso singolo

## 3. Consegna digitale

- link **firmato** (HMAC lato server) con scadenza: predefinito **72 ore** e **5 download** per ordine
- il link contiene id ordine e firma, mai email o dati personali in chiaro
- scaduto/esaurito: errore chiaro con istruzione per richiedere il reinvio
- reinvio: su richiesta del cliente verificata (email dell'ordine); genera un nuovo link, invalida il precedente, registra l'evento; limite di reinvii (es. 3) oltre cui interviene il customer care
- verifica checksum: a ogni consegna e nel test, lo SHA-256 del file servito deve coincidere con quello del manifest; se differisce, consegna bloccata e allarme al QA
- il file non è mai servito da URL pubblico non firmato
- i download sono contati per ordine (idempotente)

## 4. Tracciamento

Eventi minimi, tutti con `order_id` quando esiste (altrimenti `session_id` anonimo):

| Evento | Quando | Campi minimi |
|---|---|---|
| view_item | vista scheda | sku, lingua, utm, creator_code |
| add_to_cart | aggiunta al carrello | sku, prezzo_cents |
| begin_checkout | avvio checkout | sku, prezzo_cents, paese |
| purchase | ordine pagato | order_id, sku, lordo_cents, iva_cents, netto_cents, paese, sconto, creator_code |
| refund | rimborso | order_id, importo_cents, tipo (totale/parziale), motivo |

Attribuzione creator:
- UTM standard: `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`; convenzioni minuscole, senza spazi
- ogni creator ha un codice sconto univoco; l'ordine riporta il codice e l'UTM; in conflitto prevale il codice (regola da confermare con creator-partnership)
- le commissioni creator si calcolano sul netto (policy) e sono soggette a clawback entro la finestra prevista

Privacy:
- **nessun dato personale nei log interni**: niente email, nome, indirizzo, IP, telefono; si usano `order_id`, hash non reversibili e paese
- i log non contengono token, firme complete dei link né dati di pagamento
- retention minima; accesso ai dati personali solo nel pannello del negozio

## 5. Riconciliazione ordini

Deduplica:
- chiave unica = `order_id`; i webhook possono arrivare più volte, fuori ordine o in ritardo
- ogni ordine è contato **una sola volta**: elaborazione idempotente (se `order_id` già presente, si ignora l'evento duplicato e si registra solo il conteggio dei duplicati)
- eventi successivi (rimborso) si agganciano allo stesso `order_id` con un proprio id evento per evitare doppi rimborsi

Rimborsi:
- totale: ordine annullato nel netto, link invalidato, commissione creator stornata (clawback)
- parziale: importo e IVA proporzionali; il saldo residuo resta ricavo; link valido salvo decisione del customer care
- la somma dei rimborsi non può superare il lordo dell'ordine; oltre = anomalia da segnalare
- le **commissioni di pagamento non vengono rimborsate** dal gateway (`commissione_pagamento_rimborsata_su_refund: false`): restano un costo; il costo effettivo di un ordine rimborsato è la sola commissione trattenuta (ipotesi 2,90% + 30 cent, da verificare)

Riconciliazione con i payout del gateway:
- per ogni payout: elenco transazioni, lordo, commissioni, rimborsi, netto accreditato
- confronto con gli ordini del negozio: stesso `order_id`/transaction id, stesso importo
- differenze classificate: ordine mancante, importo diverso, duplicato, rimborso non registrato, commissione diversa dall'ipotesi
- report periodico: ordini unici, lordo, IVA, netto, commissioni pagamento, rimborsi, commissioni creator, margine; ogni scostamento va spiegato prima di chiudere il periodo
- i dati di prova e sintetici sono marcati `"sintetico": true`/`test: true` e mai sommati ai reali

## 6. Accessi da chiedere al titolare (pacchetto unico)

Da raccogliere in **un solo passaggio** (`team/azioni_titolare.json` tramite Team Lead; mai direttamente dall'agente). Nessuna di queste azioni è eseguita da noi:
1. creazione del negozio e scelta/attivazione del piano (costo da riservare prima nel registro `studio/ledger.py`)
2. verifica dell'identità (KYC) e configurazione dei payout (IBAN) sul gateway
3. autorizzazione di app/token API con **scope minimi**, creando una app personalizzata nel negozio:
   - `read_products`, `write_products` (schede in bozza)
   - `read_orders` (solo ordini recenti; evitare `read_all_orders` se non serve)
   - `read_customers`: NON richiesto (dati personali non necessari)
   - `read_discounts`, `write_discounts` (codici creator e sconto di prova)
   - `read_files`, `write_files` (file della consegna digitale)
   - `read_analytics`/report: solo se necessario alla riconciliazione
   - niente scope su pagamenti, rimborsi, impostazioni, utenti o checkout: i rimborsi si fanno dal pannello dal titolare/customer care
   - webhook: `orders/paid`, `refunds/create`, `orders/cancelled`, con verifica HMAC
4. dominio: acquisto/collegamento, DNS, certificato (costo da riservare nel registro)

Gestione del token: resta **nel gestore segreti dell'ambiente**; mai in file, prompt, log, commit o output. In caso di sospetta esposizione: revoca e rigenerazione dal titolare.

## 7. Checklist prove dal vivo prima del lancio

Da eseguire solo dopo autorizzazione del titolare, in modalità test dove possibile:
- [ ] scheda in bozza corretta in tutte le lingue; prezzi IVA inclusa; nessuna immagine senza diritti
- [ ] politiche (privacy, condizioni, rimborsi, recesso digitale) pubblicate e collegate
- [ ] checkout in test: ordine pagato, email ricevuta, ricevuta con IVA corretta per almeno 3 paesi UE
- [ ] link firmato funzionante; dopo 72 ore (o scadenza forzata) rifiuta; dopo 5 download rifiuta
- [ ] reinvio link: nuovo link valido, vecchio invalidato
- [ ] checksum del file scaricato = manifest
- [ ] 5 eventi di tracciamento visibili con `order_id` coerente; UTM e codice creator registrati
- [ ] webhook inviato due volte: ordine contato una volta
- [ ] rimborso parziale e totale di prova: importi, link e clawback corretti
- [ ] commissione di pagamento non rimborsata riflessa nel report
- [ ] riconciliazione di un payout di test senza scostamenti non spiegati
- [ ] log controllati: nessun dato personale, token o firma completa
- [ ] token nel gestore segreti, assente da repository e log
- [ ] nuovo ordine reale di piccolo importo (se autorizzato) rimborsato e riconciliato
- [ ] verdetto QA approvato e decisione del titolare registrata prima di pubblicare
