"""Muhasebe pratikleri: ekonomik gerçek seri → kaydedilen BWA (docs/01, Bölüm 4; docs/03, E13–E18).

Her pratik kaydedilen seriyi değiştirir ve bir olay olarak kaydedilir. Böylece
kaydedilen − gerçek = çarpıklık olaylarının etkilerinin toplamı olur.
"""

import numpy as np

from .events import Event
from .lines import EPS, LINE_INDEX
from .timeline import Timeline
from .variant import Variant

PERS = LINE_INDEX["personalkosten"]
VERS = LINE_INDEX["versicherungen_beitraege"]
BV = LINE_INDEX["bestandsveraenderungen_fe_ue"]
MAT = LINE_INDEX["material_wareneinkauf"]
AFA = LINE_INDEX["abschreibungen"]


class _Book:
    """Kaydedilen seriyi tutar; her değişikliği bir olaya yazar."""

    def __init__(self, true: np.ndarray, firm_id: str):
        self.booked = true.copy()
        self.firm_id = firm_id
        self.events: list[Event] = []

    def record(self, etype: str, start: int, end: int | None, shape: str,
               new_values: dict[int, np.ndarray], params: dict | None = None,
               near: bool = False) -> Event:
        before = self.booked.copy()
        for row, values in new_values.items():
            self.booked[row] = values
        ev = Event(firm_id=self.firm_id, type=etype, start=start, end=end, shape=shape,
                   params=params or {}, near_threshold=near)
        ev.before, ev.deltas = before, self.booked - before
        self.events.append(ev)
        return ev


def _month_in_year(timeline: Timeline, months: list[int], moy: int) -> int | None:
    found = [i for i in months if timeline.month_of_year(i) == moy]
    return found[0] if found else None


def _sonderzahlungen(book: _Book, true: np.ndarray, variant: Variant, timeline: Timeline) -> None:
    """E13/E14: Urlaubs- ve Weihnachtsgeld tahakkuksuz, ödeme ayında (P1)."""
    p = variant.practices
    total_share = p.urlaubsgeld_share + p.weihnachtsgeld_share
    for etype, share, moy in (("E13", p.urlaubsgeld_share, 5), ("E14", p.weihnachtsgeld_share, 10)):
        for year in timeline.years:
            months = timeline.year_indices(year)
            pay = _month_in_year(timeline, months, moy)
            if pay is None:
                continue
            wage = true[PERS, months] / (1 + total_share / 12)  # tahakkuksuz aylık ücret
            payment = share * wage[months.index(pay)]
            row = book.booked[PERS].copy()
            row[months] -= payment / 12  # gerçek seride her aya düşen tahakkuk geri alınır
            row[pay] += payment          # ödeme ayında tek seferde kaydedilir; yıllık toplam değişmez
            # start = ödeme ayı; tahakkuk farkı yılın bütün aylarına yayılır (end = yıl sonu).
            ev = book.record(etype, pay, months[-1], "periodisch", {PERS: row},
                             {"share_of_monthly_wage_pct": round(share * 100, 1)})
            ev.expected_flags = [(pay, "V1", "personalkosten")]


def _jahrespraemien(book: _Book, variant: Variant, timeline: Timeline) -> None:
    """E15: yıllık sigorta primi Ocak'ta tek seferde (P2)."""
    share = variant.practices.praemien_share
    for year in timeline.years:
        months = timeline.year_indices(year)
        jan = _month_in_year(timeline, months, 0)
        if jan is None or len(months) < 12:
            continue
        row = book.booked[VERS].copy()
        values = row[months].copy()
        row[months] = (1 - share) * values
        row[jan] += share * values.sum()
        ev = book.record("E15", jan, months[-1], "periodisch", {VERS: row},
                         {"premium_share_pct": round(share * 100, 1),
                          "jan_multiple": round(1 + 11 * share, 2)})
        ev.expected_flags = [(jan, "V1", "versicherungen_beitraege")]


def _bestand_quartal(book: _Book, timeline: Timeline) -> None:
    """E16 sistematik, üretici: Bestandsveränderung yalnızca çeyrek sonlarında (P3)."""
    for q_start in range(timeline.n):
        if timeline.month_of_year(q_start) % 3 != 0 or q_start + 2 >= timeline.n:
            continue
        months = [q_start, q_start + 1, q_start + 2]
        row = book.booked[BV].copy()
        quarter_total = row[months].sum()
        row[months[:2]] = 0.0
        row[months[2]] = quarter_total
        ev = book.record("E16", q_start, months[2], "periodisch", {BV: row}, {"mode": "quartal"})
        ev.expected_flags = [(m, "V2", "bestandsveraenderungen_fe_ue") for m in months[:2]
                             if abs(ev.deltas[BV, m]) > EPS]
        ev.expected_flags.append((months[2], "V4", "bestandsveraenderungen_fe_ue"))


def _bestand_inventur(book: _Book, timeline: Timeline) -> None:
    """E16 sistematik, ticaret: mal stok değişimi yalnızca envanterde, Wareneinkauf satırında (P3).

    Yıl içinde satırda alışlar görünür (alış satıştan bir ay önce gelir); Aralık'taki envanter
    kaydı yıllık toplamı ekonomik gerçeğe eşitler.
    """
    for year in timeline.years:
        months = timeline.year_indices(year)
        if len(months) < 12:
            continue
        row = book.booked[MAT].copy()
        consumption = row[months].copy()           # Wareneinsatz (ekonomik gerçek)
        purchases = np.append(consumption[1:], 0.0)  # Einkauf_m ≈ Wareneinsatz_m+1
        purchases[-1] = consumption.sum() - purchases[:-1].sum()  # Aralık: envanter kaydı
        row[months] = purchases
        ev = book.record("E16", months[0], months[-1], "periodisch", {MAT: row}, {"mode": "inventur"})
        ev.expected_flags = [(m, "V2", "material_wareneinkauf") for m in months[:-1]]
        ev.expected_flags.append((months[-1], "V4", "material_wareneinkauf"))


def _pick_month(occupancy: np.ndarray, row: int, months: list[int], gen: dict,
                rng: np.random.Generator) -> int | None:
    """t ve t+1 aylarında satır doluluğu sınırı aşmayan bir ay seçer; dolu aylar yalnızca
    `overlap_accept_share` olasılıkla kabul edilir (events.sample_pool_events ile aynı kural)."""
    cap = gen["events"]["max_events_per_line_month"]
    free = [t for t in months if occupancy[row, t] < cap and occupancy[row, t + 1] < cap]
    for _ in range(20):
        if not free:
            return None
        t = int(rng.choice(free))
        if not occupancy[row, [t, t + 1]].any() or rng.random() < gen["events"]["overlap_accept_share"]:
            return t
    return None


def _bestand_episodisch(book: _Book, variant: Variant, timeline: Timeline, occupancy: np.ndarray,
                        gen: dict, rng: np.random.Generator) -> None:
    """E16 epizodik: bir ay unutulur, ertesi ay telafi edilir (havuz olayı)."""
    for y, year in enumerate(timeline.years):
        months = [t for t in timeline.year_indices(year) if t + 1 < timeline.n]
        for _ in range(variant.practices.episodic_bv_per_year[y]):
            t = _pick_month(occupancy, BV, months, gen, rng)
            if t is None:
                break
            row = book.booked[BV].copy()
            row[t + 1] += row[t]
            row[t] = 0.0
            ev = book.record("E16", t, t + 1, "temporär", {BV: row}, {"mode": "episodisch"})
            ev.expected_flags = [(t, "V2", "bestandsveraenderungen_fe_ue"),
                                 (t + 1, "V4", "bestandsveraenderungen_fe_ue")]
            occupancy[BV, [t, t + 1]] += 1
            months.remove(t)


def _afa_jahresende(book: _Book, timeline: Timeline) -> None:
    """E17: AfA yalnızca yıl sonunda (P4)."""
    for year in timeline.years:
        months = timeline.year_indices(year)
        if len(months) < 12:
            continue
        row = book.booked[AFA].copy()
        total = row[months].sum()
        row[months[:-1]] = 0.0
        row[months[-1]] = total
        ev = book.record("E17", months[0], months[-1], "periodisch", {AFA: row},
                         {"annual_total": round(float(total), 2)})
        ev.expected_flags = [(m, "V3", "abschreibungen") for m in months]


def _spaete_rechnungen(book: _Book, variant: Variant, timeline: Timeline, gen: dict,
                       occupancy: np.ndarray, rng: np.random.Generator) -> None:
    """E18: geç gelen alış faturaları — t ayında eksik, t+1 ayında fazla (P5, havuz olayı)."""
    mag = gen["events"]["magnitude"]
    share_near = gen["events"]["near_threshold_share"]
    for y, year in enumerate(timeline.years):
        months = [t for t in timeline.year_indices(year) if t + 1 < timeline.n]
        for _ in range(variant.practices.p5_per_year[y]):
            line = "material_wareneinkauf" if rng.random() < mag["E18_material_share"] else "sonstige_kosten"
            row_idx = LINE_INDEX[line]
            t = _pick_month(occupancy, row_idx, months, gen, rng)
            if t is None:
                continue
            near = bool(rng.random() < share_near)
            lo, hi = mag["E18_pct_material" if line == "material_wareneinkauf" else "E18_pct_other"]
            pct = lo + (hi - lo) * (rng.uniform(0, 0.25) if near else rng.uniform(0, 1))
            row = book.booked[row_idx].copy()
            shifted = pct / 100.0 * row[t]
            row[t] -= shifted
            row[t + 1] += shifted
            ev = book.record("E18", t, t + 1, "temporär", {row_idx: row},
                             {"line": line, "pct_shifted": round(pct, 1)}, near)
            ev.expected_flags = [(t + 1, "V4", line)]
            occupancy[row_idx, [t, t + 1]] += 1
            months.remove(t)


def apply_practices(variant: Variant, true: np.ndarray, timeline: Timeline, gen: dict,
                    occupancy: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, list[Event]]:
    """Döner: (kaydedilen seri, çarpıklık olayları E13–E18)."""
    p = variant.practices
    book = _Book(true, variant.firm_id)
    if p.p1_sonderzahlungen:
        _sonderzahlungen(book, true, variant, timeline)
    if p.p2_jahrespraemien:
        _jahrespraemien(book, variant, timeline)
    if p.p3_bestand:
        if variant.kind == "trader":
            _bestand_inventur(book, timeline)
        else:
            _bestand_quartal(book, timeline)
    elif variant.kind == "producer":
        _bestand_episodisch(book, variant, timeline, occupancy, gen, rng)
    if p.p4_afa_jahresende:
        _afa_jahresende(book, timeline)
    _spaete_rechnungen(book, variant, timeline, gen, occupancy, rng)
    return book.booked, book.events
