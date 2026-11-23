# Checklist QA — passaggio di fase

Responsabile: qa-indipendente. Si usa a ogni passaggio di fase critico (in particolare QA → Shopify, Ordine di prova → Distribuzione, Misurazione → Decisione) e a ogni collaudo di sistema.

## Come si usa
- Ogni controllo ha un **esito** (`OK` / `KO` / `N.A.` con motivo) e una **prova**: comando eseguito con output sintetico, oppure `file:riga`. Senza prova il controllo vale `KO`.
- Tipi di prova: **[CMD]** comando riproducibile con output; **[FILE]** riferimento `file:riga` o campo JSON; **[TEST]** test automatico in `tests/` (nome del test); **[ISP]** ispezione manuale motivata (solo dove non esiste un controllo automatico, e va detto).
- Un solo `KO` in un controllo **bloccante** ⇒ verdetto `BLOCCATO`. Il blocco si supera correggendo la causa o con decisione registrata in `DECISIONI.md`.
- Il verdetto va in `qa/<data>-<oggetto>.md`. I difetti trovati diventano test in `tests/test_qa_*.py` (con `@unittest.expectedFailure` finché non sono corretti).
- Variabili: `RUN=runs/<id>` (o `--runs-dir`), `ID=<run_id>`.

## 0. Base
| # | Criterio | Prova richiesta | Bloccante |
|---|---|---|---|
| B1 | Tutti i test passano (gli `expectedFailure` sono difetti noti elencati nel verdetto) | [CMD] `python3 -m unittest discover -s tests` → `OK` | sì |
| B2 | Collaudo end-to-end superato | [CMD] `python3 -m studio collaudo --runs-dir <tmp>` → `N/N casi superati` | sì |
| B3 | Ordine delle fasi rispettato; nessuna fase approvata due volte senza ritorno QA registrato | [CMD] `python3 -m studio decisions --run-id $ID` (sequenza `fase_approvata`) + [TEST] `test_fasi_fuori_ordine_rifiutate_ovunque` | sì |
| B4 | Ripresa: le fasi approvate non si rieseguono (`tentativi` = 1 salvo ritorni QA) | [FILE] `$RUN/state.json` campo `tentativi`, `riprese` | sì |

## 1. Fonti (Ricerca, Selezione)
| # | Criterio | Prova richiesta | Bloccante |
|---|---|---|---|
| F1 | Ogni fonte è `osservata` (con `url` e `data`) o `ipotesi`; nessuna ipotesi presentata come fatto | [FILE] `$RUN/artifacts/ricerca.json` → `scartate` con errori; [CMD] verifica dei campi `tipo`, `url`, `data` | sì |
| F2 | Opportunità selezionata con ≥ 2 fonti osservate e punteggio ≥ soglia (`config/policy.json` → `selezione`) | [FILE] `$RUN/artifacts/selezione.json` → `classifica[].fonti_osservate`, `punteggio`, `idonea` | sì |
| F3 | In simulazione ogni dato è `sintetico: true`; in fase commerciale nessun dato sintetico | [FILE] `ricerca.json`, `orders.json` (`sintetico`) | sì |
| F4 | Le fonti osservate sono verificabili (url raggiungibile dal titolare, data plausibile) | [ISP] campione di fonti con esito per fonte; in collaudo `N.A.` (url `.invalid`) | sì in fase commerciale |

## 2. Prodotto
| # | Criterio | Prova richiesta | Bloccante |
|---|---|---|---|
| P1 | Ogni promessa dell'offerta è coperta da almeno un file | [FILE] `$RUN/artifacts/qa.json` → Q1; `prodotto.json` → `manifest.promesse`, `files[].copre_promesse` | sì |
| P2 | Ogni file ha sha256 valido; il download dell'ordine di prova coincide con i checksum | [FILE] `qa.json` Q2; `ordine_prova.json` → `download_ok: true` | sì |
| P3 | Licenza documentata nel manifest | [FILE] `qa.json` Q3 | sì |
| P4 | Piano di test completo (domanda, offerta, canale primario, soglia di stop, criterio di successo) | [FILE] `qa.json` Q8; `selezione.json` → `piano_test` | sì |
| P5 | Scheda negozio in **bozza**, link con scadenza | [FILE] `shopify.json` → `stato_scheda: bozza`, `scheda.consegna.scadenza_ore` | sì |

## 3. Tracciamento e ordini
| # | Criterio | Prova richiesta | Bloccante |
|---|---|---|---|
| T1 | Eventi di tracciamento dichiarati (view_item … purchase, refund) | [FILE] `shopify.json` → `eventi_tracciamento` (oggi è una lista statica: controllo [ISP]) | no in collaudo |
| T2 | Ordini deduplicati per `order_id`; webhook duplicato scartato e contato | [FILE] `orders.json` → `duplicati_scartati`; [TEST] `test_ordine_duplicato_in_distribuzione_non_raddoppia_commissione` | sì |
| T3 | Ordine di prova riconciliato una volta ed escluso dai KPI | [FILE] `ordine_prova.json` → `riconciliato`; `misurazione.json` → `ordini` = ordini non di prova | sì |
| T4 | Ricavo contato una volta (canale primario creator > ads > organico); costi di tutti i canali conservati; ordini "assistiti" | [FILE] `misurazione.json` → `controllo_doppio_conteggio_ok: true`, `per_canale` | sì |
| T5 | Rimborsi: ordine inesistente gestito senza crash; rimborso doppio ignorato | [TEST] `test_rimborso_ordine_inesistente_non_manda_in_crash_il_run`, `test_rimborso_doppio_non_raddoppia_storno` | sì |

## 4. Contabilità
| # | Criterio | Prova richiesta | Bloccante |
|---|---|---|---|
| C1 | Netto = lordo dopo sconto, IVA del **paese del cliente** scorporata (half-up al centesimo) | [TEST] `test_roas_e_margine_del_run_seguono_la_formula`, `test_esempio_strategia_unit_economics` | sì |
| C2 | Commissione di pagamento su tutti gli ordini pagati, **non** restituita sui rimborsi | [FILE] `misurazione.json` → `fee_pagamento_cents` = somma su tutti gli ordini; [TEST] `test_rimborso_dopo_clawback_commissione_e_fee_restano` | sì |
| C3 | Commissione creator = 30% del netto IVA esclusa dopo sconto; stornata solo con rimborso entro 30 giorni; dopo la finestra resta | [FILE] `ledger.json` → busta `<id>/creator-…-commissioni`, `consumi[].stornato`; [TEST] clawback | sì |
| C4 | ROAS sul margine = (R − C_pag) / (Ads + commissioni + compensi fissi); indefinito se acquisizione = 0 (D-008) | [TEST] `test_roas_e_margine_del_run_seguono_la_formula` | sì |
| C5 | Margine = R − C_pag − acquisizione − piattaforma − AI − riserva − test falliti | idem C4 | sì |
| C6 | Regole stop/ripeti/scala come STRATEGIA.md §5 (minimo 10 ordini, D-007) | [TEST] `test_regole_decisione_strategia_par5` | sì |
| C7 | Numeri del registro = numeri della misurazione (stesso prefisso di run) | [CMD] `python3 -m studio ledger --run-id $ID` vs `misurazione.json` → `costi_cents` | sì |

## 5. Limiti di spesa
| # | Criterio | Prova richiesta | Bloccante |
|---|---|---|---|
| L1 | Consumato + impegnato ≤ tetto (500 €), anche con registro condiviso | [CMD] `python3 -m studio ledger --run-id $ID`; [FILE] `qa.json` Q5; [TEST] `test_registro_condiviso_due_istanze_non_superano_l_allocazione` | sì |
| L2 | Ogni categoria ≤ allocazione; nessuna compensazione tra categorie | [TEST] `test_allocazione_non_aggirabile_con_buste_piccole`, `test_tetto_non_superabile_sommando_le_categorie` | sì |
| L3 | Ogni azione a pagamento ha una busta riservata **prima**, con costo massimo noto | [CMD] in `external_calls.jsonl` ogni `a_pagamento: true` ha `busta` presente in `ledger.json`; [TEST] `test_simulato_nessuna_azione_reale_e_azioni_a_pagamento_con_busta` | sì |
| L4 | Vie indirette chiuse: storno + nuovo consumo, ID ripetuti con importi diversi, buste chiuse | [TEST] classe `TestQARegistro` | sì |
| L5 | Limiti contrattuali creator (`config/commissioni.json`: compenso fisso per creator, tetto commissioni) applicati | [TEST] `test_compenso_fisso_oltre_il_massimo_per_creator_bloccato`, `test_tetto_commissioni_sospende_il_codice` | sì |
| L6 | La Selezione verifica la disponibilità di **tutte** le categorie che il test consumerà (incluso AI delle fasi restanti) | [TEST] `test_categoria_ai_esaurita_scoperta_prima_di_spendere` | sì |
| L7 | A fine test nessuna busta aperta; codici creator sospesi; tentativi bloccati registrati | [FILE] `ledger.json` → `buste[].stato`, `bloccati`; `decisions.jsonl` → `chiusura_test` | sì |

## 6. Azioni esterne
| # | Criterio | Prova richiesta | Bloccante |
|---|---|---|---|
| E1 | In simulazione ogni chiamata è `simulato`; nessun `contatto_reale` | [FILE] `$RUN/external_calls.jsonl`; `qa.json` Q7 | sì |
| E2 | Modalità live: blocco alla prima azione, nessun consumo, chiamata registrata come `bloccato` (anche con `STUDIO_LIVE=1`) | [TEST] `test_live_blocca_senza_consumi_anche_con_studio_live`, `test_live_ripreso_resta_bloccato_e_non_spende` | sì |
| E3 | Nessuna pubblicazione, campagna reale, email, account o acquisto | [ISP] `grep -rn "requests\|urllib\|smtplib\|http.client\|socket" studio/` → nessun uso; scheda in bozza | sì |
| E4 | Azioni del titolare raccolte nel pacchetto unico, senza credenziali | [FILE] `$RUN/AZIONI_TITOLARE.md`, `AZIONI_TITOLARE.md` | sì |

## 7. Segreti e dati personali
| # | Criterio | Prova richiesta | Bloccante |
|---|---|---|---|
| S1 | Nessun segreto in **tutti** i file del run (incluse le sottocartelle `artifacts/`) | [FILE] `qa.json` Q6; [TEST] `TestQASegreti`; [CMD] `grep -rIE 'shpat_\|sk_live_\|ghp_\|AKIA' $RUN` → vuoto | sì |
| S2 | Nessuna credenziale o dato personale nei file versionati | [CMD] `git ls-files \| xargs grep -nIE '<pattern token, carte, IBAN, email, telefoni>'` → vuoto; [TEST] `test_nessuna_credenziale_o_dato_personale_versionato` | sì |
| S3 | `runs/`, `.env*`, `secrets/`, `settings.local.json` non versionati | [CMD] `git ls-files runs` → solo `runs/.gitkeep`; [TEST] `test_runs_e_segreti_non_versionati` | sì |
| S4 | Nessun dato personale nei log (`external_calls.jsonl`, `decisions.jsonl`): solo `order_id`, paese, hash; scope Shopify senza `read_customers` (D-012) | [FILE] `studio/adapters/mock.py` `SCOPE_RICHIESTI`; [CMD] grep di email/telefono nei log del run | sì |

## 8. Coerenza documenti ↔ codice
| # | Criterio | Prova richiesta | Bloccante |
|---|---|---|---|
| D1 | Formule e regole di STRATEGIA.md e WORKFLOW.md coincidono con `studio/economics.py`, `studio/phases.py` | [TEST] classe `TestQACoerenza` | sì |
| D2 | Ogni parametro di `config/*.json` è letto dal codice o dichiarato informativo | [CMD] `grep -rn <chiave> studio/` per ogni chiave | no (importante) |
| D3 | Riferimenti incrociati a DECISIONI.md corretti | [ISP] | no |
