"""
Estruturas de dados (dataclasses) do pacote glifo_analise.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np


@dataclass
class GlyphProfile:
    """Perfil de um glifo extraído na resolução de referência (64×64)."""

    char: str
    codepoint: int
    glyph_name: str
    density: float            # proporção de pixels de tinta (ρ)
    edge_complexity: float    # proporção de pixels de borda (ε)
    bitmap_ref: np.ndarray    # bitmap 64×64 de referência


@dataclass
class TactileVerdict:
    """Veredicto tátil de um glifo para uma resolução matricial específica."""

    char: str
    codepoint: int
    resolution: Tuple[int, int]
    phys_size_mm: float
    fits_finger: bool
    density: float
    density_ok: bool
    iou: float
    iou_ok: bool
    edge_complexity: float
    complexity_ok: bool
    verdict: str  # APTO / VAZIO / SATURADO / RASO / PERDA_ESTRUTURAL / TAMANHO_GRANDE


@dataclass
class ResolutionReport:
    """Sumário da análise psicofísica para uma resolução completa."""

    resolution: Tuple[int, int]
    phys_size_mm: float
    fits_finger: bool
    total: int
    apto: int
    blank: int
    loss: int = 0
    loss_chars: List[str] = field(default_factory=list)
    verdicts: List[TactileVerdict] = field(default_factory=list)
    eff_resolution: Tuple[int, int] = (0, 0)
    crop_box: Tuple[int, int, int, int] = (0, 0, 0, 0)

    @property
    def coverage_pct(self) -> float:
        """Percentual de glifos aptos sobre os glifos com visual."""
        usable = self.total - self.blank
        return 100.0 * self.apto / usable if usable else 0.0


@dataclass
class ExtendedReport:
    """Resultado da análise estendida para um par (resolução, espaçamento)."""

    resolution: Tuple[int, int]    # (M colunas, N linhas)
    spacing_mm: float              # espaçamento centro a centro dos pinos (mm)
    cell_w_mm: float               # largura física da célula (mm)
    cell_h_mm: float               # altura física da célula (mm)
    reading_mode: str              # "1-dedo" | "multi-dedo" | "fora-de-alcance"
    seq_capacity: int              # K máximo de glifos/tira dentro da HAND_SPAN
    seq_in_range: bool             # True se seq_capacity >= SEQ_GLYPH_MIN
    report: ResolutionReport       # análise psicofísica completa
