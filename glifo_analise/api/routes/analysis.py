"""
glifo_analise.api.routes.analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Rotas para execução e monitoramento da análise de resolução.

Endpoints:
    POST /api/analysis/run    → Inicia análise em background (202)
    GET  /api/analysis/status → Retorna status da tarefa
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from glifo_analise import config
from glifo_analise.analysis.bitmap import _build_profiles, _collect_mapped_codepoints
from glifo_analise.analysis.resolution import _analyze_resolution_ext
from glifo_analise.api.state import AppState, get_state
from glifo_analise.api.ws import WebSocketManager, get_ws_manager
from glifo_analise.output.persistence import _save_candidates

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


class AnalysisParams(BaseModel):
    """Parâmetros opcionais para a análise de resolução.

    Todos os campos têm valores padrão extraídos de ``config``.
    """
    pin_spacing_candidates: List[float] = Field(
        default_factory=lambda: list(config.PIN_SPACING_CANDIDATES),
        description="Espaçamentos entre pinos a testar (mm)",
    )
    density_min: float = Field(config.DENSITY_MIN, description="Densidade mínima de pixels (0-1)")
    density_max: float = Field(config.DENSITY_MAX, description="Densidade máxima de pixels (0-1)")
    edge_complexity_min: float = Field(config.EDGE_COMPLEXITY_MIN, description="Complexidade de borda mínima")
    iou_min: float = Field(0.15, description="IoU mínimo em relação ao bitmap de referência")
    max_finger_area_mm: float = Field(config.MAX_FINGER_AREA_MM, description="Tamanho máximo para leitura 1 dedo (mm)")
    max_multi_finger_mm: float = Field(config.MAX_MULTI_FINGER_MM, description="Tamanho máximo para leitura multi-dedo (mm)")
    seq_glyph_min: int = Field(config.SEQ_GLYPH_MIN, description="Capacidade sequencial mínima de glifos")
    min_coverage_pct: float = Field(80.0, description="Cobertura mínima do repertório (%)")


# Resoluções a analisar — lista fixa idêntica ao CLI legado
# (CANDIDATE_RESOLUTIONS + ASYMMETRIC_RESOLUTIONS, sem duplicatas)
def _get_resolutions() -> list[tuple[int, int]]:
    return list(dict.fromkeys(config.CANDIDATE_RESOLUTIONS + config.ASYMMETRIC_RESOLUTIONS))


def _run_analysis(
    state: AppState,
    manager: WebSocketManager,
    loop: asyncio.AbstractEventLoop,
    params: AnalysisParams,
) -> None:
    """Função bloqueante executada em executor.

    Percorre todas as combinações (cols × rows × spacing) e popula state.
    """
    try:
        codepoints = _collect_mapped_codepoints(config.FONT_PATH)
        profiles = _build_profiles(codepoints, config.FONT_PATH)
        spacings = params.pin_spacing_candidates
        resolutions = _get_resolutions()

        combinations = [
            (cols, rows, sp)
            for (cols, rows) in resolutions
            for sp in spacings
        ]
        total = len(combinations)
        extended = []

        for idx, (cols, rows, spacing_mm) in enumerate(combinations):
            pct = round((idx / total) * 100, 1)
            line = f"Analisando grade {cols}×{rows} @ {spacing_mm}mm..."
            manager.broadcast_sync({"line": line, "pct": pct}, loop)

            er = _analyze_resolution_ext(
                cols, rows, spacing_mm, profiles,
                density_min=params.density_min,
                density_max=params.density_max,
                edge_complexity_min=params.edge_complexity_min,
                iou_min=params.iou_min,
                max_finger_area_mm=params.max_finger_area_mm,
                max_multi_finger_mm=params.max_multi_finger_mm,
                seq_glyph_min=params.seq_glyph_min,
            )
            extended.append(er)

        # Critério de viabilidade
        viable = [
            er for er in extended
            if er.reading_mode != "fora-de-alcance"
            and er.seq_in_range
            and er.report.coverage_pct >= params.min_coverage_pct
        ]
        viable.sort(
            key=lambda e: (
                -e.report.coverage_pct,
                -e.seq_capacity,
                -e.spacing_mm,
                e.cell_w_mm * e.cell_h_mm,
            )
        )

        with state.lock:
            state.profiles = profiles
            state.extended_reports = extended
            state.task_status = "done"

        _save_candidates(viable)

        manager.broadcast_sync({"line": "Análise concluída.", "pct": 100.0}, loop)
        manager.broadcast_sync({"type": "done", "viable_count": len(viable)}, loop)

    except Exception as exc:
        with state.lock:
            state.task_status = "error"
            state.task_error = str(exc)
        manager.broadcast_sync({"line": f"ERRO: {exc}", "pct": 0.0, "type": "error"}, loop)


@router.get("/params/defaults")
async def get_params_defaults() -> AnalysisParams:
    """Retorna os valores padrão de todos os parâmetros de análise."""
    return AnalysisParams()


@router.post("/run", status_code=202)
async def run_analysis(
    params: Optional[AnalysisParams] = None,
    state: AppState = Depends(get_state),
    manager: WebSocketManager = Depends(get_ws_manager),
) -> Dict[str, Any]:
    """Inicia a análise completa de resolução em background.

    Returns:
        task_id e status inicial.
    """
    effective_params = params or AnalysisParams()

    with state.lock:
        if state.task_status == "running":
            raise HTTPException(status_code=409, detail="Análise já em execução.")
        state.task_status = "running"
        state.task_id = str(uuid.uuid4())
        state.task_error = None
        task_id = state.task_id

    loop = asyncio.get_event_loop()
    asyncio.get_event_loop().run_in_executor(
        None, _run_analysis, state, manager, loop, effective_params
    )

    return {"task_id": task_id, "status": "running"}


@router.get("/status")
async def analysis_status(state: AppState = Depends(get_state)) -> Dict[str, Any]:
    """Retorna o status atual da tarefa de análise.

    Returns:
        status: idle | running | done | error
    """
    with state.lock:
        return {
            "status": state.task_status,
            "task_id": state.task_id,
            "error": state.task_error,
        }
