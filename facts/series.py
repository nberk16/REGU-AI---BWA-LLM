"""Modele görünür dosyaların okunması: `model_input/bwa_raw.csv` ve `model_input/firms.json`."""

import csv
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .schema import BASE_LINES, add_subtotals


@dataclass
class FirmSeries:
    firm_id: str
    name: str
    periods: list[str]               # "YYYY-MM", artan sırada
    values: dict[str, np.ndarray]    # 21 temel satır + ara toplamlar, ay başına bir değer

    def index(self, period: str) -> int:
        return self.periods.index(period)


def load_run(run_dir: Path) -> dict[str, FirmSeries]:
    run_dir = Path(run_dir)
    raw: dict[str, dict[str, dict[str, float]]] = {}
    with open(run_dir / "model_input" / "bwa_raw.csv", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            raw.setdefault(row["firm_id"], {}).setdefault(row["period"], {})[row["line"]] = float(row["value"])
    names = {f["firm_id"]: f["name"] for f in json.loads((run_dir / "model_input" / "firms.json").read_text(encoding="utf-8"))}

    firms = {}
    for firm_id, by_period in raw.items():
        periods = sorted(by_period)
        base = {k: np.array([by_period[p].get(k, 0.0) for p in periods]) for k in BASE_LINES}
        firms[firm_id] = FirmSeries(firm_id, names.get(firm_id, firm_id), periods, add_subtotals(base))
    return firms
