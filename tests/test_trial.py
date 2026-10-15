"""Deneme turu kiti testleri (docs/08): girdilerin yeniden üretilebilirliği, sızıntı yokluğu, Ollama betiği."""

import importlib.util
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from generator.pipeline import generate_run
from generator.writer import write_run

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "trial" / "inputs" / "cases.jsonl"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"trial_{name}", ROOT / "trial" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prepare, run_ollama, score = _load("prepare"), _load("run_ollama"), _load("score")


def _cases() -> list[dict]:
    return [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_cases_are_reproducible(tmp_path):
    # Varyant başına ayrı rastgele akış: yalnızca v120–v122'yi üretmek yeterli (docs/04, 9.1).
    write_run(generate_run(["A2", "A3"], 3, 7, profile="train_price_boost", first_variant=120), tmp_path)
    chosen = prepare.select(prepare.candidates(tmp_path), len(prepare.CRITERIA))
    committed = _cases()
    assert [f"{c['firm_id']}_{c['period']}" for _, c in chosen] == [c["id"] for c in committed]
    from prompting import build_messages
    for (_, c), case in zip(chosen, committed):
        assert build_messages(c["facts"], c["notes"]) == case["messages"]


def test_cases_use_validation_variants_and_no_ground_truth():
    for case in _cases():
        assert int(case["firm_id"].split("-v")[1]) in prepare.VALIDATION_VARIANTS
        text = json.dumps(case["messages"], ensure_ascii=False)
        for leak in ("event_id", "expected_flags", "v2_candidate_decision", "distractor", "rohertrag_causes"):
            assert leak not in text
        assert case["messages"][0]["role"] == "system" and case["facts"]["period_label"] in case["messages"][0]["content"]


INSTALLED = [m["tag"] for m in run_ollama.MODELS]


class _FakeOllama(BaseHTTPRequestHandler):
    reply = "<think>Überlegung</think>**Kernaussagen Test**\n\n1. Text."

    def _send(self, body: dict) -> None:
        data = json.dumps(body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # noqa: N802
        tags = INSTALLED
        if self.path == "/api/version":
            self._send({"version": "0.0-test"})
        elif self.path == "/api/tags":
            self._send({"models": [{"name": t} for t in tags]})
        elif self.path == "/api/ps":
            self._send({"models": [{"name": t, "size": 6_000_000_000, "size_vram": 3_000_000_000} for t in tags]})

    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        assert body["options"]["num_ctx"] == run_ollama.OPTIONS["num_ctx"]
        assert ("think" in body) == (body["model"] != "ministral-3:8b-instruct-2512-q4_K_M")
        self._send({"message": {"role": "assistant", "content": self.reply}, "done_reason": "stop",
                    "prompt_eval_count": 4000, "prompt_eval_duration": 40_000_000_000,
                    "eval_count": 600, "eval_duration": 200_000_000_000, "load_duration": 5_000_000_000})

    def log_message(self, *args):
        pass


@pytest.fixture()
def fake_ollama():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeOllama)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def test_runner_and_score(fake_ollama, tmp_path, capsys):
    out = tmp_path / "outputs"
    assert run_ollama.main(["--host", fake_ollama, "--out", str(out), "--limit", "2"]) == 0
    for m in run_ollama.MODELS:
        records = [json.loads(line) for line in (out / f"{m['name']}.jsonl").read_text(encoding="utf-8").splitlines()]
        assert len(records) == 2
        r = records[0]
        assert r["output"].startswith("**Kernaussagen") and "<think>" not in r["output"]
        assert r["stats"]["output_tok_per_s"] == 3.0 and r["stats"]["prompt_tok_per_s"] == 100.0
        assert r["stats"]["thinking_chars"] > 0 and r["memory"]["size_vram"] == 3_000_000_000
    # Devam: biten örnekler atlanır.
    assert run_ollama.main(["--host", fake_ollama, "--out", str(out), "--limit", "2"]) == 0
    assert len((out / "gemma4-e4b.jsonl").read_text(encoding="utf-8").splitlines()) == 2

    report = tmp_path / "results.md"
    score.main(["--outputs", str(out), "--report", str(report)])
    text = report.read_text(encoding="utf-8")
    assert all(m["name"] in text for m in run_ollama.MODELS)
    assert "| 0/2 |" in text and "50%" in text                  # format bozuk; GPU payı %50
    capsys.readouterr()


def test_runner_reports_missing_models(fake_ollama, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(run_ollama, "MODELS", run_ollama.MODELS + [{"name": "x", "tag": "x:1b", "think": None}])
    assert run_ollama.main(["--host", fake_ollama, "--out", str(tmp_path)]) == 2
    assert "ollama pull x:1b" in capsys.readouterr().out
