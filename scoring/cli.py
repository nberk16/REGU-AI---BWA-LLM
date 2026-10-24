"""Komut satırı: bir çıktı klasöründeki bütün model metinlerini puanlar.

    python -m scoring gpu/outputs/baseline_2026-10-24
    python -m scoring <klasör> --run data/synthetic/reference_seed42 --prompts gpu/data

Klasördeki her `*.jsonl` dosyası bir sistemdir (ör. `baseline_rag_k8`); kayıtlarda `id`, `variant`, `text` olmalı.
Modelin gördüğü notlar test istemlerinden okunur (`test_<variant>.jsonl.gz`, KONTEXTNOTIZEN).
Yazar: `<klasör>/scores.jsonl` (metin başına) ve `<klasör>/scores.md` (özet).
"""

import argparse
import gzip
import json
import re
from pathlib import Path

from facts.build import MonthContext, build_facts
from facts.schema import load_config as load_facts_config
from facts.series import load_run
from ideal.build import load_truth
from validation.context import load_notes

from .score import SCORING_VERSION, Month, aggregate, make_month, score_text

ROOT = Path(__file__).resolve().parents[1]
_NOTE_ID = re.compile(r"^- \[([^\]]+)\]", re.MULTILINE)

# Raporun satırları: (anahtar, etiket, açıklama). Oranlar % olarak yazılır.
METRICS = [
    ("format_uyumu", "Format uyumu", "6.3 yapısı; doğrulamada biçim hatası olmayan metin payı"),
    ("hatasiz_metin", "Hatasız metin", "doğrulamada hiç `fehler` bulgusu olmayan metin payı"),
    ("rakam_sadakati", "Rakam sadakati (değer)", "değeri facts.json ya da kaynak gösterilen notla örtüşen rakam payı"),
    ("binlik_bosluk_metin", "Binlik ayırıcı boşluk", "„14 054 €“ yazan metin payı (istem: „14.054 €“)"),
    ("kelime_ort", "Kelime (ort., tablo hariç)", "hedef 250–350"),
    ("kelime_hedefte", "Kelime 200–400 arası", "metin payı"),
    ("neden_metin_basi", "Neden cümlesi / metin", "doğrulamanın tanıdığı neden cümleleri ve tablo açıklamaları"),
    ("neden_kaynakli", "… kaynaklı", "nedenlerin payı: [Quelle: …]"),
    ("neden_hipotez", "… „(Hypothese)“", "nedenlerin payı"),
    ("neden_isaretsiz", "… işaretsiz", "nedenlerin payı: ne kaynak ne hipotez (uydurma neden adayı)"),
    ("isaretsiz_neden_metin_basi", "İşaretsiz neden / metin", ""),
    ("kaynak_precision", "Kaynak isabeti (precision)", "gösterilen notlardan planın kaynak saydığı notların payı"),
    ("kaynak_recall", "Kaynak kapsamı (recall)", "planın kaynak saydığı notlardan gösterilenlerin payı"),
    ("celdirici_atif", "Çeldirici nota atıf", "toplam sayı"),
    ("uydurma_kaynak_metin", "Uydurma kaynak", "verilmemiş bir kaynağa atıf yapan metin payı"),
    ("sapma_yakalama", "Sapma yakalama (recall)", "facts.json'daki anlamlı kalemlerden tabloda yer alanların payı"),
    ("gereksiz_satir_metin_basi", "Gereksiz tablo satırı / metin", "anlamlı, bayraklı ya da planda olmayan satırlar"),
    ("uyari_recall_l1", "Uyarı kapsamı (Katman 1)", "Katman 1 bayraklarından Hinweise'de anılanların payı"),
    ("uyari_recall_gt", "Uyarı recall (ground truth)", "beklenen çarpıklıklardan uyarılanların payı"),
    ("uyari_precision_gt", "Uyarı precision (ground truth)", "Hinweise maddelerinden gerçek ya da kabul edilebilir çarpıklığa denk gelenlerin payı"),
    ("v2_n", "V2 adayı: ay sayısı", "Katman 1'in Rohertragsquote adayı olan aylar"),
    ("v2_dogru", "V2 adayı: doğru karar", "plana göre: notla açıkla ya da uyar"),
    ("v2_quelle_n", "… notla açıklanacak", "ay sayısı"),
    ("v2_quelle_dogru", "… bunlarda doğru", ""),
]
_COUNTS = {"kelime_ort", "neden_metin_basi", "isaretsiz_neden_metin_basi", "celdirici_atif",
           "gereksiz_satir_metin_basi", "v2_n", "v2_quelle_n"}


def load_jsonl(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def visible_note_ids(prompt: dict) -> list[str]:
    user = prompt["messages"][-1]["content"]
    section = user.split("KONTEXTNOTIZEN:", 1)[1] if "KONTEXTNOTIZEN:" in user else ""
    return _NOTE_ID.findall(section)


def segment(firm_id: str) -> str:
    return "A1 (yeni sektör)" if firm_id.startswith("A1") else "A2/A3 (yeni firma)"


def _fmt(key: str, value) -> str:
    if value is None:
        return "–"
    if key in _COUNTS:
        return f"{value:g}".replace(".", ",")
    return f"%{100 * value:.0f}"


def report(results: dict[str, list[dict]], title: str) -> str:
    systems = sorted(results)
    out = [f"# {title}", "",
           f"Puanlama {SCORING_VERSION} (`python -m scoring`). Tanımlar: `docs/13_degerlendirme.md`.", ""]
    for name, keep in [("Bütün test kümesi", lambda r: True),
                       ("A1 — yeni sektör (eğitimde hiç yok)", lambda r: r["segment"].startswith("A1")),
                       ("A2/A3 — yeni firma (görülmemiş varyantlar)", lambda r: not r["segment"].startswith("A1"))]:
        aggs = {s: aggregate([r["score"] for r in results[s] if keep(r)]) for s in systems}
        out += [f"## {name}", "", "| Ölçüt | " + " | ".join(f"`{s}`" for s in systems) + " | Açıklama |",
                "|---|" + "---:|" * len(systems) + "---|",
                "| Metin | " + " | ".join(str(aggs[s]["n"]) for s in systems) + " | |"]
        for key, label, note in METRICS:
            out.append(f"| {label} | " + " | ".join(_fmt(key, aggs[s].get(key)) for s in systems) + f" | {note} |")
        out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scoring", description="Model metinlerini puanlar (docs/13).")
    parser.add_argument("outputs", type=Path, help="model çıktılarının klasörü (*.jsonl)")
    parser.add_argument("--run", type=Path, default=ROOT / "data/synthetic/reference_seed42")
    parser.add_argument("--prompts", type=Path, default=ROOT / "gpu/data", help="test_<variant>.jsonl.gz klasörü")
    parser.add_argument("--title", default=None)
    args = parser.parse_args(argv)

    truth = load_truth(args.run)
    firms = load_run(args.run)
    fcfg = load_facts_config()
    notes_by_firm: dict[str, dict[str, dict]] = {}
    for n in load_notes(args.run):
        notes_by_firm.setdefault(n["firm_id"], {})[n["source_id"]] = n

    facts_cache: dict[str, tuple[dict, dict]] = {}
    prompts: dict[str, dict[str, dict]] = {}
    months: dict[tuple[str, str], Month] = {}

    def month(variant: str, rid: str) -> Month:
        if (variant, rid) not in months:
            firm_id, period = rid.rsplit("_", 1)
            if rid not in facts_cache:
                fs = firms[firm_id]
                facts = build_facts(fs, period, fcfg)
                mc = MonthContext(fs, fs.index(period), fcfg)
                facts_cache[rid] = (facts, {p["key"]: mc.normal_for_base(p["key"], mc.i - 12)
                                            for p in facts.get("positions", [])})
            if variant not in prompts:
                prompts[variant] = {p["id"]: p for p in load_jsonl(args.prompts / f"test_{variant}.jsonl.gz")}
            notes = [notes_by_firm[firm_id][i] for i in visible_note_ids(prompts[variant][rid])]
            facts, base_normals = facts_cache[rid]
            months[(variant, rid)] = make_month(facts, notes, truth, base_normals)
        return months[(variant, rid)]

    results: dict[str, list[dict]] = {}
    for path in sorted(args.outputs.glob("*.jsonl")):
        if path.name.startswith("scores"):
            continue
        rows = []
        for rec in load_jsonl(path):
            rows.append({"id": rec["id"], "system": path.stem, "variant": rec["variant"],
                         "segment": segment(rec["id"]),
                         "score": score_text(rec["text"], month(rec["variant"], rec["id"]))})
        results[path.stem] = rows
        print(f"{path.stem}: {len(rows)} metin puanlandı")

    with open(args.outputs / "scores.jsonl", "w", encoding="utf-8") as f:
        for rows in results.values():
            for r in rows:
                f.write(json.dumps({**r, "scoring_version": SCORING_VERSION}, ensure_ascii=False) + "\n")
    title = args.title or f"Puanlar — {args.outputs.name}"
    (args.outputs / "scores.md").write_text(report(results, title) + "\n", encoding="utf-8")
    print(f"→ {args.outputs / 'scores.md'}")
    return 0
