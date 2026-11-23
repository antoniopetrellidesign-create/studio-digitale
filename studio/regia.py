"""Regia mobile: istantanea dello stato reale del sistema e comandi del titolare.

Fonti dell'istantanea (solo dati registrati, niente inventato):
  - ruoli: .claude/agents/*.md (definizione ≠ processo attivo)
  - esecuzioni: team/eventi/*.jsonl (hook di Claude Code: SubagentStart/Stop, Pre/PostToolUse, Stop)
  - lavori e passaggi: team/queue.json; decisioni: DECISIONI.md; consegne: file del repository
  - numeri: registro comune del primo test (registro/primo-test.json, se esiste) — le simulazioni NON entrano
  - prodotti: research/*.json; integrazioni: config/account_catalogo.json + config/integrazioni_collaudate.json
  - collegamento: battito del ponte (runs/regia/battito.json)

Comandi (idempotenti per id, registro append-only team/comandi.jsonl):
  obiettivo, priorita, revisione, sospendi, riprendi, risposta.
Responsabile: team-lead.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re
from datetime import datetime, timedelta, timezone

from .storage import append_jsonl, atomic_write_json, read_json, read_jsonl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPARTI = {
    "team-lead": "Direzione", "ricerca-mercato": "Ricerca", "sviluppo-prodotto": "Sviluppo",
    "qa-indipendente": "Qualità", "shopify-operazioni": "Vendite multicanale", "acquisizione": "Acquisizione",
    "creator-partnership": "Acquisizione", "social-contenuti": "Social", "customer-care": "Assistenza",
    "strategia-finanza": "Finanza", "account-integrazioni": "Integrazioni",
}
ATTIVA_MAX = timedelta(minutes=20)      # oltre: un'esecuzione senza fine diventa "sconosciuta"
BATTITO_MAX = timedelta(minutes=10)     # oltre: il ponte è "non aggiornato"
TIPI_COMANDO = ("obiettivo", "priorita", "revisione", "sospendi", "riprendi", "risposta")
PRIORITA = ("alta", "normale", "bassa")


def _p(*a):
    if a and a[0] == "team" and os.environ.get("STUDIO_TEAM_DIR"):  # test: cartella team separata
        return os.path.join(os.environ["STUDIO_TEAM_DIR"], *a[1:])
    return os.path.join(ROOT, *a)


def _leggi(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def _ora():
    return datetime.now(timezone.utc)


def _iso(d=None):
    return (d or _ora()).isoformat(timespec="seconds")


def _parse(s):
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


# ----------------------------------------------------------------------------- sospensione
def percorso_sospensione():
    return os.environ.get("STUDIO_SOSPENSIONE") or _p("team", "sospensione.json")


def sospensione() -> dict:
    s = read_json(percorso_sospensione(), None)
    return s if isinstance(s, dict) else {"spese": False, "attivita": False}


# ----------------------------------------------------------------------------- eventi e agenti
def eventi(limite_giorni: int = 14) -> list:
    out = []
    for f in sorted(glob.glob(_p("team", "eventi", "*.jsonl")))[-limite_giorni:]:
        for riga in _leggi(f).splitlines():  # QA R-8: una riga troncata non fa cadere l'istantanea
            try:
                e = json.loads(riga)
                if isinstance(e, dict) and "evento" in e and "quando" in e and _parse(e["quando"]):
                    out.append(e)
            except ValueError:
                continue
    return out


def _ruoli() -> list:
    ruoli = []
    for f in sorted(glob.glob(_p(".claude", "agents", "*.md"))):
        testo = _leggi(f)
        nome = re.search(r"^name:\s*(\S+)", testo, re.M)
        desc = re.search(r"^description:\s*(.+)$", testo, re.M)
        mand = re.search(r"## Mandato\n(.+?)\n\n", testo, re.S)
        if nome:
            n = nome.group(1)
            ruoli.append({"id": n, "reparto": REPARTI.get(n, "Altro"),
                          "ruolo": (desc.group(1).split(".")[0] if desc else n),
                          "mandato": (mand.group(1).strip() if mand else ""), "file": os.path.relpath(f, ROOT)})
    return ruoli


def _decisioni_per(ruolo: str, n=3) -> list:
    out = []
    for riga in _leggi(_p("DECISIONI.md")).splitlines():
        if riga.startswith("| D-"):
            c = [x.strip() for x in riga.strip().strip("|").split("|")]
            if len(c) >= 6 and ruolo in c[4]:
                out.append({"id": c[0], "data": c[1], "decisione": c[2][:220], "motivazione": c[3][:220], "stato": c[5]})
    return out[-n:]


def stato_agenti(evs: list, battito_fresco: bool, ora=None) -> list:
    ora = ora or _ora()
    coda = read_json(_p("team", "queue.json"), {"compiti": []})["compiti"]
    esecuzioni = {}
    for e in evs:
        aid = e.get("agente_id")
        if e["evento"] == "SubagentStart" and aid:
            esecuzioni[aid] = {"agente_id": aid, "tipo": e.get("agente_tipo"), "inizio": e["quando"], "fine": None,
                               "attivita": [], "file": set(), "strumenti": {}, "ultimo": e["quando"], "esito": None}
        elif aid and aid in esecuzioni:
            x = esecuzioni[aid]
            x["ultimo"] = e["quando"]
            if e["evento"] == "PreToolUse":
                x["attivita"].append({"quando": e["quando"], "strumento": e.get("strumento"), "sintesi": e.get("sintesi")})
                x["strumenti"][e.get("strumento")] = x["strumenti"].get(e.get("strumento"), 0) + 1
                if e.get("strumento") in ("Write", "Edit") and e.get("file"):
                    x["file"].add(e["file"])
            elif e["evento"] == "SubagentStop":
                x["fine"] = e["quando"]
                x["esito"] = e.get("ultimo_messaggio")
    principale = [e for e in evs if not e.get("agente_id") and e["evento"] == "PreToolUse"]
    strumenti_principale = {}
    for e in principale:
        strumenti_principale[e.get("strumento")] = strumenti_principale.get(e.get("strumento"), 0) + 1
    out = []
    for r in _ruoli():
        runs = sorted([x for x in esecuzioni.values() if x["tipo"] == r["id"]], key=lambda x: x["inizio"])
        compiti = [t for t in coda if t["agente"] == r["id"]]
        in_corso_coda = [t for t in compiti if t["stato"] == "in_corso"]
        bloccati = [t for t in compiti if t["stato"] == "bloccato"]
        attesa = [t for t in compiti if t["stato"] == "da_fare"]
        aperte = [x for x in runs if not x["fine"]]  # QA R-6: un'esecuzione aperta non è nascosta da una parallela conclusa
        ultima = (sorted(aperte, key=lambda x: x["ultimo"])[-1] if aperte else (runs[-1] if runs else None))
        if r["id"] == "team-lead":  # la sessione principale agisce da team-lead
            ultima_att = principale[-1] if principale else None
            vivo = battito_fresco and ultima_att and ora - _parse(ultima_att["quando"]) < ATTIVA_MAX
            recente = ultima_att and ora - _parse(ultima_att["quando"]) < ATTIVA_MAX
            if vivo:
                stato, motivo = "in_esecuzione", "sessione principale attiva (ultimo strumento registrato)"
            elif recente and not battito_fresco:  # QA R-7
                stato, motivo = "sconosciuto", "attività recente ma ponte non aggiornato: stato reale non noto"
            else:
                stato = "bloccato" if bloccati else "in_attesa" if attesa else "inattivo"
                motivo = "nessuna attività recente della sessione principale"
            attivita = ([{"quando": a["quando"], "strumento": a.get("strumento"), "sintesi": a.get("sintesi")}
                         for a in principale[-6:]])
            esec = {"avviate": None, "concluse": None, "nota": "sessione principale, non un subagente"}
        else:
            if ultima and not ultima["fine"]:
                fresca = ora - _parse(ultima["ultimo"]) < ATTIVA_MAX
                stato = "in_esecuzione" if (fresca and battito_fresco) else "sconosciuto"
                motivo = ("avviato e senza evento di fine; eventi recenti" if stato == "in_esecuzione"
                          else "avviato senza evento di fine e senza eventi recenti: collegamento perso o processo interrotto")
            elif bloccati:
                stato, motivo = "bloccato", bloccati[-1]["note"][-1]["nota"] if bloccati[-1]["note"] else "compito bloccato"
            elif attesa or in_corso_coda:
                stato, motivo = "in_attesa", "compito in coda, nessuna esecuzione attiva registrata"
            elif ultima:
                stato, motivo = "concluso", "ultima esecuzione terminata (evento di fine registrato)"
            else:
                stato, motivo = "mai_avviato_registrato", "ruolo definito; nessuna esecuzione registrata dagli hook"
            attivita = ultima["attivita"][-6:] if ultima else []
            esec = {"avviate": len(runs), "concluse": sum(1 for x in runs if x["fine"]),
                    "nota": "esecuzioni registrate dagli hook dal 2026-11-23 sera; quelle precedenti risultano solo dalla coda"}
        strumenti = dict(strumenti_principale) if r["id"] == "team-lead" else {}
        for x in runs:
            for k, v in x["strumenti"].items():
                strumenti[k] = strumenti.get(k, 0) + v
        compito = (in_corso_coda or attesa or bloccati or compiti[-1:] or [None])[-1] if compiti else None
        out.append({
            **r, "stato": stato, "motivo_stato": motivo,
            "ultimo_aggiornamento": (ultima["ultimo"] if ultima and r["id"] != "team-lead"
                                     else (attivita[-1]["quando"] if attivita else None)),
            "incarico": (compito["titolo"] if compito else None), "compito_id": (compito["id"] if compito else None),
            "progetto": "studio-digitale (sistema)" if not compito or not compito.get("run_id") else compito["run_id"],
            "attivita_corrente": (attivita[-1]["sintesi"] if attivita and stato == "in_esecuzione" else None),
            "attivita_recente": attivita, "strumenti": strumenti, "esecuzioni": esec,
            "file_prodotti": sorted({f for x in runs for f in x["file"]} | {o for t in compiti for o in t.get("output", [])
                                                                             if isinstance(o, str)})[:20],
            "ultimo_esito": (ultima["esito"] if ultima else None),
            "decisioni": _decisioni_per(r["id"]),
            "costi": {"verificati_eur": 0.0, "nota": "nessuna spesa registrata nel registro comune; costo AI della sessione non misurabile da qui (stima non disponibile)"},
            "blocchi": [{"compito": t["id"], "titolo": t["titolo"], "nota": (t["note"][-1]["nota"] if t["note"] else "")} for t in bloccati],
            "dipendenze": sorted({d for t in compiti for d in t.get("dipende_da", [])}),
        })
    return out


def passaggi(coda: list) -> list:
    """Passaggi fra reparti: SOLO dipendenze registrate nella coda fra compiti di agenti diversi."""
    per_id = {t["id"]: t for t in coda}
    out = []
    for t in coda:
        for d in t.get("dipende_da", []):
            s = per_id.get(d)
            if s and s["agente"] != t["agente"] and s["stato"] == "fatto":
                out.append({"da": s["agente"], "a": t["agente"], "compito_origine": d, "compito_destinazione": t["id"],
                            "quando": s["aggiornato"], "stato_destinazione": t["stato"]})
    return out


# ----------------------------------------------------------------------------- numeri, prodotti, integrazioni
def numeri() -> dict:
    from .ledger import Ledger
    from .workflow import carica_json
    pol = carica_json("config/policy.json")
    reg = _p("registro", "primo-test.json")
    base = {"fonte": "registro comune del primo test", "simulazioni_escluse": True}
    if not os.path.exists(reg):
        return {**base, "esiste": False, "tetto_cents": pol["tetto_primo_test_cents"], "consumato_cents": 0,
                "impegnato_cents": 0, "residuo_cents": pol["tetto_primo_test_cents"], "incassi_cents": 0,
                "margini_per_canale": None, "per_categoria": {c: {"consumato_cents": 0, "allocazione_cents": a}
                                                             for c, a in pol["allocazione_budget_cents"].items()},
                "nota": "nessuna spesa né incasso reale: il registro comune non è ancora stato aperto"}
    led = Ledger(reg, pol["tetto_primo_test_cents"], pol["allocazione_budget_cents"], pol["categorie_spesa"])
    r = led.riepilogo()
    return {**base, "esiste": True, "tetto_cents": r["tetto_cents"], "consumato_cents": r["consumato_cents"],
            "impegnato_cents": r["impegnato_aperto_cents"], "residuo_cents": r["residuo_cents"], "incassi_cents": 0,
            "margini_per_canale": None, "per_categoria": r["per_categoria"]}


def prodotti() -> list:
    from .phases import fonti_osservate, punteggio
    out = []
    for f in sorted(glob.glob(_p("research", "[AB]-*.json"))):
        try:
            o = json.loads(_leggi(f))
            out.append({"id": o["id"], "titolo": o.get("titolo"), "mercato": o.get("mercato"), "lingua": o.get("lingua"),
                        "punteggio": punteggio(o), "fonti_osservate": fonti_osservate(o),
                        "fase": "ricerca", "esito": "sotto soglia (60)" if punteggio(o) < 60 else "idonea",
                        "pipeline": {"ricerca": "fatto", "sviluppo": "non avviato", "qa": "non avviato",
                                     "pubblicazione": "non avviato", "risultati": "nessuno"},
                        "file": os.path.relpath(f, ROOT)})
        except Exception:
            continue
    return sorted(out, key=lambda x: -x["punteggio"])


def integrazioni() -> list:
    from .workflow import carica_json
    coll = set(carica_json("config/integrazioni_collaudate.json")["collaudate"])
    voci = [("shopify", "Shopify", "negozio, ordini, consegna"), ("marketplace", "Marketplace", "Etsy/Gumroad/Payhip (catalogo)"),
            ("creator", "Creator", "codici e commissioni"), ("ads", "Ads", "campagne a pagamento"),
            ("social", "Social", "account dei prodotti validati"), ("assistenza", "Customer care", "casella dedicata e ticket")]
    return [{"id": i, "nome": n, "funzione": f, "collegato": i in coll,
             "stato": "collegato" if i in coll else "da collegare", "dati_disponibili": i in coll,
             "campagne_attive": 0 if i == "ads" else None} for i, n, f in voci]


def richieste_titolare() -> list:
    t = _leggi(_p("AZIONI_TITOLARE.md"))
    out = []
    for m in re.finditer(r"\*\*(R\d+) — (.+?)\*\*", t):
        out.append({"id": m.group(1), "titolo": m.group(2), "fonte": "AZIONI_TITOLARE.md"})
    risposte = {r["richiesta"]: r for r in read_jsonl(_p("team", "risposte_titolare.jsonl"))}
    for r in out:
        if r["id"] in risposte:
            r["risposta"] = risposte[r["id"]]["testo"][:300]
            r["risposto_il"] = risposte[r["id"]]["quando"]
    return out


CONSEGNE = ["research/GRADUATORIA-2026-11-23.md", "AZIONI_TITOLARE.md", "STRATEGIA.md", "WORKFLOW.md",
            "RIPRISTINO.md", "qa/2026-11-23-credenziali-ricerca.md", "research/A-sintesi.md", "research/B-sintesi.md"]


def consegne() -> list:
    out = []
    files = CONSEGNE + sorted(os.path.relpath(f, ROOT) for f in glob.glob(_p("team", "consegne", "*.md")))
    for rel in files:
        p = _p(rel)
        if os.path.exists(p):
            testo = _leggi(p)
            out.append({"id": re.sub(r"[^A-Za-z0-9_-]", "-", rel)[:120], "file": rel,
                        "aggiornato": datetime.fromtimestamp(os.path.getmtime(p), timezone.utc).isoformat(timespec="seconds"),
                        "byte": len(testo.encode()), "impronta": hashlib.sha256(testo.encode()).hexdigest()[:12],
                        "contenuto": testo[:200_000]})
    return out


# ----------------------------------------------------------------------------- istantanea
def battito(nota: str = "") -> dict:
    b = {"quando": _iso(), "ponte": "sessione Claude Code (temporanea)", "ambiente": "studio-digitale",
         "sessione": (os.environ.get("CLAUDE_CODE_SESSION_ID") or "")[:8], "nota": nota}
    atomic_write_json(_p("runs", "regia", "battito.json"), b)
    return b


def collegamento(ora=None) -> dict:
    ora = ora or _ora()
    b = read_json(_p("runs", "regia", "battito.json"), None)
    fresco = bool(b) and ora - _parse(b["quando"]) < BATTITO_MAX
    return {"battito": b, "fresco": fresco, "persistente": False,
            "esecuzione_motore": "dentro una sessione Claude Code nel cloud (container temporaneo)",
            "a_telefono_chiuso": "il motore continua solo finché questa sessione è attiva",
            "a_fine_sessione": "il motore si ferma: nessun repository dedicato né attività pianificata attiva",
            "per_continuita": "R1 (repository dedicato) + attività pianificata che riapre il ponte a intervalli",
            "soglia_minuti": int(BATTITO_MAX.total_seconds() // 60)}


def istantanea(ora=None) -> dict:
    ora = ora or _ora()
    col = collegamento(ora)
    evs = eventi()
    coda = read_json(_p("team", "queue.json"), {"compiti": []})["compiti"]
    agenti = stato_agenti(evs, col["fresco"], ora)
    sosp = sospensione()
    num = numeri()
    conteggi = {}
    for a in agenti:
        conteggi[a["stato"]] = conteggi.get(a["stato"], 0) + 1
    lavori = [{**{k: t.get(k) for k in ("id", "titolo", "agente", "stato", "dipende_da", "creato", "aggiornato")},
               "priorita": t.get("priorita", "normale"), "scadenza": t.get("scadenza"),
               "nota": (t["note"][-1]["nota"] if t.get("note") else ""), "reparto": REPARTI.get(t["agente"], "Altro")}
              for t in coda]
    return {
        "generato_il": _iso(ora), "collegamento": col,
        "sospensione": {**sosp, "campagne_esterne_attive": 0, "impegni_gia_assunti_cents": num["impegnato_cents"],
                        "arresti_non_confermati": 0,
                        "nota": "nessuna integrazione esterna collegata: nessuna campagna reale da fermare"},
        "riepilogo": {"agenti_definiti": len(agenti), "per_stato": conteggi,
                      "lavori_aperti": sum(1 for t in coda if t["stato"] != "fatto"),
                      "lavori_bloccati": sum(1 for t in coda if t["stato"] == "bloccato"),
                      "prodotti_in_ricerca": len(prodotti()), "prodotti_selezionati": 0},
        "agenti": agenti, "lavori": lavori, "passaggi": passaggi(coda), "prodotti": prodotti(), "numeri": num,
        "integrazioni": integrazioni(), "richieste": richieste_titolare(),
        "eventi_recenti": [e for e in evs if e["evento"] in ("SubagentStart", "SubagentStop", "Stop")][-30:],
    }


def documenti_db(s: dict) -> dict:
    """Documenti da scrivere nel database dell'app: {collezione/doc_id: corpo}."""
    sistema = {k: s[k] for k in ("generato_il", "collegamento", "sospensione", "riepilogo", "passaggi", "numeri",
                                 "integrazioni", "richieste", "eventi_recenti")}
    return {"sistema/stato": sistema, "squadra/agenti": {"generato_il": s["generato_il"], "agenti": s["agenti"]},
            "squadra/lavori": {"generato_il": s["generato_il"], "lavori": s["lavori"]},
            "squadra/prodotti": {"generato_il": s["generato_il"], "prodotti": s["prodotti"]}}


def esporta(cartella: str, con_consegne: bool = False) -> list:
    s = istantanea()
    scritti = []
    docs = documenti_db(s)
    if con_consegne:
        cs = consegne()
        docs["consegne/indice"] = {"generato_il": s["generato_il"],
                                   "voci": [{k: c[k] for k in ("id", "file", "aggiornato", "byte", "impronta")} for c in cs]}
        for c in cs:
            docs[f"testi/{c['id']}"] = c
    for path, corpo in docs.items():
        f = os.path.join(cartella, path + ".json")
        atomic_write_json(f, corpo)
        scritti.append({"collection": path.split("/")[0], "doc_id": path.split("/")[1], "file_path": f})
    return scritti


# ----------------------------------------------------------------------------- comandi
def _registro_comandi():
    return {c["id"]: c for c in read_jsonl(_p("team", "comandi.jsonl"))}


def esegui_comando(cmd: dict) -> dict:
    """Esegue un comando una sola volta per id. Ritorna lo stato confermato dal motore."""
    from .queue import TaskQueue
    cid = str(cmd.get("id", ""))
    if not re.fullmatch(r"[A-Za-z0-9_-]{6,80}", cid):
        return {"id": cid, "stato": "fallito", "esito": "id del comando non valido", "quando": _iso()}
    gia = _registro_comandi().get(cid)
    if gia:
        return {**gia, "duplicato": True}
    tipo, par = cmd.get("tipo"), cmd.get("parametri") or {}
    q = TaskQueue(_p("team", "queue.json"))
    try:
        if tipo not in TIPI_COMANDO:
            raise ValueError(f"tipo di comando sconosciuto: {tipo}")
        if tipo == "obiettivo":
            testo = str(par.get("testo", "")).strip()[:500]
            if not testo:
                raise ValueError("obiettivo vuoto")
            tid = "OB-" + cid  # QA C-1: id completo, nessuna collisione fra comandi ravvicinati
            origine = "Obiettivo di collaudo: " if "collaudo" in str(cmd.get("origine", "")) else "Obiettivo del titolare: "
            t = q.add(tid, origine + testo, "team-lead")
            t["priorita"] = par.get("priorita", "normale") if par.get("priorita") in PRIORITA else "normale"
            q._save()
            esito = f"obiettivo registrato come compito {tid} per il team-lead (priorità {t['priorita']})"
        elif tipo == "priorita":
            t = q.get(str(par.get("compito")))
            if t is None or par.get("priorita") not in PRIORITA:
                raise ValueError("compito inesistente o priorità non valida")
            t["priorita"] = par["priorita"]
            t["aggiornato"] = _iso()
            q._save()
            esito = f"priorità di {t['id']} impostata a {par['priorita']}"
        elif tipo == "revisione":
            ogg = str(par.get("oggetto", "")).strip()[:300]
            if not ogg:
                raise ValueError("oggetto della revisione mancante")
            tid = "RV-" + cid
            q.add(tid, "Revisione richiesta dal titolare: " + ogg, "qa-indipendente")
            esito = f"revisione registrata come compito {tid} per il QA indipendente"
        elif tipo == "sospendi":
            precedente = read_json(percorso_sospensione(), None)
            s = sospensione()
            s.update({"spese": bool(par.get("spese", True)), "attivita": bool(par.get("attivita", True)),
                      "dal": _iso(), "comando": cid})
            atomic_write_json(percorso_sospensione(), s)
            from .ledger import Ledger
            from .workflow import carica_json
            pol = carica_json("config/policy.json")
            import tempfile
            prova = Ledger(os.path.join(tempfile.mkdtemp(), "verifica.json"), pol["tetto_primo_test_cents"],
                           pol["allocazione_budget_cents"], pol["categorie_spesa"])
            attiva = prova.sospensione_attiva()
            if s["spese"] and not attiva:  # QA C-3: nessun effetto parziale
                if precedente is None:
                    os.remove(percorso_sospensione())
                else:
                    atomic_write_json(percorso_sospensione(), precedente)
                raise RuntimeError("il motore non legge la sospensione: comando non confermato")
            esito = ("sospese " + ", ".join(k for k in ("spese", "attivita") if s[k]) +
                     "; verificato: il registro rifiuta nuove riserve")
        elif tipo == "riprendi":
            s = sospensione()
            if par.get("compito"):
                t = q.get(str(par["compito"]))
                if t is None:
                    raise ValueError("compito inesistente")
                if t["stato"] != "bloccato":  # QA C-2
                    raise ValueError(f"il compito {t['id']} è '{t['stato']}': si riprende solo un compito bloccato")
                if s.get("attivita"):
                    raise ValueError("nuove attività sospese: riprendi prima le attività")
                if not q.pronto(t["id"]):
                    raise ValueError(f"dipendenze non completate: {t['dipende_da']}")
                q.set_stato(t["id"], "da_fare", "ripreso dal titolare")
                esito = f"compito {t['id']} riportato in coda"
            else:
                s.update({"spese": False if par.get("spese", True) else s.get("spese", False),
                          "attivita": False if par.get("attivita", True) else s.get("attivita", False),
                          "ripreso_il": _iso(), "comando": cid})
                atomic_write_json(percorso_sospensione(), s)
                esito = "ripresi: " + ", ".join(k for k in ("spese", "attivita") if not s[k])
        else:  # risposta
            rid = str(par.get("richiesta", ""))
            if rid not in {r["id"] for r in richieste_titolare()}:
                raise ValueError("richiesta del titolare inesistente")
            append_jsonl(_p("team", "risposte_titolare.jsonl"),
                         {"richiesta": rid, "testo": str(par.get("testo", ""))[:1000], "quando": _iso(), "comando": cid})
            esito = f"risposta a {rid} registrata per il team-lead"
        rec = {"id": cid, "tipo": tipo, "stato": "completato", "esito": esito, "quando": _iso()}
    except Exception as e:
        rec = {"id": cid, "tipo": tipo, "stato": "fallito", "esito": str(e)[:300], "quando": _iso()}
    append_jsonl(_p("team", "comandi.jsonl"), rec)
    return rec
