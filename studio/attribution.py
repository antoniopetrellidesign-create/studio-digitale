"""Attribuzione multi-canale.

Regole:
  - Il RICAVO di un ordine si conta una sola volta (portafoglio). Canale primario:
    codice creator > click Ads > organico.
  - I COSTI di tutti i canali che hanno contribuito si conservano: la commissione creator è dovuta
    anche se c'è un click Ads, e la spesa Ads resta a carico del canale Ads.
  - Ogni canale toccato riceve l'ordine come "assistito".
Responsabile: creator-partnership (bootstrap del Team Lead).
"""
from .money import pct_bp

PRIORITA = ("creator", "ads", "organico")


def canali(o: dict) -> list:
    c = sorted({t["canale"] for t in o.get("tocchi", [])}, key=PRIORITA.index)
    return c or ["organico"]


def canale_primario(o: dict) -> str:
    return canali(o)[0]


def partner_creator(o: dict):
    return next((t["id"] for t in o.get("tocchi", []) if t["canale"] == "creator"), None)


def commissione_creator(netto_cents: int, pct_bp_su_netto: int) -> int:
    return pct_bp(netto_cents, pct_bp_su_netto)


def entro_clawback(o: dict, finestra_giorni: int) -> bool:
    return o.get("rimborsato") and (o["rimborso_giorno"] - o.get("giorno", 0)) <= finestra_giorni
