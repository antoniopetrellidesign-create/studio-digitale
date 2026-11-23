# Verifica 2 - Haushaltsbuch DE (T-020-2), 2026-11-23

## Esito dell'accesso alle fonti
Tutte le WebFetch tentate sono fallite con errore esatto `getaddrinfo ENOTFOUND <host>`:
- https://www.etsy.com/de/search?q=haushaltsbuch+vorlage+pdf -> ENOTFOUND www.etsy.com
- https://www.amazon.de/s?k=haushaltsbuch -> ENOTFOUND www.amazon.de
- https://www.finanztip.de/haushaltsbuch/ -> ENOTFOUND www.finanztip.de

Gli host risultano fuori dai domini di rete consentiti della sessione (nonostante l'elenco indicato nel compito). Come da indicazione dell'errore, non ho provato altri siti. Va verificata la configurazione di rete.

## Evidenze (osservate in questo ciclo)
Nessuna. Prezzi, numero di recensioni, lamentele nelle recensioni negative e app/alternative gratuite NON sono stati letti.

## Evidenze preesistenti (WebSearch, pagine non aperte, date 2026-11-23)
- Etsy DE: molte inserzioni di download istantaneo; Finanzplaner a 38,16 EUR; bundle a CHF 4,73.
- Digistore24: Vorlage Excel a 5,88 EUR.
- Finanztip e C&A: modelli gratuiti.

## Ipotesi
Prezzo 12,90 EUR, sviluppo 15 EUR, accesso 2 EUR/vendita, commissioni Etsy 950 bp + 45 cent, bisogno scoperto (formato a buste/categorie per famiglia: dalla graduatoria, non verificato da recensioni).

## Differenziazione
Non determinabile: senza recensioni negative lette, il bisogno scoperto resta ipotesi.

## Punteggio (pesi 25/20/20/15/10/10)
| Criterio | Prima | Ora | Motivo |
|---|---|---|---|
| problema | 6 | 5 | nessun volume o recensione letti |
| accesso | 5 | 4 | costo acquisizione non verificato |
| margine | 6 (era 7) | 6 | prezzi bassi osservati, commissioni non verificate |
| concorrenza | 3 | 3 | gratuiti noti + offerta a basso prezzo |
| costo_sviluppo | 8 | 8 | invariato (ipotesi) |
| assistenza | 7 | 7 | invariato (ipotesi) |

Calcolo: 5*25 + 4*20 + 6*20 + 3*15 + 8*10 + 7*10 = 520 -> **52,0** (prima 58,5). Sotto la soglia 60.

## Raccomandazione
Non sviluppare. Il punteggio scende per mancanza di evidenze, non per prove contrarie. Se la rete verrà abilitata a etsy.com, amazon.de e finanztip.de, ripetere la verifica (recensioni negative, prezzi, volumi) prima di archiviare definitivamente. Restano esclusi consigli finanziari, fiscali e di investimento.
