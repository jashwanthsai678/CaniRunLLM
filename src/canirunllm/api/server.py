from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from canirunllm.application.scanner_service import ScannerService
from canirunllm.hardware.scanner import scan_hardware
from canirunllm.models.hardware import HardwareProfile
from canirunllm.models.model import ModelSpec
from canirunllm.models.results import ModelCheckResult

from canirunllm.compatibility.engine import (
    CompatibilityResult,
    check_compatibility,
)
from canirunllm.compatibility.decision import OverallVerdict
from canirunllm.compatibility.requirements import estimate_memory_requirement

from canirunllm.recommendation.engine import rank_models, RankedModel
from canirunllm.recommendation.tier import RecommendationTier

from canirunllm.performance.prediction import (
    predict_performance,
    PerformancePrediction,
)

from canirunllm.api.presentation import (
    friendly_verdict,
    build_reasons,
    build_run_command,
    pick_best_for_you,
    pick_alternative,
)

from canirunllm.api.schemas import (
    CPUResponse,
    MemoryResponse,
    GPUResponse,
    OSResponse,
    HardwareResponse,
    ModelResponse,
    ReasonItemResponse,
    CompatibilityResponse,
    PerformanceRangeResponse,
    PerformanceResponse,
    ModelResultResponse,
    SummaryResponse,
    ScanResponse,
    MemoryBreakdownResponse,
    RunCommandResponse,
    ModelDetailResponse,
)


WEB_DIR = Path(__file__).resolve().parent.parent / "web"
STATIC_DIR = WEB_DIR / "static"
TEMPLATES_DIR = WEB_DIR / "templates"

RECOMMENDED_TIERS = {
    RecommendationTier.BEST_MATCH,
    RecommendationTier.GOOD,
}
MAX_RECOMMENDED = 5


app = FastAPI(title="CanIRunLLM")

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


_service = ScannerService()


def _hardware_to_response(hardware: HardwareProfile) -> HardwareResponse:
    return HardwareResponse(
        cpu=CPUResponse(**asdict(hardware.cpu)),
        memory=MemoryResponse(**asdict(hardware.memory)),
        os=OSResponse(**asdict(hardware.os)),
        gpus=[GPUResponse(**asdict(gpu)) for gpu in hardware.gpus],
    )


def _model_to_response(model: ModelSpec) -> ModelResponse:
    return ModelResponse(
        name=model.name,
        family=model.family,
        architecture=model.architecture,
        parameters=model.parameters,
        quantization=model.quantization,
        context_length=model.context_length,
        runtime=model.runtime,
        file_size_bytes=model.file_size_bytes,
    )


def _compatibility_to_response(
    model: ModelSpec,
    compatibility: CompatibilityResult,
) -> CompatibilityResponse:

    label, icon = friendly_verdict(compatibility.overall_verdict)

    return CompatibilityResponse(
        memory_verdict=compatibility.memory_verdict.value,
        runtime_verdict=compatibility.runtime_verdict.value,
        overall_verdict=compatibility.overall_verdict.value,
        confidence=compatibility.confidence.value,
        memory_strategy=compatibility.memory_strategy,
        required_memory_bytes=compatibility.required_memory_bytes,
        available_vram_bytes=compatibility.available_vram_bytes,
        available_ram_bytes=compatibility.available_ram_bytes,
        reason=compatibility.reason,
        friendly_verdict=label,
        friendly_icon=icon,
        reasons=[
            ReasonItemResponse(ok=item.ok, text=item.text)
            for item in build_reasons(model, compatibility)
        ],
    )


def _performance_to_response(
    performance: PerformancePrediction,
) -> PerformanceResponse:

    speed = performance.generation_speed

    return PerformanceResponse(
        generation_speed=(
            PerformanceRangeResponse(
                low=speed.low,
                high=speed.high,
                unit=speed.unit,
            )
            if speed is not None
            else None
        ),
        confidence=performance.confidence.value,
        source=performance.source.value,
        explanation=performance.explanation,
    )


def _result_to_response(item: ModelCheckResult) -> ModelResultResponse:
    return ModelResultResponse(
        model=_model_to_response(item.model),
        compatibility=_compatibility_to_response(item.model, item.compatibility),
        performance=_performance_to_response(
            predict_performance(item.model, item.compatibility)
        ),
    )


def _ranked_to_response(entry: RankedModel) -> ModelResultResponse:
    return ModelResultResponse(
        model=_model_to_response(entry.model),
        compatibility=_compatibility_to_response(entry.model, entry.compatibility),
        performance=_performance_to_response(entry.performance),
    )


def _build_summary(results: list[ModelCheckResult]) -> SummaryResponse:

    counts = {verdict: 0 for verdict in OverallVerdict}

    for item in results:
        counts[item.compatibility.overall_verdict] += 1

    return SummaryResponse(
        total=len(results),
        can_run=counts[OverallVerdict.CAN_RUN],
        can_run_with_offload=counts[OverallVerdict.CAN_RUN_WITH_OFFLOAD],
        needs_validation=counts[OverallVerdict.NEEDS_VALIDATION],
        cannot_run=counts[OverallVerdict.CANNOT_RUN],
    )


def _scan_hardware_or_500() -> HardwareProfile:
    try:
        return scan_hardware()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Hardware scan failed: {exc}",
        )


@app.get("/api/health")
def get_health():
    return {"status": "ok"}


@app.get("/api/hardware", response_model=HardwareResponse)
def get_hardware():
    hardware = _scan_hardware_or_500()
    return _hardware_to_response(hardware)


@app.get("/api/models", response_model=list[ModelResultResponse])
def get_models():
    hardware = _scan_hardware_or_500()
    models = _service.resolver.resolve_all()

    results = [
        ModelCheckResult(
            model=model,
            compatibility=check_compatibility(hardware, model),
        )
        for model in models
    ]

    return [_result_to_response(item) for item in results]


@app.get("/api/scan", response_model=ScanResponse)
def get_scan():
    hardware = _scan_hardware_or_500()
    models = _service.resolver.resolve_all()

    results = [
        ModelCheckResult(
            model=model,
            compatibility=check_compatibility(hardware, model),
        )
        for model in models
    ]

    ranked = rank_models(results)

    recommended = [
        _ranked_to_response(entry)
        for entry in ranked
        if entry.tier in RECOMMENDED_TIERS
    ][:MAX_RECOMMENDED]

    best_entry = pick_best_for_you(ranked)
    best_for_you = (
        _ranked_to_response(best_entry) if best_entry is not None else None
    )

    return ScanResponse(
        hardware=_hardware_to_response(hardware),
        summary=_build_summary(results),
        results=[_result_to_response(item) for item in results],
        recommended=recommended,
        best_for_you=best_for_you,
        scanned_at=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/api/models/{model_id}", response_model=ModelDetailResponse)
def get_model_detail(model_id: str):

    model = _service.resolver.get_variant(model_id)

    if model is None:
        raise HTTPException(
            status_code=404,
            detail=f"Model not found: {model_id}",
        )

    hardware = _scan_hardware_or_500()

    compatibility = check_compatibility(hardware, model)
    requirement = estimate_memory_requirement(model)

    run_command = build_run_command(model)
    run_command_response = (
        RunCommandResponse(
            runtime=run_command.runtime,
            command=run_command.command,
            note=run_command.note,
        )
        if run_command is not None
        else None
    )

    alternative_response = None

    if compatibility.overall_verdict == OverallVerdict.CANNOT_RUN:

        all_models = _service.resolver.resolve_all()
        all_results = [
            ModelCheckResult(
                model=other_model,
                compatibility=check_compatibility(hardware, other_model),
            )
            for other_model in all_models
        ]
        ranked = rank_models(all_results)

        alternative_model = pick_alternative(ranked, exclude_model_name=model.name)

        if alternative_model is not None:
            alternative_response = _model_to_response(alternative_model)

    return ModelDetailResponse(
        model=_model_to_response(model),
        compatibility=_compatibility_to_response(model, compatibility),
        performance=_performance_to_response(
            predict_performance(model, compatibility)
        ),
        memory_breakdown=MemoryBreakdownResponse(
            weight_memory_bytes=requirement.weight_memory_bytes,
            kv_cache_bytes=requirement.kv_cache_bytes,
            runtime_overhead_bytes=requirement.runtime_overhead_bytes,
            safety_margin_bytes=requirement.safety_margin_bytes,
            total_required_bytes=requirement.total_required_bytes,
        ),
        run_command=run_command_response,
        alternative=alternative_response,
    )


@app.get("/")
def get_index():
    index_path = TEMPLATES_DIR / "index.html"

    if not index_path.is_file():
        raise HTTPException(
            status_code=500,
            detail="Dashboard UI is not installed correctly (index.html missing).",
        )

    return FileResponse(index_path)
