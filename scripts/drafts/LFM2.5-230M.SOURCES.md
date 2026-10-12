## LFM2.5-230M

- `parameters`: REVIEW — not present in config.json, check the model card for unsloth/LFM2.5-230M and fill in manually.
- `context_length`, `num_layers`, `num_kv_heads`, `head_dim`: from `config.json` at https://huggingface.co/unsloth/LFM2.5-230M (num_hidden_layers=14, num_attention_heads=16, num_key_value_heads=8, max_position_embeddings=128000).
- `file_size_bytes`: GGUF artifact sizes from https://huggingface.co/LiquidAI/LFM2.5-230M-GGUF (Q4_K_M = 0.15 GB, Q8_0 = 0.25 GB).
- Fetched 2026-10-12 by scripts/draft_all_candidates.py.
