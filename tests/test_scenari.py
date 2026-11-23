"""Collaudo end-to-end in processi separati (interruzione reale del processo inclusa)."""
import json
import os
import tempfile
import unittest

from studio.collaudo import esegui


class TestCollaudo(unittest.TestCase):
    def test_tutti_gli_scenari(self):
        d = tempfile.mkdtemp()
        self.assertEqual(esegui(d), 0)
        with open(os.path.join(d, "report.json"), encoding="utf-8") as f:
            rep = json.load(f)
        falliti = [r["caso"] for r in rep if not r["ok"]]
        self.assertEqual(falliti, [])
        self.assertGreaterEqual(len(rep), 11)


if __name__ == "__main__":
    unittest.main()
