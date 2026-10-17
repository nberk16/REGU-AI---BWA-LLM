"""Getirme: facts.json'dan sorgu üretir, K-A/K-B'yi anahtarla, K-C'yi anlamsal olarak getirir (docs/09, Bölüm 4).

- K-B: "Grundsätze" + facts.json'daki her bayrak kuralının rehber parçası.
- K-A: anlamlı kalemlerin, bayraklı satırların ve anlamlı oranların açıklamaları.
- K-C: firma + 13 aylık pencere (t−12 … t) filtresi; içinden anlamsal top-k [KARAR, tur 6]. Dönemsiz
  `Firmenprofil` notu her zaman eklenir [KARAR, tur 4]. Seçilen notlar kronolojik sıralanır.
"""

from facts.schema import BASE_LINES, RATIOS, SUMMARY_LINES

from .documents import Doc, period_index

NAME_TO_KEY = {name: key for key, name in {**BASE_LINES, **SUMMARY_LINES}.items()} | {
    "Betrieblicher Rohertrag": "betrieblicher_rohertrag", "Neutraler Aufwand": "neutraler_aufwand",
    "Neutraler Ertrag": "neutraler_ertrag"} | {r: r for r in RATIOS}

MODES = ("single", "multi", "multi_expanded")


def _direction(delta: float) -> str:
    return "gestiegen" if delta > 0 else "gesunken" if delta < 0 else "unverändert"


def items(facts: dict) -> list[dict]:
    """Sorgu öğeleri: anlamlı kalemler, bayraklar ve anlamlı oranlar (facts.json'daki sırayla)."""
    out = []
    for p in facts.get("positions", []):
        out.append({"key": p["key"], "text": f"{p['position']} {_direction(p['previous_year_month']['delta_abs'])} "
                                              f"gegenüber dem Vorjahresmonat"})
    for f in facts.get("flags", []):
        out.append({"key": NAME_TO_KEY.get(f["position"]), "rule": f["rule"], "text": f"{f['position']}: {f['evidence']}"})
    for r in facts.get("ratios", []):
        if r["previous_year_month"].get("significant"):
            out.append({"key": r["ratio"], "text": f"{r['ratio']} {_direction(r['previous_year_month']['delta_pp'])} "
                                                   f"gegenüber dem Vorjahresmonat"})
    if not out:                                         # sakin ay: özet satırlardan genel bir sorgu
        for s in facts.get("summary", []):
            if s["key"] in ("gesamtleistung", "betriebsergebnis"):
                out.append({"key": s["key"], "text": f"{s['position']} {_direction(s['previous_year_month']['delta_abs'])}"})
    return out


def build_queries(facts: dict, mode: str, ka_texts: dict[str, str]) -> list[str]:
    its = items(facts)
    if mode == "single":
        return ["; ".join(i["text"] for i in its) + f" ({facts['period_label']})"]
    if mode == "multi":
        return [i["text"] for i in its]
    if mode == "multi_expanded":
        return [f"{i['text']}. {ka_texts.get(i['key'], '')}".strip() for i in its]
    raise ValueError(f"bilinmeyen sorgu yöntemi: {mode}")


def knowledge_keys(facts: dict) -> list[str]:
    keys = ["grundsaetze"]
    for i in items(facts):
        if i.get("rule"):
            keys.append(i["rule"])
    for i in items(facts):
        if i.get("key"):
            keys.append(i["key"])
    return list(dict.fromkeys(keys))


def retrieve(facts: dict, kb, mode: str | None = None, k: int | None = None) -> dict:
    """Bir firma-ay için bağlam: {"knowledge": [Doc], "notes": [Doc], "scores": {doc_id: puan}}.

    k=None → yapılandırmadaki top_k; k=0 → penceredeki bütün notlar (ablation karşılaştırması).
    """
    cfg = kb.cfg["retrieval"]
    mode = mode or cfg["mode"]
    k = cfg["top_k"] if k is None else k
    firm_id = facts["company"]["firm_id"]
    end = period_index(facts["period"])
    start = end - (cfg["window_months"] - 1)

    knowledge = kb.general(knowledge_keys(facts))
    ka_texts = {d.meta["key"]: d.text for d in kb.general([i["key"] for i in items(facts) if i.get("key")])}

    window = {d.doc_id: d for d in kb.window_notes(firm_id, start, end)}
    scores: dict[str, float] = {}
    if k == 0 or len(window) <= k:
        chosen = list(window)
    else:
        rankings = kb.rank_notes(firm_id, start, end, build_queries(facts, mode, ka_texts))
        for ranking in rankings:                       # Reciprocal Rank Fusion
            for rank, (doc_id, _) in enumerate(ranking, start=1):
                scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (cfg["rrf_k"] + rank)
        chosen = sorted(scores, key=lambda d: (-scores[d], d))[:k]
    notes = sorted((window[d] for d in chosen), key=lambda d: (d.meta["period_index"], d.source_id))
    return {"knowledge": knowledge, "notes": kb.profile(firm_id) + notes, "scores": scores}


def as_records(result: dict) -> dict:
    """JSON'a yazılabilir biçim (prompting ve Kaggle defterleri için)."""
    def rec(d: Doc) -> dict:
        r = {"source_id": d.source_id, "kind": d.kind, "text": d.text}
        if d.kind == "K-C":
            r |= {"period": d.meta["period"] or None, "duration": d.meta["duration"]}
        return r
    return {"knowledge": [rec(d) for d in result["knowledge"]], "notes": [rec(d) for d in result["notes"]]}
