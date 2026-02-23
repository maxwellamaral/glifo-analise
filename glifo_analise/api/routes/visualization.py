"""
glifo_analise.api.routes.visualization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Rotas para geração de previews PNG (tira, células individuais, grade).

Endpoints:
    POST /api/visualization/generate → Gera preview conforme tipo solicitado
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Literal

from fastapi import APIRouter, Depends, HTTPException
from PIL import ImageFont
from pydantic import BaseModel, Field

from glifo_analise import config
from glifo_analise.analysis.bitmap import (
    _collect_mapped_codepoints,
    _build_profiles,
    _effective_resolution,
    _render_bitmap,
)
from glifo_analise.api.state import AppState, get_state
from glifo_analise.output.grid import _save_grid
from glifo_analise.output.preview import (
    _generate_tactile_preview_png,
    _generate_tactile_preview_png_full,
)

router = APIRouter(prefix="/api/visualization", tags=["visualization"])


class VisGenRequest(BaseModel):
    """Corpo da requisição de geração de visualização."""

    type: Literal["strip", "cells", "grid"] = Field(
        ..., description="Tipo: strip=tira completa, cells=por glifo, grid=grade"
    )
    candidate: Dict[str, Any] = Field(..., description="Dict do candidato")
    sequence: str = Field(default=config.DEFAULT_TACTILE_SEQUENCE)


def _build_bitmaps_for_sequence(
    sequence: str,
    resolution: tuple,  # (cols, rows)
) -> List:
    """Renderiza bitmaps de cada char da sequência no tamanho da célula."""
    cols, rows = resolution
    font = ImageFont.truetype(str(config.FONT_PATH), rows - 2)
    return [_render_bitmap(ch, font, (cols, rows)) for ch in sequence]


def _gen_strip(request: VisGenRequest) -> Dict[str, Any]:
    """Gera preview PNG da tira completa (multi-glifo)."""
    resolution = tuple(request.candidate["resolution"])
    cols, rows = resolution
    spacing_mm: float = request.candidate["spacing_mm"]

    bitmaps = _build_bitmaps_for_sequence(request.sequence, (cols, rows))
    if not bitmaps:
        raise HTTPException(status_code=400, detail="Sequência vazia.")

    out_path = _generate_tactile_preview_png_full(
        bitmaps=bitmaps,
        candidate=request.candidate,
        render_shape=(rows, cols),
        reading_mode=request.candidate.get("reading_mode", "1-dedo"),
        full_test=False,
        fname_stem=f"api_strip_{cols}x{rows}_{spacing_mm}mm",
        out_dir=config.OUTPUT_DIR,
        sequence=request.sequence,
    )
    return {"file": f"/output/{out_path.name}"}


def _gen_cells(request: VisGenRequest) -> Dict[str, Any]:
    """Gera preview PNGs individuais por glifo da sequência."""
    resolution = tuple(request.candidate["resolution"])
    cols, rows = resolution
    spacing_mm: float = request.candidate["spacing_mm"]

    font = ImageFont.truetype(str(config.FONT_PATH), rows - 2)
    files: List[str] = []

    for char in request.sequence:
        bitmap = _render_bitmap(char, font, (cols, rows))
        out_path = _generate_tactile_preview_png(
            bitmap=bitmap,
            candidate=request.candidate,
            out_dir=config.OUTPUT_DIR,
            label=f"U{ord(char):04X}",
        )
        files.append(f"/output/{out_path.name}")

    return {"files": files}


def _gen_grid(request: VisGenRequest, state: AppState) -> Dict[str, Any]:
    """Gera grade visual PNG de diagnóstico."""
    if not state.extended_reports:
        raise HTTPException(
            status_code=400, detail="Nenhuma análise disponível. Execute /api/analysis/run primeiro."
        )

    profiles = state.profiles
    if not profiles:
        codepoints = _collect_mapped_codepoints(config.FONT_PATH)
        profiles = _build_profiles(codepoints, config.FONT_PATH)

    spacing_mm: float = request.candidate["spacing_mm"]
    cols, rows = tuple(request.candidate["resolution"])

    matching = [
        er for er in state.extended_reports
        if er.resolution[0] == cols and er.resolution[1] == rows and er.spacing_mm == spacing_mm
    ]
    if not matching:
        raise HTTPException(status_code=404, detail="Candidato não encontrado nos relatórios.")

    er = matching[0]
    out_path = _save_grid(
        report=er.report,
        profiles=profiles,
        spacing_mm=spacing_mm,
        out_dir=config.OUTPUT_DIR,
    )
    return {"file": f"/output/{out_path.name}"}


@router.post("/generate")
async def generate_visualization(
    request: VisGenRequest,
    state: AppState = Depends(get_state),
) -> Dict[str, Any]:
    """Gera visualização PNG do tipo solicitado.

    Returns:
        Para strip/grid: ``{"file": "/output/...png"}``
        Para cells: ``{"files": ["/output/...png", ...]}``
    """
    loop = asyncio.get_event_loop()

    if request.type == "strip":
        return await loop.run_in_executor(None, _gen_strip, request)
    elif request.type == "cells":
        return await loop.run_in_executor(None, _gen_cells, request)
    else:  # "grid"
        if not state.extended_reports:
            raise HTTPException(
                status_code=400,
                detail="Nenhuma análise disponível. Execute /api/analysis/run primeiro.",
            )
        return await loop.run_in_executor(None, _gen_grid, request, state)

