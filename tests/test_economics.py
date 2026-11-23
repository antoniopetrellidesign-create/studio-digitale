import os
import tempfile
import unittest

from studio import economics
from studio.ledger import Ledger
from studio.orders import OrderBook
from studio.workflow import carica_json

POL = carica_json("config/policy.json")


def _o(oid, canali, sconto=0, giorno=1):
    return {"order_id": oid, "lordo_cents": 1900, "sconto_cents": sconto, "iva_bp": 2200, "giorno": giorno,
            "tocchi": [{"canale": c, "id": c} for c in canali]}


class TestEconomics(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.l = Ledger(os.path.join(d, "l.json"), 50000, POL["allocazione_budget_cents"], POL["categorie_spesa"])
        self.ob = OrderBook(os.path.join(d, "o.json"))

    def test_doppia_attribuzione_ricavo_una_volta_costi_entrambi(self):
        self.ob.ingest(_o("A", ["creator", "ads"], sconto=190))
        self.l.reserve("ads", "ads", 1000, "x", tag=["canale:ads"])
        self.l.draw("ads", "g", 1000)
        self.l.reserve("cr", "commissione", 1000, "x", tag=["canale:creator"])
        self.l.draw("cr", "A", 421)
        m = economics.misura(self.ob, self.l, POL)
        self.assertEqual(m["ordini"], 1)
        self.assertEqual(m["ricavi_netti_cents"], 1402)
        self.assertEqual(m["per_canale"]["creator"]["ricavi_netti_cents"], 1402)
        self.assertEqual(m["per_canale"]["ads"]["ricavi_netti_cents"], 0)
        self.assertEqual(m["per_canale"]["ads"]["ordini_assistiti"], 1)
        self.assertEqual(m["acquisizione_cents"], 1421)
        self.assertTrue(m["controllo_doppio_conteggio_ok"])

    def test_rimborso_esclude_ricavo_trattiene_fee(self):
        self.ob.ingest(_o("A", []))
        self.ob.rimborsa("A", 3)
        m = economics.misura(self.ob, self.l, POL)
        self.assertEqual(m["ricavi_netti_cents"], 0)
        self.assertEqual(m["fee_pagamento_cents"], 85)
        self.assertEqual(m["tasso_rimborso_bp"], 10000)

    def test_costi_test_falliti_riducono_il_margine(self):
        self.ob.ingest(_o("A", []))
        m0 = economics.misura(self.ob, self.l, POL)
        m1 = economics.misura(self.ob, self.l, POL, costi_test_falliti_cents=500)
        self.assertEqual(m0["margine_contribuzione_cents"] - m1["margine_contribuzione_cents"], 500)

    def _m(self, **kw):
        base = {"ordini": 20, "tasso_rimborso_bp": 0, "acquisizione_cents": 10000, "margine_contribuzione_cents": 100,
                "roas_su_margine_x100": 200}
        base.update(kw)
        return base

    def test_regole_decisione(self):
        piano = {"soglia_stop_cents": 12000}
        self.assertEqual(economics.decidi(self._m(), piano, POL)["esito"], "scala")
        self.assertEqual(economics.decidi(self._m(roas_su_margine_x100=120), piano, POL)["esito"], "ripeti")
        self.assertEqual(economics.decidi(self._m(roas_su_margine_x100=50), piano, POL)["esito"], "stop")
        self.assertEqual(economics.decidi(self._m(tasso_rimborso_bp=2500), piano, POL)["esito"], "stop")
        self.assertEqual(economics.decidi(self._m(margine_contribuzione_cents=-1), piano, POL)["esito"], "ripeti")
        self.assertEqual(economics.decidi(self._m(ordini=4, acquisizione_cents=13000), piano, POL)["esito"], "stop")
        self.assertEqual(economics.decidi(self._m(ordini=4, acquisizione_cents=5000), piano, POL)["esito"], "ripeti")
        self.assertIn("richiede_titolare", economics.decidi(self._m(), piano, POL))
        # sotto il minimo di ordini il tasso di rimborso non decide da solo
        self.assertEqual(economics.decidi(self._m(ordini=2, tasso_rimborso_bp=5000, acquisizione_cents=100), piano, POL)["esito"], "ripeti")


if __name__ == "__main__":
    unittest.main()
