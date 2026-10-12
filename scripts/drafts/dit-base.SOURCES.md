## dit-base

- `parameters`: REVIEW — not present in config.json, check the model card for microsoft/dit-base and fill in manually.
- `context_length`, `num_layers`, `num_kv_heads`, `head_dim`: from `config.json` at https://huggingface.co/microsoft/dit-base (num_hidden_layers=12, num_attention_heads=12, num_key_value_heads=None, max_position_embeddings=None).
- `file_size_bytes`: REVIEW — no matching quant files found in REVIEW.
- Fetched 2026-10-12 by scripts/draft_all_candidates.py.
