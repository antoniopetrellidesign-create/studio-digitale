# Sintesi T-018A - prima fase reale di ricerca (2026-11-23)

Ambito: prodotti digitali scaricabili per professionisti, freelance e piccole imprese, mercati EN/US e DE.
Metodo: `docs/metodo-ricerca.md`. Punteggio = somma(voto x peso/10) con pesi problema 25, accesso 20, margine 20, concorrenza 15, sviluppo 10, assistenza 10. Il motore ricalcola; i totali qui sono indicativi.

## Limiti dell'evidenza (leggere prima)
- WebFetch non ha funzionato: etsy.com e fiscoetasse.com non risolvono, reddit.com e rifiutato (vedi `research/fonti-bloccate.md`). Tutte le fonti "osservate" sono risultati di WebSearch (titolo, URL, snippet o riepilogo del motore). Nessuna pagina e stata aperta, nessuna recensione letta.
- Non ho osservato: volumi di vendita, recensioni, rimborsi, lamenti diretti dei compratori su Reddit (le query site:reddit.com non hanno restituito thread). Quindi `problema` e `concorrenza` non superano 6.
- Le commissioni di canale vengono da `config/canali_vendita.json` e restano ipotesi (le pagine tariffe non sono state verificate). Tutte le cifre di prezzo proprio, sviluppo e accesso sono ipotesi.
- Margine = (prezzo - commissione Etsy 9,5% + 0,45 EUR - 1,50 EUR accesso) / prezzo, IVA non scorporata: sovrastima.

## Risultato
Nessuna nicchia raggiunge la soglia 60. Nessuna e candidata. La migliore e 54,5.

| Scheda | Mercato | Punteggi (problema/accesso/margine/concorrenza/sviluppo/assistenza) | Totale indicativo | Fonti osservate |
|---|---|---|---|---|
| A-etsy-pricing-en | EN/US | 6/5/6/3/8/5 | 54,5 | 4 |
| A-freelance-tracker-en | EN/US | 5/5/6/3/8/7 | 54 | 4 |
| A-welcome-book-en | EN/US | 5/5/6/4/7/6 | 53,5 | 4 |
| A-gaestemappe-de | DE | 5/4/6/5/7/6 | 53 | 4 |
| A-content-calendar-en | EN/US | 5/5/6/2/8/7 | 52,5 | 2 |
| A-angebot-kleinunternehmer-de | DE | 5/4/5/2/8/6 | 47,5 | 3 |

## Nicchie

### 1. Calcolatore prezzi/profitto per venditori handmade (EN/US) - 54,5
- Osservato: thread community Etsy su come prezzare con tempo e imballaggio; molte inserzioni Etsy da pochi USD a circa 12 USD; Flevy XLSX a 45 USD (riepilogo motore); Craftybase gratuito.
- Stima: margine 71% (ipotesi). Ipotesi: commissioni datate nei concorrenti sono una lacuna (avviso del motore, non verificato), prezzo 10 USD.
- Perche non passa: concorrenza con gratuiti ufficiali e prezzi bassi; assistenza con aggiornamento commissioni; canale quasi solo Etsy. E la sola con una domanda posta da compratori.

### 2. Tracker clienti/progetti/fatture per freelance (EN/US) - 54
- Osservato: molte inserzioni Etsy (2-20 USD, bundle 64,60 USD); stesso prodotto su Hotmart, Payhip; gratuito FinancialAha; tracker fai-da-te su DEV Community.
- Ipotesi: nessuna lacuna dimostrata. Perche non passa: mercato saturo, problema a bassa urgenza.

### 3. Welcome book per host di affitti brevi (EN/US) - 53,5
- Osservato: inserzioni Etsy 4-30 USD, Selar 12,99 USD, Payhip 15 USD, gratuiti Touch Stay/Lodgify, guida nativa VRBO.
- Ipotesi: segmentazione per tipo di immobile come differenziazione. Rischio IP (Canva, loghi piattaforme).

### 4. Gaestemappe per Ferienwohnung (DE) - 53
- Osservato: house rules sign Etsy 11,53 EUR (da 15,37), Digistore24 sistema a 249 EUR, modelli gratuiti atraveo e altri, software Smoobu.
- Ipotesi: testi tedeschi completi come lacuna; poche evidenze (campione piccolo), per questo `concorrenza` 5 e fragile.

### 5. Calendario editoriale social (EN/US) - 52,5
- Osservato: Etsy 2-15 USD con outlier 40-50 USD; Stan Store. Solo 2 fonti in EN; gratuiti Buffer/HubSpot sono di altri mercati e non contano.
- Perche non passa: saturo, prezzi spesso sotto 3 USD.

### 6. Offerta/fattura per Kleinunternehmer (DE) - 47,5 - ESCALATION
- Osservato: modelli gratuiti sevdesk e Qonto con dicitura par. 19 UStG; Etsy 18,89 EUR per un tracker.
- Tocca contenuti fiscali/legali (finanza/legale): segnalato al Team Lead; nessuno sviluppo senza decisione.

## Nicchie scartate prima della scheda
- **Autonomi/forfettari/auto-entrepreneur: fatturazione e imposte (IT, ES, FR)**: categoria finanza/fiscale (escalation al Team Lead); la ricerca FR mostra modelli di devis/fattura gratuiti (Abby, Qonto, Sellsy), ES gratuiti (Holded, Quipu, Stelorder); l'unico prezzo IT visto (14,90 EUR + IVA, fiscoetasse) viene da una sola pagina non apribile (ENOTFOUND). Evidenza insufficiente e rischio regolamentato.
- **Calcolo Stundensatz/Angebot per Handwerker (DE)**: la ricerca ha mostrato solo strumenti gratuiti (Streit, WKO, bauprofessor); nessun prezzo di prodotto a pagamento osservato; dato mancante per valutare margine.
- **Piano editoriale social in italiano (IT)**: solo gratuiti (Buffer IT, Canva); nessun prezzo a pagamento osservato; una pagina Tally senza prezzo leggibile.
- **Calcetto, pesca e bambini**: esempi del brief, non nel target professionisti; bambini escluso (minori).

## Raccomandazioni
1. Nessuna opportunita da selezionare per il test con i dati attuali.
2. Prima di altro lavoro: consentire etsy.com e le pagine tariffe di canale, poi aprire 8-10 inserzioni per nicchia e leggere recensioni a 1-3 stelle per trovare lacune concrete.
3. Cercare nicchie con minore saturazione di gratuiti e dolore piu urgente (ad esempio flussi di lavoro di settore con compliance non regolamentata) invece di modelli generici.
4. Escalation al Team Lead: A-angebot-kleinunternehmer-de e la nicchia autonomi/fisco.
