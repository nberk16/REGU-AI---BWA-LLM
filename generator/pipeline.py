"""Varyant başına üretim akışı (docs/04_veri_ureteci.md, Bölüm 2).

1. Varyant parametreleri     → variant.py
2. Ekonomik taban seri       → model.py
3. Gerçek olaylar (E01–E12)  → events.py
4. Gürültü                   → model.apply_noise
5. Muhasebe pratikleri       → practices.py (E13–E18; kaydedilen seri)
6. Sezon kaydı (E19), kimlikler, çakışmalar
7. Bağlam notları            → notes.py
8. Ground truth              → ground_truth.py

Her aşamanın kendi rastgele sayı akışı vardır: [seed, arketip, varyant, aşama]. Böylece varyant
sayısını artırmak mevcut varyantları değiştirmez.
"""

from dataclasses import dataclass

import numpy as np

from .config import Archetype, load_archetypes, load_generation, load_templates
from .events import Event, apply_pool_events, assign_ids, mark_overlaps, sample_pool_events, season_event
from .ground_truth import add_acceptable_flags, month_records
from .model import apply_noise, make_base
from .notes import generate_notes
from .practices import apply_practices
from .timeline import Timeline
from .variant import Variant, make_variant

_STAGES = {"variant": 0, "base": 1, "events": 2, "noise": 3, "practices": 4, "notes": 5}


@dataclass
class VariantResult:
    variant: Variant
    baseline: np.ndarray  # olaysız ekonomik seri
    economic: np.ndarray  # olaylı ekonomik seri, gürültüsüz
    true: np.ndarray      # ekonomik gerçek (gürültülü) — değerlendirme
    booked: np.ndarray    # kaydedilen BWA — modele görünür
    events: list[Event]
    notes: list[dict]
    notes_gt: list[dict]
    months: list[dict]


def _rng(seed: int, arch: Archetype, index: int, stage: str) -> np.random.Generator:
    return np.random.default_rng([seed, arch.number, index, _STAGES[stage]])


def generate_variant(arch: Archetype, index: int, seed: int, gen: dict, templates: dict,
                     timeline: Timeline) -> VariantResult:
    variant = make_variant(arch, index, gen, timeline, _rng(seed, arch, index, "variant"))
    base = make_base(variant, timeline, gen, _rng(seed, arch, index, "base"))

    pool, occupancy = sample_pool_events(variant, timeline, gen, _rng(seed, arch, index, "events"))
    baseline, economic = apply_pool_events(variant, base, pool, timeline, gen)
    true = apply_noise(economic, gen, _rng(seed, arch, index, "noise"))
    booked, distortions = apply_practices(variant, true, timeline, gen, occupancy,
                                          _rng(seed, arch, index, "practices"))

    events = pool + distortions + [season_event(variant, timeline, gen)]
    events.sort(key=lambda e: (e.start, e.type))
    assign_ids(events, timeline)
    mark_overlaps(events)

    notes, notes_gt = generate_notes(variant, events, timeline, templates, gen,
                                     _rng(seed, arch, index, "notes"))
    add_acceptable_flags(events)
    months = month_records(events, notes_gt, notes, timeline, variant.firm_id)
    return VariantResult(variant, baseline, economic, true, booked, events, notes, notes_gt, months)


def generate_run(archetype_codes: list[str], variants_per_archetype: int, seed: int,
                 gen: dict | None = None, templates: dict | None = None,
                 archetypes: dict[str, Archetype] | None = None) -> tuple[Timeline, list[VariantResult]]:
    gen = gen or load_generation()
    templates = templates or load_templates()
    archetypes = archetypes or load_archetypes()
    unknown = [c for c in archetype_codes if c not in archetypes]
    if unknown:
        raise ValueError(f"Bilinmeyen arketip: {', '.join(unknown)} (mevcut: {', '.join(archetypes)})")
    if variants_per_archetype < 1:
        raise ValueError("Arketip başına en az 1 varyant gerekir.")
    timeline = Timeline.from_config(gen["series"])
    results = [
        generate_variant(archetypes[code], index, seed, gen, templates, timeline)
        for code in archetype_codes
        for index in range(variants_per_archetype)
    ]
    return timeline, results
