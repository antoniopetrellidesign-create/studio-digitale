# V2 sintesi 1 (T-032-1, fase c, metodo v2) - 2026-11-27

Dieci schede `research/V2-<id>.json`, `sintetico: false`. Il motore ricalcola i totali; qui i punteggi sono la somma pesata dei voti (problema 20, accesso 20, offerta 15, margine 15, concorrenza 15, sviluppo 8, assistenza 7).

## Limite comune delle fonti
Le pagine lette sono ricerche Amazon: mostrano soprattutto **libri fisici** (brossura, rilegato, qualche Kindle). Provano domanda e disponibilita a pagare, **non vendite di prodotti digitali** (fogli Excel, piani di studio, kit documentali). Nessuna scheda ha dati di vendita. Prezzi Amazon.de/.es mostrati in USD o EUR secondo la consegna impostata nella pagina: riportati come letti.

## Graduatoria
| # | Scheda | Totale | Fonte letta | Nota |
|---|---|---|---|---|
| 1 | V2-T031-3-44 food cost DE | 65,3 | si | Unico sopra 60 con fonte letta pertinente |
| 2 | V2-T031-1-007 QM/ISO 9001 DE | 60,0 | si | Sul bordo; titoli "ISO 9001:2026" osservati, norma non letta |
| 3 | V2-T031-1-052 food cost EN | 59,3 | si | Prezzi digitali concorrenti 19-39 USD solo da estratto |
| 4 | V2-T031-3-45 food cost IT | 58,3 | no | Tetto 6 su problema/concorrenza |
| 5 | V2-t031-2-01 Einbuergerungstest DE | 57,8 | si | Catalogo ufficiale gratuito, 14+ libri a 13-26 USD |
| 6 | V2-T031-1-026 food cost ES | 56,8 | si | Un solo risultato su Amazon.es (libro a 23 EUR) |
| 7 | V2-T031-1-034 Qualiopi FR | 55,0 | no | Garanzia d'audit insostenibile; solo rimborso |
| 8 | V2-t031-2-19 Policia Local ES | 53,2 | si | Sviluppo per comunita costoso |
| 9 | V2-t031-2-18 Auxiliar Administrativo ES | 49,5 | si | Saturo, margine 3351 bp |
| 10 | V2-t031-2-13 patente nautica IT | 49,2 | no | Sviluppo alto, nessuna prova libri |

Motivazione: la famiglia food cost ha sviluppo basso (stesso nucleo Excel in 4 lingue), assistenza semplice, offerta misurabile (food cost % per 10 piatti) e margine ipotizzato 5.500-6.200 bp. Gli esami hanno domanda forte ma mercato saturo di libri economici e sviluppo/aggiornamento costosi. La conformita ha margine migliore ma richiede competenza e nessuna garanzia di esito.

## Sintesi di famiglia: food cost / calcolo ricette (4 lingue)
Una famiglia, una scheda per lingua (metodo par. 8: ogni mercato si rifa con fonti locali).
- DE (65,3): fonte letta con libri Gastro + Excel-Tools a 58-62 USD (32-44 valutazioni). Migliore mercato su disponibilita a pagare e offerta a 69 EUR.
- EN (59,3): offerta piu bassa: concorrenti digitali a 19-39 USD (estratto) contro 49 EUR; titoli forti (441 valutazioni).
- IT (58,3): nessuna fonte letta; solo estratto Payhip.
- ES (56,8): solo un titolo su Amazon.es (23 EUR); pagina letta ma poco informativa.
Nucleo condivisibile: stesso foglio (schede ricetta, food cost % per piatto, menu engineering, 3 menu di esempio) localizzato per lingua, IVA e termini. Prima prova consigliata: DE; secondo: IT/EN come estensione solo se la DE converte. Nessuna lingua e candidata: manca la seconda fonte osservata indipendente per mercato.

## Offerte proposte (39-99 EUR)
Food DE/IT 69, EN 49, ES 59; Einbuergerungstest 49; Policia Local 49; Auxiliar 39; patente nautica 59; ISO 9001 79; Qualiopi 89. Promesse misurabili sull'uso del prodotto (calcolo di 10 piatti, completamento di 3 simulazioni, matrice dei 32 indicatori), mai sul risultato esterno (ricavi, esame superato, certificazione). Garanzia: rimborso 30 giorni a condizione verificabile; r* teorico 46-96% (STRATEGIA.md par. 9.3), tasso reale da misurare. Nessuna urgenza finta.

## Evidenze, stime, ipotesi
- **Evidenze (osservate, pagina letta il 2026-11-27, file in `research/fonti/`)**: numero di risultati, titoli, prezzi, valutazioni e formati di 7 pagine Amazon (DE x3, EN, ES x3). Non provano vendite di digitali.
- **Evidenze deboli (osservate, solo risultato di ricerca)**: prezzi Payhip, TestHelden 69-99 EUR, Preparaoposiciones 79 EUR, Certiforma 279 EUR, corsi nautica 210-500 EUR, OpositaTest. Pagine non lette.
- **Stime (calcolo su ipotesi)**: margini in bp con IVA del paese, commissione 2,9% + 30 cent, accesso 2000 cent per ordine (scenario STRATEGIA.md par. 9.4), prima di rimborsi e ammortamento sviluppo.
- **Ipotesi**: prezzi proposti, costo di sviluppo, tempi di compilazione, tasso di rimborso, canali e costo d'accesso, requisiti della norma ISO 9001:2026, licenze delle domande ufficiali.

## Segnalazioni per il Team Lead
1. Einbuergerungstest: cittadinanza e vicino al legale; il prodotto prepara solo al test. Servono licenza delle domande BAMF e conferma di escalation.
2. Qualiopi: conformita nel settore formazione; nessuna promessa di esito audit.
3. Pagine non lette per IT food, nautica e Qualiopi: se la fase c prosegue, leggere pagine locali (host consentiti) per sbloccare il tetto 6.
4. Nessuna scheda raggiunge i 2 criteri di candidatura (>=60 con 2 fonti osservate indipendenti); QM DE arriva a 60,0 ma con una sola fonte letta e senza verifica della norma.
