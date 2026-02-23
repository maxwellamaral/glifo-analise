"""
Geração de modelo 3D tátil (STL / 3MF) para impressão de protótipo.
"""
from __future__ import annotations

import pathlib
from typing import List, Tuple

import numpy as np
from PIL import ImageFont

from glifo_analise.config import (
    FONT_PATH,
    OUTPUT_DIR,
    PIN_DIAMETER_MM,
    GAP_BETWEEN_CELLS_MM,
    MAX_FINGER_AREA_MM,
    MAX_MULTI_FINGER_MM,
    INTENTIONALLY_BLANK,
)
from glifo_analise.models import GlyphProfile
from glifo_analise.analysis.bitmap import _effective_resolution, _render_bitmap
from glifo_analise.output.preview import _generate_tactile_preview_png_full

DEFAULT_TACTILE_SEQUENCE = "tqlDà"


def _generate_tactile_3d(
    sequence: str,
    candidate: dict,
    profiles: List[GlyphProfile],
    fmt: str = "3mf",
    pin_height_mm: float = 0.6,
    base_thickness_mm: float = 2.0,
    margin_mm: float = 1.5,
    full_test: bool = False,
    out_dir: pathlib.Path | None = None,
) -> pathlib.Path:
    """
    Gera modelo 3D de tira tátil com os glifos da sequência fornecida.

    Args:
        sequence: String ELIS a renderizar (ignorado se *full_test=True*).
        candidate: Dict com 'resolution' e 'spacing_mm'.
        profiles: Perfis dos glifos.
        fmt: 'stl' ou '3mf'.
        pin_height_mm: Altura dos pinos acima da base.
        base_thickness_mm: Espessura da placa-base.
        margin_mm: Margem lateral ao redor da tira.
        full_test: Se True, gera célula com todos os pinos levantados.
        out_dir: Diretório de saída (padrão: OUTPUT_DIR).

    Returns:
        Caminho do arquivo 3D gerado.
    """
    try:
        import trimesh  # type: ignore[import]
    except ImportError as exc:
        raise RuntimeError("trimesh não encontrado. Execute: uv add trimesh") from exc

    dest = out_dir if out_dir is not None else OUTPUT_DIR
    dest.mkdir(parents=True, exist_ok=True)

    cols, rows = tuple(candidate["resolution"])
    spacing_mm: float = candidate["spacing_mm"]
    resolution: Tuple[int, int] = (cols, rows)

    eff_res, crop_box = _effective_resolution(profiles, resolution)
    eff_cols, eff_rows = eff_res

    if full_test:
        render_cols, render_rows = cols, rows
    else:
        render_cols, render_rows = eff_cols, eff_rows

    cell_w_mm = (render_cols - 1) * spacing_mm
    cell_h_mm = (render_rows - 1) * spacing_mm

    if full_test:
        bitmaps: List[np.ndarray] = [np.ones((render_rows, render_cols), dtype=np.uint8)]
    else:
        font = ImageFont.truetype(str(FONT_PATH), rows - 2)
        bitmaps = []
        for ch in sequence:
            cp = ord(ch)
            if cp in INTENTIONALLY_BLANK:
                bitmaps.append(np.zeros((eff_rows, eff_cols), dtype=np.uint8))
            else:
                bm = _render_bitmap(ch, font, resolution)
                if crop_box != (0, 0, 0, 0):
                    bm = bm[crop_box[0]:crop_box[1] + 1, crop_box[2]:crop_box[3] + 1]
                bitmaps.append(bm)

    n = len(bitmaps)
    total_w = n * cell_w_mm + max(0, n - 1) * GAP_BETWEEN_CELLS_MM
    plate_w  = total_w + 2 * margin_mm
    plate_h  = cell_h_mm + 2 * margin_mm

    meshes: List[object] = []

    base = trimesh.creation.box([plate_w, plate_h, base_thickness_mm])
    base.apply_translation([plate_w / 2, plate_h / 2, base_thickness_mm / 2])
    meshes.append(base)

    pin_r = PIN_DIAMETER_MM / 2
    for g_idx, bm in enumerate(bitmaps):
        bm_rows, bm_cols = bm.shape
        x_off = margin_mm + g_idx * (cell_w_mm + GAP_BETWEEN_CELLS_MM)
        for r_idx in range(bm_rows):
            for c_idx in range(bm_cols):
                if not bm[r_idx, c_idx]:
                    continue
                cx = x_off + c_idx * spacing_mm
                cy = margin_mm + (bm_rows - 1 - r_idx) * spacing_mm
                cz = base_thickness_mm + pin_height_mm / 2
                pin = trimesh.creation.cylinder(radius=pin_r, height=pin_height_mm, sections=16)
                pin.apply_translation([cx, cy, cz])
                meshes.append(pin)

    combined = trimesh.util.concatenate(meshes)

    if full_test:
        fname_stem = f"tatil_3d_{cols}x{rows}_{spacing_mm:.1f}mm_TESTE_COMPLETO"
    else:
        seq_safe = "".join(c if c.isalnum() else f"U{ord(c):04X}" for c in sequence)
        fname_stem = f"tatil_3d_{cols}x{rows}_{spacing_mm:.1f}mm_{seq_safe}"

    out = dest / f"{fname_stem}.{fmt}"
    combined.export(str(out))

    # Preview PNG parceiro
    _w, _h = cell_w_mm, cell_h_mm
    _mode = (
        "1-dedo"
        if _w <= MAX_FINGER_AREA_MM and _h <= MAX_FINGER_AREA_MM
        else "multi-dedo"
        if max(_w, _h) <= MAX_MULTI_FINGER_MM
        else "fora-de-alcance"
    )
    _generate_tactile_preview_png_full(
        bitmaps=bitmaps,
        candidate=candidate,
        render_shape=(render_rows, render_cols),
        reading_mode=_mode,
        full_test=full_test,
        fname_stem=fname_stem,
        out_dir=dest,
        margin_mm=margin_mm,
        gap_mm=GAP_BETWEEN_CELLS_MM,
        sequence=sequence,
    )

    return out
