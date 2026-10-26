"""Veri üreteci testleri (docs/04_veri_ureteci.md, Bölüm 5)."""

import json
import re

import numpy as np
import pytest

from generator.config import load_archetypes, load_generation, load_templates
from generator.events import CATEGORY, PRIMARY_LINES, REAL_AND_V5
from generator.lines import BASE_LINES, LINE_INDEX
from generator.notes import format_eur, format_pct
from generator.pipeline import generate_run
from generator.writer import run_statistics, write_run

SEED = 42
TOL = 1e-6


@pytest.fixture(scope="module")
def run():
    return generate_run(["A1", "A2", "A3"], 10, SEED)


@pytest.fixture(scope="module")
def timeline(run):
    return run.timeline


@pytest.fixture(scope="module")
def results(run):
    return run.results


# --- Belirlenimcilik ---------------------------------------------------------------------------

def test_same_seed_same_output(results):
    again = generate_run(["A1", "A2", "A3"], 10, SEED).results
    for a, b in zip(results, again):
        assert np.array_equal(a.booked, b.booked)
        assert a.notes == b.notes
        assert a.months == b.months


def test_more_variants_do_not_change_existing_ones(results):
    small = generate_run(["A1"], 3, SEED).results
    for a, b in zip(results[:3], small):
        assert a.variant.firm_id == b.variant.firm_id
        assert np.array_equal(a.booked, b.booked)
        assert a.notes == b.notes


def test_different_seed_differs(results):
    other = generate_run(["A1"], 2, SEED + 1).results
    assert not np.array_equal(results[1].booked, other[1].booked)


# --- Seri kimlikleri ---------------------------------------------------------------------------

def test_booked_minus_true_equals_distortion_effects(results):
    """kaydedilen − gerçek = V1–V4 olaylarının etkilerinin toplamı (docs/04, Bölüm 2)."""
    for r in results:
        distortion = sum((e.deltas for e in r.events
                          if e.deltas is not None and e.category in ("V1", "V2", "V3", "V4")),
                         np.zeros_like(r.booked))
        assert np.allclose(r.booked - r.true, distortion, atol=1e-4)


def test_economic_series_equals_baseline_plus_real_events(results):
    for r in results:
        real = sum((e.deltas for e in r.events if e.category in ("R", "V5")), np.zeros_like(r.baseline))
        assert np.allclose(r.economic, r.baseline + real, atol=1e-4)


def test_distortions_keep_annual_totals(results, timeline):
    """V1–V3 yalnızca zamanlamayı kaydırır: yıllık toplamlar ekonomik gerçekle aynı kalır."""
    for r in results:
        for e in r.events:
            if e.category in ("V1", "V2", "V3") and e.shape == "periodisch":
                assert abs(e.deltas.sum()) < 1e-4, e.event_id


def test_raw_series_shape(results, timeline):
    for r in results:
        assert r.booked.shape == (len(BASE_LINES), timeline.n) == (21, 36)
        assert np.isfinite(r.booked).all()


def test_baseline_quotas_match_archetypes(results, timeline):
    """v00 taban serisi (olaysız, gürültüsüz) 2024 maliyet oranları docs/01 ile aynı."""
    archetypes = load_archetypes()
    first_year = timeline.year_indices(timeline.years[0])
    for r in results:
        if r.variant.index != 0:
            continue
        b = r.baseline[:, first_year].sum(axis=1)
        gl = b[LINE_INDEX["umsatzerloese"]] + b[LINE_INDEX["bestandsveraenderungen_fe_ue"]]
        for line, q in archetypes[r.variant.archetype.code].quotas.items():
            assert b[LINE_INDEX[line]] / gl == pytest.approx(q, abs=0.002), (r.variant.firm_id, line)


def test_muster_gmbh_profile(results):
    muster = results[0]
    p = muster.variant.practices
    assert muster.variant.firm_id == "A1-v00" and muster.variant.name == "Muster GmbH"
    assert muster.variant.employees == 55
    assert (p.p1_sonderzahlungen, p.p2_jahrespraemien, p.p3_bestand, p.p4_afa_jahresende) == (True, True, True, False)
    assert set(p.p5_per_year) == {3}


def test_employees_within_target_band(results):
    lo, hi = load_generation()["variants"]["employees_bounds"]
    assert all(lo <= r.variant.employees <= hi for r in results)


# --- Olay kayıtları ----------------------------------------------------------------------------

def test_every_event_is_complete(results, timeline):
    """Her olay eksiksiz kaydedilir: ay, satır, büyüklük, kalıcı/geçici, notlu mu (tur 2)."""
    from generator.ground_truth import event_record
    for r in results:
        for e in r.events:
            rec = event_record(e, timeline)
            assert rec["event_id"] and rec["start"] and rec["lines"]
            assert rec["duration"] in ("dauerhaft", "temporär")
            assert rec["shape"] in ("einmalig", "temporär", "dauerhaft", "periodisch")
            assert isinstance(rec["documented"], bool)
            assert rec["magnitude"], e.event_id
            if e.type != "E19":
                assert rec["effects"], e.event_id
                assert all(f["abs_at_start"] != 0 for f in rec["effects"])


def test_event_ids_unique(results):
    ids = [e.event_id for r in results for e in r.events]
    assert len(ids) == len(set(ids))


def test_accounting_distortions_are_never_documented(results):
    for r in results:
        for e in r.events:
            if e.category in ("V1", "V2", "V3", "V4"):
                assert not e.documented and e.source_id is None
                assert e.expected_treatment == "warning"


def test_documented_events_point_to_existing_notes(results):
    for r in results:
        source_ids = {n["source_id"] for n in r.notes}
        for e in r.events:
            if e.documented:
                assert e.source_id in source_ids


def test_v1_to_v4_have_expected_flags(results):
    for r in results:
        for e in r.events:
            if e.category in ("V1", "V2", "V3", "V4", "V5"):
                codes = {c for _, c, _ in e.expected_flags}
                assert e.category in codes, e.event_id


def test_trader_v2_is_booked_in_material_line(results):
    for r in results:
        for e in r.events:
            if e.type == "E16" and r.variant.kind == "trader":
                assert e.lines() == ["material_wareneinkauf"]
            if r.variant.kind == "trader":
                assert not r.booked[LINE_INDEX["bestandsveraenderungen_fe_ue"]].any()


def test_overlap_cap(results):
    """Gerçek olaylar: birincil satır ve ayda en fazla 2 olay; aynı tür aynı ayda bir kez (D8)."""
    cap = load_generation()["events"]["max_events_per_line_month"]
    for r in results:
        cells, type_starts = {}, set()
        for e in r.events:
            if e.type not in REAL_AND_V5:
                continue
            last = e.start if e.end is None else e.end
            for line in PRIMARY_LINES[e.type]:
                for m in range(e.start, last + 1):
                    cells[(line, m)] = cells.get((line, m), 0) + 1
            assert (e.type, e.start) not in type_starts, e.event_id
            type_starts.add((e.type, e.start))
        assert max(cells.values()) <= cap


# --- Notlar ------------------------------------------------------------------------------------

_GERMAN_NUMBER = re.compile(r"\d{1,3}(?:\.\d{3})+|\d+(?:,\d+)?")


def _parse(token: str) -> float:
    return float(token.replace(".", "").replace(",", "."))


def test_note_numbers_are_recorded(results):
    """Notta görünen her rakam değerlendirme kaydında var; başka rakam yok (tur 2, 3b)."""
    for r in results:
        gt = {g["source_id"]: g for g in r.notes_gt}
        for n in r.notes:
            found = sorted(_parse(t) for t in _GERMAN_NUMBER.findall(n["text"]))
            assert found == sorted(float(x) for x in gt[n["source_id"]]["numbers"]), n["text"]


def test_model_visible_note_fields(results):
    for r in results:
        for n in r.notes:
            assert set(n) == {"source_id", "firm_id", "period", "duration", "text"}
            assert n["duration"] in ("dauerhaft", "temporär")


def test_note_text_has_no_unfilled_placeholders(results):
    for r in results:
        for n in r.notes:
            assert "{" not in n["text"] and "}" not in n["text"]


def test_source_ids_unique_per_firm(results):
    for r in results:
        ids = [n["source_id"] for n in r.notes]
        assert len(ids) == len(set(ids))


def test_templates_have_four_to_five_patterns_per_type():
    t = load_templates()
    for etype in REAL_AND_V5:
        assert 4 <= len(t[etype]["with_number"]) + len(t[etype]["without_number"]) <= 5
    for code in ("A1", "A2", "A3"):
        assert 4 <= len(t["E19"][code]) <= 5


def test_templates_contain_no_literal_digits():
    t = load_templates()
    texts = [s for e in REAL_AND_V5 for k in ("with_number", "without_number") for s in t[e][k]]
    texts += [s for code in ("A1", "A2", "A3") for s in t["E19"][code]]
    texts += [d["text"] for d in t["distractor"]]
    assert not any(re.search(r"\d", s) for s in texts)


def test_number_formatting():
    assert format_eur(25000) == "25.000 €"
    assert format_pct(3.5) == "3,5 %"
    assert format_pct(7) == "7 %"


# --- Oranlar (docs/03) -------------------------------------------------------------------------

def test_rates_close_to_targets(run):
    s = run_statistics(run.results, run.timeline, run.gen)
    assert 0.60 <= s["documented_share_real_v5"] <= 0.80
    assert 0.60 <= s["season_note_share"] <= 0.80
    assert 0.08 <= s["quiet_month_share_commentable"] <= 0.25
    assert 0.07 <= s["distractor_month_share"] <= 0.18
    assert 0.35 <= s["event_notes_with_numbers_share"] <= 0.65
    assert 0.10 <= s["near_threshold_share_pool"] <= 0.30


# --- Ground truth ay kayıtları ------------------------------------------------------------------

def test_month_records_cover_series(results, timeline):
    for r in results:
        assert [m["period"] for m in r.months] == timeline.periods
        assert sum(m["commentable"] for m in r.months) == timeline.n - timeline.commentable_from


def test_v2_candidate_decision_rule(results):
    for r in results:
        for m in r.months:
            causes = m["rohertrag_causes"]
            if not causes:
                assert m["v2_candidate_decision"] is None
            elif any(c["kind"] == "distortion" for c in causes):
                assert m["v2_candidate_decision"] == "warn"
            elif all(c["documented"] for c in causes):
                assert m["v2_candidate_decision"] == "cite"
            else:
                assert m["v2_candidate_decision"] == "either"


def test_undocumented_price_events_make_v2_acceptable(results):
    for r in results:
        for e in r.events:
            if e.type in ("E04", "E05"):
                v2 = [f for f in e.acceptable_flags if f[1] == "V2"]
                assert bool(v2) != e.documented


# --- Yazılan dosyalar ---------------------------------------------------------------------------

def test_written_files_separate_model_input_and_evaluation(timeline, tmp_path):
    write_run(generate_run(["A1"], 2, SEED), tmp_path)
    model_files = {p.name for p in (tmp_path / "model_input").iterdir()}
    assert model_files == {"bwa_raw.csv", "context_notes.jsonl", "firms.json"}
    raw = (tmp_path / "model_input" / "bwa_raw.csv").read_text(encoding="utf-8")
    notes = (tmp_path / "model_input" / "context_notes.jsonl").read_text(encoding="utf-8")
    for leak in ("E0", "E1", "expected", "distractor", "documented", "V1", "V2"):
        assert leak not in raw and leak not in notes
    rows = raw.strip().splitlines()
    assert rows[0] == "firm_id,period,line,value"
    assert len(rows) - 1 == 2 * timeline.n * len(BASE_LINES)
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["seed"] == SEED
    assert set(CATEGORY) >= set(manifest["statistics"]["events_by_type"])


# --- Profiller ve dengelenmiş V2 kümesi (karar turu 4) -----------------------------------------

def test_profile_overrides_apply():
    from generator.config import load_archetypes, load_profile
    base = load_archetypes()
    over = load_archetypes(overrides=load_profile("v2_balanced")["archetypes"])
    assert base["A2"].practices["p3_bestand"] == 0.8
    assert over["A2"].practices["p3_bestand"] == 0.2
    assert over["A2"].practices["p3_mode"] == base["A2"].practices["p3_mode"]  # diğer alanlar korunur


def test_unknown_profile_is_rejected():
    with pytest.raises(ValueError):
        generate_run(["A1"], 1, SEED, profile="yok_boyle_profil")


def test_first_variant_offset_creates_new_firms(results):
    shifted = generate_run(["A1"], 2, SEED, first_variant=50).results
    assert [r.variant.firm_id for r in shifted] == ["A1-v50", "A1-v51"]
    reference_names = {r.variant.name for r in results}
    assert not reference_names & {r.variant.name for r in shifted}


def test_rohertrag_candidate_rule(results, timeline):
    from generator.v2_set import rohertrag_candidates, rohertragsquote
    pp = load_generation()["v2_candidates"]["ratio_pp"]
    for r in results[:5]:
        rq = rohertragsquote(r.booked)
        candidates = rohertrag_candidates(r.booked, timeline, pp)
        for i in range(12, timeline.n):
            both = abs(rq[i] - rq[i - 1]) >= pp and abs(rq[i] - rq[i - 12]) >= pp
            assert (i in candidates) == both


def test_balanced_set_is_balanced():
    from generator.v2_set import balanced_v2_set, rohertrag_candidates
    run = generate_run(["A2", "A3"], 4, SEED, profile="v2_balanced", first_variant=50)
    pp = run.gen["v2_candidates"]["ratio_pp"]
    selected = balanced_v2_set(run.results, run.timeline, pp, SEED)
    by_firm = {r.variant.firm_id: r for r in run.results}
    for code in ("A2", "A3"):
        items = [x for x in selected if x["archetype"] == code]
        cite = sum(x["decision"] == "cite" for x in items)
        warn = sum(x["decision"] == "warn" for x in items)
        either = sum(x["decision"] == "either" for x in items)
        assert cite == warn and either <= cite
    for x in selected:
        r = by_firm[x["firm_id"]]
        i = run.timeline.index(x["period"])
        assert i in rohertrag_candidates(r.booked, run.timeline, pp)
        assert r.months[i]["v2_candidate_decision"] == x["decision"]


def test_reference_report_shows_v2_decisions_per_archetype(run):
    s = run_statistics(run.results, run.timeline, run.gen)
    assert set(s["v2_decisions_by_archetype"]) == {"A1", "A2", "A3"}
    for entry in s["v2_decisions_by_archetype"].values():
        assert sum(entry["all"].values()) == 10 * (run.timeline.n - run.timeline.commentable_from)
        assert all(entry["candidates"][k] <= entry["all"][k] for k in entry["all"])
