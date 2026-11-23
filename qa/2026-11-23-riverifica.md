# Verdetto QA: riverifica dopo D-013

Data: 2026-11-23 · Verificatore: qa-indipendente (non ha scritto né corretto il codice) · Oggetto: le correzioni del Team Lead (D-013) ai 13 difetti di `qa/2026-11-23-collaudo-sistema.md`, più un collaudo di concorrenza reale.
Checklist: `docs/qa-checklist.md`. Test: `tests/test_qa_sistema.py`, ora con 47 test. Sono stati tolti i 13 `expectedFailure` corretti e aggiunta la classe `TestQAConcorrenza` (5 test, 4 dei quali `expectedFailure` per difetti nuovi).
Nessuna azione esterna e nessuna rete: si usano processi locali, directory temporanee e adattatori simulati.

## VERDETTO: **BLOCCATO**

I 13 difetti del primo collaudo sono **corretti**, e lo ho verificato in modo indipendente. Anche il difetto bloccante B-1 è risolto: con processi reali in parallelo il tetto e le allocazioni reggono e nessuna riserva viene persa nei casi osservati.
Il nuovo collaudo di concorrenza mostra però **4 difetti nuovi, tutti importanti**. Per tre di essi la causa è il registro condiviso, che ora vede le scritture degli altri processi. Il controllo bloccante L6 della checklist fallisce: "un test non finanziabile si ferma alla Selezione, prima di spendere" (D-006). Fallisce anche L7: "a fine test nessuna busta aperta". Il tetto di 500 € **non** viene superato in nessuna delle prove.

**Come si supera il blocco:**
- **(a)** Si correggono N-1…N-4: i test `expectedFailure` di `TestQAConcorrenza` devono diventare test normali e verdi.
- **(b)** In alternativa, il Team Lead registra in `DECISIONI.md` che il registro condiviso si usa **solo in sequenza**, e la CLI lo fa rispettare. Con un lock per run sul registro restano fuori campo N-1, N-2 e N-3; N-4 va corretto comunque.

## Controlli (esito e prova)

| # | Controllo | Esito | Prova |
|---|---|---|---|
| B1 | Suite completa | OK (4 difetti noti) | `python3 -m unittest discover -s tests` → `Ran 75 tests … OK (expected failures=4)`. Prima della riverifica dava `FAILED (unexpected successes=13)` |
| B2 | Collaudo end-to-end | OK | `python3 -m studio collaudo --runs-dir /tmp/claude-qa-collaudo-2` → `11/11 casi superati` |
| R1 | I 13 difetti del primo collaudo | OK | sono 13 test normali, tutti verdi: `test_registro_condiviso_due_istanze_non_superano_l_allocazione`, `test_q6_blocca_segreto_negli_artifacts`, `test_categoria_ai_esaurita_scoperta_prima_di_spendere`, `test_rimborso_ordine_inesistente_non_manda_in_crash_il_run`, `test_compenso_fisso_oltre_il_massimo_per_creator_bloccato`, `test_paese_senza_aliquota_iva_non_manda_in_crash_il_run`, `test_consumo_ripetuto_con_importo_diverso_e_segnalato`, `test_importo_booleano_rifiutato_nel_consumo`, `test_spesa_singola_bloccata_non_lascia_impegni_aperti`, `test_roas_indefinito_non_compare_come_numero_nei_motivi`, `test_q6_riconosce_altri_formati_di_token`, `test_flag_fee_rimborsata_letto_dal_codice`, `test_duplicato_con_payload_diverso_e_tracciato_come_conflitto` |
| R2 | Le asserzioni dei test non sono state indebolite | OK | Ho confrontato il file con la mia copia di lavoro. Fuori dal QA è cambiato solo il commento `# QA-DIFETTO` aggiunto ai 13 decoratori, che ho rimosso. Nessuna asserzione era modificata |
| R3 | Falso positivo del test sui file versionati | OK, test reso robusto | Ora il test salta l'intero blocco `SEGRETI = re.compile(...)` di `studio/phases.py`, anche su più righe, e non dipende più dall'offuscamento `github_p[a]t_` |
| L1 | Tetto e allocazioni con processi reali in parallelo | OK | `test_processi_paralleli_stesso_registro_entro_tetto_e_allocazioni`: 2 giri × 3 processi `python3 -m studio simulate` sullo stesso `--registro`. Risultato: consumato + impegnato ≤ 50000; ogni categoria ≤ allocazione; ogni busta citata in `external_calls.jsonl` presente nel registro; tutte le buste AI di ogni tentativo presenti; al più una busta commissioni con consumi. Prova manuale ripetuta 5 volte: `22702 0 True` (consumato, impegnato, entro il tetto) |
| L6 | Il test non finanziabile si ferma alla Selezione | **KO** | N-1, N-4 |
| L7 | Nessuna busta aperta né buste altrui chiuse | **KO** | N-2, N-4 |
| L1' | Nessun aggiornamento perso alla creazione del registro | **KO** | N-3 |
| S1 | Q6 ricorsivo, più formati | OK | `test_q6_*` verdi; `grep -rIlE 'shpat_\|sk_live_\|ghp_\|AKIA[0-9A-Z]{16}' /tmp/claude-qa-collaudo-2` → nessun file |
| S2 | Nessuna credenziale o dato personale nei file versionati | OK | `test_nessuna_credenziale_o_dato_personale_versionato` |
| E2 | Modalità live | OK | `test_live_*` verdi |

## Difetti nuovi

### Bloccanti
Nessuno. In nessuna prova il tetto di 500 € viene superato.

### Importanti
**N-1 La Selezione verifica il budget ma non lo prenota.** Riferimenti: `studio/phases.py:153-180` (`g_selezione`) e `studio/phases.py:283`. Due test che passano la Selezione in parallelo vedono entrambi le categorie libere. Il secondo si blocca solo in Shopify o in Distribuzione, dopo aver già speso piattaforma e AI. Contrario a D-006.
- Riproduzione deterministica: `test_due_test_interfogliati_il_non_finanziabile_si_ferma_alla_selezione` → `B bloccato in distribuzione dopo aver speso 4560 cent`.
- Con 3 processi reali (5 giri su 5): un run `completato`, uno `bloccato` in `shopify` ("allocazione della categoria superata", 7,20 € spesi), uno `bloccato` in `distribuzione` ("canale primario non attivabile", 45,60 € spesi). In sequenza il collaudo li ferma tutti alla Selezione.

**N-2 L'annullamento dell'attivazione chiude buste di altri run.** Riferimenti: `studio/phases.py:283` e `:310`. Quando la riserva di un canale fallisce, il codice chiude `set(led.data["buste"]) - n_buste`. Dopo D-013 `_tx` rilegge il registro, quindi quell'insieme contiene anche le buste create nel frattempo da un altro processo. L'impegno dell'altro run viene liberato, i suoi consumi successivi falliscono con "consumo su busta chiusa" e la sua campagna o il suo codice si fermano.
- Riproduzione: `test_rollback_atomico_non_chiude_buste_di_altri_run`. Un altro run riserva `ALTRO/creator-CR-X-commissioni` subito prima della riserva di B; B si blocca e chiude la busta altrui (`'chiusa' != 'aperta'`).
- Correzione suggerita: annullare solo gli ID riservati da questo run per questo canale.

**N-3 La creazione del registro non è sotto lock.** Riferimento: `studio/ledger.py:46-62`. Il controllo `os.path.exists` e il primo `_save()` stanno fuori da `_tx`. Se due processi partono insieme su un `--registro` nuovo, il secondo può scrivere un registro vuoto sopra le riserve già fatte dal primo. Il primo run trova poi "consumo senza riserva preventiva", mentre le azioni esterne già avviate restano senza busta.
- Riproduzione: `test_creazione_concorrente_del_registro_non_perde_riserve`. Simula l'interleaving con `mock.patch` su `os.path.exists`; risultato `'A/ads' not found in {}`. La finestra temporale è stretta, ma corrisponde esattamente all'avvio in parallelo.

**N-4 La previsione AI della Selezione non conta le fasi ripetute dopo un blocco.** Riferimento: `studio/phases.py:142-147`. La stima copre le 7 fasi restanti e i 2 ritorni QA, ma non le ripetizioni dopo `bloccato_titolare` o `bloccato` (nuovo tentativo, quindi nuova busta AI). Con costo AI effettivo pari al massimo, 24 € di AI già consumati, un ritorno QA e Shopify in attesa del titolare, il test supera la Selezione, spende e si blocca alla Decisione. La busta commissioni resta aperta e il codice creator resta attivo: è lo stesso esito di I-2, raggiunto per un'altra via.
- Riproduzione: `test_previsione_ai_regge_ritorno_qa_e_ripresa_dopo_blocco` → `stato bloccato in fase decisione, buste aperte ['r/creator-CR-SIM-1-commissioni']`.

### Minori e osservazioni
- **O-1** (`studio/phases.py:350-352`). `DatoMancante` per un paese senza IVA blocca la Distribuzione a metà. Le buste Ads e commissioni del run restano aperte, cioè impegnate ma entro il tetto, finché qualcuno non interviene. È il blocco motivato richiesto da I-5, quindi lo registro come osservazione e non come difetto. Va valutato se una sola aliquota mancante debba fermare tutto il test o solo quell'ordine.
- **O-2** (`studio/phases.py:161-166`). `tetto_commissioni_per_test_cents` viene confrontato con ogni singolo creator, non con la somma del test. Oggi non ha effetto, perché l'allocazione `commissione` (6000) coincide con il tetto e la verifica per categoria somma i creator.
- **O-3, processo.** D-013 ha modificato file di altri responsabili: `studio/ledger.py` e `STRATEGIA.md` (strategia-finanza), `studio/orders.py` (shopify-operazioni). Ha anche aggiunto commenti a `tests/test_qa_sistema.py`, che è del QA. CLAUDE.md, regola 4, chiede di proporre le modifiche al responsabile. D-013 lo motiva con D-004: lo segnalo perché resti tracciato, non è un blocco.

## Note
- Non ho aggiornato `team/queue.json`, perché è fuori dal mio perimetro di scrittura in questo compito. Il Team Lead deve registrare l'esito BLOCCATO e assegnare le correzioni: N-1, N-2 e N-4 al team-lead (phases); N-3 a strategia-finanza (ledger).
- Escalation: Team Lead. Se si procede nonostante il blocco, la decisione va registrata in `DECISIONI.md` con la motivazione (opzione (b) sopra).
