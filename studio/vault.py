"""ACCESSI_SISTEMA: documento accessi cifrato, scrivibile dagli agenti, leggibile solo dal titolare.

Cifratura asimmetrica con `age` verso le chiavi PUBBLICHE del titolare (config/accessi_destinatari.txt):
  - gli agenti cifrano nuove voci ma non possono decifrarle (la chiave privata resta al titolare);
  - nessun testo in chiaro tocca il disco: il JSON passa da stdin a `age`;
  - ogni creazione/modifica/revoca è una nuova voce datata (storia completa, append-only);
  - l'indice `accessi/INDICE.md` contiene solo dati non sensibili e riferimenti `segreto://servizio/campo`.
Il titolare ricostruisce il documento completo con:
  python3 -m studio accessi esporta --identita <file chiave privata age o ssh>
Responsabile: account-integrazioni.
"""
from __future__ import annotations

import json
import os
import secrets
import string
import subprocess
from datetime import datetime, timezone

CAMPI_SEGRETI = ("email", "utente", "password", "token", "codici_recupero", "domande_recupero", "chiave_api")
CAMPI_INDICE = ("funzione", "url_accesso", "autenticazione", "titolare", "recupero", "stato_verifica",
                "piano", "costo", "scadenza", "rinnovo", "integrazioni", "permessi", "posizione_codici_recupero")


class VaultNonConfigurato(Exception):
    pass


def genera_password(lunghezza: int = 28) -> str:
    """Password casuale con generatore crittografico (modulo `secrets`). Non va mai stampata o registrata."""
    alfabeto = string.ascii_letters + string.digits + "-_.!@#%^*+="
    while True:
        p = "".join(secrets.choice(alfabeto) for _ in range(lunghezza))
        if (any(c.islower() for c in p) and any(c.isupper() for c in p) and any(c.isdigit() for c in p)
                and any(not c.isalnum() for c in p)):
            return p


class Vault:
    def __init__(self, cartella: str, destinatari_path: str):
        self.cartella = cartella
        self.destinatari_path = destinatari_path
        os.makedirs(os.path.join(cartella, "voci"), exist_ok=True)

    def destinatari(self) -> list:
        if not os.path.exists(self.destinatari_path):
            return []
        with open(self.destinatari_path, encoding="utf-8") as f:
            righe = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        return [r for r in righe if r.startswith(("age1", "ssh-ed25519 ", "ssh-rsa "))]

    def registra(self, servizio: str, azione: str, dati: dict) -> dict:
        """Cifra una voce (creazione | modifica | revoca | verifica) e aggiorna l'indice senza segreti."""
        dest = self.destinatari()
        if not dest:
            raise VaultNonConfigurato("nessuna chiave pubblica del titolare in " + self.destinatari_path +
                                      ": nessuna credenziale può essere conservata finché non viene fornita")
        quando = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        voce = {"servizio": servizio, "azione": azione, "quando": quando, **dati}
        out = os.path.join(self.cartella, "voci", f"{quando}-{servizio}-{azione}.age")
        cmd = ["age", "--armor", "-o", out]
        for d in dest:
            cmd += ["-r", d]
        subprocess.run(cmd, input=json.dumps(voce, ensure_ascii=False).encode(), check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        self._aggiorna_indice(servizio, azione, quando, dati)
        return {"voce": os.path.relpath(out, self.cartella),
                "riferimenti": [f"segreto://{servizio}/{k}" for k in dati if k in CAMPI_SEGRETI]}

    def _aggiorna_indice(self, servizio, azione, quando, dati):
        p = os.path.join(self.cartella, "indice.json")
        idx = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
        r = idx.setdefault(servizio, {})
        r.update({k: v for k, v in dati.items() if k in CAMPI_INDICE})
        r["ultima_azione"] = azione
        r["aggiornato"] = quando
        r["segreti"] = sorted(set(r.get("segreti", [])) | {f"segreto://{servizio}/{k}" for k in dati if k in CAMPI_SEGRETI})
        with open(p, "w", encoding="utf-8") as f:
            json.dump(idx, f, ensure_ascii=False, indent=2)
        righe = ["# ACCESSI_SISTEMA — indice (nessun segreto)", "",
                 "Il documento completo è cifrato in `accessi/voci/*.age` (solo il titolare può decifrarlo).",
                 "Ricostruzione: `python3 -m studio accessi esporta --identita <chiave privata>`.", "",
                 "| Servizio | Funzione | Stato verifica | Piano / costo | Rinnovo | Ultima azione | Segreti |", "|---|---|---|---|---|---|---|"]
        for s, v in sorted(idx.items()):
            righe.append(f"| {s} | {v.get('funzione', '')} | {v.get('stato_verifica', '')} | {v.get('piano', '')} {v.get('costo', '')} "
                         f"| {v.get('rinnovo', '')} | {v['ultima_azione']} {v['aggiornato']} | {', '.join(v['segreti'])} |")
        with open(os.path.join(self.cartella, "INDICE.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(righe) + "\n")

    def esporta(self, identita: str) -> dict:
        """Solo per il titolare: decifra tutte le voci con la sua chiave privata e ricostruisce lo stato corrente."""
        doc = {}
        for nome in sorted(os.listdir(os.path.join(self.cartella, "voci"))):
            r = subprocess.run(["age", "-d", "-i", identita, os.path.join(self.cartella, "voci", nome)],
                               capture_output=True, check=True)
            v = json.loads(r.stdout)
            doc.setdefault(v["servizio"], {}).update(v)
        return doc
