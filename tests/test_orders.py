import os
import tempfile
import unittest

from studio.orders import OrderBook, valori_ordine
from studio.workflow import carica_json


class TestOrders(unittest.TestCase):
    def setUp(self):
        self.p = os.path.join(tempfile.mkdtemp(), "o.json")
        self.ob = OrderBook(self.p)

    def test_deduplica_per_id(self):
        o = {"order_id": "X1", "lordo_cents": 1900, "iva_bp": 2200}
        self.assertTrue(self.ob.ingest(o))
        self.assertFalse(self.ob.ingest(dict(o, lordo_cents=9999)))
        self.assertEqual(len(self.ob.ordini()), 1)
        self.assertEqual(self.ob.get("X1")["lordo_cents"], 1900)
        self.assertEqual(OrderBook(self.p).data["duplicati_scartati"], 1)

    def test_rimborso_doppio_ignorato(self):
        self.ob.ingest({"order_id": "X1", "lordo_cents": 1900, "iva_bp": 2200})
        self.assertTrue(self.ob.rimborsa("X1", 2))
        self.assertFalse(self.ob.rimborsa("X1", 3))
        with self.assertRaises(KeyError):
            self.ob.rimborsa("NON-ESISTE", 1)

    def test_valori(self):
        ip = carica_json("config/policy.json")["ipotesi_costi_variabili"]
        v = valori_ordine({"lordo_cents": 1900, "sconto_cents": 190, "iva_bp": 2200}, ip)
        self.assertEqual(v["pagato_cents"], 1710)
        self.assertEqual(v["netto_cents"], 1402)
        self.assertEqual(v["fee_pagamento_cents"], 50 + 30)

    def test_ordini_di_prova_esclusi_dai_kpi(self):
        self.ob.ingest({"order_id": "T", "lordo_cents": 1900, "iva_bp": 2200, "test": True})
        self.assertEqual(self.ob.ordini(), [])


if __name__ == "__main__":
    unittest.main()
