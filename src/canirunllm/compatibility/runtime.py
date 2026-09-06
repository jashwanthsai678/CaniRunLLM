from dataclasses import dataclass
from enum import Enum

from canirunllm.models.model import ModelSpec


class RuntimeVerdict(str, Enum):
    SUPPORTED = "SUPPORTED"
    UNKNOWN = "UNKNOWN"
    UNSUPPORTED = "UNSUPPORTED"


SUPPORTED_RUNTIMES = {
    "llama.cpp",
    "ollama",
    "transformers",
    "vllm",
}


@dataclass(frozen=True)
class RuntimeCapabilities:
    name: str
    supports_multi_gpu: bool
    supports_cpu_offload: bool


RUNTIME_CAPABILITIES = {

    "llama.cpp": RuntimeCapabilities(
        name="llama.cpp",
        supports_multi_gpu=True,
        supports_cpu_offload=True,
    ),

    "ollama": RuntimeCapabilities(
        name="ollama",
        supports_multi_gpu=True,
        supports_cpu_offload=True,
    ),

    "transformers": RuntimeCapabilities(
        name="transformers",
        supports_multi_gpu=True,
        supports_cpu_offload=True,
    ),

    "vllm": RuntimeCapabilities(
        name="vllm",
        supports_multi_gpu=True,
        supports_cpu_offload=True,
    ),
}


def check_runtime_compatibility(
    model: ModelSpec,
) -> RuntimeVerdict:

    if model.runtime is None:
        return RuntimeVerdict.UNKNOWN

    if model.runtime.lower() in {
        runtime.lower()
        for runtime in SUPPORTED_RUNTIMES
    }:
        return RuntimeVerdict.SUPPORTED

    return RuntimeVerdict.UNSUPPORTED


def get_runtime_capabilities(
    runtime: str | None,
) -> RuntimeCapabilities:

    if runtime is None:
        return RuntimeCapabilities(
            name="unknown",
            supports_multi_gpu=False,
            supports_cpu_offload=False,
        )

    return RUNTIME_CAPABILITIES.get(
        runtime.lower(),
        RuntimeCapabilities(
            name=runtime,
            supports_multi_gpu=False,
            supports_cpu_offload=False,
        ),
    )
