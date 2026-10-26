"""Almanca sayı biçimi (gerekçe ve kanıt metinleri için)."""


def de_int(x: float) -> str:
    return f"{round(x):,}".replace(",", ".")


def de_signed(x: float) -> str:
    return ("+" if round(x) > 0 else "") + de_int(x)


def de_pct(x: float | None, signed: bool = True) -> str:
    if x is None:
        return "n. a."
    return (f"{x:+.1f}" if signed else f"{x:.1f}").replace(".", ",") + " %"


def de_pp(x: float) -> str:
    return f"{x:+.1f}".replace(".", ",") + " Prozentpunkte"


def de_factor(x: float) -> str:
    return f"{x:.1f}".replace(".", ",")
