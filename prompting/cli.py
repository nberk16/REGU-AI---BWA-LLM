"""Komut satırı (docs/10_istem.md, Bölüm 5): bir koşunun bütün yorumlanabilir ayları için istemleri yazar.

    python -m prompting --run DIR                                  # bağlamsız (çıplak model, yalnızca FT)
    python -m prompting --run DIR --retrieval DIR/rag/retrieval.jsonl   # RAG (top-k ya da k = 0: bütün notlar)

Çıktı: <run>/prompts/<varyant>.jsonl (repoda tutulmaz). Kayıt: id, firm_id, period, prompt_version, variant,
messages. Kaggle defterleri bu dosyayı okur; GPU tarafında facts ve embedding hesaplanmaz.
"""

import argparse
import json
from pathlib import Path

from .templates import PROMPT_VERSION, build_messages


def load_retrieval(path: Path) -> dict[tuple[str, str], dict]:
    with open(path, encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]
    return {(r["firm_id"], r["period"]): r for r in records}


def variant_name(record: dict | None) -> str:
    if record is None:
        return "ohne_kontext"
    return "rag_alle" if record["k"] == 0 else f"rag_k{record['k']}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m prompting", description="İstemleri yazar (docs/10).")
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--retrieval", type=Path, help="python -m rag export çıktısı; yoksa bağlamsız varyant")
    parser.add_argument("--firms", nargs="*", help="yalnızca bu firmalar (ör. A1-v00)")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    from facts.build import build_facts, commentable_periods
    from facts.schema import load_config
    from facts.series import load_run

    contexts = load_retrieval(args.retrieval) if args.retrieval else None
    fcfg = load_config()
    rows = []
    for firm_id, fs in sorted(load_run(args.run).items()):
        if args.firms and firm_id not in args.firms:
            continue
        for period in commentable_periods(fs):
            record = None
            if contexts is not None:
                if (firm_id, period) not in contexts:
                    parser.error(f"{args.retrieval} içinde {firm_id} {period} yok")
                record = contexts[(firm_id, period)]
            rows.append({"id": f"{firm_id}_{period}", "firm_id": firm_id, "period": period,
                         "prompt_version": PROMPT_VERSION, "variant": variant_name(record),
                         "messages": build_messages(build_facts(fs, period, fcfg), record)})
    if not rows:
        parser.error("yorumlanabilir ay bulunamadı")
    variants = {r["variant"] for r in rows}
    if len(variants) > 1:
        parser.error(f"retrieval dosyasında birden fazla k var: {sorted(variants)}")
    out = args.out or args.run / "prompts" / f"{variants.pop()}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    chars = sorted(sum(len(m["content"]) for m in r["messages"]) for r in rows)
    print(f"{len(rows)} istem ({rows[0]['variant']}, sürüm {PROMPT_VERSION}) → {out}")
    de = lambda n: f"{n:,}".replace(",", ".")
    print(f"İstem uzunluğu (karakter): medyan {de(chars[len(chars) // 2])}, en fazla {de(chars[-1])}")
    return 0
