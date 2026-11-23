# Specifica prodotto — TEMPLATE

> Responsabile: sviluppo-prodotto. Compilare in `products/<id>/spec.md`, partendo da una scheda `research/<id>.json` **approvata**.
> Sostituire ogni `<...>`. Ogni dato è `osservata` (fonte + data) oppure `ipotesi`: mai presentare un'ipotesi come fatto.
> Dati sintetici: marcare `"sintetico": true` nel manifest e SINTETICO nel testo.

## 1. Riferimento
- ID opportunità: `<id>` (scheda `research/<id>.json`, stato: approvata, data approvazione `<AAAA-MM-GG>`)
- Piano di test: `<riferimento / percorso>`; ipotesi da validare: `<...>`
- Titolo di lavoro del prodotto: `<...>`; versione specifica: `<x.y.z>`
- Sintetico: `<sì/no>`

## 2. Promessa al cliente
Ogni promessa è numerata, concreta e verificabile. Niente esiti garantiti (guadagni, risultati, tempi) che non siano dimostrati.

| ID | Promessa (cosa ottiene il cliente) | Come si verifica | Evidenza / ipotesi |
|---|---|---|---|
| P1 | `<...>` | `<...>` | `<osservata: fonte+data / ipotesi>` |
| P2 | `<...>` | `<...>` | `<...>` |

## 3. Contenuto e formati dei file
| File | Formato | Scopo | Promesse coperte | Dimensione stimata |
|---|---|---|---|---|
| `<nome.ext>` | `<pdf/xlsx/zip/...>` | `<...>` | `<P1, P2>` | `<...>` |

- Struttura interna e indice: `<...>`
- Istruzioni d'uso incluse nel pacchetto: `<sì/no, dove>`
- Compatibilità (software/versioni): `<...>`

## 4. Lingua e localizzazione
- Lingua del prodotto (codice ISO): `<it, en, ...>`; lingua di partenza: `<...>`
- Adattamenti locali: valuta, formati data/numero, unità, riferimenti normativi o culturali: `<...>`
- Come è stata verificata la qualità della lingua (madrelingua / revisione AI + controllo): `<...>`

## 5. Licenze e diritti degli asset
Un'unica riga per asset. Origine ammessa: **proprio** | **licenza commerciale verificata** | **generato con AI** (indicare lo strumento). Asset con licenza non verificata: vietati.

| Asset | Origine | Licenza / prova (link, ID, data verifica) | Strumento AI (se generato) | Uso commerciale e redistribuzione |
|---|---|---|---|---|
| `<...>` | `<...>` | `<...>` | `<nome+versione o —>` | `<ammessi / limiti>` |

- Licenza con cui è venduto il prodotto: `<es. uso personale non trasferibile>`
- Diritti di terzi (marchi, persone, testi citati): `<nessuno / dettaglio>`

## 6. Manifest richiesto dal motore
File `products/<id>/manifest.json`. Campi esatti, nessun altro obbligatorio:

```json
{
  "id": "<id>",
  "versione": "<x.y.z>",
  "lingua": "<codice>",
  "licenza": "<testo o riferimento sezione 5>",
  "files": [
    {"nome": "<file>", "formato": "<ext>", "sha256": "<64 esadecimali>", "copre_promesse": ["P1"]}
  ],
  "promesse": ["P1", "P2"],
  "sintetico": false
}
```
Il checksum si calcola con `sha256sum products/<id>/files/<file>` dopo la versione finale del file.

## 7. Criteri di accettazione (verificabili dal QA)
Ciascun criterio ha esito PASS/FAIL e la prova indicata.
- [ ] **A1** Ogni promessa del manifest (`promesse`) compare in `copre_promesse` di almeno un file; nessun ID sconosciuto. Prova: confronto elenchi.
- [ ] **A2** Ogni file in `files/` è nel manifest e viceversa, con `sha256` presente (64 esadecimali) e coincidente con il file. Prova: `sha256sum`.
- [ ] **A3** Campi `id, versione, lingua, licenza, files, promesse, sintetico` presenti e non vuoti.
- [ ] **A4** Licenza e diritti documentati per ogni asset (sezione 5), nessuna origine "sconosciuta"; strumento AI indicato dove applicabile.
- [ ] **A5** Nessuna affermazione non verificata presentata come fatto: ogni dato numerico o di mercato ha fonte+data o è etichettato come ipotesi.
- [ ] **A6** Nessun dato personale (nomi, email, indirizzi, identificativi di clienti reali) nei file e nei metadati. Prova: ricerca di email/telefoni/nomi + controllo metadati dei file.
- [ ] **A7** I file si aprono nei formati dichiarati e la lingua corrisponde a `lingua`.
- [ ] **A8** Se sintetico: marcatura visibile nel prodotto e `"sintetico": true`.

## 8. Stima di ore e costo AI incrementale
| Voce | Ore | Costo AI max (€) | Nota |
|---|---|---|---|
| Specifica e struttura | `<...>` | `<...>` | |
| Produzione file | `<...>` | `<...>` | |
| Revisione e correzioni (previsto 1 giro QA) | `<...>` | `<...>` | |
| **Totale** | `<...>` | `<...>` | |

- Costo AI incrementale = solo spesa aggiuntiva di strumenti/API rispetto a quanto già riservato. Va **riservato nel registro** (`studio/ledger.py`) prima di sostenerlo.
- Soglia di escalation al Team Lead: sforzo oltre +50% del costo di sviluppo stimato, o due respingimenti QA.

## 9. Rischi per l'assistenza
Cosa è probabile che generi richieste dei clienti, e la mitigazione prevista.
| Rischio | Richiesta attesa | Mitigazione (testo nel prodotto / FAQ) | Probabilità |
|---|---|---|---|
| `<es. software non compatibile>` | `<...>` | `<...>` | `<bassa/media/alta, ipotesi>` |

Rischi fissi da valutare: download non riuscito, file non apribile, richiesta di rimborso, aspettativa di risultato non promesso, richiesta di versione in altra lingua.

---

# ESEMPIO COMPILATO — SINTETICO / ILLUSTRATIVO
> Dati inventati per mostrare la compilazione. Non è una decisione commerciale né un prodotto reale.

**1. Riferimento** — ID `syn-demo-001` (scheda sintetica approvata, 2026-11-23); piano di test `piano-demo` (ipotesi: 20 visite → 1 acquisto, ipotesi); titolo "Planner pasti settimanale (DEMO)"; versione 0.1.0; sintetico: sì.

**2. Promesse**
| ID | Promessa | Verifica | Evidenza |
|---|---|---|---|
| P1 | Un planner stampabile di 4 settimane | `planner.pdf` ha 4 pagine settimanali | ipotesi di domanda |
| P2 | Una lista della spesa modificabile | `spesa.xlsx` si apre e ha celle editabili | ipotesi di domanda |

**3. File** — `planner.pdf` (pdf, copre P1), `spesa.xlsx` (xlsx, copre P2), `LEGGIMI.pdf` (istruzioni, nessuna promessa).

**4. Lingua** — it; formati data GG/MM/AAAA, euro, unità metriche; revisione testi con controllo manuale.

**5. Licenze**
| Asset | Origine | Prova | Strumento AI |
|---|---|---|---|
| layout planner | proprio | creato internamente | — |
| font "DemoSans" | licenza commerciale verificata | licenza DEMO-123, verificata 2026-11-20 (fittizia) | — |
| icone pasti | generato con AI | — | "StrumentoAI-demo v1" |

**6. Manifest**
```json
{
  "id": "syn-demo-001",
  "versione": "0.1.0",
  "lingua": "it",
  "licenza": "uso personale non trasferibile; asset: vedi spec sez. 5",
  "files": [
    {"nome": "planner.pdf", "formato": "pdf", "sha256": "0000000000000000000000000000000000000000000000000000000000000001", "copre_promesse": ["P1"]},
    {"nome": "spesa.xlsx", "formato": "xlsx", "sha256": "0000000000000000000000000000000000000000000000000000000000000002", "copre_promesse": ["P2"]},
    {"nome": "LEGGIMI.pdf", "formato": "pdf", "sha256": "0000000000000000000000000000000000000000000000000000000000000003", "copre_promesse": []}
  ],
  "promesse": ["P1", "P2"],
  "sintetico": true
}
```
(Checksum segnaposto: in un prodotto reale vanno calcolati.)

**7. Accettazione** — A1 PASS (P1→planner.pdf, P2→spesa.xlsx); A2 PASS solo con checksum reali; A4 PASS; A5 PASS (nessuna promessa di risultati); A6 PASS; A8 PASS.

**8. Stima** — 6 h totali, costo AI incrementale max 3,00 € (riservato nel registro prima dell'uso).

**9. Rischi assistenza** — xlsx non apribile su telefono (media) → nota in LEGGIMI; stampa con margini errati (media) → istruzioni di stampa; richiesta rimborso (bassa).
