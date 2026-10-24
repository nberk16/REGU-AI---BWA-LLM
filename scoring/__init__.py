"""Model metinlerinin puanlanması (paket 9; docs/13_degerlendirme.md)."""

from .score import SCORING_VERSION, aggregate, make_month, score_text

__all__ = ["SCORING_VERSION", "aggregate", "make_month", "score_text"]
