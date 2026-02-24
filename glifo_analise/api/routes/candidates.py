"""
glifo_analise.api.routes.candidates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Rotas para leitura dos candidatos viáveis persistidos.

Endpoints:
    GET /api/candidates → Lista candidatos do arquivo JSON
    GET /api/candidates/detail/{rank} → Detalhe enriquecido de um candidato
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from glifo_analise import config
from glifo_analise.analysis.iso import candidate_detail_from_dict

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


@router.get("/candidates/detail/{rank}", response_model=Dict[str, Any])
async def candidate_detail(rank: int) -> Dict[str, Any]:
    """Retorna dados detalhados enriquecidos de um candidato específico.

    Inclui: conformidade ISO 11548-2, métricas derivadas (gap, razão,
    área de célula), análise de cobertura por tier, ranking econômico
    e notas de fabricação para dispositivo tátil dinâmico.

    Args:
        rank: Número de ordem do candidato (1-based).

    Returns:
        Dict enriquecido com todos os campos derivados.

    Raises:
        HTTPException 404: se o candidato não existir.
    """
    path = config.CANDIDATES_FILE
    if not path.exists():
        raise HTTPException(status_code=404, detail="Arquivo de candidatos não encontrado.")
    try:
        all_items: List[Dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao ler candidatos: {exc}") from exc

    candidate = next((c for c in all_items if c.get("rank") == rank), None)
    if candidate is None:
        raise HTTPException(status_code=404, detail=f"Candidato #{rank} não encontrado.")

    return candidate_detail_from_dict(candidate, all_items)
