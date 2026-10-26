---
license: apache-2.0
base_model: google/gemma-4-E4B-it
library_name: peft
pipeline_tag: text-generation
language:
- de
tags:
- lora
- gguf
- llama.cpp
- gemma4
- finance
- accounting
- controlling
- rag
- synthetic-data
---

# BWA-Kommentar: Gemma 4 E4B LoRA (RAG + fine-tuning)

A LoRA adapter for **Gemma 4 E4B** that writes a German **management commentary draft** for a monthly
*BWA* (Betriebswirtschaftliche Auswertung, the DATEV short-term P&L report used by German SMEs).

It is the language-model part (layer 3) of a four-layer system built as an **education and portfolio
project**:

```
BWA (monthly values) ─► [1] Python computes all numbers  ──► facts.json
                        [2] RAG retrieves company notes   ──► context notes with source IDs
                        [3] this model writes the draft   ──► German commentary
                        [4] validation checks numbers and sources ──► flagged draft ──► human approval
```

The model is trained **not to compute numbers itself**, to cite a context note for every stated cause
(`[Quelle: Kontextnotiz 2025-07]`) or mark it as `(Hypothese)`, and to phrase possible accounting
distortions (missing accruals, missing inventory change, seasonality …) as warnings, not as facts.

> **All data is synthetic.** The model was trained and tested only on generated companies and months.
> It is not a product, not tax or legal advice, and every draft needs a human check.

## Output format

Four fixed sections, about 250–350 words plus a table:

```
**Kernaussagen <Monat Jahr>**                      (at most 3 points)
**Abweichungen im Detail**                         (Position | Ist | Vergleich | Abweichung | Erklärung | Quelle oder Hypothese)
**Hinweise auf mögliche Verzerrungen**
**Offene Fragen an Buchhaltung / Steuerberater**
```

Example input and output for one test month (Muster GmbH, July 2025, a sector never seen in training):
`example_A1-v00_2025-07_messages.json` → `example_A1-v00_2025-07_output.md`.

## Input format

The model expects exactly the prompt it was trained on (prompt version 1.1):

- **System message:** role, 8 rules (numbers only from FACTS, number format, direction, sources,
  hypotheses, warnings, open questions, structure) and the output template. Identical for every month.
- **User message**, three blocks:
  - `FACTS:` the month as JSON, computed by code: actual, previous month, same month of the previous year,
    cumulative, deviations, ratios, significance and distortion flags;
  - `WISSEN:` general explanations of BWA lines and a guide to typical distortions (background only, not a source);
  - `KONTEXTNOTIZEN:` the company profile plus the top-8 retrieved company notes, each with a source ID,
    month and duration (`dauerhaft` / `temporär`).

See `example_A1-v00_2025-07_messages.json` for a complete message pair. Outside this format (other
languages, free questions, other reports) the behaviour is untested.

## How to run (tested path: llama.cpp `llama-server`)

This is the path used for the evaluation below.

1. **Base model file:** Ollama's `gemma4:e4b-it-q4_K_M`. After `ollama pull gemma4:e4b-it-q4_K_M`, it is
   in Ollama's `models/blobs/` folder as `sha256-370c2879f17648d337b0ab4e208fdce348e24d1060064e93d7645daafd56d39c`
   (5.5 GB). Other GGUF conversions of `google/gemma-4-E4B-it` should work but were not tested.
2. **Adapter:** `adapter_rag.gguf` from this repository (*Files and versions*).
3. **Server:** a `llama-server` build with Gemma 4 support. We used the one bundled with Ollama 0.40.10
   (Linux: `/usr/local/lib/ollama/llama-server`).

```bash
llama-server --model <base>.gguf --lora adapter_rag.gguf -c 12288 -ngl 999 --port 8080
python request_llama_server.py example_A1-v00_2025-07_prompt.txt > kommentar.md
```

- `example_..._prompt.txt` is the Gemma 4 chat template already applied: system and user turn, generation
  prompt `<|turn>model\n`, thinking off. It has no leading `<bos>`, because the server adds it.
- To build prompts for other months, apply the chat template of `google/gemma-4-E4B-it` with
  `enable_thinking=False` and remove the leading `<bos>`.
- **Sampling used in the evaluation:** temperature 0.2, top_k 64, top_p 0.95, min_p 0, seed 42, max 1500 tokens.
- On a 4 GB laptop GPU, offload fewer layers (`-ngl`) and reduce `-c`; prompts are 4–6k tokens.

`adapter_model.safetensors` and `adapter_config.json` are the same adapter in PEFT format (trained with Unsloth on
`unsloth/gemma-4-E4B-it-unsloth-bnb-4bit`). They are provided for reference and further training; only the GGUF
path above was evaluated.

## Training

| | |
|---|---|
| Method | QLoRA (4-bit base), Unsloth 2026.10.8 + TRL 1.15.0, loss on the answer only |
| LoRA | r 16, alpha 16, dropout 0, attention and MLP of the language layers (34.9 M parameters); vision and audio untouched |
| Schedule | 1 epoch, LR 2e-4 linear, warmup 5 %, batch 1 × gradient accumulation 8 (113 steps), AdamW 8-bit, max length 7168 tokens |
| Data | 898 synthetic company-months: wholesale (Sanitär/Heizung) and garden-furniture manufacturer, 20 variants each |
| Targets | rule-based content plan from the generator's ground truth (what to say, which note explains what) + German wording by a teacher model (Mistral Large 3) + automatic checks; rejected texts were regenerated or dropped |
| Validation loss | 0.834 → 0.130 (32 held-out examples) |
| Compute | one Kaggle T4, 7.8 h |

The training targets never contain the true cause of an event unless a visible note states it; otherwise they ask an open
question or give a marked hypothesis.

## Evaluation

720 test months: 240 from a **new sector** never seen in training (metal-working supplier) and 480 from **new companies**
of the trained sectors. Same base model file, prompt and sampling for all rows; only the adapter differs.

| Metric | Base model | Base + RAG | Fine-tuned, no RAG ¹ | **This model (RAG + FT)** |
|---|---:|---:|---:|---:|
| Output format correct | 39 % | 30 % | 100 % | **97 %** |
| Texts without validation error | 18 % | 4 % | 93 % | **82 %** |
| Numbers matching the facts | 95 % | 94 % | 100 % | **99 %** |
| Unmarked causes per text (neither source nor hypothesis) | 0.16 | 1.01 | 0 | **0.06** |
| Cited notes that really explain a deviation (precision) | – | 54 % | – | **75 %** |
| Expected notes cited (recall) | – | 34 % | – | **59 %** |
| Citations on the right table row | – | 37 % | – | **64 %** |
| Distortion warnings: recall / precision (ground truth) | 66 % / 86 % | 64 % / 85 % | 84 % / 88 % | **82 % / 87 %** |

¹ A separate adapter trained without context notes (not published here).

- **New sector vs. new companies:** same level. Format 99 % vs. 96 %, precision 76 % vs. 75 %, recall 58 % vs. 60 %.
- **Retrieval:** the top-8 notes contain 91 % of the notes on the month's own events; with all notes in the window instead of
  the top 8, recall drops slightly (55 %).

## Limitations

- **Inventory-change decision (V2):** when a gross-margin jump is explained by a price note, the model still warns about a
  possible missing inventory booking (1 of 17 such test months right). Only 5 % of the training months had this case.
- **Wrong row:** 26 % of texts attach a real note to a table row it does not explain.
- **Numbers:** 12 % of texts contain at least one wrong or self-computed number (e.g. a difference to the normal level). The
  validation layer flags these; the model must be used together with such a check and a human review.
- **Length:** 19 % of texts are shorter than 200 words.
- **Data:** synthetic companies and notes only. Real BWA exports, real note styles and other chart-of-accounts setups are untested.

## License

Apache 2.0, like the base model Gemma 4. Training targets were written with Mistral Large 3 via the Mistral API.

## Files

| File | Content |
|---|---|
| `adapter_rag.gguf` | LoRA adapter for llama.cpp (tested) |
| `adapter_model.safetensors`, `adapter_config.json` | same adapter, PEFT format |
| `example_A1-v00_2025-07_messages.json` | input of one test month (system + user message) |
| `example_A1-v00_2025-07_prompt.txt` | the same input with the chat template applied |
| `example_A1-v00_2025-07_output.md` | the model's output for it (from the evaluation run) |
| `request_llama_server.py` | sends a prompt file to `llama-server` with the evaluation settings |
