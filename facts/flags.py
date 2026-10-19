"""Çarpıklık bayrakları (docs/05_facts_semasi.md, Bölüm 4).

Bayraklar yalnızca gözlem ve sayısal kanıt içerir (`hinweis`). Rohertrag sıçraması nötr bir adaydır
(`kandidat`): notla açıklanıp açıklanmadığına model karar verir; doğru karar yalnızca ground truth'tadır.
Kural parametreleri [ÖNERİ] facts/config.toml'dadır.
"""

import statistics

import numpy as np

from .formatting import de_factor, de_int, de_pct, de_pp, de_signed
from .schema import BASE_LINES, FIXED_COST_LINES, MONTHS_DE


def _flag(code: str, rule: str, position: str, evidence: str, status: str = "hinweis") -> dict:
    return {"code": code, "status": status, "rule": rule, "position": position, "evidence": evidence}


def _month(period: str) -> str:
    return MONTHS_DE[int(period[5:7]) - 1]


def _months_list(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " und " + names[-1]


def rohertragsquote(values: dict) -> np.ndarray:
    gl = values["gesamtleistung"]
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(gl != 0, values["rohertrag"] / gl * 100.0, np.nan)


def compute_flags(ctx) -> list[dict]:
    fs, i, v = ctx.fs, ctx.i, ctx.fs.values
    f = ctx.cfg["flags"]
    thr, rel, pp = ctx.abs_thr, ctx.rel, ctx.pp
    flags = []

    # V1 (wiederkehrende Spitze) ve V5 (einmalige Spitze): ciroya bağlı olmayan gider satırları
    for key in FIXED_COST_LINES:
        a, vj, normal = float(v[key][i]), float(v[key][i - 12]), ctx.normal(key)
        if normal <= 0 or a - normal < thr:
            continue
        name = BASE_LINES[key]
        previous_spike = vj >= f["v1_factor"] * normal
        if a >= f["v1_factor"] * normal and previous_spike:
            flags.append(_flag("V1", "wiederkehrende_spitze", name,
                               f"{name} {de_int(a)} € = {de_factor(a / normal)}-faches des Normalniveaus "
                               f"({de_int(normal)} €); Vorjahresmonat ebenfalls erhöht ({de_int(vj)} €)"))
        elif a >= f["v5_factor"] * normal and not previous_spike:
            flags.append(_flag("V5", "einmalige_spitze", name,
                               f"{name} {de_int(a)} € = {de_factor(a / normal)}-faches des Normalniveaus "
                               f"({de_int(normal)} €); im Vorjahresmonat keine vergleichbare Spitze ({de_int(vj)} €)"))

    # V2 (üretici): stok değişimi 0 iken malzeme anlamlı değişmiş.
    # Üretici olup olmadığı veriden çıkarılır: geçmişte stok değişimi hiç kaydedilmemişse kural uygulanmaz.
    bv = v["bestandsveraenderungen_fe_ue"]
    producer = bool(np.any(np.abs(bv[:i]) >= 1.0))
    material = v["material_wareneinkauf"]
    if producer and abs(bv[i]) < 1.0:
        for j, label in ((i - 1, "Vormonat"), (i - 12, "Vorjahresmonat")):
            delta = float(material[i] - material[j])
            pct = ctx.pct(float(material[i]), float(material[j]), "material_wareneinkauf", thr)
            if ctx.significant(delta, pct, thr):
                flags.append(_flag("V2", "bestand_fehlt", "Bestandsveränderungen FE/UE",
                                   f"Bestandsveränderungen 0 €; Material-/Wareneinkauf {de_signed(delta)} € "
                                   f"({de_pct(pct)}) ggü. {label}"))
                break

    # V2 adayı (bütün arketipler, nötr): Rohertragsquote hem önceki aya hem önceki yılın aynı ayına göre ≥ pp
    rq = rohertragsquote(v)
    d_vm, d_vj = rq[i] - rq[i - 1], rq[i] - rq[i - 12]
    if abs(d_vm) >= pp and abs(d_vj) >= pp:
        flags.append(_flag("V2", "rohertrag_sprung", "Rohertragsquote",
                           f"Rohertragsquote {de_pct(rq[i], signed=False)} (Vormonat {de_pct(rq[i - 1], signed=False)}, "
                           f"Vorjahresmonat {de_pct(rq[i - 12], signed=False)}); Veränderung {de_pp(d_vm)} "
                           f"bzw. {de_pp(d_vj)}", status="kandidat"))

    # V3: AfA eksik ya da yıllık AfA tek ayda
    afa = v["abschreibungen"]
    avg = float(afa[i - 12:i].sum() / 12)
    if avg > 0:
        low = f["v3_low_share"] * avg
        if afa[i] < low:
            flags.append(_flag("V3", "afa_fehlt", "Abschreibungen",
                               f"Abschreibungen {de_int(afa[i])} € bei durchschnittlich {de_int(avg)} € pro Monat "
                               f"in den letzten 12 Monaten"))
        elif afa[i] >= f["v3_booking_factor"] * avg:
            empty = int(np.sum(afa[i - 11:i] < low))
            if empty >= 6:
                flags.append(_flag("V3", "afa_jahresbuchung", "Abschreibungen",
                                   f"Abschreibungen {de_int(afa[i])} € = {de_factor(afa[i] / avg)}-faches des "
                                   f"Monatsdurchschnitts ({de_int(avg)} €); in {empty} der letzten 11 Monate "
                                   f"keine Abschreibungen gebucht"))

    # V4: zamanlama kayması — önceki ay normalin altında, bu ay üstünde
    gl = v["gesamtleistung"]
    mq = material / gl * 100.0
    mq_normal = float(statistics.median(mq[i - 12:i]))
    if mq[i - 1] <= mq_normal - pp and mq[i] >= mq_normal + pp:
        flags.append(_flag("V4", "zeitverschiebung", "Material-/Wareneinkauf",
                           f"Materialquote Vormonat {de_pct(mq[i - 1], signed=False)}, aktuell "
                           f"{de_pct(mq[i], signed=False)} (Normalniveau {de_pct(mq_normal, signed=False)})"))
    r = f["v4_rel"]
    for key in FIXED_COST_LINES:
        prev, cur, normal = float(v[key][i - 1]), float(v[key][i]), ctx.normal(key)
        if (normal > 0 and normal - prev >= thr and prev <= (1 - r) * normal
                and cur - normal >= thr and cur >= (1 + r) * normal):
            name = BASE_LINES[key]
            flags.append(_flag("V4", "zeitverschiebung", name,
                               f"{name}: Vormonat {de_int(prev)} € unter, aktueller Monat {de_int(cur)} € über "
                               f"dem Normalniveau ({de_int(normal)} €)"))
    if producer and abs(bv[i - 1]) < 1.0 and abs(bv[i]) >= thr:
        streak, j = [], i - 1  # stok değişiminin 0 olduğu önceki aylar (en fazla 3)
        while j >= 0 and abs(bv[j]) < 1.0 and len(streak) < 3:
            streak.append(j)
            j -= 1
        names = [_month(fs.periods[j]) for j in sorted(streak)]
        zero_text = f"{names[0]} 0 €" if len(names) == 1 else f"{_months_list(names)} je 0 €"
        flags.append(_flag("V4", "bestand_nachbuchung", "Bestandsveränderungen FE/UE",
                           f"Bestandsveränderungen {zero_text}, {_month(fs.periods[i])} {de_int(bv[i])} €: "
                           f"möglicherweise Buchung für mehrere Monate"))

    # V6: Umsatz önceki aya göre anlamlı değişmiş, önceki yılın aynı ayına göre değişmemiş: önceki yıla göre değişim
    # küçük ve ya ters yönde ya da önceki aya göre değişimin en fazla v6_max_ratio katı
    u = v["umsatzerloese"]
    if u[i - 1] > 0 and u[i - 12] > 0:
        pct_vm = (u[i] - u[i - 1]) / u[i - 1] * 100.0
        pct_vj = (u[i] - u[i - 12]) / u[i - 12] * 100.0
        if (abs(u[i] - u[i - 1]) >= thr and abs(pct_vm) >= rel and abs(pct_vj) < f["v6_max_previous_year_pct"]
                and (pct_vj * pct_vm <= 0 or abs(pct_vj) <= f["v6_max_ratio"] * abs(pct_vm))):
            flags.append(_flag("V6", "saisonal", "Umsatzerlöse",
                               f"Umsatzerlöse {de_pct(pct_vm)} ggü. Vormonat, aber {de_pct(pct_vj)} "
                               f"ggü. Vorjahresmonat"))
    return flags
