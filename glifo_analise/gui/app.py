"""
Interface gráfica NiceGUI para análise de viabilidade tátil ELIS.

Painéis:
  - Análise      : executa o pipeline completo com log em streaming
  - Candidatos   : tabela interativa dos candidatos viáveis
  - Visualização : galeria de PNGs gerados
  - Modelo 3D    : geração e download de STL/3MF
"""
from __future__ import annotations

import asyncio
import io
import pathlib
import sys
from typing import Any, Dict, List, Optional

from nicegui import app, ui

from glifo_analise import config
from glifo_analise.analysis.bitmap import _build_profiles, _collect_mapped_codepoints
from glifo_analise.analysis.resolution import _analyze_resolution, _analyze_resolution_ext
from glifo_analise.models import ExtendedReport, GlyphProfile, ResolutionReport
from glifo_analise.output.grid import _save_grid
from glifo_analise.output.model3d import _generate_tactile_3d
from glifo_analise.output.persistence import _load_candidates, _save_candidates

# ── Estado global da sessão ──────────────────────────────────────────────────
class _State:
    profiles:      List[GlyphProfile]     = []
    reports:       List[ResolutionReport]  = []
    ext_results:   List[ExtendedReport]    = []
    viable:        List[Dict[str, Any]]    = []
    last_model:    Optional[pathlib.Path]  = None
    analysis_step: int = 0  # 0-5


_S = _State()
config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ── Captura de stdout para a fila de log ─────────────────────────────────────
class _QueueStream(io.TextIOBase):
    """Redireciona print() de uma thread worker para uma asyncio.Queue."""

    def __init__(self, queue: "asyncio.Queue[str]", loop: asyncio.AbstractEventLoop) -> None:
        self._q = queue
        self._loop = loop

    def write(self, s: str) -> int:
        stripped = s.rstrip("\n")
        if stripped:
            self._loop.call_soon_threadsafe(self._q.put_nowait, stripped)
        return len(s)

    def flush(self) -> None:
        pass


# ── Lógica de análise (executada em thread separada) ─────────────────────────
def _run_analysis_sync(q: "asyncio.Queue[str]", loop: asyncio.AbstractEventLoop) -> None:
    """Pipeline completo. Todo print() vai para a fila e aparece no log da UI."""
    import numpy as np

    old_stdout = sys.stdout
    sys.stdout = _QueueStream(q, loop)  # type: ignore[assignment]
    try:
        # [1] Perfis
        print("[1/5] Carregando glifos da fonte ELIS...")
        codepoints = _collect_mapped_codepoints(config.FONT_PATH)
        _S.profiles = _build_profiles(codepoints, config.FONT_PATH)
        real = [p for p in _S.profiles if p.density > 0]
        dens = [p.density for p in real]
        print(f"      {len(_S.profiles)} glifos no cmap — {len(real)} com conteúdo visual")
        print(f"      Densidade média: {np.mean(dens):.3f}  "
              f"(min {np.min(dens):.3f} / max {np.max(dens):.3f})")
        _S.analysis_step = 1

        # [2] Resoluções básicas
        print("\n[2/5] Analisando resoluções básicas...")
        _S.reports = []
        for res in config.CANDIDATE_RESOLUTIONS:
            r = _analyze_resolution(_S.profiles, res)
            _S.reports.append(r)
            print(f"      {res[0]}x{res[1]}  → cobertura {r.coverage_pct:.1f}%  "
                  f"({'ok - 1 dedo' if r.fits_finger else 'multi-dedo'})")
        _S.analysis_step = 2

        # [3] Grades visuais
        print("\n[3/5] Gerando grades visuais...")
        config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        for r in _S.reports:
            path = _save_grid(r, _S.profiles)
            print(f"      → {path.name}")
        _S.analysis_step = 3

        # [4] Análise estendida (M×N × espaçamento)
        all_res = list(dict.fromkeys(config.CANDIDATE_RESOLUTIONS + config.ASYMMETRIC_RESOLUTIONS))
        total = len(all_res) * len(config.PIN_SPACING_CANDIDATES)
        print(f"\n[4/5] Análise estendida — {total} combinações (resolução × espaçamento)...")
        _S.ext_results = []
        done = 0
        step_report = max(1, total // 10)
        for res in all_res:
            for sp in config.PIN_SPACING_CANDIDATES:
                er = _analyze_resolution_ext(res[0], res[1], sp, _S.profiles)
                _S.ext_results.append(er)
                done += 1
                if done % step_report == 0:
                    print(f"      {done}/{total}  ({done * 100 // total}%)")
        _S.analysis_step = 4

        # [5] Candidatos viáveis
        print("\n[5/5] Selecionando candidatos viáveis (cobertura ≥ 80%)...")
        viable_er = [
            er for er in _S.ext_results
            if er.reading_mode != "fora-de-alcance"
            and er.seq_in_range
            and er.report.coverage_pct >= 80.0
        ]
        viable_er.sort(key=lambda e: (
            -e.report.coverage_pct,
            -e.seq_capacity,
            e.cell_w_mm * e.cell_h_mm,
        ))
        _save_candidates(viable_er)
        _S.viable = _load_candidates()
        _S.analysis_step = 5
        print(f"\n✓ Concluído — {len(_S.viable)} candidatos viáveis salvos em "
              f"'{config.CANDIDATES_FILE.name}'.")
    except Exception as exc:
        print(f"\n[ERRO] {exc}")
        raise
    finally:
        sys.stdout = old_stdout


# ── Painel: Análise ──────────────────────────────────────────────────────────
def _build_analysis_panel() -> None:
    with ui.column().classes("w-full gap-4"):
        ui.label("▶ Análise Completa de Viabilidade Tátil").classes("text-2xl font-bold text-gray-800")
        with ui.row().classes("text-sm text-gray-500 gap-6"):
            ui.label(f"Fonte: {config.FONT_PATH}")
            ui.label(f"Saída: {config.OUTPUT_DIR}")

        progress = ui.linear_progress(value=0).props('stripe color="green"').classes("w-full h-3 rounded")
        log = ui.log(max_lines=1000).classes("w-full h-96 font-mono text-sm bg-gray-900 text-green-300 rounded p-2")

        btn_run = ui.button("▶  Iniciar Análise", icon="play_arrow").classes(
            "bg-green-600 text-white text-base px-6 py-2"
        )

        async def _on_run() -> None:
            btn_run.disable()
            log.clear()
            progress.set_value(0)
            _S.analysis_step = 0

            loop = asyncio.get_running_loop()
            q: asyncio.Queue[str] = asyncio.Queue()

            async def _drain() -> None:
                while True:
                    try:
                        msg = q.get_nowait()
                        log.push(msg)
                    except asyncio.QueueEmpty:
                        break

            future = loop.run_in_executor(None, _run_analysis_sync, q, loop)

            while not future.done():
                await _drain()
                progress.set_value(_S.analysis_step / 5)
                await asyncio.sleep(0.2)

            await _drain()
            progress.set_value(1.0)

            try:
                await future
                ui.notify("Análise concluída! Consulte as demais abas.", type="positive", timeout=5000)
            except Exception as exc:
                ui.notify(f"Erro na análise: {exc}", type="negative", timeout=0)
            finally:
                btn_run.enable()

        btn_run.on("click", _on_run)


# ── Painel: Candidatos ───────────────────────────────────────────────────────
def _build_candidates_panel() -> None:
    with ui.column().classes("w-full gap-4"):
        ui.label("📋 Candidatos Viáveis").classes("text-2xl font-bold text-gray-800")
        ui.label(
            "Candidatos com cobertura ≥ 80%, modo de leitura válido e capacidade sequencial na faixa configurada."
        ).classes("text-sm text-gray-500")

        columns = [
            {"name": "rank",         "label": "#",           "field": "rank",         "sortable": True, "align": "center"},
            {"name": "resolution",   "label": "Resolução",   "field": "resolution",   "sortable": True, "align": "center"},
            {"name": "spacing_mm",   "label": "Espaç. (mm)", "field": "spacing_mm",   "sortable": True, "align": "right"},
            {"name": "cell_w_mm",    "label": "W (mm)",      "field": "cell_w_mm",    "sortable": True, "align": "right"},
            {"name": "cell_h_mm",    "label": "H (mm)",      "field": "cell_h_mm",    "sortable": True, "align": "right"},
            {"name": "reading_mode", "label": "Modo",        "field": "reading_mode", "sortable": True},
            {"name": "seq_capacity", "label": "Cap. Seq.",   "field": "seq_capacity", "sortable": True, "align": "right"},
            {"name": "coverage_pct", "label": "Cobertura %", "field": "coverage_pct", "sortable": True, "align": "right"},
        ]

        table = ui.table(
            columns=columns, rows=[], row_key="rank",
            pagination={"rowsPerPage": 20},
        ).classes("w-full")
        table.add_slot("top-right", r"""
            <q-input debounce="300" v-model="filter" placeholder="Filtrar…" dense outlined clearable>
                <template v-slot:prepend><q-icon name="search"/></template>
            </q-input>
        """)

        count_label = ui.label("").classes("text-sm text-gray-500")

        def _reload() -> None:
            rows = _load_candidates()
            for r in rows:
                if isinstance(r.get("resolution"), list):
                    r["resolution"] = f"{r['resolution'][0]}×{r['resolution'][1]}"
                r["cell_w_mm"]    = round(float(r.get("cell_w_mm",    0)), 2)
                r["cell_h_mm"]    = round(float(r.get("cell_h_mm",    0)), 2)
                r["coverage_pct"] = round(float(r.get("coverage_pct", 0)), 1)
            table.rows = rows
            table.update()
            count_label.set_text(f"{len(rows)} candidatos carregados.")

        ui.button("🔄 Recarregar", on_click=_reload, icon="refresh").classes("mt-1")
        _reload()


# ── Painel: Visualização ─────────────────────────────────────────────────────
def _build_visualization_panel() -> None:
    with ui.column().classes("w-full gap-4"):
        ui.label("🖼 Galeria de Imagens Geradas").classes("text-2xl font-bold text-gray-800")

        gallery = ui.row().classes("w-full flex-wrap gap-4 mt-2")

        def _refresh() -> None:
            gallery.clear()
            pngs = sorted(config.OUTPUT_DIR.glob("*.png"))
            if not pngs:
                with gallery:
                    ui.label("Nenhuma imagem encontrada. Execute a análise primeiro.").classes(
                        "text-gray-500 italic"
                    )
                return
            for p in pngs:
                with gallery:
                    with ui.card().classes("w-64 shadow-md"):
                        ui.image(f"/output/{p.name}").classes("w-full rounded-t cursor-pointer")
                        with ui.card_section().classes("p-2"):
                            ui.label(p.name).classes("text-xs truncate")
                            ui.link("⬇ download", f"/output/{p.name}", new_tab=True).classes(
                                "text-blue-500 text-xs"
                            )

        ui.button("🔄 Atualizar Galeria", on_click=_refresh, icon="refresh")
        _refresh()


# ── Painel: Modelo 3D ────────────────────────────────────────────────────────
def _build_model3d_panel() -> None:
    with ui.column().classes("w-full gap-4"):
        ui.label("🖨 Geração de Modelo 3D Tátil").classes("text-2xl font-bold text-gray-800")
        ui.label(
            "Selecione um candidato viável, informe a sequência de glifos e gere o arquivo para impressão 3D."
        ).classes("text-sm text-gray-500")

        # ── Controles ────────────────────────────────────────────────────────
        with ui.row().classes("w-full flex-wrap gap-4 items-end"):
            seq_input = ui.input(
                label="Sequência de glifos",
                value=config.DEFAULT_TACTILE_SEQUENCE,
                placeholder="ex: tqlDà",
            ).classes("w-48")
            fmt_sel = ui.select(["3mf", "stl"], value="3mf", label="Formato").classes("w-28")
            full_test_cb = ui.checkbox("Teste completo (todos os pinos)", value=False)

        cand_sel = ui.select(
            options=[],
            label="Candidato",
            value=None,
        ).classes("w-full")

        # Mapa label → dict candidato
        _opts_map: Dict[str, dict] = {}

        def _populate() -> None:
            _opts_map.clear()
            rows = _load_candidates()
            for r in rows:
                res = r.get("resolution", [0, 0])
                res_str = f"{res[0]}×{res[1]}" if isinstance(res, list) else str(res)
                label = (
                    f"#{r['rank']}  {res_str} @ {r['spacing_mm']} mm  "
                    f"— cobertura {r.get('coverage_pct', 0):.1f}%  [{r.get('reading_mode', '')}]"
                )
                _opts_map[label] = r
            cand_sel.options = list(_opts_map.keys())
            cand_sel.update()
            if _opts_map:
                cand_sel.set_value(list(_opts_map.keys())[0])

        ui.button("🔄 Recarregar candidatos", on_click=_populate, icon="refresh")
        _populate()

        # ── Resultado ────────────────────────────────────────────────────────
        status_label   = ui.label("").classes("text-sm text-gray-600 italic")
        download_area  = ui.row().classes("mt-2")

        btn_gen = ui.button("🖨  Gerar Modelo 3D", icon="print").classes(
            "bg-blue-600 text-white text-base px-6 py-2 mt-2"
        )

        async def _on_generate() -> None:
            sel = cand_sel.value
            if not sel:
                ui.notify("Selecione um candidato primeiro.", type="warning")
                return
            if not _S.profiles:
                ui.notify(
                    "Execute a análise completa na aba Análise para carregar os perfis de glifos.",
                    type="warning",
                    timeout=5000,
                )
                return

            candidate_raw = _opts_map.get(sel)
            if not candidate_raw:
                ui.notify("Candidato não encontrado.", type="warning")
                return

            # Normaliza para o formato esperado por _generate_tactile_3d
            res = candidate_raw.get("resolution", [13, 13])
            if isinstance(res, list):
                cols, rows = res[0], res[1]
            else:
                cols, rows = 13, 13
            sp = float(candidate_raw.get("spacing_mm", 2.5))
            candidate_full: dict = {
                **candidate_raw,
                "cols":         cols,
                "rows":         rows,
                "spacing_mm":   sp,
                "cell_w_mm":    float(candidate_raw.get("cell_w_mm", (cols - 1) * sp)),
                "cell_h_mm":    float(candidate_raw.get("cell_h_mm", (rows - 1) * sp)),
                "resolution":   (cols, rows),
                "reading_mode": candidate_raw.get("reading_mode", "1-dedo"),
                "seq_capacity": int(candidate_raw.get("seq_capacity", 4)),
                "eff_cols":     cols,
                "eff_rows":     rows,
            }

            btn_gen.disable()
            status_label.set_text("⏳ Gerando modelo 3D…")
            download_area.clear()

            seq_val       = seq_input.value or config.DEFAULT_TACTILE_SEQUENCE
            fmt_val       = fmt_sel.value or "3mf"
            full_test_val = full_test_cb.value

            def _work() -> pathlib.Path:
                return _generate_tactile_3d(
                    sequence=seq_val,
                    candidate=candidate_full,
                    profiles=_S.profiles,
                    fmt=fmt_val,
                    full_test=full_test_val,
                    out_dir=config.OUTPUT_DIR,
                )

            try:
                loop = asyncio.get_running_loop()
                path = await loop.run_in_executor(None, _work)
                _S.last_model = path
                status_label.set_text(f"✓ Gerado: {path.name}")
                with download_area:
                    ui.link(
                        f"⬇  Baixar {path.name}",
                        f"/output/{path.name}",
                        new_tab=True,
                    ).classes("text-blue-600 underline text-base")
                ui.notify(f"Modelo gerado: {path.name}", type="positive")
            except Exception as exc:
                status_label.set_text(f"❌ Erro: {exc}")
                ui.notify(str(exc), type="negative", timeout=0)
            finally:
                btn_gen.enable()

        btn_gen.on("click", _on_generate)


# ── Ponto de entrada ─────────────────────────────────────────────────────────
def run() -> None:
    """Inicia a interface gráfica NiceGUI em http://localhost:8080."""
    # Serve o diretório de saída como arquivos estáticos (imagens, modelos 3D)
    app.add_static_files("/output", str(config.OUTPUT_DIR))

    @ui.page("/")
    def _index() -> None:
        ui.query("body").style("background-color: #f0f2f5")

        with ui.header().classes("bg-gray-900 text-white items-center justify-between px-8 py-3"):
            with ui.row().classes("items-center gap-3"):
                ui.icon("touch_app", size="28px").classes("text-green-400")
                ui.label("ELIS — Análise de Viabilidade Tátil").classes("text-lg font-bold")
            ui.label("ISO 11548-2 · Dispositivo Matricial de Pinos").classes("text-sm opacity-60")

        with ui.tabs().classes("bg-white shadow-sm px-4") as tabs:
            t_analise  = ui.tab("analise",    label="Análise",      icon="science")
            t_cands    = ui.tab("candidatos", label="Candidatos",   icon="list_alt")
            t_visual   = ui.tab("visual",     label="Visualização", icon="image")
            t_model3d  = ui.tab("modelo3d",   label="Modelo 3D",    icon="view_in_ar")

        with ui.tab_panels(tabs, value=t_analise).classes("w-full"):
            with ui.tab_panel(t_analise).classes("p-6"):
                _build_analysis_panel()
            with ui.tab_panel(t_cands).classes("p-6"):
                _build_candidates_panel()
            with ui.tab_panel(t_visual).classes("p-6"):
                _build_visualization_panel()
            with ui.tab_panel(t_model3d).classes("p-6"):
                _build_model3d_panel()

    ui.run(
        title="ELIS — Análise Tátil",
        port=8080,
        host="127.0.0.1",
        reload=False,
        show=True,
        dark=False,
        favicon="🖐",
    )
