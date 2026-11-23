# Calendario editoriale: `<id prodotto>`

Responsabile: social-contenuti. Metodo: `docs/social.md`. Compilare solo per prodotti VALIDATI. Stato iniziale di ogni voce: `bozza`. Nessuna pubblicazione prima della fase di lancio.

## 1. Identità
| Campo | Valore |
|---|---|
| Nome | `<dal manifest>` |
| Tono (3 aggettivi + 3 divieti) | `<...>` |
| Lingua | `<dal manifest>` |
| Elementi visivi | `<elemento: origine, licenza, data verifica>` |

## 2. Piattaforme (1 primaria, max 1 secondaria)
| Piattaforma | Ruolo | Motivazione | Evidenza (osservata: fonte+data / ipotesi) |
|---|---|---|---|
| `<...>` | primaria | `<dove si trova l'acquirente>` | `<...>` |

## 3. Calendario (minimo 4 voci; tutte le promesse coperte)
| ID | Data | Piattaforma | Formato | Tema | Promesse | Dichiarazione promo | Etichetta AI | ID link | Stato |
|---|---|---|---|---|---|---|---|---|---|
| C-01 | `<AAAA-MM-GG>` | `<...>` | `<...>` | `<...>` | `<P1>` | `<testo>` | `<si/no/non richiesta>` | `L-01` | bozza |

## 4. Link tracciati
| ID link | URL (generato con `studio/links.py`) |
|---|---|
| L-01 | `<url>?utm_source=<piattaforma>&utm_medium=social&utm_campaign=<id prodotto>&utm_content=<id contenuto>` |

## 5. Metriche (dopo il lancio)
| ID contenuto | Click tracciati | Ordini attribuiti | Costo tempo AI |
|---|---|---|---|

---
## Esempio SINTETICO (non è una decisione commerciale né un dato di mercato)
Prodotto sintetico `prod-esempio-001`, lingua `it`, promesse: P1 "checklist da 20 punti", P2 "foglio di calcolo precompilato", P3 "guida di 10 pagine".

- Identità: nome `Kit Esempio`; tono: chiaro, pratico, sobrio; mai: esiti garantiti, urgenza finta, confronti non verificati; elementi visivi: schermate del proprio file (licenza propria, verifica 2026-11-23, ipotesi sintetica).
- Piattaforma: `linkedin` (primaria), motivazione: ipotesi sintetica che l'acquirente cerchi soluzioni professionali lì.

| ID | Data | Piattaforma | Formato | Tema | Promesse | Dichiarazione promo | Etichetta AI | ID link | Stato |
|---|---|---|---|---|---|---|---|---|---|
| C-01 | 2026-12-01 | linkedin | post immagine | problema riconoscibile | P1 | Pubblicità | non richiesta | L-01 | bozza |
| C-02 | 2026-12-03 | linkedin | carosello | dimostrazione della checklist | P1 | Pubblicità | non richiesta | L-02 | bozza |
| C-03 | 2026-12-08 | linkedin | post immagine | foglio precompilato in uso | P2 | Pubblicità | non richiesta | L-03 | bozza |
| C-04 | 2026-12-10 | linkedin | post testo | domanda frequente sulla guida | P3 | Pubblicità | non richiesta | L-04 | bozza |

Link L-01: `https://negozio.example/prodotto?utm_source=linkedin&utm_medium=social&utm_campaign=prod-esempio-001&utm_content=C-01`
