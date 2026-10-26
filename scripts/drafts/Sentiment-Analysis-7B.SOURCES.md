## Sentiment-Analysis-7B

- `parameters`: REVIEW — not present in config.json, check the model card for microsoft/Sentiment-Analysis-7B and fill in manually.
- `context_length`, `num_layers`, `num_kv_heads`, `head_dim`: from `config.json` at https://huggingface.co/microsoft/Sentiment-Analysis-7B (num_hidden_layers=32, num_attention_heads=32, num_key_value_heads=8, max_position_embeddings=32768).
- `file_size_bytes`: GGUF artifact sizes from https://huggingface.co/mradermacher/Sentiment-Analysis-7B-GGUF (Q4_K_M = 4.37 GB, Q8_0 = 7.70 GB).
- Fetched 2026-10-26 by scripts/draft_all_candidates.py.
