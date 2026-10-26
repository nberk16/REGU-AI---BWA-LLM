"""BWA satırları, ara toplamlar ve oranlar (docs/02_bwa_satir_yapisi.md)."""

import tomllib
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.toml"

BASE_LINES = {
    "umsatzerloese": "Umsatzerlöse",
    "bestandsveraenderungen_fe_ue": "Bestandsveränderungen FE/UE",
    "aktivierte_eigenleistungen": "Aktivierte Eigenleistungen",
    "material_wareneinkauf": "Material-/Wareneinkauf",
    "sonstige_betriebliche_erloese": "Sonstige betriebliche Erlöse",
    "personalkosten": "Personalkosten",
    "raumkosten": "Raumkosten",
    "betriebliche_steuern": "Betriebliche Steuern",
    "versicherungen_beitraege": "Versicherungen/Beiträge",
    "besondere_kosten": "Besondere Kosten",
    "fahrzeugkosten": "Fahrzeugkosten (ohne Steuer)",
    "werbe_reisekosten": "Werbe-/Reisekosten",
    "kosten_warenabgabe": "Kosten der Warenabgabe",
    "abschreibungen": "Abschreibungen",
    "reparatur_instandhaltung": "Reparatur/Instandhaltung",
    "sonstige_kosten": "Sonstige Kosten",
    "zinsaufwand": "Zinsaufwand",
    "sonstiger_neutraler_aufwand": "Sonstiger neutraler Aufwand",
    "zinsertraege": "Zinserträge",
    "sonstiger_neutraler_ertrag": "Sonstiger neutraler Ertrag",
    "steuern_einkommen_ertrag": "Steuern vom Einkommen und Ertrag",
}

COST_LINES = (
    "personalkosten", "raumkosten", "betriebliche_steuern", "versicherungen_beitraege",
    "besondere_kosten", "fahrzeugkosten", "werbe_reisekosten", "kosten_warenabgabe",
    "abschreibungen", "reparatur_instandhaltung", "sonstige_kosten",
)

# Ciroya bağlı olmayan gider satırları: V1, V4 ve V5 kuralları yalnızca bunlara uygulanır.
# (Abschreibungen V3 ile, Material Materialquote ile ayrıca ele alınır.)
FIXED_COST_LINES = (
    "personalkosten", "raumkosten", "betriebliche_steuern", "versicherungen_beitraege",
    "besondere_kosten", "fahrzeugkosten", "werbe_reisekosten", "reparatur_instandhaltung",
    "sonstige_kosten",
)

SUMMARY_LINES = {
    "gesamtleistung": "Gesamtleistung",
    "rohertrag": "Rohertrag",
    "gesamtkosten": "Gesamtkosten",
    "betriebsergebnis": "Betriebsergebnis",
    "ergebnis_vor_steuern": "Ergebnis vor Steuern",
    "vorlaeufiges_ergebnis": "Vorläufiges Ergebnis",
}

# Sonuç satırlarında yüzde değişim verilmez (karar turu 5).
RESULT_LINES = ("betriebsergebnis", "ergebnis_vor_steuern", "vorlaeufiges_ergebnis")

RATIOS = {
    "Rohertragsquote": "rohertrag",
    "Materialquote": "material_wareneinkauf",
    "Personalkostenquote": "personalkosten",
    "Betriebsergebnis-Marge": "betriebsergebnis",
}

MONTHS_DE = ("Januar", "Februar", "März", "April", "Mai", "Juni",
             "Juli", "August", "September", "Oktober", "November", "Dezember")


def add_subtotals(v: dict) -> dict:
    """Ara toplamlar ve sonuç satırları (docs/02, Bölüm 3). Değerler sayı veya numpy dizisi olabilir."""
    v = dict(v)
    v["gesamtleistung"] = v["umsatzerloese"] + v["bestandsveraenderungen_fe_ue"] + v["aktivierte_eigenleistungen"]
    v["rohertrag"] = v["gesamtleistung"] - v["material_wareneinkauf"]
    v["betrieblicher_rohertrag"] = v["rohertrag"] + v["sonstige_betriebliche_erloese"]
    v["gesamtkosten"] = sum(v[k] for k in COST_LINES)
    v["betriebsergebnis"] = v["betrieblicher_rohertrag"] - v["gesamtkosten"]
    v["neutraler_aufwand"] = v["zinsaufwand"] + v["sonstiger_neutraler_aufwand"]
    v["neutraler_ertrag"] = v["zinsertraege"] + v["sonstiger_neutraler_ertrag"]
    v["ergebnis_vor_steuern"] = v["betriebsergebnis"] - v["neutraler_aufwand"] + v["neutraler_ertrag"]
    v["vorlaeufiges_ergebnis"] = v["ergebnis_vor_steuern"] - v["steuern_einkommen_ertrag"]
    return v


def load_config(path: Path | None = None) -> dict:
    with open(path or CONFIG_PATH, "rb") as f:
        return tomllib.load(f)
