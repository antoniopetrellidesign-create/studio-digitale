"""Motore del workflow: stato persistente, ripresa dal punto corretto, traccia delle decisioni.

File di un run (runs/<run_id>/):
  state.json            stato (fase corrente, fasi completate, tentativi, blocchi, azioni titolare)
  decisions.jsonl       traccia append-only di ogni decisione e passaggio di fase
  artifacts/<fase>.json output obbligatori di ogni fase
  ledger.json           registro spese (o un registro condiviso indicato con --registro)
  orders.json           libro ordini deduplicato
  external_calls.jsonl  ogni chiamata agli adattatori (simulata o bloccata)
  queue.json            compiti generati per gli agenti responsabili
  AZIONI_TITOLARE.md    pacchetto unico delle azioni riservate al titolare
"""
from __future__ import annotations

import copy
import json
import os
from datetime import datetime, timezone

from . import adapters as adapters_mod
from .adapters.base import ExternalActionBlocked
from .ledger import Ledger, SpendBlocked
from .orders import OrderBook
from .phases import FASI, NOMI_FASI, SEGRETI, NeedOwner, PhaseStop, SimulatedCrash
from .queue import TaskQueue
from .storage import append_jsonl, atomic_write_json, read_json, read_jsonl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATI_ATTIVI = ("nuovo", "in_corso")


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def deep_merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def carica_scenario(nome_o_path: str) -> dict:
    path = nome_o_path if nome_o_path.endswith(".json") else os.path.join(ROOT, "fixtures", "scenari", nome_o_path + ".json")
    with open(path, encoding="utf-8") as f:
        sc = json.load(f)
    if "estende" in sc:
        base = carica_scenario(sc["estende"])
        sc = deep_merge(base, {k: v for k, v in sc.items() if k != "estende"})
    return sc


def carica_json(rel: str) -> dict:
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


class Run:
    def __init__(self, run_dir: str, scenario: dict | None = None, modalita: str = "simulato",
                 registro: str | None = None):
        self.dir = run_dir
        os.makedirs(os.path.join(run_dir, "artifacts"), exist_ok=True)
        self.state_path = os.path.join(run_dir, "state.json")
        st = read_json(self.state_path)
        if st is None:
            if scenario is None:
                raise FileNotFoundError(f"nessun run in {run_dir}")
            st = {"run_id": os.path.basename(run_dir), "scenario": scenario, "modalita": modalita,
                  "registro": os.path.abspath(registro) if registro else os.path.join(run_dir, "ledger.json"),
                  "stato": "nuovo", "fase_corrente": NOMI_FASI[0], "fasi_completate": [], "tentativi": {},
                  "in_esecuzione": None, "concessioni": [], "azioni_titolare": [], "blocco": None,
                  "esito_finale": None, "riprese": 0, "creato": _now(), "aggiornato": _now()}
            self.state = st
            self._save()
        self.state = st
        self.scenario = st["scenario"]
        self.modalita = st["modalita"]
        self.policy = carica_json("config/policy.json")
        self.commissioni = carica_json("config/commissioni.json")
        self.ledger = Ledger(st["registro"], self.policy["tetto_primo_test_cents"],
                             self.policy["allocazione_budget_cents"], self.policy["categorie_spesa"])
        self.orders = OrderBook(os.path.join(run_dir, "orders.json"))
        self.queue = TaskQueue(os.path.join(run_dir, "queue.json"))
        self.calls_path = os.path.join(run_dir, "external_calls.jsonl")
        self.gate = adapters_mod.ExternalGate(self.modalita, self.calls_path)
        guasti = dict(self.scenario.get("guasti", {}))
        if "shopify" in st["concessioni"]:
            guasti["shopify_accesso"] = True
        self.guasti = guasti
        self.adapters = adapters_mod.build(self.modalita, self.gate, guasti)

    # ------------------------------------------------------------------ utilità
    def _save(self):
        self.state["aggiornato"] = _now()
        atomic_write_json(self.state_path, self.state)

    def bid(self, nome: str) -> str:
        """ID busta specifico del run: con un registro condiviso i run non si sovrappongono."""
        return f"{self.state['run_id']}/{nome}"

    def artifact(self, fase: str) -> dict:
        a = read_json(os.path.join(self.dir, "artifacts", f"{fase}.json"))
        if a is None:
            raise RuntimeError(f"output della fase '{fase}' mancante: ordine delle fasi violato")
        return a

    def decidi(self, fase: str, decisione: str, motivo: str, attore: str = "motore", **dati):
        append_jsonl(os.path.join(self.dir, "decisions.jsonl"),
                     {"quando": _now(), "fase": fase, "decisione": decisione, "motivo": motivo, "attore": attore, **dati})

    def azione_titolare(self, azione_id: str, descrizione: str, concessione: str):
        if not any(a["id"] == azione_id for a in self.state["azioni_titolare"]):
            self.state["azioni_titolare"].append({"id": azione_id, "descrizione": descrizione,
                                                  "concessione": concessione, "stato": "in_attesa", "creata": _now()})
            self._save()
        self._scrivi_pacchetto_titolare()

    def _scrivi_pacchetto_titolare(self):
        righe = ["# Azioni riservate al titolare (pacchetto unico)", "",
                 "Eseguire tutte le voci in un'unica sessione. Non incollare credenziali, carte o OTP in chat o nei file.", ""]
        for a in self.state["azioni_titolare"]:
            righe.append(f"- [{'x' if a['stato'] == 'concessa' else ' '}] `{a['id']}` — {a['descrizione']}")
        with open(os.path.join(self.dir, "AZIONI_TITOLARE.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(righe) + "\n")

    def crash_once(self, fase: str):
        marker = os.path.join(self.dir, f".interruzione-{fase}")
        if not os.path.exists(marker):
            open(marker, "w").close()
            raise SimulatedCrash(f"interruzione simulata durante '{fase}'")

    def scan_segreti(self) -> list:
        trovati = []
        for nome in os.listdir(self.dir):
            p = os.path.join(self.dir, nome)
            if os.path.isfile(p):
                with open(p, encoding="utf-8", errors="ignore") as f:
                    if SEGRETI.search(f.read()):
                        trovati.append(nome)
        return trovati

    def azioni_esterne_reali(self) -> int:
        return sum(1 for c in read_jsonl(self.calls_path) if c["esito"] not in ("simulato", "bloccato"))

    # ------------------------------------------------------------------ motore
    def concedi(self, concessione: str):
        """Registra che il titolare ha completato un'azione (es. 'shopify'). Sblocca il run."""
        if concessione not in self.state["concessioni"]:
            self.state["concessioni"].append(concessione)
        for a in self.state["azioni_titolare"]:
            if a["concessione"] == concessione:
                a["stato"] = "concessa"
        if self.state["stato"] == "bloccato_titolare" and self.state["blocco"] and \
                self.state["blocco"].get("concessione") == concessione:
            self.state["stato"] = "in_corso"
            self.state["blocco"] = None
        self._save()
        self.decidi(self.state["fase_corrente"], "concessione_titolare", f"concessione '{concessione}' registrata",
                    attore="titolare")
        self.__init__(self.dir)  # ricostruisce gli adattatori con la concessione
        self._scrivi_pacchetto_titolare()

    def esegui_fase(self, nome: str) -> bool:
        """Esegue una fase. Rifiuta l'esecuzione fuori ordine. Ritorna True se il controllo è superato."""
        idx = NOMI_FASI.index(nome)
        mancanti = [f for f in NOMI_FASI[:idx] if f not in self.state["fasi_completate"]]
        if mancanti or nome != self.state["fase_corrente"]:
            raise RuntimeError(f"fase '{nome}' fuori ordine: mancano {mancanti}, fase corrente "
                               f"'{self.state['fase_corrente']}'")
        _, owner, richiesti, handler, gate = FASI[idx]

        ripresa = self.state["in_esecuzione"] and self.state["in_esecuzione"]["fase"] == nome
        if ripresa:
            tentativo = self.state["in_esecuzione"]["tentativo"]
            self.state["riprese"] += 1
            self.decidi(nome, "ripresa", f"ripresa della fase dopo interruzione (tentativo {tentativo})")
        else:
            tentativo = self.state["tentativi"].get(nome, 0) + 1
            self.state["tentativi"][nome] = tentativo
        self.state["in_esecuzione"] = {"fase": nome, "tentativo": tentativo, "iniziata": _now()}
        self.state["stato"] = "in_corso"
        self._save()
        task_id = f"{nome}-{tentativo}"
        self.queue.add(task_id, f"Fase {nome} (tentativo {tentativo})", owner, fase=nome, output=richiesti,
                       run_id=self.state["run_id"])
        self.queue.set_stato(task_id, "in_corso")

        # Costo AI incrementale: riservato prima, idempotente per (fase, tentativo).
        ai = self.scenario.get("costi_ai_per_fase_cents", {"max": 300, "effettivo": 100})
        busta_ai = self.bid(f"ai-{nome}-{tentativo}")
        try:
            self.ledger.reserve(busta_ai, "ai", ai["max"], f"costo AI fase {nome}", fase=nome, tag=["ai"])
            costo = self.adapters["ai"].esegui(nome, busta=busta_ai, costo_cents=ai["effettivo"])
            self.ledger.draw(busta_ai, "unico", costo, f"AI fase {nome}")
            self.ledger.close(busta_ai)
            out = handler(self)
        except NeedOwner as e:
            self.azione_titolare(e.azione_id, e.descrizione, e.concessione)
            return self._blocca(nome, task_id, "bloccato_titolare", e.descrizione, concessione=e.concessione)
        except PhaseStop as e:
            return self._ferma(nome, task_id, str(e))
        except SpendBlocked as e:
            return self._blocca(nome, task_id, "bloccato", f"spesa bloccata: {e.motivo}", dettagli=e.dettagli,
                                escalation="strategia-finanza → team-lead")
        except ExternalActionBlocked as e:
            if busta_ai in self.ledger.data["buste"]:
                self.ledger.close(busta_ai)
            return self._blocca(nome, task_id, "bloccato", f"azione esterna bloccata: {e}",
                                escalation="team-lead (integrazione live non collegata)")

        mancanti_out = [k for k in richiesti if k not in out]
        ok, motivi = gate(self, out) if not mancanti_out else (False, [f"output obbligatorio mancante: {k}" for k in mancanti_out])
        atomic_write_json(os.path.join(self.dir, "artifacts", f"{nome}.json"), out)
        self.state["in_esecuzione"] = None
        if ok:
            self.state["fasi_completate"].append(nome)
            self.queue.set_stato(task_id, "fatto")
            self.decidi(nome, "fase_approvata", "controllo di sblocco superato", attore="team-lead",
                        responsabile=owner, tentativo=tentativo)
            if idx + 1 < len(NOMI_FASI):
                self.state["fase_corrente"] = NOMI_FASI[idx + 1]
            else:
                self.state["fase_corrente"] = None
                self.state["stato"] = "completato"
                self.state["esito_finale"] = out["esito"]
                self.decidi(nome, f"esito_{out['esito']}", "; ".join(out["motivi"]), attore="team-lead")
            self._save()
            return True

        self.queue.set_stato(task_id, "bloccato", "; ".join(motivi))
        if nome == "qa":
            self.decidi("qa", "qa_bloccato", "; ".join(motivi), attore="qa-indipendente", tentativo=tentativo)
            if self.state["tentativi"].get("prodotto", 0) < self.policy["qa"]["max_tentativi_prodotto"]:
                self.state["fasi_completate"].remove("prodotto")
                self.state["fase_corrente"] = "prodotto"
                self.decidi("qa", "ritorno_a_prodotto", "il prodotto torna a sviluppo-prodotto con i motivi del QA",
                            attore="team-lead")
                self._save()
                return False
            return self._ferma("qa", task_id, "prodotto respinto dal QA oltre il numero massimo di tentativi",
                               gia_bloccato=True)
        return self._blocca(nome, task_id, "bloccato", "controllo di sblocco fallito: " + "; ".join(motivi),
                            escalation="team-lead")

    def _blocca(self, fase, task_id, stato, motivo, **extra):
        self.state["stato"] = stato
        self.state["blocco"] = {"fase": fase, "motivo": motivo, **extra}
        self.state["in_esecuzione"] = None
        self._save()
        if self.queue.get(task_id)["stato"] != "bloccato":
            self.queue.set_stato(task_id, "bloccato", motivo)
        self.decidi(fase, stato, motivo, attore="motore", **{k: v for k, v in extra.items() if k != "dettagli"})
        return False

    def _ferma(self, fase, task_id, motivo, gia_bloccato=False):
        self.state["stato"] = "fermato"
        self.state["esito_finale"] = "stop"
        self.state["in_esecuzione"] = None
        self.state["costo_test_fallito_cents"] = self.ledger.consumato(prefisso=self.bid(""))
        self._save()
        if not gia_bloccato:
            self.queue.set_stato(task_id, "bloccato", motivo)
        self.decidi(fase, "test_fermato", motivo, attore="team-lead",
                    costo_test_fallito_cents=self.state["costo_test_fallito_cents"])
        return False

    def avanza(self) -> dict:
        while self.state["stato"] in STATI_ATTIVI and self.state["fase_corrente"]:
            self.esegui_fase(self.state["fase_corrente"])
        return self.riepilogo()

    def riepilogo(self) -> dict:
        s = self.state
        return {"run_id": s["run_id"], "scenario": self.scenario["nome"], "modalita": s["modalita"], "stato": s["stato"],
                "fase_corrente": s["fase_corrente"], "fasi_completate": s["fasi_completate"],
                "tentativi": s["tentativi"], "riprese": s["riprese"], "blocco": s["blocco"],
                "esito_finale": s["esito_finale"], "azioni_titolare": s["azioni_titolare"],
                "registro": self.ledger.riepilogo()}


def nuovo_run(run_dir: str, scenario_nome: str, modalita="simulato", registro=None) -> Run:
    if os.path.exists(os.path.join(run_dir, "state.json")):
        raise FileExistsError(f"esiste già un run in {run_dir}: usa 'resume'")
    return Run(run_dir, carica_scenario(scenario_nome), modalita, registro)
