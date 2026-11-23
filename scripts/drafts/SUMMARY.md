# Registry candidate scan summary

Nothing under `registry/` was modified. Review each draft below, fill in any `REVIEW` markers, resolve any caveats, then move the entries into `registry/models.json` and the stub into `registry/SOURCES.md` by hand.

## Drafted (6)

- **Qwen2-1.5B-Instruct** (`Qwen/Qwen2-1.5B-Instruct`)
  - CAVEAT: sliding_window=32768 present — context/KV-cache math does not model sliding-window attention and will overestimate memory use (same caveat as Gemma-2).
  - CAVEAT: No GGUF file matched for quant(s): Q4_K_M in legraphista/Qwen2-1.5B-Instruct-IMat-GGUF.
- **Aion-1.0-Instruct-2.3B** (`microsoft/Aion-1.0-Instruct-2.3B`)
  - CAVEAT: sliding_window=2048 present — context/KV-cache math does not model sliding-window attention and will overestimate memory use (same caveat as Gemma-2).
  - CAVEAT: No GGUF file matched for quant(s): Q8_0 in AtomicChat/Aion-1.0-Instruct-2.3B-Uncensored-GGUF.
- **Aion-1.0-Instruct-2.3B-ONNX-WebGPU** (`microsoft/Aion-1.0-Instruct-2.3B-ONNX-WebGPU`)
  - CAVEAT: sliding_window=2048 present — context/KV-cache math does not model sliding-window attention and will overestimate memory use (same caveat as Gemma-2).
- **FrogNano-4B-2609** (`microsoft/FrogNano-4B-2609`)
- **granite-4.1-8b-llmon-preview** (`ibm-granite/granite-4.1-8b-llmon-preview`)
- **granite-4.1-3b-llmon-preview** (`ibm-granite/granite-4.1-3b-llmon-preview`)

## Skipped (1)

- **Graphormer** (`microsoft/Graphormer`): Failed to fetch config.json for microsoft/Graphormer: HTTP 404
