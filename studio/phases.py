"""Fasi del workflow: responsabile, output obbligatori, gestore e controllo di sblocco.

Strategia → Ricerca → Selezione → Prodotto → QA → Shopify → Ordine di prova e download
→ Distribuzione → Misurazione → Decisione

Ogni gestore riceve il Run (workflow.Run) e ritorna un dict di output.
Ogni controllo ritorna (ok: bool, motivi: list[str]).
"""
from __future__ import annotations

import hashlib
import json
import os
import re

from . import attribution, economics
from .adapters.mock import ShopifyAccessMissing
from .ledger import SpendBlocked
from .money import pct_bp, scorporo_iva


class NeedOwner(Exception):
    """La fase richiede un'azione riservata al titolare (account, pagamenti, identità)."""

    def __init__(self, azione_id: str, descrizione: str, concessione: str):
        super().__init__(descrizione)
        self.azione_id, self.descrizione, self.concessione = azione_id, descrizione, concessione


class PhaseStop(Exception):
    """La fase decide di fermare il test (es. nessuna opportunità valida)."""


class SimulatedCrash(Exception):
    """Interruzione simulata della sessione."""


CAMPI_OPPORTUNITA = ["id", "titolo", "sintetico", "lingua", "mercato", "acquirente", "problema", "fonti",
                     "concorrenti", "prezzo_da_verificare_cents", "accesso_pubblico", "costo_sviluppo_cents",
                     "complessita_assistenza", "ipotesi_margine_bp", "punteggi"]
PESI = {"problema": 25, "accesso": 20, "margine": 20, "concorrenza": 15, "costo_sviluppo": 10, "assistenza": 10}
CAMPI_PIANO = ["domanda", "offerta", "canale_primario", "soglia_stop_cents", "criterio_successo"]
IVA_BP = {"IT": 2200, "DE": 1900, "FR": 2000, "ES": 2100, "NL": 2100, "AT": 2000}
SEGRETI = re.compile(r"(shpat_[0-9a-f]{8,}|sk_live_\w+|\b(?:\d[ -]?){15,16}\b|otp\s*[:=]\s*\d{4,8}|password\s*[:=])",
                     re.IGNORECASE)


# ----------------------------------------------------------------------------- helper
def punteggio(opp: dict) -> int:
    p = opp["punteggi"]
    return sum(PESI[k] * max(0, min(10, int(p.get(k, 0)))) for k in PESI) // 10


def fonti_osservate(opp: dict) -> int:
    return sum(1 for f in opp.get("fonti", []) if f.get("tipo") == "osservata" and f.get("url") and f.get("data"))


def valida_opportunita(opp: dict) -> list:
    errori = [f"campo mancante: {c}" for c in CAMPI_OPPORTUNITA if c not in opp or opp[c] in (None, "", [])]
    for i, f in enumerate(opp.get("fonti", [])):
        if f.get("tipo") not in ("osservata", "ipotesi"):
            errori.append(f"fonte {i}: tipo deve essere 'osservata' o 'ipotesi'")
        elif f["tipo"] == "osservata" and not (f.get("url") and f.get("data")):
            errori.append(f"fonte {i}: osservata senza url o data")
    return errori


def sha(testo: str) -> str:
    return hashlib.sha256(testo.encode()).hexdigest()


# ----------------------------------------------------------------------------- gestori
def h_strategia(run):
    pol = run.policy
    return {
        "obiettivo_lungo_periodo": pol["obiettivo_lungo_periodo"],
        "tetto_cents": pol["tetto_primo_test_cents"],
        "allocazione_cents": pol["allocazione_budget_cents"],
        "regole_decisione": pol["regole_decisione"],
        "domanda_portafoglio": run.scenario.get("domanda_portafoglio",
                                                "Quale opportunità offre margine positivo entro il tetto?"),
    }


def g_strategia(run, out):
    m = []
    if out["tetto_cents"] != run.ledger.tetto:
        m.append("tetto della strategia diverso dal tetto del registro")
    if sum(out["allocazione_cents"].values()) > out["tetto_cents"]:
        m.append("allocazione oltre il tetto")
    return not m, m


def h_ricerca(run):
    valide, scartate = [], []
    for opp in run.scenario["opportunita"]:
        err = valida_opportunita(opp)
        (scartate if err else valide).append(opp if not err else {"id": opp.get("id"), "errori": err})
    return {"opportunita": valide, "scartate": scartate, "metodo": "docs/metodo-ricerca.md"}


def g_ricerca(run, out):
    m = []
    if not out["opportunita"]:
        m.append("nessuna opportunità con scheda completa")
    if run.modalita == "simulato" and any(not o.get("sintetico") for o in out["opportunita"]):
        m.append("in simulazione tutte le opportunità devono essere marcate sintetiche")
    return not m, m


def h_selezione(run):
    sel = run.policy["selezione"]
    classifica = []
    for o in run.artifact("ricerca")["opportunita"]:
        classifica.append({"id": o["id"], "punteggio": punteggio(o), "fonti_osservate": fonti_osservate(o),
                           "idonea": punteggio(o) >= sel["punteggio_minimo"]
                           and fonti_osservate(o) >= sel["fonti_osservate_minime"]})
    classifica.sort(key=lambda c: -c["punteggio"])
    idonee = [c for c in classifica if c["idonea"]]
    if not idonee:
        raise PhaseStop("nessuna opportunità supera soglia di punteggio e fonti osservate")
    scelta = idonee[0]["id"]
    piano = dict(run.scenario["piano_test"])
    piano["opportunita_id"] = scelta
    budget = sum(c.get("budget_max_cents", 0) + c.get("compenso_fisso_cents", 0) + c.get("tetto_commissioni_cents", 0)
                 for c in piano["canali"]) + sum(p["max_cents"] or 0 for p in run.scenario.get("costi_piattaforma", []))
    piano["budget_massimo_cents"] = budget
    per_cat = {}
    for c in piano["canali"]:
        for campo, cat in (("budget_max_cents", "ads"), ("compenso_fisso_cents", "compenso_fisso"),
                           ("tetto_commissioni_cents", "commissione")):
            if c.get(campo):
                per_cat[cat] = per_cat.get(cat, 0) + c[campo]
    for pc in run.scenario.get("costi_piattaforma", []):
        per_cat["piattaforma"] = per_cat.get("piattaforma", 0) + (pc["max_cents"] or 0)
    piano["budget_per_categoria_cents"] = per_cat
    return {"classifica": classifica, "selezionata": scelta, "piano_test": piano,
            "approvazione": "team-lead (automatica in simulazione, registrata)"}


def g_selezione(run, out):
    p = out["piano_test"]
    m = [f"piano di test senza '{c}'" for c in CAMPI_PIANO if not p.get(c)]
    if p["canale_primario"] not in [c["canale"] for c in p["canali"]]:
        m.append("canale primario non presente tra i canali del piano")
    if any(pc["max_cents"] is None for pc in run.scenario.get("costi_piattaforma", [])):
        m.append("costo massimo di piattaforma sconosciuto")
    alloc = run.ledger.data["allocazione_cents"]
    for cat, imp in p["budget_per_categoria_cents"].items():
        if cat in alloc and run.ledger.usato_categoria(cat) + imp > alloc[cat]:
            m.append(f"budget '{cat}' del piano ({imp}) oltre la disponibilità della categoria "
                     f"({alloc[cat] - run.ledger.usato_categoria(cat)})")
    if p["budget_massimo_cents"] > run.ledger.residuo():
        m.append(f"budget massimo del piano {p['budget_massimo_cents']} oltre il residuo {run.ledger.residuo()}")
    return not m, m


def h_prodotto(run):
    cfg = run.scenario["prodotto"]
    opp_id = run.artifact("selezione")["selezionata"]
    tent = run.state["tentativi"].get("prodotto", 1)
    difettoso = tent <= run.guasti.get("qa_respinge_tentativi", 0)
    files = []
    for f in cfg["files"]:
        files.append({"nome": f["nome"], "formato": f["formato"],
                      "sha256": sha(f"{opp_id}/{f['nome']}/v{tent}"), "copre_promesse": f["copre_promesse"]})
    licenza = cfg["licenza"]
    if difettoso:  # difetto iniettato: manca il file che copre l'ultima promessa e la licenza
        files = files[:-1]
        licenza = ""
    manifest = {"id": f"PRD-{opp_id}", "versione": f"0.{tent}", "lingua": cfg["lingua"], "licenza": licenza,
                "files": files, "promesse": cfg["promesse"], "sintetico": True}
    return {"manifest": manifest, "spec": f"products/{opp_id}/spec.md (simulata)", "prezzo_cents": cfg["prezzo_cents"]}


def g_prodotto(run, out):
    m = [f"manifest senza '{k}'" for k in ("id", "versione", "lingua", "files", "promesse") if k not in out["manifest"]]
    return not m, m


def h_qa(run):
    man = run.artifact("prodotto")["manifest"]
    sel = run.artifact("selezione")
    opp = next(o for o in run.artifact("ricerca")["opportunita"] if o["id"] == sel["selezionata"])
    coperte = {p for f in man["files"] for p in f["copre_promesse"]}
    controlli = [
        ("Q1 ogni promessa coperta da un file", set(man["promesse"]) <= coperte,
         f"promesse scoperte: {sorted(set(man['promesse']) - coperte)}"),
        ("Q2 checksum sha256 presenti", all(re.fullmatch(r"[0-9a-f]{64}", f["sha256"]) for f in man["files"]) and bool(man["files"]),
         "checksum mancanti o non validi"),
        ("Q3 licenza documentata", bool(man.get("licenza")), "licenza assente nel manifest"),
        ("Q4 almeno 2 fonti osservate", fonti_osservate(opp) >= run.policy["selezione"]["fonti_osservate_minime"],
         "fonti osservate insufficienti"),
        ("Q5 registro entro il tetto", run.ledger.residuo() >= 0 and run.ledger.consumato() <= run.ledger.tetto,
         "registro oltre il tetto"),
        ("Q6 nessun segreto nei file del run", not run.scan_segreti(), f"possibili segreti: {run.scan_segreti()}"),
        ("Q7 nessuna azione esterna reale", run.azioni_esterne_reali() == 0, "azioni esterne non simulate"),
        ("Q8 piano di test completo", all(sel["piano_test"].get(c) for c in CAMPI_PIANO), "piano incompleto"),
    ]
    esiti = [{"controllo": n, "ok": ok, "prova": "ok" if ok else motivo} for n, ok, motivo in controlli]
    return {"verdetto": "APPROVATO" if all(e["ok"] for e in esiti) else "BLOCCATO", "controlli": esiti,
            "verificatore": "qa-indipendente"}


def g_qa(run, out):
    m = [e["controllo"] + ": " + e["prova"] for e in out["controlli"] if not e["ok"]]
    return out["verdetto"] == "APPROVATO", m


def h_shopify(run):
    shop = run.adapters["shopify"]
    try:
        shop.verifica_accesso()
    except ShopifyAccessMissing:
        raise NeedOwner("shopify-accesso",
                        "Autorizzare l'app del negozio Shopify con scope minimi (vedi docs/operazioni-shopify.md); "
                        "token nel gestore segreti dell'ambiente, mai in file o chat.", "shopify")
    for c in run.scenario.get("costi_piattaforma", []):
        run.ledger.spend_once(run.bid(f"piattaforma-{c['id']}"), "piattaforma", c["max_cents"], c["effettivo_cents"],
                              c["descrizione"], fase="shopify", tag=["piattaforma"])
    prod = run.artifact("prodotto")
    scheda = shop.crea_prodotto_bozza(prod["manifest"], prod["prezzo_cents"], [prod["manifest"]["lingua"]])
    return {"scheda": scheda, "stato_scheda": scheda["stato"],
            "eventi_tracciamento": ["view_item", "add_to_cart", "begin_checkout", "purchase", "refund"]}


def g_shopify(run, out):
    m = []
    if out["stato_scheda"] != "bozza":
        m.append("la scheda non deve essere pubblicata in collaudo")
    if not out["scheda"]["consegna"].get("scadenza_ore"):
        m.append("link di download senza scadenza")
    return not m, m


def h_ordine_prova(run):
    prod = run.artifact("prodotto")
    sch = run.artifact("shopify")["scheda"]
    ordine = run.adapters["pagamenti"].ordine_di_prova(sch["product_id"], prod["prezzo_cents"])
    nuovo = run.orders.ingest(ordine)
    duplicato = run.orders.ingest(ordine)  # il webhook arriva due volte: deve essere scartato
    link = run.adapters["consegna"].invia_link(ordine["order_id"], prod["manifest"])
    dl = run.adapters["consegna"].scarica(link, prod["manifest"])
    return {"order_id": ordine["order_id"], "download_ok": dl["ok"], "link_scadenza_ore": link["scadenza_ore"],
            "duplicato_scartato": not duplicato,
            "riconciliato": (nuovo or run.orders.get(ordine["order_id"]) is not None)
            and len([o for o in run.orders.ordini(includi_test=True) if o.get("test")]) == 1}


def g_ordine_prova(run, out):
    m = [k for k in ("download_ok", "duplicato_scartato", "riconciliato") if not out[k]]
    return not m, [f"controllo fallito: {k}" for k in m]


def h_distribuzione(run):
    piano = run.artifact("selezione")["piano_test"]
    led, comm_cfg = run.ledger, run.commissioni
    attivi, bloccate = {}, []
    # Il canale primario si attiva per primo: se non è finanziabile non si attiva nient'altro.
    canali = sorted(piano["canali"], key=lambda c: c["canale"] != piano["canale_primario"])
    for c in canali:
        n_buste = set(led.data["buste"])
        try:
            if c["canale"] == "creator":
                fisso = run.bid(f"creator-{c['id']}-fisso")
                if c.get("compenso_fisso_cents"):
                    led.reserve(fisso, "compenso_fisso", c["compenso_fisso_cents"], f"compenso fisso {c['id']}",
                                fase="distribuzione", tag=["canale:creator"])
                env = run.bid(f"creator-{c['id']}-commissioni")
                led.reserve(env, "commissione", c["tetto_commissioni_cents"], f"tetto commissioni {c['id']}",
                            fase="distribuzione", tag=["canale:creator"])
                run.adapters["creator"].attiva_partner(c["id"], c["codice"],
                                                       busta_fisso=fisso if c.get("compenso_fisso_cents") else None)
                if c.get("compenso_fisso_cents"):
                    led.draw(fisso, "unico", c["compenso_fisso_cents"], "compenso fisso")
                    led.close(fisso)
                attivi["creator"] = {"id": c["id"], "busta": env, "codice": c["codice"], "attivo": True}
            elif c["canale"] == "ads":
                env = run.bid(f"ads-{c['id']}")
                led.reserve(env, "ads", c["budget_max_cents"], f"campagna {c['id']}", fase="distribuzione",
                            tag=["canale:ads"])
                run.adapters["ads"].crea_campagna(c["id"], c["budget_max_cents"], busta=env)
                attivi["ads"] = {"id": c["id"], "busta": env, "giornaliero_max_cents": c["giornaliero_max_cents"],
                                 "attivo": True}
            else:
                attivi[c["canale"]] = {"id": c["id"], "attivo": True}
        except SpendBlocked as e:
            # Attivazione atomica: libera le riserve già fatte per questo canale (nessun consumo avvenuto).
            for bid in set(led.data["buste"]) - n_buste:
                led.close(bid)
            bloccate.append({"canale": c["canale"], "motivo": e.motivo, **e.dettagli})
            run.decidi("distribuzione", "spesa_bloccata", e.motivo, canale=c["canale"])
            if c["canale"] == piano["canale_primario"]:
                raise SpendBlocked("canale primario non attivabile entro il registro", {"bloccate": bloccate})

    for r in run.scenario.get("richieste_spesa_extra", []):
        try:
            led.reserve(run.bid(r["id"]), r["categoria"], r["max_cents"], r["descrizione"], fase="distribuzione")
            bloccate.append({"id": r["id"], "motivo": "NON BLOCCATA (inatteso)"})
        except SpendBlocked as e:
            bloccate.append({"id": r["id"], "motivo": e.motivo})
            run.decidi("distribuzione", "spesa_bloccata", e.motivo, richiesta=r["id"])

    v = run.scenario["vendite"]
    # Spesa Ads giornaliera simulata: tetto giornaliero e busta riservata.
    if "ads" in attivi:
        a = attivi["ads"]
        for i, importo in enumerate(v.get("spesa_ads_giornaliera_cents", []), 1):
            if not a["attivo"]:
                break
            if importo > a["giornaliero_max_cents"]:
                run.decidi("distribuzione", "spesa_giornaliera_ridotta",
                           f"giorno {i}: {importo} oltre il massimo giornaliero", canale="ads")
                importo = a["giornaliero_max_cents"]
            try:
                led.draw(a["busta"], f"giorno-{i}", importo, f"spesa Ads simulata giorno {i}")
            except SpendBlocked as e:
                a["attivo"] = False
                run.adapters["ads"].pausa(a["id"], e.motivo)
                run.decidi("distribuzione", "campagna_in_pausa", e.motivo, canale="ads")

    prezzo = run.artifact("prodotto")["prezzo_cents"]
    nuovi = 0
    eventi = list(v["ordini"]) + [next(o for o in v["ordini"] if o["order_id"] == d) for d in v.get("duplicati", [])]
    for ev in eventi:
        tocchi = [{"canale": c.split(":")[0], "id": c.split(":")[1] if ":" in c else c} for c in ev.get("canali", [])]
        ha_creator = any(t["canale"] == "creator" for t in tocchi)
        sconto = pct_bp(prezzo, comm_cfg["sconto_codice_creator_bp"]) if ha_creator else 0
        ordine = {"order_id": ev["order_id"], "lordo_cents": prezzo, "sconto_cents": sconto,
                  "iva_bp": IVA_BP[ev.get("paese", "IT")], "paese": ev.get("paese", "IT"),
                  "giorno": ev.get("giorno", 0), "tocchi": tocchi, "sintetico": True}
        if not run.orders.ingest(ordine):
            continue
        nuovi += 1
        if ha_creator and "creator" in attivi:
            cr = attivi["creator"]
            netto = scorporo_iva(prezzo - sconto, ordine["iva_bp"])
            comm = attribution.commissione_creator(netto, comm_cfg["commissione_pct_bp_su_netto"])
            if cr["attivo"]:
                try:
                    led.draw(cr["busta"], ev["order_id"], comm, "commissione creator impegnata")
                except SpendBlocked as e:
                    cr["attivo"] = False
                    run.adapters["creator"].sospendi_codice(cr["codice"], e.motivo)
                    run.decidi("distribuzione", "codice_creator_sospeso", "tetto contrattuale commissioni raggiunto")
        if run.guasti.get("interrompi_in") == "distribuzione" and nuovi == run.guasti.get("interrompi_dopo_ordini", 1):
            run.crash_once("distribuzione")

    rimborsi = 0
    for r in v.get("rimborsi", []):
        if run.orders.rimborsa(r["order_id"], r["giorno"]):
            rimborsi += 1
        o = run.orders.get(r["order_id"])
        if "creator" in attivi and attribution.partner_creator(o) and \
                attribution.entro_clawback(o, comm_cfg["finestra_clawback_giorni"]):
            led.undraw(attivi["creator"]["busta"], r["order_id"], "rimborso entro la finestra di clawback")
    if "ads" in attivi:
        led.close(attivi["ads"]["busta"])  # libera il budget Ads non speso
    return {"canali_attivati": sorted(attivi), "spese_bloccate": bloccate, "ordini_nuovi": len(run.orders.ordini()),
            "duplicati_scartati": run.orders.data["duplicati_scartati"], "rimborsi": rimborsi,
            "canale_primario": piano["canale_primario"]}


def g_distribuzione(run, out):
    m = []
    if out["canale_primario"] not in out["canali_attivati"]:
        m.append("canale primario non attivo")
    if run.azioni_esterne_reali():
        m.append("rilevate azioni esterne non simulate")
    return not m, m


def h_misurazione(run):
    met = economics.misura(run.orders, run.ledger, run.policy, run.scenario.get("costi_test_falliti_cents", 0),
                           prefisso=run.bid(""))
    return {"metriche": met, "registro": run.ledger.riepilogo()}


def g_misurazione(run, out):
    met, m = out["metriche"], []
    if not met["controllo_doppio_conteggio_ok"]:
        m.append("ricavi contati più di una volta tra i canali")
    if out["registro"]["consumato_cents"] + out["registro"]["impegnato_aperto_cents"] > run.ledger.tetto:
        m.append("registro oltre il tetto")
    if met["ordini"] != len(run.orders.ordini()):
        m.append("ordini non riconciliati")
    return not m, m


def h_decisione(run):
    met = run.artifact("misurazione")["metriche"]
    d = economics.decidi(met, run.artifact("selezione")["piano_test"], run.policy)
    if d.get("richiede_titolare"):
        run.azione_titolare("budget-scala", "Approvare un nuovo tetto di spesa per scalare il test", "budget")
    # Chiusura del test: sospende i codici creator e libera gli impegni non consumati.
    # Le commissioni già maturate restano consumate (pagabili dopo la finestra di clawback).
    liberato = 0
    for b in list(run.ledger.data["buste"].values()):
        if b["id"].startswith(run.bid("")) and b["stato"] == "aperta" and any(t.startswith("canale:") for t in b["tag"]):
            liberato += run.ledger.close(b["id"])
    for c in run.artifact("selezione")["piano_test"]["canali"]:
        if c["canale"] == "creator":
            run.adapters["creator"].sospendi_codice(c["codice"], "fine test")
    run.decidi("decisione", "chiusura_test", f"buste di canale chiuse, liberati {liberato} cent", attore="team-lead")
    return {"esito": d["esito"], "motivi": d["motivi"], "margine_contribuzione_cents": met["margine_contribuzione_cents"],
            "roas_su_margine_x100": met["roas_su_margine_x100"]}


def g_decisione(run, out):
    return out["esito"] in ("stop", "ripeti", "scala"), []


FASI = [
    ("strategia", "strategia-finanza", ["obiettivo_lungo_periodo", "tetto_cents", "allocazione_cents", "regole_decisione"], h_strategia, g_strategia),
    ("ricerca", "ricerca-mercato", ["opportunita", "scartate"], h_ricerca, g_ricerca),
    ("selezione", "team-lead", ["selezionata", "piano_test", "classifica"], h_selezione, g_selezione),
    ("prodotto", "sviluppo-prodotto", ["manifest", "spec", "prezzo_cents"], h_prodotto, g_prodotto),
    ("qa", "qa-indipendente", ["verdetto", "controlli"], h_qa, g_qa),
    ("shopify", "shopify-operazioni", ["scheda", "stato_scheda", "eventi_tracciamento"], h_shopify, g_shopify),
    ("ordine_prova", "shopify-operazioni", ["order_id", "download_ok", "duplicato_scartato", "riconciliato"], h_ordine_prova, g_ordine_prova),
    ("distribuzione", "acquisizione", ["canali_attivati", "spese_bloccate", "ordini_nuovi"], h_distribuzione, g_distribuzione),
    ("misurazione", "strategia-finanza", ["metriche", "registro"], h_misurazione, g_misurazione),
    ("decisione", "team-lead", ["esito", "motivi"], h_decisione, g_decisione),
]
NOMI_FASI = [f[0] for f in FASI]
