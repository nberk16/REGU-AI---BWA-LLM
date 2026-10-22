"""Altın küme: elle kontrol edilmiş doğrulama metinleri (docs/12_egitim_verisi.md, Bölüm 3).

    python -m ideal gold        # ideal/gold/edits.json → ideal/gold/gold.jsonl + özet

- Kaynak: pilot için seçilmiş 24 çeşitli doğrulama ayı (`val`) ve 6 bağlamsız doğrulama ayı (`val_ohne`).
- Her metin önce eğitim verisindeki otomatik temizlikten geçer (eksi işareti, Kernaussage uyarısı), sonra
  ideal/gold/edits.json'daki elle bulunan düzeltmeler uygulanır. Sonuç kontrolden geçmek zorunda.
- Bulgu türleri, öğretmen metinlerinin otomatik kontrolün göremediği kusurlarını ölçer.
"""

import json
from collections import Counter
from pathlib import Path

from .check import check

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "ideal" / "gold"


def _latest_ok(name: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    with open(ROOT / "ideal" / "outputs" / f"{name}.jsonl", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            if rec["status"] == "ok":
                out[rec["id"]] = rec
    return out


def build(edits_path: Path = GOLD / "edits.json") -> list[dict]:
    from training.data import _jsonl, normalize, warn_kernaussagen

    edits = json.loads(edits_path.read_text(encoding="utf-8"))
    requests = {s: {r["id"]: r for r in _jsonl(ROOT / "ideal" / "requests" / f"{s}.jsonl.gz")}
                for s in {e["set"] for e in edits.values()}}
    records = {s: _latest_ok(s) for s in requests}
    rows = []
    for id_, entry in edits.items():
        req, rec = requests[entry["set"]][id_], records[entry["set"]][id_]
        text, added, deviates = warn_kernaussagen(normalize(rec["text"]), req["plan"])
        findings = [dict(art="ka_ohne_warnung", beschreibung="Kernaussage zu einem Hinweis ohne Warnsprache",
                         auto=True)] * added
        for b in entry["befunde"]:
            if b["alt"] not in text:
                raise ValueError(f"{id_}: zu ersetzender Text nicht gefunden: {b['alt'][:60]}")
            text = text.replace(b["alt"], b["neu"])
            findings.append(dict(b, auto=False))
        if deviates and not any(b["art"] == "plan_abweichung" for b in entry["befunde"]):
            raise ValueError(f"{id_}: Kernaussage weicht vom Plan ab, aber keine Korrektur eingetragen")
        result = check(text, req["plan"], req["facts"], req["notes"])
        if not result["ok"]:
            raise ValueError(f"{id_}: Goldtext besteht die Kontrolle nicht: {result['problems'][:2]}")
        rows.append({"id": id_, "set": entry["set"], "input_sha": rec["input_sha"], "attempts": rec["attempts"],
                     "befunde": findings, "teacher_text": rec["text"], "gold_text": text})
    return rows


def summary(rows: list[dict]) -> str:
    kinds = Counter(b["art"] for r in rows for b in r["befunde"])
    texts = Counter(b["art"] for r in rows for b in {x["art"]: x for x in r["befunde"]}.values())
    clean = sum(not r["befunde"] for r in rows)
    manual = sum(any(not b["auto"] for b in r["befunde"]) for r in rows)
    lines = [f"# Altın küme: {len(rows)} metin", "",
             f"- Düzeltme gerekmeyen: {clean} · yalnızca otomatik düzeltme: {len(rows) - clean - manual} · "
             f"elle düzeltme: {manual}", "", "| Bulgu türü | Metin | Bulgu |", "|---|---:|---:|"]
    lines += [f"| {k} | {texts[k]} | {v} |" for k, v in kinds.most_common()]
    return "\n".join(lines)


def write(rows: list[dict], path: Path = GOLD / "gold.jsonl") -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
