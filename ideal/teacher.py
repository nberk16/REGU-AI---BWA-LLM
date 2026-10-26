"""Öğretmen istemi: içerik planı → Almanca yorum (karma yöntemin 2. adımı; docs/11_ideal_yorumlar.md, Bölüm 3).

Öğretmen yalnızca dili kurar; ne söyleneceğini plan belirler [KARAR, tur 7]. Yalnızca standart kütüphane:
bu modül kullanıcının dizüstündeki betikte de çalışır.
"""

import hashlib
import json

TEACHER_VERSION = "1.4"

_SYSTEM = """Du bist erfahrener Controller und Redakteur in einem mittelständischen Unternehmen. Aus einem fertigen Inhaltsplan schreibst du den Management-Kommentar zur monatlichen BWA (vorläufige Werte) für Geschäftsführung und kaufmännische Leitung. Der Plan legt fest, WAS gesagt wird; du entscheidest nur, WIE es gesagt wird.

Regeln:
1. Inhalt: Übernimm alle Punkte des Plans und füge nichts hinzu: keine weiteren Ursachen, Bewertungen, Schlussfolgerungen, Prognosen, Empfehlungen oder Fragen. Nicht erlaubt sind zum Beispiel „signalisiert Handlungsbedarf“, „unterstreicht die Notwendigkeit“, „kann … nicht kompensieren“ oder „der Einbruch folgt auf …“.
2. Zahlen: Verwende nur Zahlen aus dem Plan, genau in dieser Schreibweise. Im Fließtext darfst du statt eines Eurobetrags die im Plan angegebene T€-Form verwenden. Rechne nichts aus. Zahlen aus einer Notiz nur im selben Satz wie die Quellenangabe dieser Notiz.
3. Quellen: Ein Satz mit Quellenangabe nennt die Ursache selbst in eigenen Worten aus dem Inhalt der Notiz (z. B. „durch den Großauftrag eines Bauträgers [Quelle: Kontextnotiz 2025-11 #2]“); eine Quellenangabe ohne genannte Ursache ist falsch. Die Angabe steht genau wie im Plan, mehrere als [Quelle: A; B], in allen Abschnitten; „laut Firmenprofil“ ohne [Quelle: Firmenprofil] genügt nicht. Andere Quellenangaben gibt es nicht.
4. Vermutungen: Jeder Satz, der eine mögliche Ursache ohne Quelle nennt, endet mit „(Hypothese)“. Das gilt in allen Abschnitten, auch in den Hinweisen und auch bei Formulierungen mit „könnte“, „möglicherweise“, „vermutlich“ oder „Sollte … zurückzuführen sein“.
5. Offene Ursachen: In der Tabelle „Ursache offen“ und in der letzten Spalte „–“. Im Text keine Vermutung dazu.
6. Wörter wie „wegen“, „durch“, „aufgrund“, „ursächlich“, „bedingt“, „zurückzuführen“, „infolge“, „verantwortlich“ oder „weil“ nur in Sätzen mit Quellenangabe oder „(Hypothese)“.
7. Tabelle: genau die Zeilen des Plans in dieser Reihenfolge. Ist, Vergleich (mit „Vj.“ bzw. „Vm.“) und Abweichung genau wie im Plan, in vollen Euro. Die Spalte Erklärung nennt die Ursache in wenigen Wörtern (z. B. „Großauftrag eines Bauträgers“, „möglicher Einmaleffekt“); sie ist nie leer und nennt nicht nur die Richtung („gestiegen“). Letzte Spalte genau „[Quelle: …]“, „Hypothese“ oder „–“.
8. Hinweise: nur Aufzählungspunkte, je Punkt des Plans einer, jeder beginnt mit dem Positionsnamen genau wie im Plan: „- Material-/Wareneinkauf: …“. Kein Einleitungssatz, keine Absätze. Hinweise sind Warnungen, keine Tatsachen.
9. Offene Fragen: genau die Fragen des Plans, sinngemäß, je eine Zeile „- …?“.
10. Länge: etwa 250–350 Wörter ohne Tabelle. Für zusätzliche Sätze nutzt du nur die Angaben unter „Einordnung“ im Plan (Vormonat, kumuliert, Gesamtleistung). Hat der Plan wenige Punkte, ist ein kürzerer Text richtig; verlängere nie mit eigenen Bewertungen. Kernaussagen: genau die Punkte des Plans, nummeriert, ohne Wiederholungen; eine Kernaussage zu einer Position nennt auch ihre Ursache wie in der Tabelle (mit Quellenangabe, als Vermutung mit „(Hypothese)“ oder als offen).
11. Format: genau die vier Überschriften des Musters in dieser Reihenfolge, kein Text davor oder danach, keine weiteren Überschriften, Trennlinien oder Hervorhebungen. Ein Abschnitt ohne Inhalt enthält nur „Keine.“
12. Sprache: natürliches, präzises Geschäftsdeutsch; abwechslungsreich formuliert, ohne Floskeln.

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
    """Satırın açıklaması öğretmene talimat olarak; etiketler metne kopyalanmasın diye içerik ve biçim ayrı yazılır."""
    if e["art"] == "quelle":
        hint = {"vorjahr": " Das Ereignis aus der Notiz lag im Vorjahresmonat und steckt im Vergleichswert.",
                "ende": " Der befristete Effekt aus der Notiz ist ausgelaufen."}.get(e["bezug"][0], "") \
            if len(e["bezug"]) == 1 else ""
        if e.get("vorjahr_quellen"):
            hint = (f" Das Ereignis aus {', '.join(e['vorjahr_quellen'])} lag im Vorjahresmonat und steckt im "
                    f"Vergleichswert; die übrigen Notizen betreffen den aktuellen Monat.")
        return (f"Ursache in wenigen Wörtern aus dem Inhalt von {', '.join(e['quellen'])}.{hint} "
                f"Letzte Spalte: [Quelle: {'; '.join(e['quellen'])}]")
    if e["art"] == "hypothese":
        ref = f" ({e['verweis']})" if e.get("verweis") else ""
        return f"Vermutung „{e['text']}“{ref}. Letzte Spalte: Hypothese"
    return "„Ursache offen“. Letzte Spalte: –"


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
            out.append(f"{i}. " + "; ".join(parts) + f". Einordnung: {k['einordnung']}")
        elif k["art"] == "ruhig":
            out.append(f"{i}. {k['position']}: Ist {k['ist']}, {k['vergleich']}, Veränderung {k['abweichung']}; "
                       f"{k['text']}")
        elif k["art"] == "position":
            r = rows[k["position"]]
            e = r["erklaerung"]
            must = {"quelle": f"die Ursache aus dem Inhalt von {', '.join(e.get('quellen', []))} im selben Satz mit "
                              f"[Quelle: {'; '.join(e.get('quellen', []))}]",
                    "hypothese": f"die Vermutung „{e.get('text', '')}“ mit „(Hypothese)“",
                    "offen": "dass die Ursache offen ist"}[e["art"]]
            out.append(f"{i}. {k['position']}: {_row_numbers(r)}. Diese Kernaussage nennt auch {must}."
                       + (f" Einordnung: {r['einordnung']}" if r.get("einordnung") else ""))
        else:
            h = hinweise[k["position"]]
            if k["position"] in rows and rows[k["position"]]["erklaerung"]["art"] == "quelle":
                e = rows[k["position"]]["erklaerung"]
                out.append(f"{i}. {k['position']}: {_row_numbers(rows[k['position']])}. Diese Kernaussage nennt auch "
                           f"die Ursache aus dem Inhalt von {', '.join(e['quellen'])} im selben Satz mit "
                           f"[Quelle: {'; '.join(e['quellen'])}].")
                continue
            how = {"warnung": "als mögliche Verzerrung (siehe Hinweise)",
                   "erklaert": f"erklärt durch [Quelle: {'; '.join(h.get('quellen', []))}]",
                   "saison": "vermutlich saisonübliches Muster, keine Verzerrung (Hypothese)"}[h["art"]]
            out.append(f"{i}. Hinweis {k['position']}: {h['befund']}; {how}")
    out += ["", "TABELLE (Zeilen in dieser Reihenfolge; Ist, Vergleich und Abweichung genau übernehmen):"]
    for r in plan["tabelle"]:
        out.append(f"- {r['position']} | {_row_numbers(r)}")
        out.append(f"  Spalte Erklärung: {_explanation(r['erklaerung'])}")
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


def input_sha(request: dict) -> str:
    """Öğretmene giden mesajların parmak izi: plan ya da bağlam değişirse eski kayıt geçersiz olur."""
    return hashlib.sha256(json.dumps(request["messages"], ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def feedback_message(problems: list[str]) -> dict:
    """Geçemeyen taslak için düzeltme isteği (yeniden üretim)."""
    lines = "\n".join(f"- {p}" for p in problems)
    return {"role": "user", "content": f"Der Entwurf erfüllt folgende Punkte nicht:\n{lines}\n\n"
                                       "Schreibe den vollständigen Kommentar neu und behebe diese Punkte. "
                                       "Alle übrigen Regeln gelten weiter."}
