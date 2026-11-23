"""Collaudo end-to-end: esegue tutti gli scenari sintetici e verifica gli esiti attesi.

Ogni run usa processi separati (`python3 -m studio ...`) così l'interruzione è un'uscita reale del processo.
Scrive il report in <runs-dir>/REPORT.md.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime

from .storage import read_json, read_jsonl
from .workflow import ROOT

EXIT_INTERROTTO = 75


def _cli(args, runs_dir):
    env = dict(os.environ, STUDIO_LIVE="0", PYTHONPATH=ROOT)
    return subprocess.run([sys.executable, "-m", "studio", *args, "--runs-dir", runs_dir], cwd=ROOT, env=env,
                          capture_output=True, text=True)


def _stato(runs_dir, rid):
    return read_json(os.path.join(runs_dir, rid, "state.json"))


def _art(runs_dir, rid, fase):
    return read_json(os.path.join(runs_dir, rid, "artifacts", f"{fase}.json"))


def _decisioni(runs_dir, rid):
    return read_jsonl(os.path.join(runs_dir, rid, "decisions.jsonl"))


def _ledger(runs_dir, rid, path=None):
    return read_json(path or os.path.join(runs_dir, rid, "ledger.json"))


def _speso(led):
    tot = 0
    for b in led["buste"].values():
        tot += sum(d["importo_cents"] for d in b["consumi"].values() if not d.get("stornato"))
    return tot


def _impegnato(led):
    tot = 0
    for b in led["buste"].values():
        if b["stato"] == "aperta":
            tot += b["max_cents"] - sum(d["importo_cents"] for d in b["consumi"].values() if not d.get("stornato"))
    return tot


def _sim(scenario, runs_dir, rid, *extra):
    return _cli(["simulate", "--scenario", scenario, "--run-id", rid, *extra], runs_dir)


def _ordine_fasi_ok(runs_dir, rid):
    from .phases import NOMI_FASI
    approvate = [d["fase"] for d in _decisioni(runs_dir, rid) if d["decisione"] == "fase_approvata"]
    # Ogni fase approvata deve avere già approvate tutte le precedenti (ammessi i ritorni QA → Prodotto).
    viste = []
    for f in approvate:
        idx = NOMI_FASI.index(f)
        if any(p not in viste for p in NOMI_FASI[:idx]):
            return False
        viste.append(f)
    return True


def esegui(runs_dir=None) -> int:
    runs_dir = runs_dir or os.path.join(ROOT, "runs", "collaudo-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    os.makedirs(runs_dir, exist_ok=True)
    risultati = []

    def caso(nome, descrizione, verifiche):
        ok = all(v for _, v in verifiche)
        risultati.append({"caso": nome, "descrizione": descrizione, "ok": ok,
                          "verifiche": [{"verifica": t, "ok": bool(v)} for t, v in verifiche]})

    # 1. Simulazione completa
    p = _sim("completo", runs_dir, "completo")
    st, led = _stato(runs_dir, "completo"), _ledger(runs_dir, "completo")
    met = _art(runs_dir, "completo", "misurazione")["metriche"]
    caso("completo", "flusso completo su 3 opportunità fittizie", [
        ("processo terminato con codice 0", p.returncode == 0),
        ("stato completato", st["stato"] == "completato"),
        ("10 fasi approvate nell'ordine previsto", len(st["fasi_completate"]) == 10 and _ordine_fasi_ok(runs_dir, "completo")),
        ("scheda incompleta scartata in Ricerca", len(_art(runs_dir, "completo", "ricerca")["scartate"]) == 1),
        ("selezionata l'unica opportunità idonea", _art(runs_dir, "completo", "selezione")["selezionata"] == "OPP-SIM-A"),
        ("esito di decisione registrato", st["esito_finale"] in ("stop", "ripeti", "scala")),
        ("spesa ≤ tetto", _speso(led) + _impegnato(led) <= led["tetto_cents"]),
        ("nessuna busta di canale aperta a fine test", _impegnato(led) == 0),
        ("tutte le chiamate esterne simulate",
         all(c["esito"] == "simulato" for c in read_jsonl(os.path.join(runs_dir, "completo", "external_calls.jsonl")))),
        ("scheda prodotto rimasta in bozza", _art(runs_dir, "completo", "shopify")["stato_scheda"] == "bozza"),
        ("download dell'ordine di prova verificato", _art(runs_dir, "completo", "ordine_prova")["download_ok"]),
    ])

    # 2. Doppia attribuzione e rimborso (dentro il run completo)
    o = read_json(os.path.join(runs_dir, "completo", "orders.json"))
    env_comm = led["buste"]["completo/creator-CR-SIM-1-commissioni"]["consumi"]
    caso("doppia_attribuzione", "ordine SIM-1011 con codice creator e click Ads", [
        ("ordine contato una sola volta", list(o["ordini"]).count("SIM-1011") == 1 and met["ordini"] == 14),
        ("ricavi per canale = ricavi totali (nessun doppio conteggio)", met["controllo_doppio_conteggio_ok"]),
        ("commissione creator dovuta sull'ordine", "SIM-1011" in env_comm and not env_comm["SIM-1011"].get("stornato")),
        ("spesa Ads conservata", met["costi_cents"]["ads"] > 0),
        ("ordine assistito da creator e da Ads", met["per_canale"]["ads"]["ordini_assistiti"] == met["per_canale"]["ads"]["ordini_primari"] + 1),
        ("webhook duplicato scartato", o["duplicati_scartati"] >= 1),
    ])
    caso("rimborso", "SIM-1002 rimborsato entro la finestra di clawback", [
        ("ordine marcato rimborsato", o["ordini"]["SIM-1002"]["rimborsato"]),
        ("commissione creator stornata", env_comm["SIM-1002"].get("stornato") is True),
        ("ricavo escluso dai ricavi netti", met["ordini_rimborsati"] == 1 and met["rimborsi_netti_cents"] > 0),
        ("commissione di pagamento trattenuta (14 ordini)", met["fee_pagamento_cents"] > 13 * 80),
    ])

    # 3. QA respinge e poi approva
    _sim("qa_respinge", runs_dir, "qa_respinge")
    st = _stato(runs_dir, "qa_respinge")
    dec = [d["decisione"] for d in _decisioni(runs_dir, "qa_respinge")]
    caso("qa_respinge", "QA blocca il primo prodotto, il secondo passa", [
        ("QA bloccato una volta con motivazione", dec.count("qa_bloccato") == 1),
        ("ritorno a Prodotto registrato", "ritorno_a_prodotto" in dec),
        ("due tentativi di Prodotto e di QA", st["tentativi"].get("prodotto") == 2 and st["tentativi"].get("qa") == 2),
        ("Shopify eseguita solo dopo l'approvazione QA",
         dec.index("qa_bloccato") < [i for i, d in enumerate(_decisioni(runs_dir, "qa_respinge")) if d["fase"] == "shopify"][0]),
        ("run completato", st["stato"] == "completato"),
    ])

    # 4. QA respinge definitivamente
    _sim("qa_respinge_definitivo", runs_dir, "qa_def")
    st = _stato(runs_dir, "qa_def")
    caso("qa_respinge_definitivo", "QA respinge entrambi i tentativi: test fermato", [
        ("stato fermato", st["stato"] == "fermato"),
        ("Shopify mai eseguita", "shopify" not in st["fasi_completate"] and not _art(runs_dir, "qa_def", "shopify")),
        ("costo del test fallito registrato", st.get("costo_test_fallito_cents", 0) > 0),
        ("nessuna spesa di acquisizione", _speso(_ledger(runs_dir, "qa_def")) == st.get("costo_test_fallito_cents")),
    ])

    # 5. Shopify senza accesso → titolare → ripresa
    _sim("shopify_senza_accesso", runs_dir, "shopify")
    st1 = _stato(runs_dir, "shopify")
    led1 = _ledger(runs_dir, "shopify")
    speso_piattaforma_1 = sum(sum(d["importo_cents"] for d in x["consumi"].values() if not d.get("stornato"))
                              for x in led1["buste"].values() if x["categoria"] == "piattaforma")
    p2 = _cli(["resume", "--run-id", "shopify"], runs_dir)  # senza concessione: deve restare fermo
    st2 = _stato(runs_dir, "shopify")
    p3 = _cli(["resume", "--run-id", "shopify", "--concedi", "shopify"], runs_dir)
    st3 = _stato(runs_dir, "shopify")
    pacchetto = open(os.path.join(runs_dir, "shopify", "AZIONI_TITOLARE.md"), encoding="utf-8").read()
    caso("shopify_senza_accesso", "accesso al negozio mancante", [
        ("blocco in attesa del titolare alla fase Shopify", st1["stato"] == "bloccato_titolare" and st1["fase_corrente"] == "shopify"),
        ("azione nel pacchetto unico del titolare", "shopify-accesso" in pacchetto),
        ("nessun consumo di piattaforma prima dell'accesso (solo prenotazione)",
         speso_piattaforma_1 == 0),
        ("ripresa senza concessione resta ferma", st2["stato"] == "bloccato_titolare"),
        ("dopo la concessione riprende da Shopify e completa", st3["stato"] == "completato" and p3.returncode == 0),
        ("fasi precedenti non rieseguite", st3["tentativi"]["strategia"] == 1 and st3["tentativi"]["qa"] == 1),
    ])

    # 6. Spesa oltre il tetto / costo sconosciuto / oltre allocazione
    _sim("spesa_oltre_tetto", runs_dir, "spesa")
    led = _ledger(runs_dir, "spesa")
    motivi = [b["motivo"] for b in led["bloccati"]]
    caso("spesa_oltre_tetto", "richieste di spesa extra", [
        ("bloccata la spesa oltre il residuo", "residuo insufficiente" in motivi),
        ("bloccato il costo massimo sconosciuto", "costo massimo sconosciuto o non valido" in motivi),
        ("bloccata la spesa oltre l'allocazione di categoria", "allocazione della categoria superata" in motivi),
        ("nessuna busta creata per le richieste bloccate",
         not any(k.endswith(("ads-aumento", "app-recensioni", "ads-seconda-campagna")) for k in led["buste"])),
        ("spesa ≤ tetto", _speso(led) + _impegnato(led) <= led["tetto_cents"]),
        ("test completato nei limiti", _stato(runs_dir, "spesa")["stato"] == "completato"),
    ])
    _sim("canale_primario_senza_budget", runs_dir, "primario")
    st = _stato(runs_dir, "primario")
    led = _ledger(runs_dir, "primario")
    caso("canale_primario_senza_budget", "budget del canale primario oltre il residuo", [
        ("blocco alla Selezione", st["stato"] == "bloccato" and st["fase_corrente"] == "selezione"),
        ("nessuna spesa di acquisizione", not any(b["categoria"] in ("ads", "commissione", "compenso_fisso")
                                                  for b in led["buste"].values())),
    ])

    # 7. Interruzione e ripresa
    p1 = _sim("interruzione", runs_dir, "interruzione")
    st1 = _stato(runs_dir, "interruzione")
    p2 = _cli(["resume", "--run-id", "interruzione"], runs_dir)
    st2 = _stato(runs_dir, "interruzione")
    li, lc = _ledger(runs_dir, "interruzione"), _ledger(runs_dir, "completo")
    mi = _art(runs_dir, "interruzione", "misurazione")["metriche"]
    mc = _art(runs_dir, "completo", "misurazione")["metriche"]
    caso("interruzione", "processo terminato a metà Distribuzione, poi ripreso", [
        ("processo uscito con codice di interruzione", p1.returncode == EXIT_INTERROTTO),
        ("stato salvato a metà fase Distribuzione", st1["in_esecuzione"] and st1["in_esecuzione"]["fase"] == "distribuzione"),
        ("ripresa dalla fase Distribuzione (fasi precedenti non rieseguite)",
         st2["riprese"] == 1 and all(v == 1 for v in st2["tentativi"].values())),
        ("run completato", st2["stato"] == "completato" and p2.returncode == 0),
        ("stessa spesa del run senza interruzione", _speso(li) == _speso(lc)),
        ("stesse metriche del run senza interruzione", mi == mc),
        ("nessun ordine doppio", mi["ordini"] == 14),
    ])

    # 8. Modalità live: ogni azione esterna bloccata
    p = _sim("completo", runs_dir, "live", "--modalita", "live")
    st = _stato(runs_dir, "live")
    calls = read_jsonl(os.path.join(runs_dir, "live", "external_calls.jsonl"))
    caso("azioni_esterne_bloccate", "modalità live senza integrazioni collegate", [
        ("run bloccato alla prima azione esterna", st["stato"] == "bloccato" and st["fase_corrente"] == "strategia"),
        ("nessuna spesa consumata", _speso(_ledger(runs_dir, "live")) == 0),
        ("tentativo registrato come bloccato", calls and all(c["esito"] == "bloccato" for c in calls)),
    ])

    # 9. Registro condiviso: due test sullo stesso tetto di 500 €
    reg = os.path.join(runs_dir, "registro-condiviso.json")
    _sim("completo", runs_dir, "cond-1", "--registro", reg)
    _sim("completo", runs_dir, "cond-2", "--registro", reg)
    _sim("completo", runs_dir, "cond-3", "--registro", reg)
    led = read_json(reg)
    stati = [_stato(runs_dir, f"cond-{i}")["stato"] for i in (1, 2, 3)]
    caso("tetto_condiviso", "tre test consecutivi sullo stesso registro da 500 €", [
        ("primo test completato", stati[0] == "completato"),
        ("un test successivo bloccato per residuo o allocazione", "bloccato" in stati[1:]),
        ("i test non finanziabili si fermano alla Selezione, prima di spendere",
         all(_stato(runs_dir, f"cond-{i}")["fase_corrente"] == "selezione" for i, s in zip((1, 2, 3), stati) if s == "bloccato")),
        ("spesa complessiva ≤ 500 €", _speso(led) + _impegnato(led) <= 50000),
        ("un test bloccato non lascia canali attivi né impegni aperti",
         not any(b["stato"] == "aperta" and b["id"].startswith(f"cond-{i}/")
                 for i, s in zip((1, 2, 3), stati) if s == "bloccato" for b in led["buste"].values())
         and not any(c["servizio"] in ("ads", "creator") and c["azione"] in ("crea_campagna", "attiva_partner")
                     for i, s in zip((1, 2, 3), stati) if s == "bloccato"
                     for c in read_jsonl(os.path.join(runs_dir, f"cond-{i}", "external_calls.jsonl")))),
    ])

    # Report
    passati = sum(r["ok"] for r in risultati)
    righe = [f"# Report di collaudo — {datetime.now().isoformat(timespec='seconds')}", "",
             "Tutti i dati sono **sintetici**; tutti i servizi esterni sono **simulati** o **bloccati**.", "",
             f"**Esito: {passati}/{len(risultati)} casi superati**", "", "| Caso | Esito | Descrizione |", "|---|---|---|"]
    for r in risultati:
        righe.append(f"| {r['caso']} | {'PASS' if r['ok'] else 'FAIL'} | {r['descrizione']} |")
    for r in risultati:
        righe += ["", f"## {r['caso']} — {'PASS' if r['ok'] else 'FAIL'}"]
        righe += [f"- [{'x' if v['ok'] else ' '}] {v['verifica']}" for v in r["verifiche"]]
    with open(os.path.join(runs_dir, "REPORT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(righe) + "\n")
    with open(os.path.join(runs_dir, "report.json"), "w", encoding="utf-8") as f:
        json.dump(risultati, f, ensure_ascii=False, indent=2)
    for r in risultati:
        print(f"{'PASS' if r['ok'] else 'FAIL'}  {r['caso']:<30} {r['descrizione']}")
        for v in r["verifiche"]:
            if not v["ok"]:
                print(f"      ✗ {v['verifica']}")
    print(f"\n{passati}/{len(risultati)} casi superati. Report: {os.path.join(runs_dir, 'REPORT.md')}")
    return 0 if passati == len(risultati) else 1
