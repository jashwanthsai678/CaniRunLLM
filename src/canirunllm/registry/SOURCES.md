# Registry data sources

All entries in `models.json` are grounded in publicly published data
as of 2026-09-07. This file records where each field came from so
values can be re-verified or updated later.

## Qwen3-8B

- `parameters`, `context_length` (native), `num_layers`,
  `num_kv_heads`, `head_dim`: from the official model card and
  `config.json` at https://huggingface.co/Qwen/Qwen3-8B
  (`num_hidden_layers=36`, `num_attention_heads=32`,
  `num_key_value_heads=8`, `head_dim=128`,
  `max_position_embeddings=40960`, native context 32,768 tokens,
  extendable to 131,072 via YaRN — YaRN extension is not modeled here).
  Total parameters: 8.2B (official figure; 6.95B non-embedding).
- `file_size_bytes`: GGUF artifact sizes from
  https://huggingface.co/Qwen/Qwen3-8B-GGUF
  (Q4_K_M = 5.03 GB, Q8_0 = 8.71 GB, converted to bytes assuming
  GiB-based reporting for consistency with this project's own
  byte/GB conversions).

## Qwen3-32B

- `parameters`, `context_length` (native), `num_layers`,
  `num_kv_heads`, `head_dim`: from the official model card and
  `config.json` at https://huggingface.co/Qwen/Qwen3-32B
  (`num_hidden_layers=64`, `num_attention_heads=64`,
  `num_key_value_heads=8`, `head_dim=128`,
  `max_position_embeddings=40960`, native context 32,768 tokens,
  extendable to 131,072 via YaRN — not modeled here).
  Total parameters: 32.8B (official figure; 31.2B non-embedding).
- `file_size_bytes`: GGUF artifact sizes from
  https://huggingface.co/Qwen/Qwen3-32B-GGUF
  (Q4_K_M = 19.8 GB, Q8_0 = 34.8 GB, same byte conversion as above).

## Llama-3.1-8B-Instruct

- `config.json` is gated on the official `meta-llama/Llama-3.1-8B-Instruct`
  repo (401 Unauthorized without an accepted-license HF token), so
  architecture fields were read from the public mirror
  https://huggingface.co/unsloth/Meta-Llama-3.1-8B-Instruct
  (`num_hidden_layers=32`, `num_attention_heads=32`,
  `num_key_value_heads=8`, `head_dim=128`,
  `max_position_embeddings=131072` — this is the native context,
  Llama 3.1 does not need a YaRN-style extension for 128K).
- `parameters=8006464512` (~8.03B): the official model card only states
  the rounded "8B" label; the precise figure is a widely-cited
  technical count (Haan et al., 2024), not read directly from a
  single authoritative page — treat as slightly less certain than
  the Qwen figures above.
- `file_size_bytes`: from
  https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF
  (Q4_K_M = 4.92 GB, Q8_0 = 8.54 GB). This is a third-party
  (community) quantization, not published by Meta directly.

## Mistral-7B-Instruct-v0.3

- `config.json` from https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3
  (`num_hidden_layers=32`, `num_attention_heads=32`,
  `num_key_value_heads=8`, `max_position_embeddings=32768`;
  `head_dim=128` is derived as `hidden_size / num_attention_heads`
  since the config does not state it explicitly).
- `parameters=7300000000`: the model card only states the rounded
  "7B params" label; 7.3B is the commonly-cited figure elsewhere,
  not an exact value read from one authoritative source.
- `file_size_bytes`: from
  https://huggingface.co/bartowski/Mistral-7B-Instruct-v0.3-GGUF
  (Q4_K_M = 4.37 GB, Q8_0 = 7.7 GB). Community quantization.

## Gemma-2-9B-it

- `config.json` is gated on the official `google/gemma-2-9b-it` repo
  (401 Unauthorized), so architecture fields were read from the
  public mirror https://huggingface.co/unsloth/gemma-2-9b-it
  (`num_hidden_layers=42`, `num_attention_heads=16`,
  `num_key_value_heads=8`, `head_dim=256`,
  `max_position_embeddings=8192`, `sliding_window=4096`).
- `parameters=9242164736`: from the Gemma 2 technical report
  (arXiv:2408.00118) — 917,962,752 embedding + 8,324,201,984
  non-embedding parameters.
- **Not modeled**: Gemma 2 alternates local (sliding-window) and
  global attention every other layer. This project's KV cache
  formula (`2 × layers × kv_heads × head_dim × context × bytes`)
  assumes every layer attends over the full context, so it will
  **overestimate** Gemma 2's real KV cache size at long context —
  this is a known gap, not a silent inaccuracy we're pretending
  doesn't exist.
- `file_size_bytes`: from
  https://huggingface.co/bartowski/gemma-2-9b-it-GGUF
  (Q4_K_M = 5.76 GB, Q8_0 = 9.83 GB). Community quantization.

## Phi-3.5-mini-instruct

- `config.json` from https://huggingface.co/microsoft/Phi-3.5-mini-instruct
  (`num_hidden_layers=32`, `num_attention_heads=32`,
  `num_key_value_heads=32` — no grouped-query attention, every head
  has its own KV — `max_position_embeddings=131072`; `head_dim=96`
  derived as `hidden_size / num_attention_heads`).
- `parameters=3800000000`: official model card states "3.8B
  parameters" directly.
- `file_size_bytes`: from
  https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF
  (Q4_K_M = 2.39 GB, Q8_0 = 4.06 GB). Community quantization.

## DeepSeek-R1-Distill-Llama-8B

- A dense distillation of DeepSeek-R1's reasoning traces onto the
  Llama-3.1-8B architecture — deliberately chosen over an actual
  DeepSeek-V2/V3-family model because those are Mixture-of-Experts
  (sparse active parameters vs. total stored parameters), which
  `ModelSpec` does not yet represent (see project roadmap, MoE
  support is a future item). Using an MoE model's total parameter
  count in the current weight-memory formula would misstate its
  real memory requirement.
- `config.json` from
  https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-8B
  confirms it is architecturally identical to Llama-3.1-8B
  (`num_hidden_layers=32`, `num_key_value_heads=8`, `head_dim=128`,
  `max_position_embeddings=131072`), so the same parameter count is
  reused.
- `file_size_bytes`: from
  https://huggingface.co/bartowski/DeepSeek-R1-Distill-Llama-8B-GGUF
  (Q4_K_M = 4.92 GB, Q8_0 = 8.54 GB). Community quantization.

## Qwen3-4B / Qwen3-14B

- Fill out the rest of Qwen3's dense lineup alongside the existing
  8B/32B entries. `config.json` from
  https://huggingface.co/Qwen/Qwen3-4B and
  https://huggingface.co/Qwen/Qwen3-14B.
  - 4B: `num_hidden_layers=36`, `num_key_value_heads=8`,
    `head_dim=128`, native context 32,768 (config
    `max_position_embeddings=40960`, YaRN-extendable, not modeled).
    Parameters: 4.0B official figure (3.6B non-embedding).
  - 14B: `num_hidden_layers=40`, `num_key_value_heads=8`,
    `head_dim=128`, same native context pattern. Parameters: 14.8B
    official figure (13.2B non-embedding).
- `file_size_bytes`: official Qwen GGUF repos
  https://huggingface.co/Qwen/Qwen3-4B-GGUF (Q4_K_M = 2.5 GB,
  Q8_0 = 4.28 GB) and https://huggingface.co/Qwen/Qwen3-14B-GGUF
  (Q4_K_M = 9 GB, Q8_0 = 15.7 GB).

## Llama-3.2-3B-Instruct / Llama-3.2-1B-Instruct

- Meta's small "edge" models — deliberately included because they're
  realistically runnable on modest hardware, unlike most of this
  registry. `config.json` is gated on the official repos (401), so
  read from public mirrors
  https://huggingface.co/unsloth/Llama-3.2-3B-Instruct and
  https://huggingface.co/unsloth/Llama-3.2-1B-Instruct.
  - 3B: `num_hidden_layers=28`, `num_key_value_heads=8`,
    `head_dim=128`, `max_position_embeddings=131072`.
    Parameters: 3.21B (rounded figure; exact integer count not
    confirmed from a single authoritative source).
  - 1B: `num_hidden_layers=16`, `num_key_value_heads=8`,
    `head_dim=64` (smaller head dimension than the 3B model — not a
    typo, confirmed from config), `max_position_embeddings=131072`.
    Parameters: 1.23B (rounded, same caveat as above).
- `file_size_bytes`: from
  https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF
  (Q4_K_M = 2.02 GB, Q8_0 = 3.42 GB) and
  https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF
  (Q4_K_M = 808 MB, Q8_0 = 1.32 GB). Community quantization.

## Phi-4

- `config.json` from https://huggingface.co/microsoft/phi-4
  (`num_hidden_layers=40`, `num_attention_heads=40`,
  `num_key_value_heads=10`, `head_dim=128`,
  `max_position_embeddings=16384` — notably shorter native context
  than Phi-3.5-mini). Parameters: 14B, stated directly on the model
  card. `architecture: "Phi3"` is carried over from Phi-3.5-mini's
  confirmed `architectures` field, not independently re-confirmed
  for Phi-4's own config — Phi-4 is documented as using the same
  dense Phi3-family transformer design, but this specific field
  wasn't re-checked.
- `file_size_bytes`: from https://huggingface.co/bartowski/phi-4-GGUF
  (Q4_K_M = 9.05 GB, Q8_0 = 15.6 GB). Community quantization.

## Gemma-2-2B-it

- The smaller sibling of Gemma-2-9B-it, included for lower-VRAM
  hardware. `config.json` gated on the official repo (401), read
  from the public mirror
  https://huggingface.co/unsloth/gemma-2-2b-it
  (`num_hidden_layers=26`, `num_attention_heads=8`,
  `num_key_value_heads=4`, `head_dim=256`,
  `max_position_embeddings=8192`, `sliding_window=4096`).
- `parameters=2614636800`: exact sum from the Gemma 2 technical
  report (arXiv:2408.00118) — 590,118,912 embedding +
  2,024,517,888 non-embedding.
- Same **not-modeled caveat as Gemma-2-9B-it**: alternating
  local/global attention means this project's KV cache formula will
  overestimate real KV cache size.
- `file_size_bytes`: from
  https://huggingface.co/bartowski/gemma-2-2b-it-GGUF
  (Q4_K_M = 1.71 GB, Q8_0 = 2.78 GB). Community quantization.

## Qwen2.5-Coder-7B-Instruct

- Included specifically to give the recommendation engine's CODING
  workload profile a model that is actually differentiated for that
  task (rather than only general-purpose chat models).
  `config.json` from
  https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct
  (`num_hidden_layers=28`, `num_key_value_heads=4`, `head_dim=128`,
  native `max_position_embeddings=32768`, YaRN-extendable to
  131,072 — not modeled, same as the Qwen3 entries).
  Parameters: 7.61B official figure (6.53B non-embedding).
- `architecture: "Qwen2"` reflects that Qwen2.5 is architecturally
  Qwen2-generation, not Qwen3 — a deliberate distinction from the
  Qwen3-family entries above.
- `file_size_bytes`: from
  https://huggingface.co/bartowski/Qwen2.5-Coder-7B-Instruct-GGUF
  (Q4_K_M = 4.68 GB, Q8_0 = 8.1 GB). Community quantization.

## TinyLlama-1.1B-Chat-v1.0

- Included deliberately as a genuinely tiny, CPU-friendly model —
  the only entry in this registry likely to actually show `CAN_RUN`
  on very constrained hardware (e.g. this project's own dev
  machine, which shows `CANNOT_RUN` for every other entry due to
  low free RAM). `config.json` from
  https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0
  (`num_hidden_layers=22`, `num_attention_heads=32`,
  `num_key_value_heads=4`, `head_dim=64`,
  `max_position_embeddings=2048` — a real, notably short native
  context, not an error; this model predates the long-context era).
  Parameters: 1.1B, stated directly on the model card.
- `file_size_bytes`: from
  https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF
  (Q4_K_M = 669 MB, Q8_0 = 1.17 GB). Community quantization
  (TheBloke, not bartowski — this model predates bartowski's
  typical catalog).

## Qwen2.5-0.5B-Instruct / Qwen2.5-1.5B-Instruct

- The tiniest realistic Qwen sizes, deliberately added for very
  constrained hardware. `config.json` from
  https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct and
  https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct.
  - 0.5B: `num_hidden_layers=24`, `num_key_value_heads=2`,
    `head_dim=64`, native context 32,768. Parameters: 0.49B official
    figure (0.36B non-embedding).
  - 1.5B: `num_hidden_layers=28`, `num_key_value_heads=2`,
    `head_dim=128`, native context 32,768. Parameters: 1.54B
    official figure (1.31B non-embedding).
- `architecture: "Qwen2"` — these are Qwen2.5-generation, same
  distinction as Qwen2.5-Coder-7B above.
- `file_size_bytes`: official Qwen GGUF repos
  https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF
  (Q4_K_M = 491 MB, Q8_0 = 676 MB) and
  https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF
  (Q4_K_M = 1.12 GB, Q8_0 = 1.89 GB).

## Phi-2

- Microsoft's earlier, still widely-used small model — a distinct
  architecture generation from Phi-3.5/Phi-4 (no grouped-query
  attention: `num_key_value_heads` equals `num_attention_heads`).
  `config.json` from https://huggingface.co/microsoft/phi-2
  (`num_hidden_layers=32`, `num_attention_heads=32`,
  `num_key_value_heads=32`, `head_dim=80`,
  `max_position_embeddings=2048`). Parameters: 2.7B, stated directly
  ("Phi-2 is a Transformer with 2.7 billion parameters").
  `architecture: "Phi"` (not "Phi3") to reflect this is a different
  model class from the later Phi-3/Phi-4 family.
- `file_size_bytes`: from https://huggingface.co/TheBloke/phi-2-GGUF
  (Q4_K_M = 1.79 GB, Q8_0 = 2.96 GB). Community quantization.

## SmolLM2-1.7B-Instruct

- Hugging Face's own compact model family (also comes in 135M and
  360M, not added here). `config.json` from
  https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct
  confirms a Llama-style architecture (`num_hidden_layers=24`,
  `num_key_value_heads=32` — no GQA — `head_dim=64`,
  `max_position_embeddings=8192`). Parameters: 1.7B, stated on the
  model card.
- `file_size_bytes`: from
  https://huggingface.co/bartowski/SmolLM2-1.7B-Instruct-GGUF
  (Q4_K_M = 1.06 GB, Q8_0 = 1.82 GB). Community quantization.

## StableLM-2-1.6B-Chat

- Stability AI's small chat model. `config.json` from
  https://huggingface.co/stabilityai/stablelm-2-1_6b-chat
  (`num_hidden_layers=24`, `num_key_value_heads=32` — no GQA —
  `head_dim=64`, `max_position_embeddings=4096`). Parameters: 1.6B,
  stated on the model card.
- `file_size_bytes`: **approximated from the base (non-chat)
  `stablelm-2-1_6b` model's GGUF quantization**
  (https://huggingface.co/afrideva/stablelm-2-1_6b-GGUF,
  Q4_K_M = 1.03 GB, Q8_0 = 1.75 GB) — no Q4_K_M/Q8_0 GGUF quantization
  of the chat variant specifically was found. Base and chat share
  the same architecture and parameter count (only fine-tuning
  differs), so file size should be effectively identical, but this
  is a slightly less direct source than the others in this registry.

## OLMo-1B

- Allen Institute for AI's fully-open model (open weights *and*
  training data, unusually for this list) — included specifically
  for that transparency, not just its small size.
  `config.json` from https://huggingface.co/allenai/OLMo-1B-hf
  (`OlmoForCausalLM`, `num_hidden_layers=16`,
  `num_key_value_heads=16` — no GQA — `head_dim=128`,
  `max_position_embeddings=2048`). Parameters: 1B, stated on the
  model card.
- `file_size_bytes`: from https://huggingface.co/nopperl/OLMo-1B-GGUF
  (Q4_K_M = 734 MB, Q8_0 = 1.25 GB). Community quantization; the
  more obvious `tensorblock/OLMo-1B-hf-GGUF` repo only kept Q2_K/
  Q3_K_M quantizations at the time of writing, so this alternate
  repo was used instead.

## StarCoder2-3B

- BigCode's coding-specific small model — a second, distinct
  coding-focused entry alongside Qwen2.5-Coder-7B, at a much smaller
  size class. `config.json` from
  https://huggingface.co/bigcode/starcoder2-3b
  (`num_hidden_layers=30`, `num_key_value_heads=2`, `head_dim=128`,
  `max_position_embeddings=16384`). Parameters: 3B, stated directly
  on the model card.
- `file_size_bytes`: from
  https://huggingface.co/second-state/StarCoder2-3B-GGUF
  (Q4_K_M = 1.85 GB, Q8_0 = 3.22 GB). Community quantization; the
  `tensorblock/starcoder2-3b-GGUF` repo only kept Q2_K/Q3_K_M
  quantizations at the time of writing, so this alternate repo was
  used instead.

## Falcon3-3B-Instruct

- TII's (Technology Innovation Institute) small instruction model.
  `config.json` from
  https://huggingface.co/tiiuae/Falcon3-3B-Instruct
  (`LlamaForCausalLM`, `num_hidden_layers=22`,
  `num_key_value_heads=4`, `head_dim=256`,
  `max_position_embeddings=32768`, matching the stated "32K context
  length"). Parameters: 3B, stated on the model card as a rounded
  figure (exact integer count not confirmed from one authoritative
  source, same caveat as Mistral/Llama-3.2 above).
- `file_size_bytes`: from
  https://huggingface.co/bartowski/Falcon3-3B-Instruct-GGUF
  (Q4_K_M = 2.01 GB, Q8_0 = 3.43 GB). Community quantization.

## Yi-1.5-6B-Chat

- 01.AI's small chat model. `config.json` from
  https://huggingface.co/01-ai/Yi-1.5-6B-Chat
  (`LlamaForCausalLM`, `num_hidden_layers=32`,
  `num_key_value_heads=4`, `head_dim=128`,
  `max_position_embeddings=4096`). Parameters: 6B, stated on the
  model card. **Context length is genuinely short (4,096) for this
  specific variant** — confirmed on both the config and the model
  card, which explicitly notes larger Yi-1.5 variants offer 16K/32K
  instead; this is a real limitation of the 6B-Chat release, not a
  data error.
- `file_size_bytes`: from https://huggingface.co/bartowski/Yi-1.5-6B-Chat-GGUF
  (Q4_K_M = 3.67 GB, Q8_0 = 6.44 GB). Community quantization.

## InternLM2.5-7B-Chat

- Shanghai AI Laboratory's chat model — a new organization for this
  registry. `config.json` from
  https://huggingface.co/internlm/internlm2_5-7b-chat
  (`num_hidden_layers=32`, `num_key_value_heads=8`, `head_dim=128`,
  `max_position_embeddings=32768`). Parameters: 7B, stated on the
  model card. `architecture: "InternLM2"` reflects the actual
  `InternLM2ForCausalLM` model class, distinct from Llama/Qwen.
- `file_size_bytes`: from
  https://huggingface.co/bartowski/internlm2_5-7b-chat-GGUF
  (Q4_K_M = 4.71 GB, Q8_0 = 8.22 GB). Community quantization.

## Granite-3.1-2B-Instruct

- IBM's open Granite model family — a new organization for this
  registry. `config.json` from
  https://huggingface.co/ibm-granite/granite-3.1-2b-instruct
  (`GraniteForCausalLM`, `num_hidden_layers=40`,
  `num_key_value_heads=8`, `head_dim=64`,
  `max_position_embeddings=131072`). Parameters: 2.5B ("2.5B total,
  2.5B active" — this variant is fully dense, not MoE, stated
  directly on the model card).
- `file_size_bytes`: from
  https://huggingface.co/bartowski/granite-3.1-2b-instruct-GGUF
  (Q4_K_M = 1.55 GB, Q8_0 = 2.69 GB). Community quantization.

## DeepSeek-Coder-6.7B-Instruct

- DeepSeek's earlier, non-R1, dense coding-specific model — a
  second DeepSeek entry alongside the R1-distill, and a third
  coding-focused entry alongside Qwen2.5-Coder-7B and StarCoder2-3B.
  `config.json` from
  https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-instruct
  (Llama-architecture, `num_hidden_layers=32`,
  `num_key_value_heads=32` — no GQA, full multi-head attention —
  `head_dim=128`, `max_position_embeddings=16384`). Parameters:
  6.7B, stated directly on the model card.
- `file_size_bytes`: from
  https://huggingface.co/TheBloke/deepseek-coder-6.7B-instruct-GGUF
  (Q4_K_M = 4.08 GB, Q8_0 = 7.16 GB). Community quantization.

## Gemma-3-4B-it

- Google's newest Gemma generation. `config.json` is gated on the
  official repo (401), read from the public mirror
  https://huggingface.co/unsloth/gemma-3-4b-it — architecture
  fields are nested under a `text_config` key since Gemma 3 is a
  multimodal model class (`num_hidden_layers=34`,
  `num_key_value_heads=4`, `head_dim=256`,
  `max_position_embeddings=131072`, `sliding_window=1024`).
  Parameters: 4B, stated on the model card (text+vision total; this
  registry only models the text/language side, consistent with
  every other entry — no vision support exists in this project).
- **Same not-modeled caveat as Gemma-2** applies here, and more
  acutely: Gemma 3 uses an even smaller sliding window (1024 vs.
  Gemma 2's 4096) with 5 local-attention layers per 1 global layer,
  so this project's full-context KV cache formula will overestimate
  Gemma 3's real KV cache size more than it does for Gemma 2.
- `file_size_bytes`: from
  https://huggingface.co/bartowski/google_gemma-3-4b-it-GGUF
  (Q4_K_M = 2.49 GB, Q8_0 = 4.13 GB). Community quantization.

## GLM-4-9B-Chat

- Zhipu AI's GLM-4 chat model — a new organization for this
  registry. `config.json` from
  https://huggingface.co/THUDM/glm-4-9b-chat, which uses
  ChatGLM-style config field names (`multi_query_group_num=2` for
  KV heads, `kv_channels=128` for head dimension, `seq_length` for
  context): `num_hidden_layers=40`, `num_key_value_heads=2`,
  `head_dim=128`, `max_position_embeddings=131072`. Parameters: 9B,
  stated on the model card. `architecture: "GLM4"` is a project
  label, not the literal HF `model_type` (`chatglm`).
- `file_size_bytes`: from
  https://huggingface.co/bartowski/glm-4-9b-chat-GGUF
  (Q4_K_M = 6.25 GB, Q8_0 = 9.99 GB). Community quantization.

## Deliberately excluded models

- **MiniCPM3-4B** (OpenBMB): its `config.json` shows a
  Multi-head Latent Attention design (`qk_nope_head_dim=64` +
  `qk_rope_head_dim=32`, `num_key_value_heads` equal to
  `num_attention_heads` with no real reduction). This project's KV
  cache formula (`2 × layers × kv_heads × head_dim × context ×
  bytes`) assumes conventional per-head K/V storage and would be
  fundamentally wrong for an MLA model — not just imprecise, but
  built on the wrong mechanism entirely (MLA compresses KV into a
  shared latent space instead of storing per-head K/V). Excluded
  rather than included with silently bad numbers.
- **Command-R7B** (Cohere): `config.json` is gated on both the
  original `CohereForAI/c4ai-command-r7b-12-2024` and its successor
  org `CohereLabs/c4ai-command-r7b-12-2024` (401 Unauthorized on
  both), and no ungated community mirror was found. Excluded rather
  than guess at architecture values.

## Fields NOT independently verified

- `kv_cache_dtype_bits: 16` for every entry is an assumption
  (llama.cpp's default KV cache precision is FP16 unless explicitly
  quantized), not a value read from any of the sources above.
- `runtime: "llama.cpp"` reflects that llama.cpp supports Qwen3 GGUF
  models (true at the time of writing), not a per-artifact
  compatibility certificate.

## Correction from the previous registry

The previous registry contained a family called "Qwen3-27B", which
does not exist in Qwen3's actual lineup. Qwen3's dense models are:
0.6B, 1.7B, 4B, 8B, 14B, 32B (source: Qwen3 announcement at
https://qwenlm.github.io/blog/qwen3/ and
https://github.com/QwenLM/Qwen3). It has been replaced with the real
Qwen3-32B entry above.

The previous registry also used the quantization label `"Q8"`, which
is not a real GGUF quantization scheme — the actual scheme name is
`"Q8_0"` (see `compatibility/memory.py`, which now accepts both).
