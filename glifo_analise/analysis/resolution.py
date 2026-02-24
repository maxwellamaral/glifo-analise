"""
Análise tátil por resolução: _analyze_resolution e _analyze_resolution_ext.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from PIL import ImageFont

from glifo_analise.config import (
    FONT_PATH,
    PIN_SPACING_MM,
    MAX_FINGER_AREA_MM,
    MAX_MULTI_FINGER_MM,
    DENSITY_MIN,
    DENSITY_MAX,
    EDGE_COMPLEXITY_MIN,
    INTENTIONALLY_BLANK,
    SEQ_GLYPH_MIN,
)
from glifo_analise.models import ExtendedReport, GlyphProfile, ResolutionReport, TactileVerdict
from glifo_analise.analysis.bitmap import (
    _effective_resolution,
    _render_bitmap,
    _pixel_density,
    _edge_complexity,
    _iou,
)
from glifo_analise.analysis.physical import (
    _physical_cell_size,
    _physical_cell_size_mn,
    _sequence_capacity,
)


def _analyze_resolution(
    profiles: List[GlyphProfile],
    resolution: Tuple[int, int],
) -> ResolutionReport:
    """Analisa a fonte inteira para uma resolução matricial quadrada."""
    phys_mm_raw = _physical_cell_size(resolution)

    eff_res, crop_box = _effective_resolution(profiles, resolution)
    eff_w_mm = (eff_res[0] - 1) * PIN_SPACING_MM
    eff_h_mm = (eff_res[1] - 1) * PIN_SPACING_MM
    phys_mm = max(eff_w_mm, eff_h_mm)

    fits_finger = phys_mm <= MAX_FINGER_AREA_MM

    test_font = ImageFont.truetype(str(FONT_PATH), resolution[1] - 2)
    verdicts: List[TactileVerdict] = []

    for p in profiles:
        if p.codepoint in INTENTIONALLY_BLANK:
            verdicts.append(TactileVerdict(
                char=p.char, codepoint=p.codepoint, resolution=resolution,
                phys_size_mm=phys_mm, fits_finger=fits_finger,
                density=0.0, density_ok=False,
                iou=1.0, iou_ok=True,
                edge_complexity=0.0, complexity_ok=False,
                verdict="VAZIO",
            ))
            continue

        bm = _render_bitmap(p.char, test_font, resolution)
        if crop_box != (0, 0, 0, 0):
            bm = bm[crop_box[0]:crop_box[1] + 1, crop_box[2]:crop_box[3] + 1]
        d   = _pixel_density(bm)
        ec  = _edge_complexity(bm)
        iou = _iou(p.bitmap_ref, bm)

        density_ok    = DENSITY_MIN <= d <= DENSITY_MAX
        iou_ok        = iou >= 0.15
        complexity_ok = ec >= EDGE_COMPLEXITY_MIN

        if not fits_finger:
            verdict = "TAMANHO_GRANDE"
        elif d < DENSITY_MIN:
            verdict = "VAZIO"
        elif d > DENSITY_MAX:
            verdict = "SATURADO"
        elif not complexity_ok:
            verdict = "RASO"
        elif not iou_ok:
            verdict = "PERDA_ESTRUTURAL"
        else:
            verdict = "APTO"

        verdicts.append(TactileVerdict(
            char=p.char, codepoint=p.codepoint, resolution=resolution,
            phys_size_mm=phys_mm, fits_finger=fits_finger,
            density=d, density_ok=density_ok,
            iou=iou, iou_ok=iou_ok,
            edge_complexity=ec, complexity_ok=complexity_ok,
            verdict=verdict,
        ))

    apto  = sum(1 for v in verdicts if v.verdict == "APTO")
    blank = sum(1 for v in verdicts if v.verdict == "VAZIO")
    loss  = sum(1 for v in verdicts if v.verdict not in ("APTO", "VAZIO"))

    return ResolutionReport(
        resolution=resolution, phys_size_mm=phys_mm, fits_finger=fits_finger,
        total=len(verdicts), apto=apto, blank=blank, loss=loss,
        loss_chars=[v.char for v in verdicts if v.verdict not in ("APTO", "VAZIO")],
        verdicts=verdicts,
        eff_resolution=eff_res, crop_box=crop_box,
    )


def _analyze_resolution_ext(
    cols: int,
    rows: int,
    spacing_mm: float,
    profiles: List[GlyphProfile],
    *,
    density_min: float = DENSITY_MIN,
    density_max: float = DENSITY_MAX,
    edge_complexity_min: float = EDGE_COMPLEXITY_MIN,
    iou_min: float = 0.15,
    max_finger_area_mm: float = MAX_FINGER_AREA_MM,
    max_multi_finger_mm: float = MAX_MULTI_FINGER_MM,
    seq_glyph_min: int = SEQ_GLYPH_MIN,
) -> ExtendedReport:
    """
    Analisa a fonte para uma resolução M×N e um espaçamento configurável.

    Args:
        cols: Número de colunas (pinos na direção X).
        rows: Número de linhas (pinos na direção Y).
        spacing_mm: Espaçamento centro a centro entre pinos (mm).
        profiles: Perfis de glifos carregados.
        density_min: Limiar mínimo de densidade de pixels (padrão 0,03).
        density_max: Limiar máximo de densidade de pixels (padrão 0,55).
        edge_complexity_min: Limiar mínimo de complexidade de borda (padrão 0,08).
        iou_min: Limiar mínimo de IoU para fidelidade estrutural (padrão 0,15).
        max_finger_area_mm: Dimensão máxima para modo 1-dedo em mm (padrão 25,0).
        max_multi_finger_mm: Dimensão máxima para modo multi-dedo em mm (padrão 55,0).
        seq_glyph_min: Capacidade sequencial mínima (padrão 4).

    Returns:
        ExtendedReport com análise completa.
    """
    resolution: Tuple[int, int] = (cols, rows)
    cell_w_raw, cell_h_raw = _physical_cell_size_mn(resolution, spacing_mm)

    eff_res, crop_box = _effective_resolution(profiles, resolution)
    cell_w_mm = (eff_res[0] - 1) * spacing_mm
    cell_h_mm = (eff_res[1] - 1) * spacing_mm
    max_dim   = max(cell_w_mm, cell_h_mm)

    if max_dim <= max_finger_area_mm:
        mode = "1-dedo"
        limit_mm = max_finger_area_mm
    elif max_dim <= max_multi_finger_mm:
        mode = "multi-dedo"
        limit_mm = max_multi_finger_mm
    else:
        mode = "fora-de-alcance"
        limit_mm = max_multi_finger_mm

    fits = max_dim <= limit_mm

    test_font = ImageFont.truetype(str(FONT_PATH), rows - 2)
    verdicts: List[TactileVerdict] = []

    for p in profiles:
        if p.codepoint in INTENTIONALLY_BLANK:
            verdicts.append(TactileVerdict(
                char=p.char, codepoint=p.codepoint, resolution=resolution,
                phys_size_mm=max_dim, fits_finger=fits,
                density=0.0, density_ok=False,
                iou=1.0, iou_ok=True,
                edge_complexity=0.0, complexity_ok=False,
                verdict="VAZIO",
            ))
            continue

        bm = _render_bitmap(p.char, test_font, resolution)
        if crop_box != (0, 0, 0, 0):
            bm = bm[crop_box[0]:crop_box[1] + 1, crop_box[2]:crop_box[3] + 1]
        d   = _pixel_density(bm)
        ec  = _edge_complexity(bm)
        iou = _iou(p.bitmap_ref, bm)

        density_ok    = density_min <= d <= density_max
        iou_ok        = iou >= iou_min
        complexity_ok = ec >= edge_complexity_min

        if not fits:
            verdict = "TAMANHO_GRANDE"
        elif d < density_min:
            verdict = "VAZIO"
        elif d > density_max:
            verdict = "SATURADO"
        elif not complexity_ok:
            verdict = "RASO"
        elif not iou_ok:
            verdict = "PERDA_ESTRUTURAL"
        else:
            verdict = "APTO"

        verdicts.append(TactileVerdict(
            char=p.char, codepoint=p.codepoint, resolution=resolution,
            phys_size_mm=max_dim, fits_finger=fits,
            density=d, density_ok=density_ok,
            iou=iou, iou_ok=iou_ok,
            edge_complexity=ec, complexity_ok=complexity_ok,
            verdict=verdict,
        ))

    apto  = sum(1 for v in verdicts if v.verdict == "APTO")
    blank = sum(1 for v in verdicts if v.verdict == "VAZIO")
    loss  = sum(1 for v in verdicts if v.verdict not in ("APTO", "VAZIO"))

    inner = ResolutionReport(
        resolution=resolution, phys_size_mm=max_dim, fits_finger=fits,
        total=len(verdicts), apto=apto, blank=blank, loss=loss,
        loss_chars=[v.char for v in verdicts if v.verdict not in ("APTO", "VAZIO")],
        verdicts=verdicts,
        eff_resolution=eff_res, crop_box=crop_box,
    )

    seq_cap = _sequence_capacity(cell_w_mm)
    return ExtendedReport(
        resolution=resolution, spacing_mm=spacing_mm,
        cell_w_mm=cell_w_mm, cell_h_mm=cell_h_mm,
        reading_mode=mode,
        seq_capacity=seq_cap,
        seq_in_range=seq_cap >= seq_glyph_min,
        report=inner,
    )
