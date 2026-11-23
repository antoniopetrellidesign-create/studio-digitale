# Passaggio alla nuova sessione (ambiente `studio-digitale`)

Scritto il 2026-11-23 dalla sessione precedente, che non è riuscita a raggiungere il repository: `add_repo` ha risposto "you don't have access to antoniopetrellidesign-create/studio-digitale". La nuova sessione **non** ha accesso ai file del vecchio container: tutto quello che serve sta nel bundle e in questo documento.

## 1. Ripristino (prima di tutto)
Il progetto arriva come bundle Git con tutta la cronologia. Due vie, in ordine di preferenza:

**A. Dalla pagina "Passaggio studio-digitale" su claude.ai** (non richiede caricamenti manuali). Il titolare incolla nella nuova sessione il link della pagina, che porta anche questo testo. Poi:
1. `Artifact` con `action: "read"`, l'`url` del link e `path: "studio-digitale.bundle.b64.txt"` → il file viene salvato in locale (il risultato dice dove);
2. stessa cosa con `path: "SHA256SUMS"`;
3. comandi nel repository clonato (vuoto):
```bash
base64 -d <percorso>/studio-digitale.bundle.b64.txt > /tmp/studio-digitale.bundle && sha256sum /tmp/studio-digitale.bundle
```
   Confronta l'impronta con quella in SHA256SUMS.
```bash
git fetch /tmp/studio-digitale.bundle 'refs/heads/*:refs/remotes/bundle/*' && git checkout -B main bundle/main
```
```bash
git push -u origin main
```

**B. In alternativa**: il titolare allega alla sessione il file `studio-digitale-<data>.bundle` scaricato dalla conversazione precedente, e si usano gli stessi comandi a partire dal file allegato.

**Verifica obbligatoria del ripristino**: `git log --oneline` deve mostrare lo stesso HEAD indicato in SHA256SUMS. Poi `python3 -W ignore -m unittest discover -s tests` (tutti OK) e `python3 -m studio collaudo` (12/12). Infine verifica il commit remoto (`git ls-remote origin main` uguale a HEAD) e un clone di prova in una cartella separata.

## 2. Stato del sistema
- Motore a 12 fasi, registro spese con tetto di **500 €** (spesa reale 0 €, nessun impegno), QA indipendente, coda del team. Regole in CLAUDE.md, decisioni D-001…D-031 in DECISIONI.md.
- Ricerca: 12 opportunità reali in 5 mercati, **nessuna ≥ 60** (DE 58, EN 57, IT 56, EN binder 56, ES 55). Fonti solo da estratti della ricerca web; le pagine originali non si sono potute aprire. Graduatoria in research/GRADUATORIA-2026-11-23.md, compito **T-020 bloccato** in attesa della lettura delle pagine.
- Credenziali: segreti di rete dell'ambiente. Credenziale **di prova** su `httpbin.org`, impronta attesa `0d6964cfcffd` (accessi/.continuita-httpbin).
- Regia mobile: https://claude.ai/artifact/33E6YNe5t3vRNhVTsnBJ6g (privata, database riservato al titolare). Architettura e ciclo del ponte in docs/regia.md. Ultimo battito del vecchio ponte: 2026-11-23 sera → l'app mostrerà "stato non aggiornato" finché la nuova sessione non riprende il ciclo. Versioni dei documenti nel database: rileggile con `ArtifactData list` prima di scrivere (`if_version`).
- Hook di Claude Code attivi da `.claude/settings.json` → team/eventi/ (verificati sulla 2.1.330).

## 3. Autorizzazioni del titolare in vigore
- Creare gli account strettamente necessari, solo tramite il registro account e solo alla fase che li richiede (D-017). Credenziali solo come segreti di rete o nel documento cifrato ACCESSI_SISTEMA.
- Tetto complessivo di 500 €, comprese app e infrastruttura; gli incassi non aumentano il budget.
- Nessuna pubblicazione commerciale, campagna o contatto esterno prima della fase di lancio.
- Dinieghi di sicurezza ricevuti, da non riproporre: usare altri progetti del titolare come appoggio; leggere le chiavi SSH del titolare; sondare i siti di registrazione; leggere pagine tramite proxy da script per aggirare lo strumento di lettura pagine.

## 4. Attività pendenti, in ordine
1. Ripristino e verifica (sezione 1), con push e verifica del commit remoto. Poi `regia battito` e una sincronizzazione completa dell'app.
2. **Continuità della credenziale di prova** (RUNBOOK §11): attesa `presente: True` e impronta uguale a `0d6964cfcffd`. Poi rimozione del segreto di prova di `httpbin.org`. Se nessuno strumento lo permette, chiedere al titolare: impostazioni dell'ambiente `studio-digitale` → Segreti di rete → elimina `httpbin.org`.
3. **T-020**: lettura delle pagine originali delle candidate (gli host consentiti sono nell'ambiente). Distinguere fonti lette integralmente, risultati della ricerca e informazioni non verificabili. Se nessuna raggiunge 60, ampliare la ricerca a nuove nicchie senza abbassare la soglia.
4. **Regia mobile**: riprendere il ciclo del ponte; dopo il push, valutare l'attività pianificata descritta in docs/regia.md (verificarne il costo prima di attivarla).
5. Verdetto del QA sulla regia: qa/2026-11-23-regia-mobile.md (vedi lo stato registrato lì).
