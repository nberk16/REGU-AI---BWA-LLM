"""Öğretmen istemi: içerik planı → Almanca yorum (karma yöntemin 2. adımı; docs/11_ideal_yorumlar.md, Bölüm 3).

Öğretmen yalnızca dili kurar; ne söyleneceğini plan belirler [KARAR, tur 7]. Yalnızca standart kütüphane:
bu modül kullanıcının dizüstündeki betikte de çalışır.
"""

TEACHER_VERSION = "1.0"

_SYSTEM = """Du bist erfahrener Controller und Redakteur in einem mittelständischen Unternehmen. Aus einem fertigen Inhaltsplan schreibst du den Management-Kommentar zur monatlichen BWA (vorläufige Werte) für Geschäftsführung und kaufmännische Leitung. Der Plan legt fest, WAS gesagt wird; du entscheidest nur, WIE es gesagt wird.

Regeln:
1. Inhalt: Übernimm alle Punkte des Plans und füge nichts hinzu: keine weiteren Ursachen, Bewertungen, Prognosen oder Empfehlungen.
2. Zahlen: Verwende nur Zahlen aus dem Plan, genau in dieser Schreibweise. Statt eines Eurobetrags darfst du die im Plan angegebene T€-Form verwenden. Rechne nichts aus. Zahlen aus einer Notiz nur im selben Satz wie die Quellenangabe dieser Notiz.
3. Quellen: Eine Ursache mit Quelle bekommt im selben Satz die Quellenangabe genau wie im Plan, z. B. [Quelle: Kontextnotiz 2025-06 #2], mehrere als [Quelle: A; B]. Andere Quellenangaben gibt es nicht. In der Tabelle steht sie in der letzten Spalte.
4. Vermutungen: Eine Vermutung aus dem Plan steht als Vermutung im Satz („vermutlich“, „möglicherweise“) und trägt im selben Satz „(Hypothese)“. In der Tabelle steht in der letzten Spalte „Hypothese“.
5. Offene Ursachen: In der Tabelle „Ursache offen“ und in der letzten Spalte „–“. Im Text keine Vermutung dazu; die Rückfrage steht bei den offenen Fragen.
6. Wörter wie „wegen“, „durch“, „aufgrund“, „ursächlich“, „bedingt“, „zurückzuführen“, „infolge“ oder „weil“ nur in Sätzen mit Quellenangabe oder „(Hypothese)“.
7. Hinweise auf mögliche Verzerrungen sind Warnungen, keine Tatsachen. Jede offene Frage endet mit „?“.
8. Länge: 250–350 Wörter ohne Tabelle. Kernaussagen: genau die Punkte des Plans, höchstens drei, nummeriert, als ganze Sätze.
9. Format: genau die vier Überschriften des Musters in dieser Reihenfolge, kein Text davor oder danach, keine weiteren Überschriften, Trennlinien oder Hervorhebungen. Ein Abschnitt ohne Inhalt enthält nur „Keine.“
10. Sprache: natürliches, präzises Geschäftsdeutsch; abwechslungsreich formuliert, ohne Floskeln und Wiederholungen.

Muster:

**Kernaussagen <Monat Jahr>**

1. …
2. …
3. …

**Abweichungen im Detail**

| Position | Ist | Vergleich | Abweichung | Erklärung | Quelle oder Hypothese |
|---|---|---|---|---|---|
| <Position> | <Ist> | <Vergleich> | <Abweichung> | <Erklärung> | <[Quelle: …], Hypothese oder –> |

**Hinweise auf mögliche Verzerrungen**

- <Position>: …

**Offene Fragen an Buchhaltung / Steuerberater**

- …?"""


def system_prompt() -> str:
    return _SYSTEM


def _explanation(e: dict) -> str:
    if e["art"] == "quelle":
        when = {"vorjahr": " (Ereignis im Vorjahresmonat: der Vergleichswert enthält den Effekt)",
                "ende": " (Ende des befristeten Effekts aus der Notiz)"}.get(e["bezug"][0], "") if len(e["bezug"]) == 1 else ""
        return f"Ursache mit Quelle{when}: Inhalt aus [Quelle: {'; '.join(e['quellen'])}]"
    if e["art"] == "hypothese":
        ref = f" ({e['verweis']})" if e.get("verweis") else ""
        return f"Vermutung: {e['text']}{ref} → Hypothese"
    return "Ursache offen → –"


def _row_numbers(r: dict) -> str:
    ist = f"{r['ist']} ({r['ist_teur']})" if r.get("ist_teur") else r["ist"]
    return f"Ist {ist} | {r['vergleich']} | Abweichung {r['abweichung']} ({r['richtung']})"


def render_plan(plan: dict) -> str:
    rows = {r["position"]: r for r in plan["tabelle"]}
    hinweise = {h["position"]: h for h in plan["hinweise"]}
    out = [f"UNTERNEHMEN: {plan['unternehmen']} · MONAT: {plan['monat']}", "",
           "KERNAUSSAGEN (in dieser Reihenfolge):"]
    for i, k in enumerate(plan["kernaussagen"], 1):
        if k["art"] == "ergebnis":
            parts = [f"Betriebsergebnis: Ist {k['ist']} ({k['ist_teur']}), {k['vergleich']}, "
                     f"Veränderung {k['abweichung']}"]
            parts += [k[x] for x in ("marge", "kumuliert") if x in k]
            out.append(f"{i}. " + "; ".join(parts))
        elif k["art"] == "ruhig":
            out.append(f"{i}. {k['position']}: Ist {k['ist']}, {k['vergleich']}, Veränderung {k['abweichung']}; "
                       f"{k['text']}")
        elif k["art"] == "position":
            r = rows[k["position"]]
            out.append(f"{i}. {k['position']}: {_row_numbers(r)}; {_explanation(r['erklaerung'])}")
        else:
            h = hinweise[k["position"]]
            how = {"warnung": "als mögliche Verzerrung (siehe Hinweise)",
                   "erklaert": f"erklärt durch [Quelle: {'; '.join(h.get('quellen', []))}]",
                   "saison": "vermutlich saisonübliches Muster, keine Verzerrung (Hypothese)"}[h["art"]]
            out.append(f"{i}. Hinweis {k['position']}: {h['befund']}; {how}")
    out += ["", "TABELLE (Zeilen in dieser Reihenfolge; Ist, Vergleich und Abweichung genau übernehmen):"]
    for r in plan["tabelle"]:
        out.append(f"- {r['position']} | {_row_numbers(r)}")
        out.append(f"  Erklärung: {_explanation(r['erklaerung'])}")
    out += ["", "HINWEISE:"]
    if not plan["hinweise"]:
        out.append("Keine.")
    for h in plan["hinweise"]:
        if h["art"] == "erklaert":
            out.append(f"- {h['position']}: Befund: {h['befund']}. Erklärt durch [Quelle: {'; '.join(h['quellen'])}]. "
                       f"{h['folge']}")
        else:
            out.append(f"- {h['position']}: Befund: {h['befund']}. Vermutung: {h['hypothese']} (Hypothese). "
                       f"Folge: {h['folge']}")
    out += ["", "OFFENE FRAGEN (sinngemäß übernehmen):"]
    out += [f"- {q}" for q in plan["fragen"]] or ["Keine."]
    out += ["", "NOTIZEN (Inhalt der zitierten Quellen):"]
    out += [f"- [{s}] {t}" for s, t in plan["notizen"].items()] or ["Keine."]
    out += ["", "Schreibe jetzt den Kommentar."]
    return "\n".join(out)


def teacher_messages(plan: dict) -> list[dict]:
    return [{"role": "system", "content": system_prompt()}, {"role": "user", "content": render_plan(plan)}]


def feedback_message(problems: list[str]) -> dict:
    """Geçemeyen taslak için düzeltme isteği (yeniden üretim)."""
    lines = "\n".join(f"- {p}" for p in problems)
    return {"role": "user", "content": f"Der Entwurf erfüllt folgende Punkte nicht:\n{lines}\n\n"
                                       "Schreibe den vollständigen Kommentar neu und behebe diese Punkte. "
                                       "Alle übrigen Regeln gelten weiter."}
