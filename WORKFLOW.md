# WORKFLOW — dalla strategia alla decisione

Responsabile: team-lead. Motore: `studio/workflow.py` (motore), `studio/phases.py` (fasi e controlli).

```
Strategia → Ricerca → Selezione → Prodotto → QA → Shopify → Ordine di prova e download
          → Distribuzione → Misurazione → Decisione
```

## Principi
- **Una fase alla volta, nell'ordine.** `esegui_fase` rifiuta una fase se le precedenti non sono approvate.
- **Output obbligatori + controllo di sblocco.** Una fase passa solo se produce tutti i campi richiesti e il controllo ritorna `ok`. Gli output finiscono in `runs/<id>/artifacts/<fase>.json`.
- **Stato persistente e riprendibile.** Ogni scrittura è atomica (file temporaneo + `os.replace` + `fsync`). Prima di eseguire una fase il motore salva `in_esecuzione = {fase, tentativo}`. Se il processo muore, `resume` riparte da quella fase con lo stesso tentativo.
- **Idempotenza.** Riserve e consumi del registro hanno ID stabili (`<run_id>/<busta>`, consumo per ordine o per giorno), gli ordini si deduplicano per `order_id` e i rimborsi doppi si ignorano. Ripetere una fase non produce doppie spese né ordini doppi.
- **Traccia delle decisioni.** `runs/<id>/decisions.jsonl` (append-only) registra ogni approvazione, blocco, ritorno, spesa bloccata, concessione del titolare ed esito.
- **Costo AI per fase.** Prima di ogni fase si riserva il costo AI massimo (`costi_ai_per_fase_cents.max`) e poi si consuma l'effettivo.

## Fasi

| # | Fase | Responsabile | Output obbligatori | Controllo che sblocca la fase successiva |
|---|---|---|---|---|
| 1 | Strategia | strategia-finanza | obiettivo di lungo periodo, tetto, allocazione, regole di decisione | tetto = tetto del registro; somma delle allocazioni ≤ tetto |
| 2 | Ricerca | ricerca-mercato | `opportunita` (schede complete), `scartate` (con errori) | almeno 1 scheda completa; fonti tipizzate `osservata`/`ipotesi` (osservata con url e data); in simulazione tutte `sintetico: true` |
| 3 | Selezione | team-lead | classifica, `selezionata`, `piano_test` | piano con domanda, offerta, canale primario, soglia di stop, criterio di successo; canale primario tra i canali; budget del piano ≤ residuo e ≤ disponibilità di **ogni** categoria; costo di piattaforma noto. Nessuna opportunità idonea (punteggio ≥ 60 e ≥ 2 fonti osservate) ⇒ **test fermato** |
| 4 | Prodotto | sviluppo-prodotto | `manifest` (id, versione, lingua, licenza, files con sha256 e promesse coperte), spec, prezzo | manifest strutturalmente completo |
| 5 | QA | qa-indipendente | `verdetto`, `controlli` con la prova di ogni controllo | Q1–Q8 tutti superati (promesse coperte, checksum, licenza, ≥2 fonti osservate, registro entro il tetto, nessun segreto nei file, nessuna azione esterna reale, piano completo). **BLOCCATO** ⇒ ritorno a Prodotto; oltre `qa.max_tentativi_prodotto` ⇒ test fermato |
| 6 | Shopify | shopify-operazioni | scheda (in **bozza**), stato, eventi di tracciamento | scheda non pubblicata; link di download con scadenza. Senza accesso ⇒ **bloccato_titolare** con voce nel pacchetto unico |
| 7 | Ordine di prova e download | shopify-operazioni | order_id, download_ok, duplicato_scartato, riconciliato | download verificato contro i checksum; webhook duplicato scartato; ordine di prova riconciliato una volta, escluso dai KPI |
| 8 | Distribuzione | acquisizione (con creator-partnership) | canali attivati, spese bloccate, ordini | canale primario attivato **per primo** e **in modo atomico** (se fallisce, nessun altro canale parte e le riserve si liberano); ogni azione a pagamento ha una busta; nessuna azione esterna reale |
| 9 | Misurazione | strategia-finanza | metriche (totali e per canale), registro | ricavi per canale = ricavi totali (nessun doppio conteggio); consumato + impegnato ≤ tetto; ordini riconciliati |
| 10 | Decisione | team-lead | esito `stop`/`ripeti`/`scala`, motivi | esito valido; chiusura del test: buste di canale chiuse, codici creator sospesi. `scala` ⇒ azione del titolare (nuovo tetto) |

Nota sulla Misurazione: è una fotografia presa all'inizio della fase. Il costo AI delle fasi Misurazione e Decisione (2 × costo per fase) compare nel registro ma non nel margine. Lo scarto è noto e piccolo.

## Stati di un run
`nuovo` → `in_corso` → `completato` | `fermato` (stop motivato) | `bloccato` (serve un intervento del team) | `bloccato_titolare` (serve un'azione del titolare).

## Regole di distribuzione (dettaglio)
- **Creator.** Compenso fisso riservato e consumato all'attivazione. Le commissioni stanno in una busta con il tetto contrattuale: ogni ordine con codice consuma il 30% del netto IVA esclusa. Oltre il tetto il codice viene sospeso. Un rimborso entro la finestra di clawback (30 giorni) storna la commissione.
- **Ads.** Busta della campagna e massimo giornaliero; una spesa giornaliera oltre il massimo viene ridotta e registrata. Se la busta si esaurisce la campagna va in pausa. A fine distribuzione la busta si chiude e il non speso si libera.
- **Doppia attribuzione.** Il ricavo va al canale primario (creator > ads > organico), contato una volta sola. La commissione creator e la spesa Ads restano entrambe a costo. Ogni canale toccato conta l'ordine come "assistito".
- **Spese extra.** Ogni richiesta passa dal registro: costo sconosciuto, residuo o allocazione insufficienti ⇒ bloccata e registrata, il test prosegue nei limiti.

## Comandi
```bash
python3 -m studio simulate --scenario completo [--run-id ID] [--registro PATH] [--modalita live]
python3 -m studio resume --run-id ID [--concedi shopify]
python3 -m studio status|ledger|decisions --run-id ID
python3 -m studio collaudo [--runs-dir DIR]
```
Codici d'uscita: `0` run concluso, bloccato o in attesa; `75` sessione interrotta (riprendere con `resume`).

## Coda del team
`team/queue.json` contiene i compiti reali degli agenti; `runs/<id>/queue.json` contiene i compiti generati dal motore per fase e tentativo. Un compito passa a `in_corso`/`fatto` solo con le dipendenze `fatto`. CLI: `python3 -m studio queue list|set|add`.
