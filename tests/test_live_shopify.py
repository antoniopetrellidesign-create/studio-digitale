"""Adattatore Shopify reale provato contro un server LOCALE che imita l'API (nessuna chiamata a Shopify)."""
import base64
import hashlib
import hmac
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

from studio.adapters.base import ExternalActionBlocked, ExternalGate
from studio.adapters.live_shopify import SCOPE_MINIMI, LiveShopify, verifica_webhook

RICHIESTE = []


class FintoShopify(BaseHTTPRequestHandler):
    def do_POST(self):
        corpo = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        RICHIESTE.append({"token": self.headers.get("X-Shopify-Access-Token"), "corpo": corpo})
        if "shop" in corpo["query"]:
            data = {"shop": {"name": "n", "myshopifyDomain": "finto.myshopify.com"},
                    "currentAppInstallation": {"accessScopes": [{"handle": s} for s in SCOPE_MINIMI[:-1]] +
                                               [{"handle": "read_customers"}]}}
        else:
            stato = corpo["variables"]["p"]["status"]
            data = {"productCreate": {"product": {"id": "gid://shopify/Product/1", "status": stato}, "userErrors": []}}
        out = json.dumps({"data": data}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *a):
        pass


class TestLiveShopify(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(("127.0.0.1", 0), FintoShopify)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.srv.server_port}/admin/api/graphql.json"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def _ad(self, collaudate=("shopify",)):
        log = os.path.join(tempfile.mkdtemp(), "calls.jsonl")
        return LiveShopify(ExternalGate("live", log, collaudate), "finto.myshopify.com", "TOKEN_DI_PROVA_ENV", self.url)

    def test_bloccato_senza_studio_live(self):
        with mock.patch.dict(os.environ, {"STUDIO_LIVE": "0", "TOKEN_DI_PROVA_ENV": "x"}):
            with self.assertRaises(ExternalActionBlocked):
                self._ad().verifica_accesso()

    def test_bloccato_se_integrazione_non_collaudata(self):
        with mock.patch.dict(os.environ, {"STUDIO_LIVE": "1", "TOKEN_DI_PROVA_ENV": "x"}):
            with self.assertRaises(ExternalActionBlocked):
                self._ad(collaudate=()).verifica_accesso()

    def test_richieste_corrette_scope_e_bozza(self):
        with mock.patch.dict(os.environ, {"STUDIO_LIVE": "1", "TOKEN_DI_PROVA_ENV": "valore-fittizio"}):
            ad = self._ad()
            acc = ad.verifica_accesso()
            self.assertEqual(acc["scope_mancanti"], [SCOPE_MINIMI[-1]])
            self.assertEqual(acc["scope_superflui"], ["read_customers"])
            p = ad.crea_prodotto_bozza({"id": "PRD-X"}, 1900, ["it"])
        self.assertEqual(p["stato"], "bozza")
        self.assertEqual(RICHIESTE[-1]["corpo"]["variables"]["p"]["status"], "DRAFT")
        self.assertEqual(RICHIESTE[-1]["token"], "valore-fittizio")

    def test_endpoint_esterni_non_ammessi(self):
        with self.assertRaises(ValueError):
            LiveShopify(ExternalGate("live", "/dev/null"), "x", endpoint="https://evil.example/graphql")

    def test_firma_webhook(self):
        corpo = b'{"id": 1}'
        firma = base64.b64encode(hmac.new(b"segreto-di-prova", corpo, hashlib.sha256).digest()).decode()
        self.assertTrue(verifica_webhook(corpo, firma, "segreto-di-prova"))
        self.assertFalse(verifica_webhook(corpo + b" ", firma, "segreto-di-prova"))
        self.assertFalse(verifica_webhook(corpo, "", "segreto-di-prova"))


if __name__ == "__main__":
    unittest.main()
