"""
glifo_analise.api.main
~~~~~~~~~~~~~~~~~~~~~~~
Fábrica da aplicação FastAPI e ponto de entrada do servidor.

Uso:
    uv run glifo-gui          # via entry point configurado no pyproject.toml
    uv run python -m glifo_analise.api.main  # direto
"""

from __future__ import annotations

import pathlib

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from glifo_analise.api.routes.analysis import router as analysis_router
from glifo_analise.api.routes.candidates import router as candidates_router
from glifo_analise.api.routes.files import router as files_router
from glifo_analise.api.routes.model3d import router as model3d_router
from glifo_analise.api.routes.visualization import router as visualization_router
from glifo_analise.api.state import get_state
from glifo_analise.api.ws import ws_manager


async def _ws_progress_endpoint(websocket: WebSocket) -> None:
    """Endpoint WebSocket que transmite progresso da análise em tempo real."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Mantém a conexão viva; cliente pode enviar pings arbitrários
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception:
        await ws_manager.disconnect(websocket)


def create_app() -> FastAPI:
    """Cria e configura a aplicação FastAPI.

    Returns:
        Instância configurada de FastAPI pronta para ser servida.
    """
    # Garante estado limpo a cada criação (importante nos testes)
    get_state().reset()

    app = FastAPI(
        title="ELIS Glifo Analyser API",
        description="Backend REST + WebSocket para análise e geração de glifos táteis ELIS.",
        version="1.0.0",
    )

    # ── Rotas REST ────────────────────────────────────────────────────────────
    app.include_router(analysis_router)
    app.include_router(candidates_router)
    app.include_router(visualization_router)
    app.include_router(model3d_router)
    app.include_router(files_router)

    # ── WebSocket ─────────────────────────────────────────────────────────────
    app.add_websocket_route("/api/ws/progress", _ws_progress_endpoint)

    # ── SPA (Vue 3 / Vite dist) — montada por último ─────────────────────────
    dist = pathlib.Path(__file__).parents[2] / "frontend" / "dist"
    if dist.exists():
        app.mount("/", StaticFiles(directory=str(dist), html=True), name="spa")

    return app


def run() -> None:
    """Inicia o servidor uvicorn. Entry point: ``glifo-gui``."""
    uvicorn.run(
        create_app(),
        host="0.0.0.0",
        port=8080,
        log_level="info",
    )


if __name__ == "__main__":
    run()
