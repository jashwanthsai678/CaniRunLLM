from canirunllm.compatibility.memory_planner import MemoryPlan
from canirunllm.compatibility.runtime import RuntimeCapabilities
from canirunllm.compatibility.engine import determine_memory_strategy


def make_plan(
    can_fit_single_gpu,
    can_fit_multi_gpu,
    can_fit_with_cpu_offload,
):
    return MemoryPlan(
        required_bytes=0,
        largest_gpu_free_bytes=0,
        total_gpu_free_bytes=0,
        available_ram_bytes=0,
        usable_gpu_bytes=0,
        usable_ram_bytes=0,
        can_fit_single_gpu=can_fit_single_gpu,
        can_fit_multi_gpu=can_fit_multi_gpu,
        can_fit_with_cpu_offload=can_fit_with_cpu_offload,
        gpu_count=2,
    )


def make_capabilities(supports_multi_gpu, supports_cpu_offload):
    return RuntimeCapabilities(
        name="test",
        supports_multi_gpu=supports_multi_gpu,
        supports_cpu_offload=supports_cpu_offload,
    )


def test_single_gpu_wins_even_if_multi_gpu_also_fits():

    plan = make_plan(True, True, True)
    capabilities = make_capabilities(True, True)

    assert determine_memory_strategy(plan, capabilities) == "SINGLE_GPU"


def test_multi_gpu_requires_runtime_support():

    plan = make_plan(False, True, True)
    capabilities = make_capabilities(False, True)

    assert determine_memory_strategy(plan, capabilities) == "CPU_OFFLOAD"


def test_multi_gpu_used_when_supported():

    plan = make_plan(False, True, True)
    capabilities = make_capabilities(True, True)

    assert determine_memory_strategy(plan, capabilities) == "MULTI_GPU"


def test_cpu_offload_requires_runtime_support():

    plan = make_plan(False, False, True)
    capabilities = make_capabilities(True, False)

    assert determine_memory_strategy(plan, capabilities) == "NONE"


def test_none_when_nothing_fits():

    plan = make_plan(False, False, False)
    capabilities = make_capabilities(True, True)

    assert determine_memory_strategy(plan, capabilities) == "NONE"
