"""Ekonomik gerçek seri: sürücüler (drivers) → 21 temel BWA satırı.

"Ekonomik gerçek", her şey doğru ve zamanında kaydedilseydi BWA'nın göstereceği değerdir.
Olaylar (events.py) yalnızca sürücüleri değiştirir; satırlar her seferinde yeniden hesaplanır.
Böylece her olayın her satıra ve aya etkisi tam olarak ölçülür.
"""

from dataclasses import dataclass, fields

import numpy as np

from .lines import BASE_LINES, LINE_INDEX
from .timeline import Timeline
from .variant import Variant

_FIXED_WITH_INFLATION = (
    "sonstige_betriebliche_erloese",
    "betriebliche_steuern",
    "versicherungen_beitraege",
    "besondere_kosten",
    "fahrzeugkosten",
    "sonstige_kosten",
)


@dataclass(frozen=True)
class Base:
    level: np.ndarray     # ciro trendi; 2024 ortalaması = 1
    infl: np.ndarray      # sabit giderlerin enflasyon kayması; 2024 ortalaması ≈ 1
    afa_runoff: np.ndarray   # mevcut varlıkların AfA'sının azalması; 2024 ortalaması ≈ 1
    zins_runoff: np.ndarray  # kredi geri ödemesiyle faiz tabanının azalması; 2024 ortalaması ≈ 1
    season: np.ndarray    # aylık satış endeksi
    shift: np.ndarray     # aylık üretim − satış
    bv_noise: np.ndarray  # rastgele stok değişimi (aylık satış tabanına oran), yıllık toplamı 0


def make_base(variant: Variant, timeline: Timeline, gen: dict, rng: np.random.Generator) -> Base:
    n = timeline.n
    moy = np.array([timeline.month_of_year(i) for i in range(n)])

    monthly_growth = np.array(
        [(1 + variant.trend_pct[timeline.year(i)] / 100.0) ** (1 / 12) for i in range(n)]
    )
    level = np.cumprod(monthly_growth)
    level /= level[:12].mean()

    years_from_mid_2024 = (np.arange(n) - 5.5) / 12
    infl = (1 + gen["series"]["fixed_cost_inflation_pct"] / 100.0) ** years_from_mid_2024
    afa_runoff = (1 - gen["series"]["afa_runoff_pct"] / 100.0) ** years_from_mid_2024
    zins_runoff = (1 - gen["series"]["zins_runoff_pct"] / 100.0) ** years_from_mid_2024

    bv_noise = np.zeros(n)
    sd = variant.archetype.bv_noise_pct / 100.0
    if variant.kind == "producer" and sd > 0:
        bv_noise = rng.normal(0.0, sd, n)
        for year in timeline.years:
            idx = timeline.year_indices(year)
            bv_noise[idx] -= bv_noise[idx].mean()

    return Base(
        level=level,
        infl=infl,
        afa_runoff=afa_runoff,
        zins_runoff=zins_runoff,
        season=variant.season[moy],
        shift=variant.production_shift[moy],
        bv_noise=bv_noise,
    )


@dataclass
class Drivers:
    vol: np.ndarray        # hacim çarpanı (E06, E07)
    price: np.ndarray      # satış fiyatı çarpanı (E05)
    mat_add: np.ndarray    # Materialquote'ye eklenen puan, oran olarak (E04)
    headcount: np.ndarray  # çalışan sayısı (E01, E02)
    wage: np.ndarray       # ücret çarpanı (E03)
    raum: np.ndarray       # Raumkosten çarpanı (E09)
    afa: np.ndarray        # Abschreibungen çarpanı (E08)
    zins: np.ndarray       # Zinsaufwand çarpanı (E08)
    werbe_add: np.ndarray          # EUR (E11)
    reparatur_add: np.ndarray      # EUR (E12)
    neutral_ertrag_add: np.ndarray  # EUR (E10)

    @classmethod
    def initial(cls, variant: Variant, n: int) -> "Drivers":
        ones, zeros = np.ones(n), np.zeros(n)
        return cls(
            vol=ones.copy(), price=ones.copy(), mat_add=zeros.copy(),
            headcount=np.full(n, float(variant.employees)), wage=ones.copy(),
            raum=ones.copy(), afa=ones.copy(), zins=ones.copy(),
            werbe_add=zeros.copy(), reparatur_add=zeros.copy(), neutral_ertrag_add=zeros.copy(),
        )

    def copy(self) -> "Drivers":
        return Drivers(**{f.name: getattr(self, f.name).copy() for f in fields(self)})


def monthly_base(variant: Variant) -> float:
    """2024 ortalama aylık ciro (= ortalama Gesamtleistung)."""
    return variant.revenue_2024 / 12.0


def compute_lines(variant: Variant, base: Base, drv: Drivers) -> np.ndarray:
    """Sürücülerden 21 temel satırı hesaplar (satır × ay, EUR)."""
    q = variant.quotas
    r0 = monthly_base(variant)
    n = len(base.level)
    out = np.zeros((len(BASE_LINES), n))

    volume = base.level * drv.vol
    umsatz = r0 * volume * base.season * drv.price
    if variant.kind == "producer":
        bv = r0 * volume * (variant.herstell_factor * base.shift + base.bv_noise)
    else:
        bv = np.zeros(n)

    def put(line: str, values) -> None:
        out[LINE_INDEX[line]] = values

    put("umsatzerloese", umsatz)
    put("bestandsveraenderungen_fe_ue", bv)
    # Materialeinsatz hacme bağlıdır; satış fiyatı artışı (E05) onu değiştirmez.
    put("material_wareneinkauf",
        (q["material_wareneinkauf"] + drv.mat_add) * (umsatz / drv.price + bv))
    for line in _FIXED_WITH_INFLATION:
        put(line, q[line] * r0 * base.infl)
    put("personalkosten",
        q["personalkosten"] * r0 * drv.headcount / variant.employees * drv.wage)
    put("raumkosten", q["raumkosten"] * r0 * base.infl * drv.raum)
    put("werbe_reisekosten", q["werbe_reisekosten"] * r0 * base.infl + drv.werbe_add)
    put("kosten_warenabgabe", q["kosten_warenabgabe"] * umsatz)
    put("abschreibungen", q["abschreibungen"] * r0 * base.afa_runoff * drv.afa)
    put("reparatur_instandhaltung",
        q["reparatur_instandhaltung"] * r0 * base.infl + drv.reparatur_add)
    put("zinsaufwand", q["zinsaufwand"] * r0 * base.zins_runoff * drv.zins)
    put("sonstiger_neutraler_ertrag", drv.neutral_ertrag_add)
    # Aktivierte Eigenleistungen, Sonstiger neutraler Aufwand, Zinserträge ve
    # Steuern vom Einkommen und Ertrag tabanda 0'dır (docs/02, Bölüm 6).
    return out


def apply_noise(lines: np.ndarray, gen: dict, rng: np.random.Generator) -> np.ndarray:
    """Her satır-aya ±%2–4 civarında çarpımsal gürültü (D7)."""
    sd = gen["series"]["noise_sd_pct"] / 100.0
    clip = gen["series"]["noise_clip_pct"] / 100.0
    eps = np.clip(rng.normal(0.0, sd, lines.shape), -clip, clip)
    return lines * (1.0 + eps)
