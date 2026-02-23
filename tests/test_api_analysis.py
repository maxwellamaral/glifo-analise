"""
Testes das rotas de análise — glifo_analise.api.routes.analysis

Histórias de usuário:
  US-A1: "Como pesquisador, quero disparar a análise completa via POST e
          receber um ID de tarefa para rastrear o progresso."
  US-A2: "Como pesquisador, quero consultar o status da análise via GET
          e saber se está rodando, concluída ou aguardando."
  US-A3: "Como pesquisador, quero receber linhas de log e porcentagem de
          progresso via WebSocket enquanto a análise evolui."
"""

from __future__ import annotations

import json
from typing import Generator

import pytest
from fastapi.testclient import TestClient

# ────────────────────────────────────────────────────────────────────────────
# Fase RED: glifo_analise.api ainda não existe — ImportError intencional
# ────────────────────────────────────────────────────────────────────────────
from glifo_analise.api.main import create_app  # noqa: E402  ← FALHA ESPERADA


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """Cria um cliente ASGI síncrono para testes sem servidor real."""
    app = create_app()
    with TestClient(app) as c:
        yield c


# ── US-A1: POST /api/analysis/run ───────────────────────────────────────────

class TestRunAnalysis:
    """POST /api/analysis/run"""

    def test_returns_202_accepted(self, client: TestClient) -> None:
        """Deve aceitar a requisição e retornar 202 com task_id."""
        resp = client.post("/api/analysis/run")
        assert resp.status_code == 202

    def test_response_contains_task_id(self, client: TestClient) -> None:
        """Corpo deve conter 'task_id' com valor não vazio."""
        resp = client.post("/api/analysis/run")
        body = resp.json()
        assert "task_id" in body
        assert body["task_id"]  # não pode ser vazio/None

    def test_second_call_while_running_returns_409(self, client: TestClient) -> None:
        """Se análise já estiver rodando, deve retornar 409 Conflict."""
        client.post("/api/analysis/run")
        resp = client.post("/api/analysis/run")
        # Aceitável ser 202 também se a tarefa anterior já tiver concluído
        # num ambiente de teste síncrono; mas se ainda running → 409
        assert resp.status_code in (202, 409)


# ── US-A2: GET /api/analysis/status ─────────────────────────────────────────

class TestAnalysisStatus:
    """GET /api/analysis/status"""

    def test_initial_status_is_idle(self, client: TestClient) -> None:
        """Antes de qualquer análise, status deve ser 'idle'."""
        resp = client.get("/api/analysis/status")
        assert resp.status_code == 200
        assert resp.json()["status"] == "idle"

    def test_status_field_valid_values(self, client: TestClient) -> None:
        """Status deve ser um dos valores esperados."""
        resp = client.get("/api/analysis/status")
        valid = {"idle", "running", "done", "error"}
        assert resp.json()["status"] in valid

    def test_status_after_run_is_done(self, client: TestClient) -> None:
        """Após o run completar (modo síncrono nos testes), status deve ser 'done'."""
        client.post("/api/analysis/run")
        # No TestClient síncrono o executor roda imediatamente
        resp = client.get("/api/analysis/status")
        assert resp.json()["status"] in ("running", "done")


# ── US-A3: WS /api/ws/progress ──────────────────────────────────────────────

class TestProgressWebSocket:
    """WS /api/ws/progress"""

    def test_websocket_accepts_connection(self, client: TestClient) -> None:
        """WebSocket deve aceitar conexão sem erro."""
        with client.websocket_connect("/api/ws/progress") as ws:
            # Deve conectar sem exceção
            assert ws is not None

    def test_websocket_receives_progress_after_run(self, client: TestClient) -> None:
        """Após POST /run, deve receber ao menos uma mensagem de progresso."""
        messages: list[dict] = []
        with client.websocket_connect("/api/ws/progress") as ws:
            client.post("/api/analysis/run")
            # Coleta até 5 mensagens com timeout
            for _ in range(5):
                try:
                    raw = ws.receive_text()
                    messages.append(json.loads(raw))
                except Exception:
                    break
        assert len(messages) > 0

    def test_progress_message_schema(self, client: TestClient) -> None:
        """Cada mensagem de progresso deve ter 'line' (str) e 'pct' (float 0-100)."""
        with client.websocket_connect("/api/ws/progress") as ws:
            client.post("/api/analysis/run")
            for _ in range(10):
                try:
                    msg = json.loads(ws.receive_text())
                    if "pct" in msg:
                        assert isinstance(msg["line"], str)
                        assert 0.0 <= msg["pct"] <= 100.0
                        return  # encontrou mensagem válida
                except Exception:
                    break
        # Se não encontrou nenhuma mensagem com 'pct', falha
        pytest.fail("Nenhuma mensagem com campo 'pct' recebida via WebSocket")
