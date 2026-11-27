"""QA T-035: riverifica della scheda V2-T031-3-44 (Wareneinsatz DE) dopo D-039.

Fissa le prove del verdetto in qa/2026-11-27-selezione.md: due fonti lette su host diversi,
impronte coincidenti con l'indice, prezzi presenti nel testo salvato, punteggio esattamente
alla soglia (60) e quindi sensibile a ogni riduzione di 1 punto."""
import hashlib
import json
import os
import unittest

from studio import phases

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEDA = os.path.join(RADICE, "research", "V2-T031-3-44.json")
FONTI = os.path.join(RADICE, "research", "fonti")


def _corpo(nome):
    with open(os.path.join(FONTI, nome), encoding="utf-8") as f:
        t = f.read()
    return t[t.index("\n\n") + 2:-1]


@unittest.skipUnless(os.path.exists(SCHEDA), "scheda di ricerca assente")
class TestQASelezioneWareneinsatz(unittest.TestCase):
    def setUp(self):
        with open(SCHEDA, encoding="utf-8") as f:
            self.o = json.load(f)

    def test_due_host_indipendenti_lette(self):
        self.assertEqual(phases.fonti_osservate(self.o), 2)

    def test_impronte_coincidono_con_indice(self):
        with open(os.path.join(FONTI, "indice.jsonl"), encoding="utf-8") as f:
            righe = [json.loads(r) for r in f if r.strip()]
        for imp in ("06ddd0a4b7e1", "1d755b27fb09"):
            rec = [r for r in righe if r.get("impronta", "").startswith(imp)]
            self.assertEqual(len(rec), 1)
            self.assertEqual(rec[0]["livello"], "letta_integralmente")
            corpo = _corpo(rec[0]["file"])
            self.assertEqual(hashlib.sha256(corpo.encode()).hexdigest(), rec[0]["impronta"])

    def test_prezzi_softguide_nel_testo(self):
        corpo = _corpo("2026-11-27-06ddd0a4b7e1.txt")
        for frammento in ("ab 150,-", "290,-", "500,-", "zzgl. 19% MwSt", "jährlich",
                          "+ Preiskalkulation", "Kalkulation (Wareneinsatz",
                          "innerhalb von 24 Stunden", "kostenlosen Registrierung"):
            self.assertIn(frammento, corpo)

    def test_punteggio_esattamente_alla_soglia(self):
        self.assertEqual(phases.punteggio(self.o), 60)
        for k in self.o["punteggi"]:
            p = dict(self.o["punteggi"])
            p[k] -= 1
            self.assertLess(phases.punteggio(dict(self.o, punteggi=p)), 60, k)


if __name__ == "__main__":
    unittest.main()
