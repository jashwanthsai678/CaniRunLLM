# Registry candidate scan summary

Nothing under `registry/` was modified. Review each draft below, fill in any `REVIEW` markers, resolve any caveats, then move the entries into `registry/models.json` and the stub into `registry/SOURCES.md` by hand.

## Drafted (5)

- **Sentiment-Analysis-7B** (`microsoft/Sentiment-Analysis-7B`)
- **granite-switch-4.1-30b** (`ibm-granite/granite-switch-4.1-30b`)
  - CAVEAT: MoE architecture detected (found one of ('num_experts', 'num_local_experts', 'num_experts_per_tok', 'moe_intermediate_size')) — this project's formulas assume dense models. Verify before adding.
- **granite-switch-4.1-8b** (`ibm-granite/granite-switch-4.1-8b`)
  - CAVEAT: MoE architecture detected (found one of ('num_experts', 'num_local_experts', 'num_experts_per_tok', 'moe_intermediate_size')) — this project's formulas assume dense models. Verify before adding.
- **granite-4.2-8b** (`ibm-granite/granite-4.2-8b`)
- **granite-4.2-3b** (`ibm-granite/granite-4.2-3b`)

## Skipped (5)

- **rho-yam-box** (`microsoft/rho-yam-box`): Failed to fetch config.json for microsoft/rho-yam-box: HTTP 404
- **rho-ur-ai-trainer** (`microsoft/rho-ur-ai-trainer`): Failed to fetch config.json for microsoft/rho-ur-ai-trainer: HTTP 404
- **CogACT-v2-RoboDojo** (`microsoft/CogACT-v2-RoboDojo`): Failed to fetch config.json for microsoft/CogACT-v2-RoboDojo: HTTP 404
- **granitelib-core-r1.0** (`ibm-granite/granitelib-core-r1.0`): Failed to fetch config.json for ibm-granite/granitelib-core-r1.0: HTTP 404
- **sdxl-base-amdnpu-medusa** (`stabilityai/sdxl-base-amdnpu-medusa`): Failed to fetch config.json for stabilityai/sdxl-base-amdnpu-medusa: HTTP 404
