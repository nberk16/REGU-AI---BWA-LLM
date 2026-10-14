"""BWA temel satırları (docs/02_bwa_satir_yapisi.md, Bölüm 2).

Ham veri yalnızca bu 21 temel satırı içerir; ara toplamlar Katman 1'de hesaplanır.
"""

BASE_LINES = (
    "umsatzerloese",
    "bestandsveraenderungen_fe_ue",
    "aktivierte_eigenleistungen",
    "material_wareneinkauf",
    "sonstige_betriebliche_erloese",
    "personalkosten",
    "raumkosten",
    "betriebliche_steuern",
    "versicherungen_beitraege",
    "besondere_kosten",
    "fahrzeugkosten",
    "werbe_reisekosten",
    "kosten_warenabgabe",
    "abschreibungen",
    "reparatur_instandhaltung",
    "sonstige_kosten",
    "zinsaufwand",
    "sonstiger_neutraler_aufwand",
    "zinsertraege",
    "sonstiger_neutraler_ertrag",
    "steuern_einkommen_ertrag",
)

LINE_INDEX = {line: i for i, line in enumerate(BASE_LINES)}

# Sayısal tolerans: bunun altındaki farklar sıfır sayılır (EUR).
EPS = 0.005
