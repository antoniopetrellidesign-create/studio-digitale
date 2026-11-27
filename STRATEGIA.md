# STRATEGIA — obiettivi, unit economics, budget e regole di decisione

Responsabile: strategia-finanza. Compito T-002. Fonte unica dei numeri: `config/policy.json` (non modificata qui; le proposte sono in fondo).
Convenzioni: importi in euro nel testo, in centesimi interi nel codice. **[P]** = valore da policy. **[I]** = ipotesi da verificare. **[O]** = dato osservato (con fonte). In questa fase non esiste alcun dato **[O]** di mercato o di vendita: ogni cifra sotto è **[P]**, **[I]** o aritmetica pura. Gli esempi numerici sono illustrazioni di formule, non previsioni e non dati di mercato.

---

## 1. Traguardo di lungo periodo e tappe

**Traguardo [P]**: 30.000 €/settimana di utile operativo (3.000.000 cent) da un portafoglio multilingua e multi-nicchia. È un traguardo strategico, non una previsione: nessuna tappa sotto garantisce che sia raggiungibile.

**Formula di scomposizione** (settimanale, valori a regime):

```
U = Σ_p Σ_l ( O_pl × m_pl ) − F
```
- p = prodotto, l = lingua/mercato, O_pl = ordini netti (non rimborsati) a settimana, m_pl = margine di contribuzione unitario per ordine (definito al §2), F = costi di struttura del portafoglio non attribuibili a un singolo ordine.
- Con N celle (prodotto×lingua) attive e valori medi: `U ≈ N × Ō × m̄ − F`, quindi `N × Ō = (30.000 + F) / m̄`.

Aritmetica pura (F = 0, nessun dato di mercato): ordini/settimana totali necessari = 30.000 / m̄.

| m̄ per ordine | ordini/sett. totali | con N=10 celle: Ō per cella | con N=30 celle |
|---|---|---|---|
| 10 € | 3.000 | 300 | 100 |
| 20 € | 1.500 | 150 | 50 |
| 30 € | 1.000 | 100 | 33 |

I valori di m̄ sono scenari di calcolo, non stime. Quali Ō e m̄ siano realistici lo diranno solo i test; fino ad allora il traguardo resta una direzione.

**Tappe verificabili** (ogni tappa si supera solo con dati misurati; soglie numeriche aggiuntive si fissano dopo T1 con dati reali, non prima):

| Tappa | Condizione verificabile | Evidenza richiesta |
|---|---|---|
| T0 Collaudo | Pipeline simulata completa, registro spese e regole decisionali testati | `python3 -m studio collaudo` e test verdi; nessuna spesa reale |
| T1 Primo margine positivo | 1 prodotto, 1 lingua, ≥10 ordini nel tetto di 500 €, margine di contribuzione > 0 | Report di misurazione + registro spese; regola "scala" soddisfatta (§5) |
| T2 Ripetibilità | Lo stesso prodotto ripete T1 in un secondo ciclo (budget approvato dal titolare se >500 €) | Due cicli con ROAS sul margine ≥ 1,5 e rimborsi ≤ 10% |
| T3 Portafoglio mono-lingua | N prodotti/nicchie nella stessa lingua, ognuno con margine > 0 | N da fissare dopo T2; margine aggregato di portafoglio > 0 inclusi costi dei test falliti |
| T4 Seconda lingua | Almeno un prodotto di T3 replicato in una nuova lingua con margine > 0 (IVA/OSS del nuovo paese gestita) | Margine per cella, tasso rimborso per lingua |
| T5 Scala di portafoglio | Crescita di N×Ō a margine unitario non peggiorativo | Utile settimanale misurato su ≥4 settimane consecutive |
| T6 Traguardo | U ≥ 30.000 €/settimana | Utile operativo misurato, non stimato |

Ogni tappa oltre il tetto di 500 € richiede approvazione del titolare tramite Team Lead.

---

## 2. Unit economics di un prodotto digitale

Notazione per un ordine: `P` prezzo di listino IVA inclusa, `v` aliquota IVA del **paese del cliente** (OSS UE) **[I: aliquota da verificare per paese e data]**, `d` sconto.

Ordine di calcolo (ogni riga è un campo del modello economico):

1. **Prezzo IVA inclusa** `P` (dopo eventuale sconto: `P_pagato = P × (1 − d)` se lo sconto è percentuale sul prezzo; il netto resta coerente perché lo sconto si applica prima dello scorporo).
2. **Scorporo IVA**: `N = P_pagato / (1 + v)`. L'IVA incassata non è ricavo: si versa tramite OSS al paese del cliente. Aliquota del paese del cliente, non del venditore.
3. **Sconti**: già in `N` (net-of-discount). Si tracciano a parte per calcolare lo sconto medio per canale (§6). Un codice creator o promozionale riduce `N` e quindi anche la base della commissione creator.
4. **Commissione di pagamento [I, da verificare]**: `C_pag = 2,9% × P_pagato + 0,30 €` (calcolata sull'importo realmente addebitato, IVA inclusa). **Non rimborsata in caso di refund [P]**: su un ordine rimborsato la perdita è `C_pag`.
5. **Rimborsi**: se rimborsato, `N` va a 0 (rimborso integrale, assunzione di default), `C_pag` resta costo, Ads già spesa resta costo.
6. **Commissione creator [P]**: `C_cr = 30% × N` (netto IVA esclusa dopo lo sconto). Regola di clawback: se il rimborso cade **entro 30 giorni** dall'ordine la commissione è stornata (costo 0); se il rimborso cade dopo, la commissione già pagata non si recupera (costo pieno e ricavo 0). La commissione è **pagata dopo la finestra**: finché non decorrono i 30 giorni è un impegno maturato, non una spesa pagata, e il margine dell'ordine è **provvisorio**.
7. **Costo Ads** `A`: spesa di acquisizione a pagamento attribuita all'ordine (spesa del test / ordini attribuiti). I clic Ads che non convertono sono comunque costo del test.
8. **Compensi fissi** `F_c`: compensi non legati al singolo ordine (es. creator a forfait, freelance) ripartiti sugli ordini del test.
9. **Piattaforma** `Pl`: abbonamenti/commissioni di negozio e servizi, ripartiti sugli ordini.
10. **Costi AI incrementali** `AI`: costo di generazione/assistenza imputabile al prodotto (non il costo AI già sostenuto per l'infrastruttura del team).
11. **Quota dei costi dei test falliti** `Q`: costo totale dei test conclusi con "stop" nel periodo, ripartito sugli ordini dei prodotti vincenti (il successo deve ripagare i fallimenti; vedi §6).

### Definizioni

```
Ricavi netti            R = Σ N su ordini non rimborsati (IVA esclusa, dopo sconti)
Margine di contribuzione  M = R − C_pag(tutti gli ordini, rimborsati inclusi)
                              − C_cr(non stornate) − A − F_c − Pl − AI − Q
ROAS sul margine = (R − C_pag) / (A + C_cr + F_c)
Tasso rimborso   = ordini rimborsati / ordini totali      [definizione proposta, §8]
```
Interpretazione: ROAS sul margine = 1 significa che ricavi netti meno costo di pagamento coprono esattamente il costo di acquisizione (Ads + creator + compensi fissi); sotto 1 ogni euro di acquisizione rende meno di un euro. Il ROAS **non** include piattaforma, AI e test falliti: è un indicatore di efficienza del canale; il segno del margine M include tutto.

### Esempio di calcolo (illustrazione, non dato)
`P = 24,40 €`, `v = 22%`, nessuno sconto, `A = 8,00 €`, creator, nessun compenso fisso/piattaforma/AI/Q.
- `N = 24,40 / 1,22 = 20,00 €`; `C_pag = 0,029×24,40 + 0,30 = 1,01 €`; `C_cr = 6,00 €`.
- `M = 20,00 − 1,01 − 6,00 − 8,00 = 4,99 €` per ordine; ROAS = (20,00 − 1,01)/(8,00 + 6,00) = **1,36** → sotto 1,5: con M>0 ma ROAS <1,5 la regola dà "ripeti", non "scala".
- Stesso ordine rimborsato entro 30 giorni: ricavo 0, `C_pag` 1,01 perso, commissione stornata, Ads 8,00 persa → perdita 9,01 €.
- Rimborsato dopo 30 giorni: perdita 15,01 € (commissione già pagata).
Un rimborso costa quindi più di un ordine non venduto: per questo soglie dure sui rimborsi.

Margine di contribuzione = ciò che resta di un ordine dopo tutti i costi variabili e quelli attribuibili al test; sopra zero il prodotto contribuisce a coprire F del portafoglio.

---

## 3. Allocazione del tetto di 500 € **[P]**

| Categoria | € | % | Motivazione |
|---|---|---|---|
| ads | 200 | 40% | Unico costo che genera domanda misurabile; serve ≥10 ordini per giudicare. Con 200 € e 10 ordini, il costo medio di acquisizione deve restare ≲20 € per non esaurire il budget prima del giudizio **[aritmetica]** |
| piattaforma | 80 | 16% | Negozio, dominio, strumenti di consegna e **tutti gli account e strumenti** (email dedicata, repository, hosting/automazione, Shopify, marketplace, strumenti creator/assistenza/analisi, social, integrazioni API non-AI): costo quasi fisso, da limitare al minimo funzionale. Le regole sono al §3-bis |
| ai | 60 | 12% | Generazione prodotto, traduzioni, assistenza clienti; limite per evitare spese elastiche e senza ritorno |
| compenso_fisso | 60 | 12% | Compensi non legati alle vendite (es. revisione, creator a forfait): tenuto basso perché è rischio senza ricavo |
| commissione | 60 | 12% | Busta per commissioni creator: al 30% sul netto copre ≈200 € di ricavi netti (60/0,30) **[aritmetica]** |
| riserva | 40 | 8% | Imprevisti (rimborsi non coperti, ripetizione di consegne, errori); sbloccabile solo dal Team Lead con motivazione |
| **Totale** | **500** | 100% | = tetto **[P]** |

**Regole di spesa** (si applicano a ogni euro, nessuna eccezione):
1. **Riserva prima**: ogni spesa è registrata nel registro (`studio/ledger.py`) come riserva con costo massimo noto **prima** dell'azione.
2. **Blocco** se il costo massimo è sconosciuto, o se il residuo totale o l'allocazione della categoria non bastano. Nessuna compensazione tra categorie senza decisione registrata.
3. **Commissioni creator**: impegnate in una **busta con tetto contrattuale** (≤ 60 €). Il tetto è scritto nell'accordo con il creator; quando le commissioni maturate raggiungono il tetto, il **codice creator viene sospeso**. Una commissione maturata ma non ancora pagata (finestra 30 giorni) consuma comunque il tetto; se stornata per rimborso, il tetto si libera.
4. **Ads**: ogni test ha una soglia di stop in € (§4) ≤ residuo ads. La spesa Ads è prenotata con tetto giornaliero e totale prima dell'avvio della campagna.
5. **Un solo test per volta** (`max_opportunita_per_test = 1` **[P]**) finché il residuo non consente due.
6. Superare 500 € richiede approvazione del titolare. Nessun agente ha accesso a strumenti di pagamento.
7. **Categorie invariate** (da `config/policy.json`): ai, piattaforma, ads, compenso_fisso, commissione, riserva. Account e strumenti rientrano in **piattaforma**; le API di modelli AI restano in **ai**; i compensi creator in commissione/compenso_fisso. Il tetto di 500 € è **unico e condiviso** tra prodotti, strumenti, API, marketplace, Ads e creator.

---

## 3-bis. Costi di account e strumenti

Mandato del titolare aggiornato: il team può creare gli account strettamente necessari (email dedicata, repository privato, hosting/automazione, Shopify e marketplace selezionati, strumenti creator/assistenza/analisi, social per prodotti validati, integrazioni API), sempre rispettando le dipendenze delle fasi (nessun account prima della fase che lo richiede; social solo per prodotti validati). La creazione dell'account non autorizza alcuna spesa: vale quanto sotto. Carte, OTP e token restano al titolare (azioni raggruppate in `AZIONI_TITOLARE.md`).

**A. Prima di assumere qualsiasi costo (tutte le condizioni, altrimenti blocco)**
1. **Verifica del prezzo effettivo**: prezzo di listino, imposte (IVA/reverse charge), commissioni di transazione, costi per utente/uso e **rinnovi** (periodicità, rinnovo automatico, prezzo dopo l'offerta). Ogni cifra è registrata con **fonte (URL o documento) e data**; senza fonte e data resta **[I]** e il costo è considerato sconosciuto.
2. **Impegno massimo riservato nel registro comune** (`studio/ledger.py`) in categoria `piattaforma` (o `ai`), con importo comprensivo di imposte e commissioni e coprendo l'intero periodo impegnato, rinnovi compresi.
3. **Controllo del residuo**: residuo totale e residuo della categoria ≥ impegno. Altrimenti blocco ed escalation al Team Lead; nessuna compensazione tra categorie senza decisione registrata.
4. **Limiti di spesa nel servizio** quando disponibili (tetto di spesa/uso, avvisi di soglia, nessun overage automatico); se il servizio non li offre lo si annota e si preferisce un piano a importo fisso.
5. **Chiusura dei rinnovi pianificata**: per ogni abbonamento si registra data di rinnovo, data limite di disdetta e azione prevista (disdire/confermare); il rinnovo automatico va disattivato se possibile. Un abbonamento senza data di chiusura non è ammesso.

**B. Prove gratuite**
- Si registrano nel registro con **scadenza, condizioni** (carta richiesta, prezzo dopo la prova, rinnovo automatico, limiti) e fonte/data.
- Prima della scadenza (promemoria ≥ 3 giorni prima) si decide **disdire o confermare**; la decisione è annotata.
- Il **costo del rinnovo** va riservato **prima** della conferma (e prima dell'avvio se il rinnovo è automatico e non disattivabile: in tal caso la riserva è obbligatoria all'inizio della prova). Prova senza riserva possibile ⇒ non si avvia.

**C. Gli incassi non aumentano il budget autorizzato**
Ricavi, commissioni recuperate e rimborsi ricevuti non incrementano il tetto di 500 €, né il residuo di alcuna categoria. Il tetto si supera solo con approvazione del titolare (tramite Team Lead). Gli incassi entrano nel margine (§2), non nel budget.

**D. Commissioni dei marketplace: costo variabile per ordine**
- La commissione del marketplace (percentuale, quota fissa, eventuali costi di pagamento/pubblicazione/inserzione e imposte sulla commissione) è un **costo variabile per ordine**, **[I]** finché non verificata con fonte e data. Si tratta come la commissione di pagamento: va **nel margine di contribuzione** e **non** si rimborsa se non lo prevedono le condizioni del marketplace (da verificare per ogni marketplace).
- Se il marketplace trattiene la commissione dal pagamento, il costo non passa dal registro come spesa autonoma ma **riduce l'incasso**: va comunque stimato prima dell'apertura e incluso nel confronto, e non crea alcun diritto a spendere di più.
- **Confronto tra canali di vendita** (sito/Shopify vs marketplace), per lo stesso prodotto e prezzo, su base per ordine:
  - Sito/Shopify: `M_sito = N − C_pag − C_cr − A − Pl_ord − AI − Q`, con costi di piattaforma ripartiti sugli ordini.
  - Marketplace: `M_mkt = N − C_mkt − C_cr(se applicabile) − A − Pl_ord − AI − Q`, dove `C_mkt` è la commissione del marketplace (che di norma sostituisce o include il costo di pagamento: verificarlo, senza doppio conteggio né omissione).
  - Si confrontano margine per ordine, tasso di rimborso, sconto medio, quota di doppia attribuzione e proprietà dei dati cliente (§6), non il solo ricavo. Un marketplace con più ordini ma margine unitario inferiore non è migliore finché il margine totale non lo dimostra.
  - Il prezzo effettivo, le imposte (chi riscuote l'IVA: venditore o marketplace) e il costo del rinnovo/abbonamento del venditore vanno verificati con fonte e data prima del confronto.

**E. Priorità ai piani gratuiti o a consumo finché un prodotto non è validato**
Fino a quando un prodotto non ha superato la regola "scala" (§5) si usano, in ordine: (1) piano gratuito senza carta; (2) piano a consumo con tetto di spesa nel servizio; (3) abbonamento mensile disdicibile; (4) abbonamento annuale solo dopo validazione e con approvazione del Team Lead. Strumenti non indispensabili al test in corso non si attivano; i social si aprono solo per prodotti validati.

**F. Nel margine e nei test**
I costi di account e strumenti sono `Pl` (e `AI` per le API di modelli) del §2. I costi di strumenti attivati per un test concluso con stop entrano in `Q`. Ogni piano di test (§4) elenca gli strumenti previsti con costo massimo noto nella riga "piattaforma".

---

## 4. Struttura obbligatoria di ogni test

Nessun test parte senza tutti i campi compilati. Un campo vuoto = blocco.

```
TEST <id>            data: ____        responsabile: ____
Opportunità selezionata (id, evidenze osservate/ipotesi): ____
1. DOMANDA PRECISA        (una sola, falsificabile)
   "Un acquirente di <segmento> in <lingua/paese> acquista <prodotto> a <P € IVA incl.>
    da <canale> con tasso rimborso ≤ ____ e ROAS sul margine ≥ ____?"
2. OFFERTA
   Prodotto: ____   Prezzo IVA incl.: ____ €   Paese/aliquota IVA: ____ %
   Sconto massimo previsto: ____ %   Garanzia/rimborso: ____
3. CANALE PRIMARIO        (uno solo: creator | organico | ads)
   Dettaglio: ____   Canali secondari ammessi: ____ (tracciati come "assistiti")
4. BUDGET E SOGLIA DI STOP
   Riserva registro per categoria (costo massimo noto): ads ___ €, ai ___ €, piattaforma ___ €,
   compenso_fisso ___ €, commissione (busta) ___ €      Totale ≤ residuo: sì/no
   SOGLIA DI STOP IN €: spesa di acquisizione (Ads + commissioni + compensi fissi) = ____ €
5. CRITERIO DI SUCCESSO   (numerico, fissato prima di vedere i dati)
   ≥ 10 ordini; margine di contribuzione > 0; ROAS sul margine ≥ 1,5; rimborsi ≤ 10%
   Durata massima: ____ giorni   Attesa finestra clawback: sì (30 gg)
6. IPOTESI DA VERIFICARE  (elencate, con come si verificano)  ____
7. DATI DA RACCOGLIERE    ordini, sconti, rimborsi, attribuzione, spesa per canale
8. DECISIONE ATTESA       stop / ripeti / scala, secondo §5
```
La soglia di stop deve essere ≤ residuo ads del test e deve coprire un numero di ordini sufficiente per giudicare; se non lo copre il test non è informativo e va ridisegnato prima di spendere.

---

## 5. Regole stop / ripeti / scala **[P]**

Valutate in quest'ordine (come in `studio/economics.py`, `decidi`); la prima che scatta decide:

1. **Ordini < 10** (`ordini_minimi_per_giudicare`): **STOP** se la spesa di acquisizione ha raggiunto la soglia di stop del test, altrimenti **RIPETI** (continua/ripeti nei limiti del budget riservato).
2. Solo dopo (≥ 10 ordini): **rimborsi > 20%** (`tasso_rimborso_max_bp` 2000) → **STOP**.
3. Poi:
   - **SCALA** se margine di contribuzione > 0 **e** ROAS sul margine ≥ 1,5 **e** rimborsi ≤ 10%.
   - **RIPETI** se ROAS sul margine ≥ 0,8 **e** rimborsi ≤ 20%.
   - **STOP** altrimenti.

Con acquisizione zero (solo organico) il ROAS è **indefinito** e non limita la decisione (D-008); decidono margine e rimborsi.

Note operative:
- **Scalare oltre il tetto di 500 € richiede approvazione del titolare** (tramite Team Lead). "Scala" entro il tetto residuo non cambia questa regola per importi superiori.
- Il margine di ordini ancora nella finestra di 30 giorni è **provvisorio**: la decisione di scala va confermata dopo la chiusura della finestra; ripeti/stop possono basarsi sui dati disponibili.
- Il costo di un test concluso con STOP entra in `Q` (§2) e nel costo del portafoglio.
- Ogni decisione si registra con i numeri che l'hanno determinata (DECISIONI.md, a cura del Team Lead).

---

## 6. Confronto creator, organico, Ads

Stato dei dati: **nessun dato osservato**; la tabella dice cosa misurare e quali relazioni valgono per costruzione.

| Voce | Creator | Organico | Ads |
|---|---|---|---|
| Costo | 30% su netto **[P]**, pagato dopo 30 gg; eventuale compenso fisso | Tempo/AI; costo cassa ≈ 0 **[I]** | Spesa per clic/impressione, sostenuta prima di vendere |
| Rischio di cassa | Basso sul variabile (storno entro 30 gg) | Basso | Alto: la spesa non si recupera se non converte né se l'ordine è rimborsato |
| Margine per ordine | `N − C_pag − 0,30·N − quote` | `N − C_pag − quote` | `N − C_pag − A/ordine − quote` |
| Tasso rimborso | da misurare | da misurare | da misurare |
| Sconto medio | **[I]** probabile se il creator usa un codice sconto: riduce N e commissione | da misurare | da misurare |
| Doppia attribuzione | quota di ordini con codice creator **e** clic Ads | n/a | idem |

**Confronto sulla qualità delle vendite**: per ogni canale si riportano (a) tasso di rimborso, (b) sconto medio, (c) quota di ordini in doppia attribuzione, oltre al margine di contribuzione e al ROAS sul margine. Un canale con margine apparente alto ma rimborsi elevati o sconti profondi non è migliore.

**Regola di doppia attribuzione** (obbligatoria):
- **Portafoglio**: il ricavo di un ordine si conta **una sola volta**; si conservano **entrambi i costi** (commissione creator e spesa Ads).
- **Report per canale**: l'ordine risulta **"assistito" da entrambi** i canali; non si divide né si duplica il ricavo nascosto in silenzio. Quindi la somma dei margini per canale può eccedere il margine di portafoglio: **fa fede il margine di portafoglio**.
- La quota di doppia attribuzione (ordini con entrambe le attribuzioni / ordini totali) è un indicatore di sovrapposizione: se alta, il costo reale di acquisizione di quegli ordini è la somma dei due costi.

**Costo dei test falliti**: ogni test stoppato produce un costo irrecuperabile (Ads + AI + piattaforma + compensi + commissioni non stornate). Va sommato nel registro per categoria e ripartito come `Q` sugli ordini dei prodotti riusciti; il margine di portafoglio è calcolato **dopo** `Q`. Un canale non va giudicato solo su test riusciti: il tasso di fallimento e il costo medio per test fanno parte del suo costo.

---

## 7. Rischi e limiti delle ipotesi

| Rischio / limite | Tipo | Effetto | Mitigazione |
|---|---|---|---|
| Commissioni di pagamento 2,9% + 0,30 € non verificate | **[I]** | Margine su prezzi bassi molto sensibile alla quota fissa | Verificare con contratto/ fatture reali prima di T1 |
| Aliquote IVA OSS per paese e regole su servizi digitali | **[I]** | Errori di scorporo = margine falso e rischio fiscale | Verificare con fonte ufficiale; fare controllare al titolare/commercialista |
| Soglia di 10 ordini: campione piccolo | limite statistico | Tassi di rimborso e ROAS molto rumorosi (1 rimborso su 10 = 10%) | Trattare esiti come indicativi; ripetere prima di scalare oltre il tetto |
| Margine provvisorio fino a 30 giorni | limite | Una decisione di scala presa troppo presto può ribaltarsi | Conferma dopo la finestra |
| Test sintetici in collaudo | limite | I fixture non sono evidenza di mercato | Nessuna conclusione commerciale dai dati sintetici |
| Tetto di 500 € piccolo rispetto al costo di acquisizione | **[I]** | Possibile impossibilità di raggiungere 10 ordini | Disegnare test a costo di acquisizione massimo noto; alternativa organico/creator |
| Dipendenza da un creator | rischio | Sospensione codice al tetto di busta, riuscita legata a una persona | Tetto contrattuale; diritti e attribuzione verificati da creator-partnership |
| Doppia attribuzione non rilevata | rischio | Ricavo contato due volte nei report di canale | Regola §6; fa fede il margine di portafoglio |
| Rimborsi tardivi (>30 gg) | rischio | Commissione già pagata non recuperabile | Includere nel costo; valutare finestra più lunga a contratto |
| Test falliti non contabilizzati | rischio | Margine sovrastimato | `Q` obbligatoria nel margine |
| Il traguardo di 30.000 €/sett. | limite | Direzione, non previsione; dipende da N, Ō, m̄ non noti | Usare solo le tappe verificabili |
| Costi fissi di portafoglio F ignorati nei test singoli | limite | Un margine di contribuzione > 0 non implica utile operativo | Calcolare U con F a livello di portafoglio da T3 |

---

## 8. Proposte di modifica alla policy (non applicate; per il Team Lead)

Nessuna modifica fatta da me a `config/policy.json`. Esito delle proposte secondo il Team Lead:

1. (rinviata, D-010) **Soglia di stop**: `regole_decisione` cita la "spesa di acquisizione" ma la policy non contiene la soglia. Proposta: aggiungere `soglia_stop_max_cents_per_test` (valore da decidere; per far entrare ≥2 test nel budget ads di 200 € servirebbe ≤ 10.000 cent, **[I]**) e imporre che ogni test dichiari la propria soglia ≤ questo massimo.
2. (rinviata, D-010) **Busta commissioni creator**: aggiungere `busta_commissioni_creator_cents` (proposta = 6000, coerente con l'allocazione) e un comportamento esplicito `sospendi_codice_al_tetto: true`.
3. (ACCETTATA, D-007) **Definizione del tasso rimborso**: aggiungere `tasso_rimborso_base` = ordini rimborsati / ordini totali, e un `ordini_minimi_per_regola_rimborso` (proposta: applicare lo stop del 20% solo da un minimo di ordini, per evitare che 1 rimborso su 2 ordini fermi un test per rumore statistico; oppure confermare l'applicazione immediata se si preferisce prudenza).
4. (rinviata, D-010) **IVA/OSS**: aggiungere una tabella versionata `iva_per_paese_bp` con data e fonte, e `iva_stato: da_verificare`; nessun calcolo di scorporo in produzione senza fonte.
5. (ACCETTATA, D-008) **ROAS sul margine**: precisare che il numeratore usa ricavi netti dopo sconti e **dopo rimborsi**, e come trattare il denominatore zero (organico puro senza costi: ROAS non definito, non infinito; valutarlo solo sul margine).
6. (rinviata, D-010) **Quota test falliti `Q`**: fissare il metodo di ripartizione (proposta: costo cumulato dei test in stop del periodo / ordini netti totali dei prodotti non in stop) e la finestra temporale.
7. (ACCETTATA, D-003) **Arrotondamento**: stabilire per le divisioni in centesimi la regola (proposta: arrotondamento al centesimo più vicino, residui assegnati alla riserva).
8. (rinviata, D-010) **Finestra di clawback per rimborsi tardivi**: valutare di portarla a 45–60 giorni a contratto; richiede decisione del titolare tramite Team Lead.
9. (nuova, T-013; non applicata) **Costi di account e strumenti**: aggiungere in policy `ipotesi_costi_variabili.commissione_marketplace_pct_bp` e `commissione_marketplace_fissa_cents` (stato `da_verificare`, per marketplace); un campo `strumenti.prova_gratuita_preavviso_giorni` (proposta 3) e `strumenti.abbonamento_annuale_solo_dopo_validazione: true`; e per il registro il tipo di voce con campi `fonte`, `data_verifica`, `data_rinnovo`, `data_limite_disdetta`, `rinnovo_automatico` (modifica a `studio/ledger.py`, mia, da fare in un compito separato). Nessuna nuova categoria di spesa.
10. (nuova, T-013; per il Team Lead) **Commissioni marketplace trattenute dall'incasso**: decidere se registrarle come categoria `commissione` (condividendo la busta creator da 60 €) o solo nel margine come minor incasso. Proposta: solo nel margine, senza riserva, ma con stima massima registrata prima dell'apertura del marketplace.

---

## 9. Offerta a sito singolo (D-038, in scrittura dal Team Lead)

Cambio di impostazione: ogni prodotto validato ha un **sito proprio a prodotto singolo** con un'offerta costruita sul valore; fascia di prezzo obiettivo **39–99 € IVA inclusa** **[I: da validare, non è un dato di mercato]**; i marketplace (Etsy ecc.) diventano **canale secondario** (§3-bis D resta valido per il confronto per ordine). Questa sezione non modifica `config/policy.json` (proposte al §10). Nessun dato di mercato osservato: ogni cifra è **[P]**, **[I]** o aritmetica pura.

### 9.1 Equazione del valore e modello compilabile dell'offerta

```
Valore percepito = (risultato desiderato × probabilità percepita di ottenerlo) / (tempo di attesa × sforzo e sacrificio)
```
Applicata a un prodotto digitale: si alzano i due termini al numeratore (risultato specifico e misurabile, prove vere che sia ottenibile) e si abbassano i due al denominatore (consegna immediata, passi piccoli, modelli già compilati). La "probabilità percepita" si costruisce solo con elementi veri: esempi reali, anteprima del contenuto, garanzia, dimostrazioni verificabili. Nessun risultato economico o di salute promesso come certo.

Modello da compilare per ogni prodotto (campo vuoto = blocco, come al §4):

```
OFFERTA <id opportunità>                          data: ____   responsabile: ____
1. NOME DELL'OFFERTA        ____ (descrive il risultato, non il file; verificabile, senza superlativi non provabili)
2. PROMESSA                 "<segmento> ottiene <risultato misurabile> in <tempo realistico> senza <sforzo/ostacolo>"
   Prova che la sostiene:   ____ [osservata: fonte+data | ipotesi]
3. CONTENUTO PRINCIPALE     ____ (deliverable dalla specifica di prodotto)
4. BONUS (max 2-3)          ____ ciascuno con: problema che risolve, costo incrementale (AI/compenso) ≤ ____ €
5. GARANZIA                 tipo ____ durata ____ giorni, condizioni ____; tasso rimborso atteso [I] ____ %
6. PREZZO IVA incl.         ____ €    IVA paese ____ %    netto ____ €
7. ANCORAGGIO ONESTO        ammesso solo se vero e documentabile (vedi 9.2): prezzo precedente realmente praticato,
                            oppure confronto con alternativa reale citata con fonte+data; altrimenti "nessuno"
8. COSTO MASSIMO NOTO       riserva registro: ai ___ €, piattaforma ___ €, compenso_fisso ___ € (totale ≤ residuo)
9. IPOTESI DA VERIFICARE    elenco, con come si verificano
```
L'ancoraggio onesto è ammesso solo nelle forme seguenti: (a) prezzo di lancio vs prezzo successivo **solo se** il prezzo successivo sarà davvero applicato alla data dichiarata; (b) valore dei bonus indicato come "venduti a parte a X €" **solo se** vendibili e venduti a parte a quel prezzo; (c) confronto con il costo di un'alternativa reale (consulente, corso) citata con fonte e data. Il valore "percepito" non si dichiara come valore "di listino".

### 9.2 Limiti di legge UE (da far verificare a un professionista prima della pubblicazione)

Riferimenti da controllare: direttiva 2005/29/CE sulle pratiche commerciali sleali (UCPD, Allegato I: pratiche sempre vietate), direttiva (UE) 2019/2161 "Omnibus" (che ha modificato UCPD, direttiva 2011/83/UE sui diritti dei consumatori e direttiva 98/6/CE sull'indicazione dei prezzi), e il recepimento nazionale (per l'Italia, Codice del consumo, D.Lgs. 206/2005). **[I]**: i riferimenti puntuali agli articoli vanno confermati; questa non è consulenza legale.

Regole operative del team (tutto deve essere **vero e documentabile**, con prova archiviata):
1. **Niente scarsità o urgenza finte**: vietato dichiarare "ultimi posti", "solo oggi", "offerta in scadenza" se non è vero. Un limite (posti, data) esiste solo se è reale, vincolante e verificabile; alla scadenza il prezzo cambia davvero.
2. **Niente timer che si azzerano** o ripartono a ogni visita/ricarica; nessun conto alla rovescia generato per visitatore. Il timer ammesso è legato a una data fissa reale e uguale per tutti.
3. **Niente prezzi barrati fittizi**: ogni riduzione indica il prezzo precedente, che per Omnibus è in linea di principio il **più basso applicato nei 30 giorni precedenti** (da verificare con il professionista, incluse eccezioni per i nuovi prodotti). Il prezzo "pieno" mai praticato non si espone. Si conserva il registro dei prezzi con date.
4. **Niente recensioni, testimonianze o numeri di clienti inventati**; nessun conteggio "venduto N volte" non reale; le recensioni dichiarano come sono raccolte (Allegato I UCPD, pratiche sulle recensioni false).
5. **Promesse di risultato**: niente garanzie di guadagno o esiti non dimostrabili; esempi di risultato solo se reali e tipici, con avvertenza.
6. **Trasparenza di prezzo e IVA**: prezzo finale IVA inclusa visibile per il paese del cliente; nessun costo aggiuntivo a sorpresa al checkout; rinnovi (per la ricorrenza) dichiarati prima dell'acquisto.
7. **Diritto di recesso**: per i contenuti digitali scaricabili va gestito il consenso esplicito alla consegna immediata e la presa d'atto della perdita del recesso (direttiva 2011/83/UE), **oltre** alla garanzia commerciale dichiarata, che è un impegno aggiuntivo e non lo sostituisce. Condizioni e informativa precontrattuale vanno verificate dal professionista.
8. **Preordine e lista d'attesa dichiarati come tali**: data di consegna prevista reale, diritto di rimborso, nessun testo che faccia sembrare il prodotto già disponibile; per la lista d'attesa consenso e informativa privacy (GDPR) e disiscrizione semplice.
9. QA indipendente verifica la pagina contro questo elenco prima di ogni pubblicazione; un elemento non documentabile è motivo di blocco.

### 9.3 Economia della garanzia

- **Tasso di rimborso atteso `r`**: è un'**ipotesi [I]**; nessun dato osservato. Valori di calcolo usati sotto: 5%, 10%, 20% (scenari, non stime). Il valore da usare per le decisioni viene solo dai test (tasso rimborso = ordini rimborsati / ordini totali, §8 punto 3).
- **Costo nel margine**: per ordine lordo, il ricavo atteso è `(1 − r) × N`; il costo di pagamento `C_pag` e la spesa Ads `A` restano a carico anche sugli ordini rimborsati (§2). Quindi `M = (1 − r)·N − C_pag − A − (altre voci del §2)`. Ogni punto percentuale di rimborso costa `N/100` per ordine.
- **Soglia oltre cui la garanzia distrugge il margine** (margine = 0), con le sole voci N, C_pag, A:

```
r* = 1 − (C_pag + A) / N
```
  Con IVA 22% (illustrativa), A = 20 € per ordine lordo: a 49 € → N = 40,16 €, C_pag = 1,72 €, **r\* = 45,9%**; a 97 € → N = 79,51 €, C_pag = 3,11 €, **r\* = 70,9%**. Con A = 0 (solo organico) r\* è 95,7% (49 €) e 96,1% (97 €). Sono limiti teorici di pareggio, non obiettivi: includendo piattaforma, AI, creator e `Q` la soglia reale scende.
- **Soglie operative**: restano quelle di policy [P], 10% per scalare e 20% per fermarsi (§5); una garanzia più lunga o "senza domande" va accettata solo se il test mostra rimborsi sotto il 10%. Se il rimborso supera il 20% si ferma e si indaga su promessa, prodotto o pubblico, prima di toccare la garanzia.
- **Garanzia come leva**: alza la probabilità percepita, ma ogni sua estensione si valuta con questo calcolo; non si estende una garanzia senza aver stimato `r` e `r*` per quel prezzo.

### 9.4 Aritmetica aggiornata (solo calcolo, non previsione)

Formula: `utile giornaliero = vendite/giorno × M`, con `M = (1 − r)·N − C_pag − A`.
Parametri di calcolo (scenari, tutti **[I]**): IVA 22% (illustrativa, da verificare per paese), commissione di pagamento 2,9% + 0,30 € su P [P, da verificare], rimborso `r` = 10%, Ads `A` = 20 € per ordine lordo (costo di acquisizione di scenario, non un dato). Esclusi: creator, piattaforma, AI, `Q`, costi fissi.

| | 49 € | 97 € |
|---|---|---|
| Netto IVA `N = P/1,22` | 40,16 € | 79,51 € |
| `C_pag` | 1,72 € | 3,11 € |
| Ricavo atteso `(1−r)·N` (r=10%) | 36,15 € | 71,56 € |
| **`M` per ordine lordo** (A=20 €) | **14,43 €** | **48,44 €** |
| CPA di pareggio (M=0, r=10%) | 34,43 € | 68,44 € |

| Vendite/giorno | utile giornaliero a 49 € | utile giornaliero a 97 € |
|---|---|---|
| 1 | 14,43 € | 48,44 € |
| 3 | 43,28 € | 145,33 € |
| 5 | 72,13 € | 242,22 € |
| 10 | 144,27 € | 484,44 € |

Sensibilità (a 49 € / 97 €, 1 vendita/giorno): con A = 30 € M = 4,43 € / 38,44 €; con r = 20% e A = 20 € M = 6,40 € / 32,53 €. Un rimborso in più su 10 ordini costa 4,02 € / 7,95 € per ordine.
Aritmetica sul traguardo di lungo periodo, F = 0: 30.000 €/sett. = 4.286 €/giorno ⇒ ≈ 297 vendite/giorno a 49 € e ≈ 88 a 97 € nello scenario sopra. È solo la scomposizione del traguardo (§1), non una previsione.

### 9.5 Validazione prima dello sviluppo

Principio: non si sviluppa il prodotto finché una **pagina di vendita singola** non ha dimostrato interesse misurato. La pagina descrive l'offerta (9.1) con il prezzo reale e dichiara con chiarezza lo stato: **"lista d'attesa"** (nessun pagamento) oppure **"preordine"** (pagamento anticipato, consegna prevista a data reale, rimborso garantito). Nessun testo che faccia credere il prodotto già disponibile (9.2 punto 8).

- **Budget**: Ads **60–80 € per test**, **massimo 3 test** nel primo tetto di 500 €. Aritmetica: 3 × 60 = 180 € ≤ 200 € allocati ad `ads`; 3 × 80 = 240 € **supera** l'allocazione di 200 € di 40 €. Con l'allocazione attuale: 3 test fino a 66 € ciascuno, oppure 2 test da 80 € + 1 da 40 €; la riserva e le altre categorie non si usano per Ads senza decisione registrata. Costo massimo noto riservato prima dell'avvio, con tetto giornaliero e totale in campagna. Pagina, dominio e strumenti in `piattaforma`/`ai` con costo massimo noto (§3-bis); tre pagine condividono ove possibile lo stesso strumento. Resta il limite di un test alla volta (`max_opportunita_per_test`) finché non si decide diversamente (§10).
- **Metriche**: visite qualificate (esclusi bot e traffico interno), iscrizioni o preordini, conversione visita→iscrizione (o preordine), **costo per iscrizione** `CPI = spesa / iscrizioni` e **costo per preordine** `CPO = spesa / preordini`.
- **Soglie fissate prima di vedere i dati** (progetto del test, non evidenza di mercato; eventuali correzioni solo prima dell'avvio, in DECISIONI.md):
  - **Test informativo**: ≥ 100 visite qualificate entro la spesa prevista; sotto questo numero il test non è informativo, non è né successo né fallimento: si rivede il canale/annuncio una sola volta con la riserva Ads residua del test.
  - **Lista d'attesa**: **successo** se conversione ≥ 10% **e** CPI ≤ 3 € (≈ ≥ 20 iscrizioni su 60 €). Poiché l'iscrizione non prova la disponibilità a pagare, la lista si convalida con una mail di conferma con prezzo reale: successo pieno se ≥ 5% degli iscritti clicca sul pagamento/preordine; senza questa verifica il risultato resta **ipotesi**.
  - **Preordine**: **successo** se ≥ 3 preordini pagati e `CPO ≤ 25 €` (prezzo 49 €: ≤ 65% del margine lordo `N − C_pag` = 38,44 €; a 97 € la stessa soglia è ≤ 33%).
  - **Stop**: conversione < 3%, o 0 iscrizioni/preordini dopo 50% della spesa e ≥ 60 visite, o CPI/CPO sopra soglia al 100% della spesa. Stop = nessuno sviluppo; il costo entra in `Q` (§2).
  - **Successo** autorizza solo lo sviluppo del prodotto e il test commerciale (§4, criterio ≥ 10 ordini); non autorizza spesa extra. Con preordini pagati: consegna entro la data dichiarata o rimborso integrale.
- Ogni test compila `TEST <id>` (§4) con offerta (9.1), canale primario (ads), soglia di stop in € e criterio di successo come sopra. Pubblicazione e campagne seguono la fase del workflow; i passaggi di pagamento (carta, OTP, conferme) li esegue il titolare (`AZIONI_TITOLARE.md`).

### 9.6 Tappe realistiche (traguardo operativo)

Il traguardo di 30.000 €/settimana (§1, T6) **resta come traguardo di lungo periodo**, non come obiettivo operativo. L'obiettivo operativo è la sequenza seguente, ogni passo con evidenza misurata:

| Tappa | Condizione verificabile | Evidenza |
|---|---|---|
| A. Prima vendita | 1 ordine reale pagato da uno sconosciuto, consegna verificata, non rimborsato nella finestra | Ordine, consegna e download in riconciliazione |
| B. 10 vendite con margine positivo | ≥ 10 ordini netti con `M` > 0 dopo IVA, commissioni, Ads, rimborsi, `Q` (= T1 del §1, regole §5) | Report di misurazione + registro spese |
| C. Secondo prodotto | Un secondo prodotto validato con 9.5 e proprio sito; margine di portafoglio > 0 inclusi i test falliti | Margine per prodotto e di portafoglio |
| D. Ricorrenza | Offerta ricorrente (abbonamento, aggiornamenti, comunità) con rinnovo dichiarato, tasso di rinnovo e rimborso misurati | Ordini ricorrenti, churn, margine per periodo |

Tappe oltre il tetto di 500 € richiedono approvazione del titolare (tramite Team Lead). Le tappe T2–T6 del §1 restano il quadro di lungo periodo: A–D ne sono la traduzione operativa e non le sostituiscono per la scala.

---

## 10. Proposte di modifica alla policy da D-038 (non applicate; per il Team Lead)

Nessuna modifica fatta a `config/policy.json` o al codice. Proposte:
11. **Fascia di prezzo**: aggiungere `prezzo_obiettivo_min_cents` = 3900 e `prezzo_obiettivo_max_cents` = 9900 (stato `da_verificare`), con avviso (non blocco) per piani di test fuori fascia.
12. **Test di validazione**: aggiungere `validazione.ads_per_test_min_cents` = 6000, `ads_per_test_max_cents` = 8000, `validazione.max_test_primo_tetto` = 3; coerenza richiesta con `allocazione_budget_cents.ads` = 20000: o fissare il massimo a 6600 cent, o spostare 4000 cent da `riserva` ad `ads` (decisione del Team Lead; la riserva scenderebbe a zero, sconsigliato) o ridurre i test a 2 da 80 €.
13. **Soglie di validazione**: `validazione.visite_minime` = 100, `validazione.conversione_min_bp` = 1000, `validazione.conversione_stop_bp` = 300, `validazione.cpi_max_cents` = 300, `validazione.cpo_max_cents` = 2500, `validazione.preordini_min` = 3.
14. **Garanzia**: aggiungere `garanzia.tasso_rimborso_atteso_bp` (stato `ipotesi`), `garanzia.giorni` e calcolo di `r*` in `studio/economics.py` (compito separato, mio).
15. **Canale secondario marketplace**: aggiornare `config/canali_vendita.json` (acquisizione) con ruolo "secondario"; confronto per ordine secondo §3-bis D. Il traguardo operativo `obiettivo_operativo` (tappe A–D) da aggiungere in policy accanto a `obiettivo_lungo_periodo`.
16. **Rivedere `ordini_minimi_per_giudicare` e le soglie ROAS** a 39–99 € dopo i primi test: nessuna modifica prima di dati osservati.
