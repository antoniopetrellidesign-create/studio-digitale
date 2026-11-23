"""Coda condivisa del team (file JSON nel repository).

Ogni compito ha un solo responsabile. Stati: da_fare, in_corso, fatto, bloccato.
Un compito può partire solo quando tutte le dipendenze sono `fatto`.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .storage import atomic_write_json, read_json

STATI = ("da_fare", "in_corso", "fatto", "bloccato")


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class TaskQueue:
    def __init__(self, path: str):
        self.path = path
        self.data = read_json(path, {"compiti": []})

    def _save(self):
        atomic_write_json(self.path, self.data)

    def get(self, task_id: str) -> dict | None:
        return next((t for t in self.data["compiti"] if t["id"] == task_id), None)

    def add(self, task_id: str, titolo: str, agente: str, fase: str = "", dipende_da=None,
            output=None, run_id: str | None = None) -> dict:
        t = self.get(task_id)
        if t:
            return t  # idempotente
        t = {"id": task_id, "titolo": titolo, "agente": agente, "fase": fase,
             "dipende_da": dipende_da or [], "output": output or [], "stato": "da_fare",
             "run_id": run_id, "creato": _now(), "aggiornato": _now(), "note": []}
        self.data["compiti"].append(t)
        self._save()
        return t

    def pronto(self, task_id: str) -> bool:
        t = self.get(task_id)
        return all((self.get(d) or {}).get("stato") == "fatto" for d in t["dipende_da"])

    def set_stato(self, task_id: str, stato: str, nota: str = "") -> dict:
        if stato not in STATI:
            raise ValueError(f"stato non valido: {stato}")
        t = self.get(task_id)
        if t is None:
            raise KeyError(task_id)
        if stato == "in_corso" and t["stato"] != "in_corso":  # QA S-1: la ripresa non è una nuova attività
            from .regia import sospensione
            if sospensione().get("attivita"):
                raise RuntimeError(f"{task_id}: nuove attività sospese dal titolare")
        if stato in ("in_corso", "fatto") and not self.pronto(task_id):
            raise RuntimeError(f"{task_id}: dipendenze non completate {t['dipende_da']}")
        t["stato"] = stato
        t["aggiornato"] = _now()
        if nota:
            t["note"].append({"quando": _now(), "nota": nota})
        self._save()
        return t

    def testo(self) -> str:
        righe = []
        for t in self.data["compiti"]:
            dip = f" ← {','.join(t['dipende_da'])}" if t["dipende_da"] else ""
            righe.append(f"{t['id']:<10} {t['stato']:<9} {t['agente']:<20} {t['titolo']}{dip}")
        return "\n".join(righe) or "(coda vuota)"
