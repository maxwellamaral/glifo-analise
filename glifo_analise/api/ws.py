"""
glifo_analise.api.ws
~~~~~~~~~~~~~~~~~~~~
WebSocket manager para broadcast de progresso em tempo real.

Uso:
    manager = WebSocketManager()

    # No endpoint WebSocket:
    await manager.connect(websocket)

    # De qualquer corrotina ou thread (via asyncio.run_coroutine_threadsafe):
    await manager.broadcast({"line": "texto", "pct": 42.0})
"""

from __future__ import annotations

import asyncio
import json
from typing import Dict, List

from fastapi import WebSocket


class WebSocketManager:
    """Gerencia conexões WebSocket activas e transmite mensagens a todos."""

    def __init__(self) -> None:
        self._connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Aceita e registra nova conexão WebSocket."""
        await websocket.accept()
        async with self._lock:
            self._connections.append(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove conexão encerrada."""
        async with self._lock:
            try:
                self._connections.remove(websocket)
            except ValueError:
                pass

    async def broadcast(self, message: Dict) -> None:
        """Envia message (serializado como JSON) a todos os clientes conectados."""
        text = json.dumps(message, ensure_ascii=False)
        dead: List[WebSocket] = []
        async with self._lock:
            for ws in list(self._connections):
                try:
                    await ws.send_text(text)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                try:
                    self._connections.remove(ws)
                except ValueError:
                    pass

    def broadcast_sync(self, message: Dict, loop: asyncio.AbstractEventLoop) -> None:
        """Versão thread-safe para chamar de dentro de um executor.

        Args:
            message: Dicionário a serializar como JSON.
            loop: Event loop do servidor (obtido via asyncio.get_event_loop()).
        """
        future = asyncio.run_coroutine_threadsafe(self.broadcast(message), loop)
        try:
            future.result(timeout=5.0)
        except Exception:
            pass  # Não bloqueia a análise se o WS falhar

    @property
    def active_count(self) -> int:
        """Número de conexões activas."""
        return len(self._connections)


# Instância singleton
ws_manager = WebSocketManager()


def get_ws_manager() -> WebSocketManager:
    """FastAPI dependency: retorna o singleton WebSocketManager."""
    return ws_manager
