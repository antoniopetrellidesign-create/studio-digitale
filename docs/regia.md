# Regia mobile — architettura e operatività

Responsabile: team-lead. App: `app/regia.html`, pubblicata come pagina privata claude.ai (https://claude.ai/artifact/33E6YNe5t3vRNhVTsnBJ6g).

## Architettura
```
Telefono (pagina privata claude.ai, login del titolare, HTTPS)
   │  legge: sistema/stato, squadra/{agenti,lavori,prodotti}, consegne/indice, testi/*, comandi/*
   │  scrive: comandi/<id>   (stato "inviato", id univoco riusato ai tentativi ripetuti)
   ▼
Database della pagina (persistente; regola: lettura e scrittura solo al titolare)
   ▲
   │  ponte = una sessione Claude Code attiva (ArtifactData)
   │   1. legge i comandi "inviati" → li segna "ricevuto" → "in_esecuzione"
   │   2. python3 -m studio regia comando --file <comando>   (idempotente per id)
   │   3. scrive l'esito confermato dal motore → "completato" o "fallito"
   │   4. python3 -m studio regia battito && python3 -m studio regia esporta [--consegne]
   │   5. scrive i documenti con if_version (nessuna sovrascrittura cieca)
   ▼
Motore (studio/): coda, registro spese, workflow, eventi reali degli hook (team/eventi/)
```

## Fonti dei dati (nessun dato inventato)
| Dato | Fonte |
|---|---|
| Ruoli e reparti | `.claude/agents/*.md`: un file è una **definizione**, non un processo attivo |
| Esecuzioni, attività, strumenti | hook di Claude Code → `team/eventi/AAAA-MM-GG.jsonl`, oscurati (`studio/hooks/registra_evento.py`) |
| Lavori, priorità, blocchi, passaggi fra reparti | `team/queue.json`: un passaggio compare solo se una dipendenza fra agenti diversi è registrata ed è conclusa |
| Decisioni | `DECISIONI.md` |
| Numeri | registro comune `registro/primo-test.json` (oggi assente: 0 €); le simulazioni sono escluse |
| Prodotti | `research/*.json` |
| Servizi | `config/integrazioni_collaudate.json` (oggi nessuno collegato) |

## Stati degli agenti
`in_esecuzione` (avvio senza fine, eventi recenti e ponte attivo) · `concluso` (evento di fine registrato) · `in_attesa` (compito in coda) · `bloccato` (compito bloccato) · `sconosciuto` (avvio senza fine ma nessun evento recente, oppure ponte scaduto) · `mai_avviato_registrato` (solo definizione). La sessione principale è il team-lead.

Compatibilità degli hook verificata in pratica su Claude Code 2.1.330 (DECISIONI.md D-030): PreToolUse, PostToolUse, PostToolUseFailure, SubagentStart e SubagentStop arrivano con `agent_id` e `agent_type` anche dai subagenti, e vengono ricaricati a sessione in corso. Gli eventi precedenti all'attivazione degli hook non esistono: le esecuzioni dei giorni scorsi risultano solo dalla coda.

## Comandi
`obiettivo`, `priorita`, `revisione`, `sospendi`, `riprendi`, `risposta`. La pagina scrive solo "inviato"; ogni altro stato lo scrive il ponte dopo l'esito del motore. Un id già eseguito restituisce l'esito registrato con `duplicato: true`, senza un secondo effetto.

Sospensione (`team/sospensione.json`):
- nuove riserve e trasferimenti da prenotazioni rifiutati dal registro;
- nessuna nuova fase del workflow;
- nessun compito messo `in_corso`;
- spesa Ads discrezionale in pausa;
- gli impegni già assunti restano.

L'app mostra separatamente: campagne esterne attive, impegni già assunti, arresti non confermati.

## Dove gira il motore (continuità)
| Situazione | Cosa succede oggi |
|---|---|
| Telefono chiuso, sessione Claude attiva | il motore e il ponte continuano finché la sessione resta attiva |
| Sessione terminata o container riciclato | **il motore si ferma**. L'app lo mostra: dopo 10 minuti senza battito compare "Stato non aggiornato" e le animazioni si fermano |
| Comandi inviati a motore fermo | restano "inviato" nel database: nulla viene perso né eseguito finché un ponte non si ricollega |

**Operatività continua: non disponibile oggi.** Serve:
1. **R1**: repository privato dedicato `studio-digitale`, perché una sessione nuova possa avere il codice;
2. un'attività pianificata (scheduled task) di Claude Code sull'ambiente `studio-digitale` che apra una sessione a intervalli, per esempio ogni ora (il minimo consentito), ed esegua il ciclo del ponte. Prompt pronto qui sotto.

Costo dell'attività pianificata: nessuna voce in euro separata osservata; consuma l'uso del piano Claude. Il suo costo AI non è misurabile da qui e resta da verificare.

Prompt dell'attività pianificata (da attivare dopo R1):
> Nel repository studio-digitale esegui il ciclo del ponte della regia descritto in docs/regia.md, passi 1–5, sull'artifact indicato. Esegui solo comandi presenti nel database con stato "inviato". Poi `git commit` e push delle modifiche a team/ e runs/regia/ non ignorati. Invia una notifica solo per blocchi importanti, consegne o richieste del titolare.

## Notifiche
Si inviano dal ponte con le notifiche dell'app Claude (strumento PushNotification), per blocchi importanti, consegne e richieste indispensabili. Il telefono le riceve solo con il consenso alle notifiche dell'app Claude e se la piattaforma le recapita: la prima del 2026-11-23 risulta "richiesta", non "consegnata".

## Installazione
La pagina non è una PWA completa: la piattaforma non consente i service worker, quindi niente uso offline né installazione con manifest. Si aggiunge alla schermata Home come collegamento:
- **iPhone**: Safari → Condividi → Aggiungi alla schermata Home;
- **Android**: Chrome → ⋮ → Aggiungi a schermata Home.
