"""
Testes dos dataclasses definidos em models.py.

História de usuário:
    Como desenvolvedor que consome os resultados de análise,
    quero que os dataclasses sejam imutavelmente tipados e que
    propriedades derivadas (ex: coverage_pct) sejam calculadas
    corretamente para evitar erros silenciosos nos relatórios.
"""
import pytest
from glifo_analise.models import (
    GlyphProfile,
    TactileVerdict,
    ResolutionReport,
    ExtendedReport,
)
import numpy as np


class TestResolutionReport:
    def test_coverage_pct_normal(self):
        r = ResolutionReport(
            resolution=(10, 10),
            phys_size_mm=17.5,
            fits_finger=True,
            total=100,
            apto=90,
            blank=10,
        )
        assert abs(r.coverage_pct - 100 * 90 / 90) < 1e-9  # total-blank = 90

    def test_coverage_pct_zero_when_all_blank(self):
        r = ResolutionReport(
            resolution=(10, 10),
            phys_size_mm=17.5,
            fits_finger=True,
            total=10,
            apto=0,
            blank=10,
        )
        assert r.coverage_pct == 0.0

    def test_coverage_pct_100(self):
        r = ResolutionReport(
            resolution=(13, 13),
            phys_size_mm=22.5,
            fits_finger=True,
            total=131,
            apto=131,
            blank=0,
        )
        assert r.coverage_pct == 100.0

    def test_eff_resolution_defaults(self):
        r = ResolutionReport(
            resolution=(10, 10),
            phys_size_mm=17.5,
            fits_finger=True,
            total=1,
            apto=1,
            blank=0,
        )
        assert r.eff_resolution == (0, 0)
        assert r.crop_box == (0, 0, 0, 0)

    def test_verdicts_defaults_to_empty_list(self):
        r = ResolutionReport(
            resolution=(10, 10),
            phys_size_mm=17.5,
            fits_finger=True,
            total=1,
            apto=1,
            blank=0,
        )
        assert r.verdicts == []
        assert r.loss_chars == []


class TestTactileVerdict:
    def test_fields_accessible(self):
        v = TactileVerdict(
            char="A",
            codepoint=65,
            resolution=(10, 10),
            phys_size_mm=17.5,
            fits_finger=True,
            density=0.2,
            density_ok=True,
            iou=0.8,
            iou_ok=True,
            edge_complexity=0.15,
            complexity_ok=True,
            verdict="APTO",
        )
        assert v.verdict == "APTO"
        assert v.char == "A"
        assert v.codepoint == 65


class TestExtendedReport:
    def test_construction(self, sample_er):
        assert sample_er.resolution == (13, 13)
        assert sample_er.spacing_mm == 2.5
        assert sample_er.reading_mode == "1-dedo"

    def test_report_is_resolution_report(self, sample_er):
        assert isinstance(sample_er.report, ResolutionReport)

    def test_coverage_delegated(self, sample_er):
        assert sample_er.report.coverage_pct == 100.0


class TestGlyphProfile:
    def test_construction(self):
        bm = np.zeros((64, 64), dtype=np.uint8)
        p = GlyphProfile(
            char="a",
            codepoint=97,
            glyph_name="a",
            density=0.1,
            edge_complexity=0.05,
            bitmap_ref=bm,
        )
        assert p.char == "a"
        assert p.bitmap_ref.shape == (64, 64)
