"""QA indipendente T-027: verifica avversariale della regia mobile.

Controlli che passano = requisiti rispettati. `@unittest.expectedFailure` = difetto reale osservato
(vedi qa/2026-11-23-regia-mobile.md): quando il responsabile corregge, il test diventa "unexpected success"
e il decoratore va tolto.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from studio import regia
from studio.ledger import Ledger, SpendBlocked
from studio.queue import TaskQueue
from studio.workflow import ROOT, Run, carica_json, nuovo_run

POL = carica_json("config/policy.json")
HOOK = os.path.join(ROOT, "studio", "hooks", "registra_evento.py")
HTML = open(os.path.join(ROOT, "app", "regia.html"), encoding="utf-8").read()
JS = HTML[HTML.index("<script>"):HTML.rindex("</script>")]


def _ev(evento, minuti_fa, **kw):
    q = (datetime.now(timezone.utc) - timedelta(minutes=minuti_fa)).isoformat(timespec="seconds")
    return {"quando": q, "evento": evento, **kw}


class _Team(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)
        self.team = os.path.join(self.d, "team")
        os.makedirs(self.team)
        shutil.copy(os.path.join(ROOT, "team", "queue.json"), os.path.join(self.team, "queue.json"))
        self.sosp = os.path.join(self.team, "sospensione.json")
        env = mock.patch.dict(os.environ, {"STUDIO_TEAM_DIR": self.team, "STUDIO_SOSPENSIONE": self.sosp})
        env.start()
        self.addCleanup(env.stop)

    def coda(self):
        return TaskQueue(os.path.join(self.team, "queue.json"))

    def sospendi(self, spese=True, attivita=True):
        with open(self.sosp, "w") as f:
            json.dump({"spese": spese, "attivita": attivita}, f)


# ----------------------------------------------------------------------------- 1. onestà degli stati
class TestQAStati(_Team):
    def stati(self, evs, fresco=True):
        return {a["id"]: a for a in regia.stato_agenti(evs, fresco)}

    def test_file_agente_non_e_processo_attivo(self):
        for a in self.stati([]).values():
            if a["id"] != "team-lead":
                self.assertNotEqual(a["stato"], "in_esecuzione", a["id"])

    def test_senza_fine_e_senza_eventi_recenti_sconosciuto(self):
        evs = [_ev("SubagentStart", 25, agente_id="q1", agente_tipo="customer-care")]
        self.assertEqual(self.stati(evs)["customer-care"]["stato"], "sconosciuto")

    def test_ponte_scaduto_sconosciuto(self):
        evs = [_ev("SubagentStart", 1, agente_id="q1", agente_tipo="customer-care"),
               _ev("PreToolUse", 0, agente_id="q1", agente_tipo="customer-care", strumento="Read", sintesi="Read")]
        a = self.stati(evs, fresco=False)["customer-care"]
        self.assertEqual(a["stato"], "sconosciuto")
        self.assertIsNone(a["attivita_corrente"])

    def test_passaggi_solo_da_dipendenze_registrate_e_concluse(self):
        coda = [{"id": "A", "agente": "ricerca-mercato", "stato": "in_corso", "aggiornato": "t", "dipende_da": []},
                {"id": "B", "agente": "qa-indipendente", "stato": "da_fare", "dipende_da": ["A", "NON-ESISTE"]}]
        self.assertEqual(regia.passaggi(coda), [])

    def test_simulazioni_escluse_dai_numeri(self):
        # un run simulato completo non tocca il registro comune letto dalla regia
        prima = regia.numeri()
        r = nuovo_run(os.path.join(self.d, "run"), "completo")
        r.avanza()
        self.assertGreater(r.ledger.consumato(), 0)
        self.assertEqual(regia.numeri(), prima)

    # ex DIFETTO R-6: due esecuzioni parallele dello stesso tipo — corretto, riverificato 2026-11-23
    def test_esecuzione_aperta_non_nascosta_da_una_parallela_conclusa(self):
        evs = [_ev("SubagentStart", 5, agente_id="p1", agente_tipo="customer-care"),
               _ev("SubagentStart", 3, agente_id="p2", agente_tipo="customer-care"),
               _ev("SubagentStop", 2, agente_id="p2", agente_tipo="customer-care"),
               _ev("PreToolUse", 0, agente_id="p1", agente_tipo="customer-care", strumento="Read", sintesi="Read")]
        self.assertEqual(self.stati(evs)["customer-care"]["stato"], "in_esecuzione")

    # ex DIFETTO R-7: team-lead con ponte scaduto e attività recente — corretto, riverificato 2026-11-23
    def test_team_lead_ponte_scaduto_non_afferma_inattivita(self):
        evs = [_ev("PreToolUse", 1, strumento="Bash", sintesi="x")]
        a = self.stati(evs, fresco=False)["team-lead"]
        self.assertEqual(a["stato"], "sconosciuto")

    # ex DIFETTO R-8: una riga troncata nel registro eventi fa cadere l'istantanea — corretto, riverificato 2026-11-23
    def test_riga_eventi_troncata_non_blocca_istantanea(self):
        os.makedirs(os.path.join(self.team, "eventi"))
        with open(os.path.join(self.team, "eventi", "2026-11-23.jsonl"), "w") as f:
            f.write(json.dumps(_ev("SubagentStart", 1, agente_id="z", agente_tipo="qa-indipendente")) + "\n")
            f.write('{"quando": "2026-11-23T10:00:00+00:00", "evento": "PreTo')  # hook interrotto dal timeout
        regia.istantanea()


# ----------------------------------------------------------------------------- 2. hook
class TestQAHook(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)

    def hook(self, raw):
        if not isinstance(raw, bytes):
            raw = json.dumps(raw).encode()
        cart = os.path.join(self.d, "team", "eventi")
        if os.path.isdir(cart):
            shutil.rmtree(cart)
        r = subprocess.run([sys.executable, HOOK], input=raw, capture_output=True, timeout=20,
                           env={**os.environ, "CLAUDE_PROJECT_DIR": self.d})
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, b"")
        testo = ""
        if os.path.isdir(cart):
            for f in os.listdir(cart):
                testo += open(os.path.join(cart, f), encoding="utf-8").read()
        return testo

    @staticmethod
    def pre(tool, inp, ev="PreToolUse"):
        return {"hook_event_name": ev, "session_id": "s", "tool_name": tool, "tool_input": inp}

    def test_input_malevoli_uscita_sempre_zero(self):
        for raw in [b"", b"{non json", b"\xff\xfe\x00", b"[1,2]", b"null", b"[" * 200000 + b"]" * 200000,
                    json.dumps({"hook_event_name": "Stop", "session_id": 123}).encode(),
                    json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": "stringa"}).encode()]:
            self.hook(raw)  # asserisce codice 0 e nessun output

    def test_comando_bash_e_contenuto_file_mai_registrati(self):
        t = self.hook(self.pre("Bash", {"command": "curl -u mario:Segreto99 https://x.io/?t=AAA", "description": "scarica"}))
        t += self.hook(self.pre("Write", {"file_path": os.path.join(self.d, "a.md"), "content": "CONTENUTO-RISERVATO"}))
        t += self.hook(self.pre("Edit", {"file_path": "/etc/shadow", "old_string": "x", "new_string": "CONTENUTO-RISERVATO"}))
        for vietato in ("Segreto99", "x.io", "CONTENUTO-RISERVATO", "/etc/shadow"):
            self.assertNotIn(vietato, t)

    def test_token_email_carte_oscurati(self):
        t = self.hook(self.pre("Bash", {"description": "token shpat_0123456789abcdef0123 per mario.rossi@example.com "
                                                       "carta 4111 1111 1111 1111 password: Hunter2"}))
        for vietato in ("shpat_0123", "mario.rossi@example.com", "4111 1111", "Hunter2"):
            self.assertNotIn(vietato, t)

    def test_webfetch_solo_host(self):
        t = self.hook(self.pre("WebFetch", {"url": "https://u:pw@shop.example.com/admin?token=SEGRETO123"}))
        self.assertIn("shop.example.com", t)
        for vietato in ("SEGRETO123", "/admin", "u:pw"):
            self.assertNotIn(vietato, t)

    # ex DIFETTO H-1: URL completi non oscurati fuori da WebFetch — corretto, riverificato 2026-11-23
    def test_url_completi_oscurati_ovunque(self):
        url = "https://api.example.com/v1/orders?access_token=SEGRETO123"
        t = self.hook(self.pre("Bash", {"command": "x", "description": "scarica " + url}))
        t += self.hook(self.pre("WebSearch", {"query": url}))
        t += self.hook({"hook_event_name": "SubagentStop", "agent_id": "a", "agent_type": "qa",
                        "last_assistant_message": "fatto, vedi " + url})
        self.assertNotIn("SEGRETO123", t)

    # ex DIFETTO H-2: password senza ':'/'=' e chiavi API generiche non oscurate — corretto, riverificato 2026-11-23
    def test_password_e_chiavi_in_altre_forme(self):
        t = self.hook(self.pre("Bash", {"description": "login --password Hunter2Segreto"}))
        t += self.hook(self.pre("Bash", {"description": "la password è Hunter2Segreto"}))
        t += self.hook(self.pre("Bash", {"description": "api_key=sk-ant-api03-AAAABBBBCCCCDDDD"}))
        self.assertNotIn("Hunter2Segreto", t)
        self.assertNotIn("sk-ant-api03", t)

    # ex DIFETTO H-3: tool_name / agent_type / file registrati grezzi — corretto, riverificato 2026-11-23
    def test_campi_grezzi_filtrati(self):
        t = self.hook(self.pre("ghp_abcdefghijklmnopqrstuvwxyz0123456789", {}))
        t += self.hook({"hook_event_name": "SubagentStart", "agent_id": "a", "agent_type": "x" * 5000})
        t += self.hook(self.pre("Read", {"file_path": os.path.join(self.d, "accessi", "mario.rossi@example.com.age")}))
        self.assertNotIn("ghp_abcdefghij", t)
        self.assertNotIn("x" * 400, t)
        self.assertNotIn("mario.rossi@example.com", t)


    # ex RESIDUO H-4 — corretto, riverificato 2026-11-23
    def test_residui_oscuramento(self):
        t = ""
        for desc in ["Authorization: Basic dXNlcjpwYXNzd29yZA==", "Bearer abc123def456",
                     "jwt eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.abcdef",
                     "vedi www.example.com/reset?code=SEGRETO99",
                     "webhook https://hooks." + "slack.com/services/T0AAAAAAA/B0BBBBBBB/" + "X" * 24,
                     "pass: Hunter2Segreto"]:
            t += self.hook(self.pre("Bash", {"command": "x", "description": desc}))
        for vietato in ("dXNlcjpwYXNz", "abc123def456", "eyJzdWIi", "SEGRETO99", "XXXXXXXXXXXXXXXX", "Hunter2Segreto"):
            self.assertNotIn(vietato, t)

    def test_nuovo_filtro_url_e_credenziali(self):
        t = self.hook(self.pre("Bash", {"description": "db postgres://admin:S3gret0@db.example.com:5432/prod?ssl=TOKQ"}))
        t += self.hook(self.pre("Bash", {"description": "il token è abcd1234 e PASSWORD=Hunter2Segreto, chiave sk-proj-abcdEFGH1234"}))
        for vietato in ("S3gret0", "TOKQ", "abcd1234", "Hunter2Segreto", "sk-proj"):
            self.assertNotIn(vietato, t)
        self.assertIn("db.example.com", t)


# ----------------------------------------------------------------------------- 3. comandi
class TestQAComandi(_Team):
    def test_stesso_id_un_solo_effetto_per_ogni_tipo(self):
        c = {"id": "qa-dup-revisione-01", "tipo": "revisione", "parametri": {"oggetto": "x"}}
        n = len(self.coda().data["compiti"])
        r1, r2 = regia.esegui_comando(c), regia.esegui_comando(c)
        self.assertEqual(r1["stato"], "completato")
        self.assertTrue(r2["duplicato"])
        self.assertEqual(len(self.coda().data["compiti"]), n + 1)
        c = {"id": "qa-dup-risposta-01", "tipo": "risposta", "parametri": {"richiesta": "R1", "testo": "ok"}}
        if "R1" in {r["id"] for r in regia.richieste_titolare()}:
            regia.esegui_comando(c), regia.esegui_comando(c)
            righe = open(os.path.join(self.team, "risposte_titolare.jsonl")).read().splitlines()
            self.assertEqual(len(righe), 1)

    def test_malevoli_falliscono_senza_effetti(self):
        prima = open(os.path.join(self.team, "queue.json")).read()
        for c in [{"id": "../../etc/passwd", "tipo": "obiettivo", "parametri": {"testo": "x"}},
                  {"id": ["qa-lista-0001"], "tipo": "obiettivo"}, {"id": "a" * 81, "tipo": "obiettivo"},
                  {"id": "qa-mal-00001", "tipo": "__class__"},
                  {"id": "qa-mal-00002", "tipo": "obiettivo", "parametri": "stringa"},
                  {"id": "qa-mal-00003", "tipo": "obiettivo", "parametri": {"testo": "   "}},
                  {"id": "qa-mal-00004", "tipo": "priorita", "parametri": {"compito": {"$ne": 1}, "priorita": "alta"}},
                  {"id": "qa-mal-00005", "tipo": "priorita", "parametri": {"compito": "T-001", "priorita": "massima"}},
                  {"id": "qa-mal-00006", "tipo": "risposta", "parametri": {"richiesta": "R1'; rm -rf /", "testo": "x"}},
                  {"id": "qa-mal-00007", "tipo": "riprendi", "parametri": {"compito": "NON-ESISTE"}}]:
            self.assertEqual(regia.esegui_comando(c)["stato"], "fallito", c)
        self.assertEqual(open(os.path.join(self.team, "queue.json")).read(), prima)
        self.assertFalse(os.path.exists(self.sosp))
        self.assertFalse(os.path.exists(os.path.join(self.team, "risposte_titolare.jsonl")))

    def test_riprendi_rifiutato_con_dipendenze_aperte(self):
        q = self.coda()
        q.add("QA-DIP-A", "a", "ricerca-mercato")
        q.add("QA-DIP-B", "b", "qa-indipendente", dipende_da=["QA-DIP-A"])
        q.set_stato("QA-DIP-B", "bloccato", "attesa")
        r = regia.esegui_comando({"id": "qa-rip-dip-01", "tipo": "riprendi", "parametri": {"compito": "QA-DIP-B"}})
        self.assertEqual(r["stato"], "fallito")
        self.assertEqual(self.coda().get("QA-DIP-B")["stato"], "bloccato")

    def test_riprendi_rifiutato_con_attivita_sospese(self):
        q = self.coda()
        q.add("QA-SOS-A", "a", "ricerca-mercato")
        q.set_stato("QA-SOS-A", "bloccato", "x")
        self.sospendi(spese=False, attivita=True)
        r = regia.esegui_comando({"id": "qa-rip-sos-01", "tipo": "riprendi", "parametri": {"compito": "QA-SOS-A"}})
        self.assertEqual(r["stato"], "fallito")
        self.assertEqual(self.coda().get("QA-SOS-A")["stato"], "bloccato")

    # ex DIFETTO C-1: id del compito = 10 caratteri dell'id → collisione con gli id dell'app — corretto, riverificato 2026-11-23
    def test_obiettivi_distinti_entrambi_registrati(self):
        # formato di nuovoId() in app/regia.html: "cmd-" + Date.now() in base 36 (8 car.) + "-" + 10 hex
        r1 = regia.esegui_comando({"id": "cmd-mhx1abcd-1111111111", "tipo": "obiettivo", "parametri": {"testo": "PRIMO"}})
        r2 = regia.esegui_comando({"id": "cmd-mhx1abef-2222222222", "tipo": "obiettivo", "parametri": {"testo": "SECONDO"}})
        self.assertEqual((r1["stato"], r2["stato"]), ("completato", "completato"))
        titoli = " ".join(t["titolo"] for t in self.coda().data["compiti"])
        self.assertIn("SECONDO", titoli)  # fallisce: "completato" ma l'obiettivo non esiste nella coda

    # ex DIFETTO C-2: "riprendi" riapre un compito già fatto — corretto, riverificato 2026-11-23
    def test_riprendi_non_riapre_compiti_fatti(self):
        fatto = next(t["id"] for t in self.coda().data["compiti"] if t["stato"] == "fatto")
        r = regia.esegui_comando({"id": "qa-riapri-0001", "tipo": "riprendi", "parametri": {"compito": fatto}})
        self.assertEqual(r["stato"], "fallito")
        self.assertEqual(self.coda().get(fatto)["stato"], "fatto")


    def test_sospendi_non_confermato_ripristina_il_file(self):
        with mock.patch.dict(os.environ, {"STUDIO_SOSPENSIONE": ""}):
            with open(self.sosp, "w") as f:
                json.dump({"spese": False, "attivita": False, "marca": 1}, f)
            with mock.patch("studio.ledger.Ledger.sospensione_attiva", return_value=None):
                r = regia.esegui_comando({"id": "qa-c3-0001", "tipo": "sospendi", "parametri": {}})
            self.assertEqual(r["stato"], "fallito")
            self.assertEqual(json.load(open(self.sosp))["marca"], 1)


# ----------------------------------------------------------------------------- 4. sospensione nel motore
class TestQASospensione(_Team):
    def led(self):
        return Ledger(os.path.join(self.d, "l.json"), 50000, POL["allocazione_budget_cents"], POL["categorie_spesa"])

    def test_nuove_riserve_e_trasferimenti_bloccati_impegni_restano(self):
        led = self.led()
        led.prenota("r/", {"ads": 5000})
        led.reserve("r/gia-assunta", "ai", 300, "impegno precedente")
        self.sospendi(spese=True, attivita=False)
        with self.assertRaises(SpendBlocked):
            led.reserve("r/nuova", "ai", 100, "nuova")
        with self.assertRaises(SpendBlocked):
            led.reserve("r/ads-campagna", "ads", 1000, "trasferimento da prenotazione")
        self.assertEqual(led.data["buste"]["r/prenotazione-ads"]["max_cents"], 5000)
        self.assertTrue(led.draw("r/gia-assunta", "d1", 200))  # impegno già assunto: resta
        self.assertEqual(led.reserve("r/gia-assunta", "ai", 300, "ripresa idempotente")["id"], "r/gia-assunta")

    def test_nessuna_nuova_fase_e_nessun_compito_in_corso(self):
        self.sospendi(spese=False, attivita=True)
        run = nuovo_run(os.path.join(self.d, "run"), "completo")
        self.assertEqual(run.avanza()["stato"], "bloccato")
        self.assertEqual(run.state["fasi_completate"], [])
        q = self.coda()
        q.add("QA-AVVIO", "x", "ricerca-mercato")
        with self.assertRaises(RuntimeError):
            q.set_stato("QA-AVVIO", "in_corso")

    def test_spesa_ads_in_pausa_durante_distribuzione(self):
        run = nuovo_run(os.path.join(self.d, "run"), "completo")
        while run.state["fase_corrente"] != "distribuzione":
            run.esegui_fase(run.state["fase_corrente"])
        vero = Ledger.draw

        def draw(s, b, did, imp, nota=""):
            if did == "giorno-1":
                self.sospendi(spese=True, attivita=False)
            return vero(s, b, did, imp, nota)
        with mock.patch.object(Ledger, "draw", draw):
            run.esegui_fase("distribuzione")
        ads = [b for b in run.ledger.data["buste"].values() if b["categoria"] == "ads" and "prenotazione" not in b["id"]]
        self.assertTrue(ads)
        self.assertEqual([list(b["consumi"]) for b in ads], [["giorno-1"]])

    # ex DIFETTO S-1: la fase già in corso esentata dal workflow cade sulla coda — corretto, riverificato 2026-11-23
    def test_ripresa_fase_in_corso_durante_sospensione_senza_eccezione(self):
        run = nuovo_run(os.path.join(self.d, "run"), "interruzione")
        try:
            run.avanza()
        except Exception:
            pass
        self.assertIsNotNone(run.state["in_esecuzione"])
        self.sospendi(spese=False, attivita=True)
        Run(os.path.join(self.d, "run")).avanza()  # RuntimeError da queue.set_stato(in_corso)


# ----------------------------------------------------------------------------- 5. app (analisi statica)
class TestQAApp(unittest.TestCase):
    def test_nessun_html_da_dati(self):
        self.assertIsNone(re.search(r"innerHTML|outerHTML|insertAdjacentHTML|document\.write|\beval\(|new Function", JS))
        self.assertIn('e.textContent=v', JS)

    def test_pagina_scrive_solo_inviato(self):
        self.assertIn('stato:"inviato"', JS)
        self.assertIsNone(re.search(r'stato\s*:\s*"(completato|fallito|ricevuto|in_esecuzione)"', JS))
        self.assertIsNone(re.search(r'\.(update|set)\([^)]*completato', JS))

    def test_id_riusato_ai_tentativi(self):
        self.assertRegex(JS, r'pend\.tipo===tipo && JSON\.stringify\(pend\.parametri\)===JSON\.stringify\(parametri\)\) \? pend\.id')
        self.assertIn('if(!g.exists) await ref.set(doc)', JS)
        self.assertIn("crypto.getRandomValues", JS)

    def test_accesso_negato_ai_non_titolari_prima_del_database(self):
        i_owner = JS.index("isOwner()")
        i_gate = JS.index("if(!owner){", i_owner)
        self.assertLess(i_gate, JS.index('claude.use("db")', JS.index("async function avvio")))
        self.assertIn("return; }", JS[i_gate:i_gate + 400])

    def test_demo_separata_e_mai_scritta(self):
        corpo = JS[JS.index("async function invia"):JS.index("function messaggio")]
        self.assertLess(corpo.index("if(S.demo) return"), corpo.index("claude.use"))
        demo = JS[JS.index("function datiDemo"):JS.index("function agenti")]
        self.assertNotIn("claude.use", demo)

    def test_soglia_battito_segnalata(self):
        self.assertIn('if(eta > (c.soglia_minuti||10)) return {stato:"bad", testo:"stato non aggiornato", stale:true}', JS)

    # ex DIFETTO A-1: a soglia superata senza nuovi dati si ridisegna solo l'intestazione — corretto, riverificato 2026-11-23
    def test_superata_la_soglia_si_ridisegnano_gli_stati(self):
        nome = re.search(r"setInterval\(\s*(\w+)", JS).group(1)
        if nome != "renderAll":
            corpo = re.search(r"function " + nome + r"\(\)\{(.*?)\n\}", JS, re.S).group(1)
            self.assertIn("renderAll", corpo)


if __name__ == "__main__":
    unittest.main()
