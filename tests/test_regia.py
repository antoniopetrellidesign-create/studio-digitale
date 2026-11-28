"""Ponte della regia: stati onesti degli agenti, comandi idempotenti, sospensione con effetto sul motore."""
import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from studio import regia
from studio.ledger import Ledger, SpendBlocked
from studio.workflow import ROOT, carica_json, nuovo_run

POL = carica_json("config/policy.json")


def _ev(evento, minuti_fa, **kw):
    q = (datetime.now(timezone.utc) - timedelta(minutes=minuti_fa)).isoformat(timespec="seconds")
    return {"quando": q, "evento": evento, **kw}


class _Team(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.team = os.path.join(self.d, "team")
        os.makedirs(self.team)
        shutil.copy(os.path.join(ROOT, "team", "queue.json"), os.path.join(self.team, "queue.json"))
        self.env = mock.patch.dict(os.environ, {"STUDIO_TEAM_DIR": self.team,
                                                "STUDIO_SOSPENSIONE": os.path.join(self.team, "sospensione.json")})
        self.env.start()
        self.addCleanup(self.env.stop)


class TestStatiAgenti(_Team):
    def _stato(self, evs, fresco=True):
        return {a["id"]: a for a in regia.stato_agenti(evs, fresco)}

    def test_definito_non_vuol_dire_attivo(self):
        a = self._stato([])
        self.assertEqual(a["customer-care"]["stato"], "mai_avviato_registrato")

    def test_in_esecuzione_concluso_sconosciuto(self):
        evs = [_ev("SubagentStart", 2, agente_id="x1", agente_tipo="customer-care"),
               _ev("PreToolUse", 1, agente_id="x1", agente_tipo="customer-care", strumento="Write",
                   sintesi="Write", file="team/consegne/x.md")]
        a = self._stato(evs)["customer-care"]
        self.assertEqual(a["stato"], "in_esecuzione")
        self.assertEqual(a["attivita_corrente"], "Write")
        self.assertIn("team/consegne/x.md", a["file_prodotti"])
        self.assertEqual(self._stato(evs, fresco=False)["customer-care"]["stato"], "sconosciuto")  # ponte perso
        vecchi = [_ev("SubagentStart", 90, agente_id="x2", agente_tipo="customer-care")]
        self.assertEqual(self._stato(vecchi)["customer-care"]["stato"], "sconosciuto")  # nessun evento recente
        fine = evs + [_ev("SubagentStop", 0, agente_id="x1", agente_tipo="customer-care", ultimo_messaggio="fatto")]
        a = self._stato(fine)["customer-care"]
        self.assertEqual(a["stato"], "concluso")
        self.assertEqual(a["esecuzioni"]["concluse"], 1)

    def test_passaggi_solo_se_registrati(self):
        coda = [{"id": "A", "agente": "ricerca-mercato", "stato": "fatto", "aggiornato": "t", "dipende_da": []},
                {"id": "B", "agente": "qa-indipendente", "stato": "da_fare", "dipende_da": ["A"]},
                {"id": "C", "agente": "qa-indipendente", "stato": "da_fare", "dipende_da": ["B"]}]
        p = regia.passaggi(coda)
        self.assertEqual([(x["da"], x["a"]) for x in p], [("ricerca-mercato", "qa-indipendente")])

    def test_collegamento_scaduto(self):
        regia.battito("prova")
        dopo = datetime.now(timezone.utc) + timedelta(minutes=30)
        self.assertFalse(regia.collegamento(dopo)["fresco"])
        self.assertTrue(regia.collegamento()["fresco"])


class TestComandi(_Team):
    def test_comando_duplicato_eseguito_una_volta(self):
        c = {"id": "cmd-prova-0001", "tipo": "obiettivo", "parametri": {"testo": "riepilogo budget", "priorita": "alta"}}
        r1 = regia.esegui_comando(c)
        r2 = regia.esegui_comando(c)
        self.assertEqual(r1["stato"], "completato")
        self.assertTrue(r2.get("duplicato"))
        coda = json.load(open(os.path.join(self.team, "queue.json")))["compiti"]
        self.assertEqual(sum(1 for t in coda if t["id"] == "OB-cmd-prova-0001"), 1)

    def test_comando_non_valido_fallisce_senza_effetti(self):
        self.assertEqual(regia.esegui_comando({"id": "x", "tipo": "obiettivo"})["stato"], "fallito")
        self.assertEqual(regia.esegui_comando({"id": "cmd-sconosciuto", "tipo": "cancella_tutto"})["stato"], "fallito")
        self.assertEqual(regia.esegui_comando({"id": "cmd-prio-0001", "tipo": "priorita",
                                               "parametri": {"compito": "NON-ESISTE", "priorita": "alta"}})["stato"], "fallito")

    def test_sospensione_agisce_sul_motore_e_ripresa(self):
        r = regia.esegui_comando({"id": "cmd-sosp-0001", "tipo": "sospendi", "parametri": {"spese": True, "attivita": True}})
        self.assertEqual(r["stato"], "completato")
        led = Ledger(os.path.join(self.d, "l.json"), 50000, POL["allocazione_budget_cents"], POL["categorie_spesa"])
        with self.assertRaises(SpendBlocked):
            led.reserve("x/ads", "ads", 100, "nuova spesa")
        run = nuovo_run(os.path.join(self.d, "run"), "completo")
        self.assertEqual(run.avanza()["stato"], "bloccato")
        self.assertEqual(run.ledger.consumato(), 0)
        # ripresa di un compito bloccata finché le attività sono sospese
        self.assertEqual(regia.esegui_comando({"id": "cmd-rip-0001", "tipo": "riprendi",
                                               "parametri": {"compito": "T-020"}})["stato"], "fallito")
        r = regia.esegui_comando({"id": "cmd-rip-0002", "tipo": "riprendi", "parametri": {}})
        self.assertEqual(r["stato"], "completato")
        led.reserve("x/ads", "ads", 100, "nuova spesa")  # di nuovo consentita
        self.assertEqual(led.impegnato_aperto(), 100)


class TestIstantanea(_Team):
    def test_istantanea_senza_segreti_e_simulazioni_escluse(self):
        s = regia.istantanea()
        self.assertTrue(s["numeri"]["simulazioni_escluse"])
        self.assertEqual(s["riepilogo"]["prodotti_selezionati"], 0)
        testo = json.dumps(s)
        from studio.phases import SEGRETI
        self.assertIsNone(SEGRETI.search(testo))
        docs = regia.documenti_db(s)
        self.assertTrue(all(len(json.dumps(v).encode()) < 256 * 1024 for v in docs.values()))


if __name__ == "__main__":
    unittest.main()


class TestPartita(_Team):
    def test_livelli_solo_da_fatti_e_scelta_una_volta(self):
        import json as _j
        carte_p = os.path.join(ROOT, "research", "carte-candidati.json")
        if not os.path.exists(carte_p):
            self.skipTest("carte non ancora pronte")
        cid = str(_j.load(open(carte_p))[0]["id"])
        p = regia.partita(regia.numeri())
        self.assertEqual(p["livello_corrente"], "scelta")
        self.assertEqual(p["missione"]["tipo"], "scelta_prodotto")
        r = regia.esegui_comando({"id": "cmd-scelta-0001", "tipo": "scelta_prodotto", "parametri": {"carta": cid}})
        self.assertEqual(r["stato"], "completato")
        self.assertEqual(regia.partita(regia.numeri())["livello_corrente"], "pagina")
        r2 = regia.esegui_comando({"id": "cmd-scelta-0002", "tipo": "scelta_prodotto", "parametri": {"carta": cid}})
        self.assertEqual(r2["stato"], "fallito")

    def test_carta_inesistente_rifiutata(self):
        r = regia.esegui_comando({"id": "cmd-scelta-0003", "tipo": "scelta_prodotto", "parametri": {"carta": "non-esiste"}})
        self.assertEqual(r["stato"], "fallito")
