"""Öğretmen metninin kontrolü: doğrulama katmanı + plana uygunluk (karma yöntemin 3. adımı; docs/11, Bölüm 4).

Bir metin ancak (1) doğrulama katmanında hiçbir `fehler` bulgusu yoksa ve (2) planın bütün maddelerini içerip
planda olmayan bir kaynak eklemiyorsa kabul edilir. Yalnızca standart kütüphane ve proje paketleri (numpy yok):
kullanıcının dizüstündeki betikte de çalışır.
"""

import re

from validation.check import load_config, validate
from validation.structure import ABWEICHUNGEN, CITATION, FRAGEN, HINWEISE, KERNAUSSAGEN, parse

_CFG = load_config()
# [ÖNERİ] Uzunluk: hedef ~250–350 kelime (B4). Kabul aralığı 180–400: az maddeli planlarda öğretmen metni kendi
# yorumuyla uzatmasın (pilot 2; docs/11, Bölüm 11).
WORDS_MIN, WORDS_MAX = 180, 400

# Öğretmenin eklememesi gereken değerlendirme, çıkarım ve öneri kalıpları (pilot 2'de görüldü).
_EVALUATIVE = re.compile(r"Handlungsbedarf|empfehl|Maßnahme|Kostenkontrolle|unterstreich|verdeutlich|signalisier|"
                         r"kompensier|Prognose|erfreulich|besorgnis|folgt auf|Notwendigkeit", re.IGNORECASE)
# Açıklama hücresinde içerik olmayan yazımlar: plan etiketi, yalnızca yön.
_META = re.compile(r"Ursache mit Quelle|Inhalt aus|Letzte Spalte|Spalte Erklärung|→")
_DIRECTION_ONLY = {"gestiegen", "gesunken", "anstieg", "rückgang", "erhöht", "gesenkt", "höher", "niedriger"}
# Kaynak gösteren cümlede notun içeriğinden bir kelime geçmeli; satır adları, aylar ve genel kelimeler sayılmaz.
_WORD = re.compile(r"[A-Za-zÄÖÜäöüß]{5,}")
_STOP = {w[:5] for w in (
    "Januar Februar April Juni Juli August September Oktober November Dezember Monat Monate Vormonat Vorjahr "
    "Vorjahresmonat Kontextnotiz Quelle gegenüber unsere unserem unseren etwa rund deutlich Bereich ab seit "
    "Umsatzerlöse Material Wareneinkauf Personalkosten Raumkosten Abschreibungen Reparatur Instandhaltung Kosten "
    "Gesamtleistung Rohertrag Rohertragsquote Betriebsergebnis Ertrag Aufwand Bestandsveränderungen Versicherungen "
    "Beiträge Fahrzeugkosten Werbekosten Reisekosten Warenabgabe Sonstige Sonstiger Erlöse Steuern Zinsaufwand "
    "Zinserträge Prozent Prozentpunkte").split()}


def _stems(text: str) -> set[str]:
    return {w.lower()[:5] for w in _WORD.findall(text)} - {s.lower() for s in _STOP}


def planned_sources(plan: dict) -> set[str]:
    out = set()
    for r in plan["tabelle"]:
        out |= set(r["erklaerung"].get("quellen", []))
    for h in plan["hinweise"]:
        out |= set(h.get("quellen", []))
    return out


def cited_sources(text: str) -> set[str]:
    return {s.strip() for m in CITATION.finditer(text) for s in m.group(1).split(";") if s.strip()}


def _source_content(parsed, plan: dict) -> list[str]:
    """Kaynak gösteren her cümle/satır, kaynağın içeriğinden en az bir kelime içermeli (yalnızca atıf yetmez)."""
    problems = []
    for seg in parsed.segments:
        cited = {c for m in CITATION.finditer(seg.text) for c in (x.strip() for x in m.group(1).split(";"))
                 if c in plan["notizen"]}
        if not cited:
            continue
        body = (seg.cells[4] if seg.kind == "zeile" else CITATION.sub(" ", seg.text)).lower()
        # Notun kök kelimesi metinde herhangi bir yerde geçebilir: birleşik kelimeler („Großkunden“ ↔ „Kunde“).
        if not any(stem in body for c in cited for stem in _stems(plan["notizen"][c])):
            where = f"Tabelle, {seg.cells[0]}" if seg.kind == "zeile" else f"„{seg.text[:160]}“"
            problems.append(f"{where}: Die Ursache aus {', '.join(sorted(cited))} wird nicht genannt; nenne sie in "
                            f"eigenen Worten aus dem Inhalt der Notiz.")
    return problems


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
            last, expl = seg.cells[-1], seg.cells[4]
            art = r["erklaerung"]["art"]
            if art != "offen" and (not expl.strip(" .–-") or _META.search(expl)
                                   or expl.strip(" .").lower() in _DIRECTION_ONLY):
                problems.append(f"Tabelle, {r['position']}: Die Spalte Erklärung nennt die Ursache in wenigen Wörtern "
                                f"(nicht leer, kein Planhinweis, nicht nur die Richtung); gefunden: „{expl}“.")
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

    problems += _source_content(parsed, plan)
    for seg in parsed.segments:
        if _EVALUATIVE.search(seg.text):
            problems.append(f"Keine eigenen Bewertungen, Schlussfolgerungen oder Empfehlungen: „{seg.text[:200]}“.")

    lo, hi = WORDS_MIN, WORDS_MAX
    words = report["metrics"]["words"]
    if not lo <= words <= hi:
        problems.append(f"Länge ohne Tabelle {words} Wörter; Ziel 250–350. "
                        + ("Ergänze ganze Sätze mit Einordnung (Vorjahr, kumuliert, Folge der Verzerrungen), ohne neue "
                           "Inhalte." if words < lo else "Kürze, ohne Punkte des Plans wegzulassen."))
    if ABWEICHUNGEN not in parsed.section_text:
        problems.append("Der Abschnitt „Abweichungen im Detail“ fehlt.")
    return {"ok": not problems, "problems": problems, "report": report}
