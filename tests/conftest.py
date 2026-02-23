"""
Fixtures compartilhadas entre todos os testes.

História de usuário:
    Como desenvolvedor que refatora o projeto glifo-analise,
    quero fixtures de sessão que carreguem dados pesados (TTF) uma
    única vez para que a suíte de testes seja rápida o suficiente
    para rodar em CI sem timeout.
"""
import pathlib
import pytest
import numpy as np

from glifo_analise.config import (
    FONT_PATH,
    PIN_SPACING_MM,
    MAX_FINGER_AREA_MM,
    SEQ_GLYPH_MIN,
    SEQ_GLYPH_MAX,
)
from glifo_analise.models import ExtendedReport, ResolutionReport, TactileVerdict
from glifo_analise.analysis.bitmap import _build_profiles, _collect_mapped_codepoints


@pytest.fixture(scope="session")
def profiles():
    """Perfis de glifos carregados da TTF real — carregado 1× por sessão."""
    codepoints = _collect_mapped_codepoints(FONT_PATH)
    return _build_profiles(codepoints, FONT_PATH)


@pytest.fixture()
def sample_report():
    """ResolutionReport sintético com 131 aptos / 131 com visual."""
    verdicts = [
        TactileVerdict(
            char="a",
            codepoint=97,
            resolution=(13, 13),
            phys_size_mm=22.5,
            fits_finger=True,
            density=0.2,
            density_ok=True,
            iou=0.8,
            iou_ok=True,
            edge_complexity=0.15,
            complexity_ok=True,
            verdict="APTO",
        )
    ]
    return ResolutionReport(
        resolution=(13, 13),
        phys_size_mm=22.5,
        fits_finger=True,
        total=131,
        apto=131,
        blank=0,
        loss=0,
        verdicts=verdicts,
        eff_resolution=(10, 10),
        crop_box=(0, 9, 0, 9),
    )


@pytest.fixture()
def sample_er(sample_report):
    """ExtendedReport sintético aprovado em todos os critérios ISO."""
    return ExtendedReport(
        resolution=(13, 13),
        spacing_mm=2.5,
        cell_w_mm=22.5,
        cell_h_mm=22.5,
        reading_mode="1-dedo",
        seq_capacity=7,
        seq_in_range=True,
        report=sample_report,
    )
