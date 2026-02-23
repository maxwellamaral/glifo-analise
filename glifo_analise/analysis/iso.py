"""
Verificação de conformidade normativa (ISO 11548-2) e psicofísica.
"""
from __future__ import annotations

from typing import List, Tuple

from glifo_analise.config import (
    PIN_DIAMETER_MM,
    MAX_FINGER_AREA_MM,
    MAX_MULTI_FINGER_MM,
    MAX_CELL_ASPECT_RATIO,
    SEQ_GLYPH_MIN,
    SEQ_GLYPH_MAX,
)
from glifo_analise.models import ExtendedReport


def _iso_compliance(er: ExtendedReport) -> List[Tuple[str, bool, str]]:
    """
    Avalia conformidade psicofísica e normativa (ISO 11548-2) de um candidato.

    Cada critério é independente para facilitar diagnóstico ponto a ponto.

    Args:
        er: ExtendedReport do candidato avaliado.

    Returns:
        Lista de (criterio, aprovado, detalhe) — todos os pontos verificados.
    """
    sp  = er.spacing_mm
    gap = sp - PIN_DIAMETER_MM
    w, h = er.cell_w_mm, er.cell_h_mm
    max_dim = max(w, h)
    min_dim = min(w, h)
    aspect  = max_dim / min_dim if min_dim > 0 else float("inf")

    checks: List[Tuple[str, bool, str]] = [
        # ── ISO 11548-2 §6.3 — parâmetros do pino ───────────────────────────
        (
            "Espaçamento mínimo (>= 2,5 mm)",
            sp >= 2.5,
            f"{sp:.1f} mm",
        ),
        (
            "Gap entre pinos (>= 1,0 mm)",
            gap >= 1.0,
            f"{gap:.1f} mm  [espaç. {sp:.1f} – ∅ {PIN_DIAMETER_MM:.1f}]",
        ),
        # ── Limiar de dois pontos — discriminação tátil ──────────────────────
        (
            "Razão espaç/diâm (>= 1,5×)",
            sp / PIN_DIAMETER_MM >= 1.5,
            f"{sp / PIN_DIAMETER_MM:.2f}×",
        ),
        # ── Tamanho de célula por modo ───────────────────────────────────────
        (
            "Cabe sob 1 dedo (ambos eixos <= 25 mm)"
            if er.reading_mode == "1-dedo"
            else "Eixo menor <= 25 mm (1 dedo varre 1 eixo)",
            min_dim <= MAX_FINGER_AREA_MM,
            f"menor eixo = {min_dim:.1f} mm",
        ),
        (
            "Dimensão máxima dentro do alcance multi-dedo (<= 55 mm)"
            if er.reading_mode == "multi-dedo"
            else "Dimensão máxima dentro do alcance 1-dedo (<= 25 mm)",
            max_dim <= (MAX_MULTI_FINGER_MM if er.reading_mode != "1-dedo"
                        else MAX_FINGER_AREA_MM),
            f"maior eixo = {max_dim:.1f} mm",
        ),
        # ── Proporção de aspecto ─────────────────────────────────────────────
        (
            f"Relação de aspecto (<= {MAX_CELL_ASPECT_RATIO:.1f}×)",
            aspect <= MAX_CELL_ASPECT_RATIO,
            f"{aspect:.2f}×  [{w:.1f} × {h:.1f} mm]",
        ),
        # ── Capacidade sequencial ────────────────────────────────────────────
        (
            f"Glifos/tira dentro da faixa ({SEQ_GLYPH_MIN}–{SEQ_GLYPH_MAX})",
            SEQ_GLYPH_MIN <= er.seq_capacity <= SEQ_GLYPH_MAX + 2,
            f"{er.seq_capacity} glifos/tira",
        ),
        # ── Cobertura psicofísica ────────────────────────────────────────────
        (
            "Cobertura útil >= 95%",
            er.report.coverage_pct >= 95.0,
            f"{er.report.coverage_pct:.1f}%",
        ),
        (
            "Cobertura útil >= 100%",
            er.report.coverage_pct >= 100.0,
            f"{er.report.coverage_pct:.1f}%",
        ),
    ]
    return checks
