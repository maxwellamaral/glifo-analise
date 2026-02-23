"""
Testes das fórmulas físicas em analysis/physical.py.

História de usuário:
    Como fabricante do dispositivo tátil, quero que os cálculos de
    dimensão de célula e capacidade sequencial respeitem as equações
    físicas documentadas para que as especificações de hardware sejam
    precisas ao milímetro.
"""
import pytest

from glifo_analise.analysis.physical import (
    _physical_cell_size,
    _physical_cell_size_mn,
    _sequence_capacity,
)
from glifo_analise.config import GAP_BETWEEN_CELLS_MM, HAND_SPAN_MM


class TestPhysicalCellSize:
    def test_square_10x10_at_2_5(self):
        # (10-1) * 2.5 = 22.5 mm mas _physical_cell_size usa max(W,H)
        # cell size = (max(10,10)-1)*2.5 = 22.5
        assert _physical_cell_size((10, 10), 2.5) == pytest.approx(22.5)

    def test_square_13x13_at_2_5(self):
        assert _physical_cell_size((13, 13), 2.5) == pytest.approx(30.0)

    def test_uses_larger_dimension(self):
        # Para (8, 12) @ 2.5 → max=12 → (12-1)*2.5 = 27.5
        assert _physical_cell_size((8, 12), 2.5) == pytest.approx(27.5)


class TestPhysicalCellSizeMN:
    def test_10x12_at_2_5(self):
        w, h = _physical_cell_size_mn((10, 12), 2.5)
        assert w == pytest.approx(22.5)   # (10-1)*2.5
        assert h == pytest.approx(27.5)   # (12-1)*2.5

    def test_13x13_at_2_5(self):
        w, h = _physical_cell_size_mn((13, 13), 2.5)
        assert w == pytest.approx(30.0)
        assert h == pytest.approx(30.0)

    def test_1x1_resolution(self):
        w, h = _physical_cell_size_mn((1, 1), 2.5)
        assert w == pytest.approx(0.0)
        assert h == pytest.approx(0.0)

    def test_asymmetric_8x10(self):
        w, h = _physical_cell_size_mn((8, 10), 2.5)
        assert w == pytest.approx(17.5)   # (8-1)*2.5
        assert h == pytest.approx(22.5)   # (10-1)*2.5

    def test_larger_spacing(self):
        w, h = _physical_cell_size_mn((10, 10), 3.5)
        assert w == pytest.approx(31.5)
        assert h == pytest.approx(31.5)


class TestSequenceCapacity:
    def test_known_value_13x13_at_2_5(self):
        # cell_w = 22.5, gap=3, hand=180
        # K = floor((180+3)/(22.5+3)) = floor(183/25.5) = floor(7.176) = 7
        k = _sequence_capacity(22.5, gap_mm=3.0, hand_span_mm=180.0)
        assert k == 7

    def test_zero_cell_width_returns_zero(self):
        assert _sequence_capacity(0.0) == 0

    def test_negative_cell_width_returns_zero(self):
        assert _sequence_capacity(-1.0) == 0

    def test_large_cell_returns_fewer(self):
        k_small = _sequence_capacity(17.5, gap_mm=3.0, hand_span_mm=180.0)
        k_large = _sequence_capacity(40.0, gap_mm=3.0, hand_span_mm=180.0)
        assert k_small > k_large

    def test_defaults_match_config(self):
        k = _sequence_capacity(22.5)
        k_explicit = _sequence_capacity(
            22.5, gap_mm=GAP_BETWEEN_CELLS_MM, hand_span_mm=HAND_SPAN_MM
        )
        assert k == k_explicit
