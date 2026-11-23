# Creator e partnership: metodo e politica

Responsabile: creator-partnership. Fase di collaudo: nessun contatto con creator, nessuna proposta, nessuna promessa di compenso. Questo documento fissa solo metodo e regole. Parametri numerici in `config/commissioni.json`, coerenti con `config/policy.json` (importi in centesimi di euro).

## 1. Criteri di selezione

Un creator entra in shortlist solo se tutti i criteri sono valutati e documentati. Ogni dato e' `osservata` (fonte verificabile + data) oppure `ipotesi`; mai presentare un'ipotesi come fatto. Solo dati pubblici.

| Criterio | Cosa si verifica | Esclusione |
|---|---|---|
| Pertinenza del pubblico | il pubblico coincide con il compratore della nicchia scelta (problema, livello, contesto d'uso) | pubblico generalista o non coerente col prodotto |
| Lingua | lingua dei contenuti uguale a quella del prodotto e del negozio | lingua diversa o mista senza prova |
| Prove di audience osservate | metriche pubbliche (iscritti, visualizzazioni recenti, commenti) con fonte e data | numeri non verificabili, screenshot non pubblici |
| Qualita' dell'engagement | rapporto interazioni/visualizzazioni sugli ultimi contenuti, commenti pertinenti e non generici, andamento stabile | picchi isolati, commenti ripetitivi o sospetti |
| Rischi reputazionali | contenuti passati, polemiche, temi incompatibili con il marchio, uso scorretto di materiale altrui | qualsiasi rischio non motivabile |
| Conformita' pubblicitaria | disponibilita' scritta a dichiarare in modo chiaro il contenuto sponsorizzato o affiliato (es. indicazione visibile di collaborazione/pubblicita' e dell'uso del codice affiliato) | rifiuto di dichiarare: escluso |

Scheda partner (completa solo se tutti i campi sono presenti): pubblico, lingua, prova di audience (osservata, con fonte e data), costo massimo, modello di compenso, attribuzione, diritti di riuso. Senza costo massimo noto il partner e' bloccato.

## 2. Modelli di compenso

1. **Solo commissione.** Nessun importo fisso. La commissione e' dovuta solo su ordini effettivamente attribuiti (sezione 3) e si paga secondo la sezione 5.
2. **Fisso + commissione.** Il fisso e' ammesso solo se l'importo massimo e' **riservato nel registro** (`studio/ledger.py`, categoria `compenso_fisso`) **prima** dell'accordo. Tetto per creator: 3.000 centesimi (30 €), entro l'allocazione complessiva di 6.000 centesimi per il test. Senza riserva: nessun accordo, nessuna promessa.

Il modello preferito nel primo test e' "solo commissione": il costo cresce solo con i ricavi. Ogni impegno economico passa dal Team Lead; la firma dell'accordo spetta al titolare (sezione 8).

## 3. Attribuzione

Ogni creator riceve:
- un **codice sconto univoco** (sconto cliente: 1.000 bp = 10%);
- un **link con parametri UTM** univoco (sorgente, mezzo e campagna che identificano creator e test).

Regole:
- L'ordine e' attribuito al creator se contiene il suo codice. Il link UTM serve a misurare traffico e conversioni anche senza codice, ma da solo non genera commissione se non e' stato concordato per iscritto.
- **Ordine con codice creator e click Ads:** il ricavo si conta **una sola volta**; la commissione creator e' **dovuta**; la spesa Ads **resta**. Si conservano entrambi i costi: nessuno dei due viene cancellato o ridotto per evitare doppi conteggi. Il margine dell'ordine sconta quindi sia commissione sia costo Ads, cosi' il ROAS non e' gonfiato.
- Il ricavo non viene mai duplicato tra canali; l'attribuzione serve a pagare correttamente e a non sovrastimare i risultati.
- Codici e link sono tracciati per creator; un codice non e' trasferibile e non va pubblicato su siti di coupon.

## 4. Commissione

- Aliquota: **30%** (3.000 bp) sul **netto IVA esclusa, dopo lo sconto** del codice.
- Formula: `commissione = netto_dopo_sconto_IVA_esclusa x 3000 / 10000`, con arrotondamento intero in centesimi (stessa convenzione di `studio/money.py`).
- Esempio sintetico (ipotesi illustrativa): prezzo IVA esclusa 2.000 centesimi, sconto 10% = 1.800 netto; commissione = 540 centesimi.
- Le spese di spedizione, se presenti, e le imposte non entrano nella base.
- La commissione di pagamento della piattaforma resta un costo a parte e non riduce la base creator.

## 5. Finestra di clawback e pagamento

- Finestra: **30 giorni** dalla data dell'ordine.
- Un rimborso **entro la finestra storna** la commissione relativa (per intero se rimborso totale, proporzionale se parziale).
- **Il pagamento avviene dopo la finestra**: nessun pagamento anticipato su ordini ancora nella finestra.
- Rimborsi oltre la finestra non stornano commissioni gia' maturate, ma si registrano ai fini del tasso di rimborso.
- Il pagamento reale e' un'azione riservata al titolare (sezione 8); in collaudo si simula.

## 6. Tetto contrattuale alle commissioni per test

- Tetto: **6.000 centesimi (60 €)** di commissioni per test, pari all'allocazione `commissione` della policy.
- Le commissioni maturate sono riservate nel registro; al raggiungimento del tetto il **codice viene sospeso** (disattivato nel negozio) e non si accettano nuovi ordini attribuiti.
- Il tetto va scritto nell'accordo, con la clausola di sospensione. Ordini gia' effettuati prima della sospensione restano dovuti secondo le regole sopra, ma solo entro il tetto.
- Aumentare il tetto richiede una modifica della policy approvata dal Team Lead (DECISIONI.md).

## 7. Diritti di riutilizzo dei contenuti

Nessun riuso senza accordo **scritto**. Il documento deve indicare:

| Voce | Contenuto richiesto | Default (vedi `config/commissioni.json`) |
|---|---|---|
| Durata | data di inizio e fine, nessun rinnovo tacito | 90 giorni |
| Canali | elenco esplicito (organico, sito/negozio, email, ecc.) | organico del creator; sito e negozio dello studio |
| Territori | paesi in cui il riuso e' ammesso | Italia |
| Uso in Ads | si/no; se si', clausola separata | no |
| Compenso | importo per il riuso, anche zero, scritto | 0 se non in Ads |

L'uso in Ads e' un diritto distinto: richiede clausola separata, compenso scritto e importo massimo riservato nel registro prima dell'accordo. Il creator mantiene la titolarita' del contenuto; lo studio ottiene solo la licenza descritta. Vanno rispettati diritti di terzi (musica, immagini, marchi) presenti nei contenuti.

## 8. Cosa richiede la firma del titolare (pacchetto unico)

Gli agenti non firmano, non pagano e non contattano. Tutto cio' che segue si raggruppa in **un solo pacchetto** presentato al titolare tramite il Team Lead (`team/azioni_titolare.json`, `AZIONI_TITOLARE.md`):
- firma di ogni accordo con un creator (compenso, attribuzione, dichiarazione pubblicitaria, tetto, clawback);
- approvazione di ogni compenso fisso e della relativa riserva nel registro;
- firma della clausola di riuso, in particolare per uso in Ads;
- pagamenti reali delle commissioni dopo la finestra di clawback;
- invio effettivo di proposte o messaggi ai creator;
- qualsiasi dato di pagamento o credenziale: mai nei file o nei log.

## 9. Controlli prima di ogni accordo

1. Scheda partner completa e prova di audience osservata.
2. Costo massimo calcolato: fisso (se presente) + commissioni entro il tetto + eventuale riuso.
3. Riserva nel registro presente per il fisso; residuo sufficiente.
4. Codice e link UTM creati nel simulatore, non nel negozio reale.
5. Dichiarazione pubblicitaria concordata per iscritto.
6. Pacchetto unico pronto per il titolare.

Fino alla fase commerciale successiva, tutto resta simulato e senza contatti esterni.
