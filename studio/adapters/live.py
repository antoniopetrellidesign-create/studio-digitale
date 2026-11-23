"""Adattatori reali: NON collegati. Ogni metodo blocca e rimanda a INTEGRAZIONI_LIVE.md.

Quando un'integrazione verrà collegata, l'implementazione deve:
  - leggere le credenziali solo dall'ambiente/gestore segreti (mai da file del repository, mai nei log)
  - richiedere un ID busta del registro per ogni chiamata a pagamento
  - essere provata dal vivo secondo la checklist in INTEGRAZIONI_LIVE.md prima dell'uso
"""
from .base import ExternalActionBlocked


class LiveAdapter:
    def __init__(self, servizio: str, gate):
        self.servizio = servizio
        self.gate = gate

    def __getattr__(self, azione):
        if azione.startswith("_"):
            raise AttributeError(azione)

        def _blocked(*args, **kwargs):
            self.gate.record(self.servizio, azione, a_pagamento=bool(kwargs.get("busta")), busta=kwargs.get("busta"))
            raise ExternalActionBlocked(f"{self.servizio}.{azione}: integrazione live non collegata")
        return _blocked
