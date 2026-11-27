# Metodo di ricerca opportunità

Metodo riutilizzabile per cercare opportunità di prodotti digitali in nicchie, lingue e mercati diversi. Responsabile: ricerca-mercato. Schema della scheda: `templates/opportunita.schema.json`. Vincoli numerici: `config/policy.json`.

Principio: si parte da **problemi e compratori**, non dal prodotto. Poi si guardano concorrenti e canali. Il prodotto è l'ultima cosa che si decide.

## 0. Metodo v2 (in vigore, approvato dal titolare)

Le nuove schede portano `"metodo_versione": 2`. Le schede v1 restano valide come storico; per confrontarle con le v2 vanno rivalutate aggiungendo `offerta`.

### Imbuto in quattro stadi
| Stadio | Volume | Contenuto | Fonti |
|---|---|---|---|
| (a) Scansione | 200-300 micro-mercati | scheda breve (acquirente, problema, indizio di domanda, concorrenti noti) | solo risultati di ricerca, costo minimo |
| (b) Shortlist | 20 | scheda completa secondo lo schema | risultati di ricerca + prime pagine |
| (c) Approfondimento | i migliori della shortlist | pagine **lette integralmente** | lettore del sistema: `python3 -m studio fonti leggi <url>` |
| (d) Candidati | 3 | pronti per la validazione con pagina di vendita | almeno 2 fonti osservate indipendenti |

Il lettore legge solo gli host consentiti dall'ambiente e salva testo, data e impronta in `research/fonti/`. Per le fonti `letta_integralmente` cita data e impronta nella descrizione. Se un host non è consentito o la pagina richiede login/pagamento, la fonte è `non_verificabile` (escalation al Team Lead se necessaria).

### Livello di ogni fonte (campo `livello`)
- `letta_integralmente`: pagina letta per intero con il lettore e salvata in `research/fonti/`.
- `risultato_di_ricerca`: visto solo titolo/estratto in un risultato di ricerca.
- `non_verificabile`: non ricontrollabile; vale come ipotesi.

Con soli `risultato_di_ricerca`, `problema` e `concorrenza` restano **<= 6** (D-028). Con pagine lette integralmente possono salire. Il livello non sostituisce `osservata`/`ipotesi`: sono due assi distinti.

### Criterio `offerta` (0-10)
Si può costruire un'offerta da 39-99 euro con un risultato misurabile, bonus credibili e una garanzia sostenibile? 0-3: risultato vago o garanzia insostenibile; 4-6: offerta plausibile ma bonus o misurabilità deboli; 7-10: risultato misurabile, bonus credibili, garanzia sostenibile a margine intatto. Obbligatorio se `metodo_versione` = 2.

## 1. Sequenza

1. **Compratore**: chi è, in quale contesto, cosa paga già oggi.
2. **Problema**: cosa gli fa perdere tempo, denaro o sicurezza; quanto è urgente e ricorrente.
3. **Domanda osservabile**: tracce pubbliche del problema (sezione 2).
4. **Concorrenti**: chi risolve già il problema, a che prezzo, con quali lacune.
5. **Canali**: dove si raggiunge il compratore e quanto costa.
6. **Economia**: prezzo, sviluppo, assistenza, margine (sezione 4).
7. **Esclusioni** (sezione 5), poi **punteggio** (sezione 6) e **soglia** (sezione 7).

## 2. Fonti tipiche per osservare la domanda

| Fonte | Cosa cercare |
|---|---|
| Forum e community (Reddit, forum di settore, gruppi pubblici) | domande ripetute, lamentele, richieste di strumenti |
| Recensioni negative dei concorrenti | lacune concrete, motivi di rimborso, funzioni mancanti |
| Marketplace (Etsy, Gumroad, app store, template store) | prodotti simili, prezzi, numero di recensioni, categorie affollate |
| Ricerche (suggerimenti di ricerca, tendenze pubbliche) | formulazioni usate dal compratore, stagionalità |
| Community e Q&A (Stack Exchange, gruppi pubblici, commenti sotto video) | linguaggio del compratore, problemi non risolti |

Solo lettura del web pubblico. Mai contattare persone, iscriversi, compilare form o creare account. Se una fonte richiede login o pagamento: escalation al Team Lead.

### Come registrare una fonte
Ogni fonte è un oggetto in `fonti` con `tipo`, `descrizione`, `url`, `data` (formato `AAAA-MM-GG`, giorno della consultazione). Nella descrizione: cosa si è visto, in una frase verificabile (es. "12 recensioni a 1-2 stelle citano l'assenza di esportazione PDF"). Non incollare testi lunghi né dati personali di utenti.

## 3. Osservata e ipotesi (obbligatorio)

- **`osservata`**: un fatto che chiunque può ricontrollare aprendo l'URL alla data indicata. Richiede `url` e `data`.
- **`ipotesi`**: tutto il resto: stime, inferenze, analogie, cifre non verificate. Non richiede URL.

Regole:
- Mai presentare un'ipotesi come fatto. Nel dubbio è `ipotesi`.
- Ogni cifra della scheda (prezzo, costi, margine) è un'ipotesi, salvo sia sostenuta da una fonte `osservata` citata.
- Un'osservazione vale una fonte; più pagine dello stesso sito o stesso thread contano come una sola fonte.
- Una fonte osservata deve riguardare il mercato e la lingua della scheda.
- I dati sintetici di collaudo si marcano `"sintetico": true`.

## 4. Stime economiche (tutte in centesimi di euro, tutte ipotesi)

- **Prezzo da verificare** (`prezzo_da_verificare_cents`): parti dai prezzi osservati dei concorrenti; il prezzo resta da verificare con un test reale nella fase commerciale.
- **Accesso al pubblico** (`accesso_pubblico`): `canale` principale (organico, marketplace, community, ads) e `costo_stimato_cents` per ottenere un acquirente. Se il canale non è raggiungibile senza spesa ignota, abbassa il punteggio.
- **Costo di sviluppo** (`costo_sviluppo_cents`): costo vivo (strumenti, AI, grafica) per una prima versione vendibile; il tempo del team non si prezza, ma conta nel punteggio.
- **Complessità di assistenza** (`bassa`/`media`/`alta`): bassa = prodotto autoesplicativo; alta = richiede supporto personale, personalizzazioni o aggiornamenti frequenti.
- **Ipotesi di margine** (`ipotesi_margine_bp`, punti base): (prezzo - costi variabili - costo di accesso per acquisto) / prezzo. Usa le ipotesi di costo in `config/policy.json` (commissioni di pagamento e creator) e dichiara le assunzioni.

## 5. Criteri di esclusione

Scarta l'opportunità, annotando il motivo, se vale uno di questi:
- **Categorie regolamentate**: salute, finanza, legale, minori. Non si scartano in silenzio: escalation al Team Lead.
- **Marchi o IP di terzi**: il prodotto richiede loghi, personaggi, contenuti protetti o derivati non autorizzati.
- **Promesse non verificabili**: guadagni garantiti, risultati medici o miracolosi, "scalabilità" non dimostrabile.
- **Dipendenza da un solo canale**: se un solo canale, controllato da terzi, dà tutto l'accesso al pubblico, il rischio è inaccettabile.
- Fonte richiesta a pagamento o con login (non accessibile): non usarla.

## 6. Punteggio 0-100

Ogni criterio riceve un voto 0-10 nel campo `punteggi`, poi il motore applica i pesi:

| Criterio (chiave) | Peso | Voto 10 significa |
|---|---|---|
| problema/urgenza (`problema`) | 20 | problema frequente, doloroso, già pagato |
| accesso al pubblico (`accesso`) | 20 | canale chiaro, economico, non unico |
| potenziale d'offerta (`offerta`) | 15 | offerta 39-99 euro, risultato misurabile, bonus credibili, garanzia sostenibile |
| margine (`margine`) | 15 | margine alto dopo commissioni e accesso |
| concorrenza superabile (`concorrenza`) | 15 | concorrenti con lacune evidenti e prezzi alti |
| costo di sviluppo basso (`costo_sviluppo`) | 8 | prima versione quasi a costo zero |
| assistenza semplice (`assistenza`) | 7 | quasi nessun supporto |

Pesi del metodo v2 (fissati nel motore). Il metodo v1 usava problema 25, accesso 20, margine 20, concorrenza 15, costo_sviluppo 10, assistenza 10 senza `offerta`. Punteggio = somma(voto/10 x peso), quindi massimo 100. Il motore ricalcola il totale: non scriverlo nella scheda.

Calibrazione dei voti: 0-3 debole, 4-6 discreto, 7-10 forte. Un voto alto su `problema`, `accesso` o `concorrenza` deve poggiare su fonti `osservata`; senza evidenza, massimo 5. Con soli risultati di ricerca, `problema` e `concorrenza` <= 6 (D-028).

## 7. Soglia di selezione

Un'opportunità è candidata solo se:
- **punteggio >= 60**, e
- **almeno 2 fonti `osservata`** (indipendenti, con URL e data).

Se manca una delle due condizioni, la scheda resta in archivio come non selezionata. Per il test si seleziona al massimo 1 opportunità (`max_opportunita_per_test`). Se le soglie in `config/policy.json` cambiano, vale il file di policy.

## 8. Adattamento multilingua

**Non tradurre l'opportunità: rifai la verifica nel mercato locale.**
- Una scheda per coppia lingua/mercato (`lingua`, `mercato`), con id distinto.
- Rifai da capo fonti, concorrenti, prezzi e canali con fonti locali: community, marketplace e recensioni nella lingua target.
- Verifica il linguaggio reale del compratore: spesso non coincide con la traduzione letterale.
- Controlla differenze locali: concorrenti, abitudini di pagamento, canali dominanti, norme (consumatori, IVA, privacy).
- Le fonti del mercato di origine possono ispirare una ricerca, ma non contano per la soglia delle 2 fonti.
- Rivaluta ogni voto di punteggio: la stessa idea può passare in un mercato e fallire in un altro.

## 9. Controllo prima della consegna

- Tutti i campi obbligatori dello schema compilati; `sintetico` presente.
- Ogni fonte `osservata` ha URL e data; ogni cifra è marcata come ipotesi o sostenuta da una fonte.
- Esclusioni controllate e annotate; categorie regolamentate segnalate al Team Lead.
- Scheda salvata in `research/<id>.json`, valida rispetto allo schema.
