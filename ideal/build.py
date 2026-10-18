"""Öğretmen istek dosyaları: plan + öğretmen istemi + kontrol girdileri (docs/11_ideal_yorumlar.md, Bölüm 5).

    python -m ideal build --run data/synthetic/train_seed7 [--retrieval …/rag/retrieval.jsonl]

Yazar: ideal/requests/{pilot,train,val}.jsonl.gz (repoda; kullanıcının dizüstündeki betik bunları okur).
- train: v100–v119 (960 ay); val: v120–v122 (144 ay) [KARAR, tur 7; docs/04, Bölüm 9].
- pilot: doğrulama varyantlarından çeşitli ~24 ay; altın küme adayları (B1). val dosyası pilot aylarını da içerir.
"""

import csv
import gzip
import hashlib
import json
from pathlib import Path

from facts.build import build_facts, commentable_periods
from facts.schema import load_config
from facts.series import load_run
from prompting import PROMPT_VERSION

from .plan import PLAN_VERSION, Truth, build_plan
from .teacher import TEACHER_VERSION, teacher_messages

ROOT = Path(__file__).resolve().parents[1]
REQUESTS = ROOT / "ideal" / "requests"
TRAIN_VARIANTS = range(100, 120)
VAL_VARIANTS = range(120, 123)
PILOT_SIZE = 24

# Pilot çeşitliliği: her ölçütten en fazla 3 ay, farklı firmalardan (sıra önceliktir).
PILOT_CRITERIA = [
    ("V2 adayı, notla açıklanır", lambda p, g: (p["meta"]["v2"] or {}).get("entscheidung") == "quelle"),
    ("V2 adayı, uyarılır", lambda p, g: (p["meta"]["v2"] or {}).get("entscheidung") == "warnung"),
    ("V1", lambda p, g: "wiederkehrende_spitze" in p["meta"]["flags"]),
    ("V3", lambda p, g: {"afa_fehlt", "afa_jahresbuchung"} & set(p["meta"]["flags"])),
    ("V4", lambda p, g: {"zeitverschiebung", "bestand_nachbuchung"} & set(p["meta"]["flags"])),
    ("V5, notla açıklanır", lambda p, g: any(h["rule"] == "einmalige_spitze" and h["art"] == "erklaert"
                                            for h in p["hinweise"])),
    ("V6", lambda p, g: "saisonal" in p["meta"]["flags"]),
    ("çeldirici not", lambda p, g: bool(g["distractor_notes"])),
    ("nedeni açık kalem", lambda p, g: any(r["erklaerung"]["art"] == "offen" for r in p["tabelle"])),
    ("sakin ay", lambda p, g: not p["tabelle"]),
]


def load_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_truth(run: Path) -> Truth:
    ev = run / "evaluation"
    with open(ev / "effects.csv", encoding="utf-8") as f:
        effects = list(csv.DictReader(f))
    return Truth(load_jsonl(ev / "events.jsonl"), load_jsonl(ev / "ground_truth_months.jsonl"), effects)


def seed_for(request_id: str) -> int:
    return int(hashlib.sha256(request_id.encode()).hexdigest()[:8], 16)


def variant(firm_id: str) -> int:
    return int(firm_id.split("-v")[1])


def build_requests(run: Path, retrieval: Path) -> dict[str, list[dict]]:
    truth = load_truth(run)
    contexts = {(r["firm_id"], r["period"]): r for r in load_jsonl(retrieval)}
    cfg = load_config()
    out: dict[str, list[dict]] = {"train": [], "val": []}
    for firm_id, fs in sorted(load_run(run).items()):
        v = variant(firm_id)
        name = "train" if v in TRAIN_VARIANTS else "val" if v in VAL_VARIANTS else None
        if name is None:
            continue
        for period in commentable_periods(fs):
            facts = build_facts(fs, period, cfg)
            ctx = contexts[(firm_id, period)]
            plan = build_plan(facts, ctx, truth)
            out[name].append({
                "id": plan["id"], "firm_id": firm_id, "period": period, "set": name,
                "versions": {"plan": PLAN_VERSION, "teacher": TEACHER_VERSION, "prompt": PROMPT_VERSION,
                             "retrieval": {"mode": ctx["mode"], "k": ctx["k"], "embedding": ctx["embedding"]}},
                "random_seed": seed_for(plan["id"]), "messages": teacher_messages(plan), "plan": plan,
                "facts": facts, "notes": ctx["notes"]})
    out["pilot"] = select_pilot(out["val"], truth)
    return out


def select_pilot(requests: list[dict], truth: Truth, size: int = PILOT_SIZE) -> list[dict]:
    chosen: list[dict] = []
    for _, cond in PILOT_CRITERIA:
        firms_used = {r["firm_id"] for r in chosen}
        pool = [r for r in requests if r not in chosen
                and cond(r["plan"], truth.months[(r["firm_id"], r["period"])])]
        pool.sort(key=lambda r: (r["firm_id"] in firms_used, seed_for("pilot" + r["id"])))
        chosen += pool[:3]
        if len(chosen) >= size:
            break
    rest = sorted((r for r in requests if r not in chosen), key=lambda r: seed_for("pilot" + r["id"]))
    chosen += rest[:max(0, size - len(chosen))]
    return [dict(r, set="pilot") for r in chosen[:size]]


def write_requests(requests: dict[str, list[dict]], out_dir: Path = REQUESTS) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, rows in requests.items():
        path = out_dir / f"{name}.jsonl.gz"
        # mtime=0: aynı içerik → aynı dosya (git'te gereksiz değişiklik olmaz)
        with open(path, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
            for r in rows:
                gz.write((json.dumps(r, ensure_ascii=False) + "\n").encode("utf-8"))
        paths[name] = path
    return paths
