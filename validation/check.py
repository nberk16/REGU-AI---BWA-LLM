"""Doğrulama: rakamlar, kaynaklar, hipotez işaretleri, format ve kapsam (docs/07)."""

import re
import tomllib
from pathlib import Path

from facts.schema import BASE_LINES, RATIOS, SUMMARY_LINES

from . import numbers as N
from .structure import ABWEICHUNGEN, BRACKET, HINWEISE, Finding, Segment, parse

CONFIG_PATH = Path(__file__).parent / "config.toml"

KNOWN_POSITIONS = set(BASE_LINES.values()) | set(SUMMARY_LINES.values()) | set(RATIOS) | {
    "Betrieblicher Rohertrag", "Neutraler Aufwand", "Neutraler Ertrag"}

# Bir satır adı geçtiğinde ona ait oran da kapsama girer (ör. "Material-/Wareneinkauf … Quote von 43,4 %").
_LINE_NAMES = {**BASE_LINES, **SUMMARY_LINES}
RATIO_OF_LINE = {_LINE_NAMES[key]: ratio for ratio, key in RATIOS.items()}

_DASHES = {"", "-", "–", "—"}

# Biçim bulguları ("Format uyumu" metriği). Geri kalan "fehler" bulguları içerikle ilgilidir.
FORMAT_CODES = frozenset({
    "periode", "ueberschrift_unbekannt", "abschnitt_doppelt", "text_ausserhalb", "abschnitt_fehlt",
    "abschnitt_reihenfolge", "abschnitt_leer", "kernaussagen_anzahl", "kernaussagen_format", "tabellenkopf",
    "tabelle_leer", "tabellenzeile", "liste_format", "frage_format", "position_unbekannt", "quellenformat",
    "zahlenformat"})


def load_config(path: Path | None = None) -> dict:
    with open(path or CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def _word_pattern(words: list[str]) -> re.Pattern:
    parts = []
    for w in words:
        if w.startswith("*"):
            parts.append(r"\w*" + re.escape(w[1:]) + r"\b")
        else:
            parts.append(r"\b" + re.escape(w) + (r"\b" if w[-1].isalnum() else ""))
    return re.compile("|".join(parts), re.IGNORECASE)


# facts.json'a yapılan atıflar ("FACTS", "Flag V2", "V5"): kaynak sayılmaz (rakamlar zaten facts'ten gelir).
_FACT_REF = re.compile(r"^(?:FACTS?(?:\.\w+)*|(?:Flag\s+)?V[1-6])$", re.IGNORECASE)
# Katman 2'nin genel bilgisi (K-A, K-B; istem 1.1'de WISSEN): firma hakkında bilgi değil, neden kaynağı sayılmaz.
# Bu bilgiden türetilen neden (Hypothese) ile işaretlenir (docs/06, B3; docs/10, Bölüm 2).
_WISSEN_REF = re.compile(r"^(?:WISSEN|BWA-Erläuterung\b.*|Leitfaden\b.*)$", re.IGNORECASE)
_SHORT_ID = re.compile(r"^\d{4}-\d{2}(?: #\d+)?$")


def _citations(seg: Segment, note_ids: set[str]) -> tuple[list[str], list[tuple[str, str]], str]:
    """Bir kontrol birimindeki kaynak gösterimleri (docs/07, Bölüm 4).

    Kanonik biçim `[Quelle: A; B]`. "Quelle:" öneki olmadan köşeli parantez içinde verilen bilinen kimlikler
    ve kısaltmalar ("[Kontextnotiz 2025-03 #3; 2024-11]") de kaynak sayılır, ama biçim bulgusu alır.
    Döner: (notlara çözülen kimlikler, [(bulgu kodu, metin)], kaynakları silinmiş metin).
    """
    cited: list[str] = []
    issues: list[tuple[str, str]] = []
    spans: list[tuple[int, int]] = []
    candidates = [(m.start(), m.end(), m.group(1)) for m in BRACKET.finditer(seg.text)]
    if seg.kind == "zeile" and "[" not in seg.cells[-1] and seg.cells[-1] not in _DASHES:
        candidates.append((-1, -1, seg.cells[-1]))     # tablo: köşeli parantezsiz kaynak sütunu
    for start, end, inner in candidates:
        content = inner.strip()
        canonical = content.startswith("Quelle:")
        parts = [s.strip() for s in re.split(r"[;,]", content.removeprefix("Quelle:")) if s.strip()]
        resolved, facts_refs, wissen_refs, unknown = [], [], [], []
        for part in parts:
            if part in note_ids:
                resolved.append(part)
            elif _SHORT_ID.match(part) and f"Kontextnotiz {part}" in note_ids:
                resolved.append(f"Kontextnotiz {part}")
            elif _FACT_REF.match(part):
                facts_refs.append(part)
            elif _WISSEN_REF.match(part):
                wissen_refs.append(part)
            else:
                unknown.append(part)
        if not canonical and not resolved and not facts_refs and not wissen_refs:
            continue                                    # kaynak değil (ör. "[sic]", "Hypothese")
        if start >= 0:
            spans.append((start, end))
        cited.extend(resolved)
        issues += ([("quelle_facts", r) for r in facts_refs] + [("quelle_wissen", r) for r in wissen_refs]
                   + [("quelle_unbekannt", u) for u in unknown])
        if not canonical and resolved:
            issues.append(("quellenformat", inner))
    body = seg.text
    for start, end in spans:
        body = body[:start] + " " * (end - start) + body[end:]
    return cited, issues, body


def validate(text: str, facts: dict, notes: list[dict], cfg: dict | None = None) -> dict:
    """Yorum metnini denetler. `notes`: modele verilen bağlam notları ({"source_id", "text", ...})."""
    cfg = cfg or load_config()
    rs = cfg["reasons"]
    causal = _word_pattern(rs["causal_words"])
    speculative = _word_pattern(rs["speculative_words"])
    unknown = _word_pattern(rs["unknown_cause_phrases"])
    marker = rs["hypothesis_marker"]

    parsed, findings = parse(text, facts["period_label"], cfg)
    fact_values = N.facts_values(facts)
    names = N.scopes(fact_values)
    aliases = cfg["scope"]["aliases"]
    note_values = {n["source_id"]: N.values_from_text(n["text"], n["source_id"]) for n in notes}

    numbers_out: list[dict] = []
    reasons = {"total": 0, "with_source": 0, "with_hypothesis": 0, "unmarked": 0}

    for seg in parsed.segments:
        cited, issues, body = _citations(seg, set(note_values))
        for code, ref in issues:
            message = {
                "quelle_unbekannt": f"Quelle „{ref}“ wurde nicht bereitgestellt.",
                "quelle_facts": f"„{ref}“ ist keine Quelle; Zahlen aus FACTS brauchen keine Quellenangabe.",
                "quelle_wissen": f"„{ref}“ ist allgemeines Wissen, keine Quelle für eine Ursache im Unternehmen; "
                                 f"daraus abgeleitete Ursachen als (Hypothese) kennzeichnen.",
                "quellenformat": f"Quellenangabe „[{ref}]“ nicht im Format [Quelle: …].",
            }[code]
            severity = "hinweis" if code in ("quelle_facts", "quelle_wissen") else "fehler"
            findings.append(Finding(severity, code, message, seg.section, seg.line, ref))
        has_hyp = marker in body or (seg.kind == "zeile" and "Hypothese" in seg.cells[-1])

        # Rakamlar
        for bad in N.non_german(body):
            findings.append(Finding("fehler", "zahlenformat",
                                    f"„{bad}“ ist kein deutsches Zahlenformat (Dezimalkomma verwenden).",
                                    seg.section, seg.line, bad))
        mentioned = _mentions(seg.context or seg.text, names, aliases)
        pool = [v for v in fact_values if v.scope is None or v.scope in mentioned] if mentioned else fact_values
        for num in N.extract(body):
            status, detail = _number_status(num, seg, pool, fact_values, note_values, cited)
            numbers_out.append({"text": num.raw, "section": seg.section, "line": seg.line, "status": status})
            if detail:
                findings.append(detail)

        # Nedenler
        if seg.kind == "zeile":
            explanation = seg.cells[4]
            if explanation in _DASHES or unknown.search(explanation):
                continue
            reasons["total"] += 1
            if cited:
                reasons["with_source"] += 1
            elif has_hyp:
                reasons["with_hypothesis"] += 1
            else:
                reasons["unmarked"] += 1
                findings.append(Finding("fehler", "tabelle_ohne_quelle",
                                        "Erklärung ohne [Quelle: …] oder „Hypothese“ in der letzten Spalte.",
                                        seg.section, seg.line, seg.cells[0]))
        elif seg.kind == "satz":
            is_reason = bool(causal.search(body)) or (seg.section != HINWEISE and bool(speculative.search(body)))
            if not is_reason or unknown.search(body):
                continue
            reasons["total"] += 1
            if cited:
                reasons["with_source"] += 1
            elif has_hyp:
                reasons["with_hypothesis"] += 1
            else:
                reasons["unmarked"] += 1
                findings.append(Finding("fehler", "begruendung_ohne_kennzeichnung",
                                        f"Begründung ohne [Quelle: …] oder {marker}.", seg.section, seg.line, seg.text))

    # Tablo konumları ve kapsam
    for no, name in parsed.table_positions:
        if name not in KNOWN_POSITIONS:
            findings.append(Finding("fehler", "position_unbekannt", f"„{name}“ ist keine BWA-Zeile oder Kennzahl.",
                                    ABWEICHUNGEN, no, name))
    for p in facts.get("positions", []):
        if p["position"] not in text:
            findings.append(Finding("hinweis", "position_fehlt",
                                    f"Wesentliche Abweichung „{p['position']}“ (Rang {p['rank']}) wird nicht erwähnt.",
                                    ABWEICHUNGEN, text=p["position"]))
    hinweise = parsed.section_text.get(HINWEISE, "")
    for flag in facts.get("flags", []):
        if flag["status"] == "hinweis" and flag["position"] not in hinweise:
            findings.append(Finding("hinweis", "flag_fehlt",
                                    f"Hinweis {flag['code']} zu „{flag['position']}“ fehlt im Abschnitt Hinweise.",
                                    HINWEISE, text=flag["position"]))

    counts = {s: sum(1 for n in numbers_out if n["status"] == s)
              for s in ("fakt", "notiz", "ausgenommen", "unbelegt", "notiz_ohne_quelle", "vorzeichen", "einheit")}
    checked = sum(counts.values()) - counts["ausgenommen"]
    errors = [f for f in findings if f.severity == "fehler"]
    return {
        "ok": not errors,
        "errors": len(errors),
        "content_errors": sum(1 for f in errors if f.code not in FORMAT_CODES),
        "hints": len(findings) - len(errors),
        "metrics": {
            "numbers": {**counts, "checked": checked,
                        "fidelity": round((counts["fakt"] + counts["notiz"]) / checked, 3) if checked else None},
            "reasons": reasons,
            "words": parsed.words,
            "format_ok": not any(f.code in FORMAT_CODES for f in errors),
        },
        "findings": [f.as_dict() for f in findings],
        "numbers": numbers_out,
    }


def _mentions(text: str, names: set[str], aliases: dict[str, str]) -> set[str]:
    found = {n for n in names if n in text}
    found |= {canon for alias, canon in aliases.items() if alias in text and canon in names}
    return found | {RATIO_OF_LINE[n] for n in found if RATIO_OF_LINE.get(n) in names}


def _number_status(num: N.Num, seg: Segment, pool, fact_values, note_values, cited) -> tuple[str, Finding | None]:
    """`pool`: cümlede adı geçen satırların değerleri (+ genel eşikler); ad geçmiyorsa bütün facts değerleri."""
    if N.is_year(num) or seg.kind == "ueberschrift":
        return "ausgenommen", None
    units = N.COMPATIBLE[num.unit]
    facts_hit = N.matching(num, pool, units)
    if facts_hit:
        if N.sign_consistent(num, facts_hit):
            return "fakt", None
        return "vorzeichen", Finding("fehler", "vorzeichen", f"Vorzeichen von „{num.raw}“ widerspricht facts.json.",
                                     seg.section, seg.line, num.raw)
    note_units = units + ((N.COUNT,) if num.unit == N.PLAIN else ())
    for sid in cited:
        if N.matching(num, note_values.get(sid, []), note_units):
            return "notiz", None
    other = [sid for sid, vals in note_values.items() if sid not in cited and N.matching(num, vals, note_units)]
    if other:
        return "notiz_ohne_quelle", Finding(
            "fehler", "zahl_notiz_ohne_quelle",
            f"„{num.raw}“ stammt aus {', '.join(other)}, aber der Satz nennt diese Quelle nicht.",
            seg.section, seg.line, num.raw)
    confusable = N.CONFUSABLE.get(num.unit)
    if confusable and N.matching(num, pool, confusable):
        other_unit = "Prozentpunkte" if num.unit == N.PCT else "Prozent"
        return "einheit", Finding("fehler", "einheit", f"„{num.raw}“ passt nur als {other_unit}.",
                                  seg.section, seg.line, num.raw)
    if pool is not fact_values and N.matching(num, fact_values, units):
        return "unbelegt", Finding("fehler", "zahl_falsche_position",
                                   f"„{num.raw}“ steht in facts.json, aber nicht bei der genannten Position.",
                                   seg.section, seg.line, num.raw)
    return "unbelegt", Finding("fehler", "zahl_unbelegt",
                               f"„{num.raw}“ ist weder in facts.json noch in einer zitierten Quelle belegt.",
                               seg.section, seg.line, num.raw)
