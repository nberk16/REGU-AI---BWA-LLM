"""Ground truth kayıtları (docs/03, Bölüm 7): olay kayıtları ve firma-ay kayıtları."""

import numpy as np

from .events import Event, seasonal_change_pct
from .lines import BASE_LINES, EPS
from .timeline import Timeline


def add_acceptable_flags(events: list[Event]) -> None:
    """Beklenmeyen ama cezalandırılmayan uyarılar (docs/03, Bölüm 7.2 ve 9.1).

    - Notsuz E04/E05: Rohertragsquote değişimi açıklanamaz → V2 uyarısı kabul edilebilir.
    - Her yıl aynı ayda tekrarlanan fuar (A3, E11): desen V1'e benzer → V1 uyarısı kabul edilebilir.
    """
    for ev in events:
        if ev.type in ("E04", "E05") and not ev.documented:
            for m in _rohertrag_months(ev):
                ev.acceptable_flags.append((m, "V2", "material_wareneinkauf"))
    fairs = sorted((e for e in events if e.type == "E11"), key=lambda e: e.start)
    for ev in fairs:
        if any(prev.start == ev.start - 12 for prev in fairs):
            ev.acceptable_flags.append((ev.start, "V1", "werbe_reisekosten"))


def _rohertrag_months(ev: Event) -> list[int]:
    """Olayın Rohertragsquote'yi değiştirdiği aylar."""
    if ev.type == "E05":
        return [ev.start]
    if ev.type == "E04":
        months = [ev.start]
        if ev.end is not None and ev.deltas is not None and ev.end + 1 < ev.deltas.shape[1]:
            months.append(ev.end + 1)  # geçici zammın sona erdiği ay
        return months
    if ev.type == "E16":
        return ev.active_months()
    if ev.type == "E18" and ev.params.get("line") == "material_wareneinkauf":
        return ev.active_months()
    return []


def _flags(items: list[tuple[int, str, str]], timeline: Timeline) -> list[dict]:
    return [{"period": timeline.period(m), "code": code, "line": line} for m, code, line in items]


def event_record(ev: Event, timeline: Timeline) -> dict:
    effects = []
    if ev.deltas is not None:
        for row in np.nonzero(np.abs(ev.deltas).max(axis=1) > EPS)[0]:
            months = np.nonzero(np.abs(ev.deltas[row]) > EPS)[0]
            first = int(months[0])
            before = ev.before[row, first]
            effects.append({
                "line": BASE_LINES[row],
                "from": timeline.period(first),
                "to": timeline.period(int(months[-1])),
                "abs_at_start": round(float(ev.deltas[row, first]), 2),
                "pct_at_start": round(float(ev.deltas[row, first] / before * 100), 1) if abs(before) > EPS else None,
                "total_abs": round(float(ev.deltas[row].sum()), 2),
            })
    return {
        "event_id": ev.event_id,
        "firm_id": ev.firm_id,
        "type": ev.type,
        "category": ev.category,
        "start": timeline.period(ev.start),
        "end": None if ev.end is None else timeline.period(ev.end),
        "shape": ev.shape,
        "duration": ev.duration,
        "lines": ev.lines() if ev.deltas is not None else ["umsatzerloese"],
        "magnitude": ev.params,
        "effects": effects,
        "documented": ev.documented,
        "source_id": ev.source_id,
        "expected_flags": _flags(ev.expected_flags, timeline),
        "acceptable_flags": _flags(ev.acceptable_flags, timeline),
        "expected_treatment": ev.expected_treatment,
        "near_threshold": ev.near_threshold,
        "overlaps_with": ev.overlaps_with,
    }


def _v2_decision(causes: list[dict]) -> str | None:
    """Katman 1'in V2 adayı karşısında beklenen model kararı (docs/03, Bölüm 9.1).

    warn   : muhasebe kaynaklı bir neden var → uyarı dili
    cite   : yalnızca notlu gerçek nedenler var → kaynakla açıkla, V2 uyarısı verme
    either : yalnızca notsuz gerçek nedenler var → uyarı veya hipotez kabul edilir
    """
    if not causes:
        return None
    if any(c["kind"] == "distortion" for c in causes):
        return "warn"
    if all(c["documented"] for c in causes):
        return "cite"
    return "either"


def month_records(events: list[Event], notes_gt: list[dict], notes: list[dict],
                  timeline: Timeline, firm_id: str) -> list[dict]:
    flows = [e for e in events if e.deltas is not None]
    # active: bu ayın önceki aya / önceki yılın aynı ayına göre karşılaştırmasını etkileyebilecek olaylar.
    # Kalıcı bir basamak yalnızca ilk 12 ayında önceki yıl karşılaştırmasında fark yaratır.
    active = {i: [] for i in range(timeline.n)}
    non_permanent = {i: set() for i in range(timeline.n)}
    for ev in flows:
        for m in ev.active_months():
            if ev.shape != "dauerhaft" or m - ev.start <= 11:
                active[m].append(ev.event_id)
            if ev.shape != "dauerhaft":
                non_permanent[m].add(ev.event_id)
    note_period = {n["source_id"]: n["period"] for n in notes}
    distractors = {g["source_id"] for g in notes_gt if g["distractor"]}

    records = []
    season = next(e for e in events if e.type == "E19")
    for i in range(timeline.n):
        period = timeline.period(i)
        expected, acceptable = [], []
        for ev in events:
            expected += [{"code": c, "line": l, "event_id": ev.event_id} for m, c, l in ev.expected_flags if m == i]
            acceptable += [{"code": c, "line": l, "event_id": ev.event_id} for m, c, l in ev.acceptable_flags if m == i]
        causes = [
            {"event_id": ev.event_id, "type": ev.type,
             "kind": "real" if ev.category == "R" else "distortion", "documented": ev.documented}
            for ev in flows if i in _rohertrag_months(ev)
        ]
        new_pool = [e.event_id for e in flows if e.start == i and e.is_pool]
        month_notes = [s for s, p in note_period.items() if p == period]
        records.append({
            "firm_id": firm_id,
            "period": period,
            "commentable": i >= timeline.commentable_from,
            "new_events": [e.event_id for e in flows if e.start == i],
            "active_events": active[i],
            "vorjahr_events": sorted(non_permanent[i - 12] - non_permanent[i]) if i >= 12 else [],
            "expected_flags": expected,
            "acceptable_flags": acceptable,
            "rohertrag_causes": causes,
            "v2_candidate_decision": _v2_decision(causes),
            "notes": month_notes,
            "distractor_notes": [s for s in month_notes if s in distractors],
            "quiet_month": not new_pool,
            "seasonal_change_pct": seasonal_change_pct(season, timeline, i),
        })
    return records
