## granite-4.2-30b

- `parameters`: REVIEW — not present in config.json, check the model card for ibm-granite/granite-4.2-30b and fill in manually.
- `context_length`, `num_layers`, `num_kv_heads`, `head_dim`: from `config.json` at https://huggingface.co/ibm-granite/granite-4.2-30b (num_hidden_layers=64, num_attention_heads=32, num_key_value_heads=8, max_position_embeddings=131072).
- `file_size_bytes`: GGUF artifact sizes from https://huggingface.co/ibm-granite/granite-4.2-30b-GGUF (Q4_K_M = 17.72 GB, Q8_0 = 31.11 GB).
- Fetched 2026-09-17 by scripts/draft_all_candidates.py.
