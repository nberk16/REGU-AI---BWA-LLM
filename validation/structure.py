"""Yorum metninin yapısı: bölümler, tablo, cümleler ve format kontrolü (docs/07, Bölüm 2)."""

import re
from dataclasses import dataclass, field

KERNAUSSAGEN, ABWEICHUNGEN, HINWEISE, FRAGEN = "kernaussagen", "abweichungen", "hinweise", "fragen"
ORDER = (KERNAUSSAGEN, ABWEICHUNGEN, HINWEISE, FRAGEN)

_HEADING = re.compile(r"^\*\*(.+?)\*\*\s*$")
_ITEM = re.compile(r"^(\d+)\.\s+(\S.*)$")
_SEPARATOR = re.compile(r"^:?-{3,}:?$")
_NEW_ITEM = re.compile(r"^(?:- |\d+\.\s|\|)")
CITATION = re.compile(r"\[Quelle:\s*([^\]]*)\]")
BRACKET = re.compile(r"\[([^\[\]]*)\]")              # her köşeli parantez (kaynak adayı)
_RULE = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$")     # Markdown yatay çizgi (---)

# Cümle bölmede nokta içeren kısaltmalar.
_ABBREVIATIONS = ("z. B.", "z.B.", "d. h.", "u. a.", "Vj.", "Vm.", "ca.", "bzw.", "ggü.", "ggf.", "inkl.",
                  "evtl.", "Mio.", "Tsd.", "Pp.", "rd.", "vgl.", "Nr.", "max.", "min.")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-ZÄÖÜ„\[(])")
_ONLY_MARKERS = re.compile(r"^(?:\s*(?:\[[^\]]*\]|\(Hypothese\))\s*)+[.!?]?\s*$")


@dataclass
class Finding:
    severity: str    # "fehler" | "hinweis"
    code: str
    message: str
    section: str | None = None
    line: int | None = None
    text: str | None = None

    def as_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class Segment:
    """Kontrol birimi: bir cümle, bir tablo satırı, bir soru veya bir başlık."""

    section: str | None
    line: int
    text: str
    kind: str                         # "satz" | "zeile" | "frage" | "ueberschrift"
    cells: list[str] | None = None
    context: str = ""                 # bütün madde veya satır; rakamların hangi satıra ait olduğu buradan okunur


@dataclass
class Parsed:
    segments: list[Segment] = field(default_factory=list)
    section_text: dict[str, str] = field(default_factory=dict)
    table_positions: list[tuple[int, str]] = field(default_factory=list)
    words: int = 0


def split_sentences(text: str) -> list[str]:
    protected = text
    for a in _ABBREVIATIONS:
        protected = protected.replace(a, a.replace(".", "\x00"))
    parts = [p.replace("\x00", ".") for p in _SENTENCE_END.split(protected) if p.strip()]
    out: list[str] = []
    for p in parts:
        if out and _ONLY_MARKERS.match(p):
            out[-1] = out[-1] + " " + p       # cümle sonuna eklenmiş kaynak/hipotez işareti
        else:
            out.append(p)
    return out


def _cells(line: str) -> list[str] | None:
    s = line.strip()
    if not (s.startswith("|") and s.endswith("|")):
        return None
    return [c.strip() for c in s[1:-1].split("|")]


def _words(text: str) -> int:
    return len(re.findall(r"\S+", BRACKET.sub(" ", text)))


def parse(text: str, period_label: str, cfg: dict) -> tuple[Parsed, list[Finding]]:
    fmt = cfg["format"]
    headings = {
        KERNAUSSAGEN: f"{fmt['kernaussagen']} {period_label}",
        ABWEICHUNGEN: fmt["abweichungen"],
        HINWEISE: fmt["hinweise"],
        FRAGEN: fmt["fragen"],
    }
    empty = fmt["empty_marker"]
    findings: list[Finding] = []
    parsed = Parsed()

    # 1. Bölümlere ayır.
    blocks: dict[str, list[tuple[int, str]]] = {}
    seen: list[str] = []
    current: str | None = None
    for no, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()
        if not line.strip() or _RULE.match(line):
            continue                                  # boş satır ve yatay çizgi: biçimsel, yok sayılır
        m = _HEADING.match(line.strip())
        if m:
            title = m.group(1).strip()
            key = next((k for k, h in headings.items() if title == h), None)
            if key is None and title.startswith(fmt["kernaussagen"]):
                findings.append(Finding("fehler", "periode",
                                        f"Überschrift „{title}“ passt nicht zur Periode; erwartet „{headings[KERNAUSSAGEN]}“.",
                                        KERNAUSSAGEN, no, title))
                key = KERNAUSSAGEN
            if key is None:
                findings.append(Finding("fehler", "ueberschrift_unbekannt", f"Unbekannte Überschrift „{title}“.",
                                        None, no, title))
                current = None
                continue
            if key in blocks:
                findings.append(Finding("fehler", "abschnitt_doppelt", f"Abschnitt „{headings[key]}“ kommt mehrfach vor.",
                                        key, no))
            parsed.segments.append(Segment(key, no, title, "ueberschrift"))
            blocks.setdefault(key, [])
            seen.append(key)
            current = key
            continue
        if current is None:
            findings.append(Finding("fehler", "text_ausserhalb", "Text außerhalb der vier Abschnitte.", None, no, line.strip()))
            continue
        content = line.strip().replace("**", "")     # kalın yazı biçimseldir, içerik değil
        if raw[:1].isspace() and blocks[current] and not _NEW_ITEM.match(content):
            prev_no, prev = blocks[current][-1]        # girintili devam satırı → önceki maddeye eklenir
            blocks[current][-1] = (prev_no, prev + " " + content)
            continue
        blocks[current].append((no, content))

    for key in ORDER:
        if key not in blocks:
            findings.append(Finding("fehler", "abschnitt_fehlt", f"Abschnitt „{headings[key]}“ fehlt.", key))
    present = [k for k in seen if k in ORDER]
    if [k for k in ORDER if k in present] != list(dict.fromkeys(present)):
        findings.append(Finding("fehler", "abschnitt_reihenfolge",
                                "Abschnitte nicht in der Reihenfolge Kernaussagen – Abweichungen – Hinweise – Offene Fragen."))

    # 2. Bölüm içerikleri.
    for key, lines in blocks.items():
        parsed.section_text[key] = "\n".join(l for _, l in lines)
        if not lines:
            findings.append(Finding("fehler", "abschnitt_leer", f"Leerer Abschnitt; erwartet Inhalt oder „{empty}“.", key))
            continue
        if len(lines) == 1 and lines[0][1] == empty:
            if key == KERNAUSSAGEN:
                findings.append(Finding("fehler", "kernaussagen_anzahl", "Mindestens eine Kernaussage erforderlich.", key, lines[0][0]))
            continue
        if key == KERNAUSSAGEN:
            _kernaussagen(lines, fmt, parsed, findings)
        elif key == ABWEICHUNGEN:
            _table(lines, fmt, parsed, findings)
        else:
            _bullets(key, lines, parsed, findings)

    parsed.words = sum(_words(parsed.section_text.get(k, "")) for k in (KERNAUSSAGEN, HINWEISE, FRAGEN)) \
        + sum(_words(headings[k]) for k in (KERNAUSSAGEN, HINWEISE, FRAGEN) if k in blocks)
    lo, hi, tol = fmt["words_min"], fmt["words_max"], fmt["words_tolerance"]
    if not lo - tol <= parsed.words <= hi + tol:
        findings.append(Finding("hinweis", "laenge",
                                f"{parsed.words} Wörter ohne Tabelle; Ziel {lo}–{hi} (Toleranz ±{tol})."))
    return parsed, findings


def _kernaussagen(lines, fmt, parsed: Parsed, findings: list[Finding]) -> None:
    expected = 1
    for no, line in lines:
        m = _ITEM.match(line)
        if not m:
            findings.append(Finding("fehler", "kernaussagen_format", "Kernaussagen als nummerierte Liste („1. …“).",
                                    KERNAUSSAGEN, no, line))
            continue
        if int(m.group(1)) != expected:
            findings.append(Finding("fehler", "kernaussagen_format", "Nummerierung nicht fortlaufend.", KERNAUSSAGEN, no, line))
        expected += 1
        for s in split_sentences(m.group(2)):
            parsed.segments.append(Segment(KERNAUSSAGEN, no, s, "satz", context=m.group(2)))
    count = expected - 1
    if count > fmt["max_kernaussagen"]:
        findings.append(Finding("fehler", "kernaussagen_anzahl",
                                f"{count} Kernaussagen; höchstens {fmt['max_kernaussagen']}.", KERNAUSSAGEN))


def _table(lines, fmt, parsed: Parsed, findings: list[Finding]) -> None:
    header = fmt["table_header"]
    first_no, first = lines[0]
    if _cells(first) != header:
        findings.append(Finding("fehler", "tabellenkopf", "Tabellenkopf weicht ab: | " + " | ".join(header) + " |",
                                ABWEICHUNGEN, first_no, first))
    if len(lines) < 2 or not (_cells(lines[1][1]) and all(_SEPARATOR.match(c) for c in _cells(lines[1][1]))
                              and len(_cells(lines[1][1])) == len(header)):
        findings.append(Finding("fehler", "tabellenkopf", "Trennzeile der Tabelle fehlt oder ist fehlerhaft.",
                                ABWEICHUNGEN, lines[1][0] if len(lines) > 1 else first_no))
    rows = lines[2:]
    if not rows:
        findings.append(Finding("fehler", "tabelle_leer", "Tabelle ohne Zeilen; ohne Abweichungen „Keine.“ schreiben.",
                                ABWEICHUNGEN, first_no))
    for no, line in rows:
        cells = _cells(line)
        if cells is None or len(cells) != len(header):
            findings.append(Finding("fehler", "tabellenzeile", f"Tabellenzeile braucht {len(header)} Spalten.",
                                    ABWEICHUNGEN, no, line))
            continue
        parsed.table_positions.append((no, cells[0]))
        parsed.segments.append(Segment(ABWEICHUNGEN, no, line, "zeile", cells, context=line))


def _bullets(key: str, lines, parsed: Parsed, findings: list[Finding]) -> None:
    for no, line in lines:
        if not line.startswith("- "):
            findings.append(Finding("fehler", "liste_format", "Aufzählung mit „- “ erwartet.", key, no, line))
            continue
        item = line[2:].strip()
        if key == FRAGEN:
            if not item.endswith("?"):
                findings.append(Finding("fehler", "frage_format", "Offene Frage endet nicht mit „?“.", key, no, item))
            parsed.segments.append(Segment(key, no, item, "frage", context=item))
        else:
            for s in split_sentences(item):
                parsed.segments.append(Segment(key, no, s, "satz", context=item))
