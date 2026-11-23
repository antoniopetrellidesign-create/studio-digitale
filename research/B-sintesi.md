# Sintesi ricerca T-018B - prodotti digitali per consumatori e apprendimento

Data: 2026-11-23. Responsabile: ricerca-mercato. Schede: `research/B-<id>.json`. Fonti bloccate: `research/fonti-bloccate-B.md`.

## Limite delle evidenze (leggere prima)

- WebFetch non ha funzionato su nessun host provato (finanztip.de, etsy.com, redopositor.com, money.it, payhip.com: `getaddrinfo ENOTFOUND`). Nessuna pagina e stata aperta.
- Le fonti "osservata" sono pagine che WebSearch ha restituito come risultato, con il riepilogo di WebSearch (titoli, prezzi, descrizioni). Ogni fonte ha il campo `metodo` che lo dichiara. Un ricontrollo reale richiede di aprire l'URL.
- Nessun volume di ricerca, numero di vendite o recensioni e stato osservato, salvo "53 vendite" su un listing Creative Market (da riepilogo, non verificato).
- Commissioni, prezzo di vendita, costo di sviluppo e costo di accesso sono ipotesi (config/canali_vendita.json, config/policy.json, stime del ricercatore). Le tariffe ufficiali Etsy/Shopify non sono state aperte.
- Conversione USD in EUR non verificata: i prezzi USD sono confrontati 1:1 solo come ordine di grandezza.
- Soglia (metodo sez. 7): punteggio >= 60 e almeno 2 fonti osservate indipendenti per il mercato. **Nessuna nicchia supera 60.** Nessuna e candidata.

Assunzione di margine comune (ipotesi): margine = (prezzo - commissione Etsy 950 bp - 45 cent - 200 cent di costo di accesso per vendita) / prezzo. Il costo di sviluppo e unico e non e nel margine per unita. Canale sito Shopify: 290 bp + 30 cent + canone 3900 cent/mese (ipotesi), con 20 ordini al mese il canone vale 195 cent per ordine: senza traffico proprio non e competitivo a prezzi sotto 15 EUR. Creator: 30% sul netto, non considerato nel margine perche il canale non e dimostrato.

## Punteggi (motore: somma voto/10 x peso)

| Scheda | Probl. 25 | Acc. 20 | Marg. 20 | Conc. 15 | Svil. 10 | Ass. 10 | Totale |
|---|---|---|---|---|---|---|---|
| B-de-haushaltsbuch | 6 | 5 | 7 | 3 | 8 | 7 | 58,5 |
| B-es-planificador-oposiciones | 7 | 5 | 5 | 5 | 6 | 7 | 58,0 |
| B-en-language-learning-planner | 6 | 6 | 6 | 2 | 7 | 8 | 57,0 |
| B-it-bilancio-familiare | 6 | 5 | 6 | 3 | 8 | 7 | 56,5 |
| B-en-home-maintenance-binder | 5 | 6 | 6 | 3 | 7 | 8 | 56,0 |
| B-fr-classeur-administratif | 5 | 4 | 6 | 5 | 6 | 6 | 52,0 |

Calcolo calcolato a mano, il motore deve ricalcolarlo. I voti hanno motivazione in `note_punteggi` di ogni scheda.

## Nicchie

### 1. DE - Haushaltsbuch-Vorlage (58,5)
- **Osservato** (WebSearch): molti listing Etsy DE di Haushaltsbuch come download; Digistore24 a 5,88 EUR; un Finanzplaner all-in-one a 38,16 EUR; Finanztip e C&A offrono versioni gratuite.
- **Stime**: gamma prezzi 5,88-38,16 EUR indica spazio per una fascia media; la presenza di piu venditori indica domanda, non quantificata.
- **Ipotesi**: prezzo 12,90 EUR; margine 71,5%; sviluppo 15 EUR; accesso 2 EUR.
- **Motivazione**: margine decente e sviluppo facile, ma i gratuiti autorevoli e l'affollamento limitano la concorrenza superabile (3). Differenziazione possibile: guida in tedesco, versione PDF + Sheets, nessuna app.
- Canali: Etsy DE (osservato), Shopify (ipotesi, canone non coperto), creator e organico non verificati.

### 2. ES - Planificador para oposiciones (58,0)
- **Osservato**: OpositaTest, Preparaoposiciones, MAD offrono planificadores gratuiti; Payhip vende un Excel a 3,99 EUR; Redopositor annuncia un Planificador Pro a 49 EUR (79 barrato), ancora in lista d'attesa.
- **Stime**: bisogno ricorrente e ad alta posta per chi prepara concorsi; la fascia tra 3,99 e 49 EUR potrebbe avere spazio.
- **Ipotesi**: prezzo 6,90 EUR; margine 54,9%; sviluppo 20 EUR; disponibilita a pagare non verificata.
- **Motivazione**: il problema e il piu forte (7), ma il prezzo e basso e il canale organico e occupato dai concorrenti gratuiti. Nessun esito di concorso va promesso.
- Il test del prezzo del Planificador Pro (lancio in corso) e il dato piu utile da seguire in fase commerciale.

### 3. EN - Language learning planner (57,0)
- **Osservato**: listing Etsy da 1,40 a 15,90 USD (planner, pack, bundle, versioni Sheets e GoodNotes); un listing Creative Market con 53 vendite dichiarate (da riepilogo).
- **Stime**: sotto-nicchie per lingua (coreano, giapponese, ecc.) potrebbero distinguere, ma la domanda per lingua non e osservata.
- **Ipotesi**: prezzo 7,90 EUR; margine 59,5%.
- **Motivazione**: saturo (concorrenza 2); accesso discreto per presenza dei canali.

### 4. IT - Bilancio familiare (56,5)
- **Osservato**: shop Etsy IT con fogli di budget a circa 1,39-7,85 EUR (7,85 scontato da 31,40); modelli gratuiti Banca d'Italia e Microsoft citati da Money.it; Affari Miei Bilancio Familiare Smart.
- **Stime**: domanda IT presente ma prezzi bassi e concorrenza gratuita autorevole.
- **Ipotesi**: prezzo 9,90 EUR; margine 65,8%.
- **Motivazione**: concorrenza 3; differenziazione possibile (coppie, adattamento italiano, versione Sheets) non dimostrata.
- Nota Team Lead: finanza domestica e solo tracciamento; mai consigli su investimenti, tasse o prestiti.

### 5. EN/US - Home maintenance binder (56,0)
- **Osservato**: molti listing Etsy da 3,50 a 32,94 USD, sconti frequenti (prezzi barrati).
- **Stime**: categoria affollata e scontata.
- **Ipotesi**: prezzo 9,90 EUR; margine 65,8%.
- **Motivazione**: domanda dedotta solo dai listing; due URL dello stesso sito contano come una fonte indipendente, quindi anche la soglia fonti non e rispettata.

### 6. FR - Classeur administratif (52,0)
- **Osservato**: Etsy a 3,25 EUR; pack Classeur Maison a 25 EUR; guida PDF su ComeUp; alternative gratuite lock.pub e Gard.
- **Stime**: poche offerte a pagamento osservate, ma anche pochi segnali di domanda.
- **Ipotesi**: prezzo 12,90 EUR; margine 71,5%.
- **Motivazione**: accesso debole (4); rischio di sconfinare in indicazioni legali sulle durate di conservazione (escalation al Team Lead se si procede).

## Nicchie scartate (senza scheda)

| Nicchia | Motivo |
|---|---|
| DE - Reiseplaner / Urlaubs-Checkliste | Osservato (WebSearch): offerta quasi solo gratuita da marchi grandi (ADAC, Check24, Clockify, Jotform, Zoho, Asana, ClickUp, Urlaubsguru). Nessun prodotto a pagamento osservato; concorrenza non superabile. |
| EN - Travel planner (Sheets/PDF) | Osservato: listing Etsy da 1,50 a 25,99 USD, categoria molto affollata. Non approfondita perche i dati non portano nulla di diverso dalla nicchia binder/planner; meno differenziabile, stagionale. Scartata per saturazione, non per esclusione. |
| IT - Planner viaggio (Notion/PDF) | Osservato: Notion ha template gratuiti e a pagamento, Payhip a 9,99 EUR; dipendenza da Notion (piattaforma di terzi). Dipendenza da un solo ecosistema: criterio di esclusione sez. 5. |
| DE - Hausakte / Wartungsplan Haus | Osservato: nessun prodotto a pagamento trovato; offerta gratuita da Verbraucherzentrale e altri enti. Nessuna evidenza di disponibilita a pagare. Una mancanza di offerta non prova domanda. |
| FR - Pack sante imprimable (famille) | Escluso: categoria salute (regolamentata). |
| Qualsiasi nicchia per bambini o genitori-con-minori | Esclusa dall'ambito (minori). |
| Consulenza finanziaria, fiscale, medica, legale | Esclusa dall'ambito (regolamentata). |

## Conclusioni

1. Nessuna scheda raggiunge 60: nessuna candidata secondo il metodo. Le piu vicine: DE Haushaltsbuch (58,5), ES oposiciones (58,0).
2. Tutte le nicchie osservate sono affollate o con alternative gratuite forti; i prezzi osservati sono bassi (spesso sotto 10 EUR), quindi il margine assoluto per vendita e di pochi euro.
3. Per riclassificare serve: aprire le pagine con WebFetch (host da consentire, vedi fonti-bloccate-B.md), rilevare recensioni e vendite, volumi di ricerca nelle lingue target.
4. Proposta al Team Lead: se si prosegue, la ES oposiciones e l'unica con evidenza di un problema forte e di un prodotto a pagamento di fascia alta in arrivo (Planificador Pro): osservare il lancio prima di decidere. Un test a bassissimo costo potrebbe confrontare 2 prezzi, ma resta una decisione di fase commerciale.
5. Proposta di modifica al metodo (docs/metodo-ricerca.md e di mia responsabilita, non modificato in questa fase): aggiungere il campo `metodo` alle fonti osservate da riepilogo di ricerca e la distinzione "pagina aperta" / "risultato di ricerca".
