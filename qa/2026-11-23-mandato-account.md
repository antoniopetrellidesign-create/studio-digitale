# Verdetto QA — mandato account e credenziali (T-017)

## Riverifica dopo D-023 (2026-11-23) — verdetto aggiornato: **APPROVATO**

Ambito: solo le correzioni di D-023 e la regressione completa. Il verdetto iniziale BLOCCATO resta più sotto come storico.

| Controllo | Esito | Prova |
|---|---|---|
| B1 test | OK | `timeout 300 python3 -m unittest discover -s tests` → `Ran 128 tests … OK (expected failures=1)` |
| B2 collaudo | OK | `timeout 200 python3 -m studio collaudo --runs-dir /tmp/claude-qa-collaudo-6` → `12/12 casi superati`; `grep -c '"reale"'` sui log → `0` |
| E5 rete | OK | collaudo e unittest rieseguiti con la guardia `sitecustomize` (blocca ogni connect non loopback) → 0 tentativi |
| H-1 | CORRETTO | `live_shopify.py:51-53` (riga 51) richiede `live_consentito` prima di qualsiasi richiesta; `test_gate_simulato_non_lascia_passare_adattatore_reale` passa |
| M-1 | CORRETTO | `accounts.py:57-61` (righe 57-59) accetta solo fonte `osservata` con url e data; `social` torna `da_verificare`; `test_prezzo_verificato_richiede_fonte_osservata_e_data` passa |
| M-2 | CORRETTO | `phases.py:332-350` passa da `richiedi`; `completo/account.json` → `busta: completo/account-shopify, impegno_cents: 3600`; la fase rieseguita resta idempotente (consumo piattaforma 3600 → 3600, prova manuale con `phases.h_shopify` su un run completato) |
| M-3, m-1 | CORRETTI | `live_shopify.py:42-47` controlla l'host anche quando deriva da `negozio` e impone https; i test passano |
| m-2, m-3 | CORRETTI | HMAC con segreto vuoto → `False`; la CLI rifiuta `password`/`token`/`chiave_api` in `--dati`; i test passano |

Ho tolto i 7 marcatori `expectedFailure`, che sono diventati regressioni normali. Ho anche corretto la fixture di `test_canone_riservato_e_limitato_da_allocazione_e_tetto`: la fonte osservata era senza url e data, cioè proprio il caso che M-1 chiede di rifiutare.

**Nuovo difetto introdotto da D-023 (minore, latente, non bloccante)**
- `studio/adapters/base.py:36`: `record(..., esito_forzato=...)` accetta qualsiasi valore. In modalità live, senza `STUDIO_LIVE` e senza integrazione collaudata, `esito_forzato="reale"` viene registrato come `reale` e non alza eccezioni.
- Riproduzione: `test_esito_forzato_non_allenta_il_cancello` (`expectedFailure`).
- Oggi nessun chiamante lo usa così: l'unico uso è `live_shopify.py:52`, con `"bloccato"`.
- Correzione proposta: ammettere solo `"bloccato"`.

**Osservazione (non bloccante)**
- Lo scenario `completo` imposta `passaggi_titolare: []` per Shopify e una fonte "osservata" sintetica con url `.invalid`. Questo è dichiarato in D-023 e nella nota `[SINTETICO]`.
- Con il catalogo reale l'account resta non attivabile: il prezzo è `da_verificare`.

---

## Verdetto iniziale (storico)

Data: 2026-11-23 · Verificatore: qa-indipendente (non autore del codice) · Oggetto: D-017…D-022, commit `b2d8918`
Checklist: `docs/qa-checklist.md` §0, §6 (E1–E5), §7, §9 (A1–A7, nuova).

### Verdetto iniziale: **BLOCCATO** (superato con D-023, vedi riverifica sopra)

Il blocco riguarda **l'attivazione di account con spesa** (D-017, regola 1 di CLAUDE.md) e **l'idoneità di `live_shopify` alla prova dal vivo** (D-021).
La simulazione e il collaudo restano utilizzabili: nessuna azione reale, nessuna rete esterna, nessuna credenziale in chiaro sono state osservate.
Criteri violati: A3, A4 e A7 della checklist; sono criteri espliciti del mandato T-017 (§2).

## Prove di base (evidenza osservata)
| Controllo | Esito | Prova |
|---|---|---|
| B1 test | OK | `timeout 300 python3 -m unittest discover -s tests` → `Ran 127 tests … OK (expected failures=7)` |
| B2 collaudo | OK | `timeout 200 python3 -m studio collaudo --runs-dir /tmp/claude-qa-collaudo-5` → `12/12 casi superati` |
| E1 nessuna azione reale | OK | `cat /tmp/claude-qa-collaudo-5/*/external_calls.jsonl \| grep -c '"reale"'` → `0` |
| E5 nessuna rete | OK | collaudo e unittest rieseguiti con un `sitecustomize.py` in `PYTHONPATH` che fa fallire e registra ogni `socket.connect` non loopback (vale anche per i sottoprocessi): 0 tentativi (la sonda di controllo è stata bloccata correttamente). Test: `test_tutti_gli_scenari_senza_rete_esterna` |
| Scenario completo | OK | 12 fasi completate, 16 ordini (2 Etsy) + 1 di prova; `config/integrazioni_collaudate.json` → `"collaudate": []` |

## Adeguamento dei miei test (cambiamenti voluti, non difetti)
- `tests/test_qa_sistema.py`: 14→16 ordini, 15→17 con l'ordine di prova.
- `test_nessuna_credenziale_o_dato_personale_versionato`: esclusi `qa/` e `docs/qa-checklist.md` (documentano i pattern, come `tests/test_qa_*`), ammessi gli indirizzi su domini riservati (`.invalid`, `.example`, `example.com`) usati in `tests/test_vault.py:34,41`.

## Controlli avversariali superati
| # | Controllo | Prova [TEST] in `tests/test_qa_mandato_account.py` |
|---|---|---|
| A1 | `accessi nuovo --genera-password`: password non stampata né scritta in chiaro, nemmeno in indice/voci | `test_cli_genera_password_non_stampata_ne_scritta_in_chiaro`, `test_indice_senza_campi_segreti_anche_con_nomi_imprevisti` |
| A2 | Senza chiave del titolare: `RIFIUTATO`, exit 2, nessuna voce; chiave privata estranea: `age -d` fallisce senza testo in chiaro; destinatari malformati (`age1…`, `ssh-ed25519 …`): `CalledProcessError`, nessun file e nessun indice | `test_cli_senza_chiave…`, `test_senza_chiave_privata…`, `test_destinatario_malformato…` |
| A3 | Rifiuto prima della fase, con dipendenza non attiva, prezzo `da_verificare` o senza massimo, prova gratuita senza scadenza; catalogo reale: nessun account attivabile oggi (eccetto i due del difetto M-1) | `TestQAAccount` |
| A4 (registro) | `richiedi` riserva canone x mesi; oltre l'allocazione piattaforma → `SpendBlocked` e account non registrato; mesi negativi bloccati; richiesta ripetuta non riserva due volte | `test_canone_riservato…`, `test_richiesta_ripetuta…` |
| A5 | Esclusi i canali con `regole_prodotto` o `regole_ai` a 0 (anche chiave mancante); ordini da canale escluso non entrano; fee marketplace sostituisce quella del sito; per canale di vendita: ordini, ricavi, fee e margine sommano al totale | `TestQACatalogo` |
| A6 | `g_social` respinge QA non approvato o download fallito; `pubblicato: true` respinto; scenario completo: tutto `bozza`, nessuna chiamata social/pubblicazione | `TestQASocial` |
| A7 (parziale) | Gate `live`: bloccato con `STUDIO_LIVE` 0/assente/`true` o senza collaudo, nessuna richiesta HTTP; endpoint espliciti non Shopify rifiutati; `productCreate` solo `DRAFT`; `hmac.compare_digest` | `TestQALiveShopify` |

## Difetti (per gravità) — ognuno ha un test `@unittest.expectedFailure`
Ho verificato che ogni test fallisca per il motivo dichiarato rimuovendo il decoratore in una copia nella scratchpad.

### ALTO
**H-1 — Adattatore reale con gate in modalità "simulato" esegue la richiesta HTTP con il token.**
`studio/adapters/base.py:36-39`: `record()` alza l'eccezione solo se l'esito è `bloccato`; in modalità `simulato` l'esito è `simulato` e il controllo ritorna senza errori. `studio/adapters/live_shopify.py:45` si affida a quel controllo e poi chiama `urlopen` (riga 52).
Riproduzione: `test_gate_simulato_non_lascia_passare_adattatore_reale`. Senza `STUDIO_LIVE` e con `collaudate=()`, il server locale riceve la richiesta con il token `fittizio`.
Oggi è latente perché `LiveShopify` non è collegato ad `adapters.build` (grep in `studio/` senza riscontri). Il criterio "niente azioni reali senza STUDIO_LIVE=1 E integrazione collaudata" però non è garantito dall'adattatore.
Correzione proposta (responsabile: shopify-operazioni / account-integrazioni): in `_graphql`, richiedere `self.gate.live_consentito(self.servizio)` prima di qualsiasi rete, altrimenti `ExternalActionBlocked`.

### MEDIO
**M-1 — Prezzo "verificato" accettato senza fonte osservata né data.**
`studio/accounts.py:57` controlla solo `stato` e `max_mensile_cents`, mentre la regola 3 (docstring riga 7, D-017) chiede fonte e data.
`config/account_catalogo.json:87` (servizio `social`) dichiara `"stato": "verificato"` con `"fonte": {"tipo": "ipotesi"}` e nessuna data. Anche lo scenario `completo` attiva Shopify con una fonte `ipotesi`. È un'ipotesi presentata come fatto (regola 3 di CLAUDE.md).
Riproduzione: `test_prezzo_verificato_richiede_fonte_osservata_e_data`.

**M-2 — La fase Shopify attiva l'account senza riservare il canone tramite il registro account.**
`studio/phases.py:332-338` esegue `verifica` e poi `conferma_attivo`, senza passare da `AccountRegistry.richiedi`. Di conseguenza `account.json` non ha `busta` né `impegno_cents`.
Il canone del catalogo (3600 cent) è coperto solo se lo scenario elenca `costi_piattaforma`. Con lista vuota l'account diventa `attivo` senza alcuna riserva (regola 1 di CLAUDE.md, criterio A4).
Riproduzione: `test_fase_shopify_riserva_il_canone_tramite_registro`, con l'esito `{'stato': 'attivo', 'ultima_verifica': '2026-11-23'}` e nessuna busta.

**M-3 — Host non validato quando l'endpoint deriva da `negozio`.**
`studio/adapters/live_shopify.py:39-41`: il controllo vale solo se `endpoint` è passato esplicitamente. `LiveShopify(gate, "evil.example")` costruisce `https://evil.example/admin/api/...`, che riceverebbe il token Admin.
Riproduzione: `test_negozio_non_shopify_rifiutato`.

### MINORE
- **m-1** `studio/adapters/live_shopify.py:41`: lo schema non è controllato e `http://x.myshopify.com` è ammesso, quindi il token viaggerebbe in chiaro. Test: `test_endpoint_http_non_cifrato_rifiutato`. Inoltre `localhost` è ammesso anche fuori dai test.
- **m-2** `studio/adapters/live_shopify.py:27-29`: con un segreto webhook vuoto (variabile mancante) viene accettata una firma HMAC calcolata con chiave vuota, che chiunque può produrre. Test: `test_hmac_con_segreto_vuoto_rifiutato`.
- **m-3** `studio/__main__.py:71,130`: `accessi nuovo --dati '{"password": …}'` accetta segreti come argomento della riga di comando, quindi finiscono nella cronologia della shell e nella trascrizione dell'agente. Il valore resta comunque cifrato su disco. Test: `test_cli_rifiuta_segreti_in_chiaro_negli_argomenti`.

### Osservazioni (senza test, non bloccanti)
- `accessi esporta` senza `--identita` termina con un `TypeError` invece di un messaggio d'errore (`studio/__main__.py:140`).
- `crea_prodotto_bozza` controlla lo stato `DRAFT` solo dopo la creazione. È accettabile perché l'input è sempre `DRAFT`.

## Come si supera il blocco
- Correggere H-1, M-1, M-2 e M-3. A quel punto i rispettivi `expectedFailure` diventano "unexpected success": vanno rimossi i decoratori (lo fa il QA) e rieseguito il collaudo.
- In alternativa serve una decisione del titolare o del Team Lead in `DECISIONI.md`, motivata.
- I difetti minori non bloccano.

## Nota finale (2026-11-23) — difetto `esito_forzato` corretto
- `studio/adapters/base.py:35`: qualsiasi `esito_forzato` non nullo ora produce `"bloccato"`, quindi può solo irrigidire il cancello.
- Ho tolto il marcatore da `test_esito_forzato_non_allenta_il_cancello`, che ora è un test di regressione normale.
- `timeout 300 python3 -m unittest discover -s tests` → `Ran 128 tests … OK` (0 expectedFailure, 0 unexpected success).
- Nessun difetto aperto su questo oggetto. Verdetto: **APPROVATO**.
