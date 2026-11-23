# Ripristino del progetto

La copia di sicurezza è composta da tre file con la stessa data:

| File | Contenuto |
|---|---|
| `studio-digitale-<data>.bundle` | repository Git completo, con **tutta la cronologia** |
| `studio-digitale-<data>.tar.gz` | istantanea dei file all'ultimo commit (agenti, configurazioni, codice, documenti, test) |
| `SHA256SUMS` | impronte per verificare che i file non siano corrotti |

Non contiene credenziali, token, chiavi private né dati personali: la cronologia è stata controllata prima di crearla. Non contiene nemmeno `runs/`, cioè gli stati delle simulazioni, che si rigenerano.

## 1. Verificare i file
```bash
sha256sum -c SHA256SUMS
```

## 2. Ripristinare dal bundle (consigliato: conserva la cronologia)
```bash
git clone studio-digitale-<data>.bundle studio-digitale
```
```bash
cd studio-digitale && git log --oneline
```

## 3. Controllare che il sistema funzioni
Serve Python 3.11 o successivo; non ci sono dipendenze da installare. `age` serve solo per ACCESSI_SISTEMA.
```bash
python3 -m unittest discover -s tests
```
```bash
python3 -m studio collaudo
```
Atteso: tutti i test `OK` e tutti i casi di collaudo `PASS`.

## 4. Pubblicare in un repository privato dedicato
Su github.com crea un repository **privato** vuoto, senza README. Poi, dalla cartella ripristinata:
```bash
git remote add origin https://github.com/<utente>/<repository>.git
```
```bash
git push -u origin --all
```
Per farlo usare a Claude Code: claude.ai/connect-github → abilitare la Claude GitHub App **solo** su quel repository (permessi: Contents read/write, Pull requests read/write), poi avviare una sessione con quel repository selezionato.

## 5. Alternativa senza Git
```bash
mkdir studio-digitale && tar -xzf studio-digitale-<data>.tar.gz -C studio-digitale
```
