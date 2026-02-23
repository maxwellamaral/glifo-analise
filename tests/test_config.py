"""
Testes das constantes e grupos de glifos ELiS definidos em config.py.

História de usuário:
    Como analista tátil, quero garantir que os parâmetros psicofísicos
    padrão atendam aos requisitos mínimos da ISO 11548-2 para que
    qualquer análise gerada pelo sistema seja normativamente válida.
"""
from glifo_analise.config import (
    PIN_SPACING_MM,
    PIN_DIAMETER_MM,
    ISO_MIN_GAP_MM,
    MAX_FINGER_AREA_MM,
    MAX_MULTI_FINGER_MM,
    HAND_SPAN_MM,
    GAP_BETWEEN_CELLS_MM,
    SEQ_GLYPH_MIN,
    SEQ_GLYPH_MAX,
    MIN_COVERAGE_ECONOMY,
    MAX_CELL_ASPECT_RATIO,
    DENSITY_MIN,
    DENSITY_MAX,
    EDGE_COMPLEXITY_MIN,
    GLYPH_GROUPS,
    PIN_SPACING_CANDIDATES,
    ASYMMETRIC_RESOLUTIONS,
    DEFAULT_TACTILE_SEQUENCE,
)


class TestIsoParameters:
    def test_pin_spacing_meets_iso_minimum(self):
        assert PIN_SPACING_MM >= 2.5

    def test_pin_diameter_is_correct(self):
        assert PIN_DIAMETER_MM == 1.5

    def test_iso_min_gap_derived_correctly(self):
        assert abs(ISO_MIN_GAP_MM - (PIN_SPACING_MM - PIN_DIAMETER_MM)) < 1e-9

    def test_iso_min_gap_is_at_least_1mm(self):
        assert ISO_MIN_GAP_MM >= 1.0

    def test_one_finger_area_limit(self):
        assert MAX_FINGER_AREA_MM == 25.0

    def test_multi_finger_area_limit(self):
        assert MAX_MULTI_FINGER_MM > MAX_FINGER_AREA_MM


class TestPsychophysicalThresholds:
    def test_density_range_is_valid(self):
        assert 0.0 < DENSITY_MIN < DENSITY_MAX < 1.0

    def test_edge_complexity_min_is_positive(self):
        assert EDGE_COMPLEXITY_MIN > 0.0

    def test_coverage_economy_threshold(self):
        assert MIN_COVERAGE_ECONOMY == 95.0

    def test_aspect_ratio_limit(self):
        assert MAX_CELL_ASPECT_RATIO == 2.5


class TestSequentialParameters:
    def test_seq_glyph_range_is_ordered(self):
        assert SEQ_GLYPH_MIN < SEQ_GLYPH_MAX

    def test_hand_span_reasonable(self):
        assert 100.0 <= HAND_SPAN_MM <= 250.0

    def test_gap_between_cells_positive(self):
        assert GAP_BETWEEN_CELLS_MM > 0.0


class TestGlyphGroups:
    def test_five_groups_defined(self):
        assert len(GLYPH_GROUPS) == 5

    def test_all_groups_nonempty(self):
        for name, cps in GLYPH_GROUPS.items():
            assert len(cps) > 0, f"Grupo '{name}' está vazio"

    def test_uppercase_group_has_26(self):
        upper = [cp for cp in GLYPH_GROUPS["Maiúsculas (A-Z)"]
                 if 0x41 <= cp <= 0x5A]
        assert len(upper) == 26

    def test_digits_group_has_10(self):
        digits = [cp for cp in GLYPH_GROUPS["Dígitos (0-9)"]
                  if 0x30 <= cp <= 0x39]
        assert len(digits) == 10


class TestCandidateResolutions:
    def test_spacing_candidates_include_iso_minimum(self):
        assert 2.5 in PIN_SPACING_CANDIDATES

    def test_asymmetric_resolutions_nonempty(self):
        assert len(ASYMMETRIC_RESOLUTIONS) > 0

    def test_asymmetric_resolutions_are_tuples_of_two(self):
        for res in ASYMMETRIC_RESOLUTIONS:
            assert len(res) == 2

    def test_default_sequence_nonempty(self):
        assert len(DEFAULT_TACTILE_SEQUENCE) > 0
