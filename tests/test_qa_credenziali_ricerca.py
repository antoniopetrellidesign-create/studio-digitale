"""Test del QA indipendente su T-021 (D-025…D-028): registro account senza segreti, credenziali di rete,
prova di continuità, schede di ricerca reali e graduatoria.

Scritti da qa-indipendente, che non ha scritto il codice verificato. Nessuna rete esterna: l'unico server HTTP
è su 127.0.0.1. Verdetto: qa/2026-11-23-credenziali-ricerca.md.
I test con @unittest.expectedFailure dimostrano un DIFETTO REALE: va corretto il file dal responsabile, non il test.
"""
import glob
import json
import os
import re
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

from studio.adapters.base import ExternalActionBlocked, ExternalGate
from studio.adapters.live_shopify import SEGNAPOSTO_RETE, LiveShopify, verifica_continuita
from studio.phases import SEGRETI, fonti_osservate, punteggio, valida_opportunita
from studio.vault import Vault

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESEARCH = os.path.join(RADICE, "research")
SCHEDE = sorted(glob.glob(os.path.join(RESEARCH, "A-*.json")) + glob.glob(os.path.join(RESEARCH, "B-*.json")))
POLICY = json.load(open(os.path.join(RADICE, "config", "policy.json"), encoding="utf-8"))["selezione"]
TOKEN_FINTO = "shp" + "at_" + "0123456789abcdef" * 2  # costruito a pezzi: GitHub blocca il letterale anche se finto  # formato di token, valore inventato per il test


class Registra(BaseHTTPRequestHandler):
    richieste = []

    def _rispondi(self):
        Registra.richieste.append({"path": self.path, "token": self.headers.get("X-Shopify-Access-Token")})
        out = json.dumps({"headers": {"X-Shopify-Access-Token": "VALORE-INIETTATO-DI-PROVA"},
                          "data": {"shop": {"name": "x", "myshopifyDomain": "x.myshopify.com"},
                                   "currentAppInstallation": {"accessScopes": []}}}).encode()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(out)

    do_GET = do_POST = _rispondi

    def log_message(self, *a):
        pass


class TestQARegistroAccount(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.v = Vault(os.path.join(self.d, "accessi"), os.path.join(self.d, "dest.txt"))

    def _testi(self):
        return [open(os.path.join(self.d, "accessi", n), encoding="utf-8").read() for n in ("registro.json", "REGISTRO.md")]

    def test_campi_segreti_rifiutati_e_riferimenti_ammessi(self):
        for k in ("password", "token", "codici_recupero", "chiave_api", "secret"):
            with self.assertRaises(ValueError):
                self.v.aggiorna_registro({"servizio": "s", k: "x"})
        for rif in ("https://x", "valore-nudo", TOKEN_FINTO):
            with self.assertRaises(ValueError):
                self.v.aggiorna_registro({"servizio": "s", "riferimento_credenziale": rif})
        self.v.aggiorna_registro({"servizio": "s", "riferimento_credenziale": "rete://x.myshopify.com/X-Shopify-Access-Token"})
        for t in self._testi():
            self.assertIsNone(SEGRETI.search(t))

    def test_risolto_token_nel_valore_di_un_campo_ammesso(self):
        # studio/vault.py:104 controlla solo il PREFISSO del riferimento; SEGRETI_VIETATI (vault.py:27) non è usato:
        # un token incollato dopo rete:// o segreto://, o in un altro campo ammesso, finisce in chiaro nel registro.
        casi = [{"servizio": "a", "riferimento_credenziale": "segreto://shopify/" + TOKEN_FINTO},
                {"servizio": "b", "riferimento_credenziale": "rete://x.myshopify.com/" + TOKEN_FINTO},
                {"servizio": "c", "url": "https://operativo:Pw-123456@admin.example"},
                {"servizio": "d", "funzione": "token admin " + TOKEN_FINTO}]
        for voce in casi:
            try:
                self.v.aggiorna_registro(voce)
            except ValueError:
                pass
        p = os.path.join(self.d, "accessi", "registro.json")
        testo = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
        self.assertNotIn(TOKEN_FINTO, testo)
        self.assertNotIn("Pw-123456", testo)

    def test_risolto_segreto_in_valore_non_stringa(self):
        # studio/vault.py:40-41: _controlla_valore salta i valori che non sono stringhe; un token dentro una lista o
        # un dizionario in un campo ammesso finisce in chiaro in registro.json.
        for voce in ({"servizio": "a", "funzione": [TOKEN_FINTO]}, {"servizio": "b", "costo": {"x": TOKEN_FINTO}}):
            try:
                self.v.aggiorna_registro(voce)
            except ValueError:
                pass
        p = os.path.join(self.d, "accessi", "registro.json")
        self.assertNotIn(TOKEN_FINTO, open(p, encoding="utf-8").read() if os.path.exists(p) else "")

    def test_registro_reale_nel_repository_senza_segreti(self):
        for n in ("registro.json", "REGISTRO.md", "indice.json", "INDICE.md"):
            p = os.path.join(RADICE, "accessi", n)
            if os.path.exists(p):
                t = open(p, encoding="utf-8").read()
                self.assertIsNone(SEGRETI.search(t), n)
                for rif in re.findall(r"riferimento_credenziale\"\s*:\s*\"([^\"]*)\"", t):
                    self.assertRegex(rif, r"^(rete|segreto)://")


class TestQACredenzialiRete(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(("127.0.0.1", 0), Registra)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.srv.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def setUp(self):
        Registra.richieste.clear()

    def _ad(self, mode="live", collaudate=("shopify",)):
        log = os.path.join(tempfile.mkdtemp(), "calls.jsonl")
        return LiveShopify(ExternalGate(mode, log, collaudate), "x.myshopify.com", endpoint=self.base + "/g",
                           credenziale="rete")

    def test_rete_nessuna_richiesta_se_il_cancello_e_chiuso(self):
        for env, mode, coll in (({"STUDIO_LIVE": "0"}, "live", ("shopify",)), ({"STUDIO_LIVE": "1"}, "live", ()),
                                ({"STUDIO_LIVE": "1"}, "simulato", ("shopify",))):
            with mock.patch.dict(os.environ, env):
                with self.assertRaises(ExternalActionBlocked):
                    self._ad(mode, coll).verifica_accesso()
        self.assertEqual(Registra.richieste, [])

    def test_rete_https_e_host_myshopify_obbligatori(self):
        g = ExternalGate("live", "/dev/null", ("shopify",))
        for ep in ("http://x.myshopify.com/g", "https://x.myshopify.com.evil.example/g", "https://myshopify.com.evil/g",
                   "https://evil.example/g"):
            with self.assertRaises(ValueError):
                LiveShopify(g, "x", endpoint=ep, credenziale="rete")
        with self.assertRaises(ValueError):
            LiveShopify(g, "evil.example", credenziale="rete")

    def test_rete_solo_segnaposto_nella_richiesta(self):
        env = {k: v for k, v in os.environ.items() if k != "SHOPIFY_ADMIN_TOKEN"}
        env.update({"STUDIO_LIVE": "1", "SHOPIFY_ADMIN_TOKEN": TOKEN_FINTO})
        with mock.patch.dict(os.environ, env, clear=True):
            self._ad().verifica_accesso()
        self.assertEqual([r["token"] for r in Registra.richieste], [SEGNAPOSTO_RETE])

    def test_continuita_restituisce_solo_impronta(self):
        # cancello APERTO in modo esplicito: live + STUDIO_LIVE=1 + 'eco' collaudata (server locale)
        g = ExternalGate("live", os.path.join(tempfile.mkdtemp(), "c.jsonl"), {"eco"})
        with mock.patch.dict(os.environ, {"STUDIO_LIVE": "1"}):
            r = verifica_continuita("h", self.base + "/eco", gate=g)
        self.assertEqual(set(r), {"presente", "impronta"})
        self.assertRegex(r["impronta"], r"^[0-9a-f]{12}$")
        self.assertNotIn("VALORE-INIETTATO-DI-PROVA", json.dumps(r))

    def test_risolto_continuita_senza_gate_o_fuori_elenco(self):
        # D-4 (prima parte, corretta): gate obbligatorio, solo https verso eco ammessi, cancello live chiuso => blocco.
        with self.assertRaises(ValueError):
            verifica_continuita("h", self.base + "/eco")
        g = ExternalGate("live", os.path.join(tempfile.mkdtemp(), "c.jsonl"), {"eco"})
        for url in ("http://httpbin.org/headers", "https://evil.example/h", "https://httpbin.org.evil/h"):
            with self.assertRaises(ValueError):
                verifica_continuita("h", url, gate=g)
        with mock.patch.dict(os.environ, {"STUDIO_LIVE": "0"}):
            with self.assertRaises(ExternalActionBlocked):
                verifica_continuita("h", self.base + "/eco", gate=g)
        self.assertEqual(Registra.richieste, [])

    def test_risolto_continuita_connessione_reale_in_modalita_simulato(self):
        # studio/adapters/live_shopify.py:120-122: con ExternalGate("simulato") gate.record non solleva e la funzione
        # apre comunque una connessione REALE verso https://httpbin.org (host a cui il proxy inietta la credenziale),
        # senza STUDIO_LIVE=1 e senza 'eco' collaudata. Qui urlopen è sostituito: nessuna rete viene usata.
        from studio.adapters import live_shopify as ls
        tentate = []

        def finto(req, timeout=0):
            tentate.append(req.full_url)
            raise OSError("rete bloccata dal test")

        env = {k: v for k, v in os.environ.items() if k != "STUDIO_LIVE"}
        with mock.patch.dict(os.environ, env, clear=True), mock.patch.object(ls.urllib.request, "urlopen", finto):
            try:
                verifica_continuita("h", "https://httpbin.org/headers",
                                    gate=ExternalGate("simulato", os.path.join(tempfile.mkdtemp(), "c.jsonl")))
            except (OSError, ExternalActionBlocked):
                pass
        self.assertEqual(tentate, [])

    def test_file_continuita_solo_impronta_troncata(self):
        p = os.path.join(RADICE, "accessi", ".continuita-httpbin")
        t = open(p, encoding="utf-8").read()
        self.assertRegex(t, r"^[0-9a-f]{12}\n?$")


class TestQASchedeRicerca(unittest.TestCase):
    def test_problema_e_concorrenza_al_massimo_6_con_soli_estratti(self):
        # D-028: senza pagine lette, problema e concorrenza <= 6
        for p in SCHEDE:
            o = json.load(open(p, encoding="utf-8"))
            self.assertLessEqual(o["punteggi"]["problema"], 6, p)
            self.assertLessEqual(o["punteggi"]["concorrenza"], 6, p)

    def test_schede_presenti_valide_e_reali(self):
        self.assertEqual(len(SCHEDE), 12)
        for p in SCHEDE:
            o = json.load(open(p, encoding="utf-8"))
            self.assertEqual(valida_opportunita(o), [], p)
            self.assertIs(o.get("sintetico"), False, p)
            for f in o["fonti"]:
                if f["tipo"] == "osservata":
                    self.assertRegex(f.get("url", ""), r"^https://", p)
                    self.assertRegex(f.get("data", ""), r"^2026-\d\d-\d\d$", p)
                    self.assertNotIn(".invalid", f["url"], p)

    def test_nessuna_selezione_sotto_soglia(self):
        for p in SCHEDE:
            o = json.load(open(p, encoding="utf-8"))
            idonea = punteggio(o) >= POLICY["punteggio_minimo"] and fonti_osservate(o) >= POLICY["fonti_osservate_minime"]
            self.assertFalse(idonea, p)
            esito = re.sub(r"non\s+(selezionat\w*|idone\w*)", "", str(o.get("esito", "")).lower())
            self.assertNotRegex(esito, r"selezionat|idone", p)
        self.assertEqual([x for x in glob.glob(os.path.join(RADICE, "products", "*")) if not x.endswith(".gitkeep")], [])

    def test_risolto_graduatoria_corrisponde_al_motore(self):
        # research/GRADUATORIA-2026-11-23.md:15-17 riporta 58/58/57 e 4/3/2 fonti osservate, ma le schede attuali
        # (modificate in a18ef93) danno 47/52/50 e 0/3/2 con studio.phases.punteggio / fonti_osservate.
        graduatoria = open(os.path.join(RESEARCH, "GRADUATORIA-2026-11-23.md"), encoding="utf-8").read()
        mappa = {"Planificador de oposiciones": "B-es-planificador-oposiciones", "Haushaltsbuch": "B-de-haushaltsbuch",
                 "Language learning planner": "B-en-language-learning-planner", "Bilancio familiare": "B-it-bilancio-familiare",
                 "Home maintenance binder": "B-en-home-maintenance-binder", "Freelance tracker": "A-freelance-tracker-en",
                 "Calcolatore prezzi": "A-etsy-pricing-en", "Welcome book": "A-welcome-book-en",
                 "Gästemappe": "A-gaestemappe-de", "Classeur administratif": "B-fr-classeur-administratif",
                 "Calendario editoriale": "A-content-calendar-en", "Angebot/Rechnung": "A-angebot-kleinunternehmer-de"}
        diff = []
        for riga in graduatoria.splitlines():
            m = re.match(r"\|\s*\d+\s*\|\s*([^|]+)\|[^|]+\|\s*\**(\d+)\**\s*\|\s*(\d+)", riga)
            if not m:
                continue
            sid = next(v for k, v in mappa.items() if riga.split("|")[2].strip().startswith(k))
            o = json.load(open(os.path.join(RESEARCH, sid + ".json"), encoding="utf-8"))
            if (punteggio(o), fonti_osservate(o)) != (int(m.group(2)), int(m.group(3))):
                diff.append((sid, int(m.group(2)), punteggio(o), int(m.group(3)), fonti_osservate(o)))
        self.assertEqual(diff, [])

    def test_risolto_esito_coerente_col_punteggio(self):
        # research/B-en-language-learning-planner.json:43 scrive "punteggio 57" ma il motore dà 50.
        for p in SCHEDE:
            o = json.load(open(p, encoding="utf-8"))
            for n in re.findall(r"punteggio (\d+)", str(o.get("esito", ""))):
                self.assertEqual(int(n), punteggio(o), p)

    def test_risolto_prezzi_osservati_senza_fonte(self):
        # Ogni cifra di un concorrente marcato "osservata" deve comparire in una fonte osservata della stessa scheda.
        # Mancano: research/B-de-haushaltsbuch.json:21 ("7,03 CAD") e research/B-en-home-maintenance-binder.json:17 ("9,91").
        mancanti = []
        for p in SCHEDE:
            o = json.load(open(p, encoding="utf-8"))
            oss = " ".join(json.dumps(f, ensure_ascii=False) for f in o["fonti"] if f.get("tipo") == "osservata")
            for c in o.get("concorrenti", []):
                if c.get("tipo_dato") == "osservata":
                    for n in re.findall(r"\d+[.,]\d+|\d+", c.get("prezzo", "")):
                        if n not in oss and n.replace(",", ".") not in oss:
                            mancanti.append((os.path.basename(p), c["nome"], n))
        self.assertEqual(mancanti, [])


if __name__ == "__main__":
    unittest.main()
