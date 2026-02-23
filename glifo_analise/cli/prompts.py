"""
Prompts interativos de terminal para o fluxo da CLI.
"""
from __future__ import annotations

import pathlib
from typing import List, Optional

from glifo_analise.config import OUTPUT_DIR
from glifo_analise.models import ExtendedReport, GlyphProfile
from glifo_analise.analysis.bitmap import _effective_resolution
from glifo_analise.analysis.resolution import _analyze_resolution_ext
from glifo_analise.output.grid import _save_grid
from glifo_analise.output.model3d import DEFAULT_TACTILE_SEQUENCE, _generate_tactile_3d
from glifo_analise.cli.display import _print_candidates_table


def _generate_from_saved(
    candidates: List[dict],
    profiles: List[GlyphProfile],
) -> bool:
    """
    Exibe lista salva, solicita escolha do usuário e gera a grade.

    Returns:
        True se uma grade foi gerada e o fluxo deve encerrar.
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
    res    = tuple(chosen["resolution"])   # type: ignore[arg-type]
    sp     = chosen["spacing_mm"]

    print(f"\n  Gerando grade para {res[0]}x{res[1]} @ {sp:.1f} mm...")
    er = _analyze_resolution_ext(res[0], res[1], sp, profiles)
    grid_path = _save_grid(er.report, profiles, er.spacing_mm)
    print(f"  Grade salva em: {grid_path.relative_to(pathlib.Path.cwd())}")
    print(f"  Cobertura: {er.report.coverage_pct:.1f}%  |  "
          f"Modo: {er.reading_mode}  |  Seq: {er.seq_capacity} glifos/tira")

    _prompt_tactile_3d(chosen, profiles)
    print(sep)
    return True


def _prompt_tactile_3d(
    candidate: dict,
    profiles: List[GlyphProfile],
    viable: Optional[List[ExtendedReport]] = None,
) -> None:
    """Pergunta ao usuário se deseja gerar modelo 3D e o produz."""
    if viable:
        prompt = (
            f"\n  Deseja gerar modelo 3D tátil para impressão?\n"
            f"  [S = este candidato  /  1-{len(viable)} = escolher da lista  /"
            f"  T = glifo de teste (todos os pinos)  /  N = não]: "
        )
    else:
        prompt = (
            "\n  Deseja gerar modelo 3D tátil para impressão?\n"
            "  [S = gerar glifo  /  T = glifo de teste (todos os pinos)  /  N = não]: "
        )

    resp3d = input(prompt).strip().lower()

    if resp3d in ("n", "nao", "não", "no"):
        return

    full_test = resp3d in ("t", "teste", "test")

    if not full_test:
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

    fmt_resp = input("  Formato [3mf/stl, padrão 3mf]: ").strip().lower()
    fmt = "stl" if fmt_resp == "stl" else "3mf"

    if full_test:
        cols, rows = candidate["resolution"]
        sp = candidate["spacing_mm"]
        print(
            f"  Gerando glifo de teste ({fmt.upper()}): "
            f"{cols}×{rows} pinos (resolução declarada) @ {sp:.1f} mm  "
            f"→  {(cols-1)*sp:.1f} × {(rows-1)*sp:.1f} mm ..."
        )
        try:
            out = _generate_tactile_3d("", candidate, profiles, fmt=fmt, full_test=True)
            print(f"  Modelo salvo em: {out.relative_to(pathlib.Path.cwd())}")
            png = out.with_name(out.stem + "_preview.png")
            if png.exists():
                print(f"  Preview PNG   : {png.relative_to(pathlib.Path.cwd())}")
        except Exception as exc:
            print(f"  [ERRO] Não foi possível gerar o modelo de teste 3D: {exc}")
        return

    seq = input(
        f"  Sequência de glifos ELIS [{DEFAULT_TACTILE_SEQUENCE}]: "
    ).strip()
    if not seq:
        seq = DEFAULT_TACTILE_SEQUENCE

    print(f"  Gerando modelo 3D ({fmt.upper()}) para sequência: {seq!r} ...")
    try:
        out = _generate_tactile_3d(seq, candidate, profiles, fmt=fmt)
        print(f"  Modelo salvo em: {out.relative_to(pathlib.Path.cwd())}")
        png = out.with_name(out.stem + "_preview.png")
        if png.exists():
            print(f"  Preview PNG   : {png.relative_to(pathlib.Path.cwd())}")
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
