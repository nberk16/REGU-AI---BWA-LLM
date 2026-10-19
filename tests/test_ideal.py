"""İdeal yorum hattı testleri (docs/11_ideal_yorumlar.md): plan, öğretmen istemi, kontrol, dizüstü betiği."""

import gzip
import importlib.util
import json
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from facts.build import build_facts, commentable_periods
from facts.schema import load_config as load_facts_config
from facts.series import load_run
from generator.pipeline import generate_run
from generator.writer import write_run
from ideal import build as B
from ideal.check import check
from ideal.cli import report
from ideal.plan import PLAN_VERSION, Truth, _causes, build_plan, eur, pct, pp, signed_eur, teur
from ideal.teacher import TEACHER_VERSION, teacher_messages
from prompting import PROMPT_VERSION
from validation.context import load_notes, window_notes

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "data" / "synthetic" / "reference_seed42"
sys.path.insert(0, str(Path(__file__).parent))
from ideal_template import render  # noqa: E402

LEAKS = ("event_id", "expected_flags", "v2_candidate_decision", "distractor", "rohertrag_causes")
EVENT_CODE = re.compile(r"\bE\d{2}\b")


def _load_runner():
    spec = importlib.util.spec_from_file_location("run_teacher", ROOT / "ideal" / "run_teacher.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = _load_runner()


def test_number_format_matches_rounding_rule_a():
    assert (eur(886365), signed_eur(-17002), signed_eur(141640)) == ("886.365 €", "-17.002 €", "+141.640 €")
    assert (teur(886365), teur(41500), teur(41499), teur(-56003)) == ("886 T€", "42 T€", "41 T€", "-56 T€")
    assert (pct(19.0), pct(-60.65), pct(48.9, signed=False), pp(-4.4)) == (
        "+19,0 %", "-60,7 %", "48,9 %", "-4,4 Prozentpunkte")


def test_reference_month_plan():
    truth = B.load_truth(REFERENCE)
    facts = build_facts(load_run(REFERENCE)["A1-v00"], "2025-06", load_facts_config())
    notes = window_notes(load_notes(REFERENCE), "A1-v00", "2025-06")
    plan = build_plan(facts, {"notes": notes}, truth)
    rows = {r["position"]: r["erklaerung"] for r in plan["tabelle"]}
    assert rows["Umsatzerlöse"]["quellen"] == ["Kontextnotiz 2025-06 #2", "Kontextnotiz 2025-06"]
    assert rows["Werbe-/Reisekosten"] == {"art": "quelle", "quellen": ["Kontextnotiz 2024-06 #2"], "bezug": ["vorjahr"]}
    assert rows["Bestandsveränderungen FE/UE"]["art"] == "hypothese"
    assert [(h["rule"], h["art"]) for h in plan["hinweise"]] == [("wiederkehrende_spitze", "warnung"),
                                                                 ("bestand_nachbuchung", "warnung")]
    assert len(plan["fragen"]) == 2 and [k["art"] for k in plan["kernaussagen"]] == ["ergebnis", "position", "hinweis"]
    assert set(plan["notizen"]) <= {n["source_id"] for n in notes}


def test_equal_effects_are_ordered_by_event_id():
    """Eşit etkili iki olayın sırası hash tohumuna bağlı olmamalı (aynı girdi → aynı plan ve aynı input_sha)."""
    events = [{"event_id": e, "type": "E01", "category": "R", "documented": True, "source_id": f"Kontextnotiz {e}"}
              for e in ("ev-b", "ev-a")]
    for order in (["ev-b", "ev-a"], ["ev-a", "ev-b"]):
        rows = [{"firm_id": "F", "period": "2025-06", "line": "personalkosten", "event_id": e, "delta": "100"} for e in order]
        truth = Truth(events, [], rows)
        effects = truth.yoy_effects("F", "2025-06", "personalkosten")
        assert list(effects) == ["ev-a", "ev-b"]
        causes = _causes(truth, "F", "2025-06", "personalkosten", 200.0, dict(reversed(list(effects.items()))))
        assert [c["event_id"] for c in causes] == ["ev-a", "ev-b"]


@pytest.fixture(scope="module")
def small_run(tmp_path_factory):
    """v118–v119 (eğitim) ve v120 (doğrulama); bağlam yerine yalnızca o ayın notları + Firmenprofil (dar görünürlük)."""
    path = tmp_path_factory.mktemp("ideal_run")
    write_run(generate_run(["A2", "A3"], 3, 7, profile="train_price_boost", first_variant=118), path)
    notes = load_notes(path)
    with open(path / "retrieval.jsonl", "w", encoding="utf-8") as f:
        for firm_id, fs in sorted(load_run(path).items()):
            for period in commentable_periods(fs):
                visible = [n for n in window_notes(notes, firm_id, period) if n["period"] in (None, period)]
                f.write(json.dumps({"firm_id": firm_id, "period": period, "mode": "test", "k": 8, "embedding": "test",
                                    "knowledge": [], "notes": visible}, ensure_ascii=False) + "\n")
    return path, B.build_requests(path, path / "retrieval.jsonl")


def test_plans_cite_only_visible_non_distractor_notes(small_run):
    path, requests = small_run
    distractors = {(n["firm_id"], n["source_id"]) for n in B.load_jsonl(path / "evaluation" / "notes_ground_truth.jsonl")
                   if n["distractor"]}
    assert len(requests["train"]) == 2 * 2 * 24 and len(requests["val"]) == 2 * 24 and len(requests["pilot"]) == 24
    for r in requests["train"] + requests["val"]:
        visible = {n["source_id"] for n in r["notes"]}
        cited = set(r["plan"]["notizen"])
        assert cited <= visible and not any((r["firm_id"], s) in distractors for s in cited)
        text = json.dumps(r["messages"], ensure_ascii=False)
        assert not any(leak in text for leak in LEAKS) and not EVENT_CODE.search(text)
    # Dar görünürlükte önceki yılın notları görünmez: o nedenler kaynaklı olamaz (B3)
    assert any(row["erklaerung"]["art"] != "quelle" for r in requests["train"] for row in r["plan"]["tabelle"])


def test_ohne_kontext_plans_have_no_sources(small_run):
    """„Yalnızca fine-tuning“ hedefleri [KARAR, tur 12]: aynı aylar, not yok → kaynak yok, V2 hep uyarı."""
    path, requests = small_run
    ohne = B.build_requests(path, None)
    assert set(ohne) == {"train_ohne", "val_ohne"}
    assert [r["id"] for r in ohne["train_ohne"]] == [r["id"] for r in requests["train"]]
    for r in ohne["train_ohne"] + ohne["val_ohne"]:
        plan = r["plan"]
        assert r["notes"] == [] and plan["notizen"] == {} and r["versions"]["retrieval"]["mode"] == "ohne_kontext"
        assert all(row["erklaerung"]["art"] in ("hypothese", "offen") for row in plan["tabelle"])
        assert all(h["art"] in ("warnung", "saison") for h in plan["hinweise"])
        assert (plan["meta"]["v2"] or {}).get("entscheidung", "warnung") == "warnung"
        assert "Quelle:" not in json.dumps(plan, ensure_ascii=False)
    for r in ohne["train_ohne"][::5] + ohne["val_ohne"]:
        res = check(render(r["plan"]), r["plan"], r["facts"], r["notes"])
        assert [p for p in res["problems"] if not p.startswith("Länge")] == [], r["id"]


def test_template_passes_check(small_run):
    _, requests = small_run
    for r in requests["train"][::5] + requests["val"]:
        res = check(render(r["plan"]), r["plan"], r["facts"], r["notes"])
        assert [p for p in res["problems"] if not p.startswith("Länge")] == [], r["id"]


def test_check_finds_plan_deviations(small_run):
    _, requests = small_run
    r = next(x for x in requests["val"] if any(row["erklaerung"]["art"] == "quelle" for row in x["plan"]["tabelle"])
             and x["plan"]["hinweise"])
    text = render(r["plan"])
    src = next(row["erklaerung"]["quellen"][0] for row in r["plan"]["tabelle"] if row["erklaerung"]["art"] == "quelle")
    missing = check(text.replace(f"[Quelle: {src}]", "(Hypothese)").replace(f"; {src}", ""), r["plan"], r["facts"], r["notes"])
    assert any("Quellen fehlen" in p or "letzte Spalte braucht" in p for p in missing["problems"])
    first_hint = r["plan"]["hinweise"][0]["position"]
    lines = [ln for ln in text.splitlines() if not ln.startswith(f"- {first_hint}:")]
    dropped = check("\n".join(lines), r["plan"], r["facts"], r["notes"])
    assert any("Hinweise fehlt" in p for p in dropped["problems"])
    extra = check(text.replace("**Hinweise", "Ursache laut [Quelle: Kontextnotiz 1999-01].\n\n**Hinweise"),
                  r["plan"], r["facts"], r["notes"])
    assert any("nicht im Plan" in p for p in extra["problems"])


def test_committed_requests_match_code():
    sets = {}
    for name in ("pilot", "train", "val", "train_ohne", "val_ohne"):
        with gzip.open(ROOT / "ideal" / "requests" / f"{name}.jsonl.gz", "rt", encoding="utf-8") as f:
            sets[name] = [json.loads(line) for line in f]
    assert (len(sets["train"]), len(sets["val"]), len(sets["pilot"])) == (960, 144, 24)
    for name in ("train", "val"):
        assert [r["id"] for r in sets[name + "_ohne"]] == [r["id"] for r in sets[name]]
    for r in sets["val_ohne"][::12]:
        assert r["versions"]["retrieval"]["mode"] == "ohne_kontext" and r["versions"]["plan"] == PLAN_VERSION
        assert r["notes"] == [] and r["messages"] == teacher_messages(r["plan"])
    assert {r["id"] for r in sets["pilot"]} <= {r["id"] for r in sets["val"]}
    assert all(B.variant(r["firm_id"]) in B.TRAIN_VARIANTS for r in sets["train"])
    for r in sets["pilot"] + sets["val"][::12]:
        assert r["versions"]["plan"] == PLAN_VERSION and r["versions"]["teacher"] == TEACHER_VERSION
        assert r["versions"]["prompt"] == PROMPT_VERSION and r["versions"]["retrieval"]["k"] == 8
        assert r["messages"] == teacher_messages(r["plan"])
        res = check(render(r["plan"]), r["plan"], r["facts"], r["notes"])
        assert [p for p in res["problems"] if not p.startswith("Länge")] == []


# --- Dizüstü betiği (sahte Mistral sunucusuyla) ------------------------------------------------------

class _FakeMistral(BaseHTTPRequestHandler):
    replies: list[str] = []
    calls: list[dict] = []

    def _send(self, body: dict, code: int = 200) -> None:
        data = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # noqa: N802
        if self.headers.get("Authorization") != "Bearer test-key":
            return self._send({"detail": "Unauthorized"}, 401)
        self._send({"data": [{"id": "mistral-large-2512"}, {"id": "mistral-small-latest"}]})

    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).calls.append(body)
        text = type(self).replies.pop(0)
        self._send({"choices": [{"message": {"role": "assistant", "content": text}}],
                    "usage": {"prompt_tokens": 1000, "completion_tokens": 500}})

    def log_message(self, *args):
        pass


@pytest.fixture()
def fake_api(monkeypatch):
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeMistral)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setattr(runner, "API", f"http://127.0.0.1:{server.server_address[1]}/v1")
    yield _FakeMistral
    server.shutdown()


def test_runner_retries_with_feedback_and_resumes(fake_api, small_run, tmp_path, monkeypatch, capsys):
    _, requests = small_run
    req_dir = tmp_path / "requests"
    B.write_requests({"pilot": requests["pilot"][:2]}, req_dir)
    good = [render(r["plan"]) for r in requests["pilot"][:2]]
    # 1. ay: önce biçimsiz metin, sonra doğru; 2. ay: ilk denemede doğru (uzunluk kontrolü testte gevşetilir)
    fake_api.replies = ["Kein Kommentar.", "```\n" + good[0] + "\n```", good[1]]
    fake_api.calls = []
    monkeypatch.setattr(sys.modules["ideal.check"], "WORDS_MIN", 0)      # kalıp metin kısa
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    args = ["--set", "pilot", "--requests", str(req_dir), "--out", str(tmp_path / "out"), "--workers", "1"]
    (tmp_path / "out").mkdir()
    stale = {"id": requests["pilot"][0]["id"], "status": "ok", "versions": {"plan": "0.9"}}   # eski sürüm: yeniden üretilir
    (tmp_path / "out" / "pilot.jsonl").write_text(json.dumps(stale) + "\n", encoding="utf-8")
    assert runner.main(args) == 0
    lines = (tmp_path / "out" / "pilot.jsonl").read_text(encoding="utf-8").splitlines()[1:]
    recs = [json.loads(line) for line in lines]
    assert [(r["status"], r["attempts"]) for r in recs] == [("ok", 2), ("ok", 1)]
    assert recs[0]["text"] == good[0] and recs[0]["usage"] == {"prompt_tokens": 2000, "completion_tokens": 1000}
    retry = fake_api.calls[1]["messages"]
    assert retry[-2]["role"] == "assistant" and "erfüllt folgende Punkte nicht" in retry[-1]["content"]
    assert fake_api.calls[0]["model"] == "mistral-large-2512" and "random_seed" in fake_api.calls[0]
    assert runner.main(args) == 0 and len(fake_api.calls) == 3          # devam: biten aylar atlanır
    # --retry-failed: reddedilen ay yeni tohumlarla yeniden denenir
    path = tmp_path / "out" / "pilot.jsonl"
    failed = dict(recs[1], status="failed")
    path.write_text(path.read_text(encoding="utf-8") + json.dumps(failed) + "\n", encoding="utf-8")
    fake_api.replies = [good[1]]
    assert runner.main(args + ["--retry-failed"]) == 0 and len(fake_api.calls) == 4
    assert fake_api.calls[3]["random_seed"] == fake_api.calls[2]["random_seed"] + 200   # 2 önceki kayıt
    assert "test-key" not in capsys.readouterr().out
    summary = report("pilot", tmp_path / "out")
    assert "kabul: 2 (100%)" in summary and "1: 1, 2: 1" in summary
    # Girdisi değişen ay (ör. plan düzeltmesi) yeniden üretilir; değişmeyen ay atlanır
    changed = dict(requests["pilot"][0], messages=requests["pilot"][0]["messages"] + [{"role": "user", "content": "x"}])
    B.write_requests({"pilot": [changed, requests["pilot"][1]]}, req_dir)
    fake_api.replies = [good[0]]
    assert runner.main(args) == 0 and len(fake_api.calls) == 5
    last = json.loads(path.read_text(encoding="utf-8").splitlines()[-1])
    assert last["id"] == changed["id"] and last["input_sha"] == runner.input_sha(changed)


def test_runner_needs_key_and_known_model(fake_api, monkeypatch, capsys):
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    assert runner.main(["--check"]) == 2 and "MISTRAL_API_KEY" in capsys.readouterr().out
    monkeypatch.setenv("MISTRAL_API_KEY", "wrong")
    assert runner.main(["--check"]) == 2 and "401" in capsys.readouterr().out
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    assert runner.main(["--check"]) == 0
    fake_api.replies = ["OK"]                      # listede yok ama deneme isteği çalışıyor
    assert runner.main(["--check", "--model", "mistral-large-latest"]) == 0
    out = capsys.readouterr().out
    assert "mistral-large-2512, mistral-small-latest" in out and "Deneme isteği çalıştı" in out
