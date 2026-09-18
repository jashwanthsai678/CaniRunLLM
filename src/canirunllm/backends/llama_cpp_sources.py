"""Verified Hugging Face GGUF repos for registry families - taken
directly from registry/SOURCES.md's own citations, the same audit
trail already used for each entry's file_size_bytes. A family missing
here means nobody has verified where its GGUF files actually live, so
it can't be downloaded through the llama.cpp backend.

Repo only, not filename: the exact filename for a given quantization
is resolved dynamically at download time against the repo's real file
listing (see backends/llama_cpp.py) - which repo to trust is a human
judgment call, but which file in it matches "Q4_K_M" is mechanical.
"""

HF_GGUF_REPOS: dict[str, str] = {
    "Qwen3-4B": "Qwen/Qwen3-4B-GGUF",
    "Qwen3-8B": "Qwen/Qwen3-8B-GGUF",
    "Qwen3-14B": "Qwen/Qwen3-14B-GGUF",
    "Qwen3-32B": "Qwen/Qwen3-32B-GGUF",
    "Qwen2.5-0.5B-Instruct": "Qwen/Qwen2.5-0.5B-Instruct-GGUF",
    "Qwen2.5-1.5B-Instruct": "Qwen/Qwen2.5-1.5B-Instruct-GGUF",
    "Qwen2.5-Coder-7B-Instruct": "bartowski/Qwen2.5-Coder-7B-Instruct-GGUF",
    "Llama-3.1-8B-Instruct": "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
    "Llama-3.2-3B-Instruct": "bartowski/Llama-3.2-3B-Instruct-GGUF",
    "Llama-3.2-1B-Instruct": "bartowski/Llama-3.2-1B-Instruct-GGUF",
    "Mistral-7B-Instruct-v0.3": "bartowski/Mistral-7B-Instruct-v0.3-GGUF",
    "Gemma-2-9B-it": "bartowski/gemma-2-9b-it-GGUF",
    "Gemma-2-2B-it": "bartowski/gemma-2-2b-it-GGUF",
    "Gemma-3-4B-it": "bartowski/google_gemma-3-4b-it-GGUF",
    "Phi-3.5-mini-instruct": "bartowski/Phi-3.5-mini-instruct-GGUF",
    "Phi-4": "bartowski/phi-4-GGUF",
    "Phi-2": "TheBloke/phi-2-GGUF",
    "DeepSeek-R1-Distill-Llama-8B": "bartowski/DeepSeek-R1-Distill-Llama-8B-GGUF",
    "DeepSeek-Coder-6.7B-Instruct": "TheBloke/deepseek-coder-6.7B-instruct-GGUF",
    "TinyLlama-1.1B-Chat-v1.0": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
    "SmolLM2-1.7B-Instruct": "bartowski/SmolLM2-1.7B-Instruct-GGUF",
    "StableLM-2-1.6B-Chat": "afrideva/stablelm-2-1_6b-GGUF",
    "OLMo-1B": "nopperl/OLMo-1B-GGUF",
    "StarCoder2-3B": "second-state/StarCoder2-3B-GGUF",
    "Falcon3-3B-Instruct": "bartowski/Falcon3-3B-Instruct-GGUF",
    "Yi-1.5-6B-Chat": "bartowski/Yi-1.5-6B-Chat-GGUF",
    "InternLM2.5-7B-Chat": "bartowski/internlm2_5-7b-chat-GGUF",
    "Granite-3.1-2B-Instruct": "bartowski/granite-3.1-2b-instruct-GGUF",
    "GLM-4-9B-Chat": "bartowski/glm-4-9b-chat-GGUF",
}
