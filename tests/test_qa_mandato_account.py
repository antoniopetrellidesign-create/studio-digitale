"""Test avversariali del QA indipendente sul mandato account (T-017, D-017…D-022).

Scritti da qa-indipendente, che non ha scritto il codice verificato.
Regole: solo libreria standard + `age` locale, directory temporanee, nessuna rete esterna
(l'unico server HTTP è su 127.0.0.1). Verdetto: qa/2026-11-23-mandato-account.md.
I test con @unittest.expectedFailure dimostrano un DIFETTO REALE: va corretto il codice dal responsabile,
non il test.
"""
import base64
import contextlib
import copy
import hashlib
import hmac
import io
import json
import os
import shutil
import socket
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

import studio.__main__ as cli
import studio.vault as vault_mod
from studio import economics
from studio.accounts import AccountRegistry, AttivazioneRifiutata
from studio.adapters.base import ExternalActionBlocked, ExternalGate
from studio.adapters.live_shopify import LiveShopify, verifica_webhook
from studio.ledger import Ledger, SpendBlocked
from studio.orders import valori_ordine
from studio.phases import g_social, h_catalogo
from studio.storage import read_json
from studio.vault import Vault, genera_password
from studio.workflow import Run, carica_json, carica_scenario, nuovo_run

POL = carica_json("config/policy.json")
CATALOGO = carica_json("config/account_catalogo.json")
HA_AGE = shutil.which("age") is not None and shutil.which("age-keygen") is not None


def _ledger(d):
    return Ledger(os.path.join(d, "l.json"), POL["tetto_primo_test_cents"], POL["allocazione_budget_cents"],
                  POL["categorie_spesa"])


def _chiave(d, nome="titolare.key"):
    k = os.path.join(d, nome)
    subprocess.run(["age-keygen", "-o", k], check=True, capture_output=True)
    pub = [l.split(": ")[1].strip() for l in open(k) if l.startswith("# public key")][0]
    return k, pub


class _Tmp(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)


@contextlib.contextmanager
def _solo_loopback():
    """Qualsiasi connect() verso un host non locale fallisce e viene registrato."""
    tentativi = []
    orig = socket.socket.connect

    def connect(self, addr):
        host = addr[0] if isinstance(addr, tuple) else addr
        if host not in ("127.0.0.1", "::1", "localhost") and not isinstance(addr, (str, bytes)):
            tentativi.append(addr)
            raise OSError(f"QA: rete esterna vietata ({addr})")
        return orig(self, addr)
    with mock.patch.object(socket.socket, "connect", connect):
        yield tentativi


# =========================================================================== vault / CLI
@unittest.skipUnless(HA_AGE, "age non installato")
class TestQAVault(_Tmp):
    def _cartella_root(self, con_chiave=True):
        os.makedirs(os.path.join(self.d, "config"))
        key, pub = _chiave(self.d)
        with open(os.path.join(self.d, "config", "accessi_destinatari.txt"), "w") as f:
            f.write("# commento\n" + (pub + "\n" if con_chiave else ""))
        return key

    def _cli(self, argv, generate):
        orig = vault_mod.genera_password

        def g(*a):
            p = orig(*a)
            generate.append(p)
            return p
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(cli, "ROOT", self.d), mock.patch.object(vault_mod, "genera_password", g), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = cli.main(argv)
        return rc, out.getvalue() + err.getvalue()

    def _nessun_file_contiene(self, segreto):
        for radice, _, files in os.walk(self.d):
            for f in files:
                with open(os.path.join(radice, f), encoding="utf-8", errors="ignore") as h:
                    self.assertNotIn(segreto, h.read(), os.path.join(radice, f))

    def test_cli_genera_password_non_stampata_ne_scritta_in_chiaro(self):
        self._cartella_root()
        gen = []
        rc, testo = self._cli(["accessi", "nuovo", "--servizio", "shopify", "--dati", '{"funzione": "negozio"}',
                               "--genera-password"], gen)
        self.assertEqual(rc, 0)
        self.assertEqual(len(gen), 1)
        self.assertNotIn(gen[0], testo)
        self.assertIn("segreto://shopify/password", testo)
        self._nessun_file_contiene(gen[0])

    def test_cli_senza_chiave_del_titolare_rifiuta_e_non_scrive(self):
        self._cartella_root(con_chiave=False)
        gen = []
        rc, testo = self._cli(["accessi", "nuovo", "--servizio", "x", "--genera-password"], gen)
        self.assertEqual(rc, 2)
        self.assertIn("RIFIUTATO", testo)
        self.assertNotIn(gen[0], testo)
        self.assertEqual(os.listdir(os.path.join(self.d, "accessi", "voci")), [])
        self._nessun_file_contiene(gen[0])

    def test_senza_chiave_privata_del_titolare_non_si_decifra(self):
        self._cartella_root()
        v = Vault(os.path.join(self.d, "accessi"), os.path.join(self.d, "config", "accessi_destinatari.txt"))
        pw = genera_password()
        v.registra("svc", "creazione", {"password": pw, "funzione": "f"})
        altra, _ = _chiave(self.d, "agente.key")  # chiave di un estraneo/agente
        with self.assertRaises(subprocess.CalledProcessError) as cm:
            v.esporta(altra)
        self.assertNotIn(pw.encode(), cm.exception.stdout or b"")
        self.assertNotIn(pw.encode(), cm.exception.stderr or b"")
        self.assertNotIn(pw, str(cm.exception))

    def test_destinatario_malformato_non_produce_voci_in_chiaro(self):
        for dest in ("age1malformata", "ssh-ed25519 AAAAmalformata", "age1zz\nage1"):
            d = tempfile.mkdtemp(dir=self.d)
            p = os.path.join(d, "dest.txt")
            open(p, "w").write(dest + "\n")
            v = Vault(os.path.join(d, "acc"), p)
            with self.assertRaises(subprocess.CalledProcessError) as cm:
                v.registra("svc", "creazione", {"password": "QA-SEGRETO-in-chiaro-1", "funzione": "f"})
            self.assertNotIn("QA-SEGRETO-in-chiaro-1", str(cm.exception))
            self.assertEqual(os.listdir(os.path.join(d, "acc", "voci")), [])
            self.assertFalse(os.path.exists(os.path.join(d, "acc", "indice.json")))

    def test_indice_senza_campi_segreti_anche_con_nomi_imprevisti(self):
        self._cartella_root()
        v = Vault(os.path.join(self.d, "accessi"), os.path.join(self.d, "config", "accessi_destinatari.txt"))
        v.registra("svc", "creazione", {"funzione": "f", "pin": "QA-PIN-777", "segreto_webhook": "QA-WH-888",
                                        "token": "QA-TOK-999"})
        for f in ("indice.json", "INDICE.md"):
            t = open(os.path.join(self.d, "accessi", f), encoding="utf-8").read()
            for s in ("QA-PIN-777", "QA-WH-888", "QA-TOK-999"):
                self.assertNotIn(s, t)

    def test_voci_append_only(self):
        self._cartella_root()
        v = Vault(os.path.join(self.d, "accessi"), os.path.join(self.d, "config", "accessi_destinatari.txt"))
        v.registra("svc", "creazione", {"password": "a"})
        v.registra("svc", "revoca", {"stato_verifica": "revocato"})
        self.assertEqual(len(os.listdir(os.path.join(self.d, "accessi", "voci"))), 2)

    # CORRETTO in D-023, riverificato dal QA — era DIFETTO (minore) studio/__main__.py:62,131-134 — `accessi nuovo --dati` accetta campi segreti
    # (password/token/chiave_api) passati come argomento della riga di comando: il valore finisce nella cronologia
    # della shell e nella trascrizione dell'agente. Atteso: rifiuto dei CAMPI_SEGRETI in --dati (solo
    # --genera-password o lettura da stdin/variabile).
    def test_cli_rifiuta_segreti_in_chiaro_negli_argomenti(self):
        self._cartella_root()
        rc, _ = self._cli(["accessi", "nuovo", "--servizio", "svc", "--dati", '{"password": "QA-in-argv"}'], [])
        self.assertNotEqual(rc, 0)


# =========================================================================== registro account
class TestQAAccount(_Tmp):
    def _reg(self, over=None):
        cat = copy.deepcopy(CATALOGO)
        for s in cat["servizi"]:
            s.update((over or {}).get(s["id"], {}))
        return AccountRegistry(cat, os.path.join(self.d, "account.json"))

    PREZZO_OK = {"prezzo": {"stato": "verificato", "max_mensile_cents": 3600,
                            "fonte": {"tipo": "osservata", "url": "https://esempio.invalid", "data": "2026-11-23"}},
                 "prova_gratuita": None}

    def test_nessun_account_prima_della_sua_fase(self):
        reg = self._reg({"shopify": self.PREZZO_OK})
        reg.conferma_attivo("email-dedicata")
        for fase in ("strategia", "ricerca", "selezione", "prodotto", "qa", "catalogo"):
            with self.assertRaises(AttivazioneRifiutata) as cm:
                reg.richiedi("shopify", fase, _ledger(self.d), "r/")
            self.assertTrue(any("fase" in m for m in cm.exception.motivi))
        self.assertEqual(reg.stato_di("shopify"), "pianificato")

    def test_dipendenza_non_attiva_blocca(self):
        reg = self._reg({"shopify": self.PREZZO_OK})
        with self.assertRaises(AttivazioneRifiutata) as cm:
            reg.richiedi("shopify", "shopify", _ledger(self.d), "r/")
        self.assertIn("dipendenza 'email-dedicata' non attiva", cm.exception.motivi)

    def test_prezzo_da_verificare_o_senza_massimo_blocca(self):
        for prezzo in ({"stato": "da_verificare", "max_mensile_cents": 0},
                       {"stato": "verificato", "max_mensile_cents": None}):
            reg = self._reg({"shopify": {"prezzo": prezzo, "prova_gratuita": None}})
            reg.conferma_attivo("email-dedicata")
            self.assertTrue(any("prezzo" in m for m in reg.verifica("shopify", "shopify")))

    def test_prova_gratuita_senza_scadenza_blocca(self):
        for pg in ({"stato": "verificato", "scadenza": None}, {"stato": "da_verificare", "scadenza": "2026-12-01"}):
            reg = self._reg({"shopify": {**self.PREZZO_OK, "prova_gratuita": pg}})
            reg.conferma_attivo("email-dedicata")
            self.assertTrue(any("prova gratuita" in m for m in reg.verifica("shopify", "shopify")))

    def test_canone_riservato_e_limitato_da_allocazione_e_tetto(self):
        led = _ledger(self.d)
        reg = self._reg({"shopify": self.PREZZO_OK})
        reg.conferma_attivo("email-dedicata")
        rec = reg.richiedi("shopify", "shopify", led, "r/", mesi=2)
        self.assertEqual(rec["impegno_cents"], 7200)
        self.assertEqual(led.data["buste"]["r/account-shopify"]["max_cents"], 7200)
        self.assertEqual(rec["stato"], "in_attesa_titolare")
        # oltre l'allocazione piattaforma (8000) → blocco, nessun account registrato
        reg2 = AccountRegistry({"servizi": [dict(s, prezzo={"stato": "verificato", "max_mensile_cents": 9000,
                                                            "fonte": {"tipo": "osservata", "url": "https://esempio.invalid/p",
                                                                     "data": "2026-11-23"}}, prova_gratuita=None,
                                                 dipende_da=[]) for s in CATALOGO["servizi"] if s["id"] == "shopify"]},
                               os.path.join(self.d, "a2.json"))
        with self.assertRaises(SpendBlocked):
            reg2.richiedi("shopify", "shopify", _ledger(tempfile.mkdtemp(dir=self.d)), "q/")
        self.assertEqual(reg2.stato_di("shopify"), "pianificato")
        # mesi negativi non generano riserve negative
        reg3 = AccountRegistry(copy.deepcopy(reg.catalogo) and {"servizi": list(copy.deepcopy(reg.catalogo).values())},
                               os.path.join(self.d, "a3.json"))
        reg3.conferma_attivo("email-dedicata")
        with self.assertRaises(SpendBlocked):
            reg3.richiedi("shopify", "shopify", _ledger(tempfile.mkdtemp(dir=self.d)), "n/", mesi=-1)

    def test_richiesta_ripetuta_non_riserva_due_volte(self):
        led = _ledger(self.d)
        reg = self._reg({"shopify": self.PREZZO_OK})
        reg.conferma_attivo("email-dedicata")
        reg.richiedi("shopify", "shopify", led, "r/")
        reg.richiedi("shopify", "shopify", led, "r/")
        self.assertEqual(led.impegnato_aperto(), 3600)

    def test_catalogo_reale_nessun_account_attivabile_oggi(self):
        reg = self._reg()
        for sid in reg.catalogo:
            if sid in ("ads", "social"):
                continue  # vedi difetto sul prezzo 'verificato' con fonte ipotesi
            self.assertTrue(reg.verifica(sid, "decisione"), sid)

    # CORRETTO in D-023, riverificato dal QA — era DIFETTO (medio) studio/accounts.py:52-53 + config/account_catalogo.json (servizio "social") — un prezzo con
    # stato "verificato" è accettato anche se la fonte è un'ipotesi o manca la data: la regola 3 del registro
    # ("prezzo verificato (fonte + data)", D-017) non è applicata. Il catalogo stesso dichiara "social" verificato
    # con fonte {"tipo": "ipotesi"} senza data.
    def test_prezzo_verificato_richiede_fonte_osservata_e_data(self):
        reg = self._reg({"shopify": {"prezzo": {"stato": "verificato", "max_mensile_cents": 3600,
                                                "fonte": {"tipo": "ipotesi"}}, "prova_gratuita": None}})
        reg.conferma_attivo("email-dedicata")
        self.assertTrue(any("prezzo" in m for m in reg.verifica("shopify", "shopify")))

    # CORRETTO in D-023, riverificato dal QA — era DIFETTO (medio) studio/phases.py:331-337 — la fase Shopify attiva l'account con `conferma_attivo` dopo la sola
    # `verifica`, senza `AccountRegistry.richiedi`: il canone del catalogo (max_mensile_cents × mesi) non viene
    # riservato dal registro account (account.json non ha busta né impegno). La spesa di piattaforma dipende solo
    # da `costi_piattaforma` dello scenario: con lista vuota l'account diventa attivo senza alcuna riserva.
    def test_fase_shopify_riserva_il_canone_tramite_registro(self):
        sc = carica_scenario("completo")
        sc["costi_piattaforma"] = []
        run = Run(os.path.join(self.d, "r"), sc)
        run.avanza()
        acc = read_json(os.path.join(self.d, "r", "account.json"))["account"]["shopify"]
        self.assertEqual(acc["stato"], "attivo")
        self.assertTrue(acc.get("busta"), acc)
        self.assertEqual(acc.get("impegno_cents"), 3600)


# =========================================================================== catalogo e marketplace
class _FintoRun:
    def __init__(self, scenario, artefatti=None):
        self.scenario, self.art, self.azioni = scenario, artefatti or {}, []

    def azione_titolare(self, *a):
        self.azioni.append(a)

    def artifact(self, n):
        return self.art[n]


class TestQACatalogo(_Tmp):
    def test_canali_con_regole_prodotto_o_ai_a_zero_esclusi(self):
        cfg = carica_json("config/canali_vendita.json")
        for regola in ("regole_prodotto", "regole_ai"):
            over = {c["id"]: {"punteggi_default": {**c["punteggi_default"], regola: 0}} for c in cfg["canali"]}
            out = h_catalogo(_FintoRun({"canali_vendita_override": over}))
            self.assertEqual(out["canali_selezionati"], [], regola)
            self.assertTrue(all("regole" in e["motivo"] for e in out["esclusi"]))
        # chiave mancante = 0 (prudente)
        p = {k: v for k, v in cfg["canali"][1]["punteggi_default"].items() if k != "regole_ai"}
        out = h_catalogo(_FintoRun({"canali_vendita_override": {cfg["canali"][1]["id"]: {"punteggi_default": p}}}))
        self.assertNotIn(cfg["canali"][1]["id"], [c["id"] for c in out["canali_selezionati"]])

    def test_ordine_marketplace_senza_commissione_di_pagamento_del_sito(self):
        ip = POL["ipotesi_costi_variabili"]
        o = {"lordo_cents": 1900, "iva_bp": 1900, "rimborsato": False, "fee_canale": {"pct_bp": 950, "fissa_cents": 45}}
        self.assertEqual(valori_ordine(o, ip)["fee_pagamento_cents"], (1900 * 950 + 5000) // 10000 + 45)
        sito = valori_ordine({k: v for k, v in o.items() if k != "fee_canale"}, ip)["fee_pagamento_cents"]
        self.assertNotEqual(sito + valori_ordine(o, ip)["fee_pagamento_cents"], valori_ordine(o, ip)["fee_pagamento_cents"])

    def test_scenario_completo_margine_per_canale_vendita_coerente(self):
        run = nuovo_run(os.path.join(self.d, "r"), "completo")
        r = run.avanza()
        self.assertEqual(r["stato"], "completato")
        self.assertEqual(len(r["fasi_completate"]), 12)
        m = read_json(os.path.join(self.d, "r", "artifacts", "misurazione.json"))["metriche"]
        pcv = m["per_canale_vendita"]
        self.assertEqual(m["ordini"], 16)
        self.assertEqual(pcv["etsy"]["ordini"], 2)
        self.assertEqual(sum(c["ordini"] for c in pcv.values()), m["ordini"])
        self.assertEqual(sum(c["ricavi_netti_cents"] for c in pcv.values()), m["ricavi_netti_cents"])
        self.assertEqual(sum(c["fee_cents"] for c in pcv.values()), m["fee_pagamento_cents"])
        self.assertEqual(sum(c["margine_prima_acquisizione_cents"] for c in pcv.values()),
                         m["ricavi_netti_cents"] - m["fee_pagamento_cents"])
        ip = POL["ipotesi_costi_variabili"]
        for o in run.orders.ordini():
            if o.get("canale_vendita", "shopify") != "shopify":
                atteso = (o["lordo_cents"] - o["sconto_cents"]) * o["fee_canale"]["pct_bp"]
                self.assertEqual(valori_ordine(o, ip)["fee_pagamento_cents"],
                                 (atteso + 5000) // 10000 + o["fee_canale"]["fissa_cents"])
        # commissioni dei marketplace non finiscono nelle buste "commissione" dei creator
        self.assertEqual(run.ledger.consumato("commissione"), m["costi_cents"]["commissione"])

    def test_ordine_da_canale_escluso_non_entra(self):
        sc = carica_scenario("completo")
        c = carica_json("config/canali_vendita.json")["canali"][1]
        sc["canali_vendita_override"] = {c["id"]: {"punteggi_default": {**c["punteggi_default"], "regole_ai": 0}}}
        run = Run(os.path.join(self.d, "r"), sc)
        run.avanza()
        self.assertFalse([o for o in run.orders.ordini() if o.get("canale_vendita") == c["id"]])


# =========================================================================== social
class TestQASocial(_Tmp):
    def _out(self):
        return {"calendario": [{}] * 4, "contenuti": [{"id": "c", "promesse": ["p"]}], "link_tracciati": [],
                "piattaforme": [{"id": "x", "motivazione": "m"}], "pubblicato": False}

    def test_social_non_parte_con_prodotto_non_validato(self):
        for qa, dl in (("RESPINTO", True), ("APPROVATO", False)):
            run = _FintoRun({}, {"qa": {"verdetto": qa}, "ordine_prova": {"download_ok": dl},
                                 "prodotto": {"manifest": {"promesse": ["p"]}}})
            ok, motivi = g_social(run, self._out())
            self.assertFalse(ok)
            self.assertTrue(any("non validato" in m for m in motivi))

    def test_pubblicazione_bloccata(self):
        run = _FintoRun({}, {"qa": {"verdetto": "APPROVATO"}, "ordine_prova": {"download_ok": True},
                             "prodotto": {"manifest": {"promesse": ["p"]}}})
        out = self._out()
        self.assertTrue(g_social(run, out)[0])
        out["pubblicato"] = True
        self.assertFalse(g_social(run, out)[0])

    def test_scenario_completo_nessun_contenuto_pubblicato(self):
        run = nuovo_run(os.path.join(self.d, "r"), "completo")
        run.avanza()
        soc = read_json(os.path.join(self.d, "r", "artifacts", "social.json"))
        self.assertFalse(soc["pubblicato"])
        self.assertEqual({c["stato"] for c in soc["contenuti"]}, {"bozza"})
        with open(os.path.join(self.d, "r", "external_calls.jsonl")) as f:
            chiamate = [json.loads(l) for l in f]
        self.assertEqual({c["esito"] for c in chiamate}, {"simulato"})
        self.assertFalse([c for c in chiamate if "pubblica" in c["azione"] or c["servizio"] == "social"])


# =========================================================================== live_shopify
RICEVUTE = []


class _Finto(BaseHTTPRequestHandler):
    def do_POST(self):
        RICEVUTE.append(self.headers.get("X-Shopify-Access-Token"))
        self.rfile.read(int(self.headers["Content-Length"]))
        out = json.dumps({"data": {"shop": {"myshopifyDomain": "f.myshopify.com"},
                                   "currentAppInstallation": {"accessScopes": []}}}).encode()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *a):
        pass


class TestQALiveShopify(_Tmp):
    # CORRETTO dal Team Lead, riverificato dal QA — era DIFETTO (minore, latente) studio/adapters/base.py:36 — introdotto con D-023: `record(..., esito_forzato=...)`
    # accetta qualsiasi valore, anche "reale"/"simulato" in modalità live senza STUDIO_LIVE e senza collaudo, e in quel
    # caso non alza ExternalActionBlocked. Il cancello unico deve poter solo inasprire l'esito ("bloccato"), mai
    # allentarlo. Nessun chiamante attuale lo usa così (unico uso: live_shopify.py:52 con "bloccato").
    def test_esito_forzato_non_allenta_il_cancello(self):
        g = self._gate("live", ())
        for forzato in ("reale", "simulato"):
            with self.assertRaises(ExternalActionBlocked):
                g.record("shopify", "x", esito_forzato=forzato)

    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(("127.0.0.1", 0), _Finto)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.srv.server_port}/admin/api/graphql.json"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def _gate(self, mode="live", collaudate=("shopify",)):
        return ExternalGate(mode, os.path.join(self.d, "calls.jsonl"), collaudate)

    def test_combinazioni_bloccate_senza_richiesta(self):
        casi = [("live", "0", ("shopify",)), ("live", "1", ()), ("live", None, ("shopify",)), ("live", "true", ("shopify",))]
        for mode, env, coll in casi:
            RICEVUTE.clear()
            e = {"QA_TOKEN_ENV": "fittizio"}
            if env is not None:
                e["STUDIO_LIVE"] = env
            with mock.patch.dict(os.environ, e, clear=False):
                if env is None:
                    os.environ.pop("STUDIO_LIVE", None)
                with self.assertRaises(ExternalActionBlocked):
                    LiveShopify(self._gate(mode, coll), "f.myshopify.com", "QA_TOKEN_ENV", self.url).verifica_accesso()
            self.assertEqual(RICEVUTE, [], (mode, env, coll))

    def test_config_reale_nessuna_integrazione_collaudata(self):
        self.assertEqual(carica_json("config/integrazioni_collaudate.json")["collaudate"], [])

    def test_endpoint_esterni_rifiutati(self):
        for ep in ("https://evil.example/graphql", "https://x.myshopify.com.evil.example/g",
                   "https://evil.example#.myshopify.com", "https://evil.example?h=.myshopify.com"):
            with self.assertRaises(ValueError, msg=ep):
                LiveShopify(self._gate(), "x.myshopify.com", endpoint=ep)

    def test_prodotto_sempre_draft(self):
        import inspect
        from studio.adapters import live_shopify
        src = inspect.getsource(live_shopify.LiveShopify.crea_prodotto_bozza)
        self.assertIn('"status": "DRAFT"', src)
        self.assertNotIn("ACTIVE", src)

    def test_hmac_a_tempo_costante(self):
        import inspect
        self.assertIn("hmac.compare_digest", inspect.getsource(verifica_webhook))
        corpo, seg = b'{"id":1}', "segreto-di-prova"
        firma = base64.b64encode(hmac.new(seg.encode(), corpo, hashlib.sha256).digest()).decode()
        self.assertTrue(verifica_webhook(corpo, firma, seg))
        self.assertFalse(verifica_webhook(corpo + b" ", firma, seg))
        self.assertFalse(verifica_webhook(corpo, "", seg))
        self.assertFalse(verifica_webhook(corpo, None, seg))

    # CORRETTO in D-023, riverificato dal QA — era DIFETTO (alto) studio/adapters/base.py:31-34 + studio/adapters/live_shopify.py:45 — con un ExternalGate in
    # modalità "simulato" record() ritorna esito "simulato" senza eccezione, e LiveShopify esegue la richiesta HTTP
    # reale con il token: nessun controllo di STUDIO_LIVE=1 né dell'integrazione collaudata. Il cancello dipende
    # dall'assunzione che nessuno combini un adattatore reale con un gate simulato.
    def test_gate_simulato_non_lascia_passare_adattatore_reale(self):
        RICEVUTE.clear()
        with mock.patch.dict(os.environ, {"QA_TOKEN_ENV": "fittizio"}):
            os.environ.pop("STUDIO_LIVE", None)
            ad = LiveShopify(self._gate("simulato", ()), "f.myshopify.com", "QA_TOKEN_ENV", self.url)
            try:
                ad.verifica_accesso()
            except ExternalActionBlocked:
                pass
        self.assertEqual(RICEVUTE, [], "richiesta HTTP con token partita senza STUDIO_LIVE e senza collaudo")

    # CORRETTO in D-023, riverificato dal QA — era DIFETTO (medio) studio/adapters/live_shopify.py:38-41 — il controllo dell'host vale solo se `endpoint` è
    # passato esplicitamente: con `negozio="evil.example"` l'endpoint costruito è https://evil.example/... e il
    # token Admin verrebbe inviato a un host non Shopify.
    def test_negozio_non_shopify_rifiutato(self):
        with self.assertRaises(ValueError):
            LiveShopify(self._gate(), "evil.example")

    # CORRETTO in D-023, riverificato dal QA — era DIFETTO (minore) studio/adapters/live_shopify.py:40 — schema non controllato: http:// verso *.myshopify.com
    # è ammesso (token in chiaro sulla rete).
    def test_endpoint_http_non_cifrato_rifiutato(self):
        with self.assertRaises(ValueError):
            LiveShopify(self._gate(), "x.myshopify.com", endpoint="http://x.myshopify.com/admin/api/g.json")

    # CORRETTO in D-023, riverificato dal QA — era DIFETTO (minore) studio/adapters/live_shopify.py:28-30 — con segreto webhook vuoto (variabile mancante)
    # chiunque può firmare: HMAC con chiave vuota viene accettato. Atteso: False (o eccezione) se il segreto è vuoto.
    def test_hmac_con_segreto_vuoto_rifiutato(self):
        corpo = b'{"id":1}'
        firma = base64.b64encode(hmac.new(b"", corpo, hashlib.sha256).digest()).decode()
        self.assertFalse(verifica_webhook(corpo, firma, ""))


# =========================================================================== rete
class TestQANessunaRete(_Tmp):
    def test_tutti_gli_scenari_senza_rete_esterna(self):
        scen = sorted(f[:-5] for f in os.listdir(os.path.join(os.path.dirname(__file__), "..", "fixtures", "scenari"))
                      if f.endswith(".json"))
        with _solo_loopback() as tentativi, mock.patch("urllib.request.urlopen",
                                                       side_effect=AssertionError("urlopen in simulazione")):
            for s in scen:
                if s == "interruzione":
                    continue  # usa os._exit nel CLI; il gestore della fase è coperto da test_scenari
                try:
                    nuovo_run(os.path.join(self.d, s), s).avanza()
                except Exception as e:  # noqa: BLE001 — esito della fase non rilevante qui
                    if "rete" in str(e) or isinstance(e, AssertionError):
                        raise
        self.assertEqual(tentativi, [])


if __name__ == "__main__":
    unittest.main()
