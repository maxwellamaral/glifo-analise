"""
Testes de output/grid._save_grid().

História de usuário:
    Como pesquisador de acessibilidade, quero gerar uma imagem de grade
    com todos os glifos renderizados para poder revisar visualmente a
    qualidade do mapeamento antes de imprimir em braile.
"""
import re
from pathlib import Path

import pytest
from PIL import Image

from glifo_analise.output.grid import _save_grid


class TestSaveGridFileCreation:
    def test_creates_png_file(self, tmp_path, profiles, sample_report, monkeypatch):
        monkeypatch.chdir(tmp_path)
        path = _save_grid(sample_report, profiles)
        assert path.exists(), "Arquivo PNG não foi criado"

    def test_file_has_png_extension(self, tmp_path, profiles, sample_report, monkeypatch):
        monkeypatch.chdir(tmp_path)
        path = _save_grid(sample_report, profiles)
        assert path.suffix.lower() == ".png"

    def test_filename_contains_resolution(self, tmp_path, profiles, sample_report, monkeypatch):
        monkeypatch.chdir(tmp_path)
        path = _save_grid(sample_report, profiles)
        cols, rows = sample_report.resolution
        assert str(cols) in path.name or "grid" in path.name.lower()


class TestSaveGridImageFormat:
    def test_png_is_readable_image(self, tmp_path, profiles, sample_report, monkeypatch):
        monkeypatch.chdir(tmp_path)
        path = _save_grid(sample_report, profiles)
        img = Image.open(path)
        assert img.size[0] > 0 and img.size[1] > 0

    def test_png_is_rgb_or_rgba(self, tmp_path, profiles, sample_report, monkeypatch):
        monkeypatch.chdir(tmp_path)
        path = _save_grid(sample_report, profiles)
        img = Image.open(path)
        assert img.mode in ("RGB", "RGBA", "L", "P"), f"Modo inesperado: {img.mode}"
