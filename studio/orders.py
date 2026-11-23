"""Libro ordini: deduplica per ID, rimborsi, riconciliazione. Persistito su disco a ogni modifica.

Responsabile: shopify-operazioni (bootstrap del Team Lead).
"""
from __future__ import annotations

from .money import pct_bp, scorporo_iva
from .storage import atomic_write_json, read_json


class OrderBook:
    def __init__(self, path: str):
        self.path = path
        self.data = read_json(path, {"ordini": {}, "duplicati_scartati": 0, "eventi_rimborso_duplicati": 0})

    def _save(self):
        atomic_write_json(self.path, self.data)

    def ingest(self, ordine: dict) -> bool:
        """Ritorna True se l'ordine è nuovo, False se è un duplicato (stesso order_id)."""
        oid = ordine["order_id"]
        if oid in self.data["ordini"]:
            self.data["duplicati_scartati"] += 1
            prec = self.data["ordini"][oid]
            diversi = [k for k in ("lordo_cents", "sconto_cents", "iva_bp", "paese", "tocchi")
                       if k in ordine and ordine[k] != prec.get(k)]
            if diversi:  # QA M-7: stesso ID, contenuto diverso ⇒ conflitto da riconciliare
                self.data.setdefault("conflitti", []).append({"order_id": oid, "campi": diversi})
            self._save()
            return False
        rec = dict(ordine)
        rec.setdefault("sconto_cents", 0)
        rec.setdefault("tocchi", [])
        rec.setdefault("test", False)
        rec["rimborsato"] = False
        self.data["ordini"][oid] = rec
        self._save()
        return True

    def rimborsa(self, order_id: str, giorno: int) -> bool:
        o = self.data["ordini"].get(order_id)
        if o is None:
            raise KeyError(f"rimborso per ordine inesistente: {order_id}")
        if o["rimborsato"]:
            self.data["eventi_rimborso_duplicati"] += 1
            self._save()
            return False
        o["rimborsato"] = True
        o["rimborso_giorno"] = giorno
        self._save()
        return True

    def ordini(self, includi_test=False) -> list:
        return [o for o in self.data["ordini"].values() if includi_test or not o.get("test")]

    def get(self, order_id):
        return self.data["ordini"].get(order_id)


def valori_ordine(o: dict, ipotesi: dict) -> dict:
    """Scomposizione economica di un ordine (centesimi)."""
    pagato = o["lordo_cents"] - o.get("sconto_cents", 0)
    netto = scorporo_iva(pagato, o.get("iva_bp", 0))
    fee = (pct_bp(pagato, ipotesi["commissione_pagamento_pct_bp"]) + ipotesi["commissione_pagamento_fissa_cents"]
           if pagato > 0 else 0)
    fc = o.get("fee_canale")
    if fc and pagato > 0:  # ordine da marketplace: la commissione del marketplace sostituisce quella di pagamento
        fee = pct_bp(pagato, fc["pct_bp"]) + fc["fissa_cents"]
    if o.get("rimborsato") and ipotesi.get("commissione_pagamento_rimborsata_su_refund"):
        fee = 0  # QA M-6: il flag di policy è letto dal codice
    return {"pagato_cents": pagato, "iva_cents": pagato - netto, "netto_cents": netto,
            "fee_pagamento_cents": fee, "sconto_cents": o.get("sconto_cents", 0)}
