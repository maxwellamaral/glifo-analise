"""
Funções de cálculo físico da célula tátil: dimensões mm e capacidade sequencial.
"""
from __future__ import annotations

from typing import Tuple

from glifo_analise.config import (
    PIN_SPACING_MM,
    HAND_SPAN_MM,
    GAP_BETWEEN_CELLS_MM,
    SEQ_GLYPH_MIN,
)


def _physical_cell_size(
    res: Tuple[int, int],
    spacing_mm: float = PIN_SPACING_MM,
) -> float:
    """
    Tamanho físico (mm) da célula matricial quadrada, pino-a-pino extremo a extremo.

    Args:
        res: (cols, rows) da resolução.
        spacing_mm: Espaçamento centro a centro (mm); padrão = PIN_SPACING_MM.
    """
    return (max(res) - 1) * spacing_mm


def _physical_cell_size_mn(
    res: Tuple[int, int],
    spacing_mm: float,
) -> Tuple[float, float]:
    """
    Retorna (cell_w_mm, cell_h_mm) para célula M×N com espaçamento configurável.

    Args:
        res: (cols, rows) da resolução da célula.
        spacing_mm: Espaçamento centro a centro entre pinos (mm).

    Returns:
        (largura_mm, altura_mm)
    """
    cols, rows = res
    return (cols - 1) * spacing_mm, (rows - 1) * spacing_mm


def _sequence_capacity(
    cell_w_mm: float,
    gap_mm: float = GAP_BETWEEN_CELLS_MM,
    hand_span_mm: float = HAND_SPAN_MM,
) -> int:
    """
    Número máximo K de glifos dispostos lado a lado dentro da envergadura da mão.

    Equação:
        $K \\cdot w_{cell} + (K-1) \\cdot g \\leq L_{hand}$
        $K \\leq \\frac{L_{hand} + g}{w_{cell} + g}$

    Args:
        cell_w_mm: Largura de uma célula (mm).
        gap_mm: Gap físico entre células adjacentes (mm).
        hand_span_mm: Envergadura da mão para varredura tátil (mm).

    Returns:
        Número inteiro de glifos na tira.
    """
    if cell_w_mm <= 0:
        return 0
    return int((hand_span_mm + gap_mm) / (cell_w_mm + gap_mm))
