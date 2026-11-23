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
    ac = sub.add_parser("accessi", help="documento cifrato ACCESSI_SISTEMA")
    ac.add_argument("azione", choices=["indice", "nuovo", "esporta"])
    ac.add_argument("--servizio")
    ac.add_argument("--dati", default="{}", help="JSON dei campi NON segreti (funzione, url_accesso, piano, ...)")
    ac.add_argument("--genera-password", action="store_true")
    ac.add_argument("--identita", help="(solo titolare) chiave privata age/ssh per l'esportazione")
    acc = sub.add_parser("account", help="registro account: stato e passaggi del titolare")
    acc.add_argument("azione", choices=["stato", "passaggi"])
    acc.add_argument("--fase", default="strategia")
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
    if a.cmd == "accessi":
        from .vault import Vault, VaultNonConfigurato, genera_password
        v = Vault(os.path.join(ROOT, "accessi"), os.path.join(ROOT, "config", "accessi_destinatari.txt"))
        if a.azione == "indice":
            p = os.path.join(ROOT, "accessi", "INDICE.md")
            print(open(p, encoding="utf-8").read() if os.path.exists(p) else "(nessuna voce)")
            print(f"destinatari configurati: {len(v.destinatari())}")
            return 0
        if a.azione == "nuovo":
            dati = json.loads(a.dati)
            from .vault import CAMPI_SEGRETI
            vietati = [k for k in dati if k in CAMPI_SEGRETI and k not in ("email", "utente")]
            if vietati:  # QA minore: niente segreti sulla riga di comando (finirebbero nella cronologia della shell)
                print(f"RIFIUTATO: campi segreti {vietati} non ammessi in --dati: usa --genera-password o il modulo "
                      "sicuro dei segreti dell'ambiente", file=sys.stderr)
                return 2
            if a.genera_password:
                dati["password"] = genera_password()
            try:
                r = v.registra(a.servizio, "creazione", dati)
            except VaultNonConfigurato as e:
                print(f"RIFIUTATO: {e}", file=sys.stderr)
                return 2
            print(f"voce cifrata: accessi/{r['voce']}  riferimenti: {', '.join(r['riferimenti'])}")
            return 0
        doc = v.esporta(a.identita)
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        return 0
    if a.cmd == "account":
        from .accounts import AccountRegistry
        from .workflow import carica_json
        reg = AccountRegistry(carica_json("config/account_catalogo.json"), os.path.join(ROOT, "accessi", "account.json"))
        if a.azione == "stato":
            for sid, s in reg.catalogo.items():
                motivi = reg.verifica(sid, a.fase)
                print(f"{sid:<16} {reg.stato_di(sid):<20} fase {s['fase_richiesta']:<13} "
                      f"{'attivabile' if not motivi else 'NON attivabile: ' + '; '.join(motivi)}")
        else:
            for p in reg.passaggi_titolare(a.fase):
                print(f"[{p['servizio']}] {p['passo']}. {p['azione']}")
        return 0
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
