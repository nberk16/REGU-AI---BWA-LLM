"""Komut satırı: python -m generator --archetypes A1,A2,A3 --variants 10 --seed 42"""

import argparse
from pathlib import Path

from .pipeline import generate_run
from .writer import write_run


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m generator",
        description="Sentetik BWA verisi, bağlam notları ve ground truth üretir (docs/04_veri_ureteci.md).",
    )
    parser.add_argument("--archetypes", default="A1,A2,A3", help="virgülle ayrılmış arketip kodları")
    parser.add_argument("--variants", type=int, default=10, help="arketip başına varyant sayısı")
    parser.add_argument("--first-variant", type=int, default=0,
                        help="ilk varyant numarası (ayrı kümelerin referans koşuyla firma paylaşmaması için)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--profile", default=None,
                        help="generator/config/profiles/<ad>.toml (ör. v2_balanced, train_price_boost)")
    parser.add_argument("--out", type=Path, default=None,
                        help="çıktı klasörü (varsayılan: data/synthetic/run_seed<seed>_<arketip>x<varyant>[_<profil>])")
    args = parser.parse_args(argv)

    codes = [c.strip() for c in args.archetypes.split(",") if c.strip()]
    suffix = f"_{args.profile}" if args.profile else ""
    out = args.out or Path("data/synthetic") / f"run_seed{args.seed}_{len(codes)}x{args.variants}{suffix}"
    run = generate_run(codes, args.variants, args.seed, profile=args.profile, first_variant=args.first_variant)
    manifest = write_run(run, out)

    s = manifest["statistics"]
    print(f"{s['variants']} varyant, {s['events_total']} olay → {out}")
    print(f"Notlu gerçek olaylar: {s['documented_share_real_v5']:.1%} · "
          f"olaysız ay: {s['quiet_month_share_commentable']:.1%} · "
          f"çeldirici notlu ay: {s['distractor_month_share']:.1%}")
    if "v2_balanced_set" in s:
        print("Dengelenmiş V2 kümesi:", s["v2_balanced_set"])
