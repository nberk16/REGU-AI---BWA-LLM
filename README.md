# BWA-LLM: management commentary drafts for German BWA reports

> **Status: work in progress.** The data generator, the calculation layer, the knowledge base, the validation layer, the training data and both fine-tuned models are done. The evaluation of the fine-tuned models (the ablation) and the portfolio write-up are still open. Progress: [`docs/yol_haritasi.md`](docs/yol_haritasi.md).

An education and portfolio project. A small LLM, fine-tuned with LoRA and given retrieved company context (RAG), turns a monthly **BWA** (*Betriebswirtschaftliche Auswertung*, the short-term P&L report used by German Mittelstand companies) into a German management commentary draft that cites its sources.

The aim is to show a clear, measurable link between problem and solution, not top model performance. All data is synthetic.

## How it works

```
BWA (CSV) + previous periods
  → [1] calculation layer (Python)                → facts.json
  → [2] RAG: company notes + BWA background        → context with source IDs
  → [3] fine-tuned small LLM (Gemma 4 E4B + LoRA)  → German draft
  → [4] validation: numbers and sources            → flagged draft → human review
```

- **Code calculates, the model comments.** The model never computes a figure; layer 4 checks every number in the text against `facts.json`.
- **Knowledge through RAG, behaviour through fine-tuning.** Company-specific facts come from retrieved notes; structure, tone and the habit of marking guesses come from training.
- **Facts, sourced causes and hypotheses stay separate.** Every stated cause carries either `[Quelle: …]` or `(Hypothese)`.
- **Ablation:** base model, RAG only, fine-tuning only and RAG + fine-tuning are compared on the same test set.

## Repository layout

| Path | Content |
|---|---|
| `generator/` | Synthetic BWA generator: three company archetypes, event catalogue, ground truth |
| `facts/` | Layer 1: comparisons, ratios and distortion flags → `facts.json` |
| `rag/` | Layer 2: knowledge base and retrieval (BGE-M3 + Chroma) |
| `prompting/` | Model input (prompt 1.1) and its variants |
| `validation/` | Layer 4: number and source checks |
| `ideal/` | Target commentaries (rule-based content plan + teacher model) and the gold set |
| `training/` | Training data export |
| `gpu/` | Kaggle notebooks (baselines, fine-tuning, evaluation) and run outputs |
| `scoring/` | Evaluation metrics |
| `trial/` | German-language trial of three candidate base models |
| `data/synthetic/` | Reference datasets |
| `docs/` | Design documents and decision log |
| `tests/` | pytest suite |

## Quick start

Python 3.11 or newer.

```bash
pip install -e ".[dev]"
python -m pytest
```

The RAG layer needs extra packages: `pip install -e ".[rag]"`.

## Documentation

The design documents are in Turkish; the generated commentaries are in German. Good starting points:

- [`CLAUDE.md`](CLAUDE.md): project brief (problem, architecture, decisions)
- [`docs/00_karar_kaydi.md`](docs/00_karar_kaydi.md): decision log
- [`docs/examples/`](docs/examples/): an example `facts.json` and commentary

## License

- **Code:** MIT, see [`LICENSE`](LICENSE).
- **Documentation, synthetic data, generated texts and run outputs:** CC BY 4.0, see [`LICENSE-CC-BY-4.0.txt`](LICENSE-CC-BY-4.0.txt). This covers the Markdown files and `data/`, `ideal/gold/`, `ideal/outputs/`, `ideal/requests/`, `gpu/data/`, `gpu/outputs/`, `trial/inputs/` and `trial/outputs/`.
- Model weights are not part of this repository. The base model (Gemma 4 E4B) and the teacher model (Mistral Large 3) are subject to their own terms.

This project is not tax, legal or investment advice. It is not affiliated with DATEV eG; "DATEV" is used only to describe the report format.
