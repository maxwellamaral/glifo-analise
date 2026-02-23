"""
Configurações, constantes e grupos de glifos ELIS.

Todas as constantes são imutáveis para facilitar testes parametrizados.
"""
from __future__ import annotations

import pathlib
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
FONT_PATH: pathlib.Path = pathlib.Path(__file__).parent.parent / "elis.ttf"
OUTPUT_DIR: pathlib.Path = pathlib.Path(__file__).parent.parent / "output"

# Arquivo de persistência dos candidatos viáveis
CANDIDATES_FILE: pathlib.Path = OUTPUT_DIR / "candidatos_viaveis.json"

# ---------------------------------------------------------------------------
# Resoluções candidatas
# ---------------------------------------------------------------------------
CANDIDATE_RESOLUTIONS: List[Tuple[int, int]] = [(10, 10), (15, 15), (20, 20)]

# Resolução de referência para análise estrutural
REFERENCE_RESOLUTION: Tuple[int, int] = (64, 64)

# ---------------------------------------------------------------------------
# Parâmetros psicofísicos (ISO 11548-2 / literatura tátil)
# ---------------------------------------------------------------------------
PIN_SPACING_MM: float = 2.5        # espaçamento centro a centro (mm)
PIN_DIAMETER_MM: float = 1.5       # diâmetro do pino (mm)
MAX_FINGER_AREA_MM: float = 25.0   # largura máxima para leitura com 1 dedo (mm)

DENSITY_MIN: float = 0.03          # 3%  — 3 % marca tátil mínima perceptível
DENSITY_MAX: float = 0.55          # 55% — saturação tátil indistinguível
EDGE_COMPLEXITY_MIN: float = 0.08  # 8%  — complexidade mínima de borda

# Codepoints sem forma visual (espaços / caracteres de controle)
INTENTIONALLY_BLANK: set[int] = {
    0x0020, 0x00A0, 0x200B, 0x200C, 0x200D, 0xFEFF,
}

# ---------------------------------------------------------------------------
# Extensões: multi-dedo / sequencial / M×N
# ---------------------------------------------------------------------------
PIN_SPACING_CANDIDATES: List[float] = [2.5, 3.0, 3.5]

MAX_MULTI_FINGER_MM: float = 55.0     # máximo alcançável com vários dedos (mm)
HAND_SPAN_MM: float = 180.0           # envergadura da mão adulta para varredura (mm)
GAP_BETWEEN_CELLS_MM: float = 3.0    # folga física entre células adjacentes (mm)

SEQ_GLYPH_MIN: int = 4                # faixa mínima de glifos por tira
SEQ_GLYPH_MAX: int = 6                # faixa máxima de glifos por tira

MIN_COVERAGE_ECONOMY: float = 95.0   # cobertura mínima para candidato econômico

ISO_MIN_GAP_MM: float = PIN_SPACING_MM - PIN_DIAMETER_MM  # 1,0 mm

MAX_CELL_ASPECT_RATIO: float = 2.5    # proporção máxima W/H da célula

# ---------------------------------------------------------------------------
# Sequência tátil padrão (visualização e modelos 3D)
# ---------------------------------------------------------------------------
DEFAULT_TACTILE_SEQUENCE: str = "tqlDà"

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
# Grupos de glifos ELIS (mapeados sobre teclado padrão)
# ---------------------------------------------------------------------------
GLYPH_GROUPS: Dict[str, Tuple[int, ...]] = {
    "Maiúsculas (A-Z)":           tuple(range(0x0041, 0x005B)),
    "Minúsculas (a-z)":           tuple(range(0x0061, 0x007B)),
    "Dígitos (0-9)":              tuple(range(0x0030, 0x003A)),
    "Pontuacao/Simbolos basicos": (
        0x0021, 0x0022, 0x0023, 0x0024, 0x0025, 0x0026, 0x0027,
        0x0028, 0x0029, 0x002A, 0x002B, 0x002C, 0x002D, 0x002E,
        0x002F, 0x003A, 0x003B, 0x003C, 0x003E, 0x003F, 0x0040,
        0x005C, 0x005F,
    ),
    "Acentuados / Latin-1":       tuple(range(0x00A0, 0x0100)),
}

# ---------------------------------------------------------------------------
# Candidatos de fontes de sistema para renderização de rótulos
# ---------------------------------------------------------------------------
SYSTEM_FONT_CANDIDATES: List[str] = [
    "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf",
    "/usr/share/fonts/truetype/arial.ttf",
    "/usr/share/fonts/arial.ttf",
    "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf",
    "/usr/share/fonts/truetype/times.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/usr/share/fonts/freefont/FreeSans.ttf",
]

# ---------------------------------------------------------------------------
# Sequência padrão para geração de modelos 3D de demonstração
# ---------------------------------------------------------------------------
DEFAULT_TACTILE_SEQUENCE: str = "tqlDà"

MONO_FONT_CANDIDATES: List[str] = [
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
]
