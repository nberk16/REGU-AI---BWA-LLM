"""Katman 1 (facts) testleri (docs/05_facts_semasi.md)."""

import json
import statistics

import numpy as np
import pytest

from facts.build import build_facts, commentable_periods
from facts.schema import BASE_LINES, RESULT_LINES, add_subtotals, load_config
from facts.series import load_run
from generator.lines import BASE_LINES as GENERATOR_LINES
from generator.pipeline import generate_run
from generator.v2_set import rohertrag_candidates
from generator.writer import write_run

SEED = 42


@pytest.fixture(scope="module")
def run_dir(tmp_path_factory):
    path = tmp_path_factory.mktemp("run")
    run = generate_run(["A1", "A2", "A3"], 2, SEED)
    write_run(run, path)
    return path, run


@pytest.fixture(scope="module")
def firms(run_dir):
    return load_run(run_dir[0])


@pytest.fixture(scope="module")
def cfg():
    return load_config()


@pytest.fixture(scope="module")
def all_facts(firms, cfg):
    return [build_facts(fs, p, cfg) for fs in firms.values() for p in commentable_periods(fs)]


def _walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]")
    else:
        yield path, obj


def test_line_contract_matches_generator():
    assert tuple(BASE_LINES) == GENERATOR_LINES


def test_top_level_schema(all_facts, cfg):
    keys = ["schema_version", "company", "period", "period_label", "comparisons", "thresholds",
            "summary", "positions", "further_significant", "ratios", "flags"]
    for f in all_facts:
        assert list(f) == keys
        assert f["schema_version"] == cfg["schema_version"] == "1.0"
        assert f["thresholds"]["significance_basis"] == "previous_year_month"


def test_number_formats(all_facts):
    """Tutarlar tam sayı €, yüzde ve yüzde puanları 1 ondalık."""
    for f in all_facts[:200]:
        for path, value in _walk(f):
            leaf = path.rsplit(".", 1)[-1]
            if leaf in ("actual", "value", "delta_abs", "normal_level", "previous_year",
                        "position_abs_eur", "cumulative_abs_eur") and not path.startswith(".ratios"):
                assert isinstance(value, int), path
            if leaf in ("delta_pct", "delta_pp") or (path.startswith(".ratios") and leaf in ("actual", "value", "previous_year")):
                assert value is None or round(value, 1) == value, path


def test_positions_ranked_and_capped(all_facts, cfg):
    max_positions = cfg["thresholds"]["max_positions"]
    for f in all_facts:
        positions = f["positions"]
        assert len(positions) <= max_positions
        assert [p["rank"] for p in positions] == list(range(1, len(positions) + 1))
        sizes = [abs(p["previous_year_month"]["delta_abs"]) for p in positions]
        assert sizes == sorted(sizes, reverse=True)
        assert all(p["previous_year_month"]["significant"] for p in positions)
        assert all(p["significance"]["basis"] == "previous_year_month" for p in positions)
        if f["further_significant"]:
            assert len(positions) == max_positions
            assert f["further_significant"][0]["rank"] == max_positions + 1


def test_only_previous_year_month_drives_significance(firms, cfg):
    """Önceki ay ve kümülatif sıralamaya girmez (karar turu 5)."""
    fs = next(iter(firms.values()))
    for period in commentable_periods(fs):
        f = build_facts(fs, period, cfg)
        listed = {p["key"] for p in f["positions"]} | {p["key"] for p in f["further_significant"]}
        i = fs.index(period)
        thr = 0.005 * abs(fs.values["gesamtleistung"][i])
        for key in BASE_LINES:
            a, b = fs.values[key][i], fs.values[key][i - 12]
            if a == b == fs.values[key][i - 1] == 0:
                continue
            d = a - b
            small_or_sign = b == 0 or abs(b) < thr or a * b < 0
            sig = abs(d) >= thr and (small_or_sign or abs(d / abs(b)) * 100 >= 10.0)
            assert (key in listed) == sig, (period, key)


def test_delta_pct_null_rules(all_facts):
    for f in all_facts:
        thr, thr_cum = f["thresholds"]["position_abs_eur"], f["thresholds"]["cumulative_abs_eur"]
        for item in f["summary"] + f["positions"]:
            if item["key"] in RESULT_LINES:
                assert item["previous_month"]["delta_pct"] is None
                assert item["previous_year_month"]["delta_pct"] is None
                assert item["cumulative"]["delta_pct"] is None
                continue
            a = item["actual"]
            for name in ("previous_month", "previous_year_month"):
                b = item[name]["value"]
                if abs(b) < thr - 1 or a * b < 0:
                    assert item[name]["delta_pct"] is None, (item["key"], name)
            c = item["cumulative"]
            if abs(c["previous_year"]) < thr_cum - 1:
                assert c["delta_pct"] is None


def test_normal_level_is_median_of_previous_12_months(firms, cfg):
    fs = next(iter(firms.values()))
    period = commentable_periods(fs)[5]
    i = fs.index(period)
    f = build_facts(fs, period, cfg)
    for item in f["summary"]:
        expected = statistics.median(fs.values[item["key"]][i - 12:i])
        assert item["normal_level"] == int(round(expected))


def test_subtotal_rules():
    """Ara toplam kuralları docs/02, Bölüm 3 ile aynı."""
    sample = {"umsatzerloese": 100.0, "bestandsveraenderungen_fe_ue": 10.0, "aktivierte_eigenleistungen": 0.0,
              "material_wareneinkauf": 40.0, "sonstige_betriebliche_erloese": 5.0, "zinsaufwand": 2.0,
              "sonstiger_neutraler_aufwand": 0.0, "zinsertraege": 1.0, "sonstiger_neutraler_ertrag": 0.0,
              "steuern_einkommen_ertrag": 3.0}
    sample.update({k: 4.0 for k in BASE_LINES if k not in sample})
    v = add_subtotals(sample)
    assert v["gesamtleistung"] == 110.0 and v["rohertrag"] == 70.0
    assert v["gesamtkosten"] == 44.0 and v["betriebsergebnis"] == 31.0
    assert v["ergebnis_vor_steuern"] == 30.0 and v["vorlaeufiges_ergebnis"] == 27.0


def test_rohertrag_candidate_matches_generator_rule(run_dir, firms, cfg):
    """Katman 1'in nötr adayı, üretecin ground truth için kullandığı kuralla aynı aylarda çıkar."""
    _, run = run_dir
    pp = run.gen["v2_candidates"]["ratio_pp"]
    assert pp == cfg["thresholds"]["ratio_pp"]
    for r in run.results:
        fs = firms[r.variant.firm_id]
        expected = {run.timeline.period(i) for i in rohertrag_candidates(r.booked, run.timeline, pp)}
        found = {p for p in commentable_periods(fs)
                 if any(x["rule"] == "rohertrag_sprung" for x in build_facts(fs, p, cfg)["flags"])}
        assert found == expected, r.variant.firm_id


def test_flags_are_neutral(all_facts):
    for f in all_facts:
        for flag in f["flags"]:
            assert set(flag) == {"code", "status", "rule", "position", "evidence"}
            assert flag["status"] == ("kandidat" if flag["rule"] == "rohertrag_sprung" else "hinweis")


def test_no_ground_truth_leakage(all_facts):
    text = json.dumps(all_facts, ensure_ascii=False)
    for leak in ("event_id", "expected", "acceptable", "documented", "\"cite\"", "\"warn\"", "-E0", "-E1"):
        assert leak not in text


def test_facts_need_previous_year(firms, cfg):
    fs = next(iter(firms.values()))
    with pytest.raises(ValueError):
        build_facts(fs, fs.periods[11], cfg)


def test_cli_writes_one_line_per_commentable_month(run_dir, tmp_path):
    from facts.cli import main
    out = tmp_path / "facts.jsonl"
    main(["--run", str(run_dir[0]), "--out", str(out)])
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 6 * 24
    assert json.loads(lines[0])["schema_version"] == "1.0"


def test_docs_example_matches_reference(cfg):
    """docs/examples/facts_A1-v00_2025-06.json referans koşudan üretilmiştir ve güncel kalmalıdır."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    example = json.loads((root / "docs/examples/facts_A1-v00_2025-06.json").read_text(encoding="utf-8"))
    firms = load_run(root / "data/synthetic/reference_seed42")
    assert build_facts(firms["A1-v00"], "2025-06", cfg) == example


def test_values_are_finite_and_no_negative_zero(all_facts):
    for f in all_facts[:200]:
        for path, value in _walk(f):
            if isinstance(value, float):
                assert np.isfinite(value), path
                assert not (value == 0 and str(value).startswith("-")), path
