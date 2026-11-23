# Fonti bloccate - T-018B (consultazione 2026-11-23)

Strumento: WebFetch. WebSearch ha funzionato; WebFetch no, per nessun host provato. Per ogni pagina sotto, nessun dato e stato dedotto o sostituito da supposizioni: le schede usano solo cio che WebSearch ha riportato (marcato "metodo: WebSearch, pagina non aperta") o lo marcano ipotesi.

Errore esatto restituito (stesso testo per tutti, con l'host variabile):
`getaddrinfo ENOTFOUND <host>. In this cloud session a host fails to resolve like this when it is outside the session's allowed network domains, or does not exist.`

| URL | Host | Errore |
|---|---|---|
| https://www.finanztip.de/haushaltsbuch/ | www.finanztip.de | getaddrinfo ENOTFOUND www.finanztip.de |
| https://www.etsy.com/listing/4606059348 | www.etsy.com | getaddrinfo ENOTFOUND www.etsy.com |
| https://redopositor.com/productos/planificador-pro/ | redopositor.com | getaddrinfo ENOTFOUND redopositor.com |
| https://www.money.it/bilancio-familiare-cos-e-come-fare-excel-app | www.money.it | getaddrinfo ENOTFOUND www.money.it |
| https://payhip.com/b/ihdmv | payhip.com | getaddrinfo ENOTFOUND payhip.com |

Non tentati dopo il fallimento (istruzione dell'errore: fermarsi): altri host. Pagine ufficiali tariffe (help.etsy.com, shopify.com/pricing, gumroad.com/pricing) non aperte: le commissioni delle schede restano quelle di `config/canali_vendita.json`, cioe ipotesi.

Conseguenza: nessun numero di recensioni, vendite o volumi e stato osservato su pagina aperta. Prezzi, titoli e descrizioni provengono da riepiloghi dei risultati WebSearch.

Risultati scartati come non affidabili: pagine su `certtest.bart.gov` che si presentano come "Etsy" listing (dominio di test, licenza non verificabile).

Richiesta al Team Lead: per trasformare le fonti in osservazioni su pagina aperta servono questi host nella lista di rete consentita (sola lettura).
