# Registry candidate scan summary

Nothing under `registry/` was modified. Review each draft below, fill in any `REVIEW` markers, resolve any caveats, then move the entries into `registry/models.json` and the stub into `registry/SOURCES.md` by hand.

## Drafted (3)

- **Qwen3.8-2.4T-A95B** (`Qwen/Qwen3.8-2.4T-A95B`)
  - CAVEAT: MoE architecture detected (found one of ('num_experts', 'num_local_experts', 'num_experts_per_tok', 'moe_intermediate_size')) — this project's formulas assume dense models. Verify before adding.
  - CAVEAT: No GGUF file matched for quant(s): Q4_K_M, Q8_0 in unsloth/Qwen3.8-2.4T-A95B-GGUF.
- **granite-switch-4.1-30b** (`ibm-granite/granite-switch-4.1-30b`)
  - CAVEAT: MoE architecture detected (found one of ('num_experts', 'num_local_experts', 'num_experts_per_tok', 'moe_intermediate_size')) — this project's formulas assume dense models. Verify before adding.
- **granite-switch-4.1-8b** (`ibm-granite/granite-switch-4.1-8b`)
  - CAVEAT: MoE architecture detected (found one of ('num_experts', 'num_local_experts', 'num_experts_per_tok', 'moe_intermediate_size')) — this project's formulas assume dense models. Verify before adding.

## Skipped (5)

- **rho-yam-box** (`microsoft/rho-yam-box`): Failed to fetch config.json for microsoft/rho-yam-box: HTTP 404
- **rho-fr3-duo** (`microsoft/rho-fr3-duo`): Failed to fetch config.json for microsoft/rho-fr3-duo: HTTP 404
- **rho-ur-ai-trainer** (`microsoft/rho-ur-ai-trainer`): Failed to fetch config.json for microsoft/rho-ur-ai-trainer: HTTP 404
- **Graphormer** (`microsoft/Graphormer`): Failed to fetch config.json for microsoft/Graphormer: HTTP 404
- **granitelib-core-r1.0** (`ibm-granite/granitelib-core-r1.0`): Failed to fetch config.json for ibm-granite/granitelib-core-r1.0: HTTP 404
