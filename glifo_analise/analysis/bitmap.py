"""
Funções puras de análise de bitmap e coleta de glifos.

Inclui: renderização, densidade, complexidade de borda, IoU,
resolução efetiva, coleta de codepoints e criação de perfis.
"""
from __future__ import annotations

import pathlib
import unicodedata
from typing import Dict, List, Tuple

import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

from glifo_analise.config import (
    FONT_PATH,
    REFERENCE_RESOLUTION,
    INTENTIONALLY_BLANK,
)
from glifo_analise.models import GlyphProfile

# ---------------------------------------------------------------------------
# Cache da resolução efetiva (W×H → ((W_eff, H_eff), crop_box))
# ---------------------------------------------------------------------------
_EFF_RES_CACHE: Dict[Tuple[int, int], Tuple[Tuple[int, int], Tuple[int, int, int, int]]] = {}


def _render_bitmap(
    char: str,
    pil_font: ImageFont.FreeTypeFont,
    cell: Tuple[int, int],
) -> np.ndarray:
    """Renderiza glifo centralizado em célula `cell=(W, H)`. Retorna uint8 0/1."""
    w, h = cell
    img = Image.new("L", (w, h), 255)
    draw = ImageDraw.Draw(img)
    bb = draw.textbbox((0, 0), char, font=pil_font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x = (w - tw) // 2 - bb[0]
    y = (h - th) // 2 - bb[1]
    draw.text((x, y), char, font=pil_font, fill=0)
    return (np.array(img) < 128).astype(np.uint8)


def _pixel_density(bm: np.ndarray) -> float:
    """Proporção de pixels de tinta no bitmap."""
    return float(bm.sum()) / bm.size if bm.size > 0 else 0.0


def _edge_complexity(bm: np.ndarray) -> float:
    """
    Proporção de pixels de borda no bitmap.

    Um pixel é de borda quando difere de pelo menos um vizinho
    ortogonal (cima, baixo, esquerda, direita).
    """
    if bm.size == 0:
        return 0.0
    up    = np.roll(bm, -1, axis=0)
    down  = np.roll(bm,  1, axis=0)
    left  = np.roll(bm, -1, axis=1)
    right = np.roll(bm,  1, axis=1)
    edge = (bm != up) | (bm != down) | (bm != left) | (bm != right)
    return float(edge.sum()) / bm.size


def _iou(ref_bm: np.ndarray, test_bm: np.ndarray) -> float:
    """
    Intersection over Union entre referência redimensionada e bitmap de teste.

    A referência 64×64 é reduzida para o tamanho do bitmap de teste via
    interpolação LANCZOS + threshold.
    """
    th, tw = test_bm.shape
    ref_img = Image.fromarray((ref_bm * 255).astype(np.uint8))
    ref_scaled = ref_img.resize((tw, th), Image.LANCZOS)
    ref_arr = (np.array(ref_scaled) > 64).astype(np.uint8)

    if ref_arr.sum() == 0 and test_bm.sum() == 0:
        return 1.0
    if ref_arr.sum() == 0:
        return 0.0

    inter = float((ref_arr & test_bm).sum())
    union = float((ref_arr | test_bm).sum())
    return inter / union if union > 0 else 0.0


def _effective_resolution(
    profiles: List[GlyphProfile],
    resolution: Tuple[int, int],
    font_path: pathlib.Path = FONT_PATH,
) -> Tuple[Tuple[int, int], Tuple[int, int, int, int]]:
    """
    Calcula resolução efetiva eliminando linhas/colunas de pinos nunca ativados.

    Args:
        profiles: Perfis dos glifos.
        resolution: (W, H) declarados do display.
        font_path: Caminho para a fonte TTF.

    Returns:
        ((W_eff, H_eff), (row0, row1, col0, col1))
    """
    if resolution in _EFF_RES_CACHE:
        return _EFF_RES_CACHE[resolution]

    W, H = resolution
    font = ImageFont.truetype(str(font_path), H - 2)
    bitmaps = [
        _render_bitmap(p.char, font, resolution)
        for p in profiles
        if p.codepoint not in INTENTIONALLY_BLANK
    ]

    if not bitmaps:
        result: Tuple[Tuple[int, int], Tuple[int, int, int, int]] = (
            resolution, (0, H - 1, 0, W - 1)
        )
        _EFF_RES_CACHE[resolution] = result
        return result

    stack = np.stack(bitmaps)         # (N, H, W)
    row_any = stack.any(axis=(0, 2))  # (H,) linhas com ≥1 pixel ativo
    col_any = stack.any(axis=(0, 1))  # (W,) colunas com ≥1 pixel ativo

    active_rows = np.where(row_any)[0]
    active_cols = np.where(col_any)[0]

    if len(active_rows) == 0 or len(active_cols) == 0:
        result = (resolution, (0, H - 1, 0, W - 1))
    else:
        row0, row1 = int(active_rows[0]), int(active_rows[-1])
        col0, col1 = int(active_cols[0]), int(active_cols[-1])
        result = ((col1 - col0 + 1, row1 - row0 + 1), (row0, row1, col0, col1))

    _EFF_RES_CACHE[resolution] = result
    return result


# ---------------------------------------------------------------------------
# Coleta de glifos e criação de perfis
# ---------------------------------------------------------------------------

def _collect_mapped_codepoints(font_path: pathlib.Path) -> List[int]:
    """Retorna codepoints mapeados no cmap da fonte, filtrados para imprimíveis."""
    tt = TTFont(str(font_path))
    cmap = tt.getBestCmap()
    tt.close()
    if not cmap:
        raise ValueError("Fonte sem tabela cmap utilizável.")

    ranges = list(range(32, 127)) + list(range(160, 256)) + list(range(0x2000, 0x2070))
    result: List[int] = []
    for cp in ranges:
        if cp in cmap:
            ch = chr(cp)
            if not unicodedata.category(ch).startswith("C"):
                result.append(cp)
    return result


def _build_profiles(
    codepoints: List[int],
    font_path: pathlib.Path,
) -> List[GlyphProfile]:
    """Cria perfis de referência (64×64) para todos os glifos."""
    tt = TTFont(str(font_path))
    cmap = tt.getBestCmap()
    tt.close()

    ref_font = ImageFont.truetype(str(font_path), REFERENCE_RESOLUTION[1] - 2)

    profiles: List[GlyphProfile] = []
    for cp in codepoints:
        ch = chr(cp)
        raw = cmap.get(cp, cp)
        glyph_name = raw if isinstance(raw, str) else str(raw)

        if cp in INTENTIONALLY_BLANK:
            profiles.append(GlyphProfile(
                char=ch, codepoint=cp, glyph_name=glyph_name,
                density=0.0, edge_complexity=0.0,
                bitmap_ref=np.zeros(REFERENCE_RESOLUTION[::-1], dtype=np.uint8),
            ))
            continue

        bm = _render_bitmap(ch, ref_font, REFERENCE_RESOLUTION)
        profiles.append(GlyphProfile(
            char=ch, codepoint=cp, glyph_name=glyph_name,
            density=_pixel_density(bm),
            edge_complexity=_edge_complexity(bm),
            bitmap_ref=bm,
        ))

    return profiles
