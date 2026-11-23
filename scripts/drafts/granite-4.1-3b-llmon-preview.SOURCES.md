## granite-4.1-3b-llmon-preview

- `parameters`: REVIEW — not present in config.json, check the model card for ibm-granite/granite-4.1-3b-llmon-preview and fill in manually.
- `context_length`, `num_layers`, `num_kv_heads`, `head_dim`: from `config.json` at https://huggingface.co/ibm-granite/granite-4.1-3b-llmon-preview (num_hidden_layers=40, num_attention_heads=40, num_key_value_heads=8, max_position_embeddings=131072).
- `file_size_bytes`: GGUF artifact sizes from https://huggingface.co/liodon-ai/granite-4.1-3b-llmon-preview-GGUF (Q4_K_M = 2.24 GB, Q8_0 = 3.89 GB).
- Fetched 2026-11-23 by scripts/draft_all_candidates.py.
