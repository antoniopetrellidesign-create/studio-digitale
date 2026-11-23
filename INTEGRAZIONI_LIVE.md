# Integrazioni da collegare e provare dal vivo

Responsabile: account-integrazioni (prima team-lead). Stato attuale: **nessuna integrazione reale collegata**; l'adattatore Shopify reale è implementato e provato contro un server locale (`tests/test_live_shopify.py`), in attesa di B2–B3 per la prova dal vivo. `studio/adapters/live.py` blocca ogni chiamata; il collaudo verifica che la modalità `live` si fermi alla prima azione esterna senza spendere.

Un'integrazione si considera pronta solo quando **tutte** le condizioni sono vere:
1. accesso concesso dal titolare (pacchetto unico);
2. credenziali nel gestore segreti dell'ambiente, lette solo dall'adattatore;
3. adattatore live implementato con la stessa interfaccia del mock e lo stesso cancello (`ExternalGate`), con ID busta obbligatorio per le azioni a pagamento;
4. prova dal vivo superata secondo la checklist sotto, con verdetto QA in `qa/`;
5. voce in DECISIONI.md che la dichiara collaudata e inserimento in `config/integrazioni_collaudate.json`.

| Integrazione | Adattatore simulato | Cosa va collegato | Prova dal vivo minima |
|---|---|---|---|
| Shopify (negozio, prodotti, file) | `MockShopify` | negozio e piano, app personalizzata con scope `read/write_products`, `read_orders`, `read/write_discounts`, `read/write_files` (no `read_customers`) | creare un prodotto in bozza, caricare il file, verificare i checksum, eliminare la bozza |
| Webhook ordini | ingest in `OrderBook` | `orders/paid`, `refunds/create`, `orders/cancelled` con verifica HMAC | ordine di test consegnato 2 volte ⇒ 1 ordine; rimborso di test ⇒ ordine rimborsato |
| Pagamenti / gateway | `MockPagamenti` | gateway in modalità test, KYC e payout completati dal titolare | ordine di test pagato e rimborsato; fee effettiva confrontata con l'ipotesi 2,9% + 0,30 € |
| Consegna digitale | `MockConsegna` | app o funzione di download con link firmato (72 h, 5 download) | download riuscito, scadenza rispettata, reinvio con invalidazione del vecchio link |
| IVA OSS | tabella sintetica `phases.IVA_BP` | aliquote verificate per paese, con fonte e data | prezzo IVA inclusa corretto in 3 paesi UE |
| Ads | `MockAds` | account pubblicitario, metodo di pagamento del titolare, limite di spesa **impostato anche sulla piattaforma** ≤ busta | campagna creata in pausa; limite giornaliero verificato; spesa letta e riconciliata con la busta |
| Creator / affiliazione | `MockCreator` | codici sconto univoci, link UTM, accordo firmato | ordine di test con codice ⇒ commissione calcolata; rimborso entro 30 giorni ⇒ storno |
| Tracciamento | eventi in `h_shopify` | pixel o eventi server-side con order_id, senza dati personali | 5 eventi ricevuti per un ordine di test |
| Costo AI | `MockAI` (costo stimato) | lettura del costo effettivo per sessione, se disponibile | confronto stima/effettivo su una fase |

Fino a quel momento ogni importo, prezzo, fee e aliquota nei fixture resta **sintetico**.

## Stato per integrazione (2026-11-23)
| Integrazione | Codice | Prova locale | Prova dal vivo |
|---|---|---|---|
| Shopify Admin (accesso, scope, prodotto DRAFT) | `studio/adapters/live_shopify.py` | sì (server finto locale) | no — servono B2, B3 |
| Webhook Shopify (HMAC) | `verifica_webhook` | sì | no |
| Marketplace | solo mock + catalogo (`config/canali_vendita.json`, fonti "ipotesi") | sì | no — servono B4 e lettura delle pagine ufficiali (C5) |
| Social | link UTM reali (`studio/links.py`), account solo al lancio | sì | no — C1 |
| ACCESSI_SISTEMA | `studio/vault.py` (age) | sì (chiave di prova) | no — serve A4 |
