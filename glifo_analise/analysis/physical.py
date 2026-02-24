"""
Funções de cálculo físico da célula tátil: dimensões mm e capacidade sequencial.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple

from glifo_analise.config import (
    PIN_SPACING_MM,
    PIN_DIAMETER_MM,
    MAX_FINGER_AREA_MM,
    MAX_MULTI_FINGER_MM,
    MAX_CELL_ASPECT_RATIO,
    HAND_SPAN_MM,
    GAP_BETWEEN_CELLS_MM,
    SEQ_GLYPH_MIN,
    SEQ_GLYPH_MAX,
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


# ── Regex: captura 8x12_2.5mm ou 13x13_3.0mm em nomes de arquivos ───────────
_FILENAME_RE = re.compile(r"(\d+)x(\d+)_(\d+(?:\.\d+)?)mm", re.IGNORECASE)


def _physics_from_filename(filename: str) -> Optional[Dict[str, Any]]:
    """Extrai parâmetros psicofísicos e critérios ISO a partir do nome de um arquivo gerado.

    O padrão esperado no nome é ``{cols}x{rows}_{spacing}mm`` (ex: ``13x13_2.5mm``).

    Args:
        filename: Nome do arquivo (sem caminho) gerado pela ferramenta.

    Returns:
        Dict com campos de física da célula e lista de critérios ISO, ou ``None``
        se o padrão não for encontrado no nome.
    """
    m = _FILENAME_RE.search(filename)
    if not m:
        return None

    cols = int(m.group(1))
    rows = int(m.group(2))
    spacing_mm = float(m.group(3))

    cell_w_mm, cell_h_mm = _physical_cell_size_mn((cols, rows), spacing_mm)
    gap_mm = round(spacing_mm - PIN_DIAMETER_MM, 2)
    max_dim = max(cell_w_mm, cell_h_mm)
    min_dim = min(cell_w_mm, cell_h_mm)
    aspect = round(max_dim / min_dim, 2) if min_dim > 0 else None
    seq = _sequence_capacity(cell_w_mm)

    if max_dim <= MAX_FINGER_AREA_MM:
        reading_mode = "1-dedo"
    elif max_dim <= MAX_MULTI_FINGER_MM:
        reading_mode = "multi-dedo"
    else:
        reading_mode = "fora-de-alcance"

    ratio_sd = round(spacing_mm / PIN_DIAMETER_MM, 2)

    iso = [
        {
            "label": "Espaçamento ≥ 2,5 mm",
            "ok": spacing_mm >= 2.5,
            "detail": f"{spacing_mm:.1f} mm",
        },
        {
            "label": "Gap ≥ 1,0 mm",
            "ok": gap_mm >= 1.0,
            "detail": f"{gap_mm:.1f} mm",
        },
        {
            "label": "Razão espaç/diâm ≥ 1,5×",
            "ok": ratio_sd >= 1.5,
            "detail": f"{ratio_sd:.2f}×",
        },
        {
            "label": "Eixo menor ≤ 25 mm",
            "ok": min_dim <= MAX_FINGER_AREA_MM,
            "detail": f"{min_dim:.1f} mm",
        },
        {
            "label": "Eixo maior ≤ 55 mm",
            "ok": max_dim <= MAX_MULTI_FINGER_MM,
            "detail": f"{max_dim:.1f} mm",
        },
        {
            "label": f"Aspecto ≤ {MAX_CELL_ASPECT_RATIO:.1f}×",
            "ok": (aspect is not None and aspect <= MAX_CELL_ASPECT_RATIO),
            "detail": f"{aspect:.2f}×" if aspect is not None else "N/D",
        },
        {
            "label": f"Glifos/tira ({SEQ_GLYPH_MIN}–{SEQ_GLYPH_MAX + 2})",
            "ok": SEQ_GLYPH_MIN <= seq <= SEQ_GLYPH_MAX + 2,
            "detail": f"{seq} glifos",
        },
    ]

    return {
        "resolution": f"{cols}×{rows}",
        "spacing_mm": spacing_mm,
        "cell_w_mm": round(cell_w_mm, 1),
        "cell_h_mm": round(cell_h_mm, 1),
        "gap_mm": gap_mm,
        "aspect_ratio": aspect,
        "reading_mode": reading_mode,
        "seq_capacity": seq,
        "iso": iso,
    }
