"""CLI dello studio.  python3 -m studio <comando> ..."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

from .phases import SimulatedCrash
from .workflow import ROOT, Run, nuovo_run

RUNS = os.path.join(ROOT, "runs")
EXIT_INTERROTTO = 75


def _dir(run_id, base=None):
    return os.path.join(base or RUNS, run_id)


def _stampa(r: dict):
    reg = r["registro"]
    print(f"run {r['run_id']} [{r['scenario']}, {r['modalita']}] → stato: {r['stato']}"
          + (f", esito: {r['esito_finale']}" if r["esito_finale"] else ""))
    print(f"  fasi completate: {' → '.join(r['fasi_completate']) or '-'}")
    if r["fase_corrente"]:
        print(f"  fase corrente: {r['fase_corrente']}")
    if r["blocco"]:
        print(f"  BLOCCO in '{r['blocco']['fase']}': {r['blocco']['motivo']}")
    for a in r["azioni_titolare"]:
        print(f"  azione titolare [{a['stato']}]: {a['id']} — {a['descrizione']}")
    print(f"  registro: consumato {reg['consumato_cents']/100:.2f} € | impegnato {reg['impegnato_aperto_cents']/100:.2f} € "
          f"| residuo {reg['residuo_cents']/100:.2f} € su {reg['tetto_cents']/100:.2f} € | tentativi bloccati "
          f"{reg['tentativi_bloccati']}")


def _avanza(run: Run) -> int:
    try:
        r = run.avanza()
    except SimulatedCrash as e:
        print(f"SESSIONE INTERROTTA (simulata): {e}. Riprendi con: python3 -m studio resume --run-id "
              f"{run.state['run_id']}", file=sys.stderr)
        sys.stdout.flush()
        os._exit(EXIT_INTERROTTO)  # uscita brusca: nessun salvataggio di cortesia
    _stampa(r)
    return 0 if r["stato"] in ("completato", "fermato", "bloccato_titolare", "bloccato") else 1


def main(argv=None):
    p = argparse.ArgumentParser(prog="studio")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("simulate", help="avvia una simulazione su uno scenario sintetico")
    s.add_argument("--scenario", default="completo")
    s.add_argument("--run-id")
    s.add_argument("--modalita", default="simulato", choices=["simulato", "live"])
    s.add_argument("--registro", help="registro spese condiviso tra più run (stesso tetto)")
    s.add_argument("--runs-dir")
    r = sub.add_parser("resume", help="riprende un run dal punto corretto")
    r.add_argument("--run-id", required=True)
    r.add_argument("--concedi", action="append", default=[], help="concessione del titolare, es. shopify")
    r.add_argument("--runs-dir")
    for nome in ("status", "ledger", "decisions"):
        x = sub.add_parser(nome)
        x.add_argument("--run-id", required=True)
        x.add_argument("--runs-dir")
    c = sub.add_parser("collaudo", help="esegue tutti gli scenari di collaudo e scrive il report")
    c.add_argument("--runs-dir")
    q = sub.add_parser("queue", help="coda condivisa del team (team/queue.json)")
    q.add_argument("azione", choices=["list", "set", "add"])
    q.add_argument("args", nargs="*")
    a = p.parse_args(argv)

    if a.cmd == "simulate":
        rid = a.run_id or f"{a.scenario}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        try:
            run = nuovo_run(_dir(rid, a.runs_dir), a.scenario, a.modalita, a.registro)
        except FileExistsError as e:
            print(f"RIFIUTATO ({type(e).__name__}): {e}", file=sys.stderr)
            return 2
        return _avanza(run)
    if a.cmd == "resume":
        run = Run(_dir(a.run_id, a.runs_dir))
        if run.state["stato"] in ("completato", "fermato"):
            _stampa(run.riepilogo())
            print("  (run già concluso: nessuna azione)")
            return 0
        for c_ in a.concedi:
            run.concedi(c_)
        if run.state["stato"] == "bloccato_titolare":
            _stampa(run.riepilogo())
            print("  (in attesa del titolare: usa --concedi <azione> quando è stata completata)")
            return 0
        if run.state["stato"] == "bloccato":
            run.state["stato"] = "in_corso"
            run.decidi(run.state["fase_corrente"], "nuovo_tentativo", "ripresa manuale dopo blocco", attore="team-lead")
        return _avanza(run)
    if a.cmd == "status":
        _stampa(Run(_dir(a.run_id, a.runs_dir)).riepilogo())
        return 0
    if a.cmd == "ledger":
        print(Run(_dir(a.run_id, a.runs_dir)).ledger.testo())
        return 0
    if a.cmd == "decisions":
        with open(os.path.join(_dir(a.run_id, a.runs_dir), "decisions.jsonl"), encoding="utf-8") as f:
            for l in f:
                d = json.loads(l)
                print(f"{d['quando']} {d['fase']:<14} {d['decisione']:<24} [{d['attore']}] {d['motivo']}")
        return 0
    if a.cmd == "collaudo":
        from .collaudo import esegui
        return esegui(a.runs_dir)
    if a.cmd == "queue":
        from .queue import TaskQueue
        tq = TaskQueue(os.path.join(ROOT, "team", "queue.json"))
        if a.azione == "list":
            print(tq.testo())
        elif a.azione == "set":
            tq.set_stato(a.args[0], a.args[1], " ".join(a.args[2:]))
            print(tq.testo())
        else:
            tq.add(a.args[0], a.args[2], a.args[1])
            print(tq.testo())
        return 0


if __name__ == "__main__":
    sys.exit(main())
