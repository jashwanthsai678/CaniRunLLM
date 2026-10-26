## granite-switch-4.1-3b-preview

- `parameters`: REVIEW — not present in config.json, check the model card for ibm-granite/granite-switch-4.1-3b-preview and fill in manually.
- `context_length`, `num_layers`, `num_kv_heads`, `head_dim`: from `config.json` at https://huggingface.co/ibm-granite/granite-switch-4.1-3b-preview (num_hidden_layers=42, num_attention_heads=40, num_key_value_heads=8, max_position_embeddings=131072).
- `file_size_bytes`: REVIEW — no matching quant files found in barha/granite-switch-4.1-3b-preview-GGUF.
- CAVEAT: MoE architecture detected (found one of ('num_experts', 'num_local_experts', 'num_experts_per_tok', 'moe_intermediate_size')) — this project's formulas assume dense models. Verify before adding.
- CAVEAT: No GGUF file matched for quant(s): Q4_K_M, Q8_0 in barha/granite-switch-4.1-3b-preview-GGUF.
- Fetched 2026-10-26 by scripts/draft_all_candidates.py.
