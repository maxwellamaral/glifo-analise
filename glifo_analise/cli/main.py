"""
Entry-point do fluxo de análise tátil via terminal.
"""
from __future__ import annotations

import pathlib
from typing import Dict, List

import numpy as np

from glifo_analise.config import (
    FONT_PATH,
    OUTPUT_DIR,
    CANDIDATES_FILE,
    CANDIDATE_RESOLUTIONS,
    PIN_SPACING_MM,
    PIN_DIAMETER_MM,
    MAX_FINGER_AREA_MM,
    HAND_SPAN_MM,
    GAP_BETWEEN_CELLS_MM,
    SEQ_GLYPH_MIN,
    SEQ_GLYPH_MAX,
    PIN_SPACING_CANDIDATES,
    ASYMMETRIC_RESOLUTIONS,
    MAX_MULTI_FINGER_MM,
    MIN_COVERAGE_ECONOMY,
)
from glifo_analise.models import ExtendedReport, GlyphProfile, ResolutionReport
from glifo_analise.analysis.bitmap import _build_profiles, _collect_mapped_codepoints
from glifo_analise.analysis.resolution import _analyze_resolution, _analyze_resolution_ext
from glifo_analise.analysis.physical import _physical_cell_size
from glifo_analise.output.grid import _save_grid
from glifo_analise.output.persistence import _load_candidates, _save_candidates
from glifo_analise.cli.display import (
    _group_summary,
    _print_candidate_detail,
    _print_candidates_table,
)
from glifo_analise.cli.prompts import _generate_from_saved


def main() -> None:
    """Entry-point principal da análise tátil ELIS."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sep = "=" * 68

    # ── [0] Lista salva ────────────────────────────────────────────────────
    saved = _load_candidates()
    if saved:
        print(sep)
        print("  ELIS -- Analise de Viabilidade Tatil para Dispositivo Matricial")
        print(sep)
        print(f"\n  Encontrada lista salva em '{CANDIDATES_FILE.relative_to(pathlib.Path.cwd())}' "
              f"com {len(saved)} candidatos.")
        resp_pre = input(
            "  Deseja consultar a lista salva antes de processar? [S/n]: "
        ).strip().lower()
        if resp_pre in ("", "s", "sim", "y", "yes"):
            print("\n  Carregando perfis para renderização...")
            cps_pre   = _collect_mapped_codepoints(FONT_PATH)
            prfs_pre  = _build_profiles(cps_pre, FONT_PATH)
            if _generate_from_saved(saved, prfs_pre):
                return

    print(sep)
    print("  ELIS -- Analise de Viabilidade Tatil para Dispositivo Matricial")
    print(sep)

    if CANDIDATES_FILE.exists():
        CANDIDATES_FILE.unlink()
        print(f"  [info] Lista anterior removida: {CANDIDATES_FILE.name}")

    # ── [1] Perfis ─────────────────────────────────────────────────────────
    print("\n[1/4] Carregando glifos e calculando perfis de referencia (64x64)...")
    codepoints = _collect_mapped_codepoints(FONT_PATH)
    profiles   = _build_profiles(codepoints, FONT_PATH)
    real_glyphs = [p for p in profiles if p.density > 0]
    dens = [p.density for p in real_glyphs]
    print(f"      {len(profiles)} glifos no cmap  |  {len(real_glyphs)} com conteudo visual")
    print(f"      Densidade media  : {np.mean(dens):.3f}  "
          f"(min {np.min(dens):.3f} / max {np.max(dens):.3f})")

    # ── [2] Parâmetros físicos ─────────────────────────────────────────────
    print("\n[2/4] Parametros fisicos do dispositivo:")
    print(f"      Espaco entre pinos : {PIN_SPACING_MM} mm  (ISO 11548-2 / Braille)")
    print(f"      Diametro do pino   : {PIN_DIAMETER_MM} mm")
    print(f"      Gap entre pinos    : {PIN_SPACING_MM - PIN_DIAMETER_MM} mm")
    print(f"      Limite 1 dedo      : <= {MAX_FINGER_AREA_MM:.0f} mm")
    for res in CANDIDATE_RESOLUTIONS:
        phys = _physical_cell_size(res)
        flag = "ok - 1 dedo" if phys <= MAX_FINGER_AREA_MM else "atencao - requer exploracao"
        print(f"      {res[0]:2d}x{res[1]:2d}  ->  {phys:.1f} mm x {phys:.1f} mm  [{flag}]")

    # ── [3] Análise básica ─────────────────────────────────────────────────
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

    # ── [4] Grades visuais ─────────────────────────────────────────────────
    print("\n[4/4] Gerando grades visuais...")
    for r in reports:
        path = _save_grid(r, profiles)
        print(f"    -> {path.relative_to(pathlib.Path.cwd())}")

    # ── Resultado final básico ─────────────────────────────────────────────
    print(f"\n{sep}")
    print("  RESULTADO FINAL")
    print(sep)
    VORD = ["APTO", "VAZIO", "SATURADO", "RASO", "PERDA_ESTRUTURAL", "TAMANHO_GRANDE"]
    best: ResolutionReport | None = None
    for r in reports:
        tag = ("RECOMENDADO " if r.fits_finger and r.coverage_pct >= 90 else
               "PARCIAL      " if r.coverage_pct >= 70 else "INSUFICIENTE ")
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
    print(f"\n  Grades em: {OUTPUT_DIR.relative_to(pathlib.Path.cwd())}/")
    print(sep)

    # ── [5] Análise estendida ──────────────────────────────────────────────
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
            er = _analyze_resolution_ext(res[0], res[1], sp, profiles)
            ext_results.append(er)

    viable = [
        er for er in ext_results
        if er.reading_mode != "fora-de-alcance"
        and er.seq_in_range
        and er.report.coverage_pct >= 80.0
    ]
    viable.sort(key=lambda e: (
        -e.report.coverage_pct,
        -e.seq_capacity,
        -e.spacing_mm,
        e.cell_w_mm * e.cell_h_mm,
    ))

    _save_candidates(viable)
    print(f"  Lista de candidatos salva em '{CANDIDATES_FILE.relative_to(pathlib.Path.cwd())}'")

    print(f"\n  Candidatos viaveis ({len(viable)} encontrados):")
    saved_display = _load_candidates()
    _print_candidates_table(saved_display[:25])

    best_seq = viable[0] if viable else None
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

    if best_economy is not None and best_economy is not best_seq:
        _print_candidate_detail(
            best_economy,
            f"Melhor candidato econômico — menor área física com cobertura >= "
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
