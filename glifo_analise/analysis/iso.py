"""
Verificação de conformidade normativa (ISO 11548-2) e psicofísica.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from glifo_analise.config import (
    GAP_BETWEEN_CELLS_MM,
    HAND_SPAN_MM,
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


# ---------------------------------------------------------------------------
# API auxiliar — compatível com dicts persistidos em JSON
# ---------------------------------------------------------------------------

def iso_compliance_from_fields(
    spacing_mm: float,
    cell_w_mm: float,
    cell_h_mm: float,
    reading_mode: str,
    seq_capacity: int,
    coverage_pct: float,
) -> List[Dict[str, Any]]:
    """
    Mesmos critérios de :func:`_iso_compliance` mas operando diretamente sobre
    campos escalares (sem precisar de um :class:`ExtendedReport`).

    Útil para endpoints de detalhe que trabalham com o JSON persistido.

    Returns:
        Lista de dicts ``{"criterion", "passed", "detail", "category"}`` prontos
        para serialização JSON.
    """
    gap = spacing_mm - PIN_DIAMETER_MM
    w, h = cell_w_mm, cell_h_mm
    max_dim = max(w, h)
    min_dim = min(w, h)
    aspect = max_dim / min_dim if min_dim > 0 else float("inf")

    raw: List[Tuple[str, str, bool, str]] = [
        # (categoria, criterio, aprovado, detalhe)
        (
            "ISO 11548-2 §6.3 — Pino",
            "Espaçamento mínimo (≥ 2,5 mm)",
            spacing_mm >= 2.5,
            f"{spacing_mm:.1f} mm",
        ),
        (
            "ISO 11548-2 §6.3 — Pino",
            "Gap entre pinos (≥ 1,0 mm)",
            gap >= 1.0,
            f"{gap:.1f} mm  [espaç. {spacing_mm:.1f} – ∅ {PIN_DIAMETER_MM:.1f}]",
        ),
        (
            "Psicofísico — Limiar de dois pontos",
            "Razão espaç/diâm (≥ 1,5×)",
            spacing_mm / PIN_DIAMETER_MM >= 1.5,
            f"{spacing_mm / PIN_DIAMETER_MM:.2f}×",
        ),
        (
            "Psicofísico — Campo de leitura",
            "Cabe sob 1 dedo (ambos eixos ≤ 25 mm)"
            if reading_mode == "1-dedo"
            else "Eixo menor ≤ 25 mm (1 dedo varre 1 eixo)",
            min_dim <= MAX_FINGER_AREA_MM,
            f"menor eixo = {min_dim:.1f} mm",
        ),
        (
            "Psicofísico — Campo de leitura",
            "Dimensão máxima dentro do alcance multi-dedo (≤ 55 mm)"
            if reading_mode == "multi-dedo"
            else "Dimensão máxima dentro do alcance 1-dedo (≤ 25 mm)",
            max_dim <= (MAX_MULTI_FINGER_MM if reading_mode != "1-dedo"
                        else MAX_FINGER_AREA_MM),
            f"maior eixo = {max_dim:.1f} mm",
        ),
        (
            "Ergonomia — Proporção de célula",
            f"Relação de aspecto (≤ {MAX_CELL_ASPECT_RATIO:.1f}×)",
            aspect <= MAX_CELL_ASPECT_RATIO,
            f"{aspect:.2f}×  [{w:.1f} × {h:.1f} mm]",
        ),
        (
            "Ergonomia — Leitura sequencial",
            f"Glifos/tira dentro da faixa ({SEQ_GLYPH_MIN}–{SEQ_GLYPH_MAX})",
            SEQ_GLYPH_MIN <= seq_capacity <= SEQ_GLYPH_MAX + 2,
            f"{seq_capacity} glifos/tira",
        ),
        (
            "Cobertura psicofísica",
            "Cobertura útil ≥ 95%",
            coverage_pct >= 95.0,
            f"{coverage_pct:.1f}%",
        ),
        (
            "Cobertura psicofísica",
            "Cobertura útil = 100%",
            coverage_pct >= 100.0,
            f"{coverage_pct:.1f}%",
        ),
    ]

    return [
        {"criterion": cr, "category": cat, "passed": ok, "detail": det}
        for cat, cr, ok, det in raw
    ]


def candidate_detail_from_dict(
    candidate: Dict[str, Any],
    all_candidates: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Enriquece um candidato persistido com métricas derivadas, conformidade ISO e
    análise comparativa entre todos os candidatos.

    Args:
        candidate: dict do candidato (campos do JSON persistido).
        all_candidates: lista completa de candidatos (para ranking comparativo).

    Returns:
        Dict ampliado pronto para serialização como resposta JSON.
    """
    sp = candidate["spacing_mm"]
    w = candidate["cell_w_mm"]
    h = candidate["cell_h_mm"]
    mode = candidate["reading_mode"]
    seq = candidate["seq_capacity"]
    cov = candidate["coverage_pct"]
    cols, rows = candidate["resolution"]

    gap_mm = sp - PIN_DIAMETER_MM
    ratio = sp / PIN_DIAMETER_MM
    max_dim = max(w, h)
    min_dim = min(w, h)
    aspect = max_dim / min_dim if min_dim > 0 else 0.0
    area_mm2 = w * h
    total_pins_declared = cols * rows

    # Capacidade de strip física (K glifos lado a lado dentro da envergadura)
    seq_k = int((HAND_SPAN_MM + GAP_BETWEEN_CELLS_MM) / (w + GAP_BETWEEN_CELLS_MM))

    # Largura física de tiras com N glifos (para ergonomia de protótipo)
    strip_widths = {
        n: round(n * w + max(0, n - 1) * GAP_BETWEEN_CELLS_MM, 1)
        for n in (3, 4, 5, 6, 7)
    }

    # Tier de cobertura
    if cov >= 100.0:
        tier = "total"
    elif cov >= 95.0:
        tier = "alta"
    else:
        tier = "boa"

    # Rank de economia (menor área) dentro do mesmo tier
    same_tier = [
        c for c in all_candidates
        if (c["coverage_pct"] >= 100.0 and tier == "total")
        or (95.0 <= c["coverage_pct"] < 100.0 and tier == "alta")
        or (80.0 <= c["coverage_pct"] < 95.0 and tier == "boa")
    ]
    same_tier_sorted = sorted(same_tier, key=lambda c: c["cell_w_mm"] * c["cell_h_mm"])
    area_rank = next(
        (i + 1 for i, c in enumerate(same_tier_sorted)
         if c["rank"] == candidate["rank"]), None
    )

    # Critérios ISO
    iso = iso_compliance_from_fields(sp, w, h, mode, seq, cov)
    iso_pass = sum(1 for c in iso if c["passed"])

    # Notas de fabricação
    fab_notes: List[str] = []
    if mode == "1-dedo":
        fab_notes.append(
            "Célula legível com 1 dedo (≤ 25 mm em ambos os eixos): "
            "ideal para usuário com exploração de ponta de dedo."
        )
    else:
        fab_notes.append(
            f"Célula {mode}: o usuário precisará de 2–3 dedos para explorar "
            "verticalmente. Requer treinamento específico."
        )
    if gap_mm >= 1.2:
        fab_notes.append(
            f"Gap entre pinos confortável ({gap_mm:.1f} mm ≥ 1,2 mm): "
            "discriminação tátil robusta mesmo com dedo levemente úmido."
        )
    elif gap_mm >= 1.0:
        fab_notes.append(
            f"Gap mínimo normativo ({gap_mm:.1f} mm): atende ISO mas pode exigir "
            "superfície dos pinos com acabamento polido para melhor percepção."
        )
    else:
        fab_notes.append(
            f"Gap abaixo de 1,0 mm ({gap_mm:.1f} mm): risco de confusão tátil "
            "entre pinos adjacentes — revisar o projeto mecânico."
        )
    if sp == 3.0:
        fab_notes.append(
            "Espaçamento 3,0 mm: compromisso ideal entre detalhe dos glifos e "
            "discriminabilidade tátil individual — recomendado para primeiro protótipo."
        )
    elif sp == 3.5:
        fab_notes.append(
            "Espaçamento 3,5 mm: máxima discriminabilidade por pino — "
            "menor resolução visual, mas mais fácil de perceber ao toque."
        )
    if total_pins_declared <= 120:
        fab_notes.append(
            f"Baixa contagem de pinos ({total_pins_declared}): custo reduzido "
            "de atuadores para dispositivo dinâmico."
        )
    elif total_pins_declared <= 200:
        fab_notes.append(
            f"Contagem moderada de pinos ({total_pins_declared}): "
            "viável para protótipo com acionamento por SMA ou piezo."
        )
    else:
        fab_notes.append(
            f"Alta contagem de pinos ({total_pins_declared}): exige multiplexação "
            "ou atuadores MEMS para viabilidade econômica de série."
        )

    detail = dict(candidate)
    detail.update(
        gap_mm=round(gap_mm, 2),
        spacing_diameter_ratio=round(ratio, 2),
        aspect_ratio=round(aspect, 2),
        cell_area_mm2=round(area_mm2, 2),
        total_pins_declared=total_pins_declared,
        seq_capacity_computed=seq_k,
        strip_widths_mm=strip_widths,
        coverage_tier=tier,
        area_rank_in_tier=area_rank,
        total_in_tier=len(same_tier),
        iso_criteria=iso,
        iso_pass_count=iso_pass,
        iso_total_count=len(iso),
        iso_all_pass=(iso_pass == len(iso)),
        fabrication_notes=fab_notes,
    )
    return detail
