# Azioni riservate al titolare — pacchetto unico per il lancio

Da eseguire **in un'unica sessione**, quando si decide di passare alla fase commerciale. In questa sessione di collaudo non è richiesta alcuna azione.

**Regola:** credenziali, numeri di carta, OTP e documenti d'identità si inseriscono solo sul sito del servizio o nel gestore segreti dell'ambiente. Non vanno mai incollati in chat, nei file o nei commit.

| # | Azione | Perché serve | Sblocca |
|---|---|---|---|
| 1 | Creare il negozio Shopify e scegliere il piano. Comunicare al team solo il **costo massimo mensile** | La fase Shopify richiede un costo di piattaforma noto | `--concedi shopify` |
| 2 | Verifica dell'identità e configurazione dei payout sul gateway di pagamento | Incasso reale e rimborsi | ordine di prova reale |
| 3 | Creare l'app personalizzata con gli scope in INTEGRAZIONI_LIVE.md e salvare il token nel gestore segreti dell'ambiente | Accesso dell'adattatore senza esporre il token | adattatore Shopify live |
| 4 | Account pubblicitario con metodo di pagamento e **limite di spesa sulla piattaforma ≤ 200 €** (allocazione Ads) | Doppia protezione oltre al registro | canale Ads |
| 5 | Confermare (o modificare) il tetto di 500 € e l'allocazione per categoria in `config/policy.json` | Il registro non accetta cambi di tetto senza decisione | registro del primo test |
| 6 | Decidere la finestra di clawback per i creator (30 giorni proposti; strategia-finanza suggerisce di valutare 45–60) | Condizione contrattuale | accordi creator |
| 7 | Revisione legale della politica rimborsi UE per contenuti digitali e dei testi di checkout (consenso all'esecuzione immediata) | Conformità | pubblicazione della scheda |
| 8 | Dominio (facoltativo) | Fiducia, tracciamento | — |

Il motore aggiunge automaticamente in `runs/<id>/AZIONI_TITOLARE.md` le azioni che emergono durante un run (es. accesso Shopify mancante, nuovo tetto per scalare); il team-lead le riporta qui raggruppate.
