"""
glifo_analise.api.routes.files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Servir arquivos estáticos do diretório de saída (output/).

Endpoints:
    GET /output/{filename} → Serve o arquivo ou 404
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from glifo_analise import config

router = APIRouter(tags=["files"])


@router.get("/output/{filename}")
async def serve_output_file(filename: str) -> FileResponse:
    """Serve um arquivo gerado (PNG, 3MF, STL) do diretório de saída.

    Args:
        filename: Nome do arquivo, sem barra ou subpasta.

    Returns:
        Resposta com o arquivo ou 404 se não existir.

    Raises:
        HTTPException 404: Arquivo não encontrado.
        HTTPException 400: Tentativa de path traversal.
    """
    # Proteção básica contra path traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido.")

    path = config.OUTPUT_DIR / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"Arquivo '{filename}' não encontrado.")

    return FileResponse(str(path))
