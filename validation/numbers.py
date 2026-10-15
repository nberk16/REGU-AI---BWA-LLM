"""Almanca rakamların ayıklanması ve yuvarlama kuralı (a) (docs/07, Bölüm 3).

Metindeki bir rakam, karşılaştırılan değerin metinde gösterilen hassasiyete doğru yuvarlanmış
hâliyse eşleşir: 41.712 € → „42 T€“ ✓, „41,7 T€“ ✓, „41 T€“ ✗; 18,4 % → „18 %“ ✓, „19 %“ ✗.
Yuvarlama ticari kurala göredir (yarım yukarı).
"""

import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

EUR, PCT, PP, FACTOR, PLAIN, COUNT = "eur", "pct", "pp", "factor", "plain", "count"

MONTHS = "Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember"

# Rakam sayılmayan tarih ve dönem ifadeleri; ayıklamadan önce boşlukla değiştirilir.
_DATES = [
    re.compile(r"\b\d{4}-\d{2}(?:-\d{2})?\b"),          # 2025-06
    re.compile(r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b"),       # 30.06.2025
    re.compile(r"\b\d{1,2}/\d{2,4}\b"),                 # 06/2025
    re.compile(rf"\b\d{{1,2}}\.\s?(?:{MONTHS})\b"),     # 1. Juli
    re.compile(r"\bQ[1-4]\b"),                          # Q2
]

_NUMBER = re.compile(
    r"(?<![\w.,])"
    r"(?P<sign>[+\-−–]?)"
    r"(?P<int>\d{1,3}(?:\.\d{3})+|\d+)"
    r"(?:,(?P<dec>\d+))?"
    r"(?!\d)"
    r"(?P<unit>\s?(?:Mio\.?\s?(?:€|EUR)|T€|TEUR|Tsd\.?\s?(?:€|EUR)|€|EUR"
    r"|%-Punkte?n?|Prozentpunkte?n?|Pp\.?|%|Prozent|-?[Ff]ach\w*))?"
)

# Almanca olmayan ondalık biçim (ör. "19.0 %"); tarihler önceden silinir.
_NON_GERMAN = re.compile(r"(?<![\w.,])\d+\.\d{1,2}(?![\d.])")


@dataclass(frozen=True)
class Num:
    """Metinden ayıklanmış bir rakam. `value` mutlak değerdir, işaret ayrı tutulur."""

    raw: str
    sign: str        # "+", "-" veya ""
    value: Decimal
    decimals: int
    unit: str        # EUR / PCT / PP / FACTOR / PLAIN
    scale: int       # EUR için 1, 1.000 (T€) veya 1.000.000 (Mio. €)
    thousands: bool  # binlik ayırıcı var mı ("1.583")
    start: int

    @property
    def signed(self) -> float:
        return float(self.value) * self.scale * (-1 if self.sign == "-" else 1)


@dataclass(frozen=True)
class Value:
    """Karşılaştırma için izin verilen bir değer (facts.json veya bağlam notu)."""

    unit: str        # EUR / PCT / PP / FACTOR / COUNT
    value: float     # işaretli, ölçeksiz (€ cinsinden)
    origin: str
    scope: str | None = None   # ait olduğu satır veya oran (ör. "Umsatzerlöse"); None = genel (eşikler, notlar)


def _unit(unit: str | None) -> tuple[str, int]:
    if not unit:
        return PLAIN, 1
    u = unit.strip()
    if u.startswith("Mio"):
        return EUR, 1_000_000
    if u in ("T€", "TEUR") or u.startswith("Tsd"):
        return EUR, 1_000
    if u in ("€", "EUR"):
        return EUR, 1
    if u.startswith("%-Punkt") or u.startswith("Prozentpunkt") or u.startswith("Pp"):
        return PP, 1
    if u in ("%", "Prozent"):
        return PCT, 1
    return FACTOR, 1


def mask_dates(text: str) -> str:
    """Tarihleri aynı uzunlukta boşlukla değiştirir (konumlar korunur)."""
    for pattern in _DATES:
        text = pattern.sub(lambda m: " " * len(m.group()), text)
    return text


def extract(text: str) -> list[Num]:
    text = mask_dates(text)
    out = []
    for m in _NUMBER.finditer(text):
        unit, scale = _unit(m.group("unit"))
        dec = m.group("dec") or ""
        sign = {"+": "+", "-": "-", "−": "-", "–": "-"}.get(m.group("sign"), "")
        value = Decimal(m.group("int").replace(".", "") + ("." + dec if dec else ""))
        out.append(Num(m.group().strip(), sign, value, len(dec), unit, scale, "." in m.group("int"), m.start()))
    return out


def non_german(text: str) -> list[str]:
    return [m.group() for m in _NON_GERMAN.finditer(mask_dates(text))]


def is_year(num: Num) -> bool:
    return num.unit == PLAIN and num.decimals == 0 and not num.thousands and not num.sign \
        and 1990 <= num.value <= 2099


def rounds_to(value: float, num: Num) -> bool:
    """Yuvarlama kuralı (a): |value|, metindeki hassasiyete yuvarlanınca metindeki rakamı verir mi?"""
    quantum = Decimal(1).scaleb(-num.decimals)
    scaled = abs(Decimal(repr(float(value)))) / num.scale
    return scaled.quantize(quantum, rounding=ROUND_HALF_UP) == num.value


def values_from_text(text: str, origin: str, scope: str | None = None) -> list[Value]:
    """Serbest metindeki rakamlar (kanıt metinleri, bağlam notları); birimsiz rakamlar COUNT sayılır."""
    return [Value(COUNT if n.unit == PLAIN else n.unit, n.signed, origin, scope) for n in extract(text)]


_TEXT_KEYS = ("evidence", "reason")


def _fact_unit(section: str, key: str) -> str:
    if key in ("rank", "max_positions"):
        return COUNT
    if key.endswith("_pct"):
        return PCT
    if key.endswith("_pp"):
        return PP
    if key.endswith("_eur"):
        return EUR
    return PCT if section == "ratios" else EUR


def facts_values(facts: dict) -> list[Value]:
    """facts.json'daki bütün sayısal değerler, birimleri ve ait oldukları satır/oranla (docs/05)."""
    out: list[Value] = []

    def walk(node, path: list[str], scope: str | None) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, path + [k], scope)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, path + [str(i)], scope)
        elif isinstance(node, bool) or node is None:
            return
        elif isinstance(node, (int, float)):
            out.append(Value(_fact_unit(path[0], path[-1]), float(node), ".".join(path), scope))
        elif isinstance(node, str) and path[-1] in _TEXT_KEYS:
            out.extend(values_from_text(node, ".".join(path), scope))

    for section in ("summary", "positions", "further_significant", "ratios", "flags"):
        for i, entry in enumerate(facts.get(section, [])):
            walk(entry, [section, str(i)], entry.get("position") or entry.get("ratio"))
    walk(facts.get("thresholds", {}), ["thresholds"], None)
    return out


def scopes(values: list[Value]) -> set[str]:
    return {v.scope for v in values if v.scope}


# Metindeki birim → kabul edilen değer birimleri. Birimsiz rakam her birimle eşleşebilir (€ için tam sayı).
COMPATIBLE = {
    EUR: (EUR,),
    PCT: (PCT,),
    PP: (PP,),
    FACTOR: (FACTOR,),
    PLAIN: (EUR, PCT, PP, FACTOR, COUNT),
}
# Yüzde ile yüzde puanı karıştırılırsa "einheit" bulgusu.
CONFUSABLE = {PCT: (PP,), PP: (PCT,)}


def matching(num: Num, values: list[Value], units: tuple[str, ...]) -> list[Value]:
    return [v for v in values if v.unit in units and rounds_to(v.value, num)]


def sign_consistent(num: Num, values: list[Value]) -> bool:
    if not num.sign:
        return True
    return any(v.value == 0 or (v.value > 0) == (num.sign == "+") for v in values)
