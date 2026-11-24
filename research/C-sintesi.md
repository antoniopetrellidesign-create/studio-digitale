# Sintesi ricerca T-028C - ampliamento a 5 nicchie nuove

Data: 2026-11-24. Responsabile: ricerca-mercato. Schede: `research/C-<id>.json`. Soglia invariata: punteggio >= 60 e almeno 2 fonti osservate indipendenti.

## Limite delle evidenze (leggere prima)

- WebFetch non ha funzionato: 3 tentativi su 3 host diversi (kaz.proz.com, www.getly.store, www.berlin.de) con l'errore esatto `getaddrinfo ENOTFOUND <host>` ("host fuori dai domini di rete consentiti della sessione"). Nessuna pagina e stata aperta: 0 fonti `letta_integralmente`.
- Tutte le fonti osservate sono `risultato_di_ricerca` (`metodo: estratto_ricerca`): titolo, URL ed estratto di WebSearch. Per D-028 problema e concorrenza restano <= 6 (usati 5-6 e 3-5).
- Nessun volume di ricerca, vendita, recensione o lamentela e stato osservato. I prezzi in USD sono ordini di grandezza, non convertiti. Cifre di cui l'estratto non lega il prezzo a un URL sono state declassate a `non_verificabile`.
- Commissioni Etsy (950 bp + 45 cent) e costo di accesso (200 cent) sono ipotesi comuni. Margine = (prezzo - commissione - 45 - 200) / prezzo; lo sviluppo e unico e non e nel margine per unita.
- Mercati: US/EN (3 schede) e DE (2 schede). Le fonti US non valgono per DE.

## Punteggi (pesi 25/20/20/15/10/10; il motore deve ricalcolarli)

| Scheda | Probl. | Acc. | Marg. | Conc. | Svil. | Ass. | Totale |
|---|---|---|---|---|---|---|---|
| C-fachwirt-lernplan-de | 6 | 5 | 7 | 4 | 6 | 7 | 58,0 |
| C-etsy-seller-profit-tracker-en | 6 | 6 | 6 | 3 | 7 | 7 | 57,5 |
| C-translator-business-tracker-en | 5 | 5 | 6 | 5 | 7 | 8 | 57,0 |
| C-handmade-preiskalkulation-de | 6 | 5 | 6 | 3 | 7 | 7 | 55,5 |
| C-cert-study-planner-en | 5 | 5 | 6 | 3 | 7 | 8 | 54,0 |

**Nessuna scheda raggiunge 60: nessuna candidata.** I voti sono motivati in `note_punteggi`; il calcolo e riportato nella scheda.

## Nicchie

### 1. DE - Lernplan per esami IHK di perfezionamento (58,0)
- **Osservato** (estratto): Testhelden vende preparazione Fachwirt con piano di studio a 69 EUR; Karrierebibel ha un Lernplan gratuito generico; WBS Training: prezzo su richiesta.
- **Ipotesi**: prezzo 14,90 EUR, margine 74,03%, sviluppo 40 EUR. Nessun Lernplan standalone a pagamento trovato: assenza di offerta non prova domanda.
- Rischio: usare solo piani quadro IHK pubblici; niente domande d'esame ne promesse.

### 2. US/EN - Etsy seller profit tracker (57,5)
- **Osservato**: Craftybase offre un foglio inventario Etsy gratuito; un listing Etsy dedicato (profit tracker + fee calculator); FinancialAha ha versioni gratuite e a pagamento.
- **Ipotesi**: prezzo 9,90 EUR, margine 65,76%. Concorrenza forte e gratuita (3).

### 3. US/EN - Business tracker per traduttori freelance (57,0)
- **Osservato**: strumento gratuito Excel/Sheets su ProZ (progetti per coppia linguistica e parole); "Freelance Translator Business OS" in Notion (prezzo non letto); Everhour offre modelli fattura gratuiti; un tracker generico a 14 USD.
- **Ipotesi**: prezzo 12 EUR, margine 70,08%. Unica nicchia con un solo prodotto specifico osservato (concorrenza 5), ma domanda non quantificata.

### 4. DE - Preiskalkulation per handmade/Etsy (55,5)
- **Osservato**: sevdesk e WHK offrono Excel gratuiti; un listing Etsy a 15,74 EUR; Getly DE vende calcolatori handmade/Etsy.
- **Ipotesi**: prezzo 12,90 EUR, margine 71,47%.

### 5. US/EN - Planner per certificazioni IT (54,0)
- **Osservato**: planner cloud su Etsy (circa 2-12 USD dagli estratti); piani gratuiti Digital Cloud Training e APMG; MindMesh con template Excel.
- **Ipotesi**: prezzo 9,90 EUR, margine 65,76%. Marchi AWS/CompTIA/PMP: uso solo descrittivo.

## Tabella fonti

| Scheda | URL | Livello | Tipo |
|---|---|---|---|
| translator | kaz.proz.com/forum/software_applications/384175.html | risultato_di_ricerca (WebFetch ENOTFOUND) | osservata |
| translator | getly.store/product/freelance-translator-business-os | risultato_di_ricerca (WebFetch ENOTFOUND) | osservata |
| translator | rjcreativeshop-6hb2dbds.manus.space/product/freelance-invoice-tracker | risultato_di_ricerca | osservata |
| translator | everhour.com/invoices/invoice-template-for-translators | risultato_di_ricerca | osservata |
| translator | prezzi Etsy non attribuibili / domanda / stime economiche (3 voci) | non_verificabile | ipotesi |
| etsy-seller | craftybase.com/etsy-inventory-spreadsheet | risultato_di_ricerca | osservata |
| etsy-seller | etsy.com/listing/4597094291 | risultato_di_ricerca | osservata |
| etsy-seller | financialaha.com/ultimate-spreadsheet-templates/.../etsy-seller-spreadsheet/ | risultato_di_ricerca | osservata |
| etsy-seller | workbook 36 USD non attribuibile / numero venditori / stime (3 voci) | non_verificabile | ipotesi |
| preiskalkulation | sevdesk.de/preiskalkulation-vorlage/ | risultato_di_ricerca | osservata |
| preiskalkulation | whk-controlling.de/wissen/preiskalkulation-excel | risultato_di_ricerca | osservata |
| preiskalkulation | etsy.com/listing/4582129647 | risultato_di_ricerca | osservata |
| preiskalkulation | getly.store/de/product/handmade-pricing-calculator-... | risultato_di_ricerca | osservata |
| preiskalkulation | domanda DE / stime economiche (2 voci) | non_verificabile | ipotesi |
| cert-planner | etsy.com/au/listing/4504681543/cloud-computing-certification-study | risultato_di_ricerca | osservata |
| cert-planner | digitalcloud.training/aws-certification-study-plan/ | risultato_di_ricerca | osservata |
| cert-planner | apmg-international.com/pt-br/article/self-study-how-create-study-plan | risultato_di_ricerca | osservata |
| cert-planner | mindmeshacademy.com/blog/articles/study-schedule-templates | risultato_di_ricerca | osservata |
| cert-planner | acquirenti planner / stime economiche (2 voci) | non_verificabile | ipotesi |
| fachwirt | testhelden.com/products/fachwirt-fuer-marketing-pruefung | risultato_di_ricerca | osservata |
| fachwirt | karrierebibel.de/lernplan-erstellen/ | risultato_di_ricerca | osservata |
| fachwirt | wbstraining.de/kurse/aufstiegsfortbildung/pruefungsvorbereitung-fachwirt/ | risultato_di_ricerca | osservata |
| fachwirt | assenza offerta standalone / stime economiche (2 voci) | non_verificabile | ipotesi |

Conteggio: letta_integralmente 0; risultato_di_ricerca 18; non_verificabile 12. Data di consultazione di tutte: 2026-11-24. Le fonti dei fogli gratuiti di marca pesano come concorrenza, non come prova di domanda.

## Nicchie scartate (senza scheda)

| Nicchia | Motivo |
|---|---|
| DE - Kursplanung per formatori e Erwachsenenbildung | Osservato (estratto): le offerte trovate sono gratuite (VHS Berlin, Uni Tuebingen, TU Darmstadt, FH Vorarlberg, Microsoft, Canva); i concetti di formazione a pagamento sono libri/materiali di managerSeminare, senza prezzo letto. Nessun prodotto digitale a pagamento comparabile osservato, nessuna evidenza di spesa. |
| DE/IT - Kit eventi per associazioni (Helferplan, Vereinsfest, sagra) | Osservato: modelli gratuiti (Verbandsbuero, Jotform, ClickUp, Edraw, TeamSystem); nessun kit a pagamento con prezzo. Rischio di sconfinare in permessi, sicurezza e igiene alimentare, di natura normativa e locale (comune per comune): richiederebbe escalation al Team Lead. |
| IT/DE - Strumenti per traduttori freelance | Osservato: solo guide e pagine di prodotto di software a pagamento (Harvest, Dropbox, Everhour, Beancount) e modelli gratuiti; nessun prodotto specifico a pagamento osservato in italiano o tedesco. Non si traduce l'opportunita EN (metodo sez. 8). |
| IT - Gestione ordini e magazzino per piccoli e-commerce | Osservato: Excel gratuito di PMI.it, ClickUp, Shopify blog; solo shop Etsy generici non analizzabili dall'estratto. Niente evidenza di prezzi o di lacune; la nicchia EN/DE (profit tracker, Preiskalkulation) e piu definita. |

## Conclusioni

1. Nessuna nuova scheda raggiunge 60; le piu vicine: Fachwirt-Lernplan DE (58,0), Etsy profit tracker (57,5), traduttori (57,0).
2. In tutte le nicchie esistono alternative gratuite di marca; il prezzo osservato dei prodotti a pagamento va da pochi dollari a 14-15,74 EUR; l'unico prezzo alto osservato e 69 EUR per un pacchetto di preparazione integrato (Testhelden).
3. I limiti sono di metodo: senza pagine aperte il punteggio di problema e concorrenza non puo superare 6. Per riclassificare serve consentire alla rete gli host citati (kaz.proz.com, www.getly.store, www.berlin.de e gli altri) e leggere recensioni e lamentele.
4. Pista piu promettente da verificare per prima: preparazione esami IHK (DE), perche e l'unica con un prezzo alto osservato e nessun planner standalone trovato; da escludere subito marchi e materiali d'esame di terzi.
