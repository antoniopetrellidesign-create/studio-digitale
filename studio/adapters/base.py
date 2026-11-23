"""Cancello unico per le azioni esterne: ogni adattatore passa da qui."""
import os
from datetime import datetime, timezone

from ..storage import append_jsonl


class ExternalActionBlocked(Exception):
    pass


class ExternalGate:
    """Registra ogni azione esterna e blocca quelle reali.

    Un'azione reale richiederebbe TUTTE queste condizioni (nessuna è soddisfatta in collaudo):
      - modalità "live"
      - variabile d'ambiente STUDIO_LIVE=1 impostata dal titolare
      - integrazione dichiarata "collaudata dal vivo" in INTEGRAZIONI_LIVE.md
    In questa versione gli adattatori live non sono implementati: il blocco è incondizionato.
    """

    def __init__(self, mode: str, log_path: str, collaudate: set | None = None):
        self.mode = mode
        self.log_path = log_path
        # integrazioni dichiarate collaudate dal vivo (config/integrazioni_collaudate.json): oggi nessuna
        self.collaudate = set(collaudate or ())

    def live_consentito(self, servizio: str) -> bool:
        return (self.mode == "live" and os.environ.get("STUDIO_LIVE") == "1" and servizio in self.collaudate)

    def record(self, servizio: str, azione: str, a_pagamento: bool = False, busta: str | None = None, **dati):
        if a_pagamento and not busta:
            raise ExternalActionBlocked(f"{servizio}.{azione}: azione a pagamento senza riserva nel registro")
        rec = {"quando": datetime.now(timezone.utc).isoformat(timespec="seconds"), "modalita": self.mode,
               "servizio": servizio, "azione": azione, "a_pagamento": a_pagamento, "busta": busta,
               "esito": ("simulato" if self.mode == "simulato" else
                         "reale" if self.live_consentito(servizio) else "bloccato"), **dati}
        append_jsonl(self.log_path, rec)
        if rec["esito"] == "bloccato":
            raise ExternalActionBlocked(
                f"{servizio}.{azione}: azione esterna reale bloccata (modalità {self.mode}, "
                f"STUDIO_LIVE={os.environ.get('STUDIO_LIVE', '0')}). Vedi INTEGRAZIONI_LIVE.md.")
        return rec
