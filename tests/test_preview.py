"""
Testes de output/preview._generate_tactile_preview_png().

História de usuário:
    Como designer de displays braile, quero que ao gerar um modelo 3D
    seja automaticamente gerado um PNG de pré-visualização com vista
    superior e painel de dados técnicos para facilitar a revisão.
"""
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from glifo_analise.output.preview import _generate_tactile_preview_png


def _make_candidate_dict(rows: int = 5, cols: int = 5, spacing_mm: float = 2.5):
    """Cria dict mínimo compatível com a assinatura de _generate_tactile_preview_png."""
    return {
        "cols": cols,
        "rows": rows,
        "spacing_mm": spacing_mm,
        "cell_w_mm": cols * spacing_mm,
        "cell_h_mm": rows * spacing_mm,
        "resolution": (cols, rows),
        "reading_mode": "1-dedo",
        "seq_capacity": 4,
        "eff_cols": cols,
        "eff_rows": rows,
    }


def _make_bitmap(rows: int = 5, cols: int = 5) -> np.ndarray:
    """Bitmap all-ones (todos pinos levantados)."""
    return np.ones((rows, cols), dtype=np.uint8)


class TestGenerateTactilePreviewPng:
    def test_creates_png_file(self, tmp_path):
        bitmap = _make_bitmap()
        candidate = _make_candidate_dict()
        path = _generate_tactile_preview_png(
            bitmap=bitmap,
            candidate=candidate,
            out_dir=tmp_path,
            label="teste",
        )
        assert path.exists(), "Arquivo PNG de preview não foi criado"
        assert path.suffix.lower() == ".png"

    def test_image_has_positive_dimensions(self, tmp_path):
        bitmap = _make_bitmap()
        candidate = _make_candidate_dict()
        path = _generate_tactile_preview_png(
            bitmap=bitmap,
            candidate=candidate,
            out_dir=tmp_path,
            label="dims",
        )
        img = Image.open(path)
        w, h = img.size
        assert w > 0 and h > 0

    def test_image_mode_is_rgb(self, tmp_path):
        bitmap = _make_bitmap()
        candidate = _make_candidate_dict()
        path = _generate_tactile_preview_png(
            bitmap=bitmap,
            candidate=candidate,
            out_dir=tmp_path,
            label="mode",
        )
        img = Image.open(path)
        assert img.mode == "RGB"


class TestTactilePreviewPinColors:
    def test_all_raised_pins_contain_dark_pixels(self, tmp_path):
        """Bitmap all-ones → pinos levantados → imagem deve ter pixels escuros na zona dos pinos."""
        bitmap = _make_bitmap(5, 5)
        candidate = _make_candidate_dict(5, 5)
        path = _generate_tactile_preview_png(
            bitmap=bitmap,
            candidate=candidate,
            out_dir=tmp_path,
            label="pins_up",
        )
        img = Image.open(path).convert("RGB")
        arr = np.array(img)
        # Pelo menos alguns pixels escuros (pinos) devem existir
        dark = (arr < 100).all(axis=2)
        assert dark.any(), "Imagem sem pixels escuros — pinos levantados não foram renderizados"

    def test_all_zero_bitmap_has_no_dark_pin_circles(self, tmp_path):
        """Bitmap all-zeros → nenhum pino ativo → nenhum círculo escuro de pino."""
        bitmap_on  = np.ones((5, 5), dtype=np.uint8)
        bitmap_off = np.zeros((5, 5), dtype=np.uint8)
        cand = _make_candidate_dict(5, 5)

        path_on  = _generate_tactile_preview_png(bitmap=bitmap_on,  candidate=cand, out_dir=tmp_path, label="on")
        path_off = _generate_tactile_preview_png(bitmap=bitmap_off, candidate=cand, out_dir=tmp_path, label="off")

        arr_on  = np.array(Image.open(path_on).convert("RGB"))
        arr_off = np.array(Image.open(path_off).convert("RGB"))

        # A imagem com todos os pinos levantados deve ter mais pixels escuros
        # (círculos negros de pinos) do que a imagem sem pinos.
        dark_on  = (arr_on  < 100).all(axis=2).sum()
        dark_off = (arr_off < 100).all(axis=2).sum()
        assert dark_on > dark_off, "Imagem com pinos deveria ter mais pixels escuros que sem pinos"
