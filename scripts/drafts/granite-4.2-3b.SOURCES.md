## granite-4.2-3b

- `parameters`: REVIEW — not present in config.json, check the model card for ibm-granite/granite-4.2-3b and fill in manually.
- `context_length`, `num_layers`, `num_kv_heads`, `head_dim`: from `config.json` at https://huggingface.co/ibm-granite/granite-4.2-3b (num_hidden_layers=40, num_attention_heads=40, num_key_value_heads=8, max_position_embeddings=131072).
- `file_size_bytes`: GGUF artifact sizes from https://huggingface.co/ibm-granite/granite-4.2-3b-GGUF (Q4_K_M = 2.24 GB, Q8_0 = 3.89 GB).
- Fetched 2026-10-26 by scripts/draft_all_candidates.py.
