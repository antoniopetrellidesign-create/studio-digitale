# Studio di prodotti digitali — istruzioni per Claude Code

Questo repository è il **sistema operativo** di uno studio di prodotti digitali gestito da un team di agenti AI.
Traguardo strategico di lungo periodo: portafoglio multilingua e multi-nicchia verso **30.000 € a settimana di utile operativo**.
Primo test commerciale: **tetto complessivo 500 €** (registro in `studio/ledger.py`).

## Mandato del titolare (aggiornato 2026-11-23, DECISIONI.md D-017)
- Il team gestisce in autonomia progettazione, configurazione e preparazione delle integrazioni, nell'ordine delle fasi, con collaudo QA e tetto complessivo di **500 €**.
- **Account**: si possono creare quelli strettamente necessari (email dedicata, repository privato, Shopify e marketplace selezionati, strumenti per creator/assistenza/analisi, social dei prodotti validati, integrazioni API). Si passa **solo** dal registro account (`studio/accounts.py`, `config/account_catalogo.json`): l'attivazione richiede la fase raggiunta, le dipendenze attive, prezzo, imposte e rinnovo verificati e l'impegno riservato nel registro spese.
- **Credenziali**: solo nel documento cifrato **ACCESSI_SISTEMA** (`studio/vault.py`, `accessi/`), cifrato con la chiave pubblica del titolare. Altrove si usano solo riferimenti `segreto://servizio/campo`.
- **Passaggi personali** (identità, CAPTCHA, OTP, carte, firme, conferme di pagamento): li esegue il titolare sulle schermate ufficiali, raggruppati in un'unica richiesta (`AZIONI_TITOLARE.md`). Se un servizio non è compatibile con l'automazione, prima si valuta un'alternativa e si documenta il limite.
- **Pubblicazione e distribuzione commerciale** seguono la fase di lancio prevista dal workflow. Le integrazioni reali eseguono azioni solo se dichiarate collaudate (`config/integrazioni_collaudate.json`) e con `STUDIO_LIVE=1`.
- I dati nei fixture restano **sintetici e illustrativi** (`"sintetico": true`).

## Regole non negoziabili
1. **Spesa**: ogni azione a pagamento è preceduta da una riserva nel registro con costo massimo noto. Costo sconosciuto o residuo insufficiente ⇒ blocco. Prove gratuite registrate con scadenza; gli incassi non aumentano il budget.
2. **Credenziali**: mai in chiaro in prompt, file, log, commit o resoconti; solo in ACCESSI_SISTEMA cifrato. Carte e OTP li inserisce il titolare. Le azioni riservate al titolare si raggruppano in un unico passaggio (`AZIONI_TITOLARE.md`).
3. **Evidenze**: ogni dato di ricerca è `osservata` (fonte + data) oppure `ipotesi`. Mai presentare un'ipotesi come fatto.
4. **Un solo responsabile per file** (mappa sotto). Per modificare un file altrui, proponi la modifica al responsabile tramite la coda.
5. **QA indipendente** può bloccare un passaggio con motivazione verificabile; il blocco si supera correggendo la causa o con decisione registrata in `DECISIONI.md`.
6. **Ordine delle fasi**: Strategia → Ricerca → Selezione → Prodotto → QA → Catalogo multicanale → Shopify → Ordine di prova e download → Social → Distribuzione → Misurazione → Decisione. Nessuna fase parte senza il controllo di sblocco della precedente.

## Comandi
```bash
python3 -m studio collaudo                         # collaudo completo di tutti gli scenari
python3 -m studio simulate --scenario completo     # una simulazione
python3 -m studio resume --run-id <id> [--concedi shopify]
python3 -m studio status --run-id <id>
python3 -m studio ledger --run-id <id>
python3 -m studio queue list                       # coda condivisa del team
python3 -m studio account stato --fase <fase>      # quali account sono attivabili e perché
python3 -m studio account passaggi --fase <fase>   # elenco unico dei passaggi del titolare
python3 -m studio accessi indice                   # indice senza segreti di ACCESSI_SISTEMA
python3 -m studio accessi nuovo --servizio X --dati '{...}' --genera-password   # voce cifrata
python3 -m studio regia battito|istantanea|esporta|comando   # ponte della regia mobile (docs/regia.md)
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
| account-integrazioni | ciclo di vita degli account, ACCESSI_SISTEMA, integrazioni live |
| social-contenuti | identità, social, calendario e contenuti dei prodotti validati |

Gli Agent Teams nativi sono abilitati a livello di progetto in `.claude/settings.json` (flag sperimentale). Se nella sessione non sono disponibili, la sessione principale agisce da Team Lead e orchestra i subagenti usando la coda `team/queue.json`.

## Mappa dei responsabili (un solo responsabile per file)
| File / componente | Responsabile |
|---|---|
| CLAUDE.md, WORKFLOW.md, DECISIONI.md, RUNBOOK.md, AZIONI_TITOLARE.md, INTEGRAZIONI_LIVE.md | team-lead |
| app/regia.html, docs/regia.md, studio/regia.py, studio/hooks/, tests/test_regia.py | team-lead |
| team/ (coda), studio/workflow.py, studio/phases.py, studio/state.py, studio/queue.py, studio/__main__.py, studio/storage.py, studio/collaudo.py | team-lead |
| fixtures/scenari/, tests/test_workflow.py, tests/test_scenari.py | team-lead |
| STRATEGIA.md, config/policy.json, studio/ledger.py, studio/economics.py, studio/money.py, tests/test_ledger.py, tests/test_economics.py | strategia-finanza |
| docs/metodo-ricerca.md, templates/opportunita.schema.json, research/ | ricerca-mercato |
| templates/specifica-prodotto.md, products/ | sviluppo-prodotto |
| docs/operazioni-shopify.md, studio/adapters/ (shopify e pagamenti), studio/orders.py, tests/test_orders.py | shopify-operazioni |
| docs/creator-partnership.md, config/commissioni.json, studio/attribution.py | creator-partnership |
| docs/acquisizione.md, docs/marketplace.md, config/canali_vendita.json | acquisizione |
| config/account_catalogo.json, config/accessi_destinatari.txt, config/integrazioni_collaudate.json, studio/accounts.py, studio/vault.py, studio/adapters/live_shopify.py, accessi/, tests/test_accounts.py, tests/test_vault.py, tests/test_live_shopify.py | account-integrazioni |
| docs/social.md, templates/calendario-editoriale.md, studio/links.py | social-contenuti |
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
