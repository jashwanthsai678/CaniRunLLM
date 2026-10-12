# Registry candidate scan summary

Nothing under `registry/` was modified. Review each draft below, fill in any `REVIEW` markers, resolve any caveats, then move the entries into `registry/models.json` and the stub into `registry/SOURCES.md` by hand.

## Drafted (10)

- **LFM2.5-230M** (`unsloth/LFM2.5-230M`)
- **Qwen3-Coder-Next** (`unsloth/Qwen3-Coder-Next`)
  - CAVEAT: MoE architecture detected (found one of ('num_experts', 'num_local_experts', 'num_experts_per_tok', 'moe_intermediate_size')) — this project's formulas assume dense models. Verify before adding.
  - CAVEAT: No GGUF file matched for quant(s): Q8_0 in unsloth/Qwen3-Coder-Next-GGUF.
- **gpt-oss-20b-unsloth-bnb-4bit** (`unsloth/gpt-oss-20b-unsloth-bnb-4bit`)
  - CAVEAT: MoE architecture detected (found one of ('num_experts', 'num_local_experts', 'num_experts_per_tok', 'moe_intermediate_size')) — this project's formulas assume dense models. Verify before adding.
  - CAVEAT: sliding_window=128 present — context/KV-cache math does not model sliding-window attention and will overestimate memory use (same caveat as Gemma-2).
- **gpt-oss-20b-bnb-4bit** (`unsloth/gpt-oss-20b-bnb-4bit`)
  - CAVEAT: MoE architecture detected (found one of ('num_experts', 'num_local_experts', 'num_experts_per_tok', 'moe_intermediate_size')) — this project's formulas assume dense models. Verify before adding.
  - CAVEAT: sliding_window=128 present — context/KV-cache math does not model sliding-window attention and will overestimate memory use (same caveat as Gemma-2).
- **gpt-oss-20b-BF16** (`unsloth/gpt-oss-20b-BF16`)
  - CAVEAT: MoE architecture detected (found one of ('num_experts', 'num_local_experts', 'num_experts_per_tok', 'moe_intermediate_size')) — this project's formulas assume dense models. Verify before adding.
  - CAVEAT: sliding_window=128 present — context/KV-cache math does not model sliding-window attention and will overestimate memory use (same caveat as Gemma-2).
- **gpt-oss-120b-unsloth-bnb-4bit** (`unsloth/gpt-oss-120b-unsloth-bnb-4bit`)
  - CAVEAT: MoE architecture detected (found one of ('num_experts', 'num_local_experts', 'num_experts_per_tok', 'moe_intermediate_size')) — this project's formulas assume dense models. Verify before adding.
  - CAVEAT: sliding_window=128 present — context/KV-cache math does not model sliding-window attention and will overestimate memory use (same caveat as Gemma-2).
- **gpt-oss-120b-BF16** (`unsloth/gpt-oss-120b-BF16`)
  - CAVEAT: MoE architecture detected (found one of ('num_experts', 'num_local_experts', 'num_experts_per_tok', 'moe_intermediate_size')) — this project's formulas assume dense models. Verify before adding.
  - CAVEAT: sliding_window=128 present — context/KV-cache math does not model sliding-window attention and will overestimate memory use (same caveat as Gemma-2).
  - CAVEAT: No GGUF file matched for quant(s): Q4_K_M, Q8_0 in mradermacher/Huihui-gpt-oss-120b-BF16-abliterated-i1-GGUF.
- **dit-base** (`microsoft/dit-base`)
- **dit-large** (`microsoft/dit-large`)
- **FrogNano-4B-2609** (`microsoft/FrogNano-4B-2609`)

## Skipped (4)

- **granitelib-core-r1.0** (`ibm-granite/granitelib-core-r1.0`): Failed to fetch config.json for ibm-granite/granitelib-core-r1.0: HTTP 404
- **ensemble-forecasting-with-ibm-granite-time-series** (`ibm-granite/ensemble-forecasting-with-ibm-granite-time-series`): Failed to fetch config.json for ibm-granite/ensemble-forecasting-with-ibm-granite-time-series: HTTP 404
- **SAME-L** (`stabilityai/SAME-L`): Failed to fetch config.json for stabilityai/SAME-L: HTTP 404
- **SAME-S** (`stabilityai/SAME-S`): Failed to fetch config.json for stabilityai/SAME-S: HTTP 404
