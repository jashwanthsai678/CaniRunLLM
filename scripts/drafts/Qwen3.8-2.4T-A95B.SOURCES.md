## Qwen3.8-2.4T-A95B

- `parameters`: REVIEW — not present in config.json, check the model card for Qwen/Qwen3.8-2.4T-A95B and fill in manually.
- `context_length`, `num_layers`, `num_kv_heads`, `head_dim`: from `config.json` at https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B (num_hidden_layers=92, num_attention_heads=64, num_key_value_heads=4, max_position_embeddings=262144).
- `file_size_bytes`: REVIEW — no matching quant files found in unsloth/Qwen3.8-2.4T-A95B-GGUF.
- CAVEAT: MoE architecture detected (found one of ('num_experts', 'num_local_experts', 'num_experts_per_tok', 'moe_intermediate_size')) — this project's formulas assume dense models. Verify before adding.
- CAVEAT: No GGUF file matched for quant(s): Q4_K_M, Q8_0 in unsloth/Qwen3.8-2.4T-A95B-GGUF.
- Fetched 2026-11-09 by scripts/draft_all_candidates.py.
