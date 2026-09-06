from dataclasses import dataclass


@dataclass
class ModelSpec:

    name: str
    family: str

    parameters: int
    architecture: str

    quantization: str
    context_length: int

    file_size_bytes: int | None = None

    runtime: str | None = None

    num_layers: int | None = None
    num_kv_heads: int | None = None
    head_dim: int | None = None
    kv_cache_dtype_bits: int = 16

    @property
    def identifier(self) -> str:

        runtime = self.runtime or "unknown"

        return (
            f"{self.family}:"
            f"{self.quantization}:"
            f"{runtime}"
        )
