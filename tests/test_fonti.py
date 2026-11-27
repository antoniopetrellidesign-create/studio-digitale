"""Lettore delle fonti: solo host consentiti, redirect controllati, testo e impronta salvati (server locale)."""
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from studio import fonti


class Finto(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/fuori":
            self.send_response(302); self.send_header("Location", "https://evil.example/x"); self.end_headers(); return
        corpo = ("<html><head><title>Planner IHK</title><script>var x='segreto'</script></head><body>"
                 "<h1>Lernplan</h1><p>" + "Prüfungsvorbereitung mit Plan. " * 20 + "</p></body></html>").encode()
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *a):
        pass


class TestFonti(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(("127.0.0.1", 0), Finto)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.srv.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        self.d = tempfile.mkdtemp()

    def test_host_non_consentito_rifiutato(self):
        for u in ("https://evil.example/x", "http://www.etsy.com/x", "ftp://www.etsy.com/x"):
            with self.assertRaises(fonti.HostNonConsentito):
                fonti.leggi(u, self.d, consentiti={"www.etsy.com"})
        self.assertFalse(os.path.exists(os.path.join(self.d, "indice.jsonl")))

    def test_lettura_salva_testo_senza_script_e_indice(self):
        r = fonti.leggi(self.base + "/p", self.d, consentiti=set(), locale_ok=True)
        self.assertEqual(r["livello"], "letta_integralmente")
        self.assertEqual(r["titolo"], "Planner IHK")
        testo = open(os.path.join(self.d, r["file"]), encoding="utf-8").read()
        self.assertIn("Prüfungsvorbereitung", testo)
        self.assertNotIn("segreto", testo)
        idx = [json.loads(l) for l in open(os.path.join(self.d, "indice.jsonl"))]
        self.assertEqual(idx[-1]["impronta"], r["impronta"])

    def test_redirect_verso_host_non_consentito_rifiutato(self):
        with self.assertRaises(fonti.HostNonConsentito):
            fonti.leggi(self.base + "/fuori", self.d, consentiti=set(), locale_ok=True)

    def test_url_con_accenti_codificato(self):
        self.assertEqual(fonti.normalizza("https://www.amazon.de/s?k=prüfung+lernplan"),
                         "https://www.amazon.de/s?k=pr%C3%BCfung+lernplan")
        self.assertEqual(fonti.normalizza("https://x.de/a%20b?q=1"), "https://x.de/a%20b?q=1")
        r = fonti.leggi(self.base + "/prüfung?q=ü", self.d, consentiti=set(), locale_ok=True)
        self.assertEqual(r["livello"], "letta_integralmente")

    def test_errore_di_rete_registrato_come_non_leggibile(self):
        r = fonti.leggi("http://127.0.0.1:9/x", self.d, consentiti=set(), locale_ok=True, timeout=2)
        self.assertEqual(r["livello"], "non_leggibile")

    def test_elenco_host_sottoinsieme_ambiente(self):
        self.assertNotIn("httpbin.org", fonti.host_consentiti())


if __name__ == "__main__":
    unittest.main()


class TestPunteggioV2(unittest.TestCase):
    def _o(self, versione, livello, **p):
        base = {"problema": 9, "accesso": 8, "offerta": 8, "margine": 7, "concorrenza": 9, "costo_sviluppo": 7, "assistenza": 7}
        base.update(p)
        return {"metodo_versione": versione, "punteggi": base,
                "fonti": [{"tipo": "osservata", "url": "https://x", "data": "2026-11-27", "livello": livello}]}

    def test_tetto_d028_applicato_dal_motore(self):
        from studio.phases import punteggio
        letta = punteggio(self._o(2, "letta_integralmente"))
        estratto = punteggio(self._o(2, "risultato_di_ricerca"))
        self.assertGreater(letta, estratto)
        self.assertEqual(estratto, (20*6 + 20*8 + 15*8 + 15*7 + 15*6 + 8*7 + 7*7) // 10)

    def test_v1_invariato_senza_offerta(self):
        from studio.phases import punteggio
        o = self._o(1, "letta_integralmente"); o["punteggi"].pop("offerta"); o.pop("metodo_versione")
        self.assertEqual(punteggio(o), (25*9 + 20*8 + 20*7 + 15*9 + 10*7 + 10*7) // 10)
