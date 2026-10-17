"""Bilgi tabanı parçaları: K-A, K-B (knowledge.toml) ve K-C (bağlam notları)."""

import json
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).parent


@dataclass(frozen=True)
class Doc:
    doc_id: str          # depodaki benzersiz kimlik
    source_id: str       # modelin atıf yapacağı kaynak kimliği (CLAUDE.md 6.2, Katman 2)
    kind: str            # "K-A" | "K-B" | "K-C"
    text: str
    meta: dict = field(default_factory=dict, compare=False, hash=False)


def period_index(period: str) -> int:
    y, m = map(int, period.split("-"))
    return y * 12 + m - 1


def load_knowledge(path: Path | None = None) -> list[Doc]:
    with open(path or HERE / "knowledge.toml", "rb") as f:
        data = tomllib.load(f)
    docs = [Doc(f"KA|{e['key']}", f"BWA-Erläuterung {e['title']}", "K-A", e["text"], {"key": e["key"]})
            for e in data["ka"]]
    for e in data["kb"]:
        source = "Leitfaden Grundsätze" if e["rule"] == "grundsaetze" else f"Leitfaden {e['code']} ({e['title']})"
        docs.append(Doc(f"KB|{e['rule']}", source, "K-B", e["text"], {"key": e["rule"]}))
    return docs


def load_notes(run_dir: Path) -> list[dict]:
    with open(Path(run_dir) / "model_input" / "context_notes.jsonl", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def notes_to_docs(notes: list[dict]) -> list[Doc]:
    docs = []
    for n in notes:
        meta = {"firm_id": n["firm_id"], "period": n["period"] or "", "duration": n["duration"],
                "period_index": period_index(n["period"]) if n["period"] else -1,
                "profile": n["period"] is None}
        docs.append(Doc(f"{n['firm_id']}|{n['source_id']}", n["source_id"], "K-C", n["text"], meta))
    return docs
