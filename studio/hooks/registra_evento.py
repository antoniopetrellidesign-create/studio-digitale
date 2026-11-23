"""Hook di Claude Code → registro eventi della regia (team/eventi/AAAA-MM-GG.jsonl).

Legge il JSON dell'hook da stdin e scrive UNA riga con dati oscurati:
  - niente input completi degli strumenti: per Bash solo la descrizione, per WebFetch solo l'host,
    per i file solo il percorso relativo al progetto;
  - ogni testo passa dal filtro dei segreti (studio.phases.SEGRETI) ed è troncato.
Non blocca mai: qualsiasi errore → uscita 0 senza output.
Responsabile: team-lead.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse

RADICE = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEG = re.compile(r"(shp(?:at|ss|ca)_[0-9a-f]{8,}|[sr]k_(?:live|test)_\w+|ghp_[A-Za-z0-9]{20,}|github_p[a]t_\w+|AKIA[0-9A-Z]{16}"
                 r"|xox[bpas]-[\w-]+|-----BEGIN [A-Z ]*PRIVATE KEY|bearer\s+[A-Za-z0-9._~+/-]{16,}|AGE-SECRET-KEY-1\w+"
                 r"|\b(?:\d[ -]?){15,16}\b|[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z.]{2,}|password\s*[:=]\s*\S+)", re.I)


URL = re.compile(r"\b([a-z][a-z0-9+.-]*://)([^/\s?#@]*@)?([^/\s?#]+)([^\s?#]*)(\?[^\s#]*)?(#\S*)?", re.I)
CREDENZIALI = re.compile(
    r"(?:(--?(?:password|passwd|pass|pwd|token|secret|api[-_]?key|apikey|key|auth|otp|pin)\b)[ =]+\S+)"
    r"|(?:\b(password|passwd|pwd|token|secret|api[-_]?key|apikey|access[-_]?token|client[-_]?secret|otp|pin)\b"
    r"\s*(?:[:=]|è|e'|is|vale|=>)\s*\S+)"
    r"|(?:\bsk-[A-Za-z0-9_-]{8,})"
    r"|(?:\b(?:pass|pwd)\b\s*[:=]\s*\S+)"                                         # pass: X, PWD=X
    r"|(?:\b(?:pwd|passphrase|passcode)\b\s+\S+)"                                  # PWD X, passphrase X
    r"|(?:\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){2,7}(?: ?[A-Z0-9]{1,4})?\b)"                  # IBAN
    r"|(?:\b(?:basic|bearer|digest|token)\s+[A-Za-z0-9._~+/=-]{6,})"                  # Authorization: Basic …, Bearer corto
    r"|(?:\beyJ[A-Za-z0-9_-]{4,}\.[A-Za-z0-9_-]{4,}(?:\.[A-Za-z0-9_-]*)?)"            # JWT
    r"|(?:\b[A-Za-z0-9_\-]{32,}\b)", re.I)
# URL senza schema con parametri (www.x.y/percorso?…) e segmenti di percorso lunghi tipo chiave (webhook)
SENZA_SCHEMA = re.compile(r"\b((?:[a-z0-9-]+\.)+[a-z]{2,}(?:/[^\s?#]*)?)\?[^\s#]*", re.I)
IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]){11,30}\b")
SEGMENTO = re.compile(r"/[A-Za-z0-9_-]{16,}(?=/|\b)")


def _url_sicuro(m):
    # solo schema + host + percorso: via credenziali (user:pass@), parametri e frammento
    percorso = SEGMENTO.sub("/[oscurato]", m.group(4) or "")
    if m.group(3).lower().startswith("hooks."):  # webhook: l'intero percorso è il segreto
        percorso = "/[oscurato]" if percorso else ""
    return m.group(1) + m.group(3) + percorso + ("?[parametri oscurati]" if m.group(5) else "")


def pulisci(t, n=160):
    if not isinstance(t, str):
        return None
    t = t.replace("\n", " ").replace("\r", " ")
    t = IBAN.sub("[oscurato]", t)  # prima del filtro carte, che altrimenti lascerebbe visibile l'inizio
    t = URL.sub(_url_sicuro, t)
    t = SENZA_SCHEMA.sub(lambda m: m.group(1) + "?[parametri oscurati]", t)
    t = SEG.sub("[oscurato]", t)
    t = CREDENZIALI.sub("[oscurato]", t)
    return t[:n] + ("…" if len(t) > n else "")


def nome_strumento(t):
    """Nomi di strumenti (anche MCP, lunghi): conservati se hanno la forma di un nome e non somigliano a un segreto noto."""
    if isinstance(t, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_.:-]{0,79}", t) and not SEG.search(t) \
            and not re.search(r"(?:sk-|ghp_|AKIA|xox)", t):
        return t
    return pulisci(t, 60)


def relativo(p):
    if not isinstance(p, str):
        return None
    try:
        r = os.path.relpath(p, RADICE)
    except ValueError:
        return None
    return None if r.startswith("..") else pulisci(r, 200)


def sintesi(nome, inp):
    inp = inp if isinstance(inp, dict) else {}
    if nome == "Bash":
        return pulisci(inp.get("description") or "comando di shell"), None
    if nome in ("Read", "Write", "Edit", "NotebookEdit"):
        return nome, relativo(inp.get("file_path"))
    if nome in ("Glob", "Grep"):
        return pulisci(f"{nome} {inp.get('pattern', '')}", 80), relativo(inp.get("path"))
    if nome == "WebFetch":
        return "lettura pagina " + (urlparse(inp.get("url", "")).hostname or "?"), None
    if nome == "WebSearch":
        return pulisci("ricerca: " + str(inp.get("query", "")), 120), None
    if nome == "Agent":
        return pulisci(f"avvio agente {inp.get('subagent_type', '')}: {inp.get('description', '')}"), None
    return nome_strumento(nome), None  # strumento sconosciuto: anche il nome passa dal filtro


def main():
    try:
        d = json.load(sys.stdin)
        ev = d.get("hook_event_name", "?")
        rec = {"quando": datetime.now(timezone.utc).isoformat(timespec="seconds"), "evento": pulisci(ev, 40),
               "sessione": pulisci((d.get("session_id") or "")[:8], 8), "agente_id": pulisci(d.get("agent_id"), 40),
               "agente_tipo": pulisci(d.get("agent_type"), 60)}
        if ev in ("PreToolUse", "PostToolUse", "PostToolUseFailure"):
            rec["strumento"] = nome_strumento(d.get("tool_name"))
            rec["sintesi"], rec["file"] = sintesi(d.get("tool_name"), d.get("tool_input"))
            if ev != "PreToolUse":
                rec["esito"] = "errore" if ev == "PostToolUseFailure" else "ok"
                rec["durata_ms"] = d.get("duration_ms") if isinstance(d.get("duration_ms"), (int, float)) else None
        elif ev in ("SubagentStop", "Stop"):
            rec["ultimo_messaggio"] = pulisci(d.get("last_assistant_message"), 300)
        elif ev == "Notification":
            rec["sintesi"] = pulisci(d.get("message"), 200)
            rec["tipo"] = pulisci(d.get("notification_type"), 40)
        elif ev == "SessionStart":
            rec["origine"] = pulisci(d.get("source"), 30)
        rec = {k: v for k, v in rec.items() if v is not None}
        cartella = os.path.join(RADICE, "team", "eventi")
        os.makedirs(cartella, exist_ok=True)
        with open(os.path.join(cartella, datetime.now(timezone.utc).strftime("%Y-%m-%d") + ".jsonl"), "a",
                  encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
