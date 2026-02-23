"""
Geração de preview PNG (vista superior) da tira tátil.
"""
from __future__ import annotations

import pathlib
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from glifo_analise.config import (
    OUTPUT_DIR,
    PIN_DIAMETER_MM,
    GAP_BETWEEN_CELLS_MM,
    MONO_FONT_CANDIDATES,
)


def _generate_tactile_preview_png(
    bitmap: np.ndarray,
    candidate: dict,
    out_dir: pathlib.Path,
    label: str,
    px_per_mm: float = 22.0,
) -> pathlib.Path:
    """
    Gera PNG de vista superior de UMA célula tátil com painel de dados técnicos.

    Interface simplificada — aceita um único bitmap (array 2-D 0/1), o dict
    do candidato, o diretório de saída e um rótulo textual para o nome do arquivo.

    Args:
        bitmap: Array NumPy (rows, cols) com 0=pino baixo / 1=pino levantado.
        candidate: Dict contendo pelo menos 'spacing_mm', 'resolution' (ou 'cols'/'rows'),
                   'reading_mode', 'seq_capacity'.
        out_dir: Diretório onde o arquivo PNG será gravado.
        label: Rótulo textual (usado no nome do arquivo e no título da imagem).
        px_per_mm: Escala em pixels/mm.

    Returns:
        Caminho absoluto do arquivo PNG criado.
    """
    # ── Parâmetros do candidato ───────────────────────────────────────────────
    spacing_mm: float = candidate.get("spacing_mm", 2.5)
    resolution = candidate.get("resolution", (bitmap.shape[1], bitmap.shape[0]))
    cols, rows_decl = resolution
    reading_mode: str = candidate.get("reading_mode", "1-dedo")

    bm_rows, bm_cols = bitmap.shape
    cell_w_mm = (bm_cols - 1) * spacing_mm if bm_cols > 1 else spacing_mm
    cell_h_mm = (bm_rows - 1) * spacing_mm if bm_rows > 1 else spacing_mm
    gap_pins_mm = spacing_mm - PIN_DIAMETER_MM

    margin_mm: float = 1.5
    total_strip_w_mm = cell_w_mm + 2 * margin_mm
    total_strip_h_mm = cell_h_mm + 2 * margin_mm

    def px(mm: float) -> int:
        return int(round(mm * px_per_mm))

    strip_w_px = px(total_strip_w_mm)
    strip_h_px = px(total_strip_h_mm)
    pin_r_px   = max(2, int(round(PIN_DIAMETER_MM / 2 * px_per_mm)))

    # ── Fonte mono para painel ────────────────────────────────────────────────
    font_sz = 15
    info_font: ImageFont.FreeTypeFont | ImageFont.ImageFont = ImageFont.load_default()
    for fp in MONO_FONT_CANDIDATES:
        try:
            info_font = ImageFont.truetype(fp, font_sz)
            break
        except OSError:
            pass

    info_lines = [
        f"  Resolução declarada : {cols}×{rows_decl}",
        f"  Resolução de render  : {bm_cols}×{bm_rows}",
        f"  Espaç. (pitch)       : {spacing_mm:.1f} mm",
        f"  Gap entre pinos      : {gap_pins_mm:.1f} mm",
        f"  Ø pino               : {PIN_DIAMETER_MM:.1f} mm",
        f"  Cell W               : {cell_w_mm:.1f} mm",
        f"  Cell H               : {cell_h_mm:.1f} mm",
        f"  Modo de leitura      : {reading_mode}",
        f"  Rótulo               : {label}",
    ]

    line_h      = font_sz + 6
    panel_pad   = 12
    panel_h     = len(info_lines) * line_h + panel_pad * 2
    title_h     = font_sz + panel_pad * 2
    total_h     = title_h + strip_h_px + panel_h
    total_w     = max(strip_w_px, 400)

    # ── Montagem da imagem ────────────────────────────────────────────────────
    img  = Image.new("RGB", (total_w, total_h), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)

    # Título
    draw.rectangle([0, 0, total_w, title_h], fill=(45, 45, 60))
    draw.text((panel_pad, panel_pad), label, fill=(220, 220, 255), font=info_font)

    # Placa base
    plate_y0 = title_h
    draw.rectangle(
        [0, plate_y0, strip_w_px - 1, plate_y0 + strip_h_px - 1],
        fill=(210, 185, 140),
    )

    # Pinos
    x_off_mm = margin_mm
    for r_idx in range(bm_rows):
        for c_idx in range(bm_cols):
            cx  = px(x_off_mm + c_idx * spacing_mm)
            cy  = plate_y0 + px(margin_mm + r_idx * spacing_mm)
            bbox = [cx - pin_r_px, cy - pin_r_px, cx + pin_r_px, cy + pin_r_px]
            if bitmap[r_idx, c_idx]:
                draw.ellipse(bbox, fill=(50, 50, 50))
                hl = max(1, pin_r_px // 3)
                draw.ellipse(
                    [cx - hl, cy - hl, cx + hl, cy + hl],
                    fill=(130, 130, 130),
                )
            else:
                draw.ellipse(bbox, outline=(170, 145, 100), width=1)

    # Painel técnico
    panel_y0 = title_h + strip_h_px
    draw.rectangle([0, panel_y0, total_w - 1, total_h - 1], fill=(28, 28, 38))
    draw.line([0, panel_y0, total_w, panel_y0], fill=(80, 80, 120), width=2)
    for i, line in enumerate(info_lines):
        draw.text(
            (0, panel_y0 + panel_pad + i * line_h),
            line, fill=(180, 230, 180), font=info_font,
        )

    # ── Salvar ───────────────────────────────────────────────────────────────
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in label)
    cols_r, rows_r = bm_cols, bm_rows
    out = out_dir / f"tatil_3d_{cols_r}x{rows_r}_{spacing_mm:.1f}mm_{safe_label}_preview.png"
    img.save(str(out), dpi=(int(px_per_mm * 25.4), int(px_per_mm * 25.4)))
    return out


def _generate_tactile_preview_png_full(
    bitmaps: List[np.ndarray],
    candidate: dict,
    render_shape: Tuple[int, int],
    reading_mode: str,
    full_test: bool,
    fname_stem: str,
    out_dir: Optional[pathlib.Path] = None,
    margin_mm: float = 1.5,
    gap_mm: float = GAP_BETWEEN_CELLS_MM,
    sequence: str = "",
    px_per_mm: float = 22.0,
) -> pathlib.Path:
    """
    Versão completa (interna) — gera preview para uma tira multi-glifo.

    Usada por output/model3d.py depois de gerar o arquivo 3D.
    """
    dest = out_dir if out_dir is not None else OUTPUT_DIR
    dest.mkdir(parents=True, exist_ok=True)

    cols, rows = candidate["resolution"]
    spacing_mm: float = candidate["spacing_mm"]
    render_rows, render_cols = render_shape
    n = len(bitmaps)

    cell_w_mm = (render_cols - 1) * spacing_mm
    cell_h_mm = (render_rows - 1) * spacing_mm
    gap_pins_mm = spacing_mm - PIN_DIAMETER_MM

    total_strip_w_mm = n * cell_w_mm + max(0, n - 1) * gap_mm + 2 * margin_mm
    total_strip_h_mm = cell_h_mm + 2 * margin_mm

    def px(mm: float) -> int:
        return int(round(mm * px_per_mm))

    strip_w_px = px(total_strip_w_mm)
    strip_h_px = px(total_strip_h_mm)
    pin_r_px   = max(2, int(round(PIN_DIAMETER_MM / 2 * px_per_mm)))

    font_sz = 15
    info_font: ImageFont.FreeTypeFont | ImageFont.ImageFont = ImageFont.load_default()
    for fp in MONO_FONT_CANDIDATES:
        try:
            info_font = ImageFont.truetype(fp, font_sz)
            break
        except OSError:
            pass

    render_label = f"{'TESTE COMPLETO' if full_test else repr(sequence)}"
    info_lines = [
        f"  Resolução declarada : {cols}×{rows}",
        f"  Resolução de render  : {render_cols}×{render_rows}",
        f"  Espaç. (pitch)       : {spacing_mm:.1f} mm",
        f"  Gap entre pinos      : {gap_pins_mm:.1f} mm",
        f"  Ø pino               : {PIN_DIAMETER_MM:.1f} mm",
        f"  Cell W               : {cell_w_mm:.1f} mm",
        f"  Cell H               : {cell_h_mm:.1f} mm",
        f"  Modo de leitura      : {reading_mode}",
        f"  Render               : {render_label}",
        f"  Glifos na tira       : {n}",
        f"  Escala               : 1 px = {1/px_per_mm:.3f} mm",
    ]

    line_h      = font_sz + 6
    panel_pad   = 12
    panel_h     = len(info_lines) * line_h + panel_pad * 2
    title_h     = font_sz + panel_pad * 2
    total_h     = title_h + strip_h_px + panel_h
    total_w     = max(strip_w_px, 520)

    img  = Image.new("RGB", (total_w, total_h), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, total_w, title_h], fill=(45, 45, 60))
    draw.text((panel_pad, panel_pad), fname_stem, fill=(220, 220, 255), font=info_font)

    plate_y0 = title_h
    draw.rectangle(
        [0, plate_y0, strip_w_px - 1, plate_y0 + strip_h_px - 1],
        fill=(210, 185, 140),
    )

    for g_idx in range(n):
        x_off_mm = margin_mm + g_idx * (cell_w_mm + gap_mm)
        half = spacing_mm * 0.45
        bx0  = px(x_off_mm - half)
        bx1  = px(x_off_mm + cell_w_mm + half)
        by0  = plate_y0 + px(margin_mm - half)
        by1  = plate_y0 + px(margin_mm + cell_h_mm + half)
        draw.rectangle([bx0, by0, bx1, by1], outline=(160, 130, 80), width=1)

    for g_idx, bm in enumerate(bitmaps):
        bm_r, bm_c = bm.shape
        x_off_mm = margin_mm + g_idx * (cell_w_mm + gap_mm)
        for r_idx in range(bm_r):
            for c_idx in range(bm_c):
                cx  = px(x_off_mm + c_idx * spacing_mm)
                cy  = plate_y0 + px(margin_mm + r_idx * spacing_mm)
                bbox = [cx - pin_r_px, cy - pin_r_px, cx + pin_r_px, cy + pin_r_px]
                if bm[r_idx, c_idx]:
                    draw.ellipse(bbox, fill=(50, 50, 50))
                    hl = max(1, pin_r_px // 3)
                    draw.ellipse([cx - hl, cy - hl, cx + hl, cy + hl], fill=(130, 130, 130))
                else:
                    draw.ellipse(bbox, outline=(170, 145, 100), width=1)

    panel_y0 = title_h + strip_h_px
    draw.rectangle([0, panel_y0, total_w - 1, total_h - 1], fill=(28, 28, 38))
    draw.line([0, panel_y0, total_w, panel_y0], fill=(80, 80, 120), width=2)
    for i, line in enumerate(info_lines):
        draw.text(
            (0, panel_y0 + panel_pad + i * line_h),
            line, fill=(180, 230, 180), font=info_font,
        )

    out_png = dest / f"{fname_stem}_preview.png"
    img.save(str(out_png), dpi=(int(px_per_mm * 25.4), int(px_per_mm * 25.4)))
    return out_png
