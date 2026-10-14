"""Çıktı dosyaları ve sağlama raporu (docs/04_veri_ureteci.md, Bölüm 3).

model_input/ : modele ve RAG'e girebilecek dosyalar
evaluation/  : yalnızca değerlendirme; hiçbir zaman model girdisine veya RAG'e girmez
"""

import csv
import json
from pathlib import Path

import numpy as np

from . import __version__
from .config import config_fingerprint
from .events import REAL_AND_V5
from .ground_truth import event_record
from .lines import BASE_LINES, EPS, LINE_INDEX
from .pipeline import VariantResult
from .timeline import Timeline

MODEL_INPUT_FILES = ("bwa_raw.csv", "context_notes.jsonl", "firms.json")
EVALUATION_FILES = ("bwa_true.csv", "effects.csv", "events.jsonl", "ground_truth_months.jsonl",
                    "notes_ground_truth.jsonl", "variants.json")


def _json_default(obj):
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"JSON'a çevrilemiyor: {type(obj)}")


def _dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, default=_json_default)


def _money(x: float) -> str:
    return f"{round(float(x), 2) + 0.0:.2f}"


def _write_jsonl(path: Path, rows) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(_dumps(row) + "\n")


def _write_series(path: Path, results: list[VariantResult], timeline: Timeline, attr: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["firm_id", "period", "line", "value"])
        for r in results:
            values = getattr(r, attr)
            for i in range(timeline.n):
                period = timeline.period(i)
                for row, line in enumerate(BASE_LINES):
                    w.writerow([r.variant.firm_id, period, line, _money(values[row, i])])


def _write_effects(path: Path, results: list[VariantResult], timeline: Timeline) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["firm_id", "period", "line", "event_id", "delta"])
        for r in results:
            for ev in r.events:
                if ev.deltas is None:
                    continue
                rows, months = np.nonzero(np.abs(ev.deltas) > EPS)
                for row, i in sorted(zip(rows, months), key=lambda x: (x[1], x[0])):
                    w.writerow([ev.firm_id, timeline.period(int(i)), BASE_LINES[row], ev.event_id,
                                _money(ev.deltas[row, i])])


def _variant_record(r: VariantResult) -> dict:
    v = r.variant
    p = v.practices
    return {
        "firm_id": v.firm_id,
        "archetype": v.archetype.code,
        "name": v.name,
        "branche": v.archetype.branche,
        "kind": v.kind,
        "employees": v.employees,
        "revenue_2024": round(v.revenue_2024, 2),
        "quotas_pct": {k: round(q * 100, 2) for k, q in v.quotas.items()},
        "season_index": [round(float(x), 4) for x in v.season],
        "trend_pct": {str(y): round(g, 2) for y, g in v.trend_pct.items()},
        "fair_month": v.fair_month,
        "practices": {
            "p1_sonderzahlungen": p.p1_sonderzahlungen,
            "p2_jahrespraemien": p.p2_jahrespraemien,
            "p3_bestand": p.p3_bestand,
            "p3_mode": p.p3_mode,
            "p4_afa_jahresende": p.p4_afa_jahresende,
            "p5_per_year": list(p.p5_per_year),
            "episodic_bv_per_year": list(p.episodic_bv_per_year),
            "urlaubsgeld_share_pct": round(p.urlaubsgeld_share * 100, 1),
            "weihnachtsgeld_share_pct": round(p.weihnachtsgeld_share * 100, 1),
            "praemien_share_pct": round(p.praemien_share * 100, 1),
        },
    }


def write_run(results: list[VariantResult], timeline: Timeline, out_dir: Path, seed: int,
              archetype_codes: list[str], variants_per_archetype: int) -> dict:
    model_dir, eval_dir = out_dir / "model_input", out_dir / "evaluation"
    model_dir.mkdir(parents=True, exist_ok=True)
    eval_dir.mkdir(parents=True, exist_ok=True)

    _write_series(model_dir / "bwa_raw.csv", results, timeline, "booked")
    _write_jsonl(model_dir / "context_notes.jsonl", (n for r in results for n in r.notes))
    (model_dir / "firms.json").write_text(
        _dumps([{"firm_id": r.variant.firm_id, "name": r.variant.name} for r in results]) + "\n",
        encoding="utf-8")

    _write_series(eval_dir / "bwa_true.csv", results, timeline, "true")
    _write_effects(eval_dir / "effects.csv", results, timeline)
    _write_jsonl(eval_dir / "events.jsonl", (event_record(e, timeline) for r in results for e in r.events))
    _write_jsonl(eval_dir / "ground_truth_months.jsonl", (m for r in results for m in r.months))
    _write_jsonl(eval_dir / "notes_ground_truth.jsonl", (g for r in results for g in r.notes_gt))
    (eval_dir / "variants.json").write_text(
        json.dumps([_variant_record(r) for r in results], ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8")

    stats = run_statistics(results, timeline)
    manifest = {
        "generator_version": __version__,
        "config_fingerprint": config_fingerprint(),
        "seed": seed,
        "archetypes": archetype_codes,
        "variants_per_archetype": variants_per_archetype,
        "periods": {"start": timeline.period(0), "end": timeline.period(timeline.n - 1),
                    "commentable_from": timeline.period(timeline.commentable_from)},
        "files": {
            "model_input": [f"model_input/{f}" for f in MODEL_INPUT_FILES],
            "evaluation": [f"evaluation/{f}" for f in EVALUATION_FILES],
        },
        "statistics": stats,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, default=_json_default) + "\n", encoding="utf-8")
    (out_dir / "report.md").write_text(build_report(results, timeline, manifest), encoding="utf-8")
    return manifest


# --- İstatistikler ve rapor -------------------------------------------------------------------

def _share(num: int, den: int) -> float | None:
    return round(num / den, 3) if den else None


def run_statistics(results: list[VariantResult], timeline: Timeline) -> dict:
    events = [e for r in results for e in r.events]
    real = [e for e in events if e.type in REAL_AND_V5]
    pool = [e for e in events if e.is_pool]
    commentable = [m for r in results for m in r.months if m["commentable"]]
    event_notes = [g for r in results for g in r.notes_gt
                   if g["event_id"] and g["source_id"] != "Firmenprofil"]
    months_with_distractor = sum(1 for r in results for m in r.months if m["distractor_notes"])
    total_months = len(results) * timeline.n
    years = len(timeline.years)

    by_type = {}
    for etype in sorted({e.type for e in events}):
        same = [e for e in events if e.type == etype]
        by_type[etype] = {"count": len(same), "documented": sum(e.documented for e in same)}

    a2_decisions = {}
    for r in results:
        if r.variant.kind != "trader":
            continue
        for m in r.months:
            if m["commentable"] and m["v2_candidate_decision"]:
                a2_decisions[m["v2_candidate_decision"]] = a2_decisions.get(m["v2_candidate_decision"], 0) + 1

    return {
        "variants": len(results),
        "events_total": len(events),
        "events_by_type": by_type,
        "documented_share_real_v5": _share(sum(e.documented for e in real), len(real)),
        "pool_events_per_month": round(len(pool) / (len(results) * years * 12), 2),
        "quiet_month_share_commentable": _share(sum(m["quiet_month"] for m in commentable), len(commentable)),
        "distractor_month_share": _share(months_with_distractor, total_months),
        "event_notes_with_numbers_share": _share(sum(bool(g["numbers"]) for g in event_notes), len(event_notes)),
        "near_threshold_share_pool": _share(sum(e.near_threshold for e in pool), len(pool)),
        "overlap_share_pool": _share(sum(bool(e.overlaps_with) for e in pool), len(pool)),
        "season_note_share": _share(sum(1 for e in events if e.type == "E19" and e.documented), len(results)),
        "a2_v2_candidate_decisions": a2_decisions,
    }


def _subtotals(lines: np.ndarray) -> dict[str, np.ndarray]:
    g = lambda name: lines[LINE_INDEX[name]]  # noqa: E731
    gl = g("umsatzerloese") + g("bestandsveraenderungen_fe_ue") + g("aktivierte_eigenleistungen")
    rohertrag = gl - g("material_wareneinkauf")
    gesamtkosten = lines[LINE_INDEX["personalkosten"]:LINE_INDEX["sonstige_kosten"] + 1].sum(axis=0)
    betriebsergebnis = rohertrag + g("sonstige_betriebliche_erloese") - gesamtkosten
    return {"Gesamtleistung": gl, "Rohertrag": rohertrag, "Gesamtkosten": gesamtkosten,
            "Betriebsergebnis": betriebsergebnis}


def _eur(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")


def build_report(results: list[VariantResult], timeline: Timeline, manifest: dict) -> str:
    s = manifest["statistics"]
    out = [
        "# Sentetik veri koşusu — sağlama raporu",
        "",
        f"- Seed: `{manifest['seed']}` · Arketipler: {', '.join(manifest['archetypes'])} · "
        f"Arketip başına varyant: {manifest['variants_per_archetype']}",
        f"- Dönem: {manifest['periods']['start']} – {manifest['periods']['end']} "
        f"(yorumlanabilir: {manifest['periods']['commentable_from']} itibarıyla)",
        f"- Üreteç sürümü: {manifest['generator_version']} · Parametre özeti: `{manifest['config_fingerprint']}`",
        "",
        "## Hedef oranlar (docs/03) ve gerçekleşen",
        "",
        "| Ölçüt | Hedef | Gerçekleşen |",
        "|---|---|---|",
        f"| Notlanan gerçek olaylar (E01–E12) | ~%70 | {s['documented_share_real_v5']:.1%} |",
        f"| Firma notu (sezon) olan varyantlar | ~%70 | {s['season_note_share']:.1%} |",
        f"| Havuz olayı / ay | ~2 | {s['pool_events_per_month']} |",
        f"| Olaysız ay (yorumlanabilir aylar) | ~%15 | {s['quiet_month_share_commentable']:.1%} |",
        f"| Çeldirici notlu ay | %10–15 | {s['distractor_month_share']:.1%} |",
        f"| Rakamlı olay notları | ~%50 | {s['event_notes_with_numbers_share']:.1%} |",
        f"| Eşik yakını havuz olayları | ~%20 | {s['near_threshold_share_pool']:.1%} |",
        f"| Çakışan havuz olayları | ~%10 | {s['overlap_share_pool']:.1%} |",
        "",
        "A2'de V2 adayı olan yorumlanabilir aylarda beklenen karar dağılımı "
        "(cite = notla açıkla, warn = uyar, either = ikisi de kabul): "
        + ", ".join(f"{k}: {v}" for k, v in sorted(s["a2_v2_candidate_decisions"].items())),
        "",
        "## Olay türleri",
        "",
        "| Tür | Adet | Notlu |",
        "|---|---:|---:|",
    ]
    out += [f"| {t} | {v['count']} | {v['documented']} |" for t, v in s["events_by_type"].items()]

    out += ["", "## Varyantlar", "",
            "| Firma | Ad | Çalışan | Ciro 2024 | P1 | P2 | P3 | P4 | E18/yıl |",
            "|---|---|---:|---:|:-:|:-:|:-:|:-:|---|"]
    yes = lambda b: "✓" if b else "–"  # noqa: E731
    for r in results:
        v, p = r.variant, r.variant.practices
        out.append(f"| {v.firm_id} | {v.name} | {v.employees} | {_eur(v.revenue_2024)} | {yes(p.p1_sonderzahlungen)} "
                   f"| {yes(p.p2_jahrespraemien)} | {yes(p.p3_bestand)} | {yes(p.p4_afa_jahresende)} "
                   f"| {', '.join(map(str, p.p5_per_year))} |")

    out += ["", "## Kalibrasyon: v00 varyantları, 2024 taban serisi (olaysız, gürültüsüz)", "",
            "| Firma | Materialquote | Personalquote | Betriebsergebnis-Marge |", "|---|---:|---:|---:|"]
    first_year = timeline.year_indices(timeline.years[0])
    for r in results:
        if r.variant.index != 0:
            continue
        b = r.baseline[:, first_year].sum(axis=1, keepdims=True)
        sub = _subtotals(b)
        gl = sub["Gesamtleistung"][0]
        out.append(f"| {r.variant.firm_id} | {b[LINE_INDEX['material_wareneinkauf'], 0] / gl:.1%} "
                   f"| {b[LINE_INDEX['personalkosten'], 0] / gl:.1%} | {sub['Betriebsergebnis'][0] / gl:.1%} |")

    muster = next((r for r in results if r.variant.firm_id == "A1-v00"), None)
    if muster is not None:
        year = timeline.years[min(1, len(timeline.years) - 1)]
        idx = timeline.year_indices(year)
        booked = _subtotals(muster.booked[:, idx])
        true = _subtotals(muster.true[:, idx])
        out += ["", f"## Muster GmbH (A1-v00), {year}: aylık Betriebsergebnis, kaydedilen ve ekonomik gerçek", "",
                "| Ay | Kaydedilen | Gerçek | Fark |", "|---|---:|---:|---:|"]
        for k, i in enumerate(idx):
            b, t = booked["Betriebsergebnis"][k], true["Betriebsergebnis"][k]
            out.append(f"| {timeline.period(i)} | {_eur(b)} | {_eur(t)} | {_eur(b - t)} |")

    out += ["", "## Dosyalar", ""]
    out += [f"- `{f}` (modele görünür)" for f in manifest["files"]["model_input"]]
    out += [f"- `{f}` (yalnızca değerlendirme)" for f in manifest["files"]["evaluation"]]
    return "\n".join(out) + "\n"
