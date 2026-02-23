"""
Testes de output/persistence._save_candidates() e _load_candidates().

História de usuário:
    Como pesquisador, quero salvar candidatos de resolução em disco e
    carregá-los novamente numa sessão futura para não refazer a análise
    computacionalmente cara.
"""
import json
from pathlib import Path

import pytest

from glifo_analise.output.persistence import _save_candidates, _load_candidates


class TestLoadCandidatesEmpty:
    def test_returns_empty_list_when_file_missing(self, tmp_path, monkeypatch):
        """Se o arquivo não existe, _load_candidates() deve retornar []."""
        target = tmp_path / "candidates_nonexistent.json"
        monkeypatch.setattr("glifo_analise.output.persistence.CANDIDATES_FILE", target)
        result = _load_candidates()
        assert result == []

    def test_returns_empty_list_when_file_empty_json(self, tmp_path, monkeypatch):
        target = tmp_path / "candidates_empty.json"
        target.write_text("[]", encoding="utf-8")
        monkeypatch.setattr("glifo_analise.output.persistence.CANDIDATES_FILE", target)
        result = _load_candidates()
        assert result == []


class TestSaveCandidatesRoundTrip:
    def test_round_trip(self, tmp_path, monkeypatch, sample_er):
        target = tmp_path / "candidates.json"
        monkeypatch.setattr("glifo_analise.output.persistence.CANDIDATES_FILE", target)

        _save_candidates([sample_er])
        loaded = _load_candidates()

        assert len(loaded) >= 1
        first = loaded[0]
        assert first["resolution"] == list(sample_er.resolution)
        assert first["spacing_mm"] == pytest.approx(sample_er.spacing_mm)

    def test_json_has_required_keys(self, tmp_path, monkeypatch, sample_er):
        target = tmp_path / "candidates.json"
        monkeypatch.setattr("glifo_analise.output.persistence.CANDIDATES_FILE", target)

        _save_candidates([sample_er])
        data = json.loads(target.read_text(encoding="utf-8"))

        required_keys = {"resolution", "spacing_mm", "cell_w_mm", "cell_h_mm",
                         "reading_mode", "seq_capacity"}
        for entry in data:
            missing = required_keys - entry.keys()
            assert not missing, f"Chaves ausentes no JSON: {missing}"

    def test_save_multiple_and_load_all(self, tmp_path, monkeypatch, sample_er):
        target = tmp_path / "candidates_multi.json"
        monkeypatch.setattr("glifo_analise.output.persistence.CANDIDATES_FILE", target)

        _save_candidates([sample_er, sample_er])
        loaded = _load_candidates()
        assert len(loaded) == 2
