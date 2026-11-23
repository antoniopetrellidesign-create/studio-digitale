"""Utilità monetarie: tutti gli importi sono interi in centesimi di euro."""


def eur(cents: int | None) -> str:
    if cents is None:
        return "sconosciuto"
    segno = "-" if cents < 0 else ""
    c = abs(int(cents))
    intero = f"{c // 100:,}".replace(",", ".")
    return f"{segno}{intero},{c % 100:02d} €"


def pct_bp(importo_cents: int, bp: int) -> int:
    """Percentuale in punti base (1% = 100 bp), arrotondata al centesimo (half-up)."""
    return (importo_cents * bp + 5000) // 10000


def scorporo_iva(lordo_cents: int, iva_bp: int) -> int:
    """Imponibile da un importo IVA inclusa."""
    return (lordo_cents * 10000 + (10000 + iva_bp) // 2) // (10000 + iva_bp)
