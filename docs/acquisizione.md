# Acquisizione: metodo per gli esperimenti

Responsabile: acquisizione. Fase: Distribuzione. Importi in euro nel testo, in centesimi interi nei file di config e nel registro (`studio/ledger.py`).
Stato: collaudo. Nessun account, campagna o spesa reale; gli Ads sono **simulati** (`studio/adapters/mock.py`). Tutto ciò che segue è metodo, non un dato di mercato: ogni soglia o aspettativa è **ipotesi** finché non c'è evidenza osservata (fonte + data).

## 1. Principi
1. Un esperimento risponde a una sola domanda e usa un solo canale primario.
2. Nessuna spesa senza busta riservata nel registro con costo massimo noto. Costo ignoto o residuo insufficiente: blocco ed escalation al Team Lead.
3. I canali si confrontano sul **margine**, mai sui ricavi lordi.
4. Un test fallito o fermato costa e va contato: non si cancella dal confronto.
5. Criteri, soglie e aspettative di costo sono ipotesi finché non verificate; i dati sintetici sono marcati `"sintetico": true`.

## 2. Anatomia di un esperimento
| Campo | Contenuto |
|---|---|
| Domanda | Ipotesi falsificabile, es. "A questo prezzo, gli ordini da search coprono Ads + commissioni?" |
| Canale primario | Uno solo tra i canali del par. 6 |
| Offerta | Prodotto, prezzo, sconto massimo ammesso, garanzia/rimborso, pagina di arrivo |
| Budget massimo | Importo riservato nel registro **prima** del lancio, categoria `ads`, `compenso_fisso` o `commissione` |
| Soglia di stop in € | Perdita/spesa cumulata oltre la quale si ferma (par. 5), sempre ≤ budget massimo |
| Criterio di successo | Numerico, fissato prima: ordini minimi, ROAS sul margine, tasso di rimborso (par. 4) |
| Attribuzione | UTM, codici, finestra, regola per la doppia attribuzione (par. 7) |
| Durata minima | Giorni minimi e ordini minimi prima di giudicare (par. 8) |

Un esperimento senza uno di questi campi non parte.

## 3. Confronto tra canali: metriche obbligatorie
- **Ricavi netti** = incassi IVA esclusa, meno rimborsi, meno sconti applicati.
- **Margine di contribuzione** = ricavi netti − commissioni di pagamento − commissioni creator − costi diretti dell'esperimento (Ads, compensi fissi) − costo dei test falliti attribuibili al canale.
- **ROAS sul margine** = (ricavi netti IVA esclusa − commissioni di pagamento) / (Ads + commissioni creator + compensi fissi).
- **Tasso di rimborso** = ordini rimborsati / ordini (in punti base).
- **Sconto medio** = sconti totali / ricavi prima dello sconto.
- **Quota di ordini con doppia attribuzione** = ordini rivendicati da più di un canale / ordini totali. Se alta, il confronto è inaffidabile.

Costi da includere sempre: rimborsi, sconti, commissioni (pagamento e creator, tenendo conto della finestra di clawback in `config/policy.json`) e **costo dei test falliti, anche di quelli fermati dalla soglia di stop**. Non si confrontano ricavi lordi, visite, clic o ordini senza costo.

Il confronto è una tabella con una riga per canale e queste colonne; due canali sono confrontabili solo se hanno almeno `ordini_minimi_per_giudicare` ordini (policy) e offerta simile.

## 4. Criteri di decisione
I valori vengono da `config/policy.json` (`regole_decisione`), che ha come responsabile strategia-finanza; qui si rimanda e non si duplicano:
- **Scala** se margine di contribuzione > 0, ROAS sul margine ≥ soglia "scala" e rimborsi sotto il massimo.
- **Ripeti** se ROAS sul margine ≥ soglia "ripeti" e rimborsi sotto il massimo.
- **Altrimenti stop.**
- Sotto gli ordini minimi: nessun giudizio, solo "dati insufficienti" (non si estrapola).

Ordini con rimborso e sconto pesano nel margine; un canale con molti ordini ma rimborsi alti o sconti profondi perde il confronto.

## 5. Soglia di stop e budget
- Soglia di stop in € ≤ busta riservata. Si indica anche una soglia di allarme (es. 50% della soglia) per rivalutare in corsa.
- La soglia è sulla **spesa netta cumulata** (spesa − margine già generato dagli ordini confermati oltre la finestra rimborsi, se si vuole un criterio meno conservativo; in assenza di decisione, si usa la spesa lorda).
- Alla soglia: pausa automatica, nessuna ripresa senza nuova decisione registrata (DECISIONI.md).
- La spesa fermata resta nel conto del canale (par. 3).
- Lo storno di una commissione creator su ordine rimborsato entro la finestra si registra con `undraw`; non si riduce la busta a mano.

## 6. Scegliere un canale compatibile con l'offerta
Le regole seguenti sono **ipotesi da verificare** con gli esperimenti, non fatti. Ogni canale ha prima di tutto un test di sostenibilità sul margine: con prezzo P, costo variabile e costo massimo ammissibile per ordine, il canale è plausibile solo se il costo di acquisizione atteso per ordine sta sotto il margine unitario dopo commissioni, sconti e rimborsi attesi.

Calcolo guida (ipotesi): margine unitario ≈ P netto IVA − commissione di pagamento (policy: percentuale più quota fissa, "da_verificare") − commissione creator o sconto previsti − rimborso atteso × P. Il costo per ordine ammissibile è una frazione di questo margine unitario, scelta nel piano dell'esperimento.

| Canale | Quando è plausibile (ipotesi) | Quando è debole (ipotesi) | Metrica da osservare |
|---|---|---|---|
| Ads search | Intento d'acquisto esplicito, prezzo o margine abbastanza alti da assorbire il costo per clic e la conversione bassa | Prezzo basso: il costo per ordine supera presto il margine; rare eccezioni da verificare | ROAS sul margine, costo per ordine |
| Ads social | Offerta visiva, problema riconoscibile, prezzo medio-alto o ritorno ricorrente | Prezzo basso, domanda non ancora formulata, tracciamento debole | ROAS sul margine, rimborsi |
| SEO / organico | Domande ricercate stabilmente, tempi lunghi accettabili, nessuna spesa media diretta | Serve velocità; il tempo di indicizzazione supera la durata utile del test | Ordini attribuiti per pagina, margine; costo in ore/AI |
| Marketplace digitali | Prodotto standardizzato, prezzo basso (la visibilità interna compensa), accetta commissione di piattaforma | Margine eroso da commissione alta; poco controllo su rimborsi e clienti | Margine dopo commissione di piattaforma, rimborsi |
| Community | Nicchia con luoghi di discussione attivi, offerta utile senza spam, regole del luogo rispettate | Nessuna presenza credibile; rischio di essere percepiti come promozione | Ordini per contributo, sconto medio |
| Email | Esiste già una lista con consenso valido; offerta di follow-up | Lista da costruire da zero: non è acquisizione ma un esperimento di lead magnet separato | Ordini per invio, rimborsi |
| Creator | Fiducia di una persona verso un pubblico di nicchia; commissione a successo | Compenso fisso alto rispetto al margine; diritti e attribuzione non chiari | Vedi `docs/creator-partnership.md` |

Dettagli su selezione, compensi, codici e diritti dei creator: **`docs/creator-partnership.md`** (responsabile creator-partnership). Qui si usano solo i suoi numeri nel confronto del par. 3.

Regola pratica (ipotesi): a **prezzo basso** gli Ads a pagamento sono raramente sostenibili, perché commissione di pagamento fissa e rimborsi consumano buona parte del margine; si parte da organico, marketplace, community o email. Gli Ads entrano per prezzi medio-alti o dopo evidenza di conversione organica. Ogni esperimento Ads su prezzo basso è quindi un test della regola, con soglia di stop piccola.

Un canale sconsigliato dall'ipotesi non è vietato: è ammesso solo con budget minimo e domanda esplicita ("l'ipotesi è falsa?").

## 7. Attribuzione
- **UTM** su ogni link: `utm_source` (canale), `utm_medium`, `utm_campaign` (id esperimento, es. `E-012`), `utm_content` (variante).
- **Codici**: un codice sconto/affiliato per creator e per esperimento; il codice prevale solo se rispetta la regola sotto.
- **Finestra**: indicare in giorni (ipotesi iniziale: stessa sessione per Ads/community, 7 giorni per email, finestra creator come da `docs/creator-partnership.md`). La finestra è fissata prima del lancio e non cambia a test avviato.
- **Doppia attribuzione**: regola scelta in anticipo (ultimo clic con UTM, oppure codice come priorità per i creator). Ogni ordine va a **un solo** canale nel margine; la quota di ordini ambigui si riporta come metrica e, se alta (soglia nel piano), il risultato del confronto è "non conclusivo".
- Ordini senza UTM né codice: "non attribuiti"; si mostrano a parte, non si distribuiscono a piacere.
- Riconciliazione ordini/pagamenti con i dati di Shopify (`docs/operazioni-shopify.md`).

## 8. Durata minima
- Una durata minima in giorni **e** un numero minimo di ordini (policy: `ordini_minimi_per_giudicare`), valida la prima soddisfatta solo se entrambi, tranne stop per soglia.
- Per rimborsi e clawback si attende la finestra dei rimborsi prima del verdetto finale; il verdetto provvisorio è marcato tale.
- SEO e community: durata più lunga e metriche anticipatrici (indicizzazione, interazioni) marcate come tali, mai come successo.
- Mai chiudere in anticipo un test in positivo per entusiasmo: solo per soglia di stop o per blocco QA.

## 9. Regole di sicurezza
1. **Budget giornaliero ≤ busta riservata** (e ≤ soglia di stop residua): il tetto giornaliero si dichiara nel piano e il motore rifiuta valori maggiori.
2. **Spesa Ads simulata** finché il titolare non collega l'account. Non si creano account, non si caricano creatività, non si attivano campagne. Il collegamento è un'azione del titolare in `team/azioni_titolare.json` tramite il Team Lead.
3. **Pausa automatica alla soglia di stop**, senza conferma umana; la ripresa richiede nuova decisione.
4. Nessuna credenziale, carta o token nei piani o nei log.
5. Un esperimento oltre il residuo della categoria o con costo massimo ignoto: escalation al Team Lead, niente avvio.
6. Contatti esterni (creator, community, email a terzi) vietati in collaudo: sono solo piani.

## 10. Ciclo di vita
1. Bozza con il modello del par. 11 (stato: `bozza`).
2. Riserva della busta nel registro; senza riserva restano `bozza`.
3. QA indipendente controlla completezza e coerenza (soglia ≤ busta, attribuzione definita).
4. Esecuzione (simulata in collaudo); raccolta dati.
5. Chiusura: tabella di confronto (par. 3), decisione scala/ripeti/stop (par. 4), chiusura della busta e rilascio del non speso.
6. Registro dei risultati e lezioni appresi, distinguendo osservato da ipotesi.

Il piano macchina corrispondente è `runs/<id>/artifacts/distribuzione.json`, prodotto dal motore; questo documento ne descrive il metodo.

## 11. Modello compilabile
Copiare, compilare ogni campo; `[...]` = da riempire. Nulla di ciò che segue è un dato finché non è marcato come osservato.

```
ID esperimento:            E-[nnn]
Stato:                     bozza | riservato | in corso | fermato | chiuso
Sintetico:                 sì | no
Data / responsabile:       [aaaa-mm-gg] / acquisizione

DOMANDA
[Ipotesi falsificabile, una frase]

CANALE PRIMARIO:           [Ads search | Ads social | SEO | marketplace | community | email | creator]
Perché compatibile:        [ragionamento sul margine unitario; etichetta: ipotesi | osservato (fonte, data)]

OFFERTA
Prodotto / prezzo (IVA escl.): [..] / [..] €
Sconto massimo:            [..] %    Garanzia/rimborso: [..]
Pagina di arrivo:          [..]
Margine unitario atteso:   [..] €    (dopo commissione pagamento, sconto, rimborso atteso) - ipotesi

BUDGET
Busta riservata (id):      [..]      Categoria: [ads | compenso_fisso | commissione]
Budget massimo:            [..] €    Budget giornaliero max: [..] €  (<= busta)
Soglia di allarme:         [..] €
Soglia di stop:            [..] €    (<= busta; pausa automatica)
Modalità:                  simulata (collaudo) | reale (solo dopo collegamento del titolare)

CRITERIO DI SUCCESSO (fissato prima)
Ordini minimi:             [..]
ROAS sul margine >=:       [..]
Tasso di rimborso <=:      [..] %
Sconto medio <=:           [..] %
Doppia attribuzione <=:    [..] %
Margine di contribuzione > [..] €

ATTRIBUZIONE
UTM:                       source=[..] medium=[..] campaign=E-[nnn] content=[..]
Codice:                    [..]
Finestra:                  [..] giorni      Regola doppia attribuzione: [..]

DURATA MINIMA
Giorni:                    [..]      Ordini:  [..]      Attesa finestra rimborsi: [..] giorni

RISULTATI (a chiusura)
Spesa (Ads + commissioni creator + compensi fissi): [..] €
Ricavi netti IVA escl.:    [..] €    Commissioni di pagamento: [..] €
Rimborsi / sconti:         [..] € / [..] €
Margine di contribuzione:  [..] €    ROAS sul margine: [..]
Tasso di rimborso:         [..] %    Sconto medio: [..] %    Doppia attribuzione: [..] %
Costo test (anche se fermato): [..] €
Decisione:                 scala | ripeti | stop | non conclusivo   Motivo: [..]
Evidenze:                  osservate [fonte, data] / ipotesi [..]
```
