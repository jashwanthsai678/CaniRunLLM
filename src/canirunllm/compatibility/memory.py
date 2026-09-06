from canirunllm.models.model import ModelSpec


BITS_PER_BYTE = 8


def estimate_weight_memory(model: ModelSpec) -> int:
    """
    Estimate model weight memory from parameter count
    and quantization bits.

    This is an approximation, not an exact runtime requirement.
    """

    bits_per_parameter = get_bits_per_parameter(
        model.quantization
    )

    total_bits = (
        model.parameters * bits_per_parameter
    )

    total_bytes = total_bits // BITS_PER_BYTE

    return total_bytes


def get_bits_per_parameter(quantization: str) -> float:

    quantization = quantization.upper()

    if quantization in {"FP32"}:
        return 32

    if quantization in {"FP16", "BF16"}:
        return 16

    if quantization in {"INT8", "Q8"}:
        return 8

    if quantization == "Q6":
        return 6

    if quantization == "Q5":
        return 5

    if quantization == "Q4":
        return 4

    if quantization == "Q4_K_M":
        return 4

    if quantization == "Q3":
        return 3

    raise ValueError(
        f"Unsupported quantization: {quantization}"
    )
