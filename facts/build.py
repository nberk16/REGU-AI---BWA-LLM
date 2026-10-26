"""Bir firma-ay için facts.json (şema 1.0, docs/05_facts_semasi.md).

Kurallar [KARAR, tur 4–5]:
- Kalem anlamlı: önceki yılın aynı ayına göre |Δ| ≥ %10 ve |Δ| ≥ cari ay Gesamtleistung'unun %0,5'i.
- Önceki ay karşılaştırması ve kümülatif bilgi amaçlıdır; sıralamaya girmez.
- Yorumda en fazla 5 kalem, önceki yılın aynı ayına göre |Δ €| büyüklüğüne göre sıralı.
- delta_pct: sonuç satırlarında, küçük tabanlarda (|taban| < mutlak eşik) ve işaret değiştiren
  tabanlarda null.
- Eşik karşılaştırmaları yuvarlanmamış değerlerle yapılır; çıktıda tutarlar tam sayı €,
  yüzde ve yüzde puanları 1 ondalık.
"""

import statistics

from .flags import compute_flags
from .formatting import de_int, de_pct, de_signed
from .schema import BASE_LINES, MONTHS_DE, RATIOS, RESULT_LINES, SUMMARY_LINES
from .series import FirmSeries


def _r(x: float) -> int:
    return int(round(float(x)))


def _r1(x: float | None) -> float | None:
    return None if x is None else round(float(x), 1) + 0.0  # + 0.0: -0.0 yerine 0.0


def period_label(period: str) -> str:
    return f"{MONTHS_DE[int(period[5:7]) - 1]} {period[:4]}"


class MonthContext:
    """Bir firma-ay için eşikler, normal düzeyler ve karşılaştırma dönemleri."""

    def __init__(self, fs: FirmSeries, i: int, cfg: dict):
        if i < 12:
            raise ValueError(f"{fs.periods[i]}: önceki yılın aynı ayı yok; facts.json en erken 13. ay için üretilir.")
        th, fl = cfg["thresholds"], cfg["flags"]
        self.fs, self.i, self.cfg = fs, i, cfg
        self.rel = th["position_rel_pct"]
        self.pp = th["ratio_pp"]
        share = th["position_abs_share_of_gl_pct"] / 100.0
        gl = fs.values["gesamtleistung"]
        year = fs.periods[i][:4]
        self.ytd = [j for j in range(i + 1) if fs.periods[j][:4] == year]
        self.ytd_prev = [j - 12 for j in self.ytd]
        self.abs_thr = float(share * abs(gl[i]))
        self.abs_thr_cum = float(share * abs(gl[self.ytd].sum()))
        self.n_normal = fl["normal_months"]
        self.min_history = fl["min_history_months"]

    def normal(self, key: str, end: int | None = None) -> float:
        """Normal düzey: `end`'den önceki 12 ayın medyanı (varsayılan: cari ay)."""
        end = self.i if end is None else end
        return float(statistics.median(self.fs.values[key][max(0, end - self.n_normal):end]))

    def normal_for_base(self, key: str, j: int) -> float:
        """Karşılaştırma tabanı j için normal düzey; yeterli geçmiş yoksa cari ayın normal düzeyi."""
        history = self.fs.values[key][max(0, j - self.n_normal):j]
        if len(history) >= self.min_history:
            return float(statistics.median(history))
        return self.normal(key)

    def pct(self, a: float, b: float, key: str, thr: float) -> float | None:
        if key in RESULT_LINES or b == 0 or abs(b) < thr or a * b < 0:
            return None
        return (a - b) / abs(b) * 100.0

    def significant(self, delta: float, pct: float | None, thr: float) -> bool:
        return bool(abs(delta) >= thr and (pct is None or abs(pct) >= self.rel))

    def unusual(self, x: float, normal: float) -> bool:
        dev = x - normal
        return bool(abs(dev) >= self.abs_thr and (normal == 0 or abs(dev) / abs(normal) * 100.0 >= self.rel))


def _item(ctx: MonthContext, key: str, label: str) -> dict:
    v, i = ctx.fs.values[key], ctx.i
    a, b_vm, b_vj = float(v[i]), float(v[i - 1]), float(v[i - 12])
    pct_vm = ctx.pct(a, b_vm, key, ctx.abs_thr)
    pct_vj = ctx.pct(a, b_vj, key, ctx.abs_thr)
    a_cum, b_cum = float(v[ctx.ytd].sum()), float(v[ctx.ytd_prev].sum())
    pct_cum = ctx.pct(a_cum, b_cum, key, ctx.abs_thr_cum)
    return {
        "key": key,
        "position": label,
        "actual": _r(a),
        "normal_level": _r(ctx.normal(key)),
        "previous_month": {
            "value": _r(b_vm), "delta_abs": _r(a - b_vm), "delta_pct": _r1(pct_vm),
            "base_unusual": ctx.unusual(b_vm, ctx.normal(key)),
        },
        "previous_year_month": {
            "value": _r(b_vj), "delta_abs": _r(a - b_vj), "delta_pct": _r1(pct_vj),
            "significant": ctx.significant(a - b_vj, pct_vj, ctx.abs_thr),
            "base_unusual": ctx.unusual(b_vj, ctx.normal_for_base(key, i - 12)),
        },
        "cumulative": {
            "actual": _r(a_cum), "previous_year": _r(b_cum), "delta_abs": _r(a_cum - b_cum),
            "delta_pct": _r1(pct_cum), "significant": ctx.significant(a_cum - b_cum, pct_cum, ctx.abs_thr_cum),
        },
        "_delta_vj": abs(a - b_vj),
    }


def _reason(ctx: MonthContext, item: dict) -> str:
    vj = item["previous_year_month"]
    return (f"Vorjahresmonat {de_signed(vj['delta_abs'])} € ({de_pct(vj['delta_pct'])}); "
            f"Schwelle: ≥ {de_pct(ctx.rel, signed=False)} und ≥ {de_int(ctx.abs_thr)} € "
            f"(0,5 % der Gesamtleistung)")


def _ratio(ctx: MonthContext, label: str, numerator: str) -> dict:
    v, i = ctx.fs.values, ctx.i
    gl, num = v["gesamtleistung"], v[numerator]

    def q(j: int) -> float:
        return float(num[j] / gl[j] * 100.0)

    a, m, y = q(i), q(i - 1), q(i - 12)
    ca = float(num[ctx.ytd].sum() / gl[ctx.ytd].sum() * 100.0)
    cp = float(num[ctx.ytd_prev].sum() / gl[ctx.ytd_prev].sum() * 100.0)
    return {
        "ratio": label,
        "actual": _r1(a),
        "previous_month": {"value": _r1(m), "delta_pp": _r1(a - m)},
        "previous_year_month": {"value": _r1(y), "delta_pp": _r1(a - y), "significant": abs(a - y) >= ctx.pp},
        "cumulative": {"actual": _r1(ca), "previous_year": _r1(cp), "delta_pp": _r1(ca - cp),
                       "significant": abs(ca - cp) >= ctx.pp},
    }


def build_facts(fs: FirmSeries, period: str, cfg: dict) -> dict:
    ctx = MonthContext(fs, fs.index(period), cfg)
    i, p = ctx.i, fs.periods
    max_positions = cfg["thresholds"]["max_positions"]

    candidates = []
    for key, label in BASE_LINES.items():
        v = fs.values[key]
        if v[i] == 0 and v[i - 1] == 0 and v[i - 12] == 0:
            continue
        item = _item(ctx, key, label)
        if item["previous_year_month"]["significant"]:
            candidates.append(item)
    candidates.sort(key=lambda it: -it["_delta_vj"])

    positions = []
    for rank, item in enumerate(candidates, start=1):
        item.pop("_delta_vj")
        significance = {"basis": "previous_year_month", "reason": _reason(ctx, item)}
        positions.append({"rank": rank, **item, "significance": significance})

    summary = []
    for key, label in SUMMARY_LINES.items():
        item = _item(ctx, key, label)
        item.pop("_delta_vj")
        summary.append(item)

    return {
        "schema_version": cfg["schema_version"],
        "company": {"firm_id": fs.firm_id, "name": fs.name},
        "period": p[i],
        "period_label": period_label(p[i]),
        "comparisons": {
            "previous_month": p[i - 1],
            "previous_year_month": p[i - 12],
            "cumulative": f"{p[ctx.ytd[0]]} – {p[i]}",
            "cumulative_previous_year": f"{p[ctx.ytd_prev[0]]} – {p[i - 12]}",
        },
        "thresholds": {
            "significance_basis": "previous_year_month",
            "position_rel_pct": ctx.rel,
            "position_abs_eur": _r(ctx.abs_thr),
            "cumulative_abs_eur": _r(ctx.abs_thr_cum),
            "ratio_pp": ctx.pp,
            "max_positions": max_positions,
        },
        "summary": summary,
        "positions": positions[:max_positions],
        "further_significant": [{"rank": it["rank"], "key": it["key"], "position": it["position"]}
                                for it in positions[max_positions:]],
        "ratios": [_ratio(ctx, label, num) for label, num in RATIOS.items()],
        "flags": compute_flags(ctx),
    }


def commentable_periods(fs: FirmSeries) -> list[str]:
    """facts.json üretilebilen aylar (önceki yılın aynı ayı mevcut olanlar)."""
    return fs.periods[12:]
