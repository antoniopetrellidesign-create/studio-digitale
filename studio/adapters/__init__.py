"""Adattatori verso i servizi esterni.

modalità "simulato": adattatori in mock.py, nessuna rete, ogni chiamata registrata in external_calls.jsonl.
modalità "live": adattatori in live.py; in questa fase BLOCCANO ogni chiamata (vedi INTEGRAZIONI_LIVE.md).
"""
from .base import ExternalActionBlocked, ExternalGate
from . import mock, live


def build(mode: str, gate: ExternalGate, guasti: dict | None = None) -> dict:
    guasti = guasti or {}
    if mode == "simulato":
        return {
            "shopify": mock.MockShopify(gate, accesso=guasti.get("shopify_accesso", True)),
            "pagamenti": mock.MockPagamenti(gate),
            "consegna": mock.MockConsegna(gate),
            "ads": mock.MockAds(gate),
            "creator": mock.MockCreator(gate),
            "ai": mock.MockAI(gate),
        }
    if mode == "live":
        return {k: live.LiveAdapter(k, gate) for k in ("shopify", "pagamenti", "consegna", "ads", "creator", "ai")}
    raise ValueError(f"modalità adattatori sconosciuta: {mode}")
