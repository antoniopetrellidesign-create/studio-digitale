"""Adattatori simulati: comportamento deterministico, nessuna rete, nessun costo reale."""
import hashlib

from .base import ExternalActionBlocked


class ShopifyAccessMissing(ExternalActionBlocked):
    pass


class _Base:
    servizio = "?"

    def __init__(self, gate):
        self.gate = gate

    def _rec(self, azione, **kw):
        return self.gate.record(self.servizio, azione, **kw)


class MockShopify(_Base):
    servizio = "shopify"
    SCOPE_RICHIESTI = ["read_products", "write_products", "read_orders", "read_discounts", "write_discounts",
                       "read_files", "write_files"]  # D-012: nessun read_customers

    def __init__(self, gate, accesso=True):
        super().__init__(gate)
        self.accesso = accesso

    def verifica_accesso(self):
        self._rec("verifica_accesso", accesso=self.accesso)
        if not self.accesso:
            raise ShopifyAccessMissing("accesso al negozio Shopify non autorizzato")
        return {"negozio": "negozio-simulato.myshopify.example", "scope": self.SCOPE_RICHIESTI}

    def crea_prodotto_bozza(self, manifest, prezzo_cents, lingue):
        if not self.accesso:
            raise ShopifyAccessMissing("accesso al negozio Shopify non autorizzato")
        pid = "gid://sim/Product/" + hashlib.sha256(manifest["id"].encode()).hexdigest()[:10]
        self._rec("crea_prodotto_bozza", product_id=pid, stato="bozza", prezzo_cents=prezzo_cents)
        return {"product_id": pid, "stato": "bozza", "prezzo_cents": prezzo_cents, "lingue": lingue,
                "checkout": {"iva": "OSS UE, prezzo IVA inclusa", "consenso_esecuzione_immediata": True},
                "consegna": {"tipo": "link_firmato", "scadenza_ore": 72, "max_download": 5}}


class MockPagamenti(_Base):
    servizio = "pagamenti"

    def ordine_di_prova(self, product_id, prezzo_cents):
        oid = "TEST-" + hashlib.sha256(product_id.encode()).hexdigest()[:8]
        self._rec("ordine_di_prova", order_id=oid, modalita_test=True, sconto_pct=100)
        return {"order_id": oid, "lordo_cents": prezzo_cents, "sconto_cents": prezzo_cents,
                "iva_bp": 2200, "test": True, "tocchi": [], "paese": "IT"}


class MockConsegna(_Base):
    servizio = "consegna"

    def invia_link(self, order_id, manifest):
        token = hashlib.sha256((order_id + manifest["id"]).encode()).hexdigest()[:16]
        self._rec("invia_link", order_id=order_id)  # nessun dato personale nel log
        return {"order_id": order_id, "token": "sim-" + token, "scadenza_ore": 72, "max_download": 5,
                "files": [{"nome": f["nome"], "sha256": f["sha256"]} for f in manifest["files"]]}

    def scarica(self, link, manifest):
        attesi = {f["nome"]: f["sha256"] for f in manifest["files"]}
        ricevuti = {f["nome"]: f["sha256"] for f in link["files"]}
        self._rec("scarica", order_id=link["order_id"])
        return {"ok": attesi == ricevuti and bool(attesi), "files": len(ricevuti)}


class MockAds(_Base):
    servizio = "ads"

    def crea_campagna(self, campagna_id, budget_max_cents, busta):
        self._rec("crea_campagna", a_pagamento=True, busta=busta, campagna=campagna_id,
                  budget_max_cents=budget_max_cents, stato="simulata")
        return {"campagna_id": campagna_id, "stato": "simulata"}

    def pausa(self, campagna_id, motivo):
        self._rec("pausa", campagna=campagna_id, motivo=motivo)


class MockCreator(_Base):
    servizio = "creator"

    def attiva_partner(self, partner_id, codice, busta_fisso=None):
        self._rec("attiva_partner", a_pagamento=busta_fisso is not None, busta=busta_fisso,
                  partner=partner_id, codice=codice, contatto_reale=False)
        return {"partner": partner_id, "codice": codice, "stato": "simulato"}

    def sospendi_codice(self, codice, motivo):
        self._rec("sospendi_codice", codice=codice, motivo=motivo)


class MockAI(_Base):
    servizio = "ai"

    def esegui(self, fase, busta, costo_cents):
        self._rec("esegui", a_pagamento=True, busta=busta, fase=fase, costo_simulato_cents=costo_cents)
        return costo_cents
