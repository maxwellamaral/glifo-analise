# Roadmap — glifo-analise

## Fases de Implementação

### Fase 1 — Testes do Núcleo (TDD Red → Green → Refactor)

Antes de qualquer reestruturação, escrever a bateria de testes unitários
que valida o comportamento atual de `main.py`. Esses testes guiarão a
refatoração: se continuarem verdes após a extração dos módulos, a
reestruturação está correta.

Arquivos de teste a criar (fase `/test`):
- `tests/__init__.py`
- `tests/test_config.py` — constantes e grupos de glifos
- `tests/test_models.py` — criação e campos dos dataclasses
- `tests/test_bitmap.py` — _render_bitmap, _pixel_density, _edge_complexity, _iou, _effective_resolution
- `tests/test_physical.py` — _physical_cell_size, _physical_cell_size_mn, _sequence_capacity
- `tests/test_resolution.py` — _analyze_resolution_ext (mocked profiles)
- `tests/test_iso.py` — _iso_compliance (todos os 9 critérios)
- `tests/test_persistence.py` — save/load candidates JSON (tmp_path fixture)
- `tests/test_grid.py` — _save_grid gera PNG com dimensões corretas
- `tests/test_preview.py` — _generate_tactile_preview_png gera PNG com pixels corretos
- `tests/test_model3d.py` — _generate_tactile_3d gera STL/3MF com nº correto de componentes

---

### Fase 2 — Reestruturação do Pacote (Refactor)

Criar o pacote `glifo_analise/` extraindo o código de `main.py` para os
módulos definidos em `specs/architecture.md`. Todos os testes da Fase 1
devem continuar verdes após cada extração.

Ordem de extração (do menos dependente para o mais dependente):

1. `glifo_analise/config.py` ← constantes e GLYPH_GROUPS
2. `glifo_analise/models.py` ← dataclasses
3. `glifo_analise/analysis/bitmap.py`
4. `glifo_analise/analysis/physical.py`
5. `glifo_analise/analysis/resolution.py`
6. `glifo_analise/analysis/iso.py`
7. `glifo_analise/output/persistence.py`
8. `glifo_analise/output/grid.py`
9. `glifo_analise/output/model3d.py`
10. `glifo_analise/output/preview.py`
11. `glifo_analise/cli/display.py`
12. `glifo_analise/cli/prompts.py`
13. `glifo_analise/cli/main.py`
14. Shims `main.py` e `gui.py` na raiz
15. Atualizar `pyproject.toml` (scripts, dependências)

---

### Fase 3 — GUI NiceGUI

1. `glifo_analise/gui/state.py` — `AppState` dataclass + defaults de `config.py`
2. `glifo_analise/gui/panels/settings.py` — formulários NiceGUI para todos os parâmetros
3. `glifo_analise/gui/panels/analysis.py` — botão de análise + log streaming (background thread)
4. `glifo_analise/gui/panels/candidates.py` — `ui.table` interativa + seleção de candidato
5. `glifo_analise/gui/panels/viewer.py` — galeria `ui.image` dos PNGs em `output/`
6. `glifo_analise/gui/panels/model3d.py` — controles de geração 3D + `ui.download`
7. `glifo_analise/gui/app.py` — montagem de abas + `ui.run()`
8. Shim `gui.py` na raiz

---

### Fase 4 — Integração e Documentação

1. README.md atualizado com nova estrutura e instruções de uso GUI+CLI
2. Testes de smoke da GUI (opcional — NiceGUI test client)
3. `uv run glifo-analise` (CLI) e `uv run glifo-gui` (GUI) validados de ponta a ponta
