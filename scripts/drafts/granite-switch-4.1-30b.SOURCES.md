## granite-switch-4.1-30b

- `parameters`: REVIEW — not present in config.json, check the model card for ibm-granite/granite-switch-4.1-30b and fill in manually.
- `context_length`, `num_layers`, `num_kv_heads`, `head_dim`: from `config.json` at https://huggingface.co/ibm-granite/granite-switch-4.1-30b (num_hidden_layers=66, num_attention_heads=32, num_key_value_heads=8, max_position_embeddings=131072).
- `file_size_bytes`: GGUF artifact sizes from https://huggingface.co/ibm-granite/granite-switch-4.1-30b-GGUF (Q4_K_M = 21.04 GB, Q8_0 = 34.05 GB).
- CAVEAT: MoE architecture detected (found one of ('num_experts', 'num_local_experts', 'num_experts_per_tok', 'moe_intermediate_size')) — this project's formulas assume dense models. Verify before adding.
- Fetched 2026-10-26 by scripts/draft_all_candidates.py.
