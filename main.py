"""
Análise de viabilidade tátil — fonte ELIS (Escrita das Línguas de Sinais).

Contexto:
    A fonte elis.ttf codifica sinais da Língua de Sinais usando codepoints
    Unicode Latin como chaves de acesso. Cada glifo representa um sinal
    gráfico da notação ELIS, NÃO um caractere de idioma convencional.

Objetivo:
    Determinar quais glifos são reproduzíveis em uma matriz de pinos táteis
    para leitura por pessoas cegas, respeitando os limiares psicofísicos
    de discriminação tátil dos dedos.

Requisitos psicofísicos incorporados (base: ISO 11548-2 / literatura tátil):
    - Espaçamento mínimo entre pinos: 2,5 mm (limiar de dois pontos no dedo)
    - Diâmetro do pino: 1,5 mm
    - Gap mínimo entre pinos: >= 1,0 mm
    - Tamanho máximo para leitura com um dedo:  <= 25 mm x 25 mm
    - Densidade mínima de pinos ativos: 3%  (marca perceptível ao tato)
    - Densidade máxima de pinos ativos: 55% (acima disso = "blob" indistinto)
    - Complexidade estrutural mínima (epsilon): 8% de pixels de borda
      (sinais com pouca variação interna são confundidos ao tato)
"""

from __future__ import annotations

import pathlib
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import json

import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Configurações gerais
# ---------------------------------------------------------------------------
FONT_PATH = pathlib.Path(__file__).parent / "elis.ttf"
OUTPUT_DIR = pathlib.Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Arquivo de persistência da lista de candidatos viáveis gerada pelo último processamento
CANDIDATES_FILE: pathlib.Path = OUTPUT_DIR / "candidatos_viaveis.json"

# Resoluções candidatas (W×H) — número de pinos na matriz
CANDIDATE_RESOLUTIONS: List[Tuple[int, int]] = [(10, 10), (15, 15), (20, 20)]

# Resolução de referência alta para análise estrutural
REFERENCE_RESOLUTION: Tuple[int, int] = (64, 64)

# ---------------------------------------------------------------------------
# Parâmetros psicofísicos (ISO 11548-2 e literatura de percepção tátil)
# ---------------------------------------------------------------------------
PIN_SPACING_MM: float = 2.5       # espaçamento centro a centro (mm)
PIN_DIAMETER_MM: float = 1.5      # diâmetro do pino ativo (mm)
MAX_FINGER_AREA_MM: float = 25.0  # largura máxima legível com 1 dedo (mm)

# Limiares de densidade de pixels verificados na resolução de teste
DENSITY_MIN: float = 0.03   # 3%  — marca tátil mínima perceptível
DENSITY_MAX: float = 0.55   # 55% — saturação: forma indiferenciada ao tato

# Limiar de complexidade de borda
EDGE_COMPLEXITY_MIN: float = 0.08  # 8% de pixels na fronteira tinta/fundo

# Codepoints intencionalmente sem forma visual
INTENTIONALLY_BLANK: set[int] = {
    0x0020,  # SPACE
    0x00A0,  # NO-BREAK SPACE
    0x200B, 0x200C, 0x200D, 0xFEFF,
}

# ---------------------------------------------------------------------------
# Grupos de glifos ELIS (mapeados sobre teclado padrão)
# ---------------------------------------------------------------------------
GLYPH_GROUPS: Dict[str, Tuple[int, ...]] = {
    "Maiusculas (A-Z)":              tuple(range(0x0041, 0x005B)),
    "Minusculas (a-z)":              tuple(range(0x0061, 0x007B)),
    "Digitos (0-9)":                 tuple(range(0x0030, 0x003A)),
    "Pontuacao/Simbolos basicos":    (
        0x0021,0x0022,0x0023,0x0024,0x0025,0x0026,0x0027,
        0x0028,0x0029,0x002A,0x002B,0x002C,0x002D,0x002E,
        0x002F,0x003A,0x003B,0x003C,0x003E,0x003F,0x0040,
        0x005C,0x005F,
    ),
    "Acentuados / Latin-1":          tuple(range(0x00A0, 0x0100)),
}

# ---------------------------------------------------------------------------
# Extensão: leitura multi-dedo, varrimento sequencial e resolucoes M×N
# ---------------------------------------------------------------------------

# Varredura de espaçamentos (mm) — do mínimo normativo ao máximo ergonômico
PIN_SPACING_CANDIDATES: List[float] = [2.5, 3.0, 3.5]

# Limite físico para glifo legível com múltiplos dedos (~3 dedos lado a lado)
MAX_MULTI_FINGER_MM: float = 55.0

# Envergadura da mão adulta para leitura sequencial (indicador → mindinho)
HAND_SPAN_MM: float = 180.0

# Folga física entre células adjacentes na tira sequencial
GAP_BETWEEN_CELLS_MM: float = 3.0

# Faixa desejada de glifos por tira sequencial
SEQ_GLYPH_MIN: int = 4
SEQ_GLYPH_MAX: int = 6

# Cobertura mínima para classificar um candidato como "econômico" (impressão 3D)
MIN_COVERAGE_ECONOMY: float = 95.0

# Razão mínima espaçamento/diâmetro do pino (ISO 11548-2 §6.3: gap >= 1,0 mm)
ISO_MIN_GAP_MM: float = PIN_SPACING_MM - PIN_DIAMETER_MM  # 2,5 - 1,5 = 1,0 mm

# Proporção máxima admissível entre os eixos da célula (relação de aspecto)
MAX_CELL_ASPECT_RATIO: float = 2.5

# Resoluções assimétricas (M colunas x N linhas) a ser testadas
ASYMMETRIC_RESOLUTIONS: List[Tuple[int, int]] = [
    (8,  8),
    (8, 10), (10,  8),
    (8, 12), (12,  8),
    (8, 15), (15,  8),
    (8, 16), (16,  8),
    (10, 12), (12, 10),
    (10, 15), (15, 10),
    (12, 15), (15, 12),
    (13, 13),
    (13, 16), (16, 13),
]


# ---------------------------------------------------------------------------
# Estruturas de dados
# ---------------------------------------------------------------------------
@dataclass
class GlyphProfile:
    """Perfil de um glifo extraído na resolução de referência."""
    char: str
    codepoint: int
    glyph_name: str
    density: float           # proporcao de pixels de tinta (rho)
    edge_complexity: float   # proporcao de pixels de borda (epsilon)
    bitmap_ref: np.ndarray   # bitmap 64x64 de referencia


@dataclass
class TactileVerdict:
    """Veredicto tatil de um glifo para uma determinada resolucao matricial."""
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
    """Sumario por resolucao."""
    resolution: Tuple[int, int]
    phys_size_mm: float
    fits_finger: bool
    total: int
    apto: int
    blank: int
    loss: int
    loss_chars: List[str] = field(default_factory=list)
    verdicts: List[TactileVerdict] = field(default_factory=list)
    eff_resolution: Tuple[int, int] = (0, 0)          # pinos efetivos após corte
    crop_box: Tuple[int, int, int, int] = (0, 0, 0, 0)  # (row0, row1, col0, col1)

    @property
    def coverage_pct(self) -> float:
        usable = self.total - self.blank
        return 100.0 * self.apto / usable if usable else 0.0


@dataclass
class ExtendedReport:
    """Resultado da análise estendida para um par (resolução, espaçamento)."""
    resolution: Tuple[int, int]   # (M colunas, N linhas)
    spacing_mm: float             # espaçamento centro a centro dos pinos (mm)
    cell_w_mm: float              # largura física da célula (mm)
    cell_h_mm: float              # altura física da célula (mm)
    reading_mode: str             # "1-dedo" | "multi-dedo" | "fora-de-alcance"
    seq_capacity: int             # K máximo de glifos na tira dentro de HAND_SPAN_MM
    seq_in_range: bool            # True se seq_capacity >= SEQ_GLYPH_MIN
    report: ResolutionReport      # análise psicofísica completa dos glifos


# ---------------------------------------------------------------------------
# Fonte do sistema para legendas e rótulos nas imagens de diagnóstico
# ---------------------------------------------------------------------------

# Cache de resolução efetiva: keyed by (W, H) → ((W_eff, H_eff), (row0, row1, col0, col1))
_EFF_RES_CACHE: Dict[Tuple[int, int], Tuple[Tuple[int, int], Tuple[int, int, int, int]]] = {}

# Candidatos em ordem de preferência: Arial → Times → Liberation → DejaVu → FreeSans
_SYSTEM_FONT_CANDIDATES: List[str] = [
    # Arial (msttcorefonts ou wine-fonts)
    "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf",
    "/usr/share/fonts/truetype/arial.ttf",
    "/usr/share/fonts/arial.ttf",
    # Times New Roman
    "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf",
    "/usr/share/fonts/truetype/times.ttf",
    # Liberation Sans (metricamente idêntico ao Arial — padrão Ubuntu/Debian)
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
    # Liberation Serif (metricamente idêntico ao Times)
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    # DejaVu Sans (fallback universal)
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    # FreeSans / FreeMono (fontes GNU)
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/usr/share/fonts/freefont/FreeSans.ttf",
]


def _system_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Retorna a primeira fonte de sistema disponível (Arial ou equivalente)."""
    for path in _SYSTEM_FONT_CANDIDATES:
        candidate = pathlib.Path(path)
        if candidate.exists():
            try:
                return ImageFont.truetype(str(candidate), size)
            except Exception:
                continue
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Resolucao efetiva: elimina pinos mortos (linhas/colunas nunca ativadas)
# ---------------------------------------------------------------------------

def _effective_resolution(
    profiles: List["GlyphProfile"],
    resolution: Tuple[int, int],
) -> Tuple[Tuple[int, int], Tuple[int, int, int, int]]:
    """
    Calcula a resolução efetiva eliminando linhas/colunas de pinos nunca ativados.

    Renderiza todos os glifos não-brancos na resolucao declarada e faz a uniao
    dos pixels ativos. A caixa delimitadora resultante define quais pinos são
    realmente necessários.

    Returns:
        (W_eff, H_eff): dimensões efetivas em pinos (colunas × linhas ativas).
        (row0, row1, col0, col1): índices de recorte no bitmap declarado.

    Usa _EFF_RES_CACHE para evitar re-renderização nas 60 chamadas da análise
    estendida.
    """
    if resolution in _EFF_RES_CACHE:
        return _EFF_RES_CACHE[resolution]

    W, H = resolution
    font = ImageFont.truetype(str(FONT_PATH), H - 2)
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

    stack = np.stack(bitmaps)          # (N, H, W)
    row_any = stack.any(axis=(0, 2))   # (H,) — linhas com pelo menos 1 pixel ativo
    col_any = stack.any(axis=(0, 1))   # (W,) — colunas com pelo menos 1 pixel ativo

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
# Funcoes de analise de bitmap
# ---------------------------------------------------------------------------

def _render_bitmap(
    char: str,
    pil_font: ImageFont.FreeTypeFont,
    cell: Tuple[int, int],
) -> np.ndarray:
    """Renderiza glifo centralizado em celula cell=(W,H). Retorna array uint8 0/1."""
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
    """Proporcao de pixels de tinta no bitmap."""
    return float(bm.sum()) / bm.size if bm.size > 0 else 0.0


def _edge_complexity(bm: np.ndarray) -> float:
    """
    Proporcao de pixels de borda no bitmap.

    Um pixel e considerado 'de borda' se seu valor difere de pelo menos
    um dos quatro vizinhos (cima, baixo, esquerda, direita).
    Mede a riqueza de contornos — mapeia para informacao tatil discriminavel.
    """
    if bm.size == 0:
        return 0.0
    up    = np.roll(bm, -1, axis=0)
    down  = np.roll(bm,  1, axis=0)
    left  = np.roll(bm, -1, axis=1)
    right = np.roll(bm,  1, axis=1)
    edge = ((bm != up) | (bm != down) | (bm != left) | (bm != right))
    return float(edge.sum()) / bm.size


def _iou(ref_bm: np.ndarray, test_bm: np.ndarray) -> float:
    """
    Intersection over Union entre referencia reduzida e bitmap de teste.
    A referencia e reduzida para o tamanho do teste via LANCZOS + threshold.
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


def _physical_cell_size(res: Tuple[int, int]) -> float:
    """Tamanho fisico em mm da celula matricial (pino a pino, extremo a extremo)."""
    return (max(res) - 1) * PIN_SPACING_MM


# ---------------------------------------------------------------------------
# Coleta de glifos e geracao de perfis
# ---------------------------------------------------------------------------

def _collect_mapped_codepoints(font_path: pathlib.Path) -> List[int]:
    """Retorna codepoints mapeados no cmap, filtrados para imprimiveis."""
    tt = TTFont(str(font_path))
    cmap = tt.getBestCmap()
    tt.close()
    if not cmap:
        raise ValueError("Fonte sem tabela cmap utilizavel.")

    ranges = list(range(32, 127)) + list(range(160, 256)) + list(range(0x2000, 0x2070))
    result = []
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
    """Cria perfis de referencia (64x64) para todos os glifos."""
    tt = TTFont(str(font_path))
    cmap = tt.getBestCmap()
    tt.close()

    ref_font = ImageFont.truetype(str(font_path), REFERENCE_RESOLUTION[1] - 2)

    profiles: List[GlyphProfile] = []
    for cp in codepoints:
        ch = chr(cp)
        glyph_name = cmap.get(cp, ".notdef") if isinstance(cmap.get(cp), str) else str(cmap.get(cp, cp))

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


# ---------------------------------------------------------------------------
# Analise tatil por resolucao
# ---------------------------------------------------------------------------

def _analyze_resolution(
    profiles: List[GlyphProfile],
    resolution: Tuple[int, int],
) -> ResolutionReport:
    """Analisa toda a fonte para uma resolucao de matriz especifica."""
    phys_mm = _physical_cell_size(resolution)

    # Resolução efetiva: elimina pinos mortos (linhas/colunas nunca ativadas)
    eff_res, crop_box = _effective_resolution(profiles, resolution)
    eff_w_mm = (eff_res[0] - 1) * PIN_SPACING_MM
    eff_h_mm = (eff_res[1] - 1) * PIN_SPACING_MM
    phys_mm = max(eff_w_mm, eff_h_mm)   # tamanho físico efetivo

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

        bm  = _render_bitmap(p.char, test_font, resolution)
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
    loss_chars = [v.char for v in verdicts if v.verdict not in ("APTO", "VAZIO")]

    return ResolutionReport(
        resolution=resolution, phys_size_mm=phys_mm, fits_finger=fits_finger,
        total=len(verdicts), apto=apto, blank=blank, loss=loss,
        loss_chars=loss_chars, verdicts=verdicts,
        eff_resolution=eff_res, crop_box=crop_box,
    )


# ---------------------------------------------------------------------------
# Grade visual de diagnostico
# ---------------------------------------------------------------------------

def _save_grid(
    report: ResolutionReport,
    profiles: List[GlyphProfile],
    spacing_mm: float = PIN_SPACING_MM,
) -> pathlib.Path:
    """Grade visual com bordas coloridas por veredicto tatil."""
    res = report.resolution
    # Usa dimensões efetivas (pós-corte de pinos mortos) se disponíveis
    eff_res = report.eff_resolution if report.eff_resolution != (0, 0) else res
    w, h = eff_res
    crop_box = report.crop_box
    v_map = {v.char: v for v in report.verdicts}

    cols  = 20
    rows  = (len(profiles) + cols - 1) // cols
    scale = max(1, 32 // max(w, h))
    cw, ch_px = w * scale, h * scale
    border = 2
    cell_w = cw + border * 2 + 2
    cell_h = ch_px + border * 2 + 10

    canvas = Image.new("RGB", (cols * cell_w, rows * cell_h + 22), (240, 240, 240))
    dc = ImageDraw.Draw(canvas)

    lbl = _system_font(9)   # Arial/Times para rótulos de codepoint e legenda
    test_font = ImageFont.truetype(str(FONT_PATH), res[1] - 2)  # fonte no tamanho declarado

    COLOR = {
        "APTO":             (60, 160, 60),
        "VAZIO":            (160, 160, 160),
        "SATURADO":         (220, 100, 0),
        "RASO":             (180, 140, 0),
        "PERDA_ESTRUTURAL": (180, 40, 40),
        "TAMANHO_GRANDE":   (80, 80, 200),
    }

    for idx, p in enumerate(profiles):
        col = idx % cols
        row = idx // cols
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
        bclr = COLOR.get(v.verdict if v else "VAZIO", (160, 160, 160))
        canvas.paste(gimg, (x0 + border, y0 + border))
        dc.rectangle([x0, y0, x0 + cw + border * 2, y0 + ch_px + border * 2],
                     outline=bclr, width=2)
        dc.text((x0 + 1, y0 + ch_px + border * 2 + 1),
                f"U+{p.codepoint:04X}", font=lbl, fill=(80, 80, 80))

    # Legenda
    ly, lx = rows * cell_h + 4, 4
    for label, color in COLOR.items():
        dc.rectangle([lx, ly, lx + 10, ly + 10], fill=color)
        dc.text((lx + 12, ly), label, font=lbl, fill=(40, 40, 40))
        lx += 105

    out = OUTPUT_DIR / f"tatil_{res[0]}x{res[1]}_{spacing_mm:.1f}mm.png"
    canvas.save(out)
    return out


# ---------------------------------------------------------------------------
# Geração de modelo 3D tátil (STL / 3MF) para impressão de protótipo
# ---------------------------------------------------------------------------

DEFAULT_TACTILE_SEQUENCE = "tqlDà"

def _generate_tactile_3d(
    sequence: str,
    candidate: dict,
    profiles: List[GlyphProfile],
    fmt: str = "3mf",
    pin_height_mm: float = 0.6,
    base_thickness_mm: float = 2.0,
    margin_mm: float = 1.5,
) -> pathlib.Path:
    """
    Gera modelo 3D de tira tátil com os glifos da sequência fornecida.

    Geometria:
      - Placa base retangular (base_thickness_mm de espessura).
      - Para cada pixel ativo no bitmap recortado: cilindro de diâmetro
        PIN_DIAMETER_MM e altura pin_height_mm rasando a face superior da base.
      - Células dispostas lado a lado com GAP_BETWEEN_CELLS_MM de separação.
      - Margem (margin_mm) em torno do conjunto de células.

    Args:
        sequence: String com os caracteres ELIS a renderizar.
        candidate: Candidato da lista (dict com 'resolution' e 'spacing_mm').
        profiles: Perfis dos glifos (necessários para _effective_resolution).
        fmt: Formato de saída — 'stl' ou '3mf'.
        pin_height_mm: Altura dos pinos acima da base (padrão: 0.6 mm).
        base_thickness_mm: Espessura da placa-base (padrão: 2.0 mm).
        margin_mm: Margem lateral ao redor da tira (padrão: 1.5 mm).

    Returns:
        Caminho do arquivo gerado.
    """
    try:
        import trimesh  # type: ignore[import]
    except ImportError as exc:
        raise RuntimeError(
            "trimesh não encontrado. Execute: uv add trimesh"
        ) from exc

    cols, rows = tuple(candidate["resolution"])
    spacing_mm: float = candidate["spacing_mm"]
    resolution: Tuple[int, int] = (cols, rows)

    # Resolução efetiva (elimina pinos mortos) — usa cache se já calculado
    eff_res, crop_box = _effective_resolution(profiles, resolution)
    eff_cols, eff_rows = eff_res

    cell_w_mm = (eff_cols - 1) * spacing_mm
    cell_h_mm = (eff_rows - 1) * spacing_mm

    # Renderiza cada glifo da sequência
    font = ImageFont.truetype(str(FONT_PATH), rows - 2)
    bitmaps: List[np.ndarray] = []
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
    total_h = cell_h_mm
    plate_w = total_w + 2 * margin_mm
    plate_h = total_h + 2 * margin_mm

    meshes: List[object] = []

    # Placa-base: box centrado em (plate_w/2, plate_h/2, base_thickness/2)
    base = trimesh.creation.box([plate_w, plate_h, base_thickness_mm])
    base.apply_translation([plate_w / 2, plate_h / 2, base_thickness_mm / 2])
    meshes.append(base)

    # Pinos
    pin_r = PIN_DIAMETER_MM / 2
    for g_idx, bm in enumerate(bitmaps):
        x_off = margin_mm + g_idx * (cell_w_mm + GAP_BETWEEN_CELLS_MM)
        for r_idx in range(eff_rows):
            for c_idx in range(eff_cols):
                if not bm[r_idx, c_idx]:
                    continue
                cx = x_off + c_idx * spacing_mm
                # Inverte verticalmente: linha 0 do bitmap → topo físico (Y máximo)
                cy = margin_mm + (eff_rows - 1 - r_idx) * spacing_mm
                cz = base_thickness_mm + pin_height_mm / 2
                pin = trimesh.creation.cylinder(
                    radius=pin_r,
                    height=pin_height_mm,
                    sections=16,
                )
                pin.apply_translation([cx, cy, cz])
                meshes.append(pin)

    combined = trimesh.util.concatenate(meshes)

    # Nome do arquivo: caracteres não alfanuméricos → U+XXXX
    seq_safe = "".join(
        c if c.isalnum() else f"U{ord(c):04X}" for c in sequence
    )
    fname = f"tatil_3d_{cols}x{rows}_{spacing_mm:.1f}mm_{seq_safe}.{fmt}"
    out = OUTPUT_DIR / fname
    combined.export(str(out))
    return out


# ---------------------------------------------------------------------------
# Funcoes de suporte a analise estendida (multi-dedo / sequencial / M×N)
# ---------------------------------------------------------------------------

def _physical_cell_size_mn(
    res: Tuple[int, int],
    spacing_mm: float,
) -> Tuple[float, float]:
    """Retorna (cell_w_mm, cell_h_mm) para célula M×N com dado espaçamento."""
    cols, rows = res
    return (cols - 1) * spacing_mm, (rows - 1) * spacing_mm


def _sequence_capacity(
    cell_w_mm: float,
    gap_mm: float = GAP_BETWEEN_CELLS_MM,
    hand_span_mm: float = HAND_SPAN_MM,
) -> int:
    """
    Número máximo K de glifos dispostos lado a lado dentro da envergadura da mão.

    Equação:  K * cell_w + (K-1) * gap <= hand_span
              K <= (hand_span + gap) / (cell_w + gap)
    """
    if cell_w_mm <= 0:
        return 0
    return int((hand_span_mm + gap_mm) / (cell_w_mm + gap_mm))


def _analyze_resolution_ext(
    profiles: List[GlyphProfile],
    resolution: Tuple[int, int],
    spacing_mm: float,
) -> ExtendedReport:
    """
    Analisa a fonte para uma resolução M×N e um espaçamento de pinos específico.

    Diferenças em relação a _analyze_resolution:
      - Aceita células assimétricas (cols != rows).
      - Espaçamento configurável → permite sweep de 2,5 a 3,5 mm.
      - Limiar de tamanho via MAX_MULTI_FINGER_MM (multi-dedo) além de
        MAX_FINGER_AREA_MM (1 dedo).
    """
    cell_w_mm, cell_h_mm = _physical_cell_size_mn(resolution, spacing_mm)

    # Resolução efetiva: elimina pinos mortos (linhas/colunas nunca ativadas)
    eff_res, crop_box = _effective_resolution(profiles, resolution)
    cell_w_mm = (eff_res[0] - 1) * spacing_mm   # tamanho físico efetivo horizontal
    cell_h_mm = (eff_res[1] - 1) * spacing_mm   # tamanho físico efetivo vertical

    max_dim = max(cell_w_mm, cell_h_mm)

    if max_dim <= MAX_FINGER_AREA_MM:
        mode = "1-dedo"
        limit_mm = MAX_FINGER_AREA_MM
    elif max_dim <= MAX_MULTI_FINGER_MM:
        mode = "multi-dedo"
        limit_mm = MAX_MULTI_FINGER_MM
    else:
        mode = "fora-de-alcance"
        limit_mm = MAX_MULTI_FINGER_MM

    fits = max_dim <= limit_mm

    test_font = ImageFont.truetype(str(FONT_PATH), resolution[1] - 2)
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

        bm  = _render_bitmap(p.char, test_font, resolution)
        if crop_box != (0, 0, 0, 0):
            bm = bm[crop_box[0]:crop_box[1] + 1, crop_box[2]:crop_box[3] + 1]
        d   = _pixel_density(bm)
        ec  = _edge_complexity(bm)
        iou = _iou(p.bitmap_ref, bm)

        density_ok    = DENSITY_MIN <= d <= DENSITY_MAX
        iou_ok        = iou >= 0.15
        complexity_ok = ec >= EDGE_COMPLEXITY_MIN

        if not fits:
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
            phys_size_mm=max_dim, fits_finger=fits,
            density=d, density_ok=density_ok,
            iou=iou, iou_ok=iou_ok,
            edge_complexity=ec, complexity_ok=complexity_ok,
            verdict=verdict,
        ))

    apto  = sum(1 for v in verdicts if v.verdict == "APTO")
    blank = sum(1 for v in verdicts if v.verdict == "VAZIO")
    loss  = sum(1 for v in verdicts if v.verdict not in ("APTO", "VAZIO"))
    loss_chars = [v.char for v in verdicts if v.verdict not in ("APTO", "VAZIO")]

    inner = ResolutionReport(
        resolution=resolution, phys_size_mm=max_dim, fits_finger=fits,
        total=len(verdicts), apto=apto, blank=blank, loss=loss,
        loss_chars=loss_chars, verdicts=verdicts,
        eff_resolution=eff_res, crop_box=crop_box,
    )

    seq_cap = _sequence_capacity(cell_w_mm)
    return ExtendedReport(
        resolution=resolution, spacing_mm=spacing_mm,
        cell_w_mm=cell_w_mm, cell_h_mm=cell_h_mm,
        reading_mode=mode,
        seq_capacity=seq_cap,
        seq_in_range=seq_cap >= SEQ_GLYPH_MIN,
        report=inner,
    )


# ---------------------------------------------------------------------------
# Persistência e prompt interativo de candidatos viáveis
# ---------------------------------------------------------------------------

def _save_candidates(viable: List[ExtendedReport]) -> None:
    """Serializa a lista de candidatos viáveis em JSON para uso futuro."""
    data = [
        {
            "rank":         idx + 1,
            "resolution":   list(er.resolution),
            "spacing_mm":   er.spacing_mm,
            "cell_w_mm":    er.cell_w_mm,
            "cell_h_mm":    er.cell_h_mm,
            "reading_mode": er.reading_mode,
            "seq_capacity": er.seq_capacity,
            "seq_in_range": er.seq_in_range,
            "coverage_pct": round(er.report.coverage_pct, 2),
        }
        for idx, er in enumerate(viable)
    ]
    CANDIDATES_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def _load_candidates() -> List[dict]:
    """Carrega a lista de candidatos salva. Retorna lista vazia se não existir."""
    if not CANDIDATES_FILE.exists():
        return []
    try:
        return json.loads(CANDIDATES_FILE.read_text())
    except Exception:
        return []


def _print_candidates_table(candidates: List[dict]) -> None:
    """Imprime a tabela de candidatos no formato padrão."""
    hdr = (
        f"  {'#':<4} {'Resoluc':<8} {'Esp':>5}  "
        f"{'W_mm':>6} {'H_mm':>6}  "
        f"{'Modo':<14} {'Seq':>4}  {'Cob%':>6}"
    )
    print(hdr)
    print("  " + "-" * 62)
    for c in candidates:
        cols, rows = c["resolution"]
        print(
            f"  {c['rank']:<4d} {cols:2d}x{rows:<5d} {c['spacing_mm']:4.1f}mm"
            f"  {c['cell_w_mm']:6.1f} {c['cell_h_mm']:6.1f}"
            f"  {c['reading_mode']:<14} {c['seq_capacity']:3d}"
            f"  {c['coverage_pct']:5.1f}%"
        )


def _iso_compliance(er: ExtendedReport) -> List[Tuple[str, bool, str]]:
    """
    Avalia conformidade psicofísica e normativa (ISO 11548-2) de um candidato.

    Retorna lista de (criterio, aprovado, detalhe) com todos os pontos verificados.
    """
    sp = er.spacing_mm
    gap = sp - PIN_DIAMETER_MM
    w, h = er.cell_w_mm, er.cell_h_mm
    max_dim = max(w, h)
    min_dim = min(w, h)
    aspect = max_dim / min_dim if min_dim > 0 else float("inf")

    checks: List[Tuple[str, bool, str]] = [
        # ── ISO 11548-2 §6.3 — parâmetros do pino ────────────────────────────
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
        # ── Limiar de dois pontos — discriminação tátil ───────────────────────
        (
            "Razão espaç/diâm (>= 1,5×)",
            sp / PIN_DIAMETER_MM >= 1.5,
            f"{sp / PIN_DIAMETER_MM:.2f}×",
        ),
        # ── Tamanho de célula por modo ────────────────────────────────────────
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
        # ── Proporção de aspecto — evita célula excessivamente alongada ───────
        (
            f"Relação de aspecto (<= {MAX_CELL_ASPECT_RATIO:.1f}×)",
            aspect <= MAX_CELL_ASPECT_RATIO,
            f"{aspect:.2f}×  [{w:.1f} × {h:.1f} mm]",
        ),
        # ── Capacidade sequencial ─────────────────────────────────────────────
        (
            f"Glifos/tira dentro da faixa ({SEQ_GLYPH_MIN}–{SEQ_GLYPH_MAX})",
            SEQ_GLYPH_MIN <= er.seq_capacity <= SEQ_GLYPH_MAX + 2,
            f"{er.seq_capacity} glifos/tira",
        ),
        # ── Cobertura psicofísica ─────────────────────────────────────────────
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


def _print_candidate_detail(
    er: ExtendedReport,
    label: str,
    profiles: List[GlyphProfile],
    offer_3d: bool = True,
    viable: Optional[List[ExtendedReport]] = None,
) -> None:
    """Exibe ficha completa de um candidato com relatório de conformidade ISO."""
    c, r = er.resolution
    sep_inner = "  " + "-" * 64
    print(f"\n  >>> {label}")
    print(sep_inner)
    print(f"      Resolução declarada : {c}×{r}  @  {er.spacing_mm:.1f} mm/pino")

    # Resolução efetiva (cache já preenchido neste ponto)
    eff_res, _ = _effective_resolution(profiles, er.resolution)
    eff_w_mm = (eff_res[0] - 1) * er.spacing_mm
    eff_h_mm = (eff_res[1] - 1) * er.spacing_mm
    print(f"      Resolução efetiva   : {eff_res[0]}×{eff_res[1]} pinos  "
          f"→  {eff_w_mm:.1f} × {eff_h_mm:.1f} mm")
    print(f"      Área de célula      : {eff_w_mm * eff_h_mm:.1f} mm²")
    print(f"      Modo tátil          : {er.reading_mode}")
    print(f"      Glifos/tira         : até {er.seq_capacity}  "
          f"(alvo: {SEQ_GLYPH_MIN}–{SEQ_GLYPH_MAX})")
    print(f"      Cobertura útil      : {er.report.coverage_pct:.1f}%"
          f"  ({er.report.apto} aptos / {er.report.total - er.report.blank} com visual)")

    print(f"\n      Conformidade ISO 11548-2 / Psicofísica:")
    checks = _iso_compliance(er)
    all_pass = True
    for name, ok, detail in checks:
        icon = "✓" if ok else "✗"
        print(f"        [{icon}] {name:<50s}  {detail}")
        if not ok:
            all_pass = False
    verdict = "APROVADO — todos os critérios ISO satisfeitos" if all_pass \
              else "ATENÇÃO  — um ou mais critérios não satisfeitos"
    print(f"\n      Resultado: {verdict}")
    print(sep_inner)

    grid_path = _save_grid(er.report, profiles, er.spacing_mm)
    print(f"      Grade visual : {grid_path.relative_to(pathlib.Path.cwd())}")

    if offer_3d:
        _prompt_tactile_3d(
            {"resolution": list(er.resolution), "spacing_mm": er.spacing_mm},
            profiles,
            viable,
        )


def _generate_from_saved(
    candidates: List[dict],
    profiles: List[GlyphProfile],
) -> bool:
    """
    Exibe a lista salva, solicita escolha do usuário e gera a grade.
    Retorna True se uma grade foi gerada (encerra o fluxo principal),
    False se o usuário optou por não escolher.
    """
    sep = "=" * 68
    print(f"\n{sep}")
    print("  Lista de candidatos viáveis do último processamento")
    print(sep)
    _print_candidates_table(candidates)
    print()
    resp = input(
        f"  Deseja gerar a grade de um candidato da lista? "
        f"[1-{len(candidates)} / Enter para processar normalmente]: "
    ).strip()

    if not resp:
        print("  -> Processamento completo será executado.\n")
        return False

    try:
        idx = int(resp)
        if not (1 <= idx <= len(candidates)):
            raise ValueError
    except ValueError:
        print("  -> Entrada inválida. Processamento completo será executado.\n")
        return False

    chosen = candidates[idx - 1]
    res    = tuple(chosen["resolution"])        # type: ignore[arg-type]
    sp     = chosen["spacing_mm"]

    print(f"\n  Gerando grade para {res[0]}x{res[1]} @ {sp:.1f} mm...")
    # Reanalisa apenas o candidato escolhido
    er = _analyze_resolution_ext(profiles, res, sp)  # type: ignore[arg-type]
    grid_path = _save_grid(er.report, profiles, er.spacing_mm)
    print(f"  Grade salva em: {grid_path.relative_to(pathlib.Path.cwd())}")
    print(f"  Cobertura: {er.report.coverage_pct:.1f}%  |  "
          f"Modo: {er.reading_mode}  |  Seq: {er.seq_capacity} glifos/tira")

    # Oferta de geração de modelo 3D para impressão
    _prompt_tactile_3d(chosen, profiles)

    print(sep)
    return True


def _prompt_tactile_3d(
    candidate: dict,
    profiles: List[GlyphProfile],
    viable: Optional[List["ExtendedReport"]] = None,
) -> None:
    """Pergunta ao usuário se deseja gerar modelo 3D tátil e o produz.

    Quando *viable* é fornecida o usuário pode digitar o número de qualquer
    candidato da lista para gerar o modelo daquele item em vez do atual.
    """
    if viable:
        prompt = (
            f"\n  Deseja gerar modelo 3D tátil para impressão?\n"
            f"  [S = este candidato  /  1-{len(viable)} = escolher da lista  /  N = não]: "
        )
    else:
        prompt = "\n  Deseja gerar modelo 3D tátil para impressão? [S/n]: "

    resp3d = input(prompt).strip().lower()

    if resp3d in ("n", "nao", "não", "no"):
        return

    if viable and resp3d.isdigit():
        idx = int(resp3d)
        if 1 <= idx <= len(viable):
            er = viable[idx - 1]
            candidate = {"resolution": list(er.resolution), "spacing_mm": er.spacing_mm}
            print(
                f"  -> Candidato #{idx} selecionado: "
                f"{er.resolution[0]}×{er.resolution[1]} @ {er.spacing_mm:.1f} mm/pino"
            )
        else:
            print(f"  -> Número fora do intervalo (1–{len(viable)}). Usando candidato atual.")
    elif resp3d not in ("", "s", "sim", "y", "yes"):
        return

    seq = input(
        f"  Sequência de glifos ELIS [{DEFAULT_TACTILE_SEQUENCE}]: "
    ).strip()
    if not seq:
        seq = DEFAULT_TACTILE_SEQUENCE

    fmt_resp = input("  Formato [3mf/stl, padrão 3mf]: ").strip().lower()
    fmt = "stl" if fmt_resp == "stl" else "3mf"

    print(f"  Gerando modelo 3D ({fmt.upper()}) para sequência: {seq!r} ...")
    try:
        out = _generate_tactile_3d(seq, candidate, profiles, fmt=fmt)
        print(f"  Modelo salvo em: {out.relative_to(pathlib.Path.cwd())}")
        cols, rows = candidate["resolution"]
        sp = candidate["spacing_mm"]
        eff_res, _ = _effective_resolution(profiles, (cols, rows))
        print(
            f"  Dimensões físicas por célula: "
            f"{(eff_res[0]-1)*sp:.1f} mm (L) × {(eff_res[1]-1)*sp:.1f} mm (A)  "
            f"+ base 2.0 mm de espessura"
        )
    except Exception as exc:
        print(f"  [ERRO] Não foi possível gerar o modelo 3D: {exc}")


# ---------------------------------------------------------------------------
# Sumario por grupo
# ---------------------------------------------------------------------------

def _group_summary(report: ResolutionReport) -> Dict[str, Dict[str, int]]:
    v_by_cp = {v.codepoint: v.verdict for v in report.verdicts}
    summary: Dict[str, Dict[str, int]] = {}
    for grp, cps in GLYPH_GROUPS.items():
        cnt: Dict[str, int] = {}
        for cp in cps:
            vrd = v_by_cp.get(cp)
            if vrd:
                cnt[vrd] = cnt.get(vrd, 0) + 1
        if cnt:
            summary[grp] = cnt
    return summary


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    sep = "=" * 68

    # -----------------------------------------------------------------------
    # [0] Verificar lista de candidatos salva
    # -----------------------------------------------------------------------
    saved = _load_candidates()
    if saved:
        print(sep)
        print("  ELIS -- Analise de Viabilidade Tatil para Dispositivo Matricial")
        print(sep)
        print(f"\n  Encontrada lista salva em '{CANDIDATES_FILE.relative_to(pathlib.Path.cwd())}' "
              f"com {len(saved)} candidatos.")
        # Para usar a lista salva o usuário não precisa carregar os perfis antes
        # — mas _generate_from_saved precisa dos perfis para renderizar o grid.
        # Carregamos os perfis só se o usuário confirmar a escolha.
        resp_pre = input(
            "  Deseja consultar a lista salva antes de processar? [S/n]: "
        ).strip().lower()
        if resp_pre in ("", "s", "sim", "y", "yes"):
            # Carrega perfis apenas neste ponto
            print("\n  Carregando perfis para renderização...")
            codepoints_pre = _collect_mapped_codepoints(FONT_PATH)
            profiles_pre   = _build_profiles(codepoints_pre, FONT_PATH)
            if _generate_from_saved(saved, profiles_pre):
                return   # grade gerada — encerra sem processamento completo

    print(sep)
    print("  ELIS -- Analise de Viabilidade Tatil para Dispositivo Matricial")
    print(sep)

    # Limpa lista anterior antes de iniciar novo processamento completo
    if CANDIDATES_FILE.exists():
        CANDIDATES_FILE.unlink()
        print(f"  [info] Lista anterior removida: {CANDIDATES_FILE.name}")

    # 1. Perfis
    print("\n[1/4] Carregando glifos e calculando perfis de referencia (64x64)...")
    codepoints = _collect_mapped_codepoints(FONT_PATH)
    profiles   = _build_profiles(codepoints, FONT_PATH)
    real_glyphs = [p for p in profiles if p.codepoint not in INTENTIONALLY_BLANK]
    dens = [p.density for p in real_glyphs]
    print(f"      {len(profiles)} glifos no cmap  |  {len(real_glyphs)} com conteudo visual")
    print(f"      Densidade media  : {np.mean(dens):.3f}  "
          f"(min {np.min(dens):.3f} / max {np.max(dens):.3f})")

    # 2. Parametros fisicos
    print("\n[2/4] Parametros fisicos do dispositivo:")
    print(f"      Espaco entre pinos : {PIN_SPACING_MM} mm  (ISO 11548-2 / Braille)")
    print(f"      Diametro do pino   : {PIN_DIAMETER_MM} mm")
    print(f"      Gap entre pinos    : {PIN_SPACING_MM - PIN_DIAMETER_MM} mm")
    print(f"      Limite 1 dedo      : <= {MAX_FINGER_AREA_MM:.0f} mm")
    for res in CANDIDATE_RESOLUTIONS:
        phys = _physical_cell_size(res)
        flag = "ok - 1 dedo" if phys <= MAX_FINGER_AREA_MM else "atencao - requer exploracao"
        print(f"      {res[0]:2d}x{res[1]:2d}  ->  {phys:.1f} mm x {phys:.1f} mm  [{flag}]")

    # 3. Analise
    print("\n[3/4] Analisando cada resolucao...")
    reports: List[ResolutionReport] = []
    for res in CANDIDATE_RESOLUTIONS:
        r = _analyze_resolution(profiles, res)
        reports.append(r)

        print(f"\n  -- {res[0]}x{res[1]}  ({r.phys_size_mm:.1f} mm) --")
        print(f"    APTO             : {r.apto}")
        print(f"    VAZIO (espaco)   : {r.blank}")
        print(f"    Com restricao    : {r.loss}")
        print(f"    Cobertura util   : {r.coverage_pct:.1f}%")

        gsumm = _group_summary(r)
        for grp, cnts in gsumm.items():
            apto  = cnts.get("APTO", 0)
            total = sum(cnts.values()) - cnts.get("VAZIO", 0)
            if total:
                print(f"      {grp:<40s}: {apto}/{total} aptos")

    # 4. Grades
    print("\n[4/4] Gerando grades visuais...")
    for r in reports:
        path = _save_grid(r, profiles)
        print(f"    -> {path.relative_to(pathlib.Path.cwd())}")

    # 5. Relatorio final
    print(f"\n{sep}")
    print("  RESULTADO FINAL")
    print(sep)

    VORD = ["APTO", "VAZIO", "SATURADO", "RASO", "PERDA_ESTRUTURAL", "TAMANHO_GRANDE"]
    best: ResolutionReport | None = None

    for r in reports:
        tag = "RECOMENDADO " if r.fits_finger and r.coverage_pct >= 90 else \
              "PARCIAL      " if r.coverage_pct >= 70 else "INSUFICIENTE "
        print(f"\n  {r.resolution[0]:2d}x{r.resolution[1]:2d}  ({r.phys_size_mm:.1f} mm)  [{tag}]")
        cnt: Dict[str, int] = {}
        for v in r.verdicts:
            cnt[v.verdict] = cnt.get(v.verdict, 0) + 1
        for vrd in VORD:
            if cnt.get(vrd, 0):
                print(f"      {vrd:<24s}: {cnt[vrd]:3d}")
        print(f"      Cobertura util        : {r.coverage_pct:.1f}%")
        if r.fits_finger and r.coverage_pct >= 90 and best is None:
            best = r

    print()
    if best:
        w, h = best.resolution
        print(f"  Resolucao minima recomendada: {w}x{h}  "
              f"({best.phys_size_mm:.1f} mm x {best.phys_size_mm:.1f} mm)")
    else:
        ranked = sorted(reports, key=lambda r: (r.fits_finger, r.coverage_pct), reverse=True)
        best   = ranked[0]
        w, h   = best.resolution
        print(f"  Melhor opcao disponivel: {w}x{h}  ({best.phys_size_mm:.1f} mm)"
              f"  -- cobertura {best.coverage_pct:.1f}%")
        print(f"  Para 100%, redesenhe manualmente os {best.loss} glifos problematicos.")

    print(f"\n  Grades em: {OUTPUT_DIR.relative_to(pathlib.Path.cwd())}/")
    print(sep)

    # -----------------------------------------------------------------------
    # [5/5] Análise Estendida — multi-dedo / varrimento sequencial / M×N
    # -----------------------------------------------------------------------
    print(f"\n{sep}")
    print("  [5/5] ANALISE ESTENDIDA: multi-dedo / sequencial / M×N assimetrico")
    print(sep)
    print(f"        Faixa de sequencia : {SEQ_GLYPH_MIN}–{SEQ_GLYPH_MAX} glifos/tira")
    print(f"        Envergadura da mao  : {HAND_SPAN_MM:.0f} mm")
    print(f"        Gap entre celulas   : {GAP_BETWEEN_CELLS_MM:.0f} mm")
    print(f"        Espaçamentos testados: {PIN_SPACING_CANDIDATES} mm")
    print(f"        Limite 1-dedo       : <= {MAX_FINGER_AREA_MM:.0f} mm")
    print(f"        Limite multi-dedo   : <= {MAX_MULTI_FINGER_MM:.0f} mm")

    all_res = list(dict.fromkeys(CANDIDATE_RESOLUTIONS + ASYMMETRIC_RESOLUTIONS))
    ext_results: List[ExtendedReport] = []

    print("\n  Processando combinacoes (resolucao x espaçamento)...")
    for res in all_res:
        for sp in PIN_SPACING_CANDIDATES:
            er = _analyze_resolution_ext(profiles, res, sp)
            ext_results.append(er)

    # Candidatos viáveis: alcance OK + sequência suficiente + cobertura >= 80%
    viable = [
        er for er in ext_results
        if er.reading_mode != "fora-de-alcance"
        and er.seq_in_range
        and er.report.coverage_pct >= 80.0
    ]

    # Ordenar: maior cobertura → maior capacidade sequencial → maior espaçamento
    viable.sort(key=lambda e: (
        -e.report.coverage_pct,
        -e.seq_capacity,
        -e.spacing_mm,
        e.cell_w_mm * e.cell_h_mm,
    ))

    # Salva/atualiza a lista de candidatos em disco
    _save_candidates(viable)
    print(f"  Lista de candidatos salva em '{CANDIDATES_FILE.relative_to(pathlib.Path.cwd())}'")

    print(f"\n  Candidatos viaveis ({len(viable)} encontrados):")
    saved_for_display = _load_candidates()   # relê para confirmar escrita
    _print_candidates_table(saved_for_display[:25])

    # ── Melhor candidato para varrimento sequencial (maior capacidade) ────────
    best_seq = viable[0] if viable else None

    # ── Melhor candidato econômico (menor área física c/ cobertura >= 95%) ───
    best_economy = min(
        (e for e in viable if e.report.coverage_pct >= MIN_COVERAGE_ECONOMY),
        key=lambda e: (e.cell_w_mm * e.cell_h_mm, -e.report.coverage_pct, -e.spacing_mm),
        default=None,
    )

    if best_seq:
        _print_candidate_detail(
            best_seq,
            "Melhor candidato — varrimento sequencial (maior capacidade)",
            profiles,
            offer_3d=True,
            viable=viable,
        )
    else:
        print("\n  Nenhum candidato viavel encontrado com os criterios definidos.")
        print("  Considere reduzir SEQ_GLYPH_MIN ou a exigencia de cobertura minima.")

    if best_economy is not None and best_economy is not best_seq:
        _print_candidate_detail(
            best_economy,
            "Melhor candidato econômico — menor área física com cobertura >= "
            f"{MIN_COVERAGE_ECONOMY:.0f}%",
            profiles,
            offer_3d=True,
            viable=viable,
        )
    elif best_economy is not None and best_economy is best_seq:
        print(
            "\n  [info] O candidato econômico coincide com o melhor sequencial — "
            "nenhum candidato adicional exibido."
        )

    print(f"\n{sep}")


if __name__ == "__main__":
    main()
