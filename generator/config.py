"""Parametre dosyalarının yüklenmesi (generator/config/*.toml)."""

import hashlib
import tomllib
from dataclasses import dataclass
from pathlib import Path

CONFIG_DIR = Path(__file__).parent / "config"
PROFILE_DIR = CONFIG_DIR / "profiles"


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


def deep_merge(base: dict, override: dict) -> dict:
    """override'daki değerleri base'e iç içe yazar (profil dosyaları için)."""
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_profile(name: str | None) -> dict:
    """Profil: ana parametrelerin üzerine yazılan küçük bir TOML dosyası (generator/config/profiles/).

    Bölümler: [archetypes] → archetypes.toml, [generation] → generation.toml,
    [balanced_v2] → dengelenmiş V2 test kümesi seçimi (v2_set.py).
    """
    if not name:
        return {}
    path = PROFILE_DIR / f"{name}.toml"
    if not path.exists():
        available = ", ".join(sorted(p.stem for p in PROFILE_DIR.glob("*.toml")))
        raise ValueError(f"Bilinmeyen profil: {name} (mevcut: {available})")
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_archetypes(path: Path | None = None, overrides: dict | None = None) -> dict[str, Archetype]:
    raw = deep_merge(_read("archetypes.toml", path), overrides or {})
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


def load_generation(path: Path | None = None, overrides: dict | None = None) -> dict:
    return deep_merge(_read("generation.toml", path), overrides or {})


def load_templates(path: Path | None = None) -> dict:
    return _read("note_templates.toml", path)


def config_fingerprint(profile: str | None = None) -> str:
    """Parametre dosyalarının (ve varsa profilin) özeti; manifest'e yazılır."""
    h = hashlib.sha256()
    for name in ("archetypes.toml", "generation.toml", "note_templates.toml"):
        h.update((CONFIG_DIR / name).read_bytes())
    if profile:
        h.update((PROFILE_DIR / f"{profile}.toml").read_bytes())
    return h.hexdigest()[:16]
