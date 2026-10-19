## UserRepGen-4B

- `parameters`: REVIEW — not present in config.json, check the model card for microsoft/UserRepGen-4B and fill in manually.
- `context_length`, `num_layers`, `num_kv_heads`, `head_dim`: from `config.json` at https://huggingface.co/microsoft/UserRepGen-4B (num_hidden_layers=None, num_attention_heads=None, num_key_value_heads=None, max_position_embeddings=None).
- `file_size_bytes`: GGUF artifact sizes from https://huggingface.co/prithivMLmods/microsoft-UserRepGen-4B-GGUF (Q4_K_M = 2.71 GB, Q8_0 = 4.48 GB).
- Fetched 2026-10-19 by scripts/draft_all_candidates.py.
