# Verifica 1 (T-020-1): B-es-planificador-oposiciones

Data: 2026-11-23. Esito: verifica NON eseguibile, nessuna evidenza nuova.

## Tentativi di lettura (tutti falliti)
Errore identico per ogni URL: `getaddrinfo ENOTFOUND <host>` (host fuori dai domini consentiti alla sessione, o rete non applicata).
- https://redopositor.com/productos/planificador-pro/
- https://payhip.com/b/ihdmv ; https://payhip.com/pricing
- https://www.etsy.com/es/search?q=planificador+oposiciones ; https://help.etsy.com/hc/en-us/articles/115015628347-Fees-Payments
- https://www.amazon.es/s?k=planificador+oposiciones
- https://www.boe.es/buscar/doc.php?id=BOE-A-2025-1
- https://gumroad.com/pricing
- https://www.shopify.com/pricing
Dopo il secondo host fallito mi sono fermato come da indicazione dell'errore. Serve aggiungere questi host ai domini di rete della sessione.

## Evidenze osservate
Nessuna. Le 4 fonti precedenti derivavano da riepiloghi WebSearch con pagine mai aperte: le ho declassate a `ipotesi`.

## Stime e ipotesi (invariate)
Prezzo 690 cent, sviluppo 2000, accesso 200, margine 5493 bp, commissioni canale; ricorrenza delle convocatorie; lacuna di prezzo 3,99-49 EUR. Domande 1-3 del compito (posti/date BOE, recensioni, regole AI dei canali): senza risposta.

## Punteggio ricalcolato
Voti: problema 5, accesso 4, margine 4, concorrenza 4, costo_sviluppo 6, assistenza 7.
5x2,5 + 4x2,0 + 4x2,0 + 4x1,5 + 6x1,0 + 7x1,0 = 12,5 + 8 + 8 + 6 + 6 + 7 = **47,5** (prima 58). Il calo e solo di prudenza: senza fonti osservate il metodo limita a 5 i voti su problema, accesso e concorrenza.

## Esito dopo D-028 (Team Lead, 2026-11-23)
Il ribasso a 47,5 e le fonti declassate a `ipotesi` sono ANNULLATI: nessuna evidenza contraria. La scheda torna al primo ciclo, con le 4 fonti `osservata` (`metodo: estratto_ricerca`) e `problema` limitato a 6 (solo estratti): voti 6/5/5/5/6/7 = **55** (primo ciclo 58). I tentativi falliti restano solo qui e in `note_punteggi`.

## Raccomandazione
**Non sviluppare** ora: sotto soglia 60 e 0 fonti osservate (servono almeno 2). Rifare la verifica appena i domini sono raggiungibili; il punteggio puo risalire solo con evidenze lette (convocatorias BOE, recensioni, commissioni).
