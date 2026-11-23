import json
import os
import subprocess
import tempfile
import unittest

from studio.vault import Vault, VaultNonConfigurato, genera_password


class TestVault(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        # chiave di PROVA generata solo per il test (simula la chiave del titolare)
        self.key = os.path.join(self.d, "titolare.key")
        subprocess.run(["age-keygen", "-o", self.key], check=True, capture_output=True)
        pub = [l.split(": ")[1] for l in open(self.key) if l.startswith("# public key")][0]
        self.dest = os.path.join(self.d, "dest.txt")
        open(self.dest, "w").write("# commento\n" + pub + "\n")
        self.v = Vault(os.path.join(self.d, "accessi"), self.dest)

    def test_password_crittografiche_uniche(self):
        ps = {genera_password() for _ in range(200)}
        self.assertEqual(len(ps), 200)
        self.assertTrue(all(len(p) == 28 for p in ps))

    def test_registro_non_segreto_senza_password_e_token(self):
        self.v.aggiorna_registro({"servizio": "shopify", "funzione": "negozio", "url": "https://x.myshopify.com",
                                  "email": "operativo@esempio.example", "username": "operativo", "titolare": "titolare",
                                  "stato": "attivo", "costo": "0", "rinnovo": "n/d",
                                  "riferimento_credenziale": "rete://x.myshopify.com/X-Shopify-Access-Token"})
        self.v.aggiorna_registro({"servizio": "console", "riferimento_credenziale": "segreto://console/password"})
        for nome in ("registro.json", "REGISTRO.md"):
            t = open(os.path.join(self.d, "accessi", nome), encoding="utf-8").read().lower()
            self.assertIn("operativo@esempio.example", t)
            self.assertNotRegex(t, r"tok_prefisso|password\"\s*:|token\"\s*:")
        for vietato in ({"password": "x"}, {"token": "x"}):
            with self.assertRaises(ValueError):
                self.v.aggiorna_registro({"servizio": "s", **vietato})
        with self.assertRaises(ValueError):
            self.v.aggiorna_registro({"servizio": "s", "riferimento_credenziale": "valore-nudo"})

    def test_senza_destinatari_rifiuta(self):
        v = Vault(os.path.join(self.d, "x"), os.path.join(self.d, "vuoto.txt"))
        with self.assertRaises(VaultNonConfigurato):
            v.registra("svc", "creazione", {"password": "x"})

    def test_nessun_segreto_in_chiaro_e_recupero_del_titolare(self):
        pw = genera_password()
        r = self.v.registra("shopify", "creazione", {"funzione": "negozio", "url_accesso": "https://admin.shopify.com",
                                                     "email": "operativo@esempio.example", "password": pw,
                                                     "piano": "base", "stato_verifica": "in attesa"})
        self.assertIn("segreto://shopify/password", r["riferimenti"])
        for radice, _, files in os.walk(os.path.join(self.d, "accessi")):
            for f in files:
                testo = open(os.path.join(radice, f), encoding="utf-8", errors="ignore").read()
                self.assertNotIn(pw, testo)
                self.assertNotIn("operativo@esempio.example", testo)
        indice = open(os.path.join(self.d, "accessi", "INDICE.md")).read()
        self.assertIn("segreto://shopify/password", indice)
        self.v.registra("shopify", "verifica", {"stato_verifica": "verificato"})
        doc = self.v.esporta(self.key)  # solo con la chiave privata del titolare
        self.assertEqual(doc["shopify"]["password"], pw)
        self.assertEqual(doc["shopify"]["stato_verifica"], "verificato")

    def test_senza_chiave_privata_non_si_decifra(self):
        self.v.registra("svc", "creazione", {"password": genera_password()})
        altra = os.path.join(self.d, "altra.key")
        subprocess.run(["age-keygen", "-o", altra], check=True, capture_output=True)
        with self.assertRaises(subprocess.CalledProcessError):
            self.v.esporta(altra)

    def test_registro_rifiuta_valori_simili_a_segreti(self):
        tok = "shp" + "at_" + "0123456789abcdef" * 2
        for voce in ({"riferimento_credenziale": "segreto://shopify/" + tok},
                     {"riferimento_credenziale": "rete://x.myshopify.com/" + tok},
                     {"riferimento_credenziale": "segreto://shopify/Valore!Esposto1"},
                     {"url": "https://u:Pw-123456@admin.example"},
                     {"funzione": "token " + tok}):
            with self.assertRaises(ValueError):
                self.v.aggiorna_registro({"servizio": "s", **voce})
        self.v.aggiorna_registro({"servizio": "s", "riferimento_credenziale": "segreto://shopify/token_admin"})

    def test_registro_controlla_ricorsivamente_liste_e_dizionari(self):
        tok = "shp" + "at_" + "0123456789abcdef" * 2
        for voce in ({"funzione": ["ok", "token " + tok]},
                     {"funzione": ("ok", ["x", {"a": "https://u:Pw-123456@h.example"}])},
                     {"costo": {"interno": {"n": "segreto://shopify/Valore!Esposto1"}}},
                     {"costo": {tok: "ok"}},
                     {"rinnovo": [{"k": [tok]}]}):
            with self.assertRaises(ValueError):
                self.v.aggiorna_registro({"servizio": "s", **voce})
        self.v.aggiorna_registro({"servizio": "s", "costo": {"mese": ["10", "EUR"]}})


if __name__ == "__main__":
    unittest.main()
