"""
Grade visual de diagnóstico com bordas coloridas por veredicto tátil.
"""
from __future__ import annotations

import pathlib
from typing import List

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from glifo_analise.config import (
    FONT_PATH,
    OUTPUT_DIR,
    PIN_SPACING_MM,
    INTENTIONALLY_BLANK,
)
from glifo_analise.models import GlyphProfile, ResolutionReport
from glifo_analise.analysis.bitmap import _render_bitmap

# ---------------------------------------------------------------------------
# Mapa de cores por veredicto
# ---------------------------------------------------------------------------
_VERDICT_COLOR = {
    "APTO":             (60,  160,  60),
    "VAZIO":            (160, 160, 160),
    "SATURADO":         (220, 100,   0),
    "RASO":             (180, 140,   0),
    "PERDA_ESTRUTURAL": (180,  40,  40),
    "TAMANHO_GRANDE":   ( 80,  80, 200),
}


def _system_font_small(size: int = 9) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Retorna fonte de sistema pequena para rótulos de codepoint."""
    from glifo_analise.config import SYSTEM_FONT_CANDIDATES
    for path_str in SYSTEM_FONT_CANDIDATES:
        p = pathlib.Path(path_str)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                continue
    return ImageFont.load_default()


def _save_grid(
    report: ResolutionReport,
    profiles: List[GlyphProfile],
    spacing_mm: float = PIN_SPACING_MM,
    out_dir: pathlib.Path | None = None,
) -> pathlib.Path:
    """
    Gera grade visual PNG com bordas coloridas por veredicto tátil.

    Args:
        report: Resultado da análise de resolução.
        profiles: Perfis de glifos.
        spacing_mm: Espaçamento utilizado (apenas para nome do arquivo).
        out_dir: Diretório de saída (padrão: OUTPUT_DIR).

    Returns:
        Caminho do arquivo PNG criado.
    """
    dest = out_dir if out_dir is not None else OUTPUT_DIR
    dest.mkdir(parents=True, exist_ok=True)

    res = report.resolution
    eff_res = report.eff_resolution if report.eff_resolution != (0, 0) else res
    w, h    = eff_res
    crop_box = report.crop_box
    v_map    = {v.char: v for v in report.verdicts}

    cols_grid = 20
    rows_grid = (len(profiles) + cols_grid - 1) // cols_grid
    scale     = max(1, 32 // max(w, h))
    cw, ch_px = w * scale, h * scale
    border    = 2
    cell_w    = cw + border * 2 + 2
    cell_h    = ch_px + border * 2 + 10

    canvas = Image.new("RGB", (cols_grid * cell_w, rows_grid * cell_h + 22), (240, 240, 240))
    dc     = ImageDraw.Draw(canvas)
    lbl    = _system_font_small(9)

    test_font = ImageFont.truetype(str(FONT_PATH), res[1] - 2)

    for idx, p in enumerate(profiles):
        col = idx % cols_grid
        row = idx // cols_grid
        x0  = col * cell_w
        y0  = row * cell_h

        if p.codepoint in INTENTIONALLY_BLANK:
            bm = np.zeros((h, w), dtype=np.uint8)
        else:
            bm = _render_bitmap(p.char, test_font, res)
            if crop_box != (0, 0, 0, 0):
                bm = bm[crop_box[0]:crop_box[1] + 1, crop_box[2]:crop_box[3] + 1]

        gimg = Image.fromarray(((1 - bm) * 255).astype(np.uint8))
        gimg = gimg.resize((cw, ch_px), Image.NEAREST).convert("RGB")

        v    = v_map.get(p.char)
        bclr = _VERDICT_COLOR.get(v.verdict if v else "VAZIO", (160, 160, 160))
        canvas.paste(gimg, (x0 + border, y0 + border))
        dc.rectangle(
            [x0, y0, x0 + cw + border * 2, y0 + ch_px + border * 2],
            outline=bclr, width=2,
        )
        dc.text(
            (x0 + 1, y0 + ch_px + border * 2 + 1),
            f"U+{p.codepoint:04X}", font=lbl, fill=(80, 80, 80),
        )

    # Legenda
    ly, lx = rows_grid * cell_h + 4, 4
    for label, color in _VERDICT_COLOR.items():
        dc.rectangle([lx, ly, lx + 10, ly + 10], fill=color)
        dc.text((lx + 12, ly), label, font=lbl, fill=(40, 40, 40))
        lx += 105

    out = dest / f"tatil_{res[0]}x{res[1]}_{spacing_mm:.1f}mm.png"
    canvas.save(str(out))
    return out
