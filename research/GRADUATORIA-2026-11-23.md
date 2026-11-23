# Graduatoria opportunità — primo ciclo di ricerca reale (2026-11-23)

Autori: ricerca-mercato (due esecuzioni indipendenti, A e B). Punteggi ricalcolati dal motore (`studio/phases.punteggio`) e schede validate (`valida_opportunita`): nessun errore. Tutte le schede hanno `"sintetico": false`.

## Metodo e limiti di questo ciclo
- **Evidenze osservate**: 38 fonti (21 in A, 17 in B), tutte consultate il 2026-11-23 tramite **ricerca web** (titolo, URL, estratto). Nessuna pagina è stata aperta: l'apertura diretta è fallita su tutti gli host provati (`research/fonti-bloccate.md`, `research/fonti-bloccate-B.md`).
- **Stime**: margini e costi di sviluppo, dedotti dalle evidenze. **Ipotesi**: prezzi di vendita, commissioni dei canali (da `config/canali_vendita.json`, non verificate), cambio USD/EUR.
- Conseguenza: i criteri *problema/urgenza* e *concorrenza superabile* restano prudenti (≤ 6), perché recensioni negative, lamentele e ampiezza reale dell'offerta non si possono leggere. Per questo nessuna nicchia raggiunge 60.

## Graduatoria (punteggi del motore dopo D-028)

| # | Opportunità | Mercato | Punteggio | Fonti osservate | Prezzo ipotizzato | Sintesi |
|---|---|---|---|---|---|---|
| 1 | Haushaltsbuch (registro delle spese domestiche) | DE | **58** | 3 | 12,90 € | Domanda costante e abitudine culturale; mercato affollato di app e modelli gratuiti; differenziazione possibile solo con un formato specifico |
| 2 | Language learning planner | EN/US | **57** | 2 | 7,90 € | Domanda osservata su marketplace; molti concorrenti economici |
| 3 | Bilancio familiare | IT | **56** | 3 | 9,90 € | Offerta italiana meno affollata di quella inglese; molti modelli gratuiti di banche e app |
| 4 | Home maintenance binder | EN/US | 56 | 2* | 9,90 € | *Le 2 fonti vengono dallo stesso sito: indipendenti = 1, non rispetta il minimo di 2 fonti |
| 5 | Planificador de oposiciones | ES | 55 | 4 | 6,90 € | Problema forte e ricorrente; osservato un prodotto a pagamento da 49 € in lista d'attesa. Era 58 con problema 7: D-028 limita il criterio a 6 finché si hanno solo estratti di ricerca |
| 6 | Freelance tracker | EN/US | 54 | 4 | 12,00 € | Saturo; forti alternative gratuite |
| 7 | Calcolatore prezzi per venditori handmade | EN/US | 54 | 4 | 10,00 € | Concorrenza da software in abbonamento e strumenti gratuiti |
| 8 | Welcome book per affitti brevi | EN/US | 53 | 4 | 12,00 € | Gli strumenti delle piattaforme di gestione lo includono gratis |
| 9 | Gästemappe Ferienwohnung | DE | 53 | 4 | 12,00 € | Come la #8, mercato tedesco |
| 10 | Classeur administratif | FR | 52 | 3 | 12,90 € | Rischio di sconfinare in indicazioni legali |
| 11 | Calendario editoriale social | EN/US | 52 | 2 | 8,00 € | Molto saturo |
| 12 | Angebot/Rechnung Kleinunternehmer | DE | 47 | 3 | 10,00 € | Tocca fisco e fatturazione: categoria sospesa |

"Fonti osservate" = estratti della ricerca web con URL e data (D-028); nessuna pagina è stata aperta.

Nicchie scartate prima della scheda: piani di viaggio DE/EN/IT (offerta gratuita di grandi marchi o dipendenza da una sola piattaforma), Hausakte DE (nessun prodotto a pagamento osservato), kit salute FR (categoria regolamentata), autonomi/forfettari IT-ES-FR (fisco). Dettagli in `A-sintesi.md` e `B-sintesi.md`.

## Decisione (DECISIONI.md D-027)
- **Nessun prodotto selezionato** in questo ciclo: nessuna opportunità raggiunge la soglia approvata di 60 con almeno 2 fonti osservate indipendenti. La soglia **non** viene abbassata.
- Entrano nel **ciclo di verifica** DE Haushaltsbuch, EN language planner, IT bilancio familiare ed ES oposiciones (quest'ultima per il problema più forte osservato; la #4 è esclusa perché ha una sola fonte indipendente). Con l'apertura diretta delle pagine si leggono recensioni negative, si contano e prezzano i concorrenti reali e si verificano le commissioni dei canali. Se una delle quattro supera 60, diventa il primo prodotto da sviluppare.
- Canali previsti per una candidata che passa: sito/Shopify più un marketplace idoneo dal catalogo; creator della nicchia; contenuti organici. I social si preparano solo dopo la validazione (fase Social).

## Ciclo di verifica (T-020) — NON eseguito
- Tutti e tre i verificatori hanno trovato lo strumento di lettura pagine ancora bloccato (`getaddrinfo ENOTFOUND`), anche sugli host appena approvati nell'ambiente `studio-digitale`. Le regole di rete nuove valgono per le richieste che passano dal proxy, mentre lo strumento di lettura pagine si aggiorna solo con una **nuova sessione** sull'ambiente. Una lettura diretta tramite proxy è stata negata dal controllo di sicurezza della sessione e non è stata riproposta.
- Senza nuove evidenze i verificatori hanno ricalcolato i punteggi al ribasso "per prudenza": ES oposiciones 58 → 47 (fonti degli estratti declassate a ipotesi), DE Haushaltsbuch 58 → 52, EN language planner 57 → 50.
- **Decisione del Team Lead (D-028)**: un ribasso senza evidenze contrarie non è un risultato della verifica. La graduatoria di riferimento resta quella del primo ciclo; i nuovi valori sono annotati come ribassi prudenziali in attesa della verifica. Regola resa uniforme: gli estratti della ricerca web con URL e data valgono come fonte "osservata" di tipo *estratto*, ma con i soli estratti *problema* e *concorrenza* non superano 6. Quindi nessuna candidata può superare 60 senza leggere le pagine.
- Applicata la regola (T-023): i ribassi annullati; ES scende a 55 per il limite di 6 su *problema*. La graduatoria sopra è quella aggiornata.
- Prossimo passo: rieseguire T-020 in una nuova sessione sull'ambiente `studio-digitale`.
