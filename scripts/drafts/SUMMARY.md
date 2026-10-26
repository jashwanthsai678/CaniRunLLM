# Registry candidate scan summary

Nothing under `registry/` was modified. Review each draft below, fill in any `REVIEW` markers, resolve any caveats, then move the entries into `registry/models.json` and the stub into `registry/SOURCES.md` by hand.

## Drafted (9)

- **Sentiment-Analysis-7B** (`microsoft/Sentiment-Analysis-7B`)
- **UserRepGen-4B** (`microsoft/UserRepGen-4B`)
- **granite-4.2-8b** (`ibm-granite/granite-4.2-8b`)
- **granite-4.2-3b** (`ibm-granite/granite-4.2-3b`)
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

- **CogACT-v2-RoboDojo** (`microsoft/CogACT-v2-RoboDojo`): Failed to fetch config.json for microsoft/CogACT-v2-RoboDojo: HTTP 404
- **scFM-dataselection** (`microsoft/scFM-dataselection`): Failed to fetch config.json for microsoft/scFM-dataselection: HTTP 404
- **bioemu2** (`microsoft/bioemu2`): Failed to fetch config.json for microsoft/bioemu2: HTTP 404
- **granitelib-guardian-r1.0** (`ibm-granite/granitelib-guardian-r1.0`): Failed to fetch config.json for ibm-granite/granitelib-guardian-r1.0: HTTP 404
- **granitelib-core-r1.0** (`ibm-granite/granitelib-core-r1.0`): Failed to fetch config.json for ibm-granite/granitelib-core-r1.0: HTTP 404
- **granitelib-rag-r1.0** (`ibm-granite/granitelib-rag-r1.0`): Failed to fetch config.json for ibm-granite/granitelib-rag-r1.0: HTTP 404
