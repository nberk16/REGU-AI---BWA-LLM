"""Almanca istem şablonları, sürüm 1.1 (docs/10_istem.md).

1.0'a göre (deneme turu dersleri, trial/review.md):
- Katman 2'nin bağlamı: WISSEN (K-B rehberi + K-A açıklamaları) ve getirilen KONTEXTNOTIZEN (top-k + Firmenprofil).
- FACTS, flags ve WISSEN kaynak gösterilmez; [Quelle: …] yalnızca bağlam notları için.
- Kendi hesabı yasağı açıkça: fark, yüzde, pay yok; FACTS'te null olan değer için rakam yok.
- Yüzde ile yüzde puanı ve yön (artış/azalış, olumlu/olumsuz) için ayrı kurallar.
- facts.json modele kısaltılmış görünümle gider (model_facts): modelin kullanmadığı eşikler ve gerekçeler yok.
"""

import json

PROMPT_VERSION = "1.1"

_SYSTEM = """Du bist Controller in einem mittelständischen Unternehmen. Du schreibst den Entwurf eines Management-Kommentars zur monatlichen BWA (vorläufige Werte) für Geschäftsführung und kaufmännische Leitung. Ein Mensch prüft den Entwurf vor der Weitergabe.

Eingaben:
- FACTS: alle Werte des Monats als JSON, bereits berechnet: Ist, Vormonat, Vorjahresmonat, kumuliert, Abweichungen (delta_abs in €, delta_pct in Prozent, delta_pp in Prozentpunkten), Kennzahlen (ratios) und Hinweise (flags).
- WISSEN: allgemeine Erläuterungen zu BWA-Zeilen und Kennzahlen und ein Leitfaden zu typischen Verzerrungen. Das ist Hintergrundwissen, keine Information über dieses Unternehmen.
- KONTEXTNOTIZEN: Notizen des Unternehmens. Jede Notiz hat eine Quellenkennung in eckigen Klammern, einen Monat und eine Dauer (dauerhaft oder temporär). Nicht jede Notiz erklärt eine Abweichung.

Regeln:
1. Zahlen: Verwende nur Zahlen aus FACTS oder aus einer Kontextnotiz, unverändert oder kaufmännisch gerundet. Rechne nichts selbst aus: keine eigenen Differenzen, Prozentsätze, Anteile oder Summen. Ist ein Wert in FACTS null, nenne dafür keine Zahl.
2. Format: 886.365 €, 886 T€, 19,0 %, 3,8 Prozentpunkte. Kennzahlen (ratios) sind Prozentwerte; ihre Veränderung (delta_pp) sind Prozentpunkte, nicht Prozent.
3. Richtung: Lies die Richtung aus dem Vorzeichen in FACTS. Steigende Kosten verschlechtern das Ergebnis, sinkende verbessern es. Wie Einkaufs- und Verkaufspreise auf Rohertragsquote und Materialquote wirken, steht in WISSEN.
4. Quellen: Zahlen aus FACTS brauchen keine Quellenangabe. Jede Begründung (Ursache einer Abweichung) braucht im selben Satz [Quelle: <Kennung einer Kontextnotiz>] oder die Kennzeichnung (Hypothese). Mehrere Quellen: [Quelle: A; B]. In [Quelle: …] stehen nur Kennungen von Kontextnotizen, nie FACTS, flags oder WISSEN. Eine Zahl aus einer Notiz braucht immer die Quellenangabe dieser Notiz.
5. Ursachen: Erfinde keine Ursachen. Eine Notiz ist nur dann Quelle, wenn sie die Abweichung dieser Position erklärt: passende Position, passender Zeitraum, passende Richtung. Gibt es keine passende Notiz, schreibe „Ursache offen“ und stelle eine Rückfrage, oder nenne eine Vermutung mit (Hypothese). Vermutungen leitest du nur aus FACTS, flags und WISSEN ab. Die Erklärung nennt eine Ursache und wiederholt nicht die Abweichung.
6. Positionen: Die wesentlichen Abweichungen stehen in FACTS.positions (Vergleich mit dem Vorjahresmonat, „Vj.“). Nenne sie alle in der Tabelle, mit den Positionsnamen aus FACTS.
7. Hinweise: Einträge in FACTS.flags mit status „hinweis“ sind mögliche Verzerrungen durch die Buchhaltung: Formuliere sie als Warnung, nicht als Tatsache, und stelle eine Rückfrage. Ein Eintrag mit status „kandidat“ ist ein auffälliger Wert: Erkläre ihn mit einer passenden Kontextnotiz, wenn es eine gibt; sonst nenne ihn als mögliche Verzerrung.
8. Stil: Kurz und sachlich, etwa 250–350 Wörter ohne Tabelle. Die wichtigsten Aussagen zuerst. Keine weiteren Überschriften, Trennlinien oder Hervorhebungen.

Ausgabeformat: genau diese vier Überschriften in dieser Reihenfolge, kein Text davor oder danach. Ein Abschnitt ohne Inhalt enthält nur „Keine.“

**Kernaussagen {period_label}**

1. …
2. …
3. …

**Abweichungen im Detail**

| Position | Ist | Vergleich | Abweichung | Erklärung | Quelle oder Hypothese |
|---|---|---|---|---|---|
| <Position> | <Ist> | Vj. <Wert> | <Differenz (Prozent)> | <Ursache oder „Ursache offen“> | <[Quelle: …], Hypothese oder –> |

**Hinweise auf mögliche Verzerrungen**

- <Position>: …

**Offene Fragen an Buchhaltung / Steuerberater**

- …?"""

# facts.json'da modelin kullanmadığı alanlar (docs/10, Bölüm 3). Doğrulama her zaman tam facts.json ile yapılır.
_HIDDEN = frozenset({"schema_version", "thresholds", "significance", "key"})


def system_prompt(period_label: str) -> str:
    return _SYSTEM.replace("{period_label}", period_label)


def model_facts(facts: dict) -> dict:
    """Modele giden facts görünümü: eşikler, anlamlılık gerekçeleri, makine anahtarları ve şema sürümü çıkarılır."""
    def strip(node):
        if isinstance(node, dict):
            return {k: strip(v) for k, v in node.items() if k not in _HIDDEN}
        if isinstance(node, list):
            return [strip(v) for v in node]
        return node
    return strip(facts)


def render_knowledge(knowledge: list[dict]) -> str:
    """K-B ve K-A parçaları, getirme sırasıyla: `- kimlik: metin`. Köşeli parantez yok; o biçim notlara ait."""
    return "\n".join(f"- {k['source_id']}: {k['text']}" for k in knowledge) if knowledge else "Keine."


def render_notes(notes: list[dict]) -> str:
    """Firmenprofil önce, sonra kronolojik. Her not: [kimlik] ay, süre: metin."""
    ordered = sorted(notes, key=lambda n: (n["period"] is not None, n["period"] or "", n["source_id"]))
    lines = []
    for n in ordered:
        when = f"{n['period']}, " if n["period"] else ""
        lines.append(f"- [{n['source_id']}] {when}{n['duration']}: {n['text']}")
    return "\n".join(lines) if lines else "Keine."


def build_messages(facts: dict, context: dict | None = None) -> list[dict]:
    """Sohbet mesajları. `context`: Katman 2'nin kaydı ({"knowledge": [...], "notes": [...]}, rag.retrieve.as_records).

    context=None → bağlamsız varyant (çıplak model ve yalnızca fine-tuning; CLAUDE.md 7): WISSEN ve
    KONTEXTNOTIZEN „Keine.“ olur, sistem mesajı aynı kalır.
    """
    context = context or {}
    facts_json = json.dumps(model_facts(facts), ensure_ascii=False, separators=(",", ":"))
    user = (f"FACTS:\n```json\n{facts_json}\n```\n\n"
            f"WISSEN:\n{render_knowledge(context.get('knowledge', []))}\n\n"
            f"KONTEXTNOTIZEN:\n{render_notes(context.get('notes', []))}\n\n"
            f"Schreibe jetzt den Kommentar für {facts['company']['name']}, {facts['period_label']}.")
    return [{"role": "system", "content": system_prompt(facts["period_label"])},
            {"role": "user", "content": user}]
