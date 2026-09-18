import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from canirunllm.application.scanner_service import ScannerService
from canirunllm.backends.interface import DownloadStatus, ModelNotDownloadableError
from canirunllm.backends.llama_cpp import LlamaCppBackend
from canirunllm.backends.manager import BackendManager
from canirunllm.backends.ollama import OllamaBackend
from canirunllm.backends.state import RunningModel, runtime_state
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
    build_run_commands,
    pick_best_for_you,
    pick_alternative,
)

from canirunllm.api.schemas import (
    CPUResponse,
    MemoryResponse,
    GPUResponse,
    OSResponse,
    DiskResponse,
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
    ChatRequest,
    ChatResponse,
    RuntimeStatusResponse,
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
_ollama_backend = OllamaBackend()
_llama_cpp_backend = LlamaCppBackend()
_backend_manager = BackendManager([_ollama_backend, _llama_cpp_backend])


def _hardware_to_response(hardware: HardwareProfile) -> HardwareResponse:
    return HardwareResponse(
        cpu=CPUResponse(**asdict(hardware.cpu)),
        memory=MemoryResponse(**asdict(hardware.memory)),
        os=OSResponse(**asdict(hardware.os)),
        gpus=[GPUResponse(**asdict(gpu)) for gpu in hardware.gpus],
        disk=(
            DiskResponse(**asdict(hardware.disk))
            if hardware.disk is not None
            else None
        ),
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

    run_commands_response = [
        RunCommandResponse(
            runtime=info.runtime,
            command=info.command,
            note=info.note,
        )
        for info in build_run_commands(model)
    ]

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
        run_commands=run_commands_response,
        alternative=alternative_response,
        ollama_downloadable=_ollama_backend.supports(model),
        llama_cpp_downloadable=_llama_cpp_backend.supports(model),
        ollama_available=_ollama_backend.is_available(),
        llama_cpp_available=_llama_cpp_backend.is_available(),
    )


@app.post("/api/models/{model_id}/download")
def download_and_run_model(model_id: str, backend: str | None = None):
    """Streams newline-delimited JSON progress events while downloading
    `model_id` through a backend, then marks it as the running model.

    `backend` selects "ollama" or "llama.cpp" explicitly; if omitted,
    picks whichever supports this model and is available (Ollama
    first, since it needs no separate binary install)."""

    model = _service.resolver.get_variant(model_id)

    if model is None:
        raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")

    candidates = _backend_manager.supporting_backends(model)

    if not candidates:
        raise HTTPException(
            status_code=400,
            detail=f"{model_id} has no verified download source on any backend yet.",
        )

    if backend is not None:
        candidates = [b for b in candidates if b.name == backend]
        if not candidates:
            raise HTTPException(status_code=400, detail=f"{model_id} doesn't support backend '{backend}'.")

    chosen = next((b for b in candidates if b.is_available()), None)

    if chosen is None:
        raise HTTPException(
            status_code=503,
            detail=f"{candidates[0].name} isn't available right now (not installed/running?).",
        )

    def event_stream():
        try:
            for progress in chosen.download(model):
                yield json.dumps({
                    "status": progress.status.value,
                    "bytes_downloaded": progress.bytes_downloaded,
                    "total_bytes": progress.total_bytes,
                    "message": progress.message,
                }) + "\n"

            endpoint_url = chosen.serve(model)
            runtime_state.set(RunningModel(
                model_name=model.name,
                backend_name=chosen.name,
                endpoint_url=endpoint_url,
            ))

            yield json.dumps({
                "status": "RUNNING",
                "bytes_downloaded": 0,
                "total_bytes": None,
                "message": f"{model.name} is ready.",
            }) + "\n"
        except Exception as exc:
            yield json.dumps({
                "status": DownloadStatus.FAILED.value,
                "bytes_downloaded": 0,
                "total_bytes": None,
                "message": str(exc),
            }) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


@app.post("/api/runtime/stop")
def stop_runtime():
    running = runtime_state.get()

    if running is None:
        return {"stopped": False}

    for backend in _backend_manager.backends:
        if backend.name == running.backend_name:
            backend.stop()
            break

    runtime_state.clear()
    return {"stopped": True}


@app.get("/api/runtime/status", response_model=RuntimeStatusResponse)
def get_runtime_status():
    running = runtime_state.get()

    if running is None:
        return RuntimeStatusResponse(
            running=False,
            model_name=None,
            backend_name=None,
            endpoint_url=None,
        )

    return RuntimeStatusResponse(
        running=True,
        model_name=running.model_name,
        backend_name=running.backend_name,
        endpoint_url=running.endpoint_url,
    )


@app.post("/api/chat", response_model=ChatResponse)
def post_chat(request: ChatRequest):
    """Routes to whichever model is actually running (Phase 1: Ollama
    only). If nothing matching is running, returns an honest
    explanation instead of a fabricated-looking reply."""

    running = runtime_state.get()

    if running is not None and running.model_name == request.model_name:

        backend = next(
            (b for b in _backend_manager.available_backends() if b.name == running.backend_name),
            None,
        )
        model = _service.resolver.get_variant(request.model_name)

        if backend is not None and model is not None:
            try:
                return ChatResponse(reply=backend.chat(model, request.message))
            except Exception as exc:
                return ChatResponse(
                    reply=f"{model.name} is running, but didn't respond: {exc}"
                )

    if not _backend_manager.available_backends():
        return ChatResponse(
            reply=(
                "No model runtime is available right now (e.g. Ollama "
                "isn't installed/running). This is a placeholder response."
            )
        )

    return ChatResponse(
        reply=(
            f"'{request.model_name}' isn't running yet - use "
            "\"Download & Run\" on this model first."
        )
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
