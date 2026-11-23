# Verdetto QA T-021 — credenziali di rete, registro account, schede di ricerca reali (D-025…D-028)

- Data: 2026-11-23 · Verificatore: qa-indipendente (non ha scritto il codice o le schede verificate)
- Oggetto: HEAD `a18ef93` (studio/vault.py, studio/adapters/live_shopify.py, accessi/.continuita-httpbin, research/A-*.json, research/B-*.json, research/GRADUATORIA-2026-11-23.md)
- Nessuna rete esterna, nessuna azione esterna: l'unico server HTTP usato nei test è su 127.0.0.1.
- Test aggiunti: `tests/test_qa_credenziali_ricerca.py` (14 test, di cui 5 `expectedFailure` = difetti reali)

## Verdetto: **BLOCCATO**

Controllo bloccante KO: la graduatoria di riferimento (`research/GRADUATORIA-2026-11-23.md`) **non corrisponde** ai punteggi ricalcolati dal motore sulle schede presenti nel repository (D-1). Si sblocca allineando graduatoria e schede (una delle due fonti deve prevalere in modo esplicito) o con decisione registrata in `DECISIONI.md`.
Il blocco riguarda il passaggio Ricerca → Selezione (graduatoria come base della prossima selezione). **Non** riguarda la sicurezza delle credenziali: lì nessun segreto è presente nei file (evidenza osservata), con due difetti non bloccanti oggi (D-3, D-4), da correggere prima del primo uso reale di `aggiorna_registro` e prima di ripetere la prova di continuità.

## Base
| # | Controllo | Esito | Prova |
|---|---|---|---|
| B1 | Test | OK | [CMD] `timeout 300 python3 -m unittest discover -s tests` → `Ran 146 tests … OK (expected failures=5)` (prima dell'aggiunta: 132 test OK) |
| B2 | Collaudo | OK | [CMD] `timeout 200 python3 -m studio collaudo` → `12/12 casi superati` (report `runs/collaudo-20261123-205357/REPORT.md`) |

## 1. Credenziali e registro account
| # | Controllo | Esito | Prova |
|---|---|---|---|
| C1 | `aggiorna_registro` rifiuta campi segreti (`password`, `token`, `codici_recupero`, `chiave_api`, `secret`) e riferimenti che non iniziano con `rete://` / `segreto://` | OK | [TEST] `test_campi_segreti_rifiutati_e_riferimenti_ammessi`; studio/vault.py:100-105 |
| C2 | Il registro non contiene MAI password/token/codici, anche nei valori | **KO (non bloccante oggi)** | [TEST] `test_DIFETTO_token_nel_valore_di_un_campo_ammesso` — vedi D-3 |
| C3 | Registro reale nel repository senza segreti | OK | [CMD] `ls -la accessi` → solo `voci/` (vuota) e `.continuita-httpbin`: `registro.json`/`REGISTRO.md` non esistono ancora; [TEST] `test_registro_reale_nel_repository_senza_segreti` |
| C4 | Scansione dei file versionati con `studio.phases.SEGRETI` | OK | [CMD] scansione di `git ls-files` + `accessi/.continuita-httpbin` → 3 corrispondenze, tutte falsi positivi: `studio/__main__.py:137` (`genera_password:` nome di flag), `tests/test_qa_sistema.py` (carta di prova 4111…, commento `password:` a riga 392) |
| C5 | `LiveShopify(credenziale="rete")`: nella richiesta va solo il segnaposto, mai il valore della variabile d'ambiente | OK | [TEST] `test_rete_solo_segnaposto_nella_richiesta` (con `SHOPIFY_ADMIN_TOKEN` impostato a un token finto, l'header inviato è `segnaposto-segreto-di-rete`); live_shopify.py:60-61 |
| C6 | Cancello valido anche in modalità rete: STUDIO_LIVE≠1, integrazione non collaudata o modalità `simulato` ⇒ `ExternalActionBlocked` e **zero richieste HTTP** | OK | [TEST] `test_rete_nessuna_richiesta_se_il_cancello_e_chiuso`; live_shopify.py:56-58 precede il ramo `rete` |
| C7 | https e `*.myshopify.com` obbligatori anche in modalità rete (anche `x.myshopify.com.evil.example`, `evil.example` come negozio) | OK | [TEST] `test_rete_https_e_host_myshopify_obbligatori`; live_shopify.py:47-52 |
| C8 | `verifica_continuita` restituisce solo `presente` + impronta troncata (12 hex), mai il valore | OK | [TEST] `test_continuita_restituisce_solo_impronta`; live_shopify.py:106-110. Nessuna stampa: la funzione non ha `print` né chiamante CLI (`grep -rn continuita studio/`) |
| C9 | `verifica_continuita` soggetta al cancello / https / host | **KO (non bloccante oggi)** | [TEST] `test_DIFETTO_continuita_fuori_dal_cancello` — vedi D-4 |
| C10 | `accessi/.continuita-httpbin` contiene solo un'impronta troncata | OK | [CMD] `cat accessi/.continuita-httpbin` → `0d6964cfcffd` (12 hex). L'impronta del segnaposto è `37ab1b6dbd69` (`python3 -c "import hashlib;print(hashlib.sha256(b'segnaposto-segreto-di-rete').hexdigest()[:12])"`): il valore registrato è dunque quello iniettato dal proxy, conservato solo come 48 bit di SHA-256 (non reversibile per un token casuale). [TEST] `test_file_continuita_solo_impronta_troncata`. La credenziale su `httpbin.org` è di prova e la sua eliminazione è già in `AZIONI_TITOLARE.md:17,55` |

## 2. Schede di ricerca reali
| # | Controllo | Esito | Prova |
|---|---|---|---|
| R1 | 12 schede `A-*`/`B-*` valide per `valida_opportunita`, `"sintetico": false` | OK | [TEST] `test_schede_presenti_valide_e_reali`; [CMD] ricalcolo: 0 errori su 12 |
| R2 | Ogni fonte `osservata` ha url https e data | OK | [TEST] stesso test (url `https://`, data `2026-MM-GG`, nessun `.invalid`) |
| R3 | Nessuna cifra presentata come osservata senza fonte | **KO (minore)** | [TEST] `test_DIFETTO_prezzi_osservati_senza_fonte` — vedi D-5 |
| R4 | La graduatoria corrisponde ai punteggi ricalcolati dal motore | **KO (bloccante)** | [TEST] `test_DIFETTO_graduatoria_corrisponde_al_motore`, `test_DIFETTO_esito_coerente_col_punteggio` — vedi D-1, D-2 |
| R5 | Nessuna opportunità selezionata sotto soglia (60, ≥ 2 fonti osservate) | OK | [TEST] `test_nessuna_selezione_sotto_soglia`: punteggio massimo ricalcolato 56 (`B-it-bilancio-familiare`, `B-en-home-maintenance-binder`); nessun `esito` dice «selezionata»; `products/` assente; GRADUATORIA:30 «Nessun prodotto selezionato» |

Punteggi ricalcolati (`studio.phases.punteggio` / `fonti_osservate`) sulle schede in HEAD: IT bilancio 56/3 · EN home binder 56/2 · A freelance 54/4 · A etsy-pricing 54/4 · A welcome-book 53/4 · A gaestemappe 53/4 · DE Haushaltsbuch 52/3 · FR classeur 52/3 · A content-calendar 52/2 · EN language planner 50/2 · ES oposiciones 47/0 · A angebot 47/3.

## Difetti
| ID | Gravità | File:riga | Descrizione | Prova |
|---|---|---|---|---|
| D-1 | **bloccante** | research/GRADUATORIA-2026-11-23.md:15-17 vs research/B-es-planificador-oposiciones.json:33, research/B-de-haushaltsbuch.json (punteggi), research/B-en-language-learning-planner.json (punteggi) | La graduatoria dichiara «punteggi ricalcolati dal motore» e riporta #1 ES 58 (4 osservate), #2 DE 58 (3), #3 EN 57 (2). Le schede attuali, modificate in `a18ef93` con i ribassi prudenziali, danno **47 (0 osservate), 52, 50**. D-028 dice che la graduatoria di riferimento resta quella del primo ciclo, ma i file letti dal motore contengono i valori ribassati: con i dati attuali le prime tre non sono le prime tre (ordine reale: IT 56, EN binder 56, …). Inoltre la scheda ES declassa a `ipotesi` gli estratti della ricerca web, contro la regola uniforme di D-028 (estratti = osservata di tipo *estratto*). | [CMD] `git show 6ca154b:research/B-es-planificador-oposiciones.json` → 58/4; HEAD → 47/0. [TEST] `test_DIFETTO_graduatoria_corrisponde_al_motore` |
| D-2 | minore | research/B-en-language-learning-planner.json:43 | `esito` scrive «punteggio 57 < 60» ma il motore dà 50; ES `esito` «47,5» e IT «56,5» non sono valori che il motore può produrre (divisione intera) | [TEST] `test_DIFETTO_esito_coerente_col_punteggio` |
| D-3 | media (non bloccante finché il registro non è usato) | studio/vault.py:27, 104 | `SEGRETI_VIETATI` è definito ma mai usato; il riferimento è controllato solo nel prefisso e i valori dei campi ammessi non sono controllati: `segreto://shopify/shpat_…`, `rete://host/shpat_…`, `url` con `utente:password@` e `funzione` con un token finiscono in chiaro in `registro.json` e `REGISTRO.md`. Correzione proposta ad account-integrazioni: rifiutare valori che corrispondono a `studio.phases.SEGRETI`, url con userinfo, e riferimenti che non rispettano `^(rete://[a-z0-9.-]+/[A-Za-z0-9-]+|segreto://[a-z0-9_-]+/[a-z_]+)$`. | [TEST] `test_DIFETTO_token_nel_valore_di_un_campo_ammesso` |
| D-4 | media (non bloccante finché la prova non viene ripetuta) | studio/adapters/live_shopify.py:97-104 | `verifica_continuita` apre una connessione verso un URL qualsiasi, anche `http://` e con `STUDIO_LIVE` assente o 0, senza `ExternalGate` né registrazione in `calls.jsonl`. È un'azione esterna (verso un host a cui il proxy inietta una credenziale) fuori dal cancello previsto da CLAUDE.md («le integrazioni reali eseguono azioni solo se … STUDIO_LIVE=1»). Correzione proposta: parametro `gate` obbligatorio (servizio dedicato, es. `continuita`), https obbligatorio salvo 127.0.0.1/localhost, host dell'URL uguale a `host`. | [TEST] `test_DIFETTO_continuita_fuori_dal_cancello` (1 richiesta ricevuta con STUDIO_LIVE=0) |
| D-5 | minore | research/B-de-haushaltsbuch.json:21; research/B-en-home-maintenance-binder.json:17 | Concorrenti marcati `tipo_dato: "osservata"` con cifre assenti da ogni fonte osservata della scheda: «7,03 CAD» e «scontato da 9,91». Vanno aggiunte alla fonte o marcate ipotesi. | [TEST] `test_DIFETTO_prezzi_osservati_senza_fonte` |

## Osservazioni (non difetti)
- Tutte le fonti osservate sono estratti della ricerca web (pagine mai aperte): coerente con D-027/D-028 e dichiarato nelle schede; F4 (verificabilità della pagina) resta da fare nel ciclo T-020.
- Il controllo di localhost in `LiveShopify` ammette `http` per i test: accettabile, nessun host esterno passa.
- T-021 non era presente in `team/queue.json`: aggiunto da qa-indipendente e impostato a `bloccato` con riferimento a questo verdetto.

## Escalation
Al Team Lead: D-1 (ricerca-mercato per schede e GRADUATORIA, team-lead per l’applicazione di D-028), D-3 e D-4 (account-integrazioni), D-2 e D-5 (ricerca-mercato). Se si procede senza correggere D-1, la decisione va registrata in `DECISIONI.md` con motivazione.

---

# Riverifica dopo le correzioni (2026-11-23, stesso giorno)

Oggetto: modifiche non ancora committate su `a18ef93` (`git status`: studio/vault.py, studio/adapters/live_shopify.py, research/B-*.json, research/GRADUATORIA-2026-11-23.md, tests/test_vault.py, tests/test_live_shopify.py). Controllo limitato alle correzioni e alla regressione completa. Test QA aggiornati in `tests/test_qa_credenziali_ricerca.py`: 17 test, di cui 2 `expectedFailure`.

## Verdetto aggiornato: **BLOCCATO** (solo per la prova di continuità delle credenziali; Ricerca APPROVATA)

| # | Controllo | Esito | Prova |
|---|---|---|---|
| B1 | Test | OK | [CMD] `timeout 300 python3 -m unittest discover -s tests` → `Ran 151 tests … OK (expected failures=2)` |
| B2 | Collaudo | OK | [CMD] `timeout 200 python3 -m studio collaudo` → `12/12 casi superati` (`runs/collaudo-20261123-210040/REPORT.md`) |
| D-1 | Graduatoria = motore | **risolto** | [TEST] `test_risolto_graduatoria_corrisponde_al_motore`: le 12 righe coincidono con `punteggio`/`fonti_osservate` (DE 58/3, EN planner 57/2, IT 56/3, binder 56/2, ES 55/4, …). I punteggi B coincidono con `6ca154b` (ribassi annullati); ES passa da *problema* 7 a 6 per D-028 |
| D-1b | D-028: *problema* e *concorrenza* ≤ 6 con soli estratti | OK | [TEST] `test_problema_e_concorrenza_al_massimo_6_con_soli_estratti` (12/12 schede) |
| D-2 | `esito` coerente col punteggio | **risolto** | [TEST] `test_risolto_esito_coerente_col_punteggio` |
| D-5 | Prezzi osservati senza fonte | **risolto** | [TEST] `test_risolto_prezzi_osservati_senza_fonte` |
| R5 | Nessuna selezione sotto soglia | OK | [TEST] `test_nessuna_selezione_sotto_soglia` (il controllo esclude ora «non selezionata»); massimo 58 < 60 |
| D-3 | Segreti nei valori del registro (stringhe) | **risolto** | [TEST] `test_risolto_token_nel_valore_di_un_campo_ammesso`; studio/vault.py:36-52 |
| D-7 (nuovo) | Segreti nei valori **non stringa** del registro | **KO, media, non bloccante finché il registro non è usato** | studio/vault.py:40-41 (`if not isinstance(valore, str): return`): `{"funzione": ["shpat_…"]}` e `{"costo": {"x": "shpat_…"}}` finiscono in chiaro in `registro.json`. [TEST] `test_DIFETTO_segreto_in_valore_non_stringa`. Correzione proposta: rifiutare i valori non scalari oppure controllare `json.dumps(valore)` |
| D-4 | `verifica_continuita`: gate obbligatorio, solo https verso eco ammessi, live chiuso ⇒ blocco senza connessione | **risolto** | [TEST] `test_risolto_continuita_senza_gate_o_fuori_elenco` |
| D-6 (nuovo, residuo di D-4) | Connessione reale in modalità `simulato` | **KO, bloccante per la prova di continuità** | studio/adapters/live_shopify.py:120-122: con `ExternalGate("simulato")` `gate.record` restituisce «simulato» senza sollevare e la funzione apre comunque una connessione **reale** verso `https://httpbin.org/headers` (host a cui il proxy inietta la credenziale), senza `STUDIO_LIVE=1` e senza `eco` collaudata. Viola CLAUDE.md («le integrazioni reali eseguono azioni solo se dichiarate collaudate e con `STUDIO_LIVE=1`») e contraddice «nessuna connessione senza permesso». [TEST] `test_DIFETTO_continuita_connessione_reale_in_modalita_simulato` (urlopen sostituito: 1 tentativo verso httpbin.org, nessuna rete usata). Correzione proposta: prima della connessione richiedere `gate.live_consentito("eco")`, ammettendo `simulato` solo per 127.0.0.1/localhost; in alternativa, decisione del Team Lead in DECISIONI.md |
| C10 | `.continuita-httpbin` | OK | [CMD] `cat accessi/.continuita-httpbin` → `0d6964cfcffd` (invariato) |

## Note sulle richieste del Team Lead
- `test_continuita_restituisce_solo_impronta` ora passa un gate, ma **live con permesso esplicito** (`STUDIO_LIVE=1`, `eco` tra le collaudate) verso il server locale, non `ExternalGate("simulato")`: usare `simulato` avrebbe fatto accettare dal test proprio il comportamento di D-6. Anche tests/test_live_shopify.py:124,129 (account-integrazioni) usa `simulato` per una connessione: va adeguato insieme alla correzione di D-6.
- Osservazioni non bloccanti (limiti dell'euristica, non difetti): `username` con `utente:password` senza schema e un token casuale con l'aspetto di un nome di intestazione dopo `rete://host/` vengono accettati, perché non distinguibili da valori legittimi. GRADUATORIA:32 dice ancora «Se una delle **tre** supera 60», ma ora le candidate sono quattro.

## Escalation
Al Team Lead: D-6 (account-integrazioni) blocca la ripetizione della prova di continuità finché non è corretto o non c'è una decisione registrata in DECISIONI.md. D-7 va corretto prima del primo `aggiorna_registro` reale. La parte Ricerca (D-1, D-2, D-5) è approvata.

---

# Verdetto finale (seconda riverifica, 2026-11-23)

## **APPROVATO**

| # | Controllo | Esito | Prova |
|---|---|---|---|
| D-6 | `verifica_continuita` non apre connessioni senza permesso live, `simulato` compreso | **risolto** | studio/adapters/live_shopify.py:127-129 (`if not gate.live_consentito("eco")` → registra «bloccato» e solleva `ExternalActionBlocked` prima di `urlopen`); [TEST] `test_risolto_continuita_connessione_reale_in_modalita_simulato` (0 tentativi verso httpbin.org con urlopen sostituito). `eco` non è in `config/integrazioni_collaudate.json` ([CMD] `grep -c '"eco"' config/integrazioni_collaudate.json` → 0): oggi nessuna connessione reale è possibile |
| D-7 | Segreti in valori non stringa del registro | **risolto** | studio/vault.py:39-46 (discesa ricorsiva in dict, chiavi comprese, e in list/tuple/set); [TEST] `test_risolto_segreto_in_valore_non_stringa` |
| B1 | Regressione test | OK | [CMD] `timeout 300 python3 -m unittest discover -s tests` → `Ran 153 tests … OK` (nessun expectedFailure, nessun unexpected success) |
| B2 | Collaudo | OK | [CMD] `timeout 200 python3 -m studio collaudo` → `12/12 casi superati` (`runs/collaudo-20261123-210227/REPORT.md`) |

Difetti D-1…D-7: tutti risolti, ciascuno coperto da un test `test_risolto_*` in `tests/test_qa_credenziali_ricerca.py`. Restano solo le osservazioni non bloccanti della riverifica precedente: limiti dell'euristica sui segreti, e la dicitura «una delle tre» in GRADUATORIA:32.
Nota: le correzioni non sono ancora committate (`git status`); il verdetto vale per il contenuto attuale dei file.
