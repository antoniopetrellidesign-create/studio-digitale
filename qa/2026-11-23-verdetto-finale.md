# Verdetto QA finale: collaudo di sistema dopo D-013, D-014 e D-015

Data: 2026-11-23 · Verificatore: qa-indipendente (non ha scritto né corretto il codice) · Riferimenti: `qa/2026-11-23-collaudo-sistema.md` (13 difetti), `qa/2026-11-23-riverifica.md` (N-1…N-4), checklist `docs/qa-checklist.md`, test `tests/test_qa_sistema.py` (51 test, nessun `expectedFailure`).
Nessuna azione esterna e nessuna rete: si usano processi locali, directory temporanee e adattatori simulati.

## VERDETTO DEFINITIVO: **APPROVATO** (per la fase di collaudo e per il passaggio alla fase commerciale, nei limiti del registro)

F-1 è corretto (D-015) e lo ho verificato in modo indipendente, anche con processi reali in parallelo. La regressione completa è verde. Non restano difetti bloccanti né importanti; restano solo le osservazioni minori O-1…O-4, che non bloccano.
Questo giro, come richiesto dal Team Lead, ha riguardato solo F-1 e la regressione completa. Non ho cercato difetti in altre aree.

### Prove dell'ultimo giro (F-1, D-015)
| # | Controllo | Esito | Prova |
|---|---|---|---|
| F1a | Run omonimo dopo aver cancellato la sua cartella | OK | `test_run_omonimo_sullo_stesso_registro_registra_la_spesa_o_viene_rifiutato`, ora senza `expectedFailure` e verde: il secondo `Run` solleva `FileExistsError`. Da CLI: `simulate --run-id prova --registro R`, poi `rm -rf <runs>/prova`, poi di nuovo `simulate …` → `FileExistsError: il run_id 'prova' ha già usato il registro …`, rc=1 |
| F1b | Run omonimo su un altro `--runs-dir` | OK | Stessa CLI con `--runs-dir b` → `FileExistsError`; in `b/prova` resta solo `artifacts/` (niente `state.json`, nessuna chiamata esterna); `run_registrati` = `['prova']` |
| F1c | Due processi in parallelo, stesso `run_id`, `--runs-dir` diverse, stesso registro | OK | `test_run_omonimo_creato_in_parallelo_su_runs_dir_diverse`, 3 giri. In ogni giro esattamente un processo con rc=0 (`completato`); l'altro termina con `FileExistsError` senza `state.json` né `external_calls.jsonl`. `run_registrati` = `["omonimo"]`, ogni azione a pagamento del vincitore ha la sua busta, spesa > 0 e ≤ tetto. Ripetuto 3 volte (`TestQAConcorrenza` → `OK` ×3) |
| F1d | La ripresa dello stesso run non viene rifiutata | OK | `test_ripresa_dello_stesso_run_non_e_rifiutata`: scenario `interruzione` sul registro condiviso, crash e poi `Run(dir).avanza()` → `completato`, `run_registrati` = `["r"]` |
| B1 | Suite completa | OK | `timeout 600 python3 -m unittest discover -s tests` → `Ran 79 tests … OK` |
| B2 | Collaudo end-to-end | OK | `timeout 600 python3 -m studio collaudo --runs-dir /tmp/claude-qa-collaudo-4` → `11/11 casi superati` |
| S1 | Nessun segreto negli output del collaudo | OK | `grep -rIlE 'shpat_\|sk_live_\|ghp_\|AKIA[0-9A-Z]{16}' /tmp/claude-qa-collaudo-4` → nessun file |

### Osservazione minore nuova
- **O-4** (`studio/workflow.py:65`, `:80-88`). Un run rifiutato per `run_id` già usato lascia una cartella vuota `runs/<id>/artifacts/`. Il rifiuto arriva come traceback Python (rc=1) e non come messaggio della CLI. È solo estetica: non ci sono stato, chiamate o buste.

---

## Storico: verdetto precedente (prima di D-015), sostituito da quello sopra

### Verdetto allora: BLOCCATO (superato con D-015)

I 13 difetti del primo collaudo e i 4 della riverifica (N-1…N-4) sono **corretti**, e lo ho verificato in modo indipendente.
Resta **un difetto bloccante**, F-1. Era già nel codice fin dal bootstrap e non l'avevo trovato nei collaudi precedenti; è emerso cercando altre vie di aggiramento del tetto. Un run con lo stesso `run_id` sullo stesso registro riusa le buste del primo run. Esegue tutte le azioni a pagamento, ma la spesa registrata non aumenta.

**Come si supera il blocco:** si corregge F-1 e `test_run_omonimo_sullo_stesso_registro_registra_la_spesa_o_viene_rifiutato` diventa un test normale e verde. In alternativa il Team Lead registra in `DECISIONI.md` una decisione motivata di procedere. Due possibili correzioni:
- rifiutare un run il cui prefisso ha già buste nel registro;
- usare ID di busta univoci per istanza, ad esempio con un UUID scritto in `state.json`.

## Controlli (esito e prova)

| # | Controllo | Esito | Prova |
|---|---|---|---|
| B1 | Suite completa | OK (1 difetto noto) | `timeout 600 python3 -m unittest discover -s tests` → `Ran 77 tests … OK (expected failures=1)` |
| B2 | Collaudo end-to-end | OK | `timeout 600 python3 -m studio collaudo --runs-dir /tmp/claude-qa-collaudo-3` → `11/11 casi superati` |
| R1 | 13 difetti del primo collaudo | OK | 13 test di regressione normali e verdi (elenco in `qa/2026-11-23-riverifica.md`) |
| R2 | N-1: un test non finanziabile si ferma alla Selezione | OK | `test_due_test_interfogliati_il_non_finanziabile_si_ferma_alla_selezione`: B si ferma `("bloccato","selezione")`, ha nel registro solo buste `ai`, nessuna aperta (la prenotazione è tutto o niente), A `completato` |
| R3 | N-2: il rollback non tocca le buste altrui | OK | `test_rollback_atomico_non_chiude_buste_di_altri_run`: `ALTRO/ads-X` resta `aperta`, `B/creator-CR-SIM-1-fisso` viene chiusa |
| R4 | N-3: creazione concorrente del registro | OK | `test_creazione_concorrente_del_registro_non_perde_riserve`: 12 processi `subprocess` indipendenti su un registro nuovo, 6 riserve riuscite, tutte presenti (`ALLOC ads // 3000`). Il test D-014 `TestLedgerConcorrenza` (fork) è verde |
| R5 | N-4: previsione AI con ritorno QA e ripresa dopo blocco | OK | `test_previsione_ai_regge_ritorno_qa_e_ripresa_dopo_blocco` verde. Prova aggiuntiva con AI effettivo = massimo, ritorno QA e Shopify in attesa del titolare: con 18 € di AI già consumati → `completato`, nessuna busta aperta; con 21 € → fermato alla `selezione`, nessuna busta aperta |
| L1 | Processi reali in parallelo sullo stesso `--registro` | OK | `test_processi_paralleli_stesso_registro_entro_tetto_e_allocazioni` (2 giri × 3 `simulate`), ripetuto 3 volte senza instabilità: tetto, allocazioni, nessuna busta persa, al più una busta commissioni |
| L1' | La spesa registrata corrisponde alle azioni a pagamento eseguite | **KO** | F-1 |
| S1 | Q6 e segreti negli output | OK | `grep -rIlE 'shpat_\|sk_live_\|ghp_\|AKIA[0-9A-Z]{16}' /tmp/claude-qa-collaudo-3` → nessun file |
| S2 | File versionati senza credenziali | OK | `test_nessuna_credenziale_o_dato_personale_versionato`, robusto rispetto al blocco multiriga `SEGRETI` |

## Adattamenti dei test richiesti dal Team Lead (verificati)
1. Creazione concorrente: confermo che il vecchio mock faceva una `reserve` rientrante sotto il lock, e con `flock` su un secondo descrittore lo stesso processo si blocca. L'ho sostituito con 12 processi `subprocess` indipendenti, non `fork`, così il test non dipende da quello di D-014.
2. Test interfogliati: ora B si ferma alla Selezione e il test verifica proprio quell'esito, più l'assenza di spese e di prenotazioni residue.
3. Rollback: l'altro run riserva sulla categoria `ads`, che ha capacità libera, e il fallimento di B è iniettato con `SpendBlocked`. Così si prova direttamente il filtro del rollback.

## Difetti

### Bloccante
**F-1 Un run omonimo sullo stesso registro spende senza registrare.** Riferimenti: `studio/workflow.py:100-102` (`Run.bid`), `studio/ledger.py:110-115` (`reserve` ritorna la busta esistente, anche chiusa), `studio/ledger.py:181-185` (`draw` con lo stesso `draw_id` ritorna `False`).
Gli ID delle buste dipendono solo dal `run_id`. Basta cancellare `runs/<id>` e rilanciare con lo stesso `--run-id`, oppure usare un altro `--runs-dir`, sullo stesso `--registro`. Il secondo run riusa buste e consumi del primo: `ai-<fase>-1/unico`, `piattaforma-…/unico`, `ads-…/giorno-N`. Esegue le azioni a pagamento, cioè AI, piano negozio e campagna Ads, ma la spesa registrata non cambia, e ripetendo il run il tetto si aggira. In modalità live sarebbe spesa reale fuori registro. È contrario a D-005 ("ID delle buste specifici del run") e alla regola 1 di CLAUDE.md.
Riproduzione: `test_run_omonimo_sullo_stesso_registro_registra_la_spesa_o_viene_rifiutato` → `secondo run completato con 11 azioni a pagamento e spesa registrata invariata (12300 cent)`.
Da CLI, con lo scenario `completo` e il canale creator: `simulate --run-id prova --registro R`, poi `rm -rf <runs>/prova`, poi di nuovo `simulate --run-id prova --registro R`. Il secondo run viene bloccato alla Selezione solo perché l'allocazione commissioni è già usata, ma ha già eseguito 3 chiamate AI a pagamento (`"esegui"`) e il registro resta a 174,22 €.

### Importanti
Nessuno.

### Minori e osservazioni (invariati rispetto alla riverifica, non bloccanti)
- **O-1** Una `DatoMancante` (IVA mancante) blocca la Distribuzione a metà. Ora le buste di canale restano aperte fino all'intervento.
- **O-2** `tetto_commissioni_per_test_cents` viene confrontato con ogni singolo creator. Oggi non ha effetto, perché coincide con l'allocazione.
- **O-3, processo.** D-013 e D-014 hanno modificato file di altri responsabili, motivandolo con D-004. D-014 ha anche cambiato `config/policy.json` (nuova chiave `qa.ripetizioni_fase_previste`, file di strategia-finanza) e `studio/collaudo.py`.

## Note
- Non ho aggiornato `team/queue.json`, perché è fuori dal mio perimetro di scrittura in questo compito. Il Team Lead deve registrare l'esito definitivo **APPROVATO** di T-009 e segnare D-013, D-014 e D-015 come verificati dal QA.
- Escalation: Team Lead. Una decisione di procedere va registrata in `DECISIONI.md` con la motivazione.
