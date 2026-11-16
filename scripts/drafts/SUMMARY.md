# Registry candidate scan summary

Nothing under `registry/` was modified. Review each draft below, fill in any `REVIEW` markers, resolve any caveats, then move the entries into `registry/models.json` and the stub into `registry/SOURCES.md` by hand.

## Drafted (4)

- **Qwen3.8-2.4T-A95B** (`Qwen/Qwen3.8-2.4T-A95B`)
  - CAVEAT: MoE architecture detected (found one of ('num_experts', 'num_local_experts', 'num_experts_per_tok', 'moe_intermediate_size')) — this project's formulas assume dense models. Verify before adding.
  - CAVEAT: No GGUF file matched for quant(s): Q4_K_M, Q8_0 in unsloth/Qwen3.8-2.4T-A95B-GGUF.
- **FrogNano-4B-2609** (`microsoft/FrogNano-4B-2609`)
- **granite-4.1-8b-llmon-preview** (`ibm-granite/granite-4.1-8b-llmon-preview`)
- **granite-4.1-3b-llmon-preview** (`ibm-granite/granite-4.1-3b-llmon-preview`)

## Skipped (4)

- **Graphormer** (`microsoft/Graphormer`): Failed to fetch config.json for microsoft/Graphormer: HTTP 404
- **rho-yam-box** (`microsoft/rho-yam-box`): Failed to fetch config.json for microsoft/rho-yam-box: HTTP 404
- **rho-fr3-duo** (`microsoft/rho-fr3-duo`): Failed to fetch config.json for microsoft/rho-fr3-duo: HTTP 404
- **rho-ur-ai-trainer** (`microsoft/rho-ur-ai-trainer`): Failed to fetch config.json for microsoft/rho-ur-ai-trainer: HTTP 404
