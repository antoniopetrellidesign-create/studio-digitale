# RUNBOOK — operatività del sistema

Responsabile: team-lead. Obiettivo: nessun intervento quotidiano del titolare. Il titolare interviene una sola volta per il pacchetto `AZIONI_TITOLARE.md` e poi solo su eventi elencati sotto.

## 1. Avvio di una sessione di lavoro
1. `git pull` e `git status`: lavorare su un ramo, mai direttamente su `main`.
2. `python3 -m unittest discover -s tests` deve risultare `OK` prima di qualsiasi lavoro.
3. `python3 -m studio queue list`: riprendere i compiti `in_corso`, poi i `da_fare` con dipendenze completate.
4. Sessione principale = Team Lead (`claude --agent team-lead`). Gli agenti in `.claude/agents/` si invocano per nome. Se gli Agent Teams nativi sono attivi, il team-lead li usa; altrimenti orchestra i subagenti.

## 2. Ripetere il collaudo
```bash
python3 -m studio collaudo
```
Report in `runs/collaudo-<data>/REPORT.md`. Tutti i casi devono risultare PASS prima di qualsiasi passaggio alla fase commerciale.

## 3. Ciclo di un test
```bash
python3 -m studio simulate --scenario <scenario> --run-id <id> --registro registro/primo-test.json
python3 -m studio status --run-id <id>
python3 -m studio decisions --run-id <id>
```
In fase commerciale tutti i test usano **lo stesso** `--registro`: il tetto di 500 € vale per l'insieme dei test, non per singolo test.

## 4. Gestione degli stati
| Stato | Significato | Azione |
|---|---|---|
| `bloccato_titolare` | serve un'azione riservata al titolare | aggiungerla al pacchetto unico (lo fa il motore); dopo l'esecuzione: `resume --run-id <id> --concedi <azione>` |
| `bloccato` | spesa bloccata o controllo fallito | leggere `blocco.motivo` in `status`; il responsabile corregge la causa; poi `resume --run-id <id>` (nuovo tentativo registrato) |
| `fermato` | test chiuso con stop motivato | nessuna ripresa; il costo è registrato come test fallito e va incluso nei conti del portafoglio |
| `in_corso` con `in_esecuzione` | sessione interrotta | `resume --run-id <id>`: riparte dalla fase interrotta senza doppie spese |
| `completato` | esito stop/ripeti/scala | il team-lead registra la decisione commerciale in DECISIONI.md |

## 5. Regole di spesa (operative)
- Mai un'azione a pagamento senza una busta nel registro. L'adattatore rifiuta le azioni a pagamento senza ID busta.
- Costo massimo sconosciuto ⇒ chiedere a strategia-finanza di stimare un massimo con fonte; finché manca, la spesa resta bloccata.
- Residuo o allocazione insufficienti ⇒ escalation al team-lead. Per aumentare il tetto serve il titolare.
- Le buste Ads si chiudono a fine distribuzione; tutte le buste di canale si chiudono alla Decisione.

## 6. Credenziali e dati sensibili
- Credenziali solo nel gestore segreti dell'ambiente (variabili d'ambiente / segreti di rete), mai in file, prompt, log o commit. `.gitignore` esclude `.env*` e `secrets/`; le impostazioni negano la lettura di quei percorsi.
- OTP e verifiche d'identità le esegue il titolare direttamente sul servizio: non vengono mai trascritte.
- Il QA (controllo Q6) cerca pattern di segreti nei file dei run e blocca se ne trova.

## 7. Escalation verso il titolare (solo questi casi)
1. Pacchetto iniziale di attivazione account (`AZIONI_TITOLARE.md`), una volta sola.
2. Esito `scala`, che richiede un nuovo tetto.
3. Accordi da firmare con creator o partner (raggruppati).
4. Chargeback, reclami legali, richieste GDPR (vedi docs/customer-care.md).
Il team-lead raggruppa le richieste in un solo messaggio settimanale, salvo i casi 4 (immediati).

## 8. Costi di esecuzione AI
- Ogni fase riserva il proprio costo AI massimo; il totale AI ha un'allocazione di 60 € nel primo test.
- Agenti operativi su modello `sonnet` (dichiarato nella definizione); QA e team-lead sul modello della sessione.
- Si lanciano in parallelo solo compiti indipendenti con file distinti; niente sessioni parallele sullo stesso file.

## 9. Ripristino
- Un run corrotto non si modifica a mano: si archivia la cartella e si riparte con un nuovo `--run-id`, riusando lo stesso registro (le buste del vecchio run restano contabilizzate).
- Il registro non si modifica mai a mano. Una correzione è una nuova voce motivata in DECISIONI.md, applicata dal codice.

## 10. Account e credenziali (mandato D-017)
1. `python3 -m studio account stato --fase <fase corrente>`: un account si attiva solo se risulta "attivabile".
2. Prima dell'attivazione: verificare prezzo, imposte, commissioni e rinnovo sulla pagina ufficiale (fonte + data in `config/account_catalogo.json`); per le prove gratuite registrare scadenza e condizioni e pianificare la disdetta o la conferma; impostare nel servizio i limiti di spesa disponibili.
3. La riserva del canone nel registro la fa `AccountRegistry.richiedi`. Se è bloccata (residuo o allocazione), l'account non si attiva.
4. Credenziali: `python3 -m studio accessi nuovo --servizio <id> --dati '{"funzione":…,"url_accesso":…,"piano":…}' --genera-password`. La password generata finisce solo nella voce cifrata e non viene mai stampata. Per i token API si usa il modulo sicuro dei segreti dell'ambiente, e in ACCESSI_SISTEMA si registra solo il riferimento.
5. Dopo ogni creazione, modifica, revoca o verifica: nuova voce cifrata (azione `modifica`/`revoca`/`verifica`) con `ultima_verifica`.
6. Recupero (solo il titolare): `python3 -m studio accessi esporta --identita ~/.config/studio/accessi.key`.
7. Passaggi personali: `python3 -m studio account passaggi --fase <fase>`, poi riportati in AZIONI_TITOLARE.md in un'unica richiesta.

## 11. Credenziali operative e prova di continuità (D-025)
- Le credenziali delle integrazioni sono **segreti di rete** dell'ambiente `studio-digitale`: il titolare le salva nel modulo sicuro aperto dal team, e il proxy le inserisce solo verso l'host indicato. Il codice manda un segnaposto, per esempio `LiveShopify(..., credenziale="rete")`.
- Prova di continuità dopo un riavvio (nuova sessione sull'ambiente `studio-digitale`). È l'unica connessione che il cancello consente a questo scopo: solo `httpbin.org`, solo con `STUDIO_LIVE=1` impostato per il comando e solo l'impronta del valore.
```bash
STUDIO_LIVE=1 python3 -c "import pathlib; from studio.adapters.base import ExternalGate; from studio.adapters.live_shopify import verifica_continuita as v; r=v('httpbin.org','https://httpbin.org/headers',gate=ExternalGate('live','runs/calls.jsonl',{'eco'}),intestazione='Authorization',segnaposto='Bearer proxy-injected'); print(r, r['impronta']==pathlib.Path('accessi/.continuita-httpbin').read_text().strip())"
```
  Atteso: `presente: True` e `True` sul confronto con l'impronta salvata (`0d6964cfcffd`). Dopo l'esito positivo il titolare elimina la credenziale di prova dai Segreti di rete.
