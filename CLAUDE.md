# Studio di prodotti digitali — istruzioni per Claude Code

Questo repository è il **sistema operativo** di uno studio di prodotti digitali gestito da un team di agenti AI.
Traguardo strategico di lungo periodo: portafoglio multilingua e multi-nicchia verso **30.000 € a settimana di utile operativo**.
Primo test commerciale: **tetto complessivo 500 €** (registro in `studio/ledger.py`).

## Stato attuale: fase di collaudo
- Tutte le integrazioni esterne sono **simulate** (`studio/adapters/mock.py`). Gli adattatori live (`studio/adapters/live.py`) bloccano ogni chiamata.
- **Vietato** in questa fase: spese, abbonamenti, campagne, pubblicazioni, creazione di account, contatti con persone esterne.
- Le nicchie e i prodotti nei fixture sono **sintetici e illustrativi** (`"sintetico": true`): non sono decisioni commerciali.
- Le decisioni su nicchia, prodotto, negozio e campagne appartengono alla fase commerciale successiva.

## Regole non negoziabili
1. **Spesa**: ogni azione a pagamento è preceduta da una riserva nel registro con costo massimo noto. Costo sconosciuto o residuo insufficiente ⇒ blocco.
2. **Credenziali**: mai in prompt, file, log o commit. Carte, OTP, token, password restano al titolare. Le azioni riservate al titolare si raggruppano in un unico passaggio (`AZIONI_TITOLARE.md`).
3. **Evidenze**: ogni dato di ricerca è `osservata` (fonte + data) oppure `ipotesi`. Mai presentare un'ipotesi come fatto.
4. **Un solo responsabile per file** (mappa sotto). Per modificare un file altrui, proponi la modifica al responsabile tramite la coda.
5. **QA indipendente** può bloccare un passaggio con motivazione verificabile; il blocco si supera correggendo la causa o con decisione registrata in `DECISIONI.md`.
6. **Ordine delle fasi**: Strategia → Ricerca → Selezione → Prodotto → QA → Shopify → Ordine di prova e download → Distribuzione → Misurazione → Decisione. Nessuna fase parte senza il controllo di sblocco della precedente.

## Comandi
```bash
python3 -m studio collaudo                         # collaudo completo di tutti gli scenari
python3 -m studio simulate --scenario completo     # una simulazione
python3 -m studio resume --run-id <id> [--concedi shopify]
python3 -m studio status --run-id <id>
python3 -m studio ledger --run-id <id>
python3 -m studio queue list                       # coda condivisa del team
python3 -m unittest discover -s tests -v           # test
```

## Team (`.claude/agents/`)
| Agente | Ruolo |
|---|---|
| team-lead | coordinamento, dipendenze, approvazione passaggi di fase, conflitti |
| strategia-finanza | obiettivi, unit economics, budget, regole stop/ripeti/scala |
| ricerca-mercato | opportunità da problemi, compratori, concorrenti, canali |
| sviluppo-prodotto | specifiche, prototipi, deliverable testabili |
| shopify-operazioni | schede, checkout, consegna, tracciamento, riconciliazione |
| creator-partnership | partner, affiliazione, attribuzione, commissioni, diritti |
| acquisizione | esperimenti Ads, organico, marketplace |
| customer-care | knowledge base, download, rimborsi, eccezioni |
| qa-indipendente | verifica e blocco motivato |

Gli Agent Teams nativi sono abilitati a livello di progetto in `.claude/settings.json` (flag sperimentale). Se nella sessione non sono disponibili, la sessione principale agisce da Team Lead e orchestra i subagenti usando la coda `team/queue.json`.

## Mappa dei responsabili (un solo responsabile per file)
| File / componente | Responsabile |
|---|---|
| CLAUDE.md, WORKFLOW.md, DECISIONI.md, RUNBOOK.md, AZIONI_TITOLARE.md, INTEGRAZIONI_LIVE.md | team-lead |
| team/ (coda), studio/workflow.py, studio/phases.py, studio/state.py, studio/queue.py, studio/__main__.py, studio/storage.py, studio/collaudo.py | team-lead |
| fixtures/scenari/, tests/test_workflow.py, tests/test_scenari.py | team-lead |
| STRATEGIA.md, config/policy.json, studio/ledger.py, studio/economics.py, studio/money.py, tests/test_ledger.py, tests/test_economics.py | strategia-finanza |
| docs/metodo-ricerca.md, templates/opportunita.schema.json, research/ | ricerca-mercato |
| templates/specifica-prodotto.md, products/ | sviluppo-prodotto |
| docs/operazioni-shopify.md, studio/adapters/ (shopify e pagamenti), studio/orders.py, tests/test_orders.py | shopify-operazioni |
| docs/creator-partnership.md, config/commissioni.json, studio/attribution.py | creator-partnership |
| docs/acquisizione.md | acquisizione |
| docs/customer-care.md | customer-care |
| qa/, docs/qa-checklist.md, tests/test_qa_*.py | qa-indipendente |

Il codice iniziale è stato scritto dal Team Lead come bootstrap (DECISIONI.md D-004); da ora le modifiche passano dal responsabile indicato.

## Struttura
```
.claude/agents/    agenti persistenti        config/     policy e soglie (centesimi di euro)
studio/            motore, registro, adattatori   fixtures/scenari/  scenari sintetici di collaudo
docs/              metodi e procedure        team/       coda condivisa e azioni titolare
tests/             test automatici           runs/       stato dei run (non versionato)
qa/                verdetti QA
```
