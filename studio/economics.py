"""Unit economics, misurazione e regole di decisione stop / ripeti / scala.

Definizioni (vedi STRATEGIA.md):
  ricavi_netti      = somma imponibile (IVA scorporata, dopo sconti) degli ordini NON rimborsati
  fee_pagamento     = commissioni di pagamento su tutti gli ordini pagati (non rimborsate in caso di refund)
  acquisizione      = Ads + commissioni creator + compensi fissi
  margine_contrib.  = ricavi_netti - fee - acquisizione - piattaforma - AI - riserva usata - costi test falliti
  roas_su_margine   = (ricavi_netti - fee) / acquisizione
Responsabile: strategia-finanza (bootstrap del Team Lead).
"""
from __future__ import annotations

from . import attribution
from .orders import valori_ordine


def _costi_per_tag(ledger, tag: str, prefisso: str = "") -> int:
    tot = 0
    for b in ledger.data["buste"].values():
        if tag in b.get("tag", []) and b["id"].startswith(prefisso):
            tot += ledger._drawn(b)
    return tot


def misura(orderbook, ledger, policy: dict, costi_test_falliti_cents: int = 0, prefisso: str = "") -> dict:
    ip = policy["ipotesi_costi_variabili"]
    ordini = orderbook.ordini()
    tot = {"ordini": 0, "ordini_rimborsati": 0, "ricavi_netti_cents": 0, "rimborsi_netti_cents": 0,
           "sconti_cents": 0, "iva_cents": 0, "fee_pagamento_cents": 0, "ordini_doppia_attribuzione": 0}
    canali = {c: {"ordini_primari": 0, "ordini_assistiti": 0, "ricavi_netti_cents": 0, "fee_pagamento_cents": 0,
                  "rimborsati": 0, "sconti_cents": 0} for c in attribution.PRIORITA}
    for o in ordini:
        v = valori_ordine(o, ip)
        tot["ordini"] += 1
        tot["sconti_cents"] += v["sconto_cents"]
        tot["fee_pagamento_cents"] += v["fee_pagamento_cents"]
        cs = attribution.canali(o)
        if len(cs) > 1:
            tot["ordini_doppia_attribuzione"] += 1
        p = cs[0]
        for c in cs:
            canali[c]["ordini_assistiti"] += 1
        canali[p]["ordini_primari"] += 1
        canali[p]["fee_pagamento_cents"] += v["fee_pagamento_cents"]
        canali[p]["sconti_cents"] += v["sconto_cents"]
        if o["rimborsato"]:
            tot["ordini_rimborsati"] += 1
            tot["rimborsi_netti_cents"] += v["netto_cents"]
            canali[p]["rimborsati"] += 1
        else:
            tot["ricavi_netti_cents"] += v["netto_cents"]
            tot["iva_cents"] += v["iva_cents"]
            canali[p]["ricavi_netti_cents"] += v["netto_cents"]

    costi = {c: ledger.consumato(c, prefisso) for c in ledger.data["categorie"]}
    acquisizione = costi.get("ads", 0) + costi.get("commissione", 0) + costi.get("compenso_fisso", 0)
    margine_lordo_acq = tot["ricavi_netti_cents"] - tot["fee_pagamento_cents"]
    margine = (margine_lordo_acq - acquisizione - costi.get("piattaforma", 0) - costi.get("ai", 0)
               - costi.get("riserva", 0) - costi_test_falliti_cents)
    n = tot["ordini"]
    tot.update({
        "costi_cents": costi,
        "costi_test_falliti_cents": costi_test_falliti_cents,
        "acquisizione_cents": acquisizione,
        "margine_contribuzione_cents": margine,
        "roas_su_margine_x100": (margine_lordo_acq * 100 // acquisizione) if acquisizione else None,
        "tasso_rimborso_bp": (tot["ordini_rimborsati"] * 10000 // n) if n else 0,
    })
    # Confronto per canale: costi attribuiti tramite i tag delle buste ("canale:<nome>").
    for c, m in canali.items():
        costo = _costi_per_tag(ledger, f"canale:{c}", prefisso)
        m["costi_acquisizione_cents"] = costo
        m["margine_canale_cents"] = m["ricavi_netti_cents"] - m["fee_pagamento_cents"] - costo
        m["roas_su_margine_x100"] = ((m["ricavi_netti_cents"] - m["fee_pagamento_cents"]) * 100 // costo
                                     if costo else None)
        m["tasso_rimborso_bp"] = (m["rimborsati"] * 10000 // m["ordini_primari"]) if m["ordini_primari"] else 0
        m["sconto_medio_cents"] = (m["sconti_cents"] // m["ordini_primari"]) if m["ordini_primari"] else 0
    tot["per_canale"] = canali
    # Controllo di coerenza: la somma dei ricavi per canale primario = ricavi totali (nessun doppio conteggio).
    tot["controllo_doppio_conteggio_ok"] = (
        sum(m["ricavi_netti_cents"] for m in canali.values()) == tot["ricavi_netti_cents"])
    return tot


def decidi(m: dict, piano: dict, policy: dict) -> dict:
    r = policy["regole_decisione"]
    motivi = []
    # D-007: sotto il minimo di ordini il tasso di rimborso è rumore; decide la soglia di stop.
    if m["ordini"] < r["ordini_minimi_per_giudicare"]:
        if m["acquisizione_cents"] >= piano["soglia_stop_cents"]:
            return {"esito": "stop", "motivi": [
                f"soglia di stop raggiunta ({m['acquisizione_cents']} ≥ {piano['soglia_stop_cents']} cent) "
                f"con soli {m['ordini']} ordini"]}
        return {"esito": "ripeti", "motivi": [f"dati insufficienti ({m['ordini']} ordini), soglia di stop non raggiunta"]}
    if m["tasso_rimborso_bp"] > r["ripeti_se"]["tasso_rimborso_max_bp"]:
        return {"esito": "stop", "motivi": [f"tasso rimborso {m['tasso_rimborso_bp']/100:.1f}% oltre il limite"]}
    # D-008: senza costi di acquisizione (solo organico) il ROAS non è definito e non limita la decisione.
    roas = m["roas_su_margine_x100"] if m["roas_su_margine_x100"] is not None else 10**9
    s = r["scala_se"]
    if (m["margine_contribuzione_cents"] >= s["margine_contribuzione_cents_min"] and roas >= s["roas_su_margine_min_x100"]
            and m["tasso_rimborso_bp"] <= s["tasso_rimborso_max_bp"]):
        return {"esito": "scala", "motivi": ["margine positivo, ROAS sul margine e rimborsi entro soglia"],
                "richiede_titolare": "budget oltre il tetto del primo test"}
    if roas >= r["ripeti_se"]["roas_su_margine_min_x100"]:
        motivi.append(f"ROAS sul margine {roas/100:.2f} tra soglia di ripetizione e di scala")
        if m["margine_contribuzione_cents"] < s["margine_contribuzione_cents_min"]:
            motivi.append("margine di contribuzione non positivo")
        return {"esito": "ripeti", "motivi": motivi}
    return {"esito": "stop", "motivi": [f"ROAS sul margine {roas/100:.2f} sotto la soglia di ripetizione"]}
