"""Model metinlerinin puanlanması: doğrulama katmanı + içerik planı + ground truth (CLAUDE.md 8; docs/13).

Her metin için:
- Doğrulama katmanı (Katman 4): format, rakam değerleri, rakam biçimi, neden işaretleri, kelime sayısı.
- İçerik planı (`ideal/plan.py`): modelin gördüğü notlarla ideal yorumda hangi notların kaynak gösterileceği, hangi
  kalemlerin tabloda olacağı ve V2 adayında doğru karar. Plan ground truth'tan kurulur, ama yalnızca görünen notları
  kaynak sayar; bu yüzden aynı ay için `ohne_kontext`, `rag_k8` ve `rag_alle` planları farklıdır.
- Ground truth: beklenen ve kabul edilebilir çarpıklık uyarıları, çeldirici notlar.

Puanlama ground truth okur; modele verilen hiçbir şeyin parçası değildir.
"""

import re
from dataclasses import dataclass

from facts.schema import BASE_LINES, SUMMARY_LINES
from ideal.plan import build_plan
from validation.check import KNOWN_POSITIONS, _citations, _mentions, load_config, validate
from validation.structure import ABWEICHUNGEN, HINWEISE, parse

SCORING_VERSION = "1.1"

_CFG = load_config()
_ALIASES = _CFG["scope"]["aliases"]
_NAME_TO_LINE = {name: key for key, name in {**BASE_LINES, **SUMMARY_LINES}.items()}
# Rohertrag adayı (V2) ticarette malzeme satırına, üreticide stok satırına yazılır (docs/03, 9.1).
_V2_LINES = {"material_wareneinkauf", "bestandsveraenderungen_fe_ue"}
_ROHERTRAG = re.compile(r"Rohertrag", re.IGNORECASE)
_HYPOTHESIS = "(Hypothese)"


@dataclass
class Month:
    """Bir firma-ayın puanlama girdileri (metinden bağımsız)."""

    facts: dict
    notes: list[dict]      # modele verilen bağlam notları ({"source_id", "text", ...})
    plan: dict
    gt: dict               # ground_truth_months kaydı


def make_month(facts: dict, notes: list[dict], truth, base_normals: dict | None) -> Month:
    plan = build_plan(facts, {"notes": notes}, truth, base_normals)
    gt = truth.months[(facts["company"]["firm_id"], facts["period"])]
    return Month(facts, notes, plan, gt)


def _planned_sources(plan: dict) -> set[str]:
    out = set()
    for r in plan["tabelle"]:
        out |= set(r["erklaerung"].get("quellen", []))
    for h in plan["hinweise"]:
        out |= set(h.get("quellen", []))
    return out


def _lines_in(text: str) -> set[str]:
    """Bir uyarı maddesinde adı geçen BWA satırları (satır anahtarı). „Rohertrag(squote)“ V2 satırları sayılır."""
    names = _mentions(text, KNOWN_POSITIONS, _ALIASES)
    lines = {_NAME_TO_LINE[n] for n in names if n in _NAME_TO_LINE}
    if _ROHERTRAG.search(text):
        lines |= _V2_LINES
    return lines - {"rohertrag"}


def score_text(text: str, month: Month) -> dict:
    facts, plan, gt = month.facts, month.plan, month.gt
    report = validate(text, facts, month.notes, _CFG)
    m = report["metrics"]
    codes = [f["code"] for f in report["findings"]]
    parsed, _ = parse(text, facts["period_label"], _CFG)
    note_ids = {n["source_id"] for n in month.notes}

    # --- Kaynaklar: plana göre doğru mu? ---
    cited: list[str] = []
    for seg in parsed.segments:
        ids, _, _ = _citations(seg, note_ids)
        cited += ids
    cited_set = set(cited)
    planned = _planned_sources(plan)
    distractors = set(gt.get("distractor_notes", []))
    quellen = {"zitiert": len(cited_set), "richtig": len(cited_set & planned), "geplant": len(planned),
               "gefunden": len(planned & cited_set), "ablenkung": len(cited_set & distractors),
               "erfunden": codes.count("quelle_unbekannt"),
               "keine_notiz": codes.count("quelle_facts") + codes.count("quelle_wissen")}

    # --- Satır düzeyinde atıf (1.1): tablodaki not, planın o satır için kaynak saydığı notlardan mı? ---
    # Not düzeyindeki precision, doğru bir notun yanlış satırın nedeni yapılmasını görmez (docs/13, Bölüm 6).
    row_sources = {r["position"]: set(r["erklaerung"].get("quellen", [])) for r in plan["tabelle"]}
    row_cited = row_wrong = 0
    for seg in parsed.segments:
        if seg.kind == "zeile":
            ids = set(_citations(seg, note_ids)[0])
            row_cited += len(ids)
            row_wrong += len(ids - row_sources.get(seg.cells[0], set()))
    quellen |= {"zeile_zitiert": row_cited, "zeile_falsch": row_wrong}

    # --- Tablo: anlamlı kalemler tabloda mı, gereksiz satır var mı? ---
    rows = {name for _, name in parsed.table_positions}
    positions = {p["position"] for p in facts.get("positions", [])}
    allowed = ({r["position"] for r in plan["tabelle"]} | positions
               | {p["position"] for p in facts.get("further_significant", [])}
               | {f["position"] for f in facts.get("flags", [])})
    tabelle = {"kalemler": len(positions), "gefunden": len(positions & rows), "zeilen": len(rows),
               "ueberfluessig": len(rows - allowed)}

    # --- Çarpıklık uyarıları ---
    hinweise_text = parsed.section_text.get(HINWEISE, "")
    bullets = [b[2:] for b in hinweise_text.splitlines() if b.startswith("- ")]
    bullet_lines = [_lines_in(b) for b in bullets]
    warned = set().union(*bullet_lines) if bullet_lines else set()
    l1 = [f for f in facts.get("flags", []) if f["status"] == "hinweis"]
    expected = {(f["code"], f["line"]) for f in gt.get("expected_flags", [])}
    ok_lines = {f["line"] for f in gt.get("expected_flags", []) + gt.get("acceptable_flags", [])}
    flags = {"l1": len(l1), "l1_gefunden": sum(f["position"] in hinweise_text for f in l1),
             "gt": len(expected), "gt_gefunden": sum(line in warned for _, line in expected),
             "hinweise": len(bullets), "hinweise_richtig": sum(bool(ls & ok_lines) for ls in bullet_lines)}

    # --- V2 adayı (Rohertragsquote sıçraması): not mu, uyarı mı? ---
    v2 = None
    if plan["meta"]["v2"]:
        row = next(r for r in plan["tabelle"] if r["position"] == "Rohertragsquote")
        sources = set(row["erklaerung"].get("quellen", []))
        warns = bool(_ROHERTRAG.search(hinweise_text))
        cites = bool(sources & cited_set)
        want = plan["meta"]["v2"]["entscheidung"]
        if want == "warnung":
            ok = warns
        elif plan["meta"]["v2"]["gt"] == "either":
            ok = cites or warns
        else:
            ok = cites and not warns
        v2 = {"plan": want, "gt": plan["meta"]["v2"]["gt"], "warnt": warns, "zitiert": cites, "richtig": ok}

    return {
        "format_ok": m["format_ok"],
        "woerter": m["words"],
        "zahlen": {"geprueft": m["numbers"]["checked"], "richtig": m["numbers"]["fakt"] + m["numbers"]["notiz"],
                   "zahlenformat": codes.count("zahlenformat")},
        "begruendungen": {**m["reasons"], "hypothese_marker": text.count(_HYPOTHESIS)},
        "quellen": quellen,
        "tabelle": tabelle,
        "flags": flags,
        "v2": v2,
        "fehler": report["errors"],
        "inhaltsfehler": report["content_errors"],
        "codes": codes,
    }


# --- Toplama --------------------------------------------------------------------------------------------

def _share(a: float, b: float) -> float | None:
    return round(a / b, 3) if b else None


def aggregate(rows: list[dict]) -> dict:
    """Metin puanlarını bir varyant (ve isteğe bağlı bir alt küme) için toplar."""
    n = len(rows)
    if not n:
        return {"n": 0}
    s = lambda f: sum(f(r) for r in rows)  # noqa: E731
    reasons = s(lambda r: r["begruendungen"]["total"])
    v2 = [r["v2"] for r in rows if r["v2"]]
    return {
        "n": n,
        "format_uyumu": _share(s(lambda r: r["format_ok"]), n),
        "rakam_sadakati": _share(s(lambda r: r["zahlen"]["richtig"]), s(lambda r: r["zahlen"]["geprueft"])),
        "binlik_bosluk_metin": _share(s(lambda r: r["zahlen"]["zahlenformat"] > 0), n),
        "kelime_ort": round(s(lambda r: r["woerter"]) / n, 1),
        "kelime_hedefte": _share(s(lambda r: 200 <= r["woerter"] <= 400), n),
        "neden_metin_basi": round(reasons / n, 2),
        "neden_kaynakli": _share(s(lambda r: r["begruendungen"]["with_source"]), reasons),
        "neden_hipotez": _share(s(lambda r: r["begruendungen"]["with_hypothesis"]), reasons),
        "neden_isaretsiz": _share(s(lambda r: r["begruendungen"]["unmarked"]), reasons),
        "isaretsiz_neden_metin_basi": round(s(lambda r: r["begruendungen"]["unmarked"]) / n, 2),
        "kaynak_precision": _share(s(lambda r: r["quellen"]["richtig"]), s(lambda r: r["quellen"]["zitiert"])),
        "kaynak_recall": _share(s(lambda r: r["quellen"]["gefunden"]), s(lambda r: r["quellen"]["geplant"])),
        "satir_atif_isabeti": _share(s(lambda r: r["quellen"]["zeile_zitiert"] - r["quellen"]["zeile_falsch"]),
                                     s(lambda r: r["quellen"]["zeile_zitiert"])),
        "yanlis_satir_atif_metin": _share(s(lambda r: r["quellen"]["zeile_falsch"] > 0), n),
        "celdirici_atif": s(lambda r: r["quellen"]["ablenkung"]),
        "uydurma_kaynak_metin": _share(s(lambda r: r["quellen"]["erfunden"] > 0), n),
        "sapma_yakalama": _share(s(lambda r: r["tabelle"]["gefunden"]), s(lambda r: r["tabelle"]["kalemler"])),
        "gereksiz_satir_metin_basi": round(s(lambda r: r["tabelle"]["ueberfluessig"]) / n, 2),
        "uyari_recall_l1": _share(s(lambda r: r["flags"]["l1_gefunden"]), s(lambda r: r["flags"]["l1"])),
        "uyari_recall_gt": _share(s(lambda r: r["flags"]["gt_gefunden"]), s(lambda r: r["flags"]["gt"])),
        "uyari_precision_gt": _share(s(lambda r: r["flags"]["hinweise_richtig"]), s(lambda r: r["flags"]["hinweise"])),
        "v2_n": len(v2),
        "v2_dogru": _share(sum(v["richtig"] for v in v2), len(v2)),
        "v2_quelle_n": sum(v["plan"] == "quelle" for v in v2),
        "v2_quelle_dogru": _share(sum(v["richtig"] for v in v2 if v["plan"] == "quelle"),
                                  sum(v["plan"] == "quelle" for v in v2)),
        "hatasiz_metin": _share(s(lambda r: r["fehler"] == 0), n),
    }
