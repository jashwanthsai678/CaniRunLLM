"""Verified Ollama tags for specific registry entries - checked directly
against https://ollama.com/library/<family>/tags at the time these were
added. Only models actually confirmed here get an exact "ollama run"
command or become downloadable through the Ollama backend; everything
else gets an honest "search the library" fallback instead of a guessed
tag. Ollama tag naming does not reliably match this project's model
names (different orgs use "-instruct-", "-it-", "-mini-instruct-", or
nothing at all before the quantization suffix), so this cannot be
derived mechanically.

Single source of truth, used by both api/presentation.py (to display
the "ollama run" command) and backends/ollama.py (to actually pull it).
"""

OLLAMA_TAGS: dict[str, str] = {
    "Qwen3-4B-Q4_K_M": "qwen3:4b-q4_K_M",
    "Qwen3-4B-Q8_0": "qwen3:4b-q8_0",
    "Qwen3-8B-Q4_K_M": "qwen3:8b-q4_K_M",
    "Qwen3-8B-Q8_0": "qwen3:8b-q8_0",
    "Qwen3-14B-Q4_K_M": "qwen3:14b-q4_K_M",
    "Qwen3-14B-Q8_0": "qwen3:14b-q8_0",
    "Qwen3-32B-Q4_K_M": "qwen3:32b-q4_K_M",
    "Qwen3-32B-Q8_0": "qwen3:32b-q8_0",
    "Qwen2.5-0.5B-Instruct-Q4_K_M": "qwen2.5:0.5b-instruct-q4_K_M",
    "Qwen2.5-0.5B-Instruct-Q8_0": "qwen2.5:0.5b-instruct-q8_0",
    "Qwen2.5-1.5B-Instruct-Q4_K_M": "qwen2.5:1.5b-instruct-q4_K_M",
    "Qwen2.5-1.5B-Instruct-Q8_0": "qwen2.5:1.5b-instruct-q8_0",
    "Qwen2.5-Coder-7B-Instruct-Q4_K_M": "qwen2.5-coder:7b-instruct-q4_K_M",
    "Qwen2.5-Coder-7B-Instruct-Q8_0": "qwen2.5-coder:7b-instruct-q8_0",
    "Llama-3.1-8B-Instruct-Q4_K_M": "llama3.1:8b-instruct-q4_K_M",
    "Llama-3.1-8B-Instruct-Q8_0": "llama3.1:8b-instruct-q8_0",
    "Llama-3.2-3B-Instruct-Q4_K_M": "llama3.2:3b-instruct-q4_K_M",
    "Llama-3.2-3B-Instruct-Q8_0": "llama3.2:3b-instruct-q8_0",
    "Llama-3.2-1B-Instruct-Q4_K_M": "llama3.2:1b-instruct-q4_K_M",
    "Llama-3.2-1B-Instruct-Q8_0": "llama3.2:1b-instruct-q8_0",
    "Mistral-7B-Instruct-v0.3-Q4_K_M": "mistral:7b-instruct-q4_K_M",
    "Mistral-7B-Instruct-v0.3-Q8_0": "mistral:7b-instruct-q8_0",
    "Gemma-2-9B-it-Q4_K_M": "gemma2:9b-instruct-q4_K_M",
    "Gemma-2-9B-it-Q8_0": "gemma2:9b-instruct-q8_0",
    "Gemma-3-4B-it-Q4_K_M": "gemma3:4b-it-q4_K_M",
    "Gemma-3-4B-it-Q8_0": "gemma3:4b-it-q8_0",
    "Phi-3.5-mini-instruct-Q4_K_M": "phi3.5:3.8b-mini-instruct-q4_K_M",
    "Phi-3.5-mini-instruct-Q8_0": "phi3.5:3.8b-mini-instruct-q8_0",
    "Phi-4-Q4_K_M": "phi4:14b-q4_K_M",
    "Phi-4-Q8_0": "phi4:14b-q8_0",
    "DeepSeek-R1-Distill-Llama-8B-Q4_K_M": "deepseek-r1:8b-llama-distill-q4_K_M",
    "DeepSeek-R1-Distill-Llama-8B-Q8_0": "deepseek-r1:8b-llama-distill-q8_0",
    "TinyLlama-1.1B-Chat-v1.0-Q4_K_M": "tinyllama:1.1b-chat-v1-q4_K_M",
    "TinyLlama-1.1B-Chat-v1.0-Q8_0": "tinyllama:1.1b-chat-v1-q8_0",
}
