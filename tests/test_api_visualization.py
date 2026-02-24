"""
Testes das rotas de visualização — glifo_analise.api.routes.visualization

Histórias de usuário:
  US-V1: "Como pesquisador, quero gerar uma tira completa (PNG único com todos
          os glifos enfileirados) a partir de um candidato e uma sequência."
  US-V2: "Como pesquisador, quero gerar células individuais (um PNG por glifo)
          para comparar cada símbolo separadamente."
  US-V3: "Como pesquisador, quero gerar uma grade diagnóstica para inspecionar
          todos os glifos da resolução em uma única imagem."
  US-V4: "Como pesquisador, se solicitar grade diagnóstica sem análise prévia,
          quero receber um erro claro (400), não um crash."
"""

from __future__ import annotations

import json
import pathlib
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from glifo_analise.api.main import create_app  # noqa: E402  ← FALHA ESPERADA
from glifo_analise import config


# ── Candidato de referência para os testes ───────────────────────────────────
SAMPLE_CANDIDATE = {
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
SAMPLE_SEQUENCE = "tqlDà"


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def _redirect_output(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redireciona OUTPUT_DIR para tmp_path para não poluir output/ real."""
    monkeypatch.setattr(config, "OUTPUT_DIR", tmp_path)


# ── US-V1: tipo "strip" ───────────────────────────────────────────────────────

class TestGenerateStrip:
    """POST /api/visualization/generate — tipo 'strip'"""

    def test_returns_200(self, client: TestClient) -> None:
        resp = client.post(
            "/api/visualization/generate",
            json={"type": "strip", "candidate": SAMPLE_CANDIDATE, "sequence": SAMPLE_SEQUENCE},
        )
        assert resp.status_code == 200

    def test_response_has_file_field(self, client: TestClient) -> None:
        body = client.post(
            "/api/visualization/generate",
            json={"type": "strip", "candidate": SAMPLE_CANDIDATE, "sequence": SAMPLE_SEQUENCE},
        ).json()
        assert "file" in body
        assert body["file"].endswith(".png")

    def test_file_url_starts_with_output(self, client: TestClient) -> None:
        body = client.post(
            "/api/visualization/generate",
            json={"type": "strip", "candidate": SAMPLE_CANDIDATE, "sequence": SAMPLE_SEQUENCE},
        ).json()
        assert body["file"].startswith("/output/")

    def test_generated_file_exists_on_disk(
        self, client: TestClient, tmp_path: pathlib.Path
    ) -> None:
        body = client.post(
            "/api/visualization/generate",
            json={"type": "strip", "candidate": SAMPLE_CANDIDATE, "sequence": SAMPLE_SEQUENCE},
        ).json()
        fname = pathlib.Path(body["file"]).name
        assert (tmp_path / fname).exists()


# ── US-V2: tipo "cells" ───────────────────────────────────────────────────────

class TestGenerateCells:
    """POST /api/visualization/generate — tipo 'cells'"""

    def test_returns_200(self, client: TestClient) -> None:
        resp = client.post(
            "/api/visualization/generate",
            json={"type": "cells", "candidate": SAMPLE_CANDIDATE, "sequence": SAMPLE_SEQUENCE},
        )
        assert resp.status_code == 200

    def test_response_has_files_list(self, client: TestClient) -> None:
        body = client.post(
            "/api/visualization/generate",
            json={"type": "cells", "candidate": SAMPLE_CANDIDATE, "sequence": SAMPLE_SEQUENCE},
        ).json()
        assert "files" in body
        assert isinstance(body["files"], list)

    def test_files_count_matches_sequence_length(self, client: TestClient) -> None:
        seq = "tqlDà"
        body = client.post(
            "/api/visualization/generate",
            json={"type": "cells", "candidate": SAMPLE_CANDIDATE, "sequence": seq},
        ).json()
        assert len(body["files"]) == len(seq)

    def test_all_files_are_png(self, client: TestClient) -> None:
        body = client.post(
            "/api/visualization/generate",
            json={"type": "cells", "candidate": SAMPLE_CANDIDATE, "sequence": SAMPLE_SEQUENCE},
        ).json()
        assert all(f.endswith(".png") for f in body["files"])


# ── US-V3 e US-V4: tipo "grid" ────────────────────────────────────────────────

class TestGenerateGrid:
    """POST /api/visualization/generate — tipo 'grid'"""

    def test_returns_200_and_generates_grid_without_analysis(self, client: TestClient) -> None:
        """Sem análise prévia, a rota re-analisa internamente e retorna 200 com 'file'."""
        resp = client.post(
            "/api/visualization/generate",
            json={"type": "grid", "candidate": SAMPLE_CANDIDATE, "sequence": ""},
        )
        assert resp.status_code == 200
        assert "file" in resp.json()

    def test_grid_file_is_png(self, client: TestClient) -> None:
        resp = client.post(
            "/api/visualization/generate",
            json={"type": "grid", "candidate": SAMPLE_CANDIDATE, "sequence": ""},
        )
        body = resp.json()
        assert body["file"].endswith(".png")


# ── Validação de payload ──────────────────────────────────────────────────────

class TestGenerateValidation:
    """Validação de entrada da rota POST /api/visualization/generate"""

    def test_missing_type_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/api/visualization/generate",
            json={"candidate": SAMPLE_CANDIDATE, "sequence": SAMPLE_SEQUENCE},
        )
        assert resp.status_code == 422

    def test_invalid_type_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/api/visualization/generate",
            json={"type": "invalido", "candidate": SAMPLE_CANDIDATE, "sequence": SAMPLE_SEQUENCE},
        )
        assert resp.status_code == 422

    def test_missing_candidate_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/api/visualization/generate",
            json={"type": "strip", "sequence": SAMPLE_SEQUENCE},
        )
        assert resp.status_code == 422
