# Riepilogo budget del primo test (T-026)

Data: 2026-11-23. Fonti: config/policy.json, STRATEGIA.md §3 e §3-bis, studio/ledger.py.
Legenda: [OSSERVATO] = letto nei file oggi; [REGOLA] = norma della policy; [IPOTESI] = non verificata.

## Tetto
- [OSSERVATO] Tetto complessivo del primo test: 500 € (tetto_primo_test_cents = 50000), unico e condiviso tra prodotti, strumenti, API, marketplace, Ads e creator.
- [REGOLA] Superarlo richiede l'approvazione del titolare, tramite il Team Lead.

## Allocazione per categoria (policy.json, STRATEGIA §3)
- ads 200 € | piattaforma 80 € | ai 60 € | compenso_fisso 60 € | commissione 60 € | riserva 40 €
- [OSSERVATO] Totale 500 €, uguale al tetto. Le allocazioni sono proposte [P] del §3.

## Registro comune
- [OSSERVATO] registro/primo-test.json non esiste (controllato: nemmeno la cartella registro/).
- Spesa effettiva: 0 €. Impegni aperti: 0 €. Residuo: 500 €. Sono valori per assenza del registro, non letti da un registro.

## Incassi
- [REGOLA] Ricavi, commissioni recuperate e rimborsi ricevuti non aumentano il tetto né il residuo di nessuna categoria. Entrano nel margine, non nel budget.
- [OSSERVATO] Incassi registrati: nessuno (nessun registro).

## Regola delle buste
- [REGOLA] Ogni spesa è prima riservata nel registro in una busta, con costo massimo noto e comprensivo di imposte e commissioni.
- La busta commissione creator vale al massimo 60 €. Il tetto è scritto nell'accordo con il creator. Al raggiungimento il codice creator viene sospeso.
- Una commissione maturata ma non pagata (finestra di 30 giorni) consuma il tetto. Se viene stornata per rimborso, il tetto si libera.
- Ads: soglia di stop del test non superiore al residuo ads. Tetto giornaliero e totale prenotati prima dell'avvio.
- La riserva (40 €) si sblocca solo dal Team Lead, con motivazione.

## Cosa blocca una spesa
- Costo massimo sconosciuto o non valido.
- Residuo totale o allocazione della categoria insufficienti. Nessuna compensazione tra categorie senza decisione registrata in DECISIONI.md.
- Prezzo, imposte o rinnovo non verificati con fonte e data (il costo resta sconosciuto).
- Abbonamento senza data di chiusura pianificata. Prova gratuita senza scadenza registrata o senza riserva possibile.
- Superamento di 500 € senza approvazione del titolare.
- Sospensione dal telefono: se team/sospensione.json esiste e contiene "spese": true, il registro rifiuta ogni nuova busta ("nuove spese sospese dal titolare"). Vale anche per i trasferimenti da prenotazioni. Il file è riletto a ogni chiamata.
- [OSSERVATO] Oggi team/sospensione.json non esiste, quindi nessuna sospensione attiva. Un file illeggibile è ignorato e annotato in `bloccati`.
- Nessun agente ha accesso a strumenti di pagamento.
