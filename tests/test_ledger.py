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


def _riserva_in_processo(args):
    path, i = args
    from studio.ledger import Ledger as L, SpendBlocked as SB
    led = L(path, 50000, ALLOC, list(ALLOC))
    try:
        led.reserve(f"p{i}/ads", "ads", 3000, f"processo {i}")
        return True
    except SB:
        return False


class TestSospensione(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.sosp = os.path.join(self.d, "sospensione.json")
        self._old = os.environ.get("STUDIO_SOSPENSIONE")
        os.environ["STUDIO_SOSPENSIONE"] = self.sosp
        self.l = Ledger(os.path.join(self.d, "l.json"), 50000, ALLOC, list(ALLOC))

    def tearDown(self):
        if self._old is None:
            os.environ.pop("STUDIO_SOSPENSIONE", None)
        else:
            os.environ["STUDIO_SOSPENSIONE"] = self._old

    def _sospendi(self):
        with open(self.sosp, "w") as f:
            f.write('{"spese": true, "motivo": "test"}')

    def test_nuova_riserva_bloccata_e_ripresa(self):
        self._sospendi()
        with self.assertRaises(SpendBlocked) as c:
            self.l.reserve("r/ads", "ads", 1000, "x")
        self.assertIn("sospese dal titolare", c.exception.motivo)
        with self.assertRaises(SpendBlocked):
            self.l.spend_once("r/ai", "ai", 100, 100, "x")
        with self.assertRaises(SpendBlocked):
            self.l.prenota("r/", {"ads": 1000})
        self.assertEqual(self.l.data["buste"], {})
        os.remove(self.sosp)
        self.assertEqual(self.l.reserve("r/ads", "ads", 1000, "x")["stato"], "aperta")

    def test_busta_esistente_e_consumo_consentiti(self):
        self.l.reserve("r/ads", "ads", 1000, "x")
        self._sospendi()
        self.assertEqual(self.l.reserve("r/ads", "ads", 1000, "x")["id"], "r/ads")
        self.assertTrue(self.l.draw("r/ads", "d1", 400))
        self.assertEqual(self.l.consumato("ads"), 400)

    def test_trasferimento_da_prenotazione_bloccato(self):
        self.l.prenota("r/", {"ads": 2000})
        self._sospendi()
        with self.assertRaises(SpendBlocked):
            self.l.reserve("r/ads", "ads", 1000, "x")

    def test_sospensione_attiva(self):
        self.assertIsNone(self.l.sospensione_attiva())
        self._sospendi()
        self.assertEqual(self.l.sospensione_attiva()["motivo"], "test")
        with open(self.sosp, "w") as f:
            f.write('{"spese": false}')
        self.assertIsNone(self.l.sospensione_attiva())

    def test_malformato_non_blocca_ma_avvisa(self):
        with open(self.sosp, "w") as f:
            f.write("{non json")
        self.assertIsNone(self.l.sospensione_attiva())
        self.assertEqual(len(self.l.data["bloccati"]), 1)
        self.assertEqual(self.l.reserve("r/ads", "ads", 1000, "x")["stato"], "aperta")


class TestLedgerConcorrenza(unittest.TestCase):
    """Processi reali in parallelo su un registro NUOVO: nessuna riserva persa, allocazione rispettata (QA N-3, B-1)."""

    def test_creazione_e_riserve_concorrenti(self):
        import multiprocessing as mp
        path = os.path.join(tempfile.mkdtemp(), "nuovo.json")
        with mp.get_context("fork").Pool(12) as pool:
            esiti = pool.map(_riserva_in_processo, [(path, i) for i in range(12)])
        led = Ledger(path, 50000, ALLOC, list(ALLOC))
        riuscite = [i for i, ok in enumerate(esiti) if ok]
        self.assertEqual(len(riuscite), ALLOC["ads"] // 3000)  # 6 da 30 € entro i 200 € di Ads
        self.assertEqual(sorted(k for k in led.data["buste"]), sorted(f"p{i}/ads" for i in riuscite))
        self.assertLessEqual(led.usato_categoria("ads"), ALLOC["ads"])
