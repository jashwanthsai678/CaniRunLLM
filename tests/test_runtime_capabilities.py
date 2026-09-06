from canirunllm.compatibility.runtime import (
    RuntimeCapabilities,
    RUNTIME_CAPABILITIES,
    get_runtime_capabilities,
)


def test_known_runtimes_support_multi_gpu_and_offload():

    for name in ("llama.cpp", "ollama", "transformers", "vllm"):

        capabilities = RUNTIME_CAPABILITIES[name]

        assert isinstance(capabilities, RuntimeCapabilities)
        assert capabilities.name == name
        assert capabilities.supports_multi_gpu is True
        assert capabilities.supports_cpu_offload is True


def test_unknown_runtime_is_not_registered():

    assert "some-unknown-runtime" not in RUNTIME_CAPABILITIES


def test_get_runtime_capabilities_known_runtime():

    capabilities = get_runtime_capabilities("llama.cpp")

    assert capabilities.supports_multi_gpu is True
    assert capabilities.supports_cpu_offload is True


def test_get_runtime_capabilities_is_case_insensitive():

    capabilities = get_runtime_capabilities("LLAMA.CPP")

    assert capabilities.supports_multi_gpu is True
    assert capabilities.supports_cpu_offload is True


def test_get_runtime_capabilities_unknown_runtime_is_conservative():

    capabilities = get_runtime_capabilities("some-unknown-runtime")

    assert capabilities.supports_multi_gpu is False
    assert capabilities.supports_cpu_offload is False


def test_get_runtime_capabilities_none_is_conservative():

    capabilities = get_runtime_capabilities(None)

    assert capabilities.supports_multi_gpu is False
    assert capabilities.supports_cpu_offload is False
