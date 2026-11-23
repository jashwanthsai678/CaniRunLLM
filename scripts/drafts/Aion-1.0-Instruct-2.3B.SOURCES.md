## Aion-1.0-Instruct-2.3B

- `parameters`: REVIEW — not present in config.json, check the model card for microsoft/Aion-1.0-Instruct-2.3B and fill in manually.
- `context_length`, `num_layers`, `num_kv_heads`, `head_dim`: from `config.json` at https://huggingface.co/microsoft/Aion-1.0-Instruct-2.3B (num_hidden_layers=28, num_attention_heads=24, num_key_value_heads=8, max_position_embeddings=32768).
- `file_size_bytes`: GGUF artifact sizes from https://huggingface.co/AtomicChat/Aion-1.0-Instruct-2.3B-Uncensored-GGUF (Q4_K_M = 1.58 GB).
- CAVEAT: sliding_window=2048 present — context/KV-cache math does not model sliding-window attention and will overestimate memory use (same caveat as Gemma-2).
- CAVEAT: No GGUF file matched for quant(s): Q8_0 in AtomicChat/Aion-1.0-Instruct-2.3B-Uncensored-GGUF.
- Fetched 2026-11-23 by scripts/draft_all_candidates.py.
