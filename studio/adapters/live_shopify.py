"""Adattatore Shopify reale (Admin GraphQL API) — implementato, NON ancora collaudato dal vivo.

- Il token si legge da una variabile d'ambiente indicata per NOME (riferimento segreto://shopify/token_admin);
  in un ambiente Claude Code cloud il proxy può iniettarlo come segreto di rete: il valore non passa mai dal codice.
- Ogni chiamata passa da ExternalGate: senza STUDIO_LIVE=1 e senza 'shopify' tra le integrazioni collaudate è bloccata.
- I prodotti si creano solo in stato DRAFT (nessuna pubblicazione prima della fase di lancio).
- verifica_webhook: firma HMAC-SHA256 dei webhook (orders/paid, refunds/create) con confronto a tempo costante.
Responsabile: account-integrazioni / shopify-operazioni.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import urllib.request
from urllib.parse import urlparse

from .base import ExternalActionBlocked

API_VERSION = "2025-10"
SCOPE_MINIMI = ["read_products", "write_products", "read_orders", "read_discounts", "write_discounts",
                "read_files", "write_files"]


def verifica_webhook(corpo: bytes, firma_b64: str, segreto: str) -> bool:
    atteso = base64.b64encode(hmac.new(segreto.encode(), corpo, hashlib.sha256).digest()).decode()
    return hmac.compare_digest(atteso, firma_b64 or "")


class LiveShopify:
    servizio = "shopify"

    def __init__(self, gate, negozio: str, token_env: str = "SHOPIFY_ADMIN_TOKEN", endpoint: str | None = None):
        self.gate = gate
        self.negozio = negozio
        self.token_env = token_env
        self.endpoint = endpoint or f"https://{negozio}/admin/api/{API_VERSION}/graphql.json"
        host = urlparse(self.endpoint).hostname or ""
        if endpoint and host not in ("127.0.0.1", "localhost") and not host.endswith(".myshopify.com"):
            raise ValueError("endpoint ammessi: *.myshopify.com oppure localhost (solo test)")

    def _graphql(self, azione: str, query: str, variabili: dict | None = None) -> dict:
        self.gate.record(self.servizio, azione)  # blocca se live non consentito
        token = os.environ.get(self.token_env)
        if not token:
            raise ExternalActionBlocked(f"segreto://shopify/token_admin non disponibile (variabile {self.token_env})")
        req = urllib.request.Request(self.endpoint, method="POST",
                                     data=json.dumps({"query": query, "variables": variabili or {}}).encode(),
                                     headers={"Content-Type": "application/json", "X-Shopify-Access-Token": token})
        with urllib.request.urlopen(req, timeout=30) as r:
            risposta = json.loads(r.read())
        if risposta.get("errors"):
            raise RuntimeError(f"Shopify {azione}: {risposta['errors']}")
        return risposta["data"]

    def verifica_accesso(self) -> dict:
        d = self._graphql("verifica_accesso", "{ shop { name myshopifyDomain } "
                                              "currentAppInstallation { accessScopes { handle } } }")
        concessi = {s["handle"] for s in d["currentAppInstallation"]["accessScopes"]}
        mancanti = [s for s in SCOPE_MINIMI if s not in concessi]
        superflui = sorted(concessi - set(SCOPE_MINIMI))
        return {"negozio": d["shop"]["myshopifyDomain"], "scope_mancanti": mancanti, "scope_superflui": superflui}

    def crea_prodotto_bozza(self, manifest: dict, prezzo_cents: int, lingue: list) -> dict:
        q = ("mutation($p: ProductCreateInput!) { productCreate(product: $p) { product { id status } "
             "userErrors { field message } } }")
        d = self._graphql("crea_prodotto_bozza", q, {"p": {"title": manifest["id"], "status": "DRAFT",
                                                          "productType": "Prodotto digitale"}})
        err = d["productCreate"]["userErrors"]
        if err:
            raise RuntimeError(f"productCreate: {err}")
        p = d["productCreate"]["product"]
        if p["status"] != "DRAFT":
            raise RuntimeError("il prodotto non è in bozza")
        return {"product_id": p["id"], "stato": "bozza", "prezzo_cents": prezzo_cents, "lingue": lingue}
