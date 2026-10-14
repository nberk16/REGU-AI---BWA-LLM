"""Parametre dosyalarının yüklenmesi (generator/config/*.toml)."""

import hashlib
import tomllib
from dataclasses import dataclass
from pathlib import Path

CONFIG_DIR = Path(__file__).parent / "config"


@dataclass(frozen=True)
class Archetype:
    code: str
    name: str
    branche: str
    kind: str  # "producer" | "trader"
    employees: int
    revenue_2024: float
    tariff_month: int  # 1..12
    herstell_factor: float
    bv_noise_pct: float
    season: tuple[float, ...]
    production_shift: tuple[float, ...]
    trend_v00_pct: float
    trend_v00_2026_pct: float
    events_excluded: tuple[str, ...]
    fair_annual: bool
    name_words: tuple[str, ...]
    quotas: dict[str, float]  # oran (0..1), Gesamtleistung'a göre
    practices: dict
    v00_practices: dict
    vocab: dict[str, list[str]]

    @property
    def number(self) -> int:
        return int(self.code[1:])


def _read(name: str, path: Path | None) -> dict:
    with open(path or CONFIG_DIR / name, "rb") as f:
        return tomllib.load(f)


def load_archetypes(path: Path | None = None) -> dict[str, Archetype]:
    raw = _read("archetypes.toml", path)
    archetypes = {}
    for code, a in raw.items():
        archetypes[code] = Archetype(
            code=code,
            name=a["name"],
            branche=a["branche"],
            kind=a["kind"],
            employees=int(a["employees"]),
            revenue_2024=float(a["revenue_2024"]),
            tariff_month=int(a["tariff_month"]),
            herstell_factor=float(a["herstell_factor"]),
            bv_noise_pct=float(a["bv_noise_pct"]),
            season=tuple(a["season"]),
            production_shift=tuple(a["production_shift"]),
            trend_v00_pct=float(a["trend_v00_pct"]),
            trend_v00_2026_pct=float(a["trend_v00_2026_pct"]),
            events_excluded=tuple(a["events_excluded"]),
            fair_annual=bool(a["fair_annual"]),
            name_words=tuple(a["name_words"]),
            quotas={k: v / 100.0 for k, v in a["quotas"].items()},
            practices=dict(a["practices"]),
            v00_practices=dict(a["v00_practices"]),
            vocab={k: list(v) for k, v in a["vocab"].items()},
        )
    return archetypes


def load_generation(path: Path | None = None) -> dict:
    return _read("generation.toml", path)


def load_templates(path: Path | None = None) -> dict:
    return _read("note_templates.toml", path)


def config_fingerprint() -> str:
    """Parametre dosyalarının özeti; manifest'e yazılır."""
    h = hashlib.sha256()
    for name in ("archetypes.toml", "generation.toml", "note_templates.toml"):
        h.update((CONFIG_DIR / name).read_bytes())
    return h.hexdigest()[:16]
