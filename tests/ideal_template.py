"""Testler için kalıp yorum: planı sabit cümlelerle metne döker (öğretmen yerine; docs/11, Bölüm 8).

Amaç plan ile kontrolün tutarlılığını sınamak: plan doğruysa bu metin uzunluk dışında bütün kontrolleri geçmeli.
"""


def _gist(plan: dict, sources: list[str]) -> str:
    """Notun ilk kelimeleri, rakamsız (kalıp metinde neden olarak)."""
    text = plan["notizen"][sources[0]].removeprefix("Firmenprofil:").split(". ")[0]
    words = [w for w in text.split() if not any(ch.isdigit() for ch in w)]
    return " ".join(words[:6]).rstrip(".,;:")


def _cell(e: dict, plan: dict) -> tuple[str, str]:
    if e["art"] == "quelle":
        return _gist(plan, e["quellen"]), f"[Quelle: {'; '.join(e['quellen'])}]"
    if e["art"] == "hypothese":
        return f"Vermutlich {e['text']}", "Hypothese"
    return "Ursache offen", "–"


def _sentence(r: dict, plan: dict) -> str:
    e = r["erklaerung"]
    base = f"{r['position']} liegt bei {r['ist']} ({r['vergleich']}, Abweichung {r['abweichung']})."
    if e["art"] == "quelle":
        return f"{base} Ursache: {_gist(plan, e['quellen'])} [Quelle: {'; '.join(e['quellen'])}]."
    if e["art"] == "hypothese":
        return f"{base} Vermutlich {e['text']} (Hypothese)."
    return f"{base} Die Ursache ist offen."


def render(plan: dict) -> str:
    rows = {r["position"]: r for r in plan["tabelle"]}
    kern = []
    for k in plan["kernaussagen"]:
        if k["art"] == "ergebnis":
            extra = "".join(f" {k[x]}." for x in ("marge", "kumuliert") if x in k)
            kern.append(f"Das Betriebsergebnis liegt bei {k['ist']} ({k['vergleich']}, Veränderung {k['abweichung']})."
                        + extra)
        elif k["art"] == "ruhig":
            kern.append(f"Die Gesamtleistung liegt bei {k['ist']} ({k['vergleich']}, Veränderung {k['abweichung']}).")
        elif k["art"] == "position":
            kern.append(_sentence(rows[k["position"]], plan))
        else:
            kern.append(f"Bei {k['position']} besteht ein Hinweis; siehe unten.")
    out = [f"**Kernaussagen {plan['monat']}**", ""] + [f"{i}. {t}" for i, t in enumerate(kern, 1)]
    out += ["", "**Abweichungen im Detail**", "",
            "| Position | Ist | Vergleich | Abweichung | Erklärung | Quelle oder Hypothese |", "|---|---|---|---|---|---|"]
    for r in plan["tabelle"]:
        text, src = _cell(r["erklaerung"], plan)
        out.append(f"| {r['position']} | {r['ist']} | {r['vergleich']} | {r['abweichung']} | {text} | {src} |")
    if not plan["tabelle"]:
        out[-2:] = ["Keine."]
    out += ["", "**Hinweise auf mögliche Verzerrungen**", ""]
    for h in plan["hinweise"]:
        if h["art"] == "erklaert":
            out.append(f"- {h['position']}: {h['befund']}. Erklärt durch: {_gist(plan, h['quellen'])} "
                       f"[Quelle: {'; '.join(h['quellen'])}]. "
                       f"{h['folge']}")
        else:
            out.append(f"- {h['position']}: {h['befund']}. Vermutlich {h['hypothese']} (Hypothese). {h['folge']}")
    if not plan["hinweise"]:
        out.append("Keine.")
    out += ["", "**Offene Fragen an Buchhaltung / Steuerberater**", ""]
    out += [f"- {q}" for q in plan["fragen"]] or ["Keine."]
    return "\n".join(out)
