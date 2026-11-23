# Customer care: knowledge base, macro, rimborsi, escalation

Responsabile: customer-care. Stato: bozza per la fase di collaudo. Nessun contatto reale con clienti; le macro sono modelli, non messaggi inviati.
Prodotti: file digitali scaricabili venduti in più lingue nell'UE. Parametri economici di riferimento: `config/policy.json` (commissione di pagamento 2,9% + 0,30 EUR non recuperata su rimborso; clawback creator entro 30 giorni).

## 1. Principi
1. Rispondere nella lingua del cliente; se manca la macro localizzata, usare l'inglese e segnalarlo (sezione 3).
2. Prima di scrivere: identificare l'ordine tramite il numero ordine, mai chiedendo dati di pagamento.
3. Chiedere il minimo: numero ordine, descrizione del problema, eventuale schermata senza dati personali.
4. Non promettere nulla fuori politica (sezione 5): passare all'escalation (sezione 8).
5. Distinguere evidenza osservata (stato ordine, log di download) da ipotesi (cause supposte).

## 2. Protezione dei dati personali (regola trasversale)
- Nei log, nelle note di ticket, nei report e nella coda: solo ID ordine e ID ticket pseudonimi. Mai nome, email, indirizzo, IP, ultime cifre di carta, contenuto di allegati.
- Il cliente che incolla dati sensibili nel messaggio: non copiarli nelle note; scrivere "dato personale presente, omesso".
- Carte, OTP, token e password non si chiedono mai e non si registrano mai.
- Le richieste GDPR (accesso, cancellazione, portabilità) non si evadono: escalation immediata (sezione 8).

## 3. Struttura per localizzare le macro
Ogni macro ha ID stabile `CC-<caso>` e variabili tra doppie graffe. Le localizzazioni vivono in questa tabella logica (una riga per lingua), non in testi sparsi.

| Elemento | Regola |
|---|---|
| ID | `CC-LINK`, `CC-APRI`, `CC-SBAGLIATO`, `CC-RIMBORSO`, `CC-DOPPIO`, `CC-FATTURA`, `CC-PREVENDITA` |
| Variabili | `{{saluto}}`, `{{numero_ordine}}`, `{{nome_prodotto}}`, `{{link_download}}`, `{{giorni_scadenza}}`, `{{firma}}` |
| Lingue | codice ISO 639-1 (it, en, de, fr, es, ...); fallback: en |
| Stato per lingua | `bozza` -> `revisionata da madrelingua` -> `approvata`; solo `approvata` si usa |
| Elementi non traducibili alla lettera | termini giuridici (recesso, rimborso, fattura), importi, date: rivederli con un madrelingua |
| Tono | cortese, breve, un'unica azione richiesta per messaggio |

Checklist per aggiungere una lingua: tradurre tutte le macro, verificare le variabili, formato data/valuta locale, termini legali, firma, revisione madrelingua, stato `approvata`.

## 4. Macro di risposta (italiano)
Firma comune: `{{firma}}` = "Il servizio clienti".

### CC-LINK: link scaduto o limite di download raggiunto
Procedura: verificare che l'ordine sia pagato e non rimborsato; verificare stato del link e conteggio download; se l'ordine è valido, rigenerare il link (una volta senza escalation; dalla seconda volta valutare uso anomalo, vedi sezione 8).
> {{saluto}}, grazie per averci scritto. Abbiamo verificato l'ordine {{numero_ordine}} e abbiamo generato un nuovo link per scaricare "{{nome_prodotto}}": {{link_download}}. Il link è valido {{giorni_scadenza}} giorni. Se riscontri ancora problemi, rispondi a questo messaggio. {{firma}}

### CC-APRI: il file non si apre
Procedura: chiedere dispositivo/app e formato che si tenta di aprire; verificare che il download sia completo; suggerire app compatibile indicata in scheda prodotto; se il file risulta corrotto, reinviare e, se persiste, trattare come difetto (sezione 5).
> {{saluto}}, ci dispiace per il disagio. Per aiutarti ci servono: l'app o il dispositivo che usi e il messaggio di errore mostrato (senza dati personali). Nel frattempo prova a scaricare di nuovo il file da {{link_download}} e ad aprirlo con un'app compatibile con il formato indicato nella pagina di "{{nome_prodotto}}". Se il file risulta difettoso lo sostituiremo o rimborseremo secondo la nostra politica. {{firma}}

### CC-SBAGLIATO: file sbagliato
Procedura: confrontare il prodotto ordinato con il file consegnato (evidenza); se è un errore di consegna, rigenerare il link giusto; se è un errore di scheda prodotto, segnalare al responsabile della scheda e valutare rimborso.
> {{saluto}}, grazie per la segnalazione. Abbiamo verificato l'ordine {{numero_ordine}}: ecco il file corretto di "{{nome_prodotto}}": {{link_download}}. Ci scusiamo per l'errore. Se il contenuto non corrisponde a quanto descritto nella pagina prodotto, scrivici e valuteremo un rimborso. {{firma}}

### CC-RIMBORSO: richiesta di rimborso
Procedura: applicare la sezione 5; chiedere il motivo (serve alle metriche); verificare consenso all'esecuzione immediata registrato in checkout; decidere dentro/fuori politica.
Esito dentro politica:
> {{saluto}}, abbiamo approvato il rimborso dell'ordine {{numero_ordine}}. L'importo sarà accreditato sul metodo di pagamento originale; i tempi dipendono dalla tua banca (di norma alcuni giorni lavorativi). L'accesso al download sarà disattivato. {{firma}}

Esito fuori politica (non promettere, scalare):
> {{saluto}}, abbiamo preso in carico la tua richiesta per l'ordine {{numero_ordine}} e la stiamo valutando. Ti aggiorneremo entro {{giorni_risposta}} giorni lavorativi. {{firma}}

### CC-DOPPIO: doppio addebito
Procedura: verificare se esistono due ordini pagati o un solo ordine con due tentativi (autorizzazione in sospeso). Due ordini distinti per lo stesso prodotto: rimborsare il duplicato (dentro politica). Autorizzazione duplicata mai catturata: spiegare che si annulla da sola.
> {{saluto}}, abbiamo verificato l'ordine {{numero_ordine}}. Risulta un addebito duplicato: lo rimborsiamo integralmente sul metodo di pagamento originale. Se invece vedi un'autorizzazione temporanea, si annullerà automaticamente entro pochi giorni. {{firma}}

### CC-FATTURA: richiesta di fattura
Procedura: verificare l'ordine; fattura/ricevuta secondo il processo di `docs/operazioni-shopify.md`; dati fiscali (partita IVA, indirizzo di fatturazione) solo tramite il canale sicuro previsto, mai nei log. Se il processo fiscale non è definito, escalation (ipotesi da confermare con un professionista).
> {{saluto}}, per emettere la fattura dell'ordine {{numero_ordine}} abbiamo bisogno dei dati di fatturazione tramite {{canale_sicuro}}. Non inviarli in chiaro in questa conversazione. Riceverai il documento entro {{giorni_fattura}} giorni lavorativi. {{firma}}

### CC-PREVENDITA: domanda pre-vendita
Procedura: rispondere solo con informazioni presenti in scheda prodotto; non inventare funzionalità; ricordare formato, lingua e informativa sul recesso prima dell'acquisto; per domande su compatibilità non documentate, scalare al responsabile prodotto.
> {{saluto}}, grazie per l'interesse in "{{nome_prodotto}}". {{risposta_specifica}} Il prodotto è un file digitale scaricabile subito dopo l'acquisto; prima di pagare ti verrà chiesto di confermare l'esecuzione immediata, con la relativa informativa sul diritto di recesso. {{firma}}

## 5. Politica rimborsi per contenuti digitali (UE)
Quadro generale (da verificare, vedi avviso): per contenuti digitali non forniti su supporto materiale il consumatore ha di norma 14 giorni di recesso dalla conclusione del contratto. Eccezione: il recesso si perde se l'esecuzione è iniziata con il previo consenso espresso del consumatore e la sua conferma di riconoscere che perde il diritto di recesso, e il professionista ha fornito conferma del contratto su supporto durevole.
Implicazioni operative:
- Il checkout deve registrare, per ordine, due elementi distinti: consenso espresso all'esecuzione immediata e riconoscimento della perdita del recesso (casella dedicata, non preselezionata).
- La conferma dell'ordine (supporto durevole) riporta tale consenso.
- Il diritto a rimedi per file difettoso o non conforme resta indipendentemente dal recesso (garanzia di conformità).
- Ordine senza consenso registrato: considerare il recesso valido per 14 giorni.

AVVISO: queste regole vanno verificate con un professionista legale (consumatori UE e normativa dei singoli Stati membri, IVA e fatturazione) PRIMA del lancio. Questo documento non è un parere legale; la sezione 5 è ipotesi di lavoro, non evidenza.

## 6. Politica commerciale proposta (da approvare dal Team Lead)
| Caso | Esito proposto |
|---|---|
| File difettoso o non apribile, non risolto con reinvio | Sostituzione; se non risolvibile, rimborso totale entro 14 giorni dall'acquisto |
| File sbagliato consegnato per errore nostro | Invio file corretto; rimborso su richiesta |
| Doppio addebito confermato | Rimborso del duplicato, nessun limite di 14 giorni |
| Prodotto non conforme alla descrizione | Rimborso totale entro 14 giorni |
| "Non mi serve più" con consenso registrato | Nessun rimborso come diritto; eventuale gesto commerciale solo con approvazione (fuori politica) |
| "Non mi serve più" senza consenso registrato, entro 14 giorni | Rimborso (recesso) |
| Oltre 14 giorni, nessun difetto | Fuori politica: escalation |
Il rimborso avviene sul metodo di pagamento originale. Un cliente: un solo rimborso per prodotto.

## 7. Effetti di un rimborso sul sistema
1. Ordine segnato come `rimborsato` (totale o parziale), con data e motivo codificato.
2. Commissione creator stornata se il rimborso avviene entro 30 giorni (`finestra_clawback_creator_giorni`); oltre 30 giorni nessun clawback automatico, segnalare a creator-partnership.
3. Commissione di pagamento non recuperata (`commissione_pagamento_rimborsata_su_refund: false`): costo a carico dello studio, da includere nell'impatto economico del rimborso.
4. Accesso al download revocato: i link attivi vengono invalidati; verificare che i link già emessi non funzionino più.
5. Registrare nel ticket solo ID ordine e motivo; aggiornare le metriche (sezione 10).
Nota: a rimborso eseguito, un nuovo acquisto crea un nuovo ordine; non riattivare il vecchio.

## 8. Matrice di escalation verso il Team Lead
| Situazione | Chi decide | Azione dell'agente | Tempo |
|---|---|---|---|
| Rimborso fuori politica (oltre 14 giorni, senza difetto, importo anomalo) | Team Lead | Non rispondere con promesse; inoltrare ID ordine e motivo | 1 giorno lavorativo |
| Chargeback / contestazione bancaria | Team Lead (e titolare per azioni su conto) | Non rimborsare in parallelo; raccogliere evidenze (log consegna, consenso registrato) senza dati personali nei log | Subito |
| Reclamo legale, diffida, autorità, associazione consumatori | Team Lead, poi professionista legale | Nessuna risposta nel merito; solo presa in carico | Subito |
| Richiesta GDPR (accesso, cancellazione, portabilità, opposizione) | Team Lead | Non evadere, non copiare dati nelle note; scadenza di legge di norma 1 mese: tracciare data di ricezione | Subito |
| Uso anomalo dei download (molti reinvii, condivisione) | Team Lead | Sospendere nuovi reinvii oltre la soglia | 1 giorno lavorativo |
| Difetto ricorrente su un prodotto (3+ ticket in 7 giorni) | Team Lead, sviluppo-prodotto, qa-indipendente | Segnalare con elenco di ID ordine | 1 giorno lavorativo |
| Minaccia, abuso, dato personale sensibile ricevuto | Team Lead | Non registrare il contenuto | Subito |
Formato della segnalazione: ID ticket, ID ordine, categoria, evidenza osservata, ipotesi, richiesta di decisione.

## 9. SLA obiettivo (da validare con dati reali)
| Tipo | Prima risposta | Risoluzione |
|---|---|---|
| Link scaduto / limite download | 4 ore lavorative | 1 giorno lavorativo |
| File non apribile / sbagliato | 1 giorno lavorativo | 2 giorni lavorativi |
| Rimborso dentro politica | 1 giorno lavorativo | 2 giorni lavorativi (poi tempi bancari) |
| Doppio addebito | 1 giorno lavorativo | 2 giorni lavorativi |
| Fattura | 2 giorni lavorativi | 5 giorni lavorativi |
| Pre-vendita | 1 giorno lavorativo | 1 giorno lavorativo |
| Escalation (GDPR, legale, chargeback) | presa in carico 1 giorno lavorativo | secondo scadenze di legge o della banca |

## 10. Metriche
| Metrica | Definizione | Soglia di attenzione (ipotesi) |
|---|---|---|
| Ticket per 100 ordini | ticket aperti nel periodo / ordini pagati x 100 | oltre 10 |
| Tasso di rimborso | ordini rimborsati / ordini pagati | oltre il tasso massimo in `config/policy.json` (`tasso_rimborso_max_bp`) |
| Motivi | distribuzione dei ticket e dei rimborsi per codice motivo | un motivo oltre il 30% del totale |
| Rispetto SLA | ticket in SLA / totale | sotto 90% |
| Tempo di prima risposta | mediana | oltre SLA |
Codici motivo: `link`, `apertura`, `file_sbagliato`, `non_conforme`, `doppio_addebito`, `fattura`, `prevendita`, `ripensamento`, `chargeback`, `altro`.
Le metriche usano solo conteggi e ID; nessun dato personale. Revisione settimanale con il Team Lead; i motivi dominanti alimentano correzioni a prodotto, scheda e checkout.

## 11. Aperto / da verificare
- Revisione legale della sezione 5 prima del lancio (obbligatoria).
- Processo di fatturazione e IVA (dipende da `docs/operazioni-shopify.md`, non ancora disponibile).
- Strumento di ticketing e canale sicuro per i dati fiscali: da definire in fase commerciale.
