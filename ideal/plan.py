"""İçerik planı: bir firma-ay için ideal yorumda ne söyleneceği (docs/11_ideal_yorumlar.md, Bölüm 2).

Karma yöntemin 1. adımı [KARAR, tur 7]. Plan şunlardan kurulur:
- facts.json (rakamlar, bayraklar),
- modele verilen bağlam (Katman 2: WISSEN + getirilen notlar),
- ground truth (hangi notun hangi sapmayı gerçekten açıkladığı).

Ground truth yalnızca **görünen** bir notun kaynak gösterilip gösterilmeyeceğine karar verir. Gerçek neden notta
yoksa ya da not getirilmemişse hedef metin onu hiçbir zaman söylemez; bayrak ve K-B'den türetilmiş işaretli bir
hipotez ya da açık soru verilir [KARAR, tur 6, B3].
"""

import re
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

from facts.schema import BASE_LINES, MONTHS_DE

PLAN_VERSION = "1.2"

NAME_TO_LINE = {name: key for key, name in BASE_LINES.items()}

# [ÖNERİ] Bir olayın satırdaki yıllık farkı (t − t−12), sapmanın en az bu payıysa neden sayılır.
CAUSE_SHARE = 0.25
MAX_QUESTIONS = 5

# Bayrak kuralı başına hipotez, sonuç ve soru (K-B rehberinden türetildi, rag/knowledge.toml). {pos}, {monat}.
RULES = {
    "wiederkehrende_spitze": {
        "hypothese": "mögliche fehlende Abgrenzung einer jährlich wiederkehrenden Zahlung (z. B. Sonderzahlung, "
                     "Versicherungsprämie oder Jahresbeitrag)",
        "folge": "Dann wäre der {monat} zu ungünstig und wären die übrigen Monate zu günstig ausgewiesen.",
        "frage": "Enthält die Position {pos} im {monat} eine jährliche Zahlung, und wird diese monatlich abgegrenzt?"},
    "einmalige_spitze": {
        "hypothese": "möglicher Einmaleffekt (z. B. größere Reparatur, Messe oder Beratungsprojekt)",
        "folge": "Ein Einmaleffekt wiederholt sich in der Regel nicht und ist bei der Beurteilung des laufenden "
                 "Ergebnisses gesondert zu betrachten.",
        "frage": "Welcher Vorgang steckt hinter dem hohen Wert bei {pos} im {monat}, und ist er einmalig?"},
    "bestand_fehlt": {
        "hypothese": "mögliche fehlende Buchung der Bestandsveränderung",
        "folge": "Dann wären Rohertrag und Ergebnis verzerrt.",
        "frage": "Wurde die Bestandsveränderung für {monat} erfasst?"},
    "rohertrag_sprung": {
        "hypothese": "möglicher Buchungseffekt, etwa Wareneingänge oder Eingangsrechnungen im falschen Monat oder "
                     "eine fehlende Bestandsbuchung",
        "folge": "Dann wären Rohertrag und Ergebnis des Monats verzerrt.",
        "frage": "Sind alle Wareneingänge und Eingangsrechnungen des {monat} periodengerecht gebucht?"},
    "afa_fehlt": {
        "hypothese": "mögliche Buchung der Abschreibungen erst zum Jahresende",
        "folge": "Dann wären die Monatsergebnisse bis November zu günstig und der Dezember zu ungünstig.",
        "frage": "Werden die Abschreibungen monatlich anteilig gebucht?"},
    "afa_jahresbuchung": {
        "hypothese": "mögliche Buchung der Abschreibungen eines ganzen Jahres in einem Monat",
        "folge": "Dann wäre der {monat} stark belastet, während die übrigen Monate zu günstig ausgewiesen waren.",
        "frage": "Enthalten die Abschreibungen im {monat} den Jahresbetrag, und wie verteilt er sich auf die Monate?"},
    "zeitverschiebung": {
        "hypothese": "mögliche zeitversetzte Buchung von Eingangsrechnungen aus dem Vormonat",
        "folge": "Dann wäre der Vormonat zu günstig und der {monat} zu ungünstig ausgewiesen; beide Monate sollten "
                 "gemeinsam beurteilt werden.",
        "frage": "Wurden bei {pos} Rechnungen des Vormonats erst im {monat} gebucht?"},
    "bestand_nachbuchung": {
        "hypothese": "mögliche Nachbuchung der Bestandsveränderung mehrerer Monate",
        "folge": "Dann wären die Vormonate und der {monat} in entgegengesetzter Richtung verzerrt.",
        "frage": "Für welche Monate gilt die Bestandsbuchung im {monat}, und wie verteilt sie sich?"},
    "saisonal": {
        "hypothese": "saisonübliches Muster, da die Veränderung gegenüber dem Vorjahresmonat gering ist",
        "folge": "Maßgeblich ist der Vorjahresvergleich; eine Verzerrung ist nicht erkennbar.",
        "frage": None},
}

# Önceki yılın aynı ayına göre sapmayı açıklayabilen bayraklar. V6 yalnızca önceki aya göre farkı, V1 ise iki yılda
# da görülen bir spike'ı anlatır; ikisi de yıllık sapmanın nedeni değildir.
ROW_RULES = {"einmalige_spitze", "bestand_fehlt", "afa_fehlt", "afa_jahresbuchung", "zeitverschiebung",
             "bestand_nachbuchung"}

# Kernaussage 3 için bayrak önceliği (önce kandidat uyarısı, sonra muhasebe kaynaklı uyarılar).
FLAG_PRIORITY = ["rohertrag_sprung", "wiederkehrende_spitze", "afa_fehlt", "afa_jahresbuchung", "bestand_fehlt",
                 "zeitverschiebung", "bestand_nachbuchung", "einmalige_spitze", "saisonal"]


# --- Almanca sayı biçimi (doğrulama katmanının yuvarlama kuralı (a) ile uyumlu) ----------------------

def _round(x: float, digits: int = 0) -> Decimal:
    q = Decimal(1).scaleb(-digits)
    return Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP)


def _group(d: Decimal) -> str:
    s = f"{abs(d):,}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("-" if d < 0 else "") + s


def eur(x: float) -> str:
    return f"{_group(_round(x))} €"


def signed_eur(x: float) -> str:
    return ("+" if _round(x) > 0 else "") + eur(x)


def teur(x: float) -> str:
    return f"{_group(_round(x / 1000))} T€"


def pct(x: float, signed: bool = True) -> str:
    d = _round(x, 1)
    return ("+" if signed and d > 0 else "") + _group(d) + " %"


def pp(x: float) -> str:
    d = _round(x, 1)
    return ("+" if d > 0 else "") + _group(d) + " Prozentpunkte"


def shift(period: str, months: int) -> str:
    y, m = map(int, period.split("-"))
    idx = y * 12 + (m - 1) + months
    return f"{idx // 12:04d}-{idx % 12 + 1:02d}"


def month_name(period: str) -> str:
    return MONTHS_DE[int(period[5:7]) - 1]


# --- Ground truth erişimi -----------------------------------------------------------------------------

class Truth:
    """Bir koşunun ground truth'u: olaylar, ay kayıtları ve aylık etkiler (evaluation/)."""

    def __init__(self, events: list[dict], months: list[dict], effects: list[dict]):
        self.events = {e["event_id"]: e for e in events}
        self.months = {(m["firm_id"], m["period"]): m for m in months}
        self.effects: dict[tuple[str, str, str], dict[str, float]] = defaultdict(dict)
        for row in effects:
            cell = self.effects[(row["firm_id"], row["period"], row["line"])]
            cell[row["event_id"]] = cell.get(row["event_id"], 0.0) + float(row["delta"])

    def yoy_effects(self, firm_id: str, period: str, line: str) -> dict[str, float]:
        """Olay başına satırdaki yıllık fark: etki(t) − etki(t−12)."""
        now = self.effects.get((firm_id, period, line), {})
        before = self.effects.get((firm_id, shift(period, -12), line), {})
        return {e: now.get(e, 0.0) - before.get(e, 0.0) for e in set(now) | set(before)}

    def month_effects(self, firm_id: str, period: str, line: str) -> dict[str, float]:
        return dict(self.effects.get((firm_id, period, line), {}))


# --- Plan ---------------------------------------------------------------------------------------------

def _causes(truth: Truth, firm_id: str, period: str, line: str, delta: float, effects: dict[str, float]) -> list[dict]:
    """Sapmayı aynı yönde ve en az CAUSE_SHARE oranında açıklayan olaylar, büyükten küçüğe."""
    out = []
    for event_id, d in sorted(effects.items(), key=lambda kv: -abs(kv[1])):
        if delta == 0 or abs(d) < CAUSE_SHARE * abs(delta) or (d > 0) != (delta > 0):
            continue
        ev = truth.events[event_id]
        now = truth.effects.get((firm_id, period, line), {}).get(event_id, 0.0)
        out.append({"event_id": event_id, "type": ev["type"], "category": ev["category"],
                    "documented": ev["documented"], "source_id": ev.get("source_id"),
                    "bezug": "aktuell" if now else "vorjahr"})
    return out


_SPIKE = re.compile(r"(-?[\d.]+) € = [\d,]+-faches des Normalniveaus \((-?[\d.]+) €\)")


def _spike(evidence: str) -> float | None:
    """V1/V5 kanıtından normal düzeyin üstündeki tutar (ör. "12.345 € = 3,2-faches des Normalniveaus (3.800 €)")."""
    m = _SPIKE.search(evidence)
    return float(m.group(1).replace(".", "")) - float(m.group(2).replace(".", "")) if m else None


def _cite(causes: list[dict], visible: dict[str, str]) -> list[str]:
    return list(dict.fromkeys(c["source_id"] for c in causes if c["documented"] and c["source_id"] in visible))


def _context(p: dict) -> str:
    """Satır için isteğe bağlı Einordnung (yalnızca facts.json'dan): önceki ay ve kümülatif."""
    pm, cum = p["previous_month"], p["cumulative"]
    return (f"Vormonat {eur(pm['value'])} (Veränderung {signed_eur(pm['delta_abs'])}); kumuliert {eur(cum['actual'])} "
            f"(Vorjahreszeitraum {eur(cum['previous_year'])}, {signed_eur(cum['delta_abs'])})")


def _quote_direction(event: dict, period: str) -> int:
    """Olayın Rohertragsquote'ye etkisinin yönü: satış fiyatı +, alış fiyatı zammı −, zammın bitişi +."""
    if event["type"] == "E05":
        return 1
    if event["type"] == "E04":
        return -1 if event["start"] == period else 1
    return 0


def _rule_text(rule: str, field: str, pos: str, period: str) -> str | None:
    text = RULES[rule][field]
    return text.format(pos=pos, monat=month_name(period)) if text else None


def build_plan(facts: dict, context: dict, truth: Truth) -> dict:
    """Bir firma-ay için içerik planı. `context`: modele verilen bağlam (rag.retrieve.as_records)."""
    firm_id, period = facts["company"]["firm_id"], facts["period"]
    gt = truth.months[(firm_id, period)]
    visible = {n["source_id"]: n["text"] for n in context.get("notes", [])}
    flags = facts.get("flags", [])
    hinweis_flags = [f for f in flags if f["status"] == "hinweis"]
    questions: list[str] = []
    used_sources: list[str] = []

    def ask(q: str | None) -> None:
        if q and q not in questions:
            questions.append(q)

    # --- Tablo: anlamlı kalemler ---
    rows = []
    for p in facts.get("positions", []):
        pym = p["previous_year_month"]
        line = p["key"]
        effects = truth.yoy_effects(firm_id, period, line)
        causes = _causes(truth, firm_id, period, line, pym["delta_abs"], effects)
        sources = _cite(causes, visible)
        own_flags = [f for f in hinweis_flags if f["position"] == p["position"] and f["rule"] in ROW_RULES]
        row = {"position": p["position"], "rank": p["rank"], "ist": eur(p["actual"]), "ist_teur": teur(p["actual"]),
               "vergleich": f"Vj. {eur(pym['value'])}",
               "abweichung": signed_eur(pym["delta_abs"]) + (f" ({pct(pym['delta_pct'])})"
                                                             if pym["delta_pct"] is not None else ""),
               "richtung": "gestiegen" if pym["delta_abs"] > 0 else "gesunken",
               "einordnung": _context(p)}
        if sources:
            row["erklaerung"] = {"art": "quelle", "quellen": sources,
                                 "bezug": sorted({c["bezug"] for c in causes if c["source_id"] in sources})}
            used_sources += sources
        elif own_flags:
            f = own_flags[0]
            row["erklaerung"] = {"art": "hypothese", "text": _rule_text(f["rule"], "hypothese", p["position"], period),
                                 "verweis": "siehe Hinweise"}
        elif pym.get("base_unusual"):
            level = "hoher" if pym["delta_abs"] < 0 else "niedriger"
            row["erklaerung"] = {"art": "hypothese",
                                 "text": f"ungewöhnlich {level} Vergleichswert im Vorjahresmonat"}
        else:
            row["erklaerung"] = {"art": "offen"}
            ask(f"Was ist die Ursache für die Veränderung bei {p['position']} ({row['abweichung']} ggü. "
                f"Vorjahresmonat)?")
        rows.append(row)

    # --- Rohertragsquote adayı (V2, kandidat): karar ground truth'tan, ama yalnızca görünen notla ---
    kandidat = next((f for f in flags if f["rule"] == "rohertrag_sprung"), None)
    v2 = None
    if kandidat:
        # Sıçrama önceki aya göre tanımlı; ground truth'taki nedenler de o ayki sıçramayı açıklar (docs/03, 9.1).
        # Bu yüzden satır önceki ayla karşılaştırılır ve yalnızca yönü tutan nedenler kaynak gösterilir.
        ratio = next(r for r in facts["ratios"] if r["ratio"] == "Rohertragsquote")
        jump = ratio["previous_month"]["delta_pp"]
        real = [c for c in gt.get("rohertrag_causes", []) if c["kind"] == "real" and c["documented"]]
        matching = [truth.events[c["event_id"]] for c in real if _quote_direction(truth.events[c["event_id"]], period)
                    == (1 if jump > 0 else -1)]
        sources = list(dict.fromkeys(e["source_id"] for e in matching if e["source_id"] in visible))
        decision = gt.get("v2_candidate_decision")
        cite = bool(sources) and decision in ("cite", "either")
        v2 = {"entscheidung": "quelle" if cite else "warnung", "gt": decision}
        row = {"position": "Rohertragsquote", "rank": None, "ist": pct(ratio["actual"], signed=False),
               "vergleich": f"Vm. {pct(ratio['previous_month']['value'], signed=False)}",
               "abweichung": pp(jump), "richtung": "gestiegen" if jump > 0 else "gesunken"}
        if cite:
            ends = any(e["type"] == "E04" and e["start"] != period for e in matching if e["source_id"] in sources)
            row["erklaerung"] = {"art": "quelle", "quellen": sources, "bezug": ["ende" if ends else "aktuell"]}
            used_sources += sources
        else:
            row["erklaerung"] = {"art": "hypothese", "text": RULES["rohertrag_sprung"]["hypothese"],
                                 "verweis": "siehe Hinweise"}
        rows.append(row)

    # --- Hinweise: her hinweis bayrağı (+ uyarılan kandidat) ---
    hinweise = []
    for f in sorted(hinweis_flags, key=lambda f: FLAG_PRIORITY.index(f["rule"])):
        item = {"position": f["position"], "code": f["code"], "rule": f["rule"], "befund": f["evidence"]}
        sources: list[str] = []
        if f["rule"] == "saisonal":
            sources = ["Firmenprofil"] if "Firmenprofil" in visible else []
        elif f["rule"] == "einmalige_spitze":
            line = NAME_TO_LINE[f["position"]]
            spike = _spike(f["evidence"])
            if spike:
                effects = truth.month_effects(firm_id, period, line)
                sources = _cite(_causes(truth, firm_id, period, line, spike, effects), visible)
        if sources:
            item |= {"art": "erklaert", "quellen": sources,
                     "folge": RULES[f["rule"]]["folge"].format(monat=month_name(period))}
            used_sources += sources
        elif f["rule"] == "saisonal":              # Saison ist keine Verzerrung: Hypothese ohne Rückfrage (K-B)
            item |= {"art": "saison", "hypothese": RULES["saisonal"]["hypothese"], "folge": RULES["saisonal"]["folge"]}
        else:
            item |= {"art": "warnung", "hypothese": _rule_text(f["rule"], "hypothese", f["position"], period),
                     "folge": _rule_text(f["rule"], "folge", f["position"], period)}
            ask(_rule_text(f["rule"], "frage", f["position"], period))
        hinweise.append(item)
    if kandidat and v2["entscheidung"] == "warnung":
        hinweise.insert(0, {"position": "Rohertragsquote", "code": "V2", "rule": "rohertrag_sprung",
                            "befund": kandidat["evidence"], "art": "warnung",
                            "hypothese": RULES["rohertrag_sprung"]["hypothese"],
                            "folge": _rule_text("rohertrag_sprung", "folge", "Rohertragsquote", period)})
        questions.insert(0, _rule_text("rohertrag_sprung", "frage", "Rohertragsquote", period))

    # --- Kernaussagen (en fazla 3) ---
    summary = {s["key"]: s for s in facts["summary"]}
    ratios = {r["ratio"]: r for r in facts["ratios"]}
    be, marge = summary["betriebsergebnis"], ratios["Betriebsergebnis-Marge"]
    gl = summary["gesamtleistung"]
    ka1 = {"art": "ergebnis", "position": "Betriebsergebnis", "ist": eur(be["actual"]), "ist_teur": teur(be["actual"]),
           "vergleich": f"Vj. {eur(be['previous_year_month']['value'])}",
           "abweichung": signed_eur(be["previous_year_month"]["delta_abs"]),
           "einordnung": f"Gesamtleistung {eur(gl['actual'])} (Vj. {eur(gl['previous_year_month']['value'])}"
                         + (f", {pct(gl['previous_year_month']['delta_pct'])})"
                            if gl["previous_year_month"]["delta_pct"] is not None else ")")}
    if marge["previous_year_month"].get("significant"):
        ka1["marge"] = (f"Betriebsergebnis-Marge {pct(marge['actual'], signed=False)} "
                        f"(Vj. {pct(marge['previous_year_month']['value'], signed=False)})")
    if be["cumulative"].get("significant"):
        ka1["kumuliert"] = (f"kumuliert {eur(be['cumulative']['actual'])} (Vorjahreszeitraum "
                            f"{eur(be['cumulative']['previous_year'])}, {signed_eur(be['cumulative']['delta_abs'])})")
    kern = [ka1]
    table_rows = [r for r in rows if r["rank"] is not None]
    if table_rows:
        kern.append({"art": "position", "position": table_rows[0]["position"]})
    else:
        kern.append({"art": "ruhig", "position": "Gesamtleistung", "ist": eur(gl["actual"]),
                     "vergleich": f"Vj. {eur(gl['previous_year_month']['value'])}",
                     "abweichung": signed_eur(gl["previous_year_month"]["delta_abs"])
                     + (f" ({pct(gl['previous_year_month']['delta_pct'])})"
                        if gl["previous_year_month"]["delta_pct"] is not None else ""),
                     "text": "keine wesentlichen Abweichungen einzelner Positionen gegenüber dem Vorjahresmonat"})
    taken = kern[-1]["position"]                 # Kernaussage 3, Kernaussage 2'nin kalemini tekrarlamaz
    warn = [h for h in hinweise if h["art"] == "warnung" and h["position"] != taken]
    if kandidat:
        kern.append({"art": "hinweis" if v2["entscheidung"] == "warnung" else "position", "position": "Rohertragsquote"})
    elif warn:
        kern.append({"art": "hinweis", "position": warn[0]["position"]})
    elif len(table_rows) > 1:
        kern.append({"art": "position", "position": table_rows[1]["position"]})
    elif [h for h in hinweise if h["position"] != taken]:
        kern.append({"art": "hinweis", "position": next(h for h in hinweise if h["position"] != taken)["position"]})

    return {
        "plan_version": PLAN_VERSION, "id": f"{firm_id}_{period}", "firm_id": firm_id, "period": period,
        "unternehmen": facts["company"]["name"], "monat": facts["period_label"],
        "kernaussagen": kern[:3], "tabelle": rows, "hinweise": hinweise, "fragen": questions[:MAX_QUESTIONS],
        "notizen": {s: visible[s] for s in dict.fromkeys(used_sources)},
        "meta": {"v2": v2, "quiet_month": gt.get("quiet_month"), "flags": [f["rule"] for f in flags]},
    }
