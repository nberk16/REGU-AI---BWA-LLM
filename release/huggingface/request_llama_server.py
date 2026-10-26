"""Send one BWA prompt to a running llama-server with the LoRA adapter (standard library only).

Start the server first (see README.md, "How to run"), then:

    python request_llama_server.py example_A1-v00_2025-07_prompt.txt > kommentar.md

The prompt file is the Gemma 4 chat template already applied (system + user turn, generation prompt
`<|turn>model\\n`, thinking off) and WITHOUT the leading `<bos>`: llama-server adds BOS itself.
Sampling settings are the ones used in the evaluation.
"""

import argparse
import json
import sys
import urllib.request

SETTINGS = {"temperature": 0.2, "top_k": 64, "top_p": 0.95, "min_p": 0.0, "repeat_penalty": 1.0,
            "seed": 42, "n_predict": 1500}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("prompt_file")
    parser.add_argument("--server", default="http://127.0.0.1:8080")
    parser.add_argument("--lora-scale", type=float, default=1.0, help="0 = base model without the adapter")
    args = parser.parse_args()

    prompt = open(args.prompt_file, encoding="utf-8").read()
    if prompt.startswith("<bos>"):
        prompt = prompt[len("<bos>"):]
    body = {"prompt": prompt, **SETTINGS, "lora": [{"id": 0, "scale": args.lora_scale}]}
    req = urllib.request.Request(f"{args.server}/completion", data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=3600) as resp:
        out = json.loads(resp.read())
    sys.stdout.write(out["content"].strip() + "\n")
    sys.stderr.write(f"prompt tokens {out.get('tokens_evaluated')}, output tokens {out.get('tokens_predicted')}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
