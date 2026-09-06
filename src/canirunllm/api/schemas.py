from pydantic import BaseModel


class CPUResponse(BaseModel):
    name: str
    architecture: str
    physical_cores: int | None
    logical_cores: int | None
    frequency_mhz: float | None


class MemoryResponse(BaseModel):
    total_bytes: int
    available_bytes: int
    used_bytes: int
    usage_percent: float


class GPUResponse(BaseModel):
    name: str
    memory_total_bytes: int
    memory_used_bytes: int
    memory_free_bytes: int
    utilization_percent: float


class OSResponse(BaseModel):
    system: str
    release: str
    version: str
    machine: str


class HardwareResponse(BaseModel):
    cpu: CPUResponse
    memory: MemoryResponse
    os: OSResponse
    gpus: list[GPUResponse]


class ModelResponse(BaseModel):
    name: str
    family: str
    architecture: str
    parameters: int
    quantization: str
    context_length: int
    runtime: str | None
    file_size_bytes: int | None


class ReasonItemResponse(BaseModel):
    ok: bool
    text: str


class CompatibilityResponse(BaseModel):
    memory_verdict: str
    runtime_verdict: str
    overall_verdict: str
    confidence: str
    memory_strategy: str
    required_memory_bytes: int
    available_vram_bytes: int
    available_ram_bytes: int
    reason: str

    # Human-facing interpretation of the fields above — generated
    # server-side (see api/presentation.py), never in the frontend.
    friendly_verdict: str
    friendly_icon: str
    reasons: list[ReasonItemResponse]


class ModelResultResponse(BaseModel):
    model: ModelResponse
    compatibility: CompatibilityResponse


class SummaryResponse(BaseModel):
    total: int
    can_run: int
    can_run_with_offload: int
    needs_validation: int
    cannot_run: int


class ScanResponse(BaseModel):
    hardware: HardwareResponse
    summary: SummaryResponse
    results: list[ModelResultResponse]
    recommended: list[ModelResultResponse]
    best_for_you: ModelResultResponse | None
    scanned_at: str


class MemoryBreakdownResponse(BaseModel):
    weight_memory_bytes: int
    kv_cache_bytes: int
    runtime_overhead_bytes: int
    safety_margin_bytes: int
    total_required_bytes: int


class RunCommandResponse(BaseModel):
    runtime: str
    command: str
    note: str


class ModelDetailResponse(BaseModel):
    model: ModelResponse
    compatibility: CompatibilityResponse
    memory_breakdown: MemoryBreakdownResponse
    run_command: RunCommandResponse | None
    alternative: ModelResponse | None
