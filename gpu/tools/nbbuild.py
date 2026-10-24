"""Kaggle defterlerini Python kaynaklarından yazan küçük yardımcılar (gpu/tools/nb_*.py).

Defterler elle değil bu betiklerle düzenlenir: `python gpu/tools/nb_02_finetune.py` → `gpu/02_finetune.ipynb`.
"""

import json
from pathlib import Path

GPU = Path(__file__).resolve().parents[1]
METADATA = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
    "kaggle": {"accelerator": "gpu", "isInternetEnabled": True},
}


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(keepends=True)}


def write(name: str, cells: list[dict], target: Path | None = None) -> Path:
    path = target or GPU / name
    nb = {"cells": cells, "metadata": METADATA, "nbformat": 4, "nbformat_minor": 5}
    path.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("yazıldı:", path, len(cells), "hücre")
    return path
