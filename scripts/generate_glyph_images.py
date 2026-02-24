"""
Gera imagens PNG dos glifos ELIS para uso no README.md.

Renderiza cada glifo com a fonte elis.ttf usando Pillow, aplica auto-crop
com margem e salva em docs/glyphs/ com fundo branco.

Uso:
    uv run python scripts/generate_glyph_images.py
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
ROOT = pathlib.Path(__file__).parent.parent
FONT_PATH = ROOT / "elis.ttf"
OUT_DIR = ROOT / "docs" / "glyphs"

# ---------------------------------------------------------------------------
# Parâmetros de renderização
# ---------------------------------------------------------------------------
FONT_SIZE = 160          # tamanho de render interno (px)
CANVAS_SIZE = 256        # canvas quadrado (px)
PADDING = 12             # margem ao redor do glifo no crop (px)
FINAL_SIZE = 96          # tamanho final exportado (px) — escalado após crop

# ---------------------------------------------------------------------------
# Glifos que aparecem explicitamente no README
# ---------------------------------------------------------------------------
GLYPHS_RESTRICTION = [
    ("i", "U+0069", "minuscula_i"),
    ("r", "U+0072", "minuscula_r"),
    ("s", "U+0073", "minuscula_s"),
]

GLYPHS_VAZIO = [
    ("b", "U+0062", "minuscula_b"),
    ("k", "U+006B", "minuscula_k"),
    ("m", "U+006D", "minuscula_m"),
    ("n", "U+006E", "minuscula_n"),
    ("q", "U+0071", "minuscula_q"),
]

# Todos os glifos referenciados no README — agrupa os dois grupos
ALL_GLYPHS = GLYPHS_RESTRICTION + GLYPHS_VAZIO


def render_glyph(char: str, font: ImageFont.FreeTypeFont) -> Image.Image:
    """
    Renderiza um glifo centralizado em canvas branco e retorna imagem
    com fundo branco, auto-cropada com PADDING de margem.
    """
    # Renderiza em canvas grande
    img = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Bounding box do texto
    bb = draw.textbbox((0, 0), char, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]

    # Centraliza
    x = (CANVAS_SIZE - tw) // 2 - bb[0]
    y = (CANVAS_SIZE - th) // 2 - bb[1]
    draw.text((x, y), char, font=font, fill=(0, 0, 0, 255))

    # Auto-crop baseado em pixels escuros
    arr = np.array(img.convert("L"))
    # Encontra linhas/colunas com conteúdo
    rows = np.any(arr < 200, axis=1)
    cols = np.any(arr < 200, axis=0)

    if not rows.any():
        # Glifo vazio — retorna canvas pequeno branco
        return Image.new("RGBA", (FINAL_SIZE, FINAL_SIZE), (255, 255, 255, 255))

    r_min, r_max = np.where(rows)[0][[0, -1]]
    c_min, c_max = np.where(cols)[0][[0, -1]]

    # Aplica padding com clamp
    r_min = max(0, r_min - PADDING)
    r_max = min(CANVAS_SIZE - 1, r_max + PADDING)
    c_min = max(0, c_min - PADDING)
    c_max = min(CANVAS_SIZE - 1, c_max + PADDING)

    cropped = img.crop((c_min, r_min, c_max + 1, r_max + 1))

    # Torna quadrado para uniformidade nas tabelas
    w, h = cropped.size
    side = max(w, h) + PADDING * 2
    square = Image.new("RGBA", (side, side), (255, 255, 255, 255))
    ox = (side - w) // 2
    oy = (side - h) // 2
    square.paste(cropped, (ox, oy))

    return square.resize((FINAL_SIZE, FINAL_SIZE), Image.LANCZOS)


def main() -> None:
    if not FONT_PATH.exists():
        print(f"[ERRO] Fonte não encontrada: {FONT_PATH}", file=sys.stderr)
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    font = ImageFont.truetype(str(FONT_PATH), FONT_SIZE)

    generated: list[tuple[str, str, pathlib.Path]] = []

    for char, codepoint, slug in ALL_GLYPHS:
        img = render_glyph(char, font)
        out_path = OUT_DIR / f"{slug}.png"
        img.save(out_path, "PNG")
        generated.append((char, codepoint, out_path))
        print(f"  ✓ {codepoint}  {char!r}  →  {out_path.relative_to(ROOT)}")

    print(f"\n{len(generated)} imagens salvas em {OUT_DIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
