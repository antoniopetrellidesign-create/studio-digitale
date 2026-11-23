# QA indipendente — Regia mobile (T-027)

Data: 2026-11-23 · Verificatore: qa-indipendente (non autore) · Oggetto: `studio/regia.py`, `studio/hooks/registra_evento.py`, hook in `.claude/settings.json`, sospensione in `studio/ledger.py` / `studio/workflow.py` / `studio/queue.py` / `studio/phases.py`, `app/regia.html`, `tests/test_regia.py`.
Nessuna rete esterna usata. Nessun file altrui modificato (verificato: `md5sum team/queue.json` invariato prima e dopo, `0c3db89e…`).

## Verdetto: **APPROVATO** dopo la riverifica, con residui non bloccanti (sezione «Riverifica» in fondo)

Verdetto della prima verifica: **BLOCCATO**

Motivi bloccanti (criteri dichiarati nel compito e in `docs/regia.md`, violati con prova riproducibile):
- **H-1/H-2** oscuramento degli eventi incompleto (URL completi, password senza `:`/`=`, chiavi API generiche);
- **C-1** comando `obiettivo` dato per `completato` senza effetto nel motore;
- **C-2** `riprendi` con parametro arbitrario riapre un compito `fatto`;
- **A-1** con il battito oltre soglia e nessun nuovo dato, gli agenti restano "In esecuzione" e animati.

Per sbloccare: correggere le cause (il responsabile è il team-lead) e togliere `@unittest.expectedFailure` dai test corrispondenti, oppure registrare una decisione motivata in DECISIONI.md.

## Esecuzioni
| Comando | Esito |
|---|---|
| `timeout 300 python3 -W ignore -m unittest discover -s tests` | `Ran 198 tests … OK (expected failures=10)`: 166 test preesistenti + 32 QA |
| `timeout 200 python3 -m studio collaudo` | `12/12 casi superati`, uscita 0 (`runs/collaudo-20261123-214828/REPORT.md`) |
| `python3 -m unittest tests.test_qa_regia -v` | 22 ok, 10 expected failure (difetti sotto) |

## Checklist (sezione 10 di `docs/qa-checklist.md`)

### 1. Onestà degli stati: superato con riserve
| Controllo | Esito | Prova |
|---|---|---|
| Un file agente non risulta un processo attivo | OK | `TestQAStati.test_file_agente_non_e_processo_attivo` |
| Avvio senza fine e senza eventi da 25 min → `sconosciuto` | OK | `test_senza_fine_e_senza_eventi_recenti_sconosciuto` |
| Ponte scaduto → `sconosciuto`, nessuna attività corrente | OK | `test_ponte_scaduto_sconosciuto` |
| Passaggi solo da dipendenze registrate e concluse | OK | `test_passaggi_solo_da_dipendenze_registrate_e_concluse` |
| Simulazioni fuori dai numeri | OK | `test_simulazioni_escluse_dai_numeri`: run `completo` con consumo > 0, `regia.numeri()` invariato |
| **R-6** due esecuzioni parallele dello stesso tipo: quella aperta è nascosta da quella conclusa (`concluso`) | DIFETTO (medio) | `studio/regia.py:134,139`: conta solo l'ultima per inizio; `test_esecuzione_aperta_non_nascosta_da_una_parallela_conclusa` |
| **R-7** team-lead con ponte scaduto e attività di 1 min fa → `inattivo` o `in_attesa` con motivo "nessuna attività recente", cioè falso | DIFETTO (minore) | `studio/regia.py:142-145`; `test_team_lead_ponte_scaduto_non_afferma_inattivita` |
| **R-8** una riga troncata in `team/eventi/*.jsonl` (hook interrotto dal timeout di 5 s) fa sollevare `JSONDecodeError` a `istantanea()` | DIFETTO (medio) | `studio/regia.py:79` → `studio/storage.py:42`; `test_riga_eventi_troncata_non_blocca_istantanea` |

### 2. Oscuramento negli hook: BLOCCATO
Prova con input malevoli via stdin: `tests/test_qa_regia.py::TestQAHook` (lo script gira con `CLAUDE_PROJECT_DIR` temporaneo).
| Controllo | Esito | Prova |
|---|---|---|
| Uscita sempre 0 e nessun output (vuoto, JSON rotto, binario, lista, `null`, annidamento di 200.000 livelli, tipi errati) | OK | `test_input_malevoli_uscita_sempre_zero` |
| Comando Bash e contenuti di Write/Edit mai registrati; percorsi fuori progetto omessi | OK | `test_comando_bash_e_contenuto_file_mai_registrati` |
| Token `shpat_`, email, carta a 16 cifre, `password:` oscurati | OK | `test_token_email_carte_oscurati` |
| WebFetch: solo host | OK | `test_webfetch_solo_host` |
| **H-1** URL completi con query (`?access_token=…`) registrati in chiaro nella descrizione Bash, nella query WebSearch e in `last_assistant_message` (esportato poi in `squadra/agenti.ultimo_esito` e `sistema/stato.eventi_recenti`) | **DIFETTO bloccante** | `studio/hooks/registra_evento.py:18-20` (nessuna regola URL), `:43,:51,:71`; `test_url_completi_oscurati_ovunque`. Riprova manuale: `{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"description":"scarica https://api.example.com/v1/orders?access_token=SEGRETO123"}}` → `"sintesi": "scarica https://api.example.com/v1/orders?access_token=SEGRETO123"` |
| **H-2** `--password Hunter2Segreto`, `la password è …`, `api_key=sk-ant-api03-…` non oscurati | **DIFETTO bloccante** | `studio/hooks/registra_evento.py:20` (`password\s*[:=]` soltanto); `test_password_e_chiavi_in_altre_forme` |
| **H-3** `tool_name`, `agent_type`, `notification_type`, `source` e percorso del file registrati grezzi e senza troncamento: un nome con token o un file `accessi/<email>.age` finiscono nel registro, e `agent_type` di 5000 caratteri viene scritto intero | DIFETTO (medio) | `studio/hooks/registra_evento.py:45,62-65,74,76`; `test_campi_grezzi_filtrati` |
| Carta a 19 cifre non oscurata | osservazione | regex `{15,16}` a `:20` |

Il registro eventi reale (`team/eventi/2026-11-23.jsonl`, 199 righe) è stato scansionato con `grep -oE "https?://…|…@…"` e non contiene corrispondenze. È un'evidenza osservata sul registro attuale, non una garanzia per i prossimi eventi.

### 3. Comandi: BLOCCATO
| Controllo | Esito | Prova |
|---|---|---|
| Stesso id due volte → un solo effetto (obiettivo, revisione, risposta) | OK | `test_stesso_id_un_solo_effetto_per_ogni_tipo`, `tests/test_regia.py:73` |
| id non valido, `../../etc/passwd`, id lista, tipo sconosciuto (`__class__`), parametri stringa, operatore `{"$ne":1}`, priorità fuori elenco, richiesta inesistente → `fallito`, coda byte per byte invariata, nessun file di sospensione o di risposte | OK | `test_malevoli_falliscono_senza_effetti` |
| `riprendi` con dipendenze aperte o con attività sospese → rifiutato | OK | `test_riprendi_rifiutato_con_dipendenze_aperte`, `test_riprendi_rifiutato_con_attivita_sospese` |
| `completato` scritto solo dopo l'esito del motore (record a `studio/regia.py:443` dopo l'azione) | OK in generale, **eccetto C-1** | lettura `studio/regia.py:374-447` |
| **C-1** il compito ha id `"OB-" + cid[:10]` e `"RV-" + cid[:10]`. Con gli id dell'app (`"cmd-" + Date.now().toString(36) + …`, `app/regia.html:368`) i primi 10 caratteri coincidono per i comandi inviati entro circa 1,3 s (36² ms). Il secondo obiettivo risulta `completato`, ma il testo va perso perché `q.add` è idempotente e restituisce il compito esistente; inoltre la priorità del primo obiettivo viene sovrascritta | **DIFETTO bloccante** | `studio/regia.py:381,383-385,399`; `test_obiettivi_distinti_entrambi_registrati` |
| **C-2** `riprendi {"compito": "T-001"}` su un compito `fatto` lo riporta a `da_fare` con esito `completato`. L'app offre solo i compiti bloccati, ma il motore accetta qualsiasi id | **DIFETTO bloccante** | `studio/regia.py:420-429` (manca il controllo `stato == "bloccato"`); `test_riprendi_non_riapre_compiti_fatti` |
| **C-3** `sospendi` scrive il file prima della verifica. Se il motore non lo legge, il comando risulta `fallito`, ma la sospensione resta scritta e viene letta da coda e workflow: un fallimento con effetti | DIFETTO (minore, dipende dalla configurazione) | `studio/regia.py:406` contro `:413-415`. Riprodotto con `STUDIO_TEAM_DIR` impostato e `STUDIO_SOSPENSIONE` assente: regia scrive `$STUDIO_TEAM_DIR/sospensione.json`, il registro legge `ROOT/team/sospensione.json` (`studio/ledger.py:107-108`) |
| Il record del motore non contiene `confermato_dal_motore`, mentre l'app mostra "Da confermare" per ogni `completato` privo di quel campo | osservazione (contratto del ponte non scritto nel codice) | `app/regia.html:426`; `studio/regia.py:443` |
| Nessun lock su `team/comandi.jsonl`: due ponti concorrenti possono eseguire lo stesso id | osservazione (oggi il ponte è uno solo) | `studio/regia.py:369-371` |

### 4. Sospensione nel motore: superato con un difetto non bloccante
| Controllo | Esito | Prova |
|---|---|---|
| Nuove riserve rifiutate | OK | `test_nuove_riserve_e_trasferimenti_bloccati_impegni_restano` (`studio/ledger.py:135-138`) |
| Trasferimenti da prenotazioni rifiutati, prenotazione invariata (5000) | OK | stesso test |
| Impegni già assunti: `draw` su busta esistente consentito, riserva idempotente restituita | OK | stesso test |
| Nessuna nuova fase, nessun compito messo `in_corso` | OK | `test_nessuna_nuova_fase_e_nessun_compito_in_corso` (`studio/workflow.py:203`, `studio/queue.py:52-55`) |
| Spesa Ads in Distribuzione: sospensione attivata dopo il giorno 1, consumi solo `giorno-1`, decisione `campagna_in_pausa` | OK | `test_spesa_ads_in_pausa_durante_distribuzione` (`studio/phases.py:443-446`) |
| **S-1** il workflow esenta dalla sospensione la fase già in corso (`studio/workflow.py:203`), ma poi `queue.set_stato(task_id, "in_corso")` (`studio/workflow.py:225`) solleva `RuntimeError: distribuzione-1: nuove attività sospese dal titolare`. La ripresa cade con un'eccezione non gestita invece di completare l'impegno già assunto o bloccarsi con un motivo | DIFETTO (medio; l'errore è comunque a favore della sicurezza, nessuna spesa) | `test_ripresa_fase_in_corso_durante_sospensione_senza_eccezione` |
| Se il file di sospensione è malformato, il registro lo ignora (spese consentite, `studio/ledger.py:114-117`), mentre `regia.sospensione()` solleva un'eccezione (`studio/regia.py:71`, `studio/storage.py:35`) | osservazione: comportamento incoerente, il registro lascia passare le spese | lettura del codice |

### 5. App (analisi statica di `app/regia.html`): BLOCCATO
| Controllo | Esito | Prova |
|---|---|---|
| Nessun `innerHTML`/`outerHTML`/`insertAdjacentHTML`/`document.write`/`eval`; i testi passano da `textContent` (`:134`) | OK | `test_nessun_html_da_dati` |
| La pagina scrive solo `stato:"inviato"` (`:374`); non imposta mai `completato` | OK | `test_pagina_scrive_solo_inviato` |
| id univoco (`crypto.getRandomValues`, `:368`) riusato ai tentativi (`:373`); nessuna riscrittura se il documento esiste (`:379`) | OK | `test_id_riusato_ai_tentativi` |
| Accesso negato ai non titolari prima di aprire il database (`:461-463`) | OK | `test_accesso_negato_ai_non_titolari_prima_del_database` |
| Demo separata: `datiDemo` non usa il database, `invia` esce in demo prima di `claude.use` (`:370`) | OK | `test_demo_separata_e_mai_scritta` |
| L'intestazione mostra "stato non aggiornato" oltre la soglia (`:151`) | OK | `test_soglia_battito_segnalata` |
| **A-1** oltre la soglia, se non arrivano nuovi dati (cioè proprio quando il ponte è morto), si ridisegna solo l'intestazione: `setInterval(renderHeader,30000)` a `:470`. Agenti, KPI "agenti in esecuzione" e animazioni 3D restano "In esecuzione" finché non arriva un nuovo snapshot o l'utente cambia vista. Questo contraddice `docs/regia.md` ("dopo 10 minuti … le animazioni si fermano") | **DIFETTO bloccante** | `test_superata_la_soglia_si_ridisegnano_gli_stati`; correzione suggerita: `setInterval(()=>renderAll(),30000)`, perché `firma()` include `stale()` (`:445`) |
| `quando` del battito non valido: `eta` diventa NaN, la condizione `NaN > soglia` è falsa e la pagina mostra "collegato" (poi `.split("(")[1]` è `undefined` e solleva un errore) | osservazione (minore) | `app/regia.html:150-152` |

## Altre osservazioni (non bloccanti)
- `numeri()` dichiara `simulazioni_escluse: True` come costante. L'esclusione dipende solo dal percorso del file: `python3 -m studio simulate --registro registro/primo-test.json` farebbe entrare spese simulate nei numeri "reali" (`studio/regia.py:208-220`, `studio/__main__.py:56`). Questo è un rischio d'uso, non un difetto osservato.
- Valori fissi presentati come stato: `costi.verificati_eur: 0.0` con la nota "nessuna spesa registrata" anche se il registro esiste (`studio/regia.py:183`); `campagne_esterne_attive: 0` e `arresti_non_confermati: 0` (`:319-320`); `prodotti_selezionati: 0` e pipeline dei prodotti (`:231-233,325`). Oggi sono veri, perché non ci sono integrazioni collegate né registro aperto, ma non sono calcolati dal motore.
- `tests/test_regia.py` copre i casi di base. Non copre hook, collisioni di id, riapertura dei compiti fatti, ripresa della fase in corso né l'analisi dell'app: queste coperture sono aggiunte in `tests/test_qa_regia.py`.

## Difetti per il responsabile (team-lead)
| id | file:riga | gravità | test |
|---|---|---|---|
| H-1 | studio/hooks/registra_evento.py:18-20,43,51,71 | bloccante | `test_url_completi_oscurati_ovunque` |
| H-2 | studio/hooks/registra_evento.py:20 | bloccante | `test_password_e_chiavi_in_altre_forme` |
| C-1 | studio/regia.py:381,399 | bloccante | `test_obiettivi_distinti_entrambi_registrati` |
| C-2 | studio/regia.py:420-429 | bloccante | `test_riprendi_non_riapre_compiti_fatti` |
| A-1 | app/regia.html:470 | bloccante | `test_superata_la_soglia_si_ridisegnano_gli_stati` |
| H-3 | studio/hooks/registra_evento.py:45,62-65 | medio | `test_campi_grezzi_filtrati` |
| S-1 | studio/workflow.py:203 contro 225 (studio/queue.py:52-55) | medio | `test_ripresa_fase_in_corso_durante_sospensione_senza_eccezione` |
| R-6 | studio/regia.py:134,139 | medio | `test_esecuzione_aperta_non_nascosta_da_una_parallela_conclusa` |
| R-8 | studio/regia.py:79 | medio | `test_riga_eventi_troncata_non_blocca_istantanea` |
| R-7 | studio/regia.py:142-145 | minore | `test_team_lead_ponte_scaduto_non_afferma_inattivita` |
| C-3 | studio/regia.py:406 | minore | (riproduzione manuale sopra) |

## Riverifica dopo le correzioni del team-lead (2026-11-23, sera)

Ho verificato in modo indipendente il codice corretto, non solo l'esito dei test. Ho tolto i 10 `expectedFailure`: i test stanno in `tests/test_qa_regia.py`, con il commento "ex DIFETTO … corretto".

| Difetto | Correzione osservata (file:riga) | Prova |
|---|---|---|
| H-1 | `studio/hooks/registra_evento.py:23,32-34,41`: URL ridotti a schema, host e percorso; credenziali `user:pass@`, parametri e frammento eliminati | `test_url_completi_oscurati_ovunque` e `test_nuovo_filtro_url_e_credenziali` (`postgres://admin:S3gret0@…?ssl=…` → solo host e percorso) |
| H-2 | `:24-29,43`: `--password X`, `password è X`, `api_key=`, `sk-…`, stringhe ≥ 32 caratteri | `test_password_e_chiavi_in_altre_forme`, `test_nuovo_filtro_url_e_credenziali` |
| H-3 | `:47-52,62,86-101`: ogni campo passa da `pulisci` ed è troncato; `durata_ms` solo numerico | `test_campi_grezzi_filtrati` |
| C-1 | `studio/regia.py` `tid = "OB-" + cid` / `"RV-" + cid` | `test_obiettivi_distinti_entrambi_registrati`; un id di 80 caratteri resta accettato |
| C-2 | `riprendi` solo su `stato == "bloccato"` | `test_riprendi_non_riapre_compiti_fatti` |
| C-3 | `sospendi` non confermato: ripristina il file precedente o lo rimuove | `test_sospendi_non_confermato_ripristina_il_file` (nuovo) + riproduzione manuale con `STUDIO_TEAM_DIR` senza `STUDIO_SOSPENSIONE`: `fallito`, file assente o ripristinato |
| S-1 | `studio/queue.py` `set_stato`: il controllo vale solo per il passaggio *a* `in_corso` da un altro stato | `test_ripresa_fase_in_corso_durante_sospensione_senza_eccezione`. Le nuove fasi e i nuovi compiti restano bloccati (`test_nessuna_nuova_fase_e_nessun_compito_in_corso`) |
| R-6 | esecuzioni aperte prioritarie su quelle concluse | `test_esecuzione_aperta_non_nascosta_da_una_parallela_conclusa` |
| R-7 | team-lead con attività recente e ponte scaduto → `sconosciuto` | `test_team_lead_ponte_scaduto_non_afferma_inattivita` |
| R-8 | `eventi()` salta le righe non valide | `test_riga_eventi_troncata_non_blocca_istantanea` |
| A-1 | `app/regia.html:459-460,474-475`: `controllaBattito()` ogni 30 s chiama `renderAll(true)` quando cambia lo stato "scaduto" | `test_superata_la_soglia_si_ridisegnano_gli_stati` |

Esecuzioni:
- `timeout 300 python3 -W ignore -m unittest discover -s tests` → `Ran 201 tests … OK (expected failures=1)` (il residuo H-4);
- `timeout 200 python3 -m studio collaudo` → `12/12 casi superati`, uscita 0 (`runs/collaudo-20261123-215430/REPORT.md`).
- Hook con input malevoli (vuoto, JSON rotto, binario, lista, `null`, annidamento di 200.000 livelli, tipi errati): codice di uscita sempre 0.

### Scansione di `team/eventi/*.jsonl` e `team/comandi.jsonl` (ora versionati: rimossi da `.gitignore`)
Ho fatto una scansione indipendente con i miei pattern, non con il filtro dell'hook: URL di qualsiasi schema, email, sequenze di ≥ 10 cifre, stringhe ≥ 24 caratteri, prefissi noti (`shpat_`, `sk-`, `ghp_`, `AKIA`, `xox`, `eyJ`, chiavi private), parole chiave (password, token, secret, api key, otp, bearer, iban, cvv, `segreto://`), percorsi assoluti, IP, telefoni. Ho poi letto a mano tutti i valori distinti di `sintesi`, `ultimo_messaggio`, `file`, `strumento`, `agente_tipo` e `sessione`.
- Righe: `team/eventi/2026-11-23.jsonl` 292, `team/comandi.jsonl` 5; tutte JSON valido.
- **Nessun segreto e nessun dato personale.** Gli unici riscontri sono falsi positivi: timestamp, `agente_id` esadecimale, il nome del file `qa/2026-11-23-…`, descrizioni come "Scan event and command logs for secrets". I comandi contengono solo id `cmd-collaudo-000N` ed esiti.
- Eccesso di oscuramento, solo cosmetico: le righe 180-185 hanno `strumento: "[oscurato]"`, le righe 254-255 `sessione: "[oscurat"`. Sono prodotte da versioni intermedie del filtro e non espongono dati.
- Evidenza osservata per lo stato attuale dei file, non una garanzia sugli eventi futuri: le descrizioni sono testo libero, vedi H-4.

### Residui non bloccanti
| id | Descrizione | Prova | Gravità |
|---|---|---|---|
| H-4 | Ancora in chiaro nelle descrizioni: `Authorization: Basic …`, `Bearer` con meno di 16 caratteri, JWT `eyJ…` a segmenti corti, URL senza schema (`www.…?code=…`), segreti nel *percorso* degli URL (webhook Slack), `pass:`/`PWD`/`passphrase`. Un nome di strumento casuale di 40 caratteri `[A-Za-z0-9]` passa come nome (`registra_evento.py:49`) | `test_residui_oscuramento` (`expectedFailure`); riproduzione in stdin come nei test | medio: il testo viene dalle descrizioni scritte dal modello, non dai comandi, e i file attuali sono puliti. Da correggere prima dell'attività pianificata, perché questi file ora finiscono nella cronologia git. Suggerimento: oscurare tutti i parametri e i percorsi degli URL oltre il primo segmento, `\b(basic|bearer)\s+\S+`, `eyJ[\w-]+\.[\w-]+`, `www\.\S+\?\S*` |
| O-1 | `eventi()` non valida il tipo di `agente_id`: una riga modificata a mano con una lista farebbe ancora cadere `stato_agenti`. L'hook ora lo impedisce (`pulisci` → `None`) | lettura `studio/regia.py` | minore |
| O-2 | Restano valide le osservazioni della prima verifica: `confermato_dal_motore` non prodotto dal motore, valori fissi (`campagne_esterne_attive`, `costi.verificati_eur`), esclusione delle simulazioni basata solo sul percorso del registro, file di sospensione malformato ignorato dal registro | sopra | minore |

Nota: nel registro eventi compare un `ultimo_messaggio` "procedi senza aspettare il QA" (riga Stop/SubagentStop). Questo verdetto rende inutile la deroga. Se in futuro si procede nonostante un blocco, la decisione va registrata in DECISIONI.md.

**Verdetto finale: APPROVATO.** Tutti i 5 blocchi e i 5 difetti medi o minori sono corretti, con prove riproducibili. H-4 resta tracciato come residuo da correggere prima del ponte pianificato.

## Seconda riverifica: residuo H-4 (2026-11-23, sera)
- Correzione osservata in `studio/hooks/registra_evento.py`. `CREDENZIALI` ora copre `pass:`/`PWD=`, `Basic`/`Bearer`/`Digest`/`token` seguiti da un valore e i JWT `eyJ…`. `SENZA_SCHEMA` oscura i parametri degli URL senza schema. `SEGMENTO` oscura i segmenti di percorso di 16 o più caratteri, e per gli host `hooks.*` l'intero percorso viene oscurato.
- Ho rieseguito tramite stdin il mio insieme avversariale: Basic, Bearer corto, JWT, `www.…?code=`, webhook Slack, `pass:` → tutti oscurati. Tutti i casi precedenti restano oscurati e l'uscita è sempre 0.
- Ho tolto il marcatore da `test_residui_oscuramento`. `timeout 300 python3 -W ignore -m unittest discover -s tests` → `Ran 201 tests … OK`, con zero expectedFailure.
- Nuova scansione indipendente di `team/eventi/*.jsonl` e `team/comandi.jsonl` (331 righe): URL, email, numeri, stringhe lunghe, prefissi noti, parole chiave, percorsi assoluti, IP. I riscontri sono solo falsi positivi: `agente_id` esadecimale, il nome del file `qa/2026-11-23-…`, una descrizione con la parola "secret". **Nessun segreto né dato personale.**
- Residui minori, non bloccanti e senza test marcato (sono fuori dalle categorie dei criteri o a basso rischio): `PWD <valore>` e `passphrase <valore>` senza separatore, IBAN, e nomi di strumento casuali di 40 caratteri accettati come nome (`registra_evento.py`, `nome_strumento`). Si possono aggiungere al filtro in un prossimo giro.

**Verdetto finale confermato: APPROVATO.**
