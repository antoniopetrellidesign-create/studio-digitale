"""Test avversariali del QA indipendente (T-009).

Scritti da qa-indipendente, che non ha scritto il codice verificato.
Regole: solo libreria standard, directory temporanee, nessuna rete.
I test marcati @unittest.expectedFailure dimostrano un DIFETTO REALE (descritto nel commento):
non vanno "aggiustati" qui, va corretto il codice dal responsabile.
Verdetti: qa/2026-11-23-collaudo-sistema.md (primo collaudo), qa/2026-11-23-riverifica.md (dopo D-013).
I commenti "CORRETTO in D-013" indicano i 13 difetti del primo collaudo, ora test di regressione normali.
"""
import copy
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from studio import economics
from studio.ledger import Ledger, SpendBlocked
from studio.money import pct_bp, scorporo_iva
from studio.orders import OrderBook, valori_ordine
from studio.phases import IVA_BP, NOMI_FASI
from studio.storage import read_json, read_jsonl
from studio.workflow import ROOT, Run, carica_json, carica_scenario, nuovo_run

POL = carica_json("config/policy.json")
COMM = carica_json("config/commissioni.json")
ALLOC = POL["allocazione_budget_cents"]
IP = POL["ipotesi_costi_variabili"]


def _ledger(d, nome="l.json"):
    return Ledger(os.path.join(d, nome), POL["tetto_primo_test_cents"], ALLOC, POL["categorie_spesa"])


def _attivo(led: Ledger) -> int:
    return led.consumato() + led.impegnato_aperto()


class _Tmp(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="qa-")
        self.addCleanup(shutil.rmtree, self.d, ignore_errors=True)

    def _run_sc(self, sc, rid="r", modalita="simulato", registro=None):
        return Run(os.path.join(self.d, rid), sc, modalita, registro)


# =========================================================================== registro e tetto
class TestQARegistro(_Tmp):
    def test_storno_e_nuovo_consumo_non_superano_il_massimo(self):
        led = _ledger(self.d)
        led.reserve("c", "commissione", 6000, "busta commissioni")
        led.draw("c", "A", 3000)
        led.draw("c", "B", 3000)
        led.undraw("c", "A", "rimborso")
        self.assertTrue(led.draw("c", "C", 3000))           # il tetto liberato dallo storno si riusa
        with self.assertRaises(SpendBlocked):                # ...ma riattivare A porterebbe a 9000 > 6000
            led.draw("c", "A", 3000)
        self.assertLessEqual(led._drawn(led.data["buste"]["c"]), 6000)

    def test_busta_chiusa_non_si_riapre(self):
        led = _ledger(self.d)
        led.reserve("a", "ads", 1000, "x")
        led.draw("a", "g1", 400)
        self.assertEqual(led.close("a"), 600)
        # stessa riserva ripetuta: ritorna la busta chiusa, non ne crea una nuova aperta
        self.assertEqual(led.reserve("a", "ads", 1000, "x")["stato"], "chiusa")
        with self.assertRaises(SpendBlocked):
            led.draw("a", "g2", 100)
        self.assertEqual(led.impegnato_aperto(), 0)

    def test_id_busta_ripetuto_con_importo_diverso_bloccato(self):
        led = _ledger(self.d)
        led.reserve("a", "ads", 1000, "x")
        with self.assertRaises(SpendBlocked):
            led.reserve("a", "ads", 20000, "x")
        with self.assertRaises(SpendBlocked):
            led.reserve("a", "piattaforma", 1000, "x")
        self.assertEqual(_attivo(led), 1000)

    def test_allocazione_non_aggirabile_con_buste_piccole(self):
        led = _ledger(self.d)
        for i in range(20):
            led.reserve(f"a{i}", "ads", 1000, "x")
        with self.assertRaises(SpendBlocked):
            led.reserve("a20", "ads", 1, "x")
        self.assertEqual(led.usato_categoria("ads"), ALLOC["ads"])

    def test_tetto_non_superabile_sommando_le_categorie(self):
        led = _ledger(self.d)
        for c, v in ALLOC.items():
            led.reserve(c, c, v, "x")
        self.assertEqual(led.residuo(), 0)
        with self.assertRaises(SpendBlocked):
            led.reserve("extra", "riserva", 1, "x")

    # CORRETTO in D-013, riverificato dal QA — era DIFETTO (minore) studio/ledger.py:124-125 — draw() con un draw_id già registrato e un importo DIVERSO
    # ritorna False in silenzio: l'importo nuovo è perso senza blocco né traccia in `bloccati`.
    # reserve() invece blocca i parametri diversi (riga 96-97): comportamento incoerente; una spesa reale
    # diversa da quella registrata sparisce dalla contabilità.
    def test_consumo_ripetuto_con_importo_diverso_e_segnalato(self):
        led = _ledger(self.d)
        led.reserve("a", "ads", 5000, "x")
        led.draw("a", "giorno-1", 1500)
        with self.assertRaises(SpendBlocked):
            led.draw("a", "giorno-1", 2500)

    # CORRETTO in D-013, riverificato dal QA — era DIFETTO (minore) studio/ledger.py:128 — draw() accetta un bool come importo (isinstance(True, int)),
    # mentre reserve() lo rifiuta (riga 99).
    def test_importo_booleano_rifiutato_nel_consumo(self):
        led = _ledger(self.d)
        led.reserve("a", "ads", 5000, "x")
        with self.assertRaises(SpendBlocked):
            led.draw("a", "g", True)

    # CORRETTO in D-013, riverificato dal QA — era DIFETTO (minore) studio/ledger.py:157-162 — spend_once(): se l'effettivo supera il massimo, draw() blocca
    # ma la busta resta APERTA con tutto il massimo impegnato; nessuno la chiude (non ha tag "canale:", quindi
    # nemmeno la Decisione). Il residuo resta ridotto per sempre. Conservativo per il tetto, ma impegno fantasma.
    def test_spesa_singola_bloccata_non_lascia_impegni_aperti(self):
        led = _ledger(self.d)
        with self.assertRaises(SpendBlocked):
            led.spend_once("p", "piattaforma", 3600, 4000, "costo effettivo oltre il massimo")
        self.assertEqual(led.impegnato_aperto(), 0)

    # CORRETTO in D-013, riverificato dal QA — era DIFETTO (importante) studio/ledger.py:44-46, 190-191 — registro condiviso senza blocco né rilettura:
    # ogni Ledger legge il file una sola volta e poi lo riscrive per intero. Due run sullo stesso --registro
    # in parallelo (ammesso dalla CLI) vedono ciascuno il residuo pieno: la seconda scrittura cancella la prima
    # e gli impegni reali superano allocazione e tetto senza che il registro lo mostri.
    def test_registro_condiviso_due_istanze_non_superano_l_allocazione(self):
        l1 = _ledger(self.d, "condiviso.json")
        l2 = _ledger(self.d, "condiviso.json")
        l1.reserve("run1/ads", "ads", ALLOC["ads"], "campagna run 1")
        with self.assertRaises(SpendBlocked):
            l2.reserve("run2/ads", "ads", ALLOC["ads"], "campagna run 2")


# =========================================================================== ordine delle fasi e ripresa
class TestQAFasi(_Tmp):
    def test_fasi_fuori_ordine_rifiutate_ovunque(self):
        run = nuovo_run(os.path.join(self.d, "r"), "completo")
        for f in NOMI_FASI[1:]:
            with self.assertRaises(RuntimeError):
                run.esegui_fase(f)
        run.esegui_fase("strategia")
        with self.assertRaises(RuntimeError):      # fase già approvata non si riesegue
            run.esegui_fase("strategia")

    def test_run_concluso_non_riesegue_nulla(self):
        run = nuovo_run(os.path.join(self.d, "r"), "completo")
        run.avanza()
        speso = run.ledger.consumato()
        run2 = Run(os.path.join(self.d, "r"))
        r = run2.avanza()
        self.assertEqual(r["registro"]["consumato_cents"], speso)
        self.assertTrue(all(v == 1 for v in r["tentativi"].values()))
        for f in NOMI_FASI:
            with self.assertRaises(RuntimeError):
                run2.esegui_fase(f)

    def test_resume_cli_su_run_completato_non_spende(self):
        run = nuovo_run(os.path.join(self.d, "r"), "completo")
        run.avanza()
        prima = read_json(run.ledger.path)
        p = subprocess.run([sys.executable, "-m", "studio", "resume", "--run-id", "r", "--runs-dir", self.d],
                           cwd=ROOT, env=dict(os.environ, PYTHONPATH=ROOT, STUDIO_LIVE="0"),
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(read_json(run.ledger.path), prima)

    def test_ripresa_dopo_blocco_non_riesegue_fasi_approvate(self):
        run = nuovo_run(os.path.join(self.d, "r"), "shopify_senza_accesso")
        run.avanza()
        run = Run(os.path.join(self.d, "r"))
        run.concedi("shopify")
        r = run.avanza()
        approvate = [d["fase"] for d in read_jsonl(os.path.join(self.d, "r", "decisions.jsonl"))
                     if d["decisione"] == "fase_approvata"]
        self.assertEqual(approvate, NOMI_FASI)  # ognuna una sola volta, nell'ordine
        self.assertEqual(r["stato"], "completato")

    # CORRETTO in D-013, riverificato dal QA — era DIFETTO (importante) studio/phases.py:141-155 (g_selezione) — il controllo di Selezione verifica il budget
    # dei canali e della piattaforma ma NON il costo AI delle fasi restanti (7 fasi × costi_ai max). Con
    # l'allocazione AI quasi esaurita il test passa la Selezione, spende in Distribuzione e poi si blocca
    # alla Decisione: non chiude le buste di canale e non sospende il codice creator (h_decisione non gira).
    # Contrario a D-006 ("scoprire una categoria esaurita prima di spendere").
    def test_categoria_ai_esaurita_scoperta_prima_di_spendere(self):
        reg = os.path.join(self.d, "condiviso.json")
        led = Ledger(reg, POL["tetto_primo_test_cents"], ALLOC, POL["categorie_spesa"])
        led.spend_once("altro-test/ai", "ai", 4700, 4700, "AI di un test precedente")
        sc = carica_scenario("completo")
        r = self._run_sc(sc, registro=reg).avanza()
        aperte = [b["id"] for b in Ledger(reg, POL["tetto_primo_test_cents"]).data["buste"].values()
                  if b["id"].startswith("r/") and b["stato"] == "aperta"]
        # Atteso: o il test completa, o si blocca PRIMA di attivare i canali, senza impegni di canale aperti.
        self.assertTrue(r["stato"] == "completato"
                        or (r["fase_corrente"] in ("strategia", "ricerca", "selezione") and not aperte),
                        f"stato {r['stato']} in fase {r['fase_corrente']}, buste aperte {aperte}")


# =========================================================================== ordini, rimborsi, clawback
class TestQAOrdini(_Tmp):
    def test_duplicato_con_payload_diverso_conserva_il_primo(self):
        ob = OrderBook(os.path.join(self.d, "o.json"))
        self.assertTrue(ob.ingest({"order_id": "X", "lordo_cents": 1900, "iva_bp": 2200, "paese": "IT"}))
        self.assertFalse(ob.ingest({"order_id": "X", "lordo_cents": 99900, "iva_bp": 1900, "paese": "DE"}))
        self.assertEqual(ob.get("X")["lordo_cents"], 1900)
        self.assertEqual(len(ob.ordini()), 1)

    # CORRETTO in D-013, riverificato dal QA — era DIFETTO (minore) studio/orders.py:19-25 — un duplicato con payload DIVERSO (importo, paese, canali) viene
    # scartato in silenzio come un normale webhook ripetuto: nessuna traccia del conflitto da riconciliare.
    def test_duplicato_con_payload_diverso_e_tracciato_come_conflitto(self):
        ob = OrderBook(os.path.join(self.d, "o.json"))
        ob.ingest({"order_id": "X", "lordo_cents": 1900, "iva_bp": 2200})
        ob.ingest({"order_id": "X", "lordo_cents": 99900, "iva_bp": 2200})
        self.assertTrue(ob.data.get("conflitti"), "conflitto di payload non registrato")

    def test_ordine_duplicato_in_distribuzione_non_raddoppia_commissione(self):
        sc = carica_scenario("completo")
        sc["vendite"]["ordini"].append({"order_id": "SIM-1001", "canali": ["ads:ADS-SIM-1"], "paese": "DE",
                                        "giorno": 9})
        run = self._run_sc(sc)
        run.avanza()
        o = run.orders.get("SIM-1001")
        self.assertEqual(o["paese"], "IT")
        self.assertEqual(len(run.orders.ordini()), 14)
        consumi = run.ledger.data["buste"]["r/creator-CR-SIM-1-commissioni"]["consumi"]
        self.assertEqual(len([k for k in consumi if k == "SIM-1001"]), 1)

    def test_rimborso_ordine_inesistente_nel_libro_ordini(self):
        ob = OrderBook(os.path.join(self.d, "o.json"))
        with self.assertRaises(KeyError):
            ob.rimborsa("NON-ESISTE", 1)

    # CORRETTO in D-013, riverificato dal QA — era DIFETTO (importante) studio/phases.py:350-351 — in Distribuzione un rimborso per un ordine inesistente
    # solleva KeyError non gestito: il processo termina con traceback, lo stato resta `in_esecuzione` e ogni
    # `resume` ripete lo stesso crash. Atteso: evento scartato e registrato (o blocco motivato), non un crash.
    def test_rimborso_ordine_inesistente_non_manda_in_crash_il_run(self):
        sc = carica_scenario("completo")
        sc["vendite"]["rimborsi"].append({"order_id": "SIM-9999", "giorno": 7})
        run = self._run_sc(sc)
        try:
            r = run.avanza()
        except KeyError as e:
            self.fail(f"eccezione non gestita: {e!r}")
        self.assertIn(r["stato"], ("completato", "bloccato"))

    # CORRETTO in D-013, riverificato dal QA — era DIFETTO (minore) studio/phases.py:330 — un ordine da un paese assente da IVA_BP (es. BE) solleva KeyError
    # non gestito in Distribuzione (crash invece di blocco motivato). La tabella IVA è sintetica (D-010).
    def test_paese_senza_aliquota_iva_non_manda_in_crash_il_run(self):
        sc = carica_scenario("completo")
        sc["vendite"]["ordini"].append({"order_id": "SIM-2001", "canali": [], "paese": "BE", "giorno": 3})
        try:
            r = self._run_sc(sc).avanza()
        except KeyError as e:
            self.fail(f"eccezione non gestita: {e!r}")
        self.assertIn(r["stato"], ("completato", "bloccato"))

    def test_rimborso_dopo_clawback_commissione_e_fee_restano(self):
        sc = carica_scenario("completo")
        sc["vendite"]["rimborsi"] = [{"order_id": "SIM-1001", "giorno": 1 + 31}]   # ordine al giorno 1
        run = self._run_sc(sc)
        run.avanza()
        c = run.ledger.data["buste"]["r/creator-CR-SIM-1-commissioni"]["consumi"]["SIM-1001"]
        self.assertFalse(c.get("stornato"), "la commissione dopo la finestra di clawback non va stornata")
        met = read_json(os.path.join(self.d, "r", "artifacts", "misurazione.json"))["metriche"]
        self.assertEqual(met["ordini_rimborsati"], 1)
        fee_tot = sum(valori_ordine(o, IP)["fee_pagamento_cents"] for o in run.orders.ordini())
        self.assertEqual(met["fee_pagamento_cents"], fee_tot)   # fee del rimborsato inclusa

    def test_rimborso_al_limite_della_finestra_storna(self):
        sc = carica_scenario("completo")
        sc["vendite"]["rimborsi"] = [{"order_id": "SIM-1001", "giorno": 1 + COMM["finestra_clawback_giorni"]}]
        run = self._run_sc(sc)
        run.avanza()
        c = run.ledger.data["buste"]["r/creator-CR-SIM-1-commissioni"]["consumi"]["SIM-1001"]
        self.assertTrue(c.get("stornato"))

    def test_rimborso_doppio_non_raddoppia_storno(self):
        sc = carica_scenario("completo")
        sc["vendite"]["rimborsi"] = [{"order_id": "SIM-1002", "giorno": 6}, {"order_id": "SIM-1002", "giorno": 8}]
        run = self._run_sc(sc)
        run.avanza()
        self.assertEqual(run.orders.data["eventi_rimborso_duplicati"], 1)
        self.assertEqual(run.orders.get("SIM-1002")["rimborso_giorno"], 6)


# =========================================================================== limiti contrattuali creator
class TestQACreator(_Tmp):
    # CORRETTO in D-013, riverificato dal QA — era DIFETTO (importante) studio/phases.py:265-271 — i limiti contrattuali di config/commissioni.json
    # (compenso_fisso_max_per_creator_cents = 3000, tetto_commissioni_per_test_cents = 6000) non sono letti
    # da nessun modulo (grep in studio/: zero occorrenze). Un piano con compenso fisso di 60 € a un solo creator
    # passa Selezione e viene riservato e pagato: vale solo l'allocazione di categoria.
    def test_compenso_fisso_oltre_il_massimo_per_creator_bloccato(self):
        sc = carica_scenario("completo")
        sc["piano_test"]["canali"][0]["compenso_fisso_cents"] = 6000
        run = self._run_sc(sc)
        run.avanza()
        fisso = run.ledger.consumato("compenso_fisso", "r/")
        self.assertLessEqual(fisso, COMM["compenso_fisso_max_per_creator_cents"])

    def test_tetto_commissioni_sospende_il_codice(self):
        sc = carica_scenario("completo")
        sc["piano_test"]["canali"][0]["tetto_commissioni_cents"] = 1000
        run = self._run_sc(sc)
        r = run.avanza()
        b = run.ledger.data["buste"]["r/creator-CR-SIM-1-commissioni"]
        self.assertLessEqual(run.ledger._drawn(b), 1000)
        dec = [d["decisione"] for d in read_jsonl(os.path.join(self.d, "r", "decisions.jsonl"))]
        self.assertIn("codice_creator_sospeso", dec)
        self.assertEqual(r["stato"], "completato")


# =========================================================================== azioni esterne e modalità live
class TestQALive(_Tmp):
    def test_live_blocca_senza_consumi_anche_con_studio_live(self):
        old = os.environ.get("STUDIO_LIVE")
        os.environ["STUDIO_LIVE"] = "1"
        self.addCleanup(lambda: os.environ.__setitem__("STUDIO_LIVE", old) if old is not None
                        else os.environ.pop("STUDIO_LIVE", None))
        run = nuovo_run(os.path.join(self.d, "r"), "completo", modalita="live")
        r = run.avanza()
        self.assertEqual(r["stato"], "bloccato")
        self.assertEqual(r["fase_corrente"], "strategia")
        self.assertEqual(run.ledger.consumato(), 0)
        self.assertEqual(run.ledger.impegnato_aperto(), 0)
        calls = read_jsonl(run.calls_path)
        self.assertTrue(calls and all(c["esito"] == "bloccato" for c in calls))

    def test_live_ripreso_resta_bloccato_e_non_spende(self):
        run = nuovo_run(os.path.join(self.d, "r"), "completo", modalita="live")
        run.avanza()
        for _ in range(3):
            run = Run(os.path.join(self.d, "r"))
            run.state["stato"] = "in_corso"
            r = run.avanza()
        self.assertEqual(r["stato"], "bloccato")
        self.assertEqual(run.ledger.consumato(), 0)
        self.assertEqual(run.ledger.impegnato_aperto(), 0)

    def test_simulato_nessuna_azione_reale_e_azioni_a_pagamento_con_busta(self):
        run = nuovo_run(os.path.join(self.d, "r"), "completo")
        run.avanza()
        calls = read_jsonl(run.calls_path)
        self.assertTrue(all(c["esito"] == "simulato" for c in calls))
        for c in calls:
            if c["a_pagamento"]:
                self.assertIn(c["busta"], run.ledger.data["buste"])
        self.assertFalse(any(c.get("contatto_reale") for c in calls))
        self.assertEqual(read_json(os.path.join(self.d, "r", "artifacts", "shopify.json"))["stato_scheda"], "bozza")


# =========================================================================== segreti (Q6)
SEGRETO_FINTO = "shpat_" + "0123456789abcdef" * 2   # finto, costruito a runtime


class TestQASegreti(_Tmp):
    def _fino_a_qa(self, scrivi):
        run = nuovo_run(os.path.join(self.d, "r"), "completo")
        for f in ("strategia", "ricerca", "selezione", "prodotto"):
            self.assertTrue(run.esegui_fase(f))
        scrivi(os.path.join(self.d, "r"))
        run.esegui_fase("qa")
        return read_json(os.path.join(self.d, "r", "artifacts", "qa.json"))

    def test_q6_blocca_segreto_nella_cartella_del_run(self):
        def scrivi(d):
            with open(os.path.join(d, "note.txt"), "w") as f:
                f.write(f"token={SEGRETO_FINTO}\n")
        qa = self._fino_a_qa(scrivi)
        self.assertEqual(qa["verdetto"], "BLOCCATO")
        q6 = next(c for c in qa["controlli"] if c["controllo"].startswith("Q6"))
        self.assertFalse(q6["ok"])

    def test_q6_blocca_numero_di_carta_finto(self):
        def scrivi(d):
            with open(os.path.join(d, "note.txt"), "w") as f:
                f.write("carta 4111 1111 1111 1111\n")
        self.assertEqual(self._fino_a_qa(scrivi)["verdetto"], "BLOCCATO")

    # CORRETTO in D-013, riverificato dal QA — era DIFETTO (importante) studio/workflow.py:135-143 (scan_segreti) — Q6 legge solo i file al primo livello
    # della cartella del run (os.listdir + isfile): un segreto in runs/<id>/artifacts/*.json (dove finiscono gli
    # output di ogni fase) non viene visto e il QA APPROVA.
    def test_q6_blocca_segreto_negli_artifacts(self):
        def scrivi(d):
            with open(os.path.join(d, "artifacts", "appunti.json"), "w") as f:
                f.write('{"token": "%s"}' % SEGRETO_FINTO)
        self.assertEqual(self._fino_a_qa(scrivi)["verdetto"], "BLOCCATO")

    # CORRETTO in D-013, riverificato dal QA — era DIFETTO (minore) studio/phases.py:44 (SEGRETI) — il pattern riconosce solo shpat_, sk_live_, carte, otp,
    # password: non riconosce altri formati comuni di token (es. GitHub ghp_, chiavi AWS AKIA…, sk_test_,
    # intestazioni "Authorization: Bearer").
    def test_q6_riconosce_altri_formati_di_token(self):
        def scrivi(d):
            with open(os.path.join(d, "note.txt"), "w") as f:
                f.write("ghp_" + "A1b2C3d4E5" * 4 + "\nAKIA" + "ABCDEFGHIJ234567" + "\n")
        self.assertEqual(self._fino_a_qa(scrivi)["verdetto"], "BLOCCATO")


# =========================================================================== coerenza documenti ↔ codice
class TestQACoerenza(_Tmp):
    def test_esempio_strategia_unit_economics(self):
        # STRATEGIA.md §2: P=24,40 €, IVA 22% ⇒ N=20,00; C_pag=1,01; C_cr=6,00
        n = scorporo_iva(2440, 2200)
        self.assertEqual(n, 2000)
        v = valori_ordine({"lordo_cents": 2440, "iva_bp": 2200}, IP)
        self.assertEqual(v["fee_pagamento_cents"], 101)
        self.assertEqual(pct_bp(n, COMM["commissione_pct_bp_su_netto"]), 600)

    def test_esempio_strategia_regola_ripeti(self):
        # 10 ordini come l'esempio: M = 4,99 €/ordine, ROAS = 18,99/14 = 1,36 ⇒ "ripeti", non "scala"
        m = {"ordini": 10, "acquisizione_cents": 14000, "margine_contribuzione_cents": 4990,
             "roas_su_margine_x100": (18990 * 100) // 14000, "tasso_rimborso_bp": 0}
        self.assertEqual(m["roas_su_margine_x100"], 135)
        self.assertEqual(economics.decidi(m, {"soglia_stop_cents": 99999}, POL)["esito"], "ripeti")

    def test_regole_decisione_strategia_par5(self):
        piano = {"soglia_stop_cents": 12000}
        base = {"ordini": 10, "acquisizione_cents": 1000, "margine_contribuzione_cents": 1,
                "roas_su_margine_x100": 150, "tasso_rimborso_bp": 1000}
        d = lambda **k: economics.decidi(dict(base, **k), piano, POL)["esito"]
        self.assertEqual(d(), "scala")
        self.assertEqual(d(margine_contribuzione_cents=0), "ripeti")
        self.assertEqual(d(roas_su_margine_x100=149), "ripeti")
        self.assertEqual(d(tasso_rimborso_bp=1001), "ripeti")
        self.assertEqual(d(tasso_rimborso_bp=2001), "stop")
        self.assertEqual(d(roas_su_margine_x100=79), "stop")
        self.assertEqual(d(ordini=9, acquisizione_cents=12000), "stop")
        self.assertEqual(d(ordini=9, acquisizione_cents=11999, tasso_rimborso_bp=5000), "ripeti")  # D-007

    def test_roas_e_margine_del_run_seguono_la_formula(self):
        run = nuovo_run(os.path.join(self.d, "r"), "completo")
        run.avanza()
        met = read_json(os.path.join(self.d, "r", "artifacts", "misurazione.json"))["metriche"]
        ordini = run.orders.ordini()
        R = sum(scorporo_iva(o["lordo_cents"] - o["sconto_cents"], o["iva_bp"]) for o in ordini if not o["rimborsato"])
        fee = sum(valori_ordine(o, IP)["fee_pagamento_cents"] for o in ordini)
        c = met["costi_cents"]
        acq = c["ads"] + c["commissione"] + c["compenso_fisso"]
        self.assertEqual(met["ricavi_netti_cents"], R)
        self.assertEqual(met["fee_pagamento_cents"], fee)
        self.assertEqual(met["acquisizione_cents"], acq)
        self.assertEqual(met["roas_su_margine_x100"], (R - fee) * 100 // acq)
        self.assertEqual(met["margine_contribuzione_cents"],
                         R - fee - acq - c["piattaforma"] - c["ai"] - c["riserva"] - met["costi_test_falliti_cents"])
        # commissione = 30% del netto IVA esclusa dopo lo sconto del 10%, sui soli ordini con codice non stornati
        attesa = sum(pct_bp(scorporo_iva(o["lordo_cents"] - o["sconto_cents"], o["iva_bp"]),
                            COMM["commissione_pct_bp_su_netto"])
                     for o in ordini if any(t["canale"] == "creator" for t in o["tocchi"]) and not o["rimborsato"])
        self.assertEqual(c["commissione"], attesa)
        for o in ordini:
            if any(t["canale"] == "creator" for t in o["tocchi"]):
                self.assertEqual(o["sconto_cents"], pct_bp(o["lordo_cents"], COMM["sconto_codice_creator_bp"]))
            self.assertEqual(o["iva_bp"], IVA_BP[o["paese"]])   # aliquota del paese del cliente

    def test_aliquote_iva_sintetiche_coerenti_con_note(self):
        # Valori noti al 2026 per le aliquote ordinarie; la tabella resta "da verificare" (D-010).
        self.assertEqual(IVA_BP, {"IT": 2200, "DE": 1900, "FR": 2000, "ES": 2100, "NL": 2100, "AT": 2000})

    def test_misurazione_non_conta_ordine_di_prova(self):
        run = nuovo_run(os.path.join(self.d, "r"), "completo")
        run.avanza()
        self.assertEqual(len(run.orders.ordini(includi_test=True)), 15)
        met = read_json(os.path.join(self.d, "r", "artifacts", "misurazione.json"))["metriche"]
        self.assertEqual(met["ordini"], 14)

    # CORRETTO in D-013, riverificato dal QA — era DIFETTO (minore) studio/orders.py:59 + config/policy.json — `commissione_pagamento_rimborsata_su_refund`
    # non è letto da nessun modulo: la fee è sempre trattenuta (corretto con il valore attuale `false`, ma un
    # cambio di policy non avrebbe effetto e nessun test lo segnalerebbe).
    def test_flag_fee_rimborsata_letto_dal_codice(self):
        ip = dict(IP, commissione_pagamento_rimborsata_su_refund=True)
        d = self.d
        ob = OrderBook(os.path.join(d, "o.json"))
        ob.ingest({"order_id": "A", "lordo_cents": 1900, "iva_bp": 2200})
        ob.rimborsa("A", 2)
        led = _ledger(d)
        m = economics.misura(ob, led, dict(POL, ipotesi_costi_variabili=ip))
        self.assertEqual(m["fee_pagamento_cents"], 0)

    # CORRETTO in D-013, riverificato dal QA — era DIFETTO (minore) studio/economics.py:98, 105 — con acquisizione zero il ROAS indefinito è sostituito da 10**9
    # e finisce nei motivi della decisione come "ROAS sul margine 10000000.00": un numero falso in un documento
    # di decisione (D-008 dice "indefinito"). Con margine negativo e ≥10 ordini l'esito è "ripeti".
    def test_roas_indefinito_non_compare_come_numero_nei_motivi(self):
        m = {"ordini": 10, "acquisizione_cents": 0, "margine_contribuzione_cents": -500,
             "roas_su_margine_x100": None, "tasso_rimborso_bp": 0}
        d = economics.decidi(m, {"soglia_stop_cents": 1}, POL)
        self.assertFalse(any("10000000" in x for x in d["motivi"]), d["motivi"])


# =========================================================================== file versionati
class TestQAFileVersionati(unittest.TestCase):
    PATTERN = re.compile(
        r"(shpat_|shpss_|shpca_|sk_live_|sk_test_|rk_live_|ghp_[A-Za-z0-9]{20}|github_pat_|AKIA[0-9A-Z]{16}|"
        r"xox[bp]-|-----BEGIN [A-Z ]*PRIVATE KEY|\b(?:\d[ -]?){15,16}\b|"
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z.]{2,}|\bIT\d{2}[A-Z]\d{10}[0-9A-Z]{12}\b|\+39 ?\d{6,})")

    def _files(self):
        if not os.path.isdir(os.path.join(ROOT, ".git")) or shutil.which("git") is None:
            self.skipTest("repository git non disponibile")
        out = subprocess.run(["git", "-C", ROOT, "ls-files"], capture_output=True, text=True, check=True).stdout
        return [l for l in out.splitlines() if l]

    def test_nessuna_credenziale_o_dato_personale_versionato(self):
        trovati = []
        for rel in self._files():
            if rel.startswith("tests/test_qa_"):
                continue  # questo file contiene i pattern di ricerca, non segreti
            p = os.path.join(ROOT, rel)
            if not os.path.isfile(p):
                continue
            with open(p, encoding="utf-8", errors="ignore") as f:
                nel_pattern = False
                for i, riga in enumerate(f, 1):
                    # La definizione del pattern di scansione (studio/phases.py, SEGRETI = re.compile(...), anche
                    # su più righe) contiene per forza i prefissi cercati: si salta l'intero blocco, senza
                    # dipendere da offuscamenti come "github_p[a]t_".
                    if rel == "studio/phases.py" and riga.startswith("SEGRETI = re.compile"):
                        nel_pattern = True
                    if nel_pattern:
                        if "re.IGNORECASE)" in riga:
                            nel_pattern = False
                        continue
                    if self.PATTERN.search(riga):
                        trovati.append(f"{rel}:{i}")
        self.assertEqual(trovati, [])

    def test_runs_e_segreti_non_versionati(self):
        files = self._files()
        self.assertEqual([f for f in files if f.startswith("runs/")], ["runs/.gitkeep"])
        self.assertFalse([f for f in files if f.startswith(("secrets/", ".env")) or f.endswith("settings.local.json")])



# =========================================================================== riverifica dopo D-013: concorrenza
TETTO = POL["tetto_primo_test_cents"]


def _drawn_raw(b):
    return sum(d["importo_cents"] for d in b["consumi"].values() if not d.get("stornato"))


def _attivo_raw(led: dict, categoria=None) -> int:
    return sum(_drawn_raw(b) + (max(b["max_cents"] - _drawn_raw(b), 0) if b["stato"] == "aperta" else 0)
               for b in led["buste"].values() if categoria is None or b["categoria"] == categoria)


class TestQAConcorrenza(_Tmp):
    """Processi reali in parallelo sullo stesso --registro (richiesta del Team Lead dopo D-013)."""

    N_PROCESSI = 3
    GIRI = 2

    def _giro(self, base):
        os.makedirs(base)
        reg = os.path.join(base, "registro.json")
        env = dict(os.environ, PYTHONPATH=ROOT, STUDIO_LIVE="0")
        procs = [subprocess.Popen([sys.executable, "-m", "studio", "simulate", "--scenario", "completo",
                                   "--run-id", f"p{i}", "--runs-dir", base, "--registro", reg],
                                  cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                 for i in range(self.N_PROCESSI)]
        esiti = [(p.wait(timeout=120), p.stderr.read()) for p in procs]
        for p in procs:
            p.stdout.close()
            p.stderr.close()
        return reg, esiti

    def test_processi_paralleli_stesso_registro_entro_tetto_e_allocazioni(self):
        for g in range(self.GIRI):
            base = os.path.join(self.d, f"giro{g}")
            reg, esiti = self._giro(base)
            for rc, err in esiti:
                self.assertEqual(rc, 0, err[-2000:])
            led = read_json(reg)
            # 1. tetto: consumato + impegnato ≤ 500 €
            self.assertLessEqual(_attivo_raw(led), TETTO)
            # 2. nessuna categoria oltre l'allocazione
            for cat, lim in ALLOC.items():
                self.assertLessEqual(_attivo_raw(led, cat), lim, cat)
            # 3. nessun aggiornamento perso: ogni busta citata da un'azione esterna esiste nel registro
            for i in range(self.N_PROCESSI):
                for c in read_jsonl(os.path.join(base, f"p{i}", "external_calls.jsonl")):
                    if c.get("busta"):
                        self.assertIn(c["busta"], led["buste"], f"busta persa (giro {g}, p{i})")
            # 4. il registro conserva le buste AI di tutte le fasi eseguite da ogni run
            for i in range(self.N_PROCESSI):
                st = read_json(os.path.join(base, f"p{i}", "state.json"))
                for fase, n in st["tentativi"].items():
                    for t in range(1, n + 1):
                        self.assertIn(f"p{i}/ai-{fase}-{t}", led["buste"])
            # 5. al più un test ottiene la busta commissioni (allocazione 60 € = tetto di un solo creator)
            comm = [b for b in led["buste"].values() if b["categoria"] == "commissione" and b["max_cents"] > 0
                    and _drawn_raw(b) > 0]
            self.assertLessEqual(len(comm), 1)
            # 6. almeno un test completato, nessun run lasciato in esecuzione
            stati = [read_json(os.path.join(base, f"p{i}", "state.json")) for i in range(self.N_PROCESSI)]
            self.assertIn("completato", [s["stato"] for s in stati])
            self.assertFalse([s for s in stati if s["in_esecuzione"]])

    def _fino_a(self, run, fase):
        while run.state["fase_corrente"] != fase:
            self.assertTrue(run.esegui_fase(run.state["fase_corrente"]))

    # Era DIFETTO NUOVO N-1 (riverifica), CORRETTO in D-014: la Selezione ora PRENOTA il budget del piano.
    # Scaffolding adattato: B non deve più superare la Selezione; si verifica che si fermi LÌ, prima di spendere.
    def test_due_test_interfogliati_il_non_finanziabile_si_ferma_alla_selezione(self):
        reg = os.path.join(self.d, "condiviso.json")
        sc = carica_scenario("completo")
        a = self._run_sc(sc, "A", registro=reg)
        b = self._run_sc(sc, "B", registro=reg)
        self._fino_a(a, "prodotto")          # A ha superato la Selezione (budget prenotato) ma non ha speso
        self._fino_a(b, "selezione")
        self.assertFalse(b.esegui_fase("selezione"))
        a.avanza()
        rb = b.riepilogo()
        self.assertEqual(a.state["stato"], "completato")
        self.assertEqual((rb["stato"], rb["fase_corrente"]), ("bloccato", "selezione"))
        led = read_json(reg)
        di_b = [x for x in led["buste"].values() if x["id"].startswith("B/")]
        self.assertEqual({x["categoria"] for x in di_b}, {"ai"})           # nessuna piattaforma né acquisizione
        self.assertFalse([x["id"] for x in di_b if x["stato"] == "aperta"])  # prenotazione fallita: tutto o niente
        self.assertLessEqual(_attivo_raw(led), TETTO)

    # Era DIFETTO NUOVO N-2, CORRETTO in D-014. Scaffolding adattato (la categoria commissione è ora tutta
    # prenotata da B): l'altro processo riserva su una categoria con capacità libera (ads) e il fallimento
    # dell'attivazione di B è iniettato con SpendBlocked, così si prova proprio il filtro del rollback.
    def test_rollback_atomico_non_chiude_buste_di_altri_run(self):
        from unittest import mock
        reg = os.path.join(self.d, "condiviso.json")
        b = self._run_sc(carica_scenario("completo"), "B", registro=reg)
        self._fino_a(b, "distribuzione")
        originale = b.ledger.reserve

        def reserve_con_altro_processo(busta_id, *a, **k):
            if busta_id.endswith("creator-CR-SIM-1-commissioni"):
                altro = Ledger(reg, TETTO, ALLOC, POL["categorie_spesa"])
                altro.reserve("ALTRO/ads-X", "ads", 5000, "altro test", tag=["canale:ads"])
                raise SpendBlocked("blocco iniettato dal QA", {"categoria": "commissione"})
            return originale(busta_id, *a, **k)

        with mock.patch.object(b.ledger, "reserve", side_effect=reserve_con_altro_processo):
            b.esegui_fase("distribuzione")
        self.assertEqual(b.state["stato"], "bloccato")
        led = read_json(reg)
        self.assertEqual(led["buste"]["ALTRO/ads-X"]["stato"], "aperta", "B ha chiuso la busta di un altro run")
        self.assertEqual(led["buste"]["B/creator-CR-SIM-1-fisso"]["stato"], "chiusa")  # il proprio rollback avviene

    # Era DIFETTO NUOVO N-3, CORRETTO in D-014. Il test con mock di os.path.exists era rientrante sotto il lock
    # (deadlock per costruzione con un lock corretto): sostituito con processi reali indipendenti (subprocess,
    # non fork) che creano e usano insieme un registro NUOVO.
    def test_creazione_concorrente_del_registro_non_perde_riserve(self):
        path = os.path.join(self.d, "nuovo.json")
        codice = ("import sys; from studio.ledger import Ledger, SpendBlocked; from studio.workflow import carica_json;"
                  "P=carica_json('config/policy.json'); i=sys.argv[1];"
                  "l=Ledger(sys.argv[2], P['tetto_primo_test_cents'], P['allocazione_budget_cents'], P['categorie_spesa']);"
                  "\ntry:\n l.reserve(f'p{i}/ads','ads',3000,'x'); print('ok')\nexcept SpendBlocked: print('no')")
        env = dict(os.environ, PYTHONPATH=ROOT)
        procs = [subprocess.Popen([sys.executable, "-c", codice, str(i), path], cwd=ROOT, env=env,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for i in range(12)]
        out = [p.communicate(timeout=60) for p in procs]
        for p, (o, e) in zip(procs, out):
            self.assertEqual(p.returncode, 0, e)
        ok = [i for i, (o, _) in enumerate(out) if o.strip() == "ok"]
        buste = read_json(path)["buste"]
        self.assertEqual(len(ok), ALLOC["ads"] // 3000)
        self.assertEqual(sorted(buste), sorted(f"p{i}/ads" for i in ok))   # nessuna riserva riuscita è andata persa

    # Era DIFETTO NUOVO N-4, CORRETTO in D-014 (ripetizioni_fase_previste; buste di canale chiuse a fine
    # Distribuzione). Asserzione invariata.
    def test_previsione_ai_regge_ritorno_qa_e_ripresa_dopo_blocco(self):
        reg = os.path.join(self.d, "condiviso.json")
        led = Ledger(reg, TETTO, ALLOC, POL["categorie_spesa"])
        led.spend_once("altro-test/ai", "ai", 2400, 2400, "AI di un test precedente")
        sc = carica_scenario("completo")
        sc["costi_ai_per_fase_cents"] = {"max": 300, "effettivo": 300}
        sc["guasti"] = {"qa_respinge_tentativi": 1, "shopify_accesso": False}
        run = self._run_sc(sc, registro=reg)
        r = run.avanza()
        if r["stato"] == "bloccato_titolare":
            run = Run(os.path.join(self.d, "r"))
            run.concedi("shopify")
            r = run.avanza()
        aperte = [b["id"] for b in read_json(reg)["buste"].values() if b["id"].startswith("r/") and b["stato"] == "aperta"]
        self.assertTrue(r["stato"] == "completato"
                        or (r["fase_corrente"] in ("strategia", "ricerca", "selezione") and not aperte),
                        f"stato {r['stato']} in fase {r['fase_corrente']}, buste aperte {aperte}")



    # CORRETTO in D-015, riverificato dal QA — era DIFETTO F-1 (bloccante) studio/workflow.py:100-102 (Run.bid) + studio/ledger.py:110-115, 181-185 — gli ID
    # delle buste dipendono solo dal run_id. Un secondo run con lo STESSO run_id sullo stesso --registro (cartella
    # del run cancellata e rilanciata, o un altro --runs-dir) riusa le buste del primo: reserve() ritorna la busta
    # esistente (anche chiusa), draw() trova gli stessi draw_id ("unico", "giorno-N", order_id) e ritorna False.
    # Il secondo test esegue tutte le azioni a pagamento (AI, piattaforma, campagna Ads, compenso creator) con
    # spesa registrata ZERO: il tetto si aggira ripetendo il run. Contrario a D-005 e alla regola 1 di CLAUDE.md.
    def test_run_omonimo_sullo_stesso_registro_registra_la_spesa_o_viene_rifiutato(self):
        reg = os.path.join(self.d, "condiviso.json")
        sc = carica_scenario("completo")
        sc["piano_test"]["canale_primario"] = "ads"
        sc["piano_test"]["canali"] = [c for c in sc["piano_test"]["canali"] if c["canale"] != "creator"]
        rid = os.path.join(self.d, "runs", "prova")
        r1 = Run(rid, sc, "simulato", reg).avanza()
        speso_1 = read_json(reg)
        speso_1 = _attivo_raw(speso_1)
        self.assertEqual(r1["stato"], "completato")
        shutil.rmtree(rid)                                  # stesso run_id, cartella ricreata
        try:
            r2 = Run(rid, sc, "simulato", reg).avanza()
        except (FileExistsError, ValueError, RuntimeError):
            return                                          # rifiuto esplicito: comportamento accettabile
        pagate = [c for c in read_jsonl(os.path.join(rid, "external_calls.jsonl")) if c["a_pagamento"]]
        speso_2 = _attivo_raw(read_json(reg))
        self.assertFalse(r2["stato"] == "completato" and speso_2 == speso_1,
                         f"secondo run {r2['stato']} con {len(pagate)} azioni a pagamento e spesa registrata "
                         f"invariata ({speso_1} cent)")
        self.assertGreater(speso_2, speso_1, f"{len(pagate)} azioni a pagamento senza spesa registrata")


    def test_run_omonimo_creato_in_parallelo_su_runs_dir_diverse(self):
        """F-1 con processi reali: due `simulate` con lo stesso --run-id, --runs-dir diverse, stesso --registro."""
        env = dict(os.environ, PYTHONPATH=ROOT, STUDIO_LIVE="0")
        for g in range(3):
            base = os.path.join(self.d, f"giro{g}")
            reg = os.path.join(base, "registro.json")
            dirs = [os.path.join(base, f"runs{i}") for i in range(2)]
            procs = [subprocess.Popen([sys.executable, "-m", "studio", "simulate", "--scenario", "completo",
                                       "--run-id", "omonimo", "--runs-dir", d, "--registro", reg],
                                      cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                     for d in dirs]
            out = [p.communicate(timeout=120) for p in procs]
            rc = [p.returncode for p in procs]
            self.assertEqual(sorted(rc != 0 for rc in rc), [False, True], f"giro {g}: rc={rc}")
            vinc, perd = (0, 1) if rc[0] == 0 else (1, 0)
            self.assertIn("FileExistsError", out[perd][1])
            # il perdente non ha stato, né azioni esterne, né buste proprie
            self.assertFalse(os.path.exists(os.path.join(dirs[perd], "omonimo", "state.json")))
            self.assertFalse(os.path.exists(os.path.join(dirs[perd], "omonimo", "external_calls.jsonl")))
            led = read_json(reg)
            self.assertEqual(led["run_registrati"], ["omonimo"])
            self.assertEqual(read_json(os.path.join(dirs[vinc], "omonimo", "state.json"))["stato"], "completato")
            # ogni azione a pagamento del vincitore ha la sua busta nel registro e la spesa registrata è > 0
            pagate = [c for c in read_jsonl(os.path.join(dirs[vinc], "omonimo", "external_calls.jsonl")) if c["a_pagamento"]]
            self.assertTrue(pagate and all(c["busta"] in led["buste"] for c in pagate))
            self.assertGreater(_attivo_raw(led), 0)
            self.assertLessEqual(_attivo_raw(led), TETTO)

    def test_ripresa_dello_stesso_run_non_e_rifiutata(self):
        reg = os.path.join(self.d, "condiviso.json")
        run = nuovo_run(os.path.join(self.d, "r"), "interruzione", registro=reg)
        from studio.phases import SimulatedCrash
        with self.assertRaises(SimulatedCrash):
            run.avanza()
        r = Run(os.path.join(self.d, "r")).avanza()        # ripresa: nessun FileExistsError
        self.assertEqual(r["stato"], "completato")
        self.assertEqual(read_json(reg)["run_registrati"], ["r"])


if __name__ == "__main__":
    unittest.main()
