"""Öğretmen metninin kontrolü: doğrulama katmanı + plana uygunluk (karma yöntemin 3. adımı; docs/11, Bölüm 4).

Bir metin ancak (1) doğrulama katmanında hiçbir `fehler` bulgusu yoksa ve (2) planın bütün maddelerini içerip
planda olmayan bir kaynak eklemiyorsa kabul edilir. Yalnızca standart kütüphane ve proje paketleri (numpy yok):
kullanıcının dizüstündeki betikte de çalışır.
"""

import re

from validation.check import load_config, validate
from validation.structure import ABWEICHUNGEN, CITATION, FRAGEN, HINWEISE, KERNAUSSAGEN, parse

# [ÖNERİ] Uzunluk: hedef 250–350 kelime (B4); kabul aralığı doğrulama katmanının toleransıyla aynı (±50).
_CFG = load_config()


def planned_sources(plan: dict) -> set[str]:
    out = set()
    for r in plan["tabelle"]:
        out |= set(r["erklaerung"].get("quellen", []))
    for h in plan["hinweise"]:
        out |= set(h.get("quellen", []))
    return out


def cited_sources(text: str) -> set[str]:
    return {s.strip() for m in CITATION.finditer(text) for s in m.group(1).split(";") if s.strip()}


def check(text: str, plan: dict, facts: dict, notes: list[dict]) -> dict:
    """{"ok", "problems": [Almanca], "report": doğrulama raporu}. `notes`: öğrenci modelin gördüğü notlar."""
    report = validate(text, facts, notes, _CFG)
    problems = [f["message"] + (f" Betroffen: „{f['text'][:200]}“" if f.get("text") and f["text"] not in f["message"]
                                else "")
                for f in report["findings"] if f["severity"] == "fehler"]

    parsed, _ = parse(text, facts["period_label"], _CFG)
    rows = [s for s in parsed.segments if s.kind == "zeile"]
    got = [s.cells[0] for s in rows]
    want = [r["position"] for r in plan["tabelle"]]
    if got != want:
        problems.append(f"Tabellenzeilen müssen genau diese Positionen in dieser Reihenfolge enthalten: "
                        f"{', '.join(want) or 'keine'} (gefunden: {', '.join(got) or 'keine'}).")
    else:
        for seg, r in zip(rows, plan["tabelle"]):
            want_cells = [r["ist"], r["vergleich"], r["abweichung"]]
            if [c.replace("\u00a0", " ") for c in seg.cells[1:4]] != want_cells:
                problems.append(f"Tabelle, {r['position']}: Ist, Vergleich und Abweichung genau so übernehmen: "
                                f"{' | '.join(want_cells)}.")
            last = seg.cells[-1]
            art = r["erklaerung"]["art"]
            if art == "quelle" and not all(q in last for q in r["erklaerung"]["quellen"]):
                problems.append(f"Tabelle, {r['position']}: letzte Spalte braucht "
                                f"[Quelle: {'; '.join(r['erklaerung']['quellen'])}].")
            elif art == "hypothese" and "Hypothese" not in last:
                problems.append(f"Tabelle, {r['position']}: letzte Spalte muss „Hypothese“ lauten.")
            elif art == "offen" and ("offen" not in seg.cells[4] or "Quelle" in last or "Hypothese" in last):
                problems.append(f"Tabelle, {r['position']}: Erklärung „Ursache offen“, letzte Spalte „–“.")

    want_src, got_src = planned_sources(plan), cited_sources(text)
    if want_src - got_src:
        problems.append(f"Diese Quellen fehlen: {', '.join(sorted(want_src - got_src))}.")
    if got_src - want_src:
        problems.append(f"Diese Quellen stehen nicht im Plan und dürfen nicht genannt werden: "
                        f"{', '.join(sorted(got_src - want_src))}.")

    hinweise = parsed.section_text.get(HINWEISE, "")
    for h in plan["hinweise"]:
        if h["position"] not in hinweise:
            problems.append(f"Im Abschnitt Hinweise fehlt der Punkt „- {h['position']}: …“ (Positionsname genau so).")
    if not plan["hinweise"] and hinweise.strip() and hinweise.strip() != _CFG["format"]["empty_marker"]:
        problems.append("Der Abschnitt Hinweise muss „Keine.“ enthalten.")

    questions = [s for s in parsed.segments if s.kind == "frage" and s.section == FRAGEN]
    if len(questions) != len(plan["fragen"]):
        problems.append(f"Offene Fragen: genau {len(plan['fragen'])} (wie im Plan), der Text enthält {len(questions)}.")

    kern = [s for s in parsed.segments if s.section == KERNAUSSAGEN and s.kind == "satz"]
    if kern and len(re.findall(r"^\d+\.\s", parsed.section_text.get(KERNAUSSAGEN, ""), re.M)) \
            < len(plan["kernaussagen"]):
        problems.append(f"Die Kernaussagen müssen {len(plan['kernaussagen'])} nummerierte Punkte enthalten.")

    f = _CFG["format"]
    lo, hi = f["words_min"] - f["words_tolerance"], f["words_max"] + f["words_tolerance"]
    words = report["metrics"]["words"]
    if not lo <= words <= hi:
        problems.append(f"Länge ohne Tabelle {words} Wörter; Ziel 250–350. "
                        + ("Ergänze ganze Sätze mit Einordnung (Vorjahr, kumuliert, Folge der Verzerrungen), ohne neue "
                           "Inhalte." if words < lo else "Kürze, ohne Punkte des Plans wegzulassen."))
    if ABWEICHUNGEN not in parsed.section_text:
        problems.append("Der Abschnitt „Abweichungen im Detail“ fehlt.")
    return {"ok": not problems, "problems": problems, "report": report}
