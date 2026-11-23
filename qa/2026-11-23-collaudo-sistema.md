# Verdetto QA — collaudo di sistema (T-009)

Data: 2026-11-23 · Verificatore: qa-indipendente (non ha scritto il codice) · Oggetto: motore `studio/`, configurazione, documenti di sistema, al commit `b52f5fe` più le modifiche locali presenti (`STRATEGIA.md` modificato nella working copy).
Checklist applicata: `docs/qa-checklist.md`. Test avversariali: `tests/test_qa_sistema.py` (42 test, di cui 13 `expectedFailure` = difetti dimostrati).
Nessuna azione esterna, nessuna rete: tutti i test usano directory temporanee e adattatori simulati.

## VERDETTO: **BLOCCATO**

Il collaudo dichiarato dal team passa (28/28 test, 11/11 scenari), ma i test avversariali dimostrano **un difetto bloccante** su un limite non negoziabile (tetto di spesa con registro condiviso) e **cinque difetti importanti**, tra cui un buco nel controllo Q6 dei segreti. Il blocco vale per il passaggio alla fase commerciale; la simulazione resta utilizzabile per lo sviluppo.
Per superarlo: correggere i difetti B-1 e I-1…I-5 (i test `expectedFailure` corrispondenti devono diventare test normali verdi), oppure registrare in `DECISIONI.md` la decisione motivata del Team Lead di procedere.

## Controlli (esito e prova)

| # | Controllo | Esito | Prova |
|---|---|---|---|
| B1 | Test del team | OK | `python3 -m unittest discover -s tests` (prima di aggiungere i test QA) → `Ran 28 tests … OK` |
| B1' | Suite completa con test QA | OK (13 difetti noti) | `python3 -m unittest discover -s tests` → `Ran 70 tests … OK (expected failures=13)` |
| B2 | Collaudo end-to-end | OK | `python3 -m studio collaudo --runs-dir /tmp/claude-qa-collaudo` → `11/11 casi superati` (completo, doppia_attribuzione, rimborso, qa_respinge, qa_respinge_definitivo, shopify_senza_accesso, spesa_oltre_tetto, canale_primario_senza_budget, interruzione, azioni_esterne_bloccate, tetto_condiviso) |
| B3 | Fasi fuori ordine rifiutate | OK | `test_fasi_fuori_ordine_rifiutate_ovunque`: ogni fase 2–10 all'avvio → `RuntimeError`; fase già approvata → `RuntimeError` |
| B4 | Ripresa senza rieseguire fasi approvate | OK | `test_run_concluso_non_riesegue_nulla`, `test_resume_cli_su_run_completato_non_spende` (registro identico byte per byte), `test_ripresa_dopo_blocco_non_riesegue_fasi_approvate` (sequenza `fase_approvata` = 10 fasi, una volta ciascuna) |
| F1–F3 | Fonti tipizzate, ≥2 osservate, dati sintetici marcati | OK | collaudo caso `completo` (scheda incompleta scartata, selezionata `OPP-SIM-A`); fixture con `"sintetico": true` |
| F4 | Fonti verificabili | N.A. | url `esempio.invalid` sintetici: in collaudo non c'è evidenza di mercato (D-011) |
| P1–P5 | Promesse, checksum, licenza, piano, scheda in bozza | OK | collaudo `qa_respinge` (Q1/Q3 bloccano il prodotto difettoso), `completo` (bozza, download verificato) |
| T1 | Eventi di tracciamento | OK con riserva | `studio/phases.py:224` lista statica, nessun controllo che li verifichi (vedi M-7) |
| T2 | Deduplica ordini | OK | `test_ordine_duplicato_in_distribuzione_non_raddoppia_commissione`: payload diverso con stesso ID → resta il primo (IT), 14 ordini, 1 commissione |
| T3 | Ordine di prova escluso dai KPI | OK | `test_misurazione_non_conta_ordine_di_prova`: 15 ordini nel libro, 14 in misurazione |
| T4 | Ricavo contato una volta | OK | collaudo `doppia_attribuzione`; `controllo_doppio_conteggio_ok: true` |
| T5 | Rimborso di ordine inesistente | **KO** | difetto I-3 |
| C1–C5 | IVA, fee non rimborsata, commissione 30% su netto, ROAS sul margine, margine | OK | `test_roas_e_margine_del_run_seguono_la_formula` (ricalcolo indipendente da ordini e registro), `test_esempio_strategia_unit_economics` (N=2000, C_pag=101, C_cr=600 come STRATEGIA §2) |
| C3 | Clawback | OK | `test_rimborso_dopo_clawback_commissione_e_fee_restano` (rimborso al giorno 32: commissione non stornata, fee inclusa), `test_rimborso_al_limite_della_finestra_storna` (giorno 31 = 30 giorni: stornata), `test_rimborso_doppio_non_raddoppia_storno` |
| C6 | Regole stop/ripeti/scala | OK | `test_regole_decisione_strategia_par5` (8 casi di confine), `test_esempio_strategia_regola_ripeti` (ROAS 1,35 → ripeti) |
| L1 | Tetto con registro condiviso | **KO** | difetto B-1 |
| L2 | Allocazione per categoria | OK | `test_allocazione_non_aggirabile_con_buste_piccole` (20×10 € poi 1 cent → blocco), `test_tetto_non_superabile_sommando_le_categorie` |
| L4 | Vie indirette (storno+consumo, ID ripetuti, buste chiuse) | OK con difetti minori | `test_storno_e_nuovo_consumo_non_superano_il_massimo`, `test_busta_chiusa_non_si_riapre`, `test_id_busta_ripetuto_con_importo_diverso_bloccato` → OK; M-1, M-2, M-3 |
| L5 | Limiti contrattuali creator | **KO** | difetto I-4 |
| L6 | Disponibilità di tutte le categorie alla Selezione | **KO** | difetto I-2 |
| L7 | Fine test senza buste aperte | OK nel caso nominale | collaudo `completo` (impegnato 0); KO nel caso I-2 |
| E1–E2 | Nessuna azione reale; live blocca senza consumi | OK | `test_live_blocca_senza_consumi_anche_con_studio_live` (anche con `STUDIO_LIVE=1`: stato `bloccato` in `strategia`, consumato 0, impegnato 0, chiamate `bloccato`), `test_live_ripreso_resta_bloccato_e_non_spende` (3 riprese) |
| E3 | Nessun codice di rete | OK | `grep -rnE "import (requests\|urllib\|smtplib\|http\.client\|socket)" studio/` → nessun risultato |
| S1 | Q6 segreti nel run | **KO parziale** | `test_q6_blocca_segreto_nella_cartella_del_run` e `test_q6_blocca_numero_di_carta_finto` → BLOCCATO correttamente; ma difetto I-1 (sottocartelle) e M-5 (formati) |
| S2 | Credenziali/dati personali versionati | OK | `git -C /home/user ls-files \| xargs grep -nIE '<token Shopify/Stripe/GitHub/AWS, chiavi private, carte, IBAN, email, +39>'` → solo la definizione del pattern `studio/phases.py:44` e testo descrittivo; `test_nessuna_credenziale_o_dato_personale_versionato` OK |
| S3 | `runs/` e segreti non versionati | OK | `git ls-files runs` → `runs/.gitkeep`; `.gitignore` copre `.env*`, `secrets/`, `settings.local.json` |
| S4 | Dati minimi, niente `read_customers` | OK | `studio/adapters/mock.py:23-24`; `invia_link` non registra dati personali |
| D1 | Coerenza STRATEGIA/WORKFLOW ↔ codice | OK con difetti minori | classe `TestQACoerenza`; M-4, M-6 |
| D2 | Parametri di config letti dal codice | **KO** | `grep -rn <chiave> studio/*.py` → 0 occorrenze per `compenso_fisso_max_per_creator_cents`, `tetto_commissioni_per_test_cents`, `commissione_pagamento_rimborsata_su_refund`, `max_opportunita_per_test` |
| D3 | Riferimenti a DECISIONI.md | OK | `STRATEGIA.md:209-213` nella working copy puntano a D-007, D-008, D-003 (corretti) |

## Difetti

### Bloccante
**B-1 Registro condiviso senza blocco: il tetto di 500 € si può superare.** `studio/ledger.py:44-46` legge il file una sola volta nel costruttore; `studio/ledger.py:190-191` riscrive l'intero file a ogni operazione, senza lock né rilettura. Due run in parallelo sullo stesso `--registro` (la CLI lo consente, `studio/__main__.py:57`) calcolano il residuo su dati vecchi: entrambe le riserve passano e l'ultima scrittura cancella l'altra, quindi il registro non mostra l'impegno reale. Viola la regola non negoziabile 1 di CLAUDE.md.
Riproduzione: `test_registro_condiviso_due_istanze_non_superano_l_allocazione`: due `Ledger` sullo stesso file riservano ciascuno 200 € di ads, nessun `SpendBlocked`. Impegno reale 400 € su un'allocazione di 200 €.

### Importanti
**I-1 Q6 non controlla le sottocartelle del run.** `studio/workflow.py:135-143` usa `os.listdir` + `isfile`, quindi `runs/<id>/artifacts/*.json` (gli output delle fasi) non viene scansionato. Riproduzione: `test_q6_blocca_segreto_negli_artifacts`: con un token Shopify finto in `artifacts/appunti.json` il QA dà `APPROVATO`.

**I-2 La Selezione non riserva il costo AI delle fasi restanti.** In `studio/phases.py:141-155` mancano le 7 fasi × `costi_ai.max`. Con l'allocazione AI quasi esaurita il test passa la Selezione, attiva i canali e spende, poi si blocca alla Decisione: la busta commissioni `r/creator-CR-SIM-1-commissioni` resta aperta e il codice creator non viene sospeso. Contrario a D-006. Riproduzione: `test_categoria_ai_esaurita_scoperta_prima_di_spendere`, con 47 € di AI già consumati nel registro condiviso → `stato bloccato in fase decisione, buste aperte ['r/creator-CR-SIM-1-commissioni']`.

**I-3 Un rimborso per un ordine inesistente manda in crash il run.** `studio/phases.py:351` → `KeyError` non gestito. Lo stato resta `in_esecuzione: distribuzione` e ogni `resume` ripete il crash. Riproduzione: `test_rimborso_ordine_inesistente_non_manda_in_crash_il_run`. Da CLI, con lo scenario `completo` più il rimborso `SIM-9999`, sia `simulate` sia `resume` terminano con `KeyError: 'rimborso per ordine inesistente: SIM-9999'`.

**I-4 I limiti contrattuali creator non sono applicati.** I valori `compenso_fisso_max_per_creator_cents` (30 €) e `tetto_commissioni_per_test_cents` di `config/commissioni.json` non vengono mai letti. `studio/phases.py:265-271` riserva gli importi del piano così come sono. Riproduzione: `test_compenso_fisso_oltre_il_massimo_per_creator_bloccato`: con un compenso fisso di 60 € a un solo creator il run consuma 6000 cent (atteso ≤ 3000).

**I-5 Paese senza aliquota IVA: il run va in crash.** `studio/phases.py:330` `IVA_BP[...]` → `KeyError` (es. `BE`). Gli effetti sono gli stessi di I-3: crash ripetuto alla ripresa invece di un blocco motivato. Riproduzione: `test_paese_senza_aliquota_iva_non_manda_in_crash_il_run`. (Classificato importante perché la tabella IVA è sintetica e incompleta, D-010.)

### Minori
- **M-1** `studio/ledger.py:124-125`: un `draw` con un ID già registrato e un importo diverso ritorna `False` senza segnalare nulla, mentre `reserve` blocca i parametri diversi (`:96-97`). Riproduzione: `test_consumo_ripetuto_con_importo_diverso_e_segnalato`.
- **M-2** `studio/ledger.py:128`: `draw` accetta `True` come importo, mentre `reserve` lo rifiuta (`:99`). Riproduzione: `test_importo_booleano_rifiutato_nel_consumo`.
- **M-3** `studio/ledger.py:157-162`: se `spend_once` è bloccato perché l'effettivo supera il massimo, la busta resta aperta con 36 € impegnati per sempre (non ha tag `canale:`). Riproduzione: `test_spesa_singola_bloccata_non_lascia_impegni_aperti` → `3600 != 0`.
- **M-4** `studio/economics.py:98,105`: un ROAS indefinito diventa `10**9` e nei motivi della decisione compare come "ROAS sul margine 10000000.00". Con ≥10 ordini, acquisizione zero e margine negativo l'esito è "ripeti". Riproduzione: `test_roas_indefinito_non_compare_come_numero_nei_motivi`.
- **M-5** `studio/phases.py:44`: il pattern `SEGRETI` non riconosce token GitHub `ghp_`, chiavi AWS `AKIA…`, `sk_test_` né `Bearer`. Riproduzione: `test_q6_riconosce_altri_formati_di_token` → `APPROVATO`.
- **M-6** `studio/orders.py:59`: il flag `commissione_pagamento_rimborsata_su_refund` non viene letto (vale anche per `max_opportunita_per_test`). Il comportamento è corretto con il valore attuale `false`, ma se la policy cambia non succede nulla. Riproduzione: `test_flag_fee_rimborsata_letto_dal_codice`.
- **M-7** `studio/orders.py:19-25`: un duplicato con payload diverso viene scartato senza registrare il conflitto. Inoltre `studio/phases.py:224`: gli eventi di tracciamento sono una lista fissa che nessun controllo verifica. Riproduzione: `test_duplicato_con_payload_diverso_e_tracciato_come_conflitto`.

## Note
- Fuori dal perimetro di scrittura di questo compito: non ho aggiornato `team/queue.json` (T-009). Il Team Lead deve segnare T-009 come `fatto` con esito BLOCCATO e aprire un compito per ogni correzione: B-1, M-1, M-2 e M-3 a strategia-finanza (ledger); I-2, I-3 e I-5 al team-lead (phases e workflow); I-1 e M-5 al team-lead (scan_segreti e SEGRETI); I-4 a creator-partnership con il team-lead.
- Escalation: Team Lead. Se decide di procedere nonostante il blocco, la decisione va registrata in `DECISIONI.md` con la motivazione.
