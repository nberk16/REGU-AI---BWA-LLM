"""Seri takvimi: dönemler (YYYY-MM), ay ve yıl yardımcıları."""

from dataclasses import dataclass, replace

MONTH_NAMES_DE = (
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
)


@dataclass(frozen=True)
class Timeline:
    start_year: int
    start_month: int  # 1..12
    n: int
    commentable_from: int  # ilk yorumlanabilir ayın indeksi

    @classmethod
    def from_config(cls, series: dict) -> "Timeline":
        year, month = (int(x) for x in series["start"].split("-"))
        draft = cls(year, month, int(series["months"]), 0)
        return replace(draft, commentable_from=draft.index(series["commentable_from"]))

    def _absolute(self, i: int) -> int:
        return self.start_year * 12 + (self.start_month - 1) + i

    def period(self, i: int) -> str:
        a = self._absolute(i)
        return f"{a // 12:04d}-{a % 12 + 1:02d}"

    @property
    def periods(self) -> list[str]:
        return [self.period(i) for i in range(self.n)]

    def index(self, period: str) -> int:
        year, month = (int(x) for x in period.split("-"))
        return year * 12 + month - 1 - self._absolute(0)

    def month_of_year(self, i: int) -> int:
        """0 = Ocak … 11 = Aralık."""
        return self._absolute(i) % 12

    def year(self, i: int) -> int:
        return self._absolute(i) // 12

    @property
    def years(self) -> list[int]:
        return sorted({self.year(i) for i in range(self.n)})

    def year_indices(self, year: int) -> list[int]:
        return [i for i in range(self.n) if self.year(i) == year]

    def month_name(self, i: int) -> str:
        return MONTH_NAMES_DE[self.month_of_year(i)]
