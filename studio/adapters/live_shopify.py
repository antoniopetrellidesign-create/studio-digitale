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

SEGNAPOSTO_RETE = "segnaposto-segreto-di-rete"  # NON segreto: il proxy lo sostituisce con il token per l'host legato
API_VERSION = "2025-10"
SCOPE_MINIMI = ["read_products", "write_products", "read_orders", "read_discounts", "write_discounts",
                "read_files", "write_files"]


def verifica_webhook(corpo: bytes, firma_b64: str, segreto: str) -> bool:
    if not segreto or not firma_b64:  # QA minore: segreto vuoto mai valido
        return False
    atteso = base64.b64encode(hmac.new(segreto.encode(), corpo, hashlib.sha256).digest()).decode()
    return hmac.compare_digest(atteso, firma_b64 or "")


class LiveShopify:
    servizio = "shopify"

    def __init__(self, gate, negozio: str, token_env: str = "SHOPIFY_ADMIN_TOKEN", endpoint: str | None = None,
                 credenziale: str = "env"):
        if credenziale not in ("env", "rete"):
            raise ValueError("credenziale: 'env' oppure 'rete'")
        self.credenziale = credenziale
        self.gate = gate
        self.negozio = negozio
        self.token_env = token_env
        self.endpoint = endpoint or f"https://{negozio}/admin/api/{API_VERSION}/graphql.json"
        u = urlparse(self.endpoint)
        host = u.hostname or ""
        locale = host in ("127.0.0.1", "localhost")
        # QA M-3 e minore: controllo dell'host anche quando l'endpoint è costruito da `negozio`; https obbligatorio
        if not locale and (not host.endswith(".myshopify.com") or u.scheme != "https"):
            raise ValueError("endpoint ammessi: https://*.myshopify.com oppure localhost (solo test)")

    def _graphql(self, azione: str, query: str, variabili: dict | None = None) -> dict:
        # QA H-1: nessuna richiesta HTTP se il live non è consentito, in QUALSIASI modalità del cancello
        if not self.gate.live_consentito(self.servizio):
            self.gate.record(self.servizio, azione, esito_forzato="bloccato")
            raise ExternalActionBlocked(f"shopify.{azione}: live non consentito (serve STUDIO_LIVE=1 e integrazione collaudata)")
        self.gate.record(self.servizio, azione)
        if self.credenziale == "rete":  # il proxy inserisce il valore reale solo per l'host legato; qui solo segnaposto
            token = SEGNAPOSTO_RETE
        else:
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


def verifica_continuita(host: str, url_eco, intestazione: str = "X-Shopify-Access-Token",
                        segnaposto: str = SEGNAPOSTO_RETE, timeout: int = 15) -> dict:
    """Prova di continuità dopo un riavvio: chiede a un servizio di eco le intestazioni ricevute e confronta SOLO
    un'impronta SHA-256 troncata (mai il valore). `url_eco` è un URL oppure un callable(host) -> URL.
    presente=True se l'intestazione è arrivata con valore diverso dal segnaposto (sostituito dal proxy)."""
    url = url_eco(host) if callable(url_eco) else url_eco
    req = urllib.request.Request(url, headers={intestazione: segnaposto})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        ricevute = {k.lower(): v for k, v in json.loads(r.read()).get("headers", {}).items()}
    valore = ricevute.get(intestazione.lower())
    if not valore:
        return {"presente": False, "impronta": None}
    impronta = hashlib.sha256(valore.encode()).hexdigest()[:12]
    return {"presente": valore != segnaposto, "impronta": impronta}
