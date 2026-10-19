# Registry candidate scan summary

Nothing under `registry/` was modified. Review each draft below, fill in any `REVIEW` markers, resolve any caveats, then move the entries into `registry/models.json` and the stub into `registry/SOURCES.md` by hand.

## Drafted (8)

- **UserRepGen-4B** (`microsoft/UserRepGen-4B`)
- **dit-base** (`microsoft/dit-base`)
- **dit-large** (`microsoft/dit-large`)
- **granite-switch-4.1-30b** (`ibm-granite/granite-switch-4.1-30b`)
  - CAVEAT: MoE architecture detected (found one of ('num_experts', 'num_local_experts', 'num_experts_per_tok', 'moe_intermediate_size')) — this project's formulas assume dense models. Verify before adding.
- **granite-switch-4.1-8b** (`ibm-granite/granite-switch-4.1-8b`)
  - CAVEAT: MoE architecture detected (found one of ('num_experts', 'num_local_experts', 'num_experts_per_tok', 'moe_intermediate_size')) — this project's formulas assume dense models. Verify before adding.
- **granite-switch-4.1-30b-preview** (`ibm-granite/granite-switch-4.1-30b-preview`)
  - CAVEAT: MoE architecture detected (found one of ('num_experts', 'num_local_experts', 'num_experts_per_tok', 'moe_intermediate_size')) — this project's formulas assume dense models. Verify before adding.
- **granite-switch-4.1-3b-preview** (`ibm-granite/granite-switch-4.1-3b-preview`)
  - CAVEAT: MoE architecture detected (found one of ('num_experts', 'num_local_experts', 'num_experts_per_tok', 'moe_intermediate_size')) — this project's formulas assume dense models. Verify before adding.
  - CAVEAT: No GGUF file matched for quant(s): Q4_K_M, Q8_0 in barha/granite-switch-4.1-3b-preview-GGUF.
- **granite-switch-4.1-8b-preview** (`ibm-granite/granite-switch-4.1-8b-preview`)
  - CAVEAT: MoE architecture detected (found one of ('num_experts', 'num_local_experts', 'num_experts_per_tok', 'moe_intermediate_size')) — this project's formulas assume dense models. Verify before adding.

## Skipped (6)

- **scFM-dataselection** (`microsoft/scFM-dataselection`): Failed to fetch config.json for microsoft/scFM-dataselection: HTTP 404
- **granitelib-guardian-r1.0** (`ibm-granite/granitelib-guardian-r1.0`): Failed to fetch config.json for ibm-granite/granitelib-guardian-r1.0: HTTP 404
- **granitelib-core-r1.0** (`ibm-granite/granitelib-core-r1.0`): Failed to fetch config.json for ibm-granite/granitelib-core-r1.0: HTTP 404
- **granitelib-rag-r1.0** (`ibm-granite/granitelib-rag-r1.0`): Failed to fetch config.json for ibm-granite/granitelib-rag-r1.0: HTTP 404
- **SAME-L** (`stabilityai/SAME-L`): Failed to fetch config.json for stabilityai/SAME-L: HTTP 404
- **SAME-S** (`stabilityai/SAME-S`): Failed to fetch config.json for stabilityai/SAME-S: HTTP 404
