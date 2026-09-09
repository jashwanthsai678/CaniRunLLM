# CanIRunLLM

[![PyPI](https://img.shields.io/pypi/v/canirunllm)](https://pypi.org/project/canirunllm/)
[![Python](https://img.shields.io/pypi/pyversions/canirunllm)](https://pypi.org/project/canirunllm/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-124%20passing-brightgreen)](tests)

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
  62 models analyzed

You can run 14 model(s) comfortably.
7 more can run with CPU/RAM offload (slower).

Dashboard:
  http://127.0.0.1:8765

Opening browser...
```

The browser dashboard shows a friendly "what can I run / what should I run"
report — including estimated throughput and comparison charts — with the
full technical breakdown (VRAM, RAM, KV cache, quantization, runtime,
confidence) available behind a "Technical details" toggle for anyone who
wants it. Clicking a runnable model shows real, verified commands for
running it locally (llama.cpp, Ollama).

## Table of contents

- [Why this exists](#why-this-exists)
- [Install](#install)
- [Quick start](#quick-start)
- [What it actually checks](#what-it-actually-checks)
- [Architecture](#architecture)
- [Current limitations](#current-limitations-being-upfront-about-them)
- [Contributing](#contributing)
- [Testing](#testing)
- [License](#license)

## Why this exists

Open-weight models are closing the gap on proprietary ones fast, and running
them locally means no API keys, no per-token bills, no vendor lock-in, and
your data never leaving your machine. That future is arriving whether or not
any single vendor cooperates.

But "just run it locally" quietly assumes you already know which model fits
your hardware, which quantization to use, whether it needs multi-GPU or
CPU/RAM offloading, and which runtime actually supports that combination —
and gets it wrong just as quietly, with an OOM crash or a model that
technically loads but is unusably slow.

CanIRunLLM exists to answer the question that actually matters before any of
that: **given the machine you actually have, what should you run?** Not "is
this hardware capable in theory," but "here's what you can run today, here's
what you should pick, and here's why" — so local, open-weight models become
something you can act on with confidence, not something you find out by
trial and (expensive) error.

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

or download the standalone Windows executable (no Python required) from the
[latest release](https://github.com/jashwanthsai678/CaniRunLLM/releases/latest) —
or from [canirunllm.vercel.app](https://canirunllm.vercel.app) if the site is
live for you.

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

- **Weight memory** from parameter count and quantization (Q4_K_M, Q5_K_M,
  Q8_0, etc.)
- **KV cache size**, which grows with context length — a model isn't just
  "fits" or "doesn't," it fits *at a given context length*
- **Runtime overhead and a safety margin**, not just the raw weight size
- **Memory strategy**: does it fit on a single GPU, does it need to be split
  across multiple GPUs, or does it need CPU/RAM offloading — each of these
  is a real, different scenario, not a single generic "offload" verdict
- **Runtime compatibility**: is the declared runtime (llama.cpp, etc.)
  actually known to support that memory strategy
- **Estimated throughput** (tokens/sec), clearly labeled as a modelled
  estimate, not a benchmark

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

The recommendation pipeline is entirely deterministic: hardware detection,
memory math, and verdicts are plain Python, not an LLM call. This is a
deliberate choice, not a missing feature — a tool whose job is helping you
get your *first* local model can't require one to already be running, and
a cloud API would contradict the "no API keys, no accounts" point of the
whole project.

## Current limitations (being upfront about them)

- GPU detection currently only recognizes NVIDIA GPUs (via `GPUtil`/
  `nvidia-smi`). On AMD/Intel/Apple Silicon machines it safely falls back to
  CPU-only mode rather than crashing, but it won't report real GPU numbers yet.
- The model registry is a curated set of well-known open-weight models, not
  an exhaustive mirror of every model on Hugging Face — see
  [`src/canirunllm/registry/SOURCES.md`](src/canirunllm/registry/SOURCES.md)
  for exactly where every number in it came from.
- Performance numbers are a coarse, clearly-labeled *estimate* based on
  parameter count and memory strategy — there is no real benchmarking yet,
  and the tool never presents an estimate as a measurement.

## Contributing

Contributions are welcome, especially:

- **New model registry entries** — add an entry to
  [`src/canirunllm/registry/models.json`](src/canirunllm/registry/models.json)
  and document the exact source for every field (HF `config.json` URL, GGUF
  repo, file sizes) in
  [`SOURCES.md`](src/canirunllm/registry/SOURCES.md). Never fabricate a
  number — if something can't be verified, it doesn't go in.
- **AMD/Intel/Apple Silicon GPU detection** — the hardware scanner
  (`src/canirunllm/hardware/`) currently only supports NVIDIA.
- **Bug reports** — via [GitHub Issues](https://github.com/jashwanthsai678/CaniRunLLM/issues).

Before opening a PR, run the test suite (see below) and make sure it passes.

## Testing

```bash
pip install -e .
pytest -v
```

## License

MIT — see [LICENSE](LICENSE).
