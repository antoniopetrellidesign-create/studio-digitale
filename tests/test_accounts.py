import copy
import os
import tempfile
import unittest

from studio.accounts import AccountRegistry, AttivazioneRifiutata
from studio.ledger import Ledger, SpendBlocked
from studio.links import link_tracciato, tracciato
from studio.workflow import carica_json

POL = carica_json("config/policy.json")
CAT = carica_json("config/account_catalogo.json")


def _cat(**override):
    c = copy.deepcopy(CAT)
    for s in c["servizi"]:
        s.update(override.get(s["id"], {}))
    return c


class TestAccounts(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.led = Ledger(os.path.join(self.d, "l.json"), 50000, POL["allocazione_budget_cents"], POL["categorie_spesa"])

    def test_catalogo_reale_nessun_account_attivabile_ora(self):
        reg = AccountRegistry(CAT, os.path.join(self.d, "a.json"))
        for sid in reg.catalogo:
            if sid != "ads":
                self.assertTrue(reg.verifica(sid, "strategia"), sid)

    def test_account_prima_della_sua_fase_rifiutato(self):
        verif = {"prezzo": {"stato": "verificato", "max_mensile_cents": 0, "fonte": {"tipo": "osservata", "url": "https://esempio.invalid/prezzi", "data": "2026-11-23"}}, "dipende_da": []}
        reg = AccountRegistry(_cat(social=verif), os.path.join(self.d, "a.json"))
        with self.assertRaises(AttivazioneRifiutata) as c:
            reg.richiedi("social", "ricerca", self.led, "r/")
        self.assertIn("non ancora raggiunta", str(c.exception))
        self.assertEqual(reg.richiedi("social", "social", self.led, "r/")["stato"], "in_attesa_titolare")

    def test_prezzo_non_verificato_rifiutato(self):
        reg = AccountRegistry(_cat(shopify={"dipende_da": []}), os.path.join(self.d, "a.json"))
        with self.assertRaises(AttivazioneRifiutata):
            reg.richiedi("shopify", "shopify", self.led, "r/")
        self.assertEqual(self.led.consumato() + self.led.impegnato_aperto(), 0)

    def test_canone_riservato_e_oltre_allocazione_bloccato(self):
        ok = {"prezzo": {"stato": "verificato", "max_mensile_cents": 3900, "fonte": {"tipo": "osservata", "url": "https://esempio.invalid/prezzi", "data": "2026-11-23"}},
              "prova_gratuita": {"stato": "verificato", "scadenza": "2026-12-31", "condizioni": "x"}, "dipende_da": []}
        reg = AccountRegistry(_cat(shopify=ok), os.path.join(self.d, "a.json"))
        rec = reg.richiedi("shopify", "shopify", self.led, "r/", mesi=2)
        self.assertEqual(self.led.impegnato_aperto("piattaforma"), 7800)
        self.assertTrue(rec["rinnovo"]["chiusura_pianificata"])
        reg2 = AccountRegistry(_cat(shopify=ok), os.path.join(self.d, "b.json"))
        with self.assertRaises(SpendBlocked):
            reg2.richiedi("shopify", "shopify", self.led, "r2/", mesi=1)  # 7800 + 3900 > 8000 allocazione
        reg.revoca("shopify", self.led)
        self.assertEqual(self.led.impegnato_aperto("piattaforma"), 0)

    def test_passaggi_titolare_raggruppati(self):
        reg = AccountRegistry(CAT, os.path.join(self.d, "a.json"))
        p = reg.passaggi_titolare("strategia")
        self.assertTrue(any(x["servizio"] == "repo-privato" for x in p))
        self.assertFalse(any(x["servizio"] == "social" for x in p))

    def test_link_tracciati(self):
        u = link_tracciato("https://n.example/p?ref=1", "pinterest", "social", "prd-a", "c1")
        self.assertTrue(tracciato(u))
        self.assertIn("ref=1", u)
        self.assertFalse(tracciato("https://n.example/p?utm_source=x"))


if __name__ == "__main__":
    unittest.main()
