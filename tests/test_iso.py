"""
Testes da verificação de conformidade ISO 11548-2 em analysis/iso.py.

História de usuário:
    Como pesquisador de acessibilidade, quero que cada critério da
    ISO 11548-2 seja verificado individualmente para poder identificar
    exatamente qual parâmetro é responsável por uma não-conformidade
    em um candidato específico.
"""
import pytest

from glifo_analise.analysis.iso import _iso_compliance
from glifo_analise.models import ExtendedReport, ResolutionReport


def _make_er(
    resolution=(13, 13),
    spacing_mm=2.5,
    cell_w_mm=22.5,
    cell_h_mm=22.5,
    reading_mode="1-dedo",
    seq_capacity=7,
    coverage_pct=100.0,
):
    """Fábrica de ExtendedReport para parametrizar testes ISO."""
    blanks = 0
    apto = int(coverage_pct)  # simplificação: total=100, blank=0
    report = ResolutionReport(
        resolution=resolution,
        phys_size_mm=max(cell_w_mm, cell_h_mm),
        fits_finger=max(cell_w_mm, cell_h_mm) <= 25.0,
        total=100,
        apto=apto,
        blank=blanks,
        eff_resolution=(10, 10),
        crop_box=(0, 9, 0, 9),
    )
    return ExtendedReport(
        resolution=resolution,
        spacing_mm=spacing_mm,
        cell_w_mm=cell_w_mm,
        cell_h_mm=cell_h_mm,
        reading_mode=reading_mode,
        seq_capacity=seq_capacity,
        seq_in_range=seq_capacity >= 4,
        report=report,
    )


def _checks_dict(er):
    """Converte lista de checks em dict {nome_do_critério_parcial: bool}."""
    raw = _iso_compliance(er)
    assert isinstance(raw, list)
    for item in raw:
        assert len(item) == 3, "Cada item deve ser (str, bool, str)"
    return raw


class TestIsoComplianceAllPass:
    def test_ideal_candidate_all_pass(self, sample_er):
        checks = _iso_compliance(sample_er)
        failed = [(name, detail) for name, ok, detail in checks if not ok]
        assert failed == [], f"Critérios falhos inesperados: {failed}"

    def test_returns_list_of_tuples(self, sample_er):
        checks = _iso_compliance(sample_er)
        assert isinstance(checks, list)
        assert len(checks) >= 6


class TestIsoComplianceSpacing:
    def test_spacing_below_2_5_fails(self):
        er = _make_er(spacing_mm=2.4, cell_w_mm=20.0, cell_h_mm=20.0)
        checks = _iso_compliance(er)
        spacing_checks = [ok for name, ok, _ in checks if "2,5" in name or "mínimo" in name.lower()]
        assert any(not ok for ok in spacing_checks), "Deve falhar com pitch < 2.5 mm"

    def test_spacing_at_2_5_passes(self):
        er = _make_er(spacing_mm=2.5)
        checks = _iso_compliance(er)
        spacing_checks = [ok for name, ok, _ in checks if "2,5" in name or "mínimo" in name.lower()]
        assert all(spacing_checks)


class TestIsoComplianceCellSize:
    def test_one_finger_oversized_fails(self):
        er = _make_er(cell_w_mm=30.0, cell_h_mm=30.0, reading_mode="1-dedo")
        checks = _iso_compliance(er)
        size_fails = [name for name, ok, _ in checks if not ok and ("dedo" in name or "25" in name)]
        assert len(size_fails) > 0, "Célula 30mm deve reprovar critério 1-dedo"

    def test_multi_finger_within_55mm_passes(self):
        er = _make_er(
            cell_w_mm=50.0, cell_h_mm=50.0,
            reading_mode="multi-dedo", seq_capacity=4
        )
        checks = _iso_compliance(er)
        multi_fails = [name for name, ok, _ in checks if not ok and "multi" in name.lower()]
        assert len(multi_fails) == 0


class TestIsoComplianceCoverage:
    def test_coverage_below_95_fails(self):
        er = _make_er(coverage_pct=94.0)
        checks = _iso_compliance(er)
        cov_fails = [name for name, ok, _ in checks if not ok and "95" in name]
        assert len(cov_fails) > 0

    def test_coverage_100_passes_both(self):
        er = _make_er(coverage_pct=100.0)
        checks = _iso_compliance(er)
        cov_fails = [name for name, ok, _ in checks
                     if not ok and ("95" in name or "100" in name)]
        assert len(cov_fails) == 0


class TestIsoComplianceAspect:
    def test_aspect_above_2_5_fails(self):
        er = _make_er(cell_w_mm=50.0, cell_h_mm=10.0, reading_mode="multi-dedo")
        checks = _iso_compliance(er)
        aspect_fails = [name for name, ok, _ in checks if not ok and "aspecto" in name.lower()]
        assert len(aspect_fails) > 0

    def test_square_cell_passes(self):
        er = _make_er(cell_w_mm=22.5, cell_h_mm=22.5)
        checks = _iso_compliance(er)
        aspect_fails = [name for name, ok, _ in checks if not ok and "aspecto" in name.lower()]
        assert len(aspect_fails) == 0


class TestIsoComplianceSequential:
    def test_below_minimum_seq_fails(self):
        er = _make_er(seq_capacity=2)
        checks = _iso_compliance(er)
        seq_fails = [name for name, ok, _ in checks if not ok and "faixa" in name.lower()]
        assert len(seq_fails) > 0

    def test_within_range_passes(self):
        er = _make_er(seq_capacity=5)
        checks = _iso_compliance(er)
        seq_fails = [name for name, ok, _ in checks if not ok and "faixa" in name.lower()]
        assert len(seq_fails) == 0
