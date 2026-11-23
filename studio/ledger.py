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

import json
import os
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
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                self.data = json.load(f)
            if self.data["tetto_cents"] != tetto_cents:
                raise ValueError(
                    f"Il registro {path} ha tetto {self.data['tetto_cents']} diverso da {tetto_cents}: "
                    "un cambio di tetto richiede una decisione del titolare.")
        else:
            self.data = {
                "valuta": "EUR",
                "tetto_cents": tetto_cents,
                "allocazione_cents": allocazione or {},
                "categorie": categorie or sorted((allocazione or {}).keys()),
                "buste": {},
                "bloccati": [],
            }
            self._save()

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
        self._save()
        raise SpendBlocked(motivo, dettagli)

    def reserve(self, busta_id: str, categoria: str, max_cents, descrizione: str,
                fase: str = "", simulato: bool = True, tag: list | None = None) -> dict:
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
        if max_cents > self.residuo():
            self._block("residuo insufficiente", busta=busta_id, categoria=categoria,
                        richiesto_cents=max_cents, residuo_cents=self.residuo(), descrizione=descrizione)
        limite = self.data["allocazione_cents"].get(categoria)
        if limite is not None and self.usato_categoria(categoria) + max_cents > limite:
            self._block("allocazione della categoria superata", busta=busta_id, categoria=categoria,
                        richiesto_cents=max_cents, usato_cents=self.usato_categoria(categoria),
                        allocazione_cents=limite)
        b = {"id": busta_id, "categoria": categoria, "max_cents": max_cents, "descrizione": descrizione,
             "fase": fase, "simulato": simulato, "tag": tag or [], "stato": "aperta",
             "creata": _now(), "consumi": {}}
        self.data["buste"][busta_id] = b
        self._save()
        return b

    def draw(self, busta_id: str, draw_id: str, importo_cents: int, nota: str = "") -> bool:
        """Registra un consumo. Ritorna False se il consumo era già registrato (idempotenza)."""
        b = self.data["buste"].get(busta_id)
        if b is None:
            self._block("consumo senza riserva preventiva", busta=busta_id, consumo=draw_id)
        if draw_id in b["consumi"] and not b["consumi"][draw_id].get("stornato"):
            return False  # già registrato (es. ripresa dopo interruzione): nessuna doppia spesa
        if b["stato"] != "aperta":
            self._block("consumo su busta chiusa", busta=busta_id, consumo=draw_id)
        if not isinstance(importo_cents, int) or importo_cents < 0:
            self._block("importo non valido", busta=busta_id, consumo=draw_id)
        if self._drawn(b) + importo_cents > b["max_cents"]:
            self._block("consumo oltre il massimo riservato", busta=busta_id, consumo=draw_id,
                        importo_cents=importo_cents, disponibile_cents=b["max_cents"] - self._drawn(b))
        b["consumi"][draw_id] = {"importo_cents": importo_cents, "nota": nota, "quando": _now()}
        self._save()
        return True

    def undraw(self, busta_id: str, draw_id: str, motivo: str) -> bool:
        b = self.data["buste"][busta_id]
        d = b["consumi"].get(draw_id)
        if d is None or d.get("stornato"):
            return False
        d["stornato"] = True
        d["motivo_storno"] = motivo
        self._save()
        return True

    def close(self, busta_id: str) -> int:
        """Chiude la busta; ritorna l'importo liberato."""
        b = self.data["buste"][busta_id]
        if b["stato"] == "chiusa":
            return 0
        b["stato"] = "chiusa"
        b["chiusa"] = _now()
        self._save()
        return b["max_cents"] - self._drawn(b)

    def spend_once(self, busta_id: str, categoria: str, max_cents, effettivo_cents: int,
                   descrizione: str, fase: str = "", tag: list | None = None) -> None:
        """Spesa singola: riserva, consuma, chiude. Idempotente."""
        self.reserve(busta_id, categoria, max_cents, descrizione, fase=fase, tag=tag)
        self.draw(busta_id, "unico", effettivo_cents, descrizione)
        self.close(busta_id)

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
