"""
Funções de exibição formatada para o terminal.
"""
from __future__ import annotations

import pathlib
from typing import Dict, List, Optional

from glifo_analise.config import (
    SEQ_GLYPH_MIN,
    SEQ_GLYPH_MAX,
    GLYPH_GROUPS,
)
from glifo_analise.models import ExtendedReport, GlyphProfile, ResolutionReport
from glifo_analise.analysis.bitmap import _effective_resolution
from glifo_analise.analysis.iso import _iso_compliance
from glifo_analise.output.grid import _save_grid


def _print_candidates_table(candidates: List[dict]) -> None:
    """Imprime tabela de candidatos viáveis no terminal."""
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


def _group_summary(report: ResolutionReport) -> Dict[str, Dict[str, int]]:
    """Retorna contagem de veredictos por grupo de glifos ELIS."""
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


def _print_candidate_detail(
    er: ExtendedReport,
    label: str,
    profiles: List[GlyphProfile],
    offer_3d: bool = True,
    viable: Optional[List[ExtendedReport]] = None,
) -> None:
    """Exibe ficha completa de um candidato com relatório de conformidade ISO."""
    from glifo_analise.cli.prompts import _prompt_tactile_3d

    c, r    = er.resolution
    sep_inn = "  " + "-" * 64
    print(f"\n  >>> {label}")
    print(sep_inn)
    print(f"      Resolução declarada : {c}×{r}  @  {er.spacing_mm:.1f} mm/pino")

    eff_res, _ = _effective_resolution(profiles, er.resolution)
    eff_w_mm   = (eff_res[0] - 1) * er.spacing_mm
    eff_h_mm   = (eff_res[1] - 1) * er.spacing_mm
    print(f"      Resolução efetiva   : {eff_res[0]}×{eff_res[1]} pinos  "
          f"→  {eff_w_mm:.1f} × {eff_h_mm:.1f} mm")
    print(f"      Área de célula      : {eff_w_mm * eff_h_mm:.1f} mm²")
    print(f"      Modo tátil          : {er.reading_mode}")
    print(f"      Glifos/tira         : até {er.seq_capacity}  "
          f"(alvo: {SEQ_GLYPH_MIN}–{SEQ_GLYPH_MAX})")
    print(f"      Cobertura útil      : {er.report.coverage_pct:.1f}%"
          f"  ({er.report.apto} aptos / {er.report.total - er.report.blank} com visual)")

    print(f"\n      Conformidade ISO 11548-2 / Psicofísica:")
    checks   = _iso_compliance(er)
    all_pass = True
    for name, ok, detail in checks:
        icon = "✓" if ok else "✗"
        print(f"        [{icon}] {name:<50s}  {detail}")
        if not ok:
            all_pass = False

    verdict = ("APROVADO — todos os critérios ISO satisfeitos" if all_pass
               else "ATENÇÃO  — um ou mais critérios não satisfeitos")
    print(f"\n      Resultado: {verdict}")
    print(sep_inn)

    grid_path = _save_grid(er.report, profiles, er.spacing_mm)
    print(f"      Grade visual : {grid_path.relative_to(pathlib.Path.cwd())}")

    if offer_3d:
        _prompt_tactile_3d(
            {"resolution": list(er.resolution), "spacing_mm": er.spacing_mm},
            profiles,
            viable,
        )
