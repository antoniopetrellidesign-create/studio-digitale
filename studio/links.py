"""Collegamenti tracciati (UTM) verso i canali di vendita."""
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

OBBLIGATORI = ("utm_source", "utm_medium", "utm_campaign", "utm_content")


def link_tracciato(base_url: str, sorgente: str, mezzo: str, campagna: str, contenuto: str) -> str:
    u = urlparse(base_url)
    q = parse_qs(u.query)
    q.update({"utm_source": [sorgente], "utm_medium": [mezzo], "utm_campaign": [campagna], "utm_content": [contenuto]})
    return urlunparse(u._replace(query=urlencode({k: v[0] for k, v in q.items()})))


def tracciato(url: str) -> bool:
    q = parse_qs(urlparse(url).query)
    return all(q.get(k) and q[k][0] for k in OBBLIGATORI)
