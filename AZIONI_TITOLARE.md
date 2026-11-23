# Azioni riservate al titolare e blocchi — elenco unico

Aggiornato il 2026-11-23. Credenziali, carte, OTP e documenti si inseriscono **solo** sulle schermate ufficiali o nel modulo sicuro dei segreti dell'ambiente Claude: mai in chat, nei file o nei commit.

## Da fare adesso (due passaggi, circa 10 minuti)

**R1 — Repository privato dedicato.** È l'unica azione che sblocca subito qualcosa: il salvataggio su GitHub.
1. github.com → **New repository** → nome `studio-digitale`, **Private**, senza README → Create.
2. https://claude.ai/connect-github → abilitare la Claude GitHub App **solo** sul repository `studio-digitale`. Permessi richiesti: *Contents* lettura/scrittura, *Pull requests* lettura/scrittura, *Metadata* lettura.
3. Scrivere al team "repository pronto". Il team collega il repository, spinge l'intera cronologia e verifica il salvataggio.

Fino ad allora la copia di sicurezza è quella scaricabile già consegnata in conversazione (bundle + archivio + RIPRISTINO.md).

**R2 — Nuova sessione sull'ambiente `studio-digitale`** (da avviare dopo R1, con il repository `studio-digitale` selezionato).
- Perché: lo strumento di lettura pagine prende gli host approvati solo in una macchina nuova, e la verifica delle prime tre opportunità ne ha bisogno. La nuova sessione serve anche come **prova di continuità** delle credenziali dopo il riavvio: il team rilancia la verifica sull'eco e confronta l'impronta salvata (`0d6964cfcffd`).
- Dove: claude.ai/code → nuova sessione → menu ambiente nella barra del titolo → `studio-digitale`.
- Dopo la prova: eliminare la credenziale di prova di `httpbin.org` dai Segreti di rete dell'ambiente.

## 1. Limiti tecnici verificati

| Limite | Operazione impedita | Verifica | Soluzione supportata |
|---|---|---|---|
| `gh` nella sessione non ha un token valido | creare repository GitHub dalla sessione | `gh auth status` → "token invalid" | R1: il titolare crea il repository, la GitHub App dà l'accesso |
| Lo strumento di lettura pagine usa le regole di rete con cui è partita la macchina | leggere le pagine sugli host appena approvati, in questa sessione | `getaddrinfo ENOTFOUND` su tutti gli host approvati (T-020) | R2: nuova sessione sull'ambiente `studio-digitale` |
| Lettura delle pagine tramite proxy da comandi della sessione | aggirare il limite qui sopra | negata dal controllo di sicurezza della sessione (rispettata) | R2 |
| Lo strumento di lettura pagine rifiuta reddit.com | leggere discussioni Reddit | messaggio "unable to fetch from www.reddit.com" (non è un blocco di rete) | usare i risultati della ricerca web e altri forum; nessuna azione del titolare |
| Registrazioni email e social con CAPTCHA e/o verifica telefono | creare la casella dedicata e gli account social | requisiti delle piattaforme; la sessione non ha browser né telefono | il titolare crea gli account alla loro fase (B1, C1); il team prepara nomi, testi e configurazione |
| Nessuna casella email collegata | leggere le email di conferma delle registrazioni | nessun connettore email disponibile | dopo B1, collegare la casella come connettore claude.ai, se disponibile |
| ACCESSI_SISTEMA non è leggibile dagli agenti (scelta di sicurezza voluta) | — | cifratura asimmetrica | solo il titolare decifra, con la propria chiave |

## 2. Autorizzazioni mancanti

| Autorizzazione | Operazione impedita | Soluzione supportata | Quando |
|---|---|---|---|
| Repository dedicato + GitHub App | salvataggio persistente su GitHub | R1 | **ora** |
| Account Shopify, gateway e app personalizzata | negozio e prova dal vivo dell'adattatore | B2–B3 | quando un prodotto supera QA e catalogo |
| Account venditore sui marketplace selezionati | pubblicazione sui marketplace | B4 | fase Catalogo / lancio |
| Account social e pubblicitario, accordi creator | distribuzione | C1–C3 | fase di lancio |
| ~~Rete per le fonti della ricerca~~ | ~~aprire le pagine delle fonti~~ | **risolta**: approvato l'ambiente personale `studio-digitale` con 15 host consentiti | — |

Dinieghi di sicurezza ricevuti e rispettati (non vengono riproposti):
- uso del repository privato di un altro tuo progetto come appoggio;
- lettura delle tue chiavi SSH pubbliche su GitHub;
- sondaggio della raggiungibilità dei siti di registrazione.

## 3. Scelte progettuali modificabili

| Scelta | Effetto | Alternativa possibile |
|---|---|---|
| Credenziali operative come **segreti di rete** dell'ambiente (legati all'host, mai visibili agli agenti, persistenti) | le integrazioni si autenticano senza che nessuno veda il valore | variabili d'ambiente (sconsigliate: leggibili dai comandi della sessione) |
| Copia di recupero ACCESSI_SISTEMA cifrata con una tua chiave `age` | serve solo quando esisterà il primo account con password; **non** blocca ricerca e sviluppo | la tua chiave SSH pubblica, oppure il gestore di password che già usi |
| Nessun account prima della fase che lo richiede | zero costi fissi prima della validazione | attivazione anticipata, ad esempio dell'email (costo 0, ma registrazione manuale) |
| Selezione solo con punteggio ≥ 60 e ≥ 2 fonti osservate indipendenti | nessun prodotto selezionato nel primo ciclo | soglia diversa, con una decisione registrata |
| Host consentiti uno per uno (massimo 20, niente wildcard) | ogni fonte nuova richiede un'aggiunta | accesso di rete più ampio, da impostare nelle impostazioni dell'ambiente |
| Credenziale **di prova** su `httpbin.org` | serve solo alla prova di continuità | va eliminata dopo la prova nel prossimo riavvio, dalle impostazioni dell'ambiente (Segreti di rete) |

## Passaggi alle fasi successive (non ora)

| # | Servizio | Schermata | Azione |
|---|---|---|---|
| B1 | Email dedicata | registrazione del provider | creare la casella con CAPTCHA e verifica telefono, poi attivare la 2FA |
| B2 | Shopify | admin.shopify.com | registrazione con l'email dedicata, verifica identità e payout; piano scelto dopo che il team ha registrato il prezzo verificato e la riserva |
| B3 | Shopify | Impostazioni → App → Sviluppa app | app personalizzata con gli scope di INTEGRAZIONI_LIVE.md; token salvato nel modulo sicuro aperto dal team per l'host `<negozio>.myshopify.com` |
| B4 | Marketplace selezionati | registrazione venditore | verifica identità e dati di pagamento |
| C1 | Social del prodotto validato | registrazione | creare gli account con i nomi utente proposti |
| C2 | Account pubblicitario | metodi di pagamento | carta e limite di spesa ≤ busta Ads |
| C3 | Accordi creator | — | firma |
| C4 | Revisione legale | — | politica rimborsi UE e testi di checkout |

Elenco generato dal registro: `python3 -m studio account passaggi --fase <fase>`.
