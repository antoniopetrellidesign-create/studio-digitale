# Social: metodo per identità, account, calendario e contenuti

Responsabile: social-contenuti. Fase: Social (dopo l'ordine di prova con download riuscito).
Stato: collaudo. Nessun account creato, nessuna pubblicazione, nessun contatto con terzi: si producono solo **bozze** e metodo. Nicchie e prodotti nei fixture sono sintetici (`"sintetico": true`); ogni numero qui sotto è **ipotesi** finché non c'è evidenza osservata (fonte + data).

## 1. Ambito e condizione di avvio
- Si applica **solo ai prodotti VALIDATI**: QA approvato **e** ordine di prova con download riuscito. Prodotto non validato: nessun lavoro social, nessuna bozza.
- Il manifest (`id`, `versione`, `lingua`, `files`, `promesse`) è la sola fonte delle affermazioni ammesse. Ciò che non è nel manifest non si dice.
- Dipendenze: canale di vendita (Shopify) pronto; schema link e attribuzione in `studio/attribution.py` / `docs/acquisizione.md` par. 7; affiliazione in `docs/creator-partnership.md`.

## 2. Output minimo per prodotto (richiesto dal motore)
| Chiave | Contenuto |
|---|---|
| `identita` | nome, tono, lingua, elementi visivi con diritti verificati |
| `piattaforme` | elenco; **ogni voce con motivazione** |
| `calendario` | **almeno 4 voci** |
| `contenuti` | ognuno con le **promesse coperte** (P1..Pn) |
| `link_tracciati` | un link UTM per contenuto |

Output mancante di una chiave o con contenuti senza promessa coperta: non si passa il controllo di sblocco.

## 3. Identità del prodotto
1. **Nome**: quello del manifest/scheda negozio; nessun nome alternativo sui social.
2. **Tono**: 3 aggettivi + 3 cose che non si dicono mai (es. esiti garantiti, urgenza finta, confronti non verificabili).
3. **Lingua**: la `lingua` del manifest. Un prodotto, una lingua per account; un'altra lingua è un altro prodotto/account.
4. **Elementi visivi**: solo materiale proprio (schermate del deliverable, grafiche create in studio) o con licenza verificata. Per ognuno: origine, licenza, data di verifica. Immagini di terzi, volti, marchi altrui, musica: **escalation al Team Lead**; senza diritti verificati non si usano.
5. Ogni elemento è registrato in `products/<id>/social/identita.md` con la dicitura `osservata` (licenza verificata + data) o `ipotesi`.

## 4. Scelta degli account
Principio: **dove si trova l'acquirente**, non dove si trova il traffico in generale. Niente account su ogni piattaforma.
1. Partire dal profilo del compratore nella ricerca (`research/`): dove cerca la soluzione, dove discute il problema, che formato consuma.
2. Per ogni piattaforma candidata annotare: evidenza di presenza dell'acquirente (`osservata` con fonte+data, oppure `ipotesi`), formato adatto al prodotto, costo di gestione (tempo AI), rischi di policy.
3. Si scelgono **1 piattaforma primaria**, al massimo 1 secondaria. Terza piattaforma solo con evidenza osservata di ritorno dalle prime due.
4. Ogni piattaforma scelta ha una `motivazione` di una riga che cita l'evidenza e la sua natura (osservata/ipotesi). Nessuna motivazione: la piattaforma non entra.
5. **Creazione account**: solo tramite il registro account (`studio/accounts.py`, mandato D-017), **solo nella fase di lancio**, con prezzo, imposte e rinnovo verificati e impegno riservato nel registro spese. Prima di allora si preparano esclusivamente le bozze. Credenziali solo in `ACCESSI_SISTEMA` (`segreto://...`); CAPTCHA, OTP, identità e carte restano al titolare (`AZIONI_TITOLARE.md`). La richiesta passa dal Team Lead (via account-integrazioni).

## 5. Calendario editoriale
Template: `templates/calendario-editoriale.md`. Bozze in `products/<id>/social/`.
- **Frequenza**: partire bassa e sostenibile (ipotesi: 2-3 pubblicazioni a settimana sulla primaria, 1 sulla secondaria per 4 settimane); aumentare solo se il ritmo è mantenuto e i click tracciati lo giustificano.
- **Formati**: scegliere per piattaforma tra post testo/immagine, carosello, breve video dimostrativo, thread, post di domanda alla community. Un formato per voce.
- **Temi**: ogni voce è legata ad almeno una promessa P1..Pn. Rotazione: problema riconoscibile, dimostrazione di una promessa, caso d'uso, domanda frequente (da `docs/customer-care.md`), novità/versione.
- **Minimo 4 voci** per prodotto, copertura di **tutte** le promesse del manifest almeno una volta.
- Ogni voce: id (`C-01`...), data prevista, piattaforma, formato, promesse, id link, stato (`bozza` / `approvata QA` / `pubblicata` dopo lancio).
- Nessuna data è un impegno finché la fase di lancio non è sbloccata.

## 6. Contenuti dimostrativi onesti
1. Si mostra il **deliverable reale** (schermate/estratti del file del manifest), non mockup migliori del prodotto.
2. Ogni contenuto dichiara le promesse coperte (`copre_promesse`) e si limita a esse. Niente esiti garantiti, guadagni, risultati medici, tempi non dimostrati.
3. Prima/dopo, numeri, testimonianze: ammessi solo se osservati, con fonte e data; altrimenti vietati. Mai recensioni o utenti inventati. Esempi sintetici si marcano **SINTETICO** nel testo della bozza e non vanno pubblicati come fatti.
4. Prezzo, rimborso e cosa è incluso coincidono con la scheda negozio.
5. Affermazioni non verificabili o immagini di terzi: stop ed escalation al Team Lead. Il QA indipendente può bloccare una bozza con motivazione verificabile.

## 7. Dichiarazioni obbligatorie
- **Contenuto promozionale / affiliato**: ogni contenuto che promuove il prodotto, o che passa da un partner con commissione (`docs/creator-partnership.md`), riporta la dichiarazione all'inizio, in modo evidente e nella lingua del contenuto (es. "Pubblicità", "Link di affiliazione"), usando anche lo strumento nativo della piattaforma quando esiste ("partnership a pagamento" o equivalente).
- **Etichetta AI**: se la piattaforma richiede di segnalare contenuti generati o modificati con AI (immagini, video, voce realistici), l'etichetta si attiva ed è registrata nella voce di calendario (`etichetta_ai: si/no/non richiesta`). Verificare la regola corrente della piattaforma prima del lancio e annotarla con data (`osservata`); non darla per nota.
- Regole di piattaforma e di legge sono verificate al momento del lancio; qui non si presentano come fatti già accertati.

## 8. Collegamenti tracciati (UTM)
Ogni contenuto con link ha un URL con:
| Parametro | Valore |
|---|---|
| `utm_source` | piattaforma (es. `instagram`, `linkedin`) in minuscolo |
| `utm_medium` | `social` |
| `utm_campaign` | id prodotto (dal manifest) |
| `utm_content` | id contenuto (es. `C-01`) |
- Link generati con `studio/links.py`; non scritti a mano. Un link per contenuto, mai riusato tra contenuti.
- Con un partner si aggiunge il codice di attribuzione secondo `studio/attribution.py`; regola per doppia attribuzione: `docs/acquisizione.md` par. 7.
- Link senza UTM o con `utm_content` non presente in `contenuti`: il QA blocca.

## 9. Metriche
| Metrica | Definizione |
|---|---|
| Click tracciati | visite con UTM del contenuto/piattaforma |
| Ordini attribuiti | ordini riconciliati con `utm_campaign` + `utm_content` (via `studio/orders.py`) |
| Costo del tempo AI | tempo/token di produzione e gestione per contenuto, registrato in `products/<id>/social/` |
| Derivate | click per contenuto, ordini per piattaforma, costo AI per ordine attribuito |
- Costi diretti (account, abbonamenti) vanno nel registro; il costo del tempo AI si espone accanto, non lo sostituisce.
- Pochi dati non sono un risultato: soglie minime di click/ordini prima di giudicare sono ipotesi fissate prima (come in `docs/acquisizione.md`). Il confronto con altri canali usa il margine, non i click.
- Piattaforma che non porta click tracciati dopo il periodo fissato: sospendere, non aggiungere piattaforme.

## 10. Passaggi e controlli
1. Identità, piattaforme, calendario, contenuti, link: tutti presenti (par. 2).
2. Ogni contenuto → promesse del manifest; ogni promessa → almeno un contenuto.
3. Diritti degli elementi visivi verificati; dichiarazioni e etichette AI presenti.
4. QA indipendente approva le bozze; Team Lead sblocca la fase di lancio.
5. Solo dopo: richiesta account tramite registro, pubblicazione, misurazione.
