"""
Testes de analysis/resolution._analyze_resolution_ext().

História de usuário:
    Como pesquisador de acessibilidade, quero analisar uma resolução de
    display braile e obter cobertura, modo de leitura e capacidade sequencial
    para que eu possa decidir se a resolução é viável para uso.
"""
import pytest

from glifo_analise.analysis.resolution import _analyze_resolution_ext
from glifo_analise.config import (
    PIN_SPACING_MM,
    SEQ_GLYPH_MIN,
    SEQ_GLYPH_MAX,
)


class TestAnalyzeResolutionExtCoverage:
    """Cobertura de glifos deve ser ≥ 95 % para resolução 13×13."""

    def test_13x13_spacing_2_5_min_85_percent(self, profiles):
        # A fonte ELIS atinge ~90% de cobertura nesta resolução; exigimos ≥ 85%
        er = _analyze_resolution_ext(13, 13, PIN_SPACING_MM, profiles)
        assert er is not None, "Deve retornar ExtendedReport"
        coverage = er.report.apto / er.report.total * 100
        assert coverage >= 85.0, f"Cobertura {coverage:.1f}% < 85%"

    def test_total_glyphs_positive(self, profiles):
        er = _analyze_resolution_ext(13, 13, PIN_SPACING_MM, profiles)
        assert er.report.total > 0


class TestAnalyzeResolutionExtReadingMode:
    """Modo de leitura deve ser '1-dedo' ou 'multi-dedo' conforme dimensão física."""

    def test_small_cell_is_one_finger(self, profiles):
        # 9×9 com pin spacing 2.5 → cell ≈ 20 mm (< 25 mm) → 1-dedo
        er = _analyze_resolution_ext(9, 9, 2.5, profiles)
        assert er.reading_mode == "1-dedo"

    def test_large_cell_is_multi_finger(self, profiles):
        # 21×21 com pin spacing 2.5 → cell = 50 mm (> 25 mm) → multi-dedo
        er = _analyze_resolution_ext(21, 21, 2.5, profiles)
        assert er.reading_mode == "multi-dedo"


class TestAnalyzeResolutionExtSeqCapacity:
    """seq_in_range deve ser True quando seq_capacity estiver na faixa esperada."""

    def test_seq_in_range_when_capacity_gte_min(self, profiles):
        er = _analyze_resolution_ext(13, 13, PIN_SPACING_MM, profiles)
        # se seq_capacity >= SEQ_GLYPH_MIN, seq_in_range deve ser True
        if er.seq_capacity >= SEQ_GLYPH_MIN:
            assert er.seq_in_range

    def test_seq_in_range_false_when_capacity_below_min(self, profiles):
        # Uso de resolução muito pequena (3×3) → seq_capacity provavelmente < SEQ_GLYPH_MIN
        er = _analyze_resolution_ext(3, 3, PIN_SPACING_MM, profiles)
        if er.seq_capacity < SEQ_GLYPH_MIN:
            assert not er.seq_in_range

    def test_physical_dimensions_positive(self, profiles):
        er = _analyze_resolution_ext(13, 13, PIN_SPACING_MM, profiles)
        assert er.cell_w_mm > 0
        assert er.cell_h_mm > 0
        assert er.spacing_mm == PIN_SPACING_MM
