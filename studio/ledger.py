"""Registro spese in euro (centesimi interi) con tetto rigido.

Modello a "buste":
  reserve(id, categoria, max)  -> impegna l'importo massimo PRIMA dell'azione a pagamento
  draw(id, draw_id, importo)    -> registra un consumo effettivo dentro la busta (idempotente per draw_id)
  undraw(id, draw_id)           -> storna un consumo (es. commissione creator su ordine rimborsato)
  close(id)                     -> chiude la busta e libera il non speso

residuo = tetto - consumato - (impegnato non ancora consumato nelle buste aperte)

Regole di blocco (SpendBlocked):
  - costo massimo sconosciuto (None, non intero, negativo)
  - residuo insufficiente
  - allocazione della categoria superata
  - consumo oltre il massimo riservato
Ogni tentativo bloccato viene registrato in `bloccati` per audit.
Responsabile: strategia-finanza (bootstrap del Team Lead, vedi DECISIONI.md D-004).
"""
from __future__ import annotations

import fcntl
import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone

from .money import eur
from .storage import atomic_write_json


class SpendBlocked(Exception):
    def __init__(self, motivo: str, dettagli: dict | None = None):
        super().__init__(motivo)
        self.motivo = motivo
        self.dettagli = dettagli or {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Ledger:
    def __init__(self, path: str, tetto_cents: int, allocazione: dict | None = None,
                 categorie: list | None = None):
        self.path = path
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        nuovo = {"valuta": "EUR", "tetto_cents": tetto_cents, "allocazione_cents": allocazione or {},
                 "categorie": categorie or sorted((allocazione or {}).keys()), "buste": {}, "bloccati": []}
        self.data = nuovo
        with self._tx():  # QA N-3: controllo di esistenza e creazione sotto lo stesso lock
            if self.data is nuovo and os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    self.data = json.load(f)
        if self.data["tetto_cents"] != tetto_cents:
            raise ValueError(
                f"Il registro {path} ha tetto {self.data['tetto_cents']} diverso da {tetto_cents}: "
                "un cambio di tetto richiede una decisione del titolare.")

    @contextmanager
    def _tx(self):
        """Transazione: lock esclusivo sul file, rilettura dello stato aggiornato, salvataggio.

        Più processi (run in parallelo sullo stesso --registro) vedono sempre il residuo reale (QA B-1).
        """
        with open(self.path + ".lock", "a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                if os.path.exists(self.path):
                    with open(self.path, encoding="utf-8") as f:
                        self.data = json.load(f)
                yield
            finally:
                self._save()
                fcntl.flock(lock, fcntl.LOCK_UN)

    # ------------------------------------------------------------------ calcoli
    @property
    def tetto(self) -> int:
        return self.data["tetto_cents"]

    def _drawn(self, b: dict) -> int:
        return sum(d["importo_cents"] for d in b["consumi"].values() if not d.get("stornato"))

    def consumato(self, categoria: str | None = None, prefisso: str = "") -> int:
        """Consumato totale; con `prefisso` solo le buste di un run (registro condiviso)."""
        return sum(self._drawn(b) for b in self.data["buste"].values()
                   if (categoria is None or b["categoria"] == categoria) and b["id"].startswith(prefisso))

    def impegnato_aperto(self, categoria: str | None = None) -> int:
        return sum(max(b["max_cents"] - self._drawn(b), 0) for b in self.data["buste"].values()
                   if b["stato"] == "aperta" and (categoria is None or b["categoria"] == categoria))

    def residuo(self) -> int:
        return self.tetto - self.consumato() - self.impegnato_aperto()

    def usato_categoria(self, categoria: str) -> int:
        return self.consumato(categoria) + self.impegnato_aperto(categoria)

    # ---------------------------------------------------------------- operazioni
    def _block(self, motivo: str, **dettagli):
        self.data["bloccati"].append({"quando": _now(), "motivo": motivo, **dettagli})
        raise SpendBlocked(motivo, dettagli)  # salvato dalla transazione

    def reserve(self, busta_id: str, categoria: str, max_cents, descrizione: str,
                fase: str = "", simulato: bool = True, tag: list | None = None) -> dict:
        with self._tx():
            return self._reserve(busta_id, categoria, max_cents, descrizione, fase, simulato, tag)

    def _reserve(self, busta_id, categoria, max_cents, descrizione, fase, simulato, tag):
        esistente = self.data["buste"].get(busta_id)
        if esistente is not None:
            # Idempotenza: una ripresa dopo interruzione non deve riservare due volte.
            if esistente["categoria"] != categoria or esistente["max_cents"] != max_cents:
                self._block("busta già esistente con parametri diversi", busta=busta_id)
            return esistente
        if max_cents is None or isinstance(max_cents, bool) or not isinstance(max_cents, int) or max_cents < 0:
            self._block("costo massimo sconosciuto o non valido", busta=busta_id,
                        categoria=categoria, max_cents=max_cents, descrizione=descrizione)
        if self.data["categorie"] and categoria not in self.data["categorie"]:
            self._block("categoria di spesa non prevista", busta=busta_id, categoria=categoria)
        # QA N-1: se il run ha una prenotazione aperta per la categoria, la riserva la trasferisce
        # (la capacità era già stata garantita alla Selezione, anche con altri run in parallelo).
        if "/" in busta_id:
            pren = self.data["buste"].get(busta_id.rsplit("/", 1)[0] + "/prenotazione-" + categoria)
            if pren and pren["stato"] == "aperta" and pren["max_cents"] - self._drawn(pren) >= max_cents:
                pren["max_cents"] -= max_cents
                if pren["max_cents"] == self._drawn(pren):
                    pren["stato"] = "chiusa"
                    pren["chiusa"] = _now()
                return self._crea(busta_id, categoria, max_cents, descrizione, fase, simulato, tag,
                                  da_prenotazione=pren["id"])
        if max_cents > self.residuo():
            self._block("residuo insufficiente", busta=busta_id, categoria=categoria,
                        richiesto_cents=max_cents, residuo_cents=self.residuo(), descrizione=descrizione)
        limite = self.data["allocazione_cents"].get(categoria)
        if limite is not None and self.usato_categoria(categoria) + max_cents > limite:
            self._block("allocazione della categoria superata", busta=busta_id, categoria=categoria,
                        richiesto_cents=max_cents, usato_cents=self.usato_categoria(categoria),
                        allocazione_cents=limite)
        return self._crea(busta_id, categoria, max_cents, descrizione, fase, simulato, tag)

    def _crea(self, busta_id, categoria, max_cents, descrizione, fase, simulato, tag, da_prenotazione=None):
        b = {"id": busta_id, "categoria": categoria, "max_cents": max_cents, "descrizione": descrizione,
             "fase": fase, "simulato": simulato, "tag": tag or [], "stato": "aperta",
             "creata": _now(), "consumi": {}}
        if da_prenotazione:
            b["da_prenotazione"] = da_prenotazione
        self.data["buste"][busta_id] = b
        return b

    def prenota(self, prefisso: str, per_categoria: dict, fase: str = "selezione") -> list:
        """Prenota in un'unica transazione il budget di un piano: tutte le categorie o nessuna."""
        with self._tx():
            ids = [f"{prefisso}prenotazione-{c}" for c in per_categoria]
            if all(i in self.data["buste"] for i in ids):
                return ids  # idempotente (ripresa)
            creati = []
            try:
                for cat, imp in per_categoria.items():
                    if imp:
                        self._reserve(f"{prefisso}prenotazione-{cat}", cat, imp, f"prenotazione piano: {cat}",
                                      fase, True, ["prenotazione"])
                        creati.append(f"{prefisso}prenotazione-{cat}")
            except SpendBlocked:
                for i in creati:
                    del self.data["buste"][i]  # tutto o niente
                raise
            return creati

    def draw(self, busta_id: str, draw_id: str, importo_cents: int, nota: str = "") -> bool:
        """Registra un consumo. Ritorna False se il consumo era già registrato (idempotenza)."""
        with self._tx():
            return self._draw(busta_id, draw_id, importo_cents, nota)

    def _draw(self, busta_id, draw_id, importo_cents, nota):
        b = self.data["buste"].get(busta_id)
        if b is None:
            self._block("consumo senza riserva preventiva", busta=busta_id, consumo=draw_id)
        if isinstance(importo_cents, bool) or not isinstance(importo_cents, int) or importo_cents < 0:
            self._block("importo non valido", busta=busta_id, consumo=draw_id)
        if draw_id in b["consumi"] and not b["consumi"][draw_id].get("stornato"):
            if b["consumi"][draw_id]["importo_cents"] != importo_cents:  # QA M-1: conflitto, non silenzio
                self._block("consumo già registrato con importo diverso", busta=busta_id, consumo=draw_id,
                            registrato_cents=b["consumi"][draw_id]["importo_cents"], nuovo_cents=importo_cents)
            return False  # già registrato (es. ripresa dopo interruzione): nessuna doppia spesa
        if b["stato"] != "aperta":
            self._block("consumo su busta chiusa", busta=busta_id, consumo=draw_id)
        if self._drawn(b) + importo_cents > b["max_cents"]:
            self._block("consumo oltre il massimo riservato", busta=busta_id, consumo=draw_id,
                        importo_cents=importo_cents, disponibile_cents=b["max_cents"] - self._drawn(b))
        b["consumi"][draw_id] = {"importo_cents": importo_cents, "nota": nota, "quando": _now()}
        return True

    def undraw(self, busta_id: str, draw_id: str, motivo: str) -> bool:
        with self._tx():
            return self._undraw(busta_id, draw_id, motivo)

    def _undraw(self, busta_id, draw_id, motivo):
        b = self.data["buste"][busta_id]
        d = b["consumi"].get(draw_id)
        if d is None or d.get("stornato"):
            return False
        d["stornato"] = True
        d["motivo_storno"] = motivo
        return True

    def close(self, busta_id: str) -> int:
        """Chiude la busta; ritorna l'importo liberato."""
        with self._tx():
            return self._close(busta_id)

    def _close(self, busta_id):
        b = self.data["buste"][busta_id]
        if b["stato"] == "chiusa":
            return 0
        b["stato"] = "chiusa"
        b["chiusa"] = _now()
        return b["max_cents"] - self._drawn(b)

    def spend_once(self, busta_id: str, categoria: str, max_cents, effettivo_cents: int,
                   descrizione: str, fase: str = "", tag: list | None = None) -> None:
        """Spesa singola: riserva, consuma, chiude. Idempotente."""
        self.reserve(busta_id, categoria, max_cents, descrizione, fase=fase, tag=tag)
        try:
            self.draw(busta_id, "unico", effettivo_cents, descrizione)
        finally:
            self.close(busta_id)  # QA M-3: anche se il consumo è bloccato, nessun impegno resta aperto

    # -------------------------------------------------------------------- report
    def riepilogo(self) -> dict:
        cats = sorted({b["categoria"] for b in self.data["buste"].values()} | set(self.data["categorie"]))
        return {
            "tetto_cents": self.tetto,
            "consumato_cents": self.consumato(),
            "impegnato_aperto_cents": self.impegnato_aperto(),
            "residuo_cents": self.residuo(),
            "per_categoria": {c: {"consumato_cents": self.consumato(c),
                                  "impegnato_aperto_cents": self.impegnato_aperto(c),
                                  "allocazione_cents": self.data["allocazione_cents"].get(c)} for c in cats},
            "tentativi_bloccati": len(self.data["bloccati"]),
        }

    def testo(self) -> str:
        r = self.riepilogo()
        righe = [f"Tetto {eur(r['tetto_cents'])} | consumato {eur(r['consumato_cents'])} | "
                 f"impegnato {eur(r['impegnato_aperto_cents'])} | residuo {eur(r['residuo_cents'])}"]
        for c, v in r["per_categoria"].items():
            alloc = eur(v["allocazione_cents"]) if v["allocazione_cents"] is not None else "-"
            righe.append(f"  {c:<15} consumato {eur(v['consumato_cents']):>10}  impegnato "
                         f"{eur(v['impegnato_aperto_cents']):>10}  allocazione {alloc:>10}")
        for blk in self.data["bloccati"]:
            righe.append(f"  BLOCCATO: {blk['motivo']} ({blk.get('busta', '')})")
        return "\n".join(righe)

    def _save(self):
        atomic_write_json(self.path, self.data)
