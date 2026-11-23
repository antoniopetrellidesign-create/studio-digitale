"""Registro account: chi, quando e a quale costo un servizio esterno può essere attivato.

Stati: pianificato → in_attesa_titolare → attivo → revocato   (oppure bloccato con motivo)
Regole di attivazione (tutte obbligatorie):
  1. la fase che richiede il servizio è raggiunta (nessun account "per sicurezza" in anticipo)
  2. le dipendenze sono attive
  3. prezzo verificato (fonte + data) o servizio a consumo coperto dalle buste del registro
  4. prova gratuita: scadenza e condizioni registrate
  5. impegno massimo (canone × mesi del test) riservato nel registro spese (categoria piattaforma)
Nessun segreto qui: credenziali solo in ACCESSI_SISTEMA (studio/vault.py).
Responsabile: account-integrazioni.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .ledger import SpendBlocked
from .phases import NOMI_FASI
from .storage import atomic_write_json, read_json

MESI_TEST_DEFAULT = 1


class AttivazioneRifiutata(Exception):
    def __init__(self, servizio, motivi):
        super().__init__(f"{servizio}: " + "; ".join(motivi))
        self.servizio, self.motivi = servizio, motivi


def _oggi():
    return datetime.now(timezone.utc).date().isoformat()


class AccountRegistry:
    def __init__(self, catalogo: dict, stato_path: str):
        self.catalogo = {s["id"]: s for s in catalogo["servizi"]}
        self.path = stato_path
        self.stato = read_json(stato_path, {"account": {}})

    def _save(self):
        atomic_write_json(self.path, self.stato)

    def stato_di(self, sid: str) -> str:
        return self.stato["account"].get(sid, {}).get("stato", "pianificato")

    def verifica(self, sid: str, fase_raggiunta: str) -> list:
        s = self.catalogo.get(sid)
        if s is None:
            return [f"servizio '{sid}' non presente nel catalogo"]
        motivi = []
        if NOMI_FASI.index(fase_raggiunta) < NOMI_FASI.index(s["fase_richiesta"]):
            motivi.append(f"fase '{s['fase_richiesta']}' non ancora raggiunta (fase attuale '{fase_raggiunta}')")
        for d in s["dipende_da"]:
            if self.stato_di(d) != "attivo":
                motivi.append(f"dipendenza '{d}' non attiva")
        p = s["prezzo"]
        f = p.get("fonte") or {}
        verificato = (p["stato"] == "verificato" and isinstance(p.get("max_mensile_cents"), int)
                      and f.get("tipo") == "osservata" and f.get("url") and f.get("data"))  # QA M-1
        if p["stato"] != "a_consumo" and not verificato:
            motivi.append("prezzo, imposte e rinnovo non verificati (servono fonte osservata con url e data)")
        pg = s.get("prova_gratuita")
        if pg and (pg.get("stato") == "da_verificare" or not pg.get("scadenza")):
            motivi.append("prova gratuita senza scadenza e condizioni registrate")
        return motivi

    def richiedi(self, sid: str, fase_raggiunta: str, ledger, prefisso_busta: str,
                 mesi: int = MESI_TEST_DEFAULT, importo_cents: int | None = None) -> dict:
        """Prepara l'attivazione: controlli + riserva. Ritorna lo stato dell'account (attivo o in attesa del titolare)."""
        if self.stato_di(sid) == "attivo":
            return self.stato["account"][sid]
        motivi = self.verifica(sid, fase_raggiunta)
        if motivi:
            raise AttivazioneRifiutata(sid, motivi)
        s = self.catalogo[sid]
        importo = importo_cents if importo_cents is not None else (s["prezzo"].get("max_mensile_cents") or 0) * mesi
        busta = None
        if importo:
            busta = f"{prefisso_busta}account-{sid}"
            ledger.reserve(busta, "piattaforma", importo, f"canone {s['nome']} × {mesi} mesi", fase=fase_raggiunta,
                           tag=["account"])  # SpendBlocked se residuo/allocazione insufficienti
        rec = {"stato": "in_attesa_titolare" if s["passaggi_titolare"] else "attivo", "busta": busta,
               "impegno_cents": importo, "richiesto": _oggi(), "ultima_verifica": None,
               "rinnovo": {"chiusura_pianificata": s.get("prova_gratuita") is not None}}
        self.stato["account"][sid] = rec
        self._save()
        return rec

    def conferma_attivo(self, sid: str, verificato_il: str | None = None):
        rec = self.stato["account"].setdefault(sid, {})
        rec["stato"] = "attivo"
        rec["ultima_verifica"] = verificato_il or _oggi()
        self._save()

    def revoca(self, sid: str, ledger=None):
        rec = self.stato["account"].get(sid)
        if rec is None:
            return
        rec["stato"] = "revocato"
        if ledger is not None and rec.get("busta"):
            ledger.close(rec["busta"])
        self._save()

    def passaggi_titolare(self, fase_raggiunta: str | None = None) -> list:
        """Elenco unico dei passaggi personali: account richiesti e in attesa + (opz.) quelli della prossima fase."""
        out = []
        for sid, s in self.catalogo.items():
            st = self.stato_di(sid)
            imminente = fase_raggiunta and NOMI_FASI.index(s["fase_richiesta"]) <= NOMI_FASI.index(fase_raggiunta) + 1
            if st == "in_attesa_titolare" or (st == "pianificato" and imminente):
                for i, p in enumerate(s["passaggi_titolare"], 1):
                    out.append({"servizio": sid, "passo": i, "azione": p, "limite": s.get("limite_automazione", "")})
        return out
