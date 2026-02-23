"""
glifo_analise.api.routes.candidates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Rotas para leitura dos candidatos viáveis persistidos.

Endpoints:
    GET /api/candidates → Lista candidatos do arquivo JSON
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from fastapi import APIRouter

from glifo_analise import config

router = APIRouter(prefix="/api", tags=["candidates"])


@router.get("/candidates", response_model=List[Dict[str, Any]])
async def list_candidates() -> List[Dict[str, Any]]:
    """Retorna a lista de candidatos viáveis persistida em disco.

    Lê diretamente de ``config.CANDIDATES_FILE`` para suportar
    substituição por monkeypatching em testes.

    Returns:
        Lista de dicts com os campos: rank, resolution, spacing_mm,
        coverage_pct, reading_mode, seq_capacity e iso_criteria.
    """
    path = config.CANDIDATES_FILE
    if not path.exists():
        return []
    try:
        items: List[Dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

    # Garante iso_criteria em cada item (pode ser vazio se análise não disponível)
    for item in items:
        item.setdefault("iso_criteria", [])

    return items
