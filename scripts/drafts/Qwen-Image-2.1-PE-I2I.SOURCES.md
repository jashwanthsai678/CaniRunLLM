## Qwen-Image-2.1-PE-I2I

- `parameters`: REVIEW — not present in config.json, check the model card for Qwen/Qwen-Image-2.1-PE-I2I and fill in manually.
- `context_length`, `num_layers`, `num_kv_heads`, `head_dim`: from `config.json` at https://huggingface.co/Qwen/Qwen-Image-2.1-PE-I2I (num_hidden_layers=None, num_attention_heads=None, num_key_value_heads=None, max_position_embeddings=None).
- `file_size_bytes`: GGUF artifact sizes from https://huggingface.co/prithivMLmods/Qwen-Image-2.1-PE-I2I-GGUF (Q4_K_M = 5.63 GB).
- CAVEAT: No GGUF file matched for quant(s): Q8_0 in prithivMLmods/Qwen-Image-2.1-PE-I2I-GGUF.
- Fetched 2026-09-21 by scripts/draft_all_candidates.py.
