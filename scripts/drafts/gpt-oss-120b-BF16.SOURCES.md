## gpt-oss-120b-BF16

- `parameters`: REVIEW — not present in config.json, check the model card for unsloth/gpt-oss-120b-BF16 and fill in manually.
- `context_length`, `num_layers`, `num_kv_heads`, `head_dim`: from `config.json` at https://huggingface.co/unsloth/gpt-oss-120b-BF16 (num_hidden_layers=36, num_attention_heads=64, num_key_value_heads=8, max_position_embeddings=131072).
- `file_size_bytes`: REVIEW — no matching quant files found in mradermacher/Huihui-gpt-oss-120b-BF16-abliterated-i1-GGUF.
- CAVEAT: MoE architecture detected (found one of ('num_experts', 'num_local_experts', 'num_experts_per_tok', 'moe_intermediate_size')) — this project's formulas assume dense models. Verify before adding.
- CAVEAT: sliding_window=128 present — context/KV-cache math does not model sliding-window attention and will overestimate memory use (same caveat as Gemma-2).
- CAVEAT: No GGUF file matched for quant(s): Q4_K_M, Q8_0 in mradermacher/Huihui-gpt-oss-120b-BF16-abliterated-i1-GGUF.
- Fetched 2026-10-12 by scripts/draft_all_candidates.py.
