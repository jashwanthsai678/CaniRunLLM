## Qwen3-Coder-Next

- `parameters`: REVIEW — not present in config.json, check the model card for unsloth/Qwen3-Coder-Next and fill in manually.
- `context_length`, `num_layers`, `num_kv_heads`, `head_dim`: from `config.json` at https://huggingface.co/unsloth/Qwen3-Coder-Next (num_hidden_layers=48, num_attention_heads=16, num_key_value_heads=2, max_position_embeddings=262144).
- `file_size_bytes`: GGUF artifact sizes from https://huggingface.co/unsloth/Qwen3-Coder-Next-GGUF (Q4_K_M = 48.53 GB).
- CAVEAT: MoE architecture detected (found one of ('num_experts', 'num_local_experts', 'num_experts_per_tok', 'moe_intermediate_size')) — this project's formulas assume dense models. Verify before adding.
- CAVEAT: No GGUF file matched for quant(s): Q8_0 in unsloth/Qwen3-Coder-Next-GGUF.
- Fetched 2026-10-12 by scripts/draft_all_candidates.py.
