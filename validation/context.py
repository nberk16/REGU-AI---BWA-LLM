"""Modele verilen bağlam notları (K-C).

[KARAR, tur 4] RAG penceresi 13 ay (t−12 … t) + dönemsiz `Firmenprofil` notu. Katman 2 (top-k getirme)
hazır olana kadar doğrulama, penceredeki bütün notları "verilmiş" sayar.
"""

import json
from pathlib import Path


def shift(period: str, months: int) -> str:
    y, m = map(int, period.split("-"))
    idx = y * 12 + (m - 1) + months
    return f"{idx // 12:04d}-{idx % 12 + 1:02d}"


def load_notes(run_dir: Path) -> list[dict]:
    path = Path(run_dir) / "model_input" / "context_notes.jsonl"
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def window_notes(notes: list[dict], firm_id: str, period: str, months: int = 13) -> list[dict]:
    start = shift(period, -(months - 1))
    return [n for n in notes
            if n["firm_id"] == firm_id and (n["period"] is None or start <= n["period"] <= period)]
