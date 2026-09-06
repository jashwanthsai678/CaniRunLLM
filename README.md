# CanIRunLLM

Find out which open-source LLMs your machine can actually run — and which
one you should pick — with an automatic hardware scan and a local dashboard.

CanIRunLLM inspects your real CPU, RAM, and GPU/VRAM, checks that against a
registry of real open-weight models (Qwen, Llama, Mistral, Gemma, Phi,
DeepSeek, and more), and gives you a plain-language verdict — not just a raw
"fits/doesn't fit" table. It runs entirely on your machine: no account, no
cloud calls, no telemetry.

```
$ canirunllm scan

CanIRunLLM

Checking your computer...
  CPU detected
  RAM detected
  GPU detected
  VRAM detected

Analyzing local AI models...
  58 models analyzed

You can run 14 model(s) comfortably.
7 more can run with CPU/RAM offload (slower).

Dashboard:
  http://127.0.0.1:8765

Opening browser...
```

The browser dashboard shows a friendly "what can I run / what should I run"
report, with the full technical breakdown (VRAM, RAM, KV cache, quantization,
runtime, confidence) available behind a "Technical details" toggle for anyone
who wants it.

## Install

Requires **Python 3.10 or newer**.

```bash
pip install canirunllm
```

or from source:

```bash
git clone https://github.com/jashwanthsai678/CaniRunLLM.git
cd CaniRunLLM
pip install -e .
```

> **Windows users with multiple Python versions installed:** your plain
> `pip`/`python` commands might point at an older Python (commonly 3.9,
> which this project doesn't support). If `pip install canirunllm` says
> it can't find a matching version, check what's installed with:
> ```cmd
> py -0
> ```
> then install using a specific newer version explicitly:
> ```cmd
> py -3.11 -m pip install canirunllm
> py -3.11 -m canirunllm.cli scan
> ```

## Quick start

```bash
canirunllm scan               # scan hardware, evaluate models, open the dashboard
canirunllm scan --no-browser  # same, but skip the dashboard (good for CI/headless)
canirunllm scan --technical   # also print the full technical breakdown in the terminal

canirunllm search qwen        # search the model registry
canirunllm check Qwen3-8B     # check one model or a whole family
canirunllm recommend          # ranked list of models for your hardware

canirunllm web                # launch the dashboard on its own
canirunllm web --port 9000    # on a custom port
```

## What it actually checks

For every model + quantization pair, CanIRunLLM estimates:

- **Weight memory** from parameter count and quantization (Q4_K_M, Q8_0, etc.)
- **KV cache size**, which grows with context length — a model isn't just
  "fits" or "doesn't," it fits *at a given context length*
- **Runtime overhead and a safety margin**, not just the raw weight size
- **Memory strategy**: does it fit on a single GPU, does it need to be split
  across multiple GPUs, or does it need CPU/RAM offloading — each of these
  is a real, different scenario, not a single generic "offload" verdict
- **Runtime compatibility**: is the declared runtime (llama.cpp, etc.)
  actually known to support that memory strategy

The result is always a verdict *plus* a confidence level and a plain-English
reason — never a bare "cannot run" with no explanation.

## Architecture

```
CLI / Web Dashboard  (presentation only)
        │
Application Layer   (ScannerService, RecommendationEngine)
        │
   ┌────┴─────┬──────────────┬─────────────┐
   ▼          ▼              ▼             ▼
Hardware   Model Registry  Compatibility  Performance
Scanner    + Resolver      Engine         Prediction
```

The CLI and the local web dashboard are two presentation layers over the
same Python core — nothing about compatibility is calculated twice, and the
frontend never re-derives a verdict on its own.

## Current limitations (being upfront about them)

- GPU detection currently only recognizes NVIDIA GPUs (via `GPUtil`/
  `nvidia-smi`). On AMD/Intel/Apple Silicon machines it safely falls back to
  CPU-only mode rather than crashing, but it won't report real GPU numbers yet.
- The model registry is a curated set of well-known open-weight models, not
  an exhaustive mirror of every model on Hugging Face — see
  `src/canirunllm/registry/SOURCES.md` for exactly where every number in it
  came from.
- Performance numbers are a coarse, clearly-labeled *estimate* based on
  parameter count and memory strategy — there is no real benchmarking yet,
  and the tool never presents an estimate as a measurement.

## Testing

```bash
pip install -e .
pytest -v
```

## License

MIT — see [LICENSE](LICENSE).
