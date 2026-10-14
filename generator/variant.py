"""Arketipten varyant üretimi (docs/01_firma_profili.md, Bölüm 4–5).

v00 her arketipin parametrelerini aynen alır; A1-v00 vitrin firması Muster GmbH'dir.
Diğer varyantlar büyüklük, oranlar, sezon genliği, trend ve muhasebe pratiği bakımından çekilir.
"""

from dataclasses import dataclass

import numpy as np

from .config import Archetype
from .timeline import Timeline


@dataclass(frozen=True)
class Practices:
    p1_sonderzahlungen: bool   # E13, E14 (V1)
    p2_jahrespraemien: bool    # E15 (V1)
    p3_bestand: bool           # E16 sistematik (V2)
    p3_mode: str               # "quartal" (üretici) | "inventur" (ticaret)
    p4_afa_jahresende: bool    # E17 (V3)
    p5_per_year: tuple[int, ...]           # E18 (V4), yıl başına adet
    episodic_bv_per_year: tuple[int, ...]  # E16 epizodik (V2), yıl başına adet
    urlaubsgeld_share: float   # aylık maaşın payı
    weihnachtsgeld_share: float
    praemien_share: float      # Versicherungen/Beiträge satırındaki yıllık prim payı


@dataclass(frozen=True)
class Variant:
    firm_id: str
    archetype: Archetype
    index: int
    name: str
    employees: int
    revenue_2024: float
    quotas: dict[str, float]
    season: np.ndarray            # 12 aylık satış endeksi
    production_shift: np.ndarray  # 12 aylık üretim − satış
    trend_pct: dict[int, float]   # yıl → yüzde
    practices: Practices
    fair_month: int | None        # A3: her yıl aynı fuar ayı (1..12)

    @property
    def kind(self) -> str:
        return self.archetype.kind

    @property
    def herstell_factor(self) -> float:
        return self.archetype.herstell_factor


def _uniform(rng: np.random.Generator, bounds) -> float:
    lo, hi = bounds
    return float(rng.uniform(lo, hi))


def _variant_name(arch: Archetype, index: int, stems: list[str]) -> str:
    if index == 0:
        return arch.name
    k = index - 1
    stem = stems[k % len(stems)]
    word = arch.name_words[k % len(arch.name_words)]
    if k >= len(stems):
        return f"{stem} {word} {k // len(stems) + 1} GmbH"
    return f"{stem} {word} GmbH"


def _practices(arch: Archetype, index: int, gen: dict, timeline: Timeline,
               rng: np.random.Generator) -> Practices:
    mag = gen["events"]["magnitude"]
    years = len(timeline.years)
    urlaub = _uniform(rng, mag["E13_pct"]) / 100.0
    weihnacht = _uniform(rng, mag["E14_pct"]) / 100.0
    jan_multiple = _uniform(rng, mag["E15_jan_multiple"])
    praemien = (jan_multiple - 1.0) / 11.0
    p = arch.practices

    if index == 0:
        v = arch.v00_practices
        p3 = bool(v["p3_bestand"])
        return Practices(
            p1_sonderzahlungen=bool(v["p1_sonderzahlungen"]),
            p2_jahrespraemien=bool(v["p2_jahrespraemien"]),
            p3_bestand=p3,
            p3_mode=p["p3_mode"],
            p4_afa_jahresende=bool(v["p4_afa_jahresende"]),
            p5_per_year=(int(v["p5_per_year"]),) * years,
            episodic_bv_per_year=(0 if p3 else int(v["episodic_bv_per_year"]),) * years,
            urlaubsgeld_share=urlaub,
            weihnachtsgeld_share=weihnacht,
            praemien_share=praemien,
        )

    p3 = bool(rng.random() < p["p3_bestand"])
    lo5, hi5 = p["p5_per_year"]
    lo_e, hi_e = p["episodic_bv_per_year"]
    return Practices(
        p1_sonderzahlungen=bool(rng.random() < p["p1_sonderzahlungen"]),
        p2_jahrespraemien=bool(rng.random() < p["p2_jahrespraemien"]),
        p3_bestand=p3,
        p3_mode=p["p3_mode"],
        p4_afa_jahresende=bool(rng.random() < p["p4_afa_jahresende"]),
        p5_per_year=tuple(int(rng.integers(lo5, hi5 + 1)) for _ in range(years)),
        episodic_bv_per_year=tuple(
            0 if p3 else int(rng.integers(lo_e, hi_e + 1)) for _ in range(years)
        ),
        urlaubsgeld_share=urlaub,
        weihnachtsgeld_share=weihnacht,
        praemien_share=praemien,
    )


def make_variant(arch: Archetype, index: int, gen: dict, timeline: Timeline,
                 rng: np.random.Generator) -> Variant:
    cfg = gen["variants"]
    firm_id = f"{arch.code}-v{index:02d}"
    season = np.array(arch.season, dtype=float)
    shift = np.array(arch.production_shift, dtype=float)
    years = timeline.years

    if index == 0:
        employees = arch.employees
        quotas = dict(arch.quotas)
        trend = {y: arch.trend_v00_pct for y in years}
        trend[years[-1]] = arch.trend_v00_2026_pct
    else:
        lo_emp, hi_emp = cfg["employees_bounds"]
        size = _uniform(rng, cfg["size_factor"])
        employees = int(np.clip(round(arch.employees * size), lo_emp, hi_emp))
        quotas = {}
        for line, q in arch.quotas.items():
            rel = cfg["material_quota_rel"] if line == "material_wareneinkauf" else cfg["quota_rel"]
            quotas[line] = q * _uniform(rng, (1 - rel, 1 + rel))
        amplitude = _uniform(rng, cfg["season_amplitude"])
        season = 1.0 + amplitude * (season - 1.0)
        growth = _uniform(rng, cfg["trend_pct"])
        trend = {y: growth for y in years}

    fair_month = int(rng.choice([6, 9])) if arch.fair_annual else None

    return Variant(
        firm_id=firm_id,
        archetype=arch,
        index=index,
        name=_variant_name(arch, index, cfg["name_stems"]),
        employees=employees,
        revenue_2024=arch.revenue_2024 * employees / arch.employees,
        quotas=quotas,
        season=season,
        production_shift=shift,
        trend_pct=trend,
        practices=_practices(arch, index, gen, timeline, rng),
        fair_month=fair_month,
    )
