"""Deneme turu çıktılarını doğrulama katmanıyla puanlar ve trial/results.md yazar (docs/08).

Kullanım: python trial/score.py [--outputs trial/outputs] [--report trial/results.md]

Almanca akıcılık ve üslup otomatik ölçülmez; çıktılar okunarak değerlendirilir (results.md'nin sonuna eklenir).
"""

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from validation.check import validate  # noqa: E402

HERE = Path(__file__).resolve().parent


def load_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _median(xs: list[float]) -> float | None:
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 1) if xs else None


def _fmt(x, suffix: str = "") -> str:
    if x is None:
        return "–"
    if isinstance(x, float):
        return f"{x:.2f}".rstrip("0").rstrip(".").replace(".", ",") + suffix
    return f"{x}{suffix}"


def score(cases: dict[str, dict], outputs_dir: Path) -> dict[str, dict]:
    results: dict[str, dict] = {}
    for path in sorted(outputs_dir.glob("*.jsonl")):
        latest = {}
        for r in load_jsonl(path):
            if not r.get("error"):
                latest[r["case_id"]] = r                 # aynı örnek tekrar koşulduysa sonuncusu
        rows = []
        for case_id, r in latest.items():
            if case_id not in cases:
                continue
            case = cases[case_id]
            report = validate(r["output"], case["facts"], case["notes"])
            rows.append({"case_id": case_id, "record": r, "report": report})
        if rows:
            results[path.stem] = {"tag": rows[0]["record"]["tag"], "rows": rows,
                                  "memory": next((x["record"].get("memory") for x in rows if x["record"].get("memory")), None)}
    return results


def summarize(results: dict[str, dict], n_cases: int) -> str:
    lines = ["# Deneme turu sonuçları", "",
             f"Örnek sayısı: {n_cases} (doğrulama varyantları; `trial/inputs/selection.md`). "
             "Puanlama: doğrulama katmanı (`docs/07`).", "",
             "## Özet", "",
             "| Model | Örnek | Format uyumu | Rakam sadakati (toplam) | İtiraz edilen rakam | Kaynaklı neden | İşaretsiz neden | "
             "İçerik hatası / örnek | Eksik kalem/bayrak | Kelime (medyan) | Çıktı token/s | İstem token/s | Süre / örnek |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for name, res in results.items():
        rows = res["rows"]
        reps = [r["report"] for r in rows]
        stats = [r["record"]["stats"] for r in rows]
        checked = sum(rep["metrics"]["numbers"]["checked"] for rep in reps)
        supported = sum(rep["metrics"]["numbers"]["fakt"] + rep["metrics"]["numbers"]["notiz"] for rep in reps)
        hints = Counter(f["code"] for rep in reps for f in rep["findings"] if f["severity"] == "hinweis")
        lines.append(
            f"| {name} | {len(rows)} | {sum(rep['metrics']['format_ok'] for rep in reps)}/{len(rows)} | "
            f"{_fmt(supported / checked if checked else None)} | {checked - supported} | "
            f"{sum(rep['metrics']['reasons']['with_source'] for rep in reps)} | "
            f"{sum(rep['metrics']['reasons']['unmarked'] for rep in reps)} | "
            f"{_fmt(statistics.mean(rep['content_errors'] for rep in reps))} | "
            f"{hints['position_fehlt'] + hints['flag_fehlt']} | {_fmt(_median([rep['metrics']['words'] for rep in reps]))} | "
            f"{_fmt(_median([s.get('output_tok_per_s') for s in stats]))} | "
            f"{_fmt(_median([s.get('prompt_tok_per_s') for s in stats]))} | "
            f"{_fmt(_median([s.get('wall_s') for s in stats]), ' s')} |")

    lines += ["", "**Sütunlar:**",
              "- **Format uyumu:** CLAUDE.md 6.3 yapısına uyan çıktı sayısı.",
              "- **Rakam sadakati:** `facts.json`'la ya da kaynak gösterilen notla eşleşen rakamların payı.",
              "- **İtiraz edilen rakam:** belgelenmemiş, yanlış satıra ait, işareti ters ya da birimi karışmış rakamlar.",
              "- **Kaynaklı / işaretsiz neden:** bir bağlam notunu gösteren ve ne not ne `(Hypothese)` taşıyan neden cümleleri.",
              "- **İçerik hatası:** biçim dışındaki `fehler` bulguları (rakam, kaynak, neden; `docs/07`, Bölüm 6).",
              "- **Eksik kalem/bayrak:** metinde geçmeyen önemli kalemler ve bayraklar (`hinweis`).",
              "- Bellek payı gösterilmez: Ollama'nın `/api/ps` değerleri bu sürümde güvenilir değil (ör. 9B model için 26 MB).",
              "", "## Örnek başına bulgular (içerik hatası · rakam sadakati)", ""]
    names = list(results)
    lines.append("| Örnek | " + " | ".join(names) + " |")
    lines.append("|---|" + "---|" * len(names))
    case_ids = sorted({r["case_id"] for res in results.values() for r in res["rows"]})
    for cid in case_ids:
        cells = []
        for name in names:
            row = next((r for r in results[name]["rows"] if r["case_id"] == cid), None)
            if row is None:
                cells.append("–")
                continue
            rep = row["report"]
            fid = rep["metrics"]["numbers"]["fidelity"]
            cells.append(f"{rep['content_errors']} · {_fmt(fid)}" + ("" if rep["metrics"]["format_ok"] else " · Format ✗"))
        lines.append(f"| {cid} | " + " | ".join(cells) + " |")

    lines += ["", "## En sık bulgular", ""]
    for name, res in results.items():
        c = Counter(f["code"] for r in res["rows"] for f in r["report"]["findings"])
        top = ", ".join(f"`{code}` × {n}" for code, n in c.most_common(8)) or "yok"
        lines.append(f"- **{name}:** {top}")
    review = HERE / "review.md"                      # elle yazılan okuma değerlendirmesi (varsa)
    lines += ["", review.read_text(encoding="utf-8").strip() if review.exists()
              else "## Almanca kalite ve üslup (okunarak)\n\n_Çıktılar okunduktan sonra eklenecek._", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Deneme turu çıktılarını puanlar.")
    parser.add_argument("--cases", type=Path, default=HERE / "inputs" / "cases.jsonl")
    parser.add_argument("--outputs", type=Path, default=HERE / "outputs")
    parser.add_argument("--report", type=Path, default=HERE / "results.md")
    args = parser.parse_args(argv)

    cases = {c["id"]: c for c in load_jsonl(args.cases)}
    results = score(cases, args.outputs)
    if not results:
        print(f"{args.outputs} içinde çıktı yok.")
        return
    text = summarize(results, len(cases))
    args.report.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
