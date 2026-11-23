import os
import tempfile
import unittest

from studio.ledger import Ledger, SpendBlocked

ALLOC = {"ai": 6000, "piattaforma": 8000, "ads": 20000, "compenso_fisso": 6000, "commissione": 6000, "riserva": 4000}


class TestLedger(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.path = os.path.join(self.d, "l.json")
        self.l = Ledger(self.path, 50000, ALLOC, list(ALLOC))

    def test_riserva_prima_della_spesa(self):
        with self.assertRaises(SpendBlocked) as c:
            self.l.draw("mai-riservata", "x", 100)
        self.assertIn("senza riserva", c.exception.motivo)

    def test_costo_sconosciuto_bloccato(self):
        for v in (None, "10", -1, 1.5, True):
            with self.assertRaises(SpendBlocked):
                self.l.reserve(f"b{v}", "ads", v, "x")
        self.assertEqual(self.l.consumato(), 0)
        self.assertEqual(len(self.l.data["bloccati"]), 5)

    def test_residuo_insufficiente(self):
        with self.assertRaises(SpendBlocked) as c:
            self.l.reserve("big", "ads", 50001, "oltre il tetto")
        self.assertEqual(c.exception.motivo, "residuo insufficiente")

    def test_allocazione_categoria(self):
        self.l.reserve("a1", "ads", 15000, "x")
        with self.assertRaises(SpendBlocked) as c:
            self.l.reserve("a2", "ads", 6000, "x")
        self.assertEqual(c.exception.motivo, "allocazione della categoria superata")

    def test_consumo_oltre_riservato(self):
        self.l.reserve("a", "ads", 1000, "x")
        self.l.draw("a", "g1", 800)
        with self.assertRaises(SpendBlocked):
            self.l.draw("a", "g2", 300)

    def test_idempotenza_riserve_e_consumi(self):
        self.l.reserve("a", "ads", 1000, "x")
        self.l.reserve("a", "ads", 1000, "x")
        self.assertTrue(self.l.draw("a", "g1", 500))
        self.assertFalse(self.l.draw("a", "g1", 500))
        self.l.close("a")
        self.assertFalse(self.l.draw("a", "g1", 500))  # ripetizione dopo la chiusura: nessun blocco, nessuna spesa
        self.assertEqual(self.l.consumato(), 500)

    def test_chiusura_libera_il_non_speso(self):
        self.l.reserve("a", "ads", 10000, "x")
        self.l.draw("a", "g1", 2500)
        self.assertEqual(self.l.residuo(), 40000)
        self.assertEqual(self.l.close("a"), 7500)
        self.assertEqual(self.l.residuo(), 47500)

    def test_storno(self):
        self.l.reserve("c", "commissione", 6000, "x")
        self.l.draw("c", "ord1", 400)
        self.assertTrue(self.l.undraw("c", "ord1", "rimborso"))
        self.assertEqual(self.l.consumato(), 0)

    def test_persistenza(self):
        self.l.reserve("a", "ads", 1000, "x")
        self.l.draw("a", "g1", 300)
        l2 = Ledger(self.path, 50000, ALLOC, list(ALLOC))
        self.assertEqual(l2.consumato(), 300)
        self.assertEqual(l2.residuo(), 49000)

    def test_tetto_non_modificabile_silenziosamente(self):
        with self.assertRaises(ValueError):
            Ledger(self.path, 100000, ALLOC, list(ALLOC))

    def test_mai_oltre_il_tetto(self):
        import random
        rnd = random.Random(7)
        for i in range(300):
            try:
                self.l.reserve(f"b{i}", rnd.choice(list(ALLOC)), rnd.randint(0, 9000), "x")
                self.l.draw(f"b{i}", "u", rnd.randint(0, 9000))
            except SpendBlocked:
                pass
            self.assertLessEqual(self.l.consumato() + self.l.impegnato_aperto(), 50000)


if __name__ == "__main__":
    unittest.main()
