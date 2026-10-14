"""Olay kataloğu (docs/03_olay_katalogu.md): kayıt yapısı, havuz olaylarının örneklenmesi ve uygulanması.

Havuz olayları (E01–E12) ekonomik gerçek seriyi değiştirir. Muhasebe pratiğinden doğan olaylar
(E13–E18) practices.py'de, kaydedilen seri üzerinde üretilir. Sezon deseni (E19) burada kaydedilir.
"""

from dataclasses import dataclass, field

import numpy as np

from .lines import BASE_LINES, EPS, LINE_INDEX
from .model import Base, Drivers, compute_lines, monthly_base
from .timeline import Timeline
from .variant import Variant

CATEGORY = {
    **{f"E{i:02d}": "R" for i in range(1, 11)},
    "E11": "V5", "E12": "V5",
    "E13": "V1", "E14": "V1", "E15": "V1",
    "E16": "V2", "E17": "V3", "E18": "V4", "E19": "V6",
}

REAL_AND_V5 = tuple(f"E{i:02d}" for i in range(1, 13))

# Yeni olay sayımında (olaysız ay, yoğunluk) kullanılan havuz olayları (docs/03, Bölüm 4).
POOL_TYPES = REAL_AND_V5 + ("E16", "E18")

# Çakışma sınırı için olayın birincil satırları (docs/03, Bölüm 4, D8).
PRIMARY_LINES = {
    "E01": ("personalkosten",), "E02": ("personalkosten",), "E03": ("personalkosten",),
    "E04": ("material_wareneinkauf",), "E05": ("umsatzerloese",),
    "E06": ("umsatzerloese", "material_wareneinkauf"),
    "E07": ("umsatzerloese", "material_wareneinkauf"),
    "E08": ("abschreibungen", "zinsaufwand"), "E09": ("raumkosten",),
    "E10": ("sonstiger_neutraler_ertrag",), "E11": ("werbe_reisekosten",),
    "E12": ("reparatur_instandhaltung",),
}


@dataclass
class Event:
    firm_id: str
    type: str
    start: int                 # ay indeksi
    end: int | None            # son etkili ay; kalıcı olaylarda None
    shape: str                 # einmalig | temporär | dauerhaft | periodisch
    params: dict = field(default_factory=dict)
    near_threshold: bool = False
    event_id: str = ""
    deltas: np.ndarray | None = None  # satır × ay, EUR
    before: np.ndarray | None = None  # olay uygulanmadan önceki değerler (yüzde hesabı için)
    note_values: dict = field(default_factory=dict)
    documented: bool = False
    source_id: str | None = None
    expected_flags: list[tuple[int, str, str]] = field(default_factory=list)    # (ay, kod, satır)
    acceptable_flags: list[tuple[int, str, str]] = field(default_factory=list)
    overlaps_with: list[str] = field(default_factory=list)

    @property
    def category(self) -> str:
        return CATEGORY[self.type]

    @property
    def duration(self) -> str:
        """Kalıcı/geçici (docs/03, Bölüm 5.2). E19 (sezon) firma notu gibi kalıcı sayılır."""
        if self.type == "E19" or self.shape == "dauerhaft":
            return "dauerhaft"
        return "temporär"

    @property
    def expected_treatment(self) -> str:
        if self.type == "E19":
            return "seasonal"
        if self.category in ("V1", "V2", "V3", "V4"):
            return "warning"
        return "cite" if self.documented else "hypothesis"

    @property
    def is_pool(self) -> bool:
        if self.type == "E16":
            return self.shape == "temporär"  # yalnızca epizodik E16 havuz olayıdır
        return self.type in POOL_TYPES

    def active_months(self) -> list[int]:
        if self.deltas is None:
            return []
        return [int(i) for i in np.nonzero(np.abs(self.deltas).max(axis=0) > EPS)[0]]

    def lines(self) -> list[str]:
        if self.deltas is None:
            return []
        rows = np.nonzero(np.abs(self.deltas).max(axis=1) > EPS)[0]
        return [BASE_LINES[r] for r in rows]


def _draw(rng: np.random.Generator, bounds, near: bool) -> float:
    lo, hi = bounds
    u = rng.uniform(0.0, 0.25) if near else rng.uniform(0.0, 1.0)
    return float(lo + (hi - lo) * u)


def _effect_months(ev: Event) -> list[int]:
    last = ev.start if ev.end is None else ev.end
    return list(range(ev.start, last + 1))


def _sample_params(etype: str, variant: Variant, gen: dict, rng: np.random.Generator,
                   start: int, n: int) -> Event:
    mag = gen["events"]["magnitude"]
    near = bool(rng.random() < gen["events"]["near_threshold_share"])
    ev = Event(firm_id=variant.firm_id, type=etype, start=start, end=None,
               shape="dauerhaft", near_threshold=near)
    p = ev.params
    if etype in ("E01", "E02"):
        pct = _draw(rng, mag[f"{etype}_pct_employees"], near)
        p["people"] = max(2, int(round(pct / 100.0 * variant.employees)))
    elif etype == "E03":
        p["pct"] = round(_draw(rng, mag["E03_pct"], near), 1)
    elif etype == "E04":
        p["pp"] = _draw(rng, mag["E04_pp"], near)
        if rng.random() < mag["E04_temporary_share"]:
            months = int(rng.integers(mag["E04_temporary_months"][0], mag["E04_temporary_months"][1] + 1))
            ev.shape, ev.end = "temporär", min(start + months - 1, n - 1)
    elif etype == "E05":
        p["pct"] = _draw(rng, mag["E05_pct"], near)
    elif etype == "E06":
        p["pct"] = _draw(rng, mag["E06_pct"], near)
        months = int(rng.integers(mag["E06_months"][0], mag["E06_months"][1] + 1))
        ev.end = min(start + months - 1, n - 1)
        ev.shape = "einmalig" if ev.end == start else "temporär"
    elif etype == "E07":
        p["pct"] = _draw(rng, mag["E07_pct"], near)
    elif etype == "E08":
        p["afa_pct"] = _draw(rng, mag["E08_afa_pct"], near)
        p["zins_pct"] = _draw(rng, mag["E08_zins_pct"], near)
    elif etype == "E09":
        p["pct"] = _draw(rng, mag["E09_pct"], near)
    elif etype == "E10":
        p["pct_of_umsatz"] = _draw(rng, mag["E10_pct_of_umsatz"], near)
        ev.shape, ev.end = "einmalig", start
    elif etype == "E11":
        p["extra_multiple"] = _draw(rng, mag["E11_extra_multiple"], near)
        two = variant.fair_month is None and rng.random() < mag["E11_two_month_share"]
        ev.end = min(start + 1, n - 1) if two else start
        ev.shape = "einmalig" if ev.end == start else "temporär"
    elif etype == "E12":
        p["extra_multiple"] = _draw(rng, mag["E12_extra_multiple"], near)
        ev.shape, ev.end = "einmalig", start
    return ev


def sample_pool_events(variant: Variant, timeline: Timeline, gen: dict,
                       rng: np.random.Generator) -> tuple[list[Event], np.ndarray]:
    """E01–E12 olaylarını örnekler. Dönen doluluk matrisi (satır × ay) E16/E18 için de kullanılır."""
    n = timeline.n
    cap = gen["events"]["max_events_per_line_month"]
    overlap_accept = gen["events"]["overlap_accept_share"]
    occupancy = np.zeros((len(BASE_LINES), n), dtype=int)
    excluded = set(variant.archetype.events_excluded)
    events: list[Event] = []
    series_count: dict[str, int] = {}
    series_cap = gen["events"].get("series_cap", {})

    def fits(ev: Event) -> bool:
        if any(e.type == ev.type and e.start == ev.start for e in events):
            return False  # aynı türden iki olay aynı ayda başlamaz
        cells = [occupancy[LINE_INDEX[l], m] for l in PRIMARY_LINES[ev.type] for m in _effect_months(ev)]
        if any(c >= cap for c in cells):
            return False
        return not any(cells) or rng.random() < overlap_accept

    def place(etype: str, candidates: list[int], forced: bool = False) -> None:
        if etype in series_cap and series_count.get(etype, 0) >= series_cap[etype]:
            return
        tries = 1 if forced else 20
        for _ in range(tries):
            start = candidates[0] if forced else int(rng.choice(candidates))
            ev = _sample_params(etype, variant, gen, rng, start, n)
            if forced or fits(ev):
                for line in PRIMARY_LINES[etype]:
                    for m in _effect_months(ev):
                        occupancy[LINE_INDEX[line], m] += 1
                events.append(ev)
                series_count[etype] = series_count.get(etype, 0) + 1
                return

    for year in timeline.years:
        months = timeline.year_indices(year)

        def fixed_month(month: int) -> list[int]:
            return [i for i in months if timeline.month_of_year(i) == month - 1]

        # Sabit aylı olaylar önce yerleştirilir; rastgele olaylar çakışma sınırına onlara göre uyar.
        fixed = {"E03": fixed_month(variant.archetype.tariff_month)}
        if variant.fair_month is not None and "E11" not in excluded:
            fixed["E11"] = fixed_month(variant.fair_month)
        for etype, candidates in fixed.items():
            if candidates:
                place(etype, candidates, forced=True)
        for etype, (lo, hi) in gen["events"]["per_year"].items():
            if etype in excluded or etype in fixed:
                continue
            for _ in range(int(rng.integers(lo, hi + 1))):
                place(etype, months)

    for etype, (lo, hi) in gen["events"].get("per_series", {}).items():
        if etype in excluded:
            continue
        for _ in range(int(rng.integers(lo, hi + 1))):
            place(etype, list(range(n)))

    return events, occupancy


def _apply(ev: Event, drv: Drivers, before: np.ndarray, variant: Variant, base: Base) -> None:
    t, p = ev.start, ev.params
    q, r0 = variant.quotas, monthly_base(variant)
    sl = slice(t, None if ev.end is None else ev.end + 1)
    if ev.type == "E01":
        drv.headcount[t:] += p["people"]
    elif ev.type == "E02":
        drv.headcount[t:] = np.maximum(drv.headcount[t:] - p["people"], 5.0)
    elif ev.type == "E03":
        drv.wage[t:] *= 1 + p["pct"] / 100.0
    elif ev.type == "E04":
        drv.mat_add[sl] += p["pp"] / 100.0
    elif ev.type == "E05":
        drv.price[t:] *= 1 + p["pct"] / 100.0
    elif ev.type == "E06":
        drv.vol[sl] *= 1 + p["pct"] / 100.0
    elif ev.type == "E07":
        drv.vol[t:] *= 1 - p["pct"] / 100.0
    elif ev.type == "E08":
        drv.afa[t:] *= 1 + p["afa_pct"] / 100.0
        drv.zins[t:] *= 1 + p["zins_pct"] / 100.0
    elif ev.type == "E09":
        drv.raum[t:] *= 1 + p["pct"] / 100.0
    elif ev.type == "E10":
        drv.neutral_ertrag_add[t] += p["pct_of_umsatz"] / 100.0 * before[LINE_INDEX["umsatzerloese"], t]
    elif ev.type == "E11":
        extra = p["extra_multiple"] * q["werbe_reisekosten"] * r0 * base.infl[t]
        if ev.end != t:
            drv.werbe_add[t] += 0.3 * extra
            drv.werbe_add[ev.end] += 0.7 * extra
        else:
            drv.werbe_add[t] += extra
    elif ev.type == "E12":
        drv.reparatur_add[t] += p["extra_multiple"] * q["reparatur_instandhaltung"] * r0 * base.infl[t]


def _note_values(ev: Event, variant: Variant, gen: dict) -> dict:
    """Notlarda kullanılabilecek, olay parametrelerinden türetilmiş değerler (yuvarlanmamış)."""
    d, p, t = ev.deltas, ev.params, ev.start
    row = LINE_INDEX
    if ev.type in ("E01", "E02"):
        return {"n": p["people"]}
    if ev.type == "E03":
        return {"p": p["pct"]}
    if ev.type == "E04":
        return {"p": p["pp"] / variant.quotas["material_wareneinkauf"]}
    if ev.type in ("E05", "E07"):
        return {"p": p["pct"]}
    if ev.type == "E06":
        return {"betrag": float(d[row["umsatzerloese"]].sum())}
    if ev.type == "E08":
        years = gen["events"]["magnitude"]["E08_useful_life_years"]
        return {"betrag": float(d[row["abschreibungen"], t]) * 12 * years}
    if ev.type == "E09":
        return {"p": p["pct"], "betrag": float(d[row["raumkosten"], t])}
    if ev.type == "E10":
        return {"betrag": float(d[row["sonstiger_neutraler_ertrag"], t])}
    if ev.type == "E11":
        return {"betrag": float(d[row["werbe_reisekosten"]].sum())}
    if ev.type == "E12":
        return {"betrag": float(d[row["reparatur_instandhaltung"], t])}
    return {}


def apply_pool_events(variant: Variant, base: Base, events: list[Event], timeline: Timeline,
                      gen: dict) -> tuple[np.ndarray, np.ndarray]:
    """Olayları sırayla uygular; her olayın etkisi (deltas) önceki duruma göre ölçülür.

    Döner: (olaysız taban seri, olaylı ekonomik seri — gürültüsüz)
    """
    drv = Drivers.initial(variant, timeline.n)
    lines = compute_lines(variant, base, drv)
    baseline = lines.copy()
    events.sort(key=lambda e: (e.start, e.type))
    for ev in events:
        before = lines
        _apply(ev, drv, before, variant, base)
        lines = compute_lines(variant, base, drv)
        ev.before, ev.deltas = before, lines - before
        ev.note_values = _note_values(ev, variant, gen)
        # Beklenen bayraklar: yalnızca V5 olaylarında (docs/03, Bölüm 3).
        if ev.category == "V5":
            line = PRIMARY_LINES[ev.type][0]
            ev.expected_flags = [(m, "V5", line) for m in ev.active_months()]
    return baseline, lines


def season_event(variant: Variant, timeline: Timeline, gen: dict) -> Event:
    """E19: sezon deseni, varyant başına bir kayıt."""
    threshold = gen["events"]["season_flag_min_change_pct"]
    ev = Event(firm_id=variant.firm_id, type="E19", start=0, end=None, shape="periodisch")
    ev.params = {"season_index": [round(float(x), 4) for x in variant.season]}
    for i in range(1, timeline.n):
        if abs(seasonal_change_pct(ev, timeline, i)) >= threshold:
            ev.expected_flags.append((i, "V6", "umsatzerloese"))
    return ev


def seasonal_change_pct(season: Event, timeline: Timeline, i: int) -> float | None:
    """Satış endeksinin önceki aya göre sezonsal değişimi (%)."""
    if i == 0:
        return None
    index = season.params["season_index"]
    prev, cur = index[timeline.month_of_year(i - 1)], index[timeline.month_of_year(i)]
    return round((cur / prev - 1.0) * 100.0, 1)


def assign_ids(events: list[Event], timeline: Timeline) -> None:
    seen: dict[str, int] = {}
    for ev in events:
        base_id = f"{ev.firm_id}-{ev.type}-{timeline.period(ev.start)}"
        seen[base_id] = seen.get(base_id, 0) + 1
        ev.event_id = base_id if seen[base_id] == 1 else f"{base_id}-{seen[base_id]}"


def mark_overlaps(events: list[Event]) -> None:
    """Aynı başlangıç ayında ortak bir satıra dokunan havuz olayları çakışır (D8)."""
    pool = [e for e in events if e.is_pool]
    for a in pool:
        a_lines = set(a.lines())
        a.overlaps_with = sorted(
            b.event_id for b in pool
            if b is not a and b.start == a.start and a_lines & set(b.lines())
        )
