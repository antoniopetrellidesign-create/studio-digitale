import os
import tempfile
import unittest

from studio.adapters import ExternalActionBlocked, ExternalGate
from studio.phases import SimulatedCrash
from studio.workflow import Run, nuovo_run


class TestWorkflow(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def _run(self, scenario, rid="r", **kw):
        return nuovo_run(os.path.join(self.d, rid), scenario, **kw)

    def test_ordine_delle_fasi_imposto(self):
        run = self._run("completo")
        with self.assertRaises(RuntimeError):
            run.esegui_fase("shopify")
        run.esegui_fase("strategia")
        with self.assertRaises(RuntimeError):
            run.esegui_fase("selezione")

    def test_output_mancante_blocca_il_passaggio(self):
        run = self._run("completo")
        with self.assertRaises(RuntimeError):
            run.artifact("prodotto")

    def test_completo_e_traccia_decisioni(self):
        r = self._run("completo").avanza()
        self.assertEqual(r["stato"], "completato")
        self.assertEqual(len(r["fasi_completate"]), 10)
        self.assertTrue(os.path.exists(os.path.join(self.d, "r", "decisions.jsonl")))

    def test_ripresa_in_processo_dopo_crash(self):
        run = self._run("interruzione")
        with self.assertRaises(SimulatedCrash):
            run.avanza()
        r = Run(os.path.join(self.d, "r")).avanza()
        self.assertEqual(r["stato"], "completato")
        self.assertEqual(r["riprese"], 1)
        ref = self._run("completo", rid="ref").avanza()
        self.assertEqual(r["registro"]["consumato_cents"], ref["registro"]["consumato_cents"])

    def test_concessione_titolare(self):
        run = self._run("shopify_senza_accesso")
        self.assertEqual(run.avanza()["stato"], "bloccato_titolare")
        run = Run(os.path.join(self.d, "r"))
        run.concedi("shopify")
        r = run.avanza()
        self.assertEqual(r["stato"], "completato")
        self.assertEqual(r["azioni_titolare"][0]["stato"], "concessa")

    def test_gate_live_blocca_e_registra(self):
        g = ExternalGate("live", os.path.join(self.d, "calls.jsonl"))
        with self.assertRaises(ExternalActionBlocked):
            g.record("ads", "crea_campagna", a_pagamento=True, busta="b")

    def test_azione_a_pagamento_senza_busta_rifiutata(self):
        g = ExternalGate("simulato", os.path.join(self.d, "calls.jsonl"))
        with self.assertRaises(ExternalActionBlocked):
            g.record("ads", "crea_campagna", a_pagamento=True)

    def test_run_esistente_non_sovrascritto(self):
        self._run("completo")
        with self.assertRaises(FileExistsError):
            self._run("completo")


if __name__ == "__main__":
    unittest.main()
