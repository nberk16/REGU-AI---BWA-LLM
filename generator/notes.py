"""Bağlam notları (K-C) ve not–olay eşlemesi (docs/03, Bölüm 5).

- Gerçek olayların (E01–E12) ~%70'i notlanır; seçim her olay türü içinde dengelidir.
- V1–V4 (E13–E18) hiç notlanmaz.
- Sezon (E19) varyantların ~%70'inde dönemsiz `Firmenprofil` notuyla belgelenir.
- Ayların ~%12'sine etkisiz çeldirici not eklenir.
- Kalıp seçimi seed'e bağlıdır; rakamlı/rakamsız kalıp oranı ~%50.
"""

import re

import numpy as np

from .events import REAL_AND_V5, Event
from .timeline import Timeline
from .variant import Variant

_PLACEHOLDER = re.compile(r"\{(\w+)\}")
_NUMERIC_KEYS = ("n", "p", "betrag")
_GOLDEN = 0.6180339887498949


def _stochastic_round(x: float, rng: np.random.Generator) -> int:
    base = int(np.floor(x))
    return base + int(rng.random() < x - base)


def round_amount(x: float) -> int:
    x = abs(x)
    step = 1_000 if x < 100_000 else 5_000 if x < 1_000_000 else 10_000
    return max(step, int(round(x / step)) * step)


def format_eur(x: int) -> str:
    return f"{x:,}".replace(",", ".") + " €"


def format_pct(x: float) -> str:
    if float(x).is_integer():
        return f"{int(x)} %"
    return f"{x:.1f}".replace(".", ",") + " %"


def _note_number(key: str, etype: str, value: float):
    """Notta görünen (yuvarlanmış) değer."""
    if key == "n":
        return int(value)
    if key == "betrag":
        return round_amount(value)
    if etype == "E03":
        return max(0.5, round(value * 2) / 2)
    return max(1, int(round(value)))


def _render(template: str, values: dict) -> tuple[str, list]:
    numbers = []
    rendered = {}
    for key in _PLACEHOLDER.findall(template):
        value = values[key]
        if key == "betrag":
            rendered[key] = format_eur(value)
            numbers.append(value)
        elif key == "p":
            rendered[key] = format_pct(value)
            numbers.append(value)
        elif key == "n":
            rendered[key] = str(value)
            numbers.append(value)
        else:
            rendered[key] = value
    return template.format(**rendered), numbers


def _event_text(ev: Event, variant: Variant, timeline: Timeline, templates: dict, gen: dict,
                rng: np.random.Generator) -> tuple[str, list]:
    spec = templates[ev.type]
    with_number = rng.random() < gen["notes"]["number_share"]
    pool = spec["with_number"] if with_number else spec["without_number"]
    template = pool[int(rng.integers(len(pool)))]

    vocab = variant.archetype.vocab
    values = {
        "monat": timeline.month_name(ev.start),
        "bereich": str(rng.choice(vocab["bereiche"])),
        "material": str(rng.choice(vocab["material"])),
        "kunde": str(rng.choice(vocab["kunden"])),
        "anlage": str(rng.choice(vocab["anlagen"])),
        "altanlage": str(rng.choice(vocab["altanlagen"])),
        "reparatur": str(rng.choice(vocab["reparatur"])),
        "zusatz": spec.get("zusatz_temporaer", "") if ev.shape == "temporär" else "",
    }
    for key in _NUMERIC_KEYS:
        if key in ev.note_values:
            values[key] = _note_number(key, ev.type, ev.note_values[key])
    return _render(template, values)


def generate_notes(variant: Variant, events: list[Event], timeline: Timeline, templates: dict,
                   gen: dict, rng: np.random.Generator) -> tuple[list[dict], list[dict]]:
    """Notları üretir, olaylara `documented`/`source_id` yazar.

    Döner: (modele görünür notlar, değerlendirme için not–olay eşlemesi)
    """
    cfg = gen["notes"]
    by_month: dict[int, list[tuple[str, object]]] = {}

    # 1) Hangi gerçek olaylar notlanacak? (tür içinde dengeli seçim)
    for etype in REAL_AND_V5:
        same_type = [e for e in events if e.type == etype]
        k = _stochastic_round(cfg["documented_share"] * len(same_type), rng)
        for pos in rng.permutation(len(same_type))[:k]:
            ev = same_type[int(pos)]
            ev.documented = True
            by_month.setdefault(ev.start, []).append(("event", ev))

    # 2) Çeldirici notlar
    distractors = templates["distractor"]
    for i in range(timeline.n):
        if rng.random() < cfg["distractor_month_share"]:
            by_month.setdefault(i, []).append(("distractor", distractors[int(rng.integers(len(distractors)))]))

    notes, notes_gt = [], []

    # 3) Dönemsiz firma notu (sezon). Varyant sayısı az olduğu için yazı-tura yerine düşük farklılıklı
    #    bir dizi kullanılır: her arketipte varyantların ~%70'i firma notu alır, v00 her zaman alır.
    season = next(e for e in events if e.type == "E19")
    if (variant.index * _GOLDEN) % 1.0 < cfg["season_note_share"]:
        pool = templates["E19"][variant.archetype.code]
        season.documented, season.source_id = True, "Firmenprofil"
        notes.append({"source_id": "Firmenprofil", "firm_id": variant.firm_id, "period": None,
                      "duration": "dauerhaft", "text": pool[int(rng.integers(len(pool)))]})
        notes_gt.append({"source_id": "Firmenprofil", "firm_id": variant.firm_id,
                         "event_id": season.event_id, "distractor": False, "numbers": []})

    # 4) Aylık notlar; ay içindeki sıra karıştırılır (çeldirici hep "#2" olmasın)
    for i in sorted(by_month):
        items = by_month[i]
        order = rng.permutation(len(items))
        for k, pos in enumerate(order, start=1):
            kind, obj = items[int(pos)]
            source_id = f"Kontextnotiz {timeline.period(i)}" + ("" if k == 1 else f" #{k}")
            if kind == "event":
                text, numbers = _event_text(obj, variant, timeline, templates, gen, rng)
                obj.source_id = source_id
                duration, event_id = obj.duration, obj.event_id
            else:
                text, numbers = _render(obj["text"], {
                    "monat": timeline.month_name(i),
                    "bereich": str(rng.choice(variant.archetype.vocab["bereiche"])),
                })
                duration, event_id = obj["duration"], None
            notes.append({"source_id": source_id, "firm_id": variant.firm_id,
                          "period": timeline.period(i), "duration": duration, "text": text})
            notes_gt.append({"source_id": source_id, "firm_id": variant.firm_id,
                             "event_id": event_id, "distractor": kind == "distractor",
                             "numbers": numbers})
    return notes, notes_gt
