"""
glifo_analise.api.routes.model3d
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Rotas para geração e listagem de modelos 3D (.3mf / .stl).

Endpoints:
    POST /api/model3d/generate → Gera modelo 3D
    GET  /api/model3d/files    → Lista arquivos 3D existentes
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from glifo_analise import config
from glifo_analise.analysis.bitmap import _build_profiles, _collect_mapped_codepoints
from glifo_analise.api.state import AppState, get_state
from glifo_analise.output.model3d import DEFAULT_TACTILE_SEQUENCE, _generate_tactile_3d

router = APIRouter(prefix="/api/model3d", tags=["model3d"])

_3D_EXTENSIONS = {".3mf", ".stl"}


class Model3DRequest(BaseModel):
    """Corpo da requisição de geração de modelo 3D."""

    candidate: Dict[str, Any] = Field(..., description="Dict do candidato (resolution, spacing_mm …)")
    sequence: str = Field(default=DEFAULT_TACTILE_SEQUENCE, description="Sequência ELIS a renderizar")
    fmt: Literal["3mf", "stl"] = Field(default="3mf", description="Formato do modelo 3D")
    full_test: bool = Field(default=False, description="Se True, gera célula com todos os pinos levantados")


def _do_generate(request: Model3DRequest, profiles: list) -> str:
    """Executa `_generate_tactile_3d` em thread separada."""
    out_path = _generate_tactile_3d(
        sequence=request.sequence,
        candidate=request.candidate,
        profiles=profiles,
        fmt=request.fmt,
        full_test=request.full_test,
        out_dir=config.OUTPUT_DIR,
    )
    return out_path.name


@router.post("/generate")
async def generate_model3d(
    request: Model3DRequest,
    state: AppState = Depends(get_state),
) -> Dict[str, Any]:
    """Gera modelo 3D da tira tátil.

    Args:
        request: Candidato, sequência, formato e flag full_test.

    Returns:
        ``{"file": "/output/<nome>.3mf"}``
    """
    with state.lock:
        profiles = list(state.profiles)

    if not profiles:
        codepoints = _collect_mapped_codepoints(config.FONT_PATH)
        profiles = _build_profiles(codepoints, config.FONT_PATH)

    loop = asyncio.get_event_loop()
    try:
        filename = await loop.run_in_executor(None, _do_generate, request, profiles)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"file": f"/output/{filename}"}


@router.get("/files")
async def list_model_files() -> List[str]:
    """Lista todos os arquivos 3D (.3mf e .stl) no diretório de saída.

    Returns:
        Lista de nomes de arquivo (ex: ``["modelo.3mf", "outro.stl"]``).
    """
    if not config.OUTPUT_DIR.exists():
        return []

    return [
        p.name
        for p in sorted(config.OUTPUT_DIR.iterdir())
        if p.suffix.lower() in _3D_EXTENSIONS
    ]
