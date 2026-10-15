"""Rohertrag adayları ve dengelenmiş V2 test kümesi (docs/03, Bölüm 9.1; docs/04, Bölüm 8).

Rohertrag adayı: Rohertragsquote hem önceki aya hem önceki yılın aynı ayına göre en az `ratio_pp` puan
değişmiş. Bu, Katman 1'in nötr "aday" işaretiyle aynı kuraldır (CLAUDE.md 6.2). Doğru karar
(cite / warn / either) yalnızca ground truth'tadır.
"""

import numpy as np

from .lines import LINE_INDEX
from .timeline import Timeline

_DECISIONS = ("cite", "warn", "either", None)


def rohertragsquote(lines: np.ndarray) -> np.ndarray:
    """Aylık Rohertragsquote (%), kaydedilen seri üzerinden."""
    gl = (lines[LINE_INDEX["umsatzerloese"]] + lines[LINE_INDEX["bestandsveraenderungen_fe_ue"]]
          + lines[LINE_INDEX["aktivierte_eigenleistungen"]])
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(gl != 0, (gl - lines[LINE_INDEX["material_wareneinkauf"]]) / gl * 100, np.nan)


def rohertrag_candidates(booked: np.ndarray, timeline: Timeline, pp: float) -> dict[int, tuple[float, float]]:
    """Ay indeksi → (önceki aya göre, önceki yılın aynı ayına göre) Rohertragsquote değişimi (puan)."""
    rq = rohertragsquote(booked)
    out = {}
    for i in range(12, timeline.n):
        vm, vj = rq[i] - rq[i - 1], rq[i] - rq[i - 12]
        if abs(vm) >= pp and abs(vj) >= pp:
            out[i] = (round(float(vm), 1), round(float(vj), 1))
    return out


def decision_counts(results, timeline: Timeline, pp: float) -> dict:
    """Arketip başına, yorumlanabilir aylarda beklenen V2 kararlarının sayısı:
    bütün aylar ve yalnızca Rohertrag adayı olan aylar."""
    table: dict[str, dict] = {}
    for r in results:
        code = r.variant.archetype.code
        entry = table.setdefault(code, {"all": dict.fromkeys(map(str, _DECISIONS), 0),
                                        "candidates": dict.fromkeys(map(str, _DECISIONS), 0)})
        candidates = rohertrag_candidates(r.booked, timeline, pp)
        for i, m in enumerate(r.months):
            if not m["commentable"]:
                continue
            key = str(m["v2_candidate_decision"])
            entry["all"][key] += 1
            if i in candidates:
                entry["candidates"][key] += 1
    return table


def balanced_v2_set(results, timeline: Timeline, pp: float, seed: int, include_either: bool = True) -> list[dict]:
    """Her arketipte eşit sayıda cite ve warn adayı ay (either: en fazla aynı sayıda)."""
    rng = np.random.default_rng([seed, 9_002])
    pools: dict[str, dict[str, list[dict]]] = {}
    for r in results:
        code = r.variant.archetype.code
        candidates = rohertrag_candidates(r.booked, timeline, pp)
        for i, (vm, vj) in candidates.items():
            m = r.months[i]
            decision = m["v2_candidate_decision"]
            if not m["commentable"] or decision is None:
                continue
            pools.setdefault(code, {"cite": [], "warn": [], "either": []})[decision].append({
                "firm_id": r.variant.firm_id,
                "period": m["period"],
                "archetype": code,
                "decision": decision,
                "rq_change_previous_month_pp": vm,
                "rq_change_previous_year_month_pp": vj,
                "rohertrag_causes": m["rohertrag_causes"],
            })

    selected = []
    for code in sorted(pools):
        pool = pools[code]
        k = min(len(pool["cite"]), len(pool["warn"]))
        groups = ("cite", "warn", "either") if include_either else ("cite", "warn")
        for decision in groups:
            items = pool[decision]
            take = min(k, len(items))
            for pos in sorted(rng.choice(len(items), take, replace=False)) if take else []:
                selected.append(items[int(pos)])
    return sorted(selected, key=lambda x: (x["firm_id"], x["period"]))
