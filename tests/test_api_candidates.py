"""
Testes das rotas de candidatos — glifo_analise.api.routes.candidates

Histórias de usuário:
  US-C1: "Como pesquisador, quero listar os candidatos viáveis via GET e
          receber os campos essenciais para decisão."
  US-C2: "Como pesquisador, quero que cada candidato traga os critérios ISO
          avaliados para conhecer pontos de atenção."
  US-C3: "Como pesquisador, se não houver análise salva, quero receber lista
          vazia sem erro."
"""

from __future__ import annotations

import json
import pathlib
import shutil
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from glifo_analise.api.main import create_app  # noqa: E402  ← FALHA ESPERADA
from glifo_analise import config


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def candidates_json(tmp_path: pathlib.Path) -> Generator[None, None, None]:
    """Instala um JSON de candidatos fictício e restaura estado após o teste."""
    sample = [
        {
            "rank": 1,
            "resolution": [13, 13],
            "spacing_mm": 2.5,
            "coverage_pct": 100.0,
            "reading_mode": "1-dedo",
            "seq_capacity": 5,
            "cell_w_mm": 30.0,
            "cell_h_mm": 30.0,
            "seq_in_range": True,
        }
    ]
    original = config.CANDIDATES_FILE
    fake_file = tmp_path / "candidatos_viaveis.json"
    fake_file.write_text(json.dumps(sample), encoding="utf-8")
    # Monkey-patch o caminho que a rota usa
    config.CANDIDATES_FILE = fake_file  # type: ignore[assignment]
    yield
    config.CANDIDATES_FILE = original  # type: ignore[assignment]


# ── US-C3: lista vazia quando não há arquivo ─────────────────────────────────

class TestCandidatesEmpty:
    """GET /api/candidates sem arquivo de candidatos."""

    def test_returns_empty_list_when_no_file(
        self,
        client: TestClient,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Deve retornar [] quando candidatos_viaveis.json não existe."""
        monkeypatch.setattr(config, "CANDIDATES_FILE", tmp_path / "nao_existe.json")
        resp = client.get("/api/candidates")
        assert resp.status_code == 200
        assert resp.json() == []


# ── US-C1: lista com candidatos ──────────────────────────────────────────────

class TestCandidatesList:
    """GET /api/candidates com arquivo presente."""

    def test_returns_200(self, client: TestClient, candidates_json: None) -> None:
        resp = client.get("/api/candidates")
        assert resp.status_code == 200

    def test_returns_list(self, client: TestClient, candidates_json: None) -> None:
        body = client.get("/api/candidates").json()
        assert isinstance(body, list)
        assert len(body) >= 1

    def test_required_fields_present(
        self, client: TestClient, candidates_json: None
    ) -> None:
        """Cada item deve ter: rank, resolution, spacing_mm, coverage_pct, reading_mode, seq_capacity."""
        required = {"rank", "resolution", "spacing_mm", "coverage_pct", "reading_mode", "seq_capacity"}
        item = client.get("/api/candidates").json()[0]
        missing = required - item.keys()
        assert not missing, f"Campos ausentes: {missing}"

    def test_resolution_is_list_of_two_ints(
        self, client: TestClient, candidates_json: None
    ) -> None:
        item = client.get("/api/candidates").json()[0]
        res = item["resolution"]
        assert isinstance(res, list) and len(res) == 2
        assert all(isinstance(v, int) for v in res)

    def test_coverage_pct_in_range(
        self, client: TestClient, candidates_json: None
    ) -> None:
        item = client.get("/api/candidates").json()[0]
        assert 0.0 <= item["coverage_pct"] <= 100.0

    def test_reading_mode_valid(
        self, client: TestClient, candidates_json: None
    ) -> None:
        valid = {"1-dedo", "multi-dedo", "fora-de-alcance"}
        item = client.get("/api/candidates").json()[0]
        assert item["reading_mode"] in valid


# ── US-C2: critérios ISO embutidos ───────────────────────────────────────────

class TestCandidatesIso:
    """Critérios ISO devem aparecer em cada candidato quando relatórios disponíveis."""

    def test_iso_criteria_field_present(
        self, client: TestClient, candidates_json: None
    ) -> None:
        """Cada item deve ter 'iso_criteria': lista de dicts com criterion/passed/detail."""
        item = client.get("/api/candidates").json()[0]
        assert "iso_criteria" in item, "Campo 'iso_criteria' ausente"

    def test_iso_criteria_is_list(
        self, client: TestClient, candidates_json: None
    ) -> None:
        item = client.get("/api/candidates").json()[0]
        assert isinstance(item["iso_criteria"], list)

    def test_iso_criteria_item_schema(
        self, client: TestClient, candidates_json: None
    ) -> None:
        item = client.get("/api/candidates").json()[0]
        criteria = item["iso_criteria"]
        if criteria:  # podem ser [] se sem análise
            c = criteria[0]
            assert "criterion" in c
            assert "passed" in c
            assert "detail" in c
            assert isinstance(c["passed"], bool)
