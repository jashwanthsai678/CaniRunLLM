## Aion-1.0-Instruct-2.3B-ONNX-WebGPU

- `parameters`: REVIEW — not present in config.json, check the model card for microsoft/Aion-1.0-Instruct-2.3B-ONNX-WebGPU and fill in manually.
- `context_length`, `num_layers`, `num_kv_heads`, `head_dim`: from `config.json` at https://huggingface.co/microsoft/Aion-1.0-Instruct-2.3B-ONNX-WebGPU (num_hidden_layers=28, num_attention_heads=24, num_key_value_heads=8, max_position_embeddings=32768).
- `file_size_bytes`: REVIEW — no matching quant files found in REVIEW.
- CAVEAT: sliding_window=2048 present — context/KV-cache math does not model sliding-window attention and will overestimate memory use (same caveat as Gemma-2).
- Fetched 2026-11-23 by scripts/draft_all_candidates.py.
