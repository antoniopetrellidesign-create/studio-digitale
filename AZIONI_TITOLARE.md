# Azioni riservate al titolare — elenco unico

Aggiornato il 2026-11-23. Contiene solo i passaggi che il team non può fare. Credenziali, carte, OTP e documenti si inseriscono **solo** sulle schermate ufficiali dei servizi o nel modulo sicuro dei segreti dell'ambiente Claude: mai in chat, nei file o nei commit.

## A. Subito (sbloccano il lavoro già pronto) — circa 10 minuti

| # | Servizio | Schermata | Azione | Perché serve al team |
|---|---|---|---|---|
| A1 | GitHub | github.com → **New repository** | Nome `studio-digitale`, visibilità **Private**, nessun README → Create | Salvataggio persistente: oggi il lavoro esiste solo in questo container temporaneo |
| A2 | GitHub ↔ Claude | claude.ai/connect-github | Abilitare la Claude GitHub App sul repository `studio-digitale` | Permette al team di collegare il repository e spingere i commit |
| A3 | Claude Code | nuova sessione | Avviarla con il repository `studio-digitale` selezionato, oppure scrivere al team "repository pronto" in questa sessione | Il team spinge i 3 commit esistenti e verifica il salvataggio |
| A4 | Chiave di ACCESSI_SISTEMA | terminale del tuo computer | `age-keygen -o ~/.config/studio/accessi.key` (installa `age` se manca). Conserva il file e una copia di backup offline. Comunica al team **solo** la riga `public key: age1…` | Il documento accessi si cifra con la tua chiave pubblica: solo tu puoi aprirlo, gli agenti possono solo aggiungere voci. Senza questa chiave il sistema rifiuta di conservare credenziali |

In alternativa ad A4 puoi usare la tua chiave SSH: comunica la riga pubblica `ssh-ed25519 …`.

## B. Alla fase Catalogo / Shopify (quando un prodotto supera il QA)

| # | Servizio | Schermata | Azione |
|---|---|---|---|
| B1 | Email dedicata | pagina di registrazione del provider scelto | Creare la casella completando CAPTCHA e verifica telefono; attivare la 2FA con la tua app. Se disponibile, collegarla a claude.ai come connettore, così il team legge le email di conferma |
| B2 | Shopify | admin.shopify.com → registrazione | Registrazione con l'email dedicata, verifica identità e payout, scelta del piano **dopo** che il team ha registrato il prezzo verificato e la riserva |
| B3 | Shopify | Impostazioni → App → Sviluppa app | Creare l'app personalizzata con gli scope di INTEGRAZIONI_LIVE.md e installarla; il team aprirà il modulo sicuro per salvare il token per l'host `<negozio>.myshopify.com` |
| B4 | Marketplace selezionati | registrazione venditore | Verifica identità e dati di pagamento sui marketplace che il catalogo avrà confermato con verifica osservata |

## C. Alla fase di lancio

| # | Servizio | Azione |
|---|---|---|
| C1 | Account social del prodotto validato | Creare gli account sulle piattaforme indicate dalla fase Social, con i nomi utente proposti (verifica telefono/CAPTCHA) |
| C2 | Account pubblicitario | Inserire il metodo di pagamento e impostare sulla piattaforma un limite di spesa ≤ busta Ads |
| C3 | Accordi creator | Firmare gli accordi preparati dal team |
| C4 | Revisione legale | Politica rimborsi UE per contenuti digitali e testi di checkout |
| C5 | Rete dell'ambiente | Approvare l'accesso in sola lettura ai siti ufficiali di prezzi e regole (Shopify e marketplace), che il team richiederà con il prompt dell'ambiente, per sostituire le ipotesi con dati osservati |

L'elenco operativo, generato dal registro account, si ottiene con `python3 -m studio account passaggi --fase <fase>`. Il motore aggiunge le azioni che emergono durante un run in `runs/<id>/AZIONI_TITOLARE.md`.
