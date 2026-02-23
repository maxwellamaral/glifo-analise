"""
Testes das rotas de modelo 3D — glifo_analise.api.routes.model3d

Histórias de usuário:
  US-M1: "Como pesquisador, quero disparar a geração de um modelo 3D via POST
          e receber confirmação imediata enquanto o processamento ocorre em background."
  US-M2: "Como pesquisador, quero listar os arquivos 3D já gerados (STL/3MF)
          para escolher qual visualizar ou baixar."
  US-M3: "Como pesquisador, quero baixar um arquivo 3D específico via GET e
          receber o binário correto para impressão."
  US-M4: "Como pesquisador, ao solicitar um arquivo inexistente, quero receber
          404 com mensagem clara."
"""

from __future__ import annotations

import pathlib
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from glifo_analise.api.main import create_app  # noqa: E402  ← FALHA ESPERADA
from glifo_analise import config


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


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def _redirect_output(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "OUTPUT_DIR", tmp_path)


# ── US-M1: POST /api/model3d/generate ────────────────────────────────────────

class TestGenerateModel3D:
    """POST /api/model3d/generate"""

    def test_returns_200(self, client: TestClient) -> None:
        resp = client.post(
            "/api/model3d/generate",
            json={
                "candidate": SAMPLE_CANDIDATE,
                "sequence": "tqlDà",
                "fmt": "3mf",
                "full_test": False,
            },
        )
        assert resp.status_code == 200

    def test_response_has_file_field(self, client: TestClient) -> None:
        body = client.post(
            "/api/model3d/generate",
            json={
                "candidate": SAMPLE_CANDIDATE,
                "sequence": "tqlDà",
                "fmt": "3mf",
                "full_test": False,
            },
        ).json()
        assert "file" in body

    def test_generated_3mf_exists(
        self, client: TestClient, tmp_path: pathlib.Path
    ) -> None:
        body = client.post(
            "/api/model3d/generate",
            json={
                "candidate": SAMPLE_CANDIDATE,
                "sequence": "tqlDà",
                "fmt": "3mf",
                "full_test": False,
            },
        ).json()
        fname = pathlib.Path(body["file"]).name
        assert (tmp_path / fname).exists()

    def test_generated_stl_exists(
        self, client: TestClient, tmp_path: pathlib.Path
    ) -> None:
        body = client.post(
            "/api/model3d/generate",
            json={
                "candidate": SAMPLE_CANDIDATE,
                "sequence": "tqlDà",
                "fmt": "stl",
                "full_test": False,
            },
        ).json()
        fname = pathlib.Path(body["file"]).name
        assert (tmp_path / fname).exists()

    def test_missing_candidate_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/api/model3d/generate",
            json={"sequence": "tqlDà", "fmt": "3mf"},
        )
        assert resp.status_code == 422

    def test_invalid_fmt_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/api/model3d/generate",
            json={"candidate": SAMPLE_CANDIDATE, "sequence": "tqlDà", "fmt": "obj"},
        )
        assert resp.status_code == 422


# ── US-M2: GET /api/model3d/files ────────────────────────────────────────────

class TestListFiles:
    """GET /api/model3d/files"""

    def test_returns_200(self, client: TestClient) -> None:
        resp = client.get("/api/model3d/files")
        assert resp.status_code == 200

    def test_returns_list(self, client: TestClient) -> None:
        body = client.get("/api/model3d/files").json()
        assert isinstance(body, list)

    def test_empty_when_no_files(self, client: TestClient) -> None:
        """tmp_path está vazio — deve retornar []."""
        body = client.get("/api/model3d/files").json()
        assert body == []

    def test_lists_3mf_after_generate(
        self, client: TestClient, tmp_path: pathlib.Path
    ) -> None:
        """Após gerar um modelo, deve aparecer na lista."""
        # Cria arquivo fake para simular geração
        fake = tmp_path / "tatil_3d_13x13_2.5mm_tqlDà.3mf"
        fake.write_bytes(b"fake-3mf-content")
        body = client.get("/api/model3d/files").json()
        assert fake.name in body

    def test_only_3mf_and_stl_returned(
        self, client: TestClient, tmp_path: pathlib.Path
    ) -> None:
        """Arquivos PNG ou JSON não devem aparecer na lista de modelos 3D."""
        (tmp_path / "preview.png").write_bytes(b"fake")
        (tmp_path / "candidatos.json").write_text("{}")
        body = client.get("/api/model3d/files").json()
        for name in body:
            assert name.endswith(".3mf") or name.endswith(".stl")


# ── US-M3 e US-M4: GET /output/{filename} ────────────────────────────────────

class TestDownloadFile:
    """GET /output/{filename}"""

    def test_existing_file_returns_200(
        self, client: TestClient, tmp_path: pathlib.Path
    ) -> None:
        fake = tmp_path / "modelo.3mf"
        fake.write_bytes(b"\x00\x01binary-content")
        resp = client.get("/output/modelo.3mf")
        assert resp.status_code == 200

    def test_existing_file_returns_binary_content(
        self, client: TestClient, tmp_path: pathlib.Path
    ) -> None:
        content = b"\x00\x01binary-content"
        (tmp_path / "modelo.3mf").write_bytes(content)
        resp = client.get("/output/modelo.3mf")
        assert resp.content == content

    def test_nonexistent_file_returns_404(self, client: TestClient) -> None:
        """US-M4: arquivo inexistente deve retornar 404."""
        resp = client.get("/output/nao_existe_nunca.3mf")
        assert resp.status_code == 404

    def test_404_has_detail_message(self, client: TestClient) -> None:
        resp = client.get("/output/nao_existe.stl")
        assert "detail" in resp.json()
