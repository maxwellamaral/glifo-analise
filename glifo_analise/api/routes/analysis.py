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
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from glifo_analise import config
from glifo_analise.analysis.bitmap import _build_profiles, _collect_mapped_codepoints
from glifo_analise.analysis.resolution import _analyze_resolution_ext
from glifo_analise.api.state import AppState, get_state
from glifo_analise.api.ws import WebSocketManager, get_ws_manager
from glifo_analise.output.persistence import _save_candidates

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

# Resoluções a analisar — lista fixa idêntica ao CLI legado
# (CANDIDATE_RESOLUTIONS + ASYMMETRIC_RESOLUTIONS, sem duplicatas)
def _get_resolutions() -> list[tuple[int, int]]:
    return list(dict.fromkeys(config.CANDIDATE_RESOLUTIONS + config.ASYMMETRIC_RESOLUTIONS))


def _run_analysis(state: AppState, manager: WebSocketManager, loop: asyncio.AbstractEventLoop) -> None:
    """Função bloqueante executada em executor.

    Percorre todas as combinações (cols × rows × spacing) e popula state.
    """
    try:
        codepoints = _collect_mapped_codepoints(config.FONT_PATH)
        profiles = _build_profiles(codepoints, config.FONT_PATH)
        spacings = config.PIN_SPACING_CANDIDATES
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

            er = _analyze_resolution_ext(cols, rows, spacing_mm, profiles)
            extended.append(er)

        # Critério de viabilidade idêntico ao CLI
        viable = [
            er for er in extended
            if er.reading_mode != "fora-de-alcance"
            and er.seq_in_range
            and er.report.coverage_pct >= 80.0
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


@router.post("/run", status_code=202)
async def run_analysis(
    state: AppState = Depends(get_state),
    manager: WebSocketManager = Depends(get_ws_manager),
) -> Dict[str, Any]:
    """Inicia a análise completa de resolução em background.

    Returns:
        task_id e status inicial.
    """
    with state.lock:
        if state.task_status == "running":
            raise HTTPException(status_code=409, detail="Análise já em execução.")
        state.task_status = "running"
        state.task_id = str(uuid.uuid4())
        state.task_error = None
        task_id = state.task_id

    loop = asyncio.get_event_loop()
    asyncio.get_event_loop().run_in_executor(
        None, _run_analysis, state, manager, loop
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
