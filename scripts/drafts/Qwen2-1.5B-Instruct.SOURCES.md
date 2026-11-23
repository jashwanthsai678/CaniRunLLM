## Qwen2-1.5B-Instruct

- `parameters`: REVIEW — not present in config.json, check the model card for Qwen/Qwen2-1.5B-Instruct and fill in manually.
- `context_length`, `num_layers`, `num_kv_heads`, `head_dim`: from `config.json` at https://huggingface.co/Qwen/Qwen2-1.5B-Instruct (num_hidden_layers=28, num_attention_heads=12, num_key_value_heads=2, max_position_embeddings=32768).
- `file_size_bytes`: GGUF artifact sizes from https://huggingface.co/legraphista/Qwen2-1.5B-Instruct-IMat-GGUF (Q8_0 = 1.65 GB).
- CAVEAT: sliding_window=32768 present — context/KV-cache math does not model sliding-window attention and will overestimate memory use (same caveat as Gemma-2).
- CAVEAT: No GGUF file matched for quant(s): Q4_K_M in legraphista/Qwen2-1.5B-Instruct-IMat-GGUF.
- Fetched 2026-11-23 by scripts/draft_all_candidates.py.
