"""Eğitim verisi: öğrenci istemi 1.1 + öğretmenin kabul edilmiş metni (docs/12_egitim_verisi.md).

    python -m training                       # gpu/data/{train,val}_{rag,ohne}.jsonl.gz + test istemleri

- Ana model (RAG + FT): `rag_k8` istemi + `train`/`val` kümelerinin kabul edilen metni.
- Karşılaştırma modeli (yalnızca FT, tur 12): `ohne_kontext` istemi + `train_ohne`/`val_ohne` metni.
- Yalnızca girdisi güncel (input_sha) ve kabul edilmiş metinler alınır. Öğrencinin istemindeki notlar, planın
  gördüğü notlarla birebir aynı olmalı; değilse dur.
- Biçim birliği: rakamdan önceki tire (–) ASCII eksiye çevrilir; metin yeniden kontrol edilir (docs/11, Bölüm 14).
- Uyarı tamamlama: Plan bir Kernaussage'yi uyarı (Hinweis) olarak istiyorsa ve metin uyarı dili içermiyorsa, planın
  kısa hipotezi „Hinweis: … (Hypothese).“ olarak eklenir. Kernaussage başka bir kalemi anlatıyorsa ay alınmaz
  (altın küme, docs/12, Bölüm 3).
- Test istemleri (reference_seed42): `ohne_kontext`, `rag_k8`, `rag_alle`; hedef metin yok (değerlendirme ground truth ile).
"""

import argparse
import gzip
import json
import re
from collections import Counter
from pathlib import Path

from facts.build import build_facts, commentable_periods
from facts.schema import load_config
from facts.series import load_run
from ideal.check import check
from ideal.teacher import input_sha
from prompting import PROMPT_VERSION
from prompting.templates import build_messages

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "gpu" / "data"
# (çıktı adı, öğretmen kümesi, öğrenci varyantı)
SETS = [("train_rag", "train", "rag_k8"), ("val_rag", "val", "rag_k8"),
        ("train_ohne", "train_ohne", "ohne_kontext"), ("val_ohne", "val_ohne", "ohne_kontext")]
_DASH_MINUS = re.compile(r"(?<![\w])[–−]\s?(?=\d)")
_WARN = re.compile(r"möglich|vermutlich|Hypothese|verzerr|Hinweis|könnte|dürfte", re.I)
_ITEM = re.compile(r"^\d\.\s.*?(?=\n\s*\d\.\s|\Z)", re.S | re.M)


def normalize(text: str) -> str:
    """Rakamdan önceki tire ya da eksi işaretini ASCII eksiye çevirir; metnin geri kalanı değişmez."""
    return _DASH_MINUS.sub("-", text)


def _short(hypothese: str) -> str:
    """Planın hipotezi örneksiz: „möglicher Buchungseffekt, etwa …“ → „möglicher Buchungseffekt“."""
    return re.split(r",? \(z\. B\.|, etwa |, z\. B\.", hypothese)[0].strip()


def _stem(position: str) -> str:
    return re.split(r"[ /(]", position)[0][:8].lower()


def warn_kernaussagen(text: str, plan: dict) -> tuple[str, int, bool]:
    """Uyarı Kernaussage'lerine eksik uyarıyı ekler. Dönüş: (metin, eklenen uyarı sayısı, plandan sapma var mı)."""
    head, sep, rest = text.partition("**Abweichungen im Detail**")
    items = list(_ITEM.finditer(head))
    warnings = {h["position"]: h for h in plan["hinweise"] if h["art"] == "warnung"}
    added, deviates, out, pos = 0, False, [], 0
    for k, ka in enumerate(plan["kernaussagen"]):
        if ka["art"] != "hinweis" or ka["position"] not in warnings or k >= len(items):
            continue
        item = items[k]
        body = item.group(0).rstrip()
        if _stem(ka["position"]) not in body.lower():
            deviates = True
            continue
        if not _WARN.search(body):
            end = item.start() + len(body)
            out.append(head[pos:end] + f" Hinweis: {_short(warnings[ka['position']]['hypothese'])} (Hypothese).")
            pos, added = end, added + 1
    return "".join(out) + head[pos:] + sep + rest, added, deviates


def _jsonl(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def accepted(name: str, root: Path = ROOT) -> tuple[list[dict], dict[str, dict]]:
    """İstekler ve kabul edilmiş, girdisi güncel son kayıtlar (id → kayıt)."""
    requests = _jsonl(root / "ideal" / "requests" / f"{name}.jsonl.gz")
    current = {r["id"]: input_sha(r) for r in requests}
    last: dict[str, dict] = {}
    for rec in _jsonl(root / "ideal" / "outputs" / f"{name}.jsonl"):
        if rec.get("input_sha") == current.get(rec["id"]):
            last[rec["id"]] = rec
    return requests, {i: r for i, r in last.items() if r["status"] == "ok"}


def build_set(teacher_set: str, variant: str, retrieval: dict[tuple[str, str], dict] | None,
              root: Path = ROOT) -> tuple[list[dict], Counter]:
    requests, ok = accepted(teacher_set, root)
    stats: Counter = Counter(istek=len(requests), kabul=len(ok))
    rows = []
    for req in requests:
        rec = ok.get(req["id"])
        if rec is None:
            continue
        context = None
        if variant != "ohne_kontext":
            context = retrieval[(req["firm_id"], req["period"])]
            if context["notes"] != req["notes"]:
                raise ValueError(f"{req['id']}: istemdeki notlar planın notlarıyla aynı değil")
        elif req["notes"]:
            raise ValueError(f"{req['id']}: bağlamsız istekte not var")
        text = normalize(rec["text"])
        stats["eksi_düzeltildi"] += text != rec["text"]
        text, added, deviates = warn_kernaussagen(text, req["plan"])
        if deviates:
            stats["ka_sapma_dışarıda"] += 1
            continue
        stats["uyarı_eklendi"] += added
        result = check(text, req["plan"], req["facts"], req["notes"])
        if not result["ok"]:
            raise ValueError(f"{req['id']}: düzeltilmiş metin kontrolden geçmiyor: {result['problems'][:2]}")
        messages = build_messages(req["facts"], context) + [{"role": "assistant", "content": text}]
        rows.append({"id": req["id"], "firm_id": req["firm_id"], "period": req["period"], "variant": variant,
                     "prompt_version": PROMPT_VERSION, "plan_version": req["plan"]["plan_version"],
                     "teacher": {"set": teacher_set, "input_sha": rec["input_sha"], "attempts": rec["attempts"],
                                 "model": rec["model"]},
                     "messages": messages})
    return rows, stats


def test_prompts(run: Path, retrieval: dict[tuple[str, str], dict] | None, variant: str) -> list[dict]:
    """Değerlendirme istemleri (hedef metin yok)."""
    cfg, rows = load_config(), []
    for firm_id, fs in sorted(load_run(run).items()):
        for period in commentable_periods(fs):
            context = retrieval[(firm_id, period)] if retrieval is not None else None
            rows.append({"id": f"{firm_id}_{period}", "firm_id": firm_id, "period": period, "variant": variant,
                         "prompt_version": PROMPT_VERSION,
                         "messages": build_messages(build_facts(fs, period, cfg), context)})
    return rows


def write_gz(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # mtime=0: aynı içerik → aynı dosya
    with open(path, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
        for r in rows:
            gz.write((json.dumps(r, ensure_ascii=False) + "\n").encode("utf-8"))


def _retrieval(path: Path) -> dict[tuple[str, str], dict]:
    return {(r["firm_id"], r["period"]): r for r in _jsonl(path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m training", description="Eğitim verisi (docs/12).")
    parser.add_argument("--train-run", type=Path, default=ROOT / "data" / "synthetic" / "train_seed7")
    parser.add_argument("--test-run", type=Path, default=ROOT / "data" / "synthetic" / "reference_seed42")
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--skip-test", action="store_true", help="test istemlerini yazma")
    args = parser.parse_args(argv)

    retrieval = _retrieval(args.train_run / "rag" / "retrieval.jsonl")
    for out_name, teacher_set, variant in SETS:
        rows, stats = build_set(teacher_set, variant, retrieval)
        write_gz(rows, args.out / f"{out_name}.jsonl.gz")
        chars = sorted(sum(len(m["content"]) for m in r["messages"]) for r in rows)
        print(f"{out_name}: {len(rows)} örnek ({stats['kabul']}/{stats['istek']} kabul; Kernaussage sapması "
              f"dışarıda {stats['ka_sapma_dışarıda']}; eksi düzeltilen {stats['eksi_düzeltildi']}; uyarı eklenen "
              f"{stats['uyarı_eklendi']}); karakter medyan {chars[len(chars) // 2]}, en fazla {chars[-1]}")
    if not args.skip_test:
        rag = args.test_run / "rag"
        for variant, path in (("ohne_kontext", None), ("rag_k8", rag / "retrieval.jsonl"),
                              ("rag_alle", rag / "retrieval_alle.jsonl")):
            rows = test_prompts(args.test_run, _retrieval(path) if path else None, variant)
            write_gz(rows, args.out / f"test_{variant}.jsonl.gz")
            print(f"test_{variant}: {len(rows)} istem")
    return 0
