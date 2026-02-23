# Roadmap — glifo-analise

## Status atual

- ✅ Núcleo Python (`analysis/`, `output/`, `cli/`, `models.py`, `config.py`) — **concluído e testado**
- ✅ CLI (`uv run glifo-analise`) — **funcional**
- ✅ Testes unitários do núcleo (`tests/`) — **concluídos** (99/99 Green)
- ✅ Viewer 3D Three.js (`glifo_analise/gui/static/viewer3d.html`) — **reutilizado no novo frontend**
- ❌ GUI NiceGUI (`glifo_analise/gui/app.py`) — **removida**
- ✅ **Fase 1 — Backend FastAPI** — **CONCLUÍDA** (47/47 testes Green)
- ✅ **Fase 2 — Frontend Vue 3 + Vite** — **CONCLUÍDA** (build OK)
- ✅ **Fase 3 — Integração e Build** — **CONCLUÍDA** (smoke test OK, servidor rodando em http://localhost:8080)

---

## Fases de Migração para Vue 3 + FastAPI

### Fase 1 — Backend FastAPI (`glifo_analise/api/`)

Substituir o `gui/app.py` NiceGUI por um backend FastAPI puro que expõe o núcleo como API.

**Arquivos a criar:**
- `glifo_analise/api/__init__.py`
- `glifo_analise/api/main.py` — FastAPI app; monta routers; serve `frontend/dist/` em `/`
- `glifo_analise/api/state.py` — `AppState` thread-safe com `threading.Lock`
- `glifo_analise/api/ws.py` — `WebSocketManager` para broadcast de progresso
- `glifo_analise/api/routes/__init__.py`
- `glifo_analise/api/routes/analysis.py` — `POST /api/analysis/run`, `GET /api/analysis/status`
- `glifo_analise/api/routes/candidates.py` — `GET /api/candidates`
- `glifo_analise/api/routes/visualization.py` — `POST /api/visualization/generate`
- `glifo_analise/api/routes/model3d.py` — `POST /api/model3d/generate`, `GET /api/model3d/files`
- `glifo_analise/api/routes/files.py` — `GET /output/{filename}` (servir artefatos)

**Atualizar:**
- `pyproject.toml`: remover `nicegui`, adicionar `fastapi`, `uvicorn[standard]`
- Script `glifo-gui` → aponta para `glifo_analise.api.main:run`

---

### Fase 2 — Frontend Vue 3 + Vite (`frontend/`)

Criar o projeto Vue 3 com Vite e implementar todas as views.

**Estrutura:**
```
frontend/
├── package.json          ← vue, vue-router, pinia, three, axios
├── vite.config.ts        ← proxy /api → http://localhost:8080
├── index.html
└── src/
    ├── main.ts
    ├── App.vue           ← layout principal com nav tabs
    ├── router/index.ts
    ├── stores/
    │   ├── analysis.ts   ← dispara análise, recebe logs via WS
    │   ├── candidates.ts ← lista de candidatos + candidato selecionado
    │   └── model3d.ts    ← geração de modelo, lista de arquivos
    ├── views/
    │   ├── AnalysisView.vue       ← botão iniciar + LogStream + barra de progresso
    │   ├── CandidatesView.vue     ← CandidateTable + ficha ISO lateral
    │   ├── VisualizationView.vue  ← seletor tipo + ImageGallery
    │   └── Model3DView.vue        ← controles + Viewer3D + download
    └── components/
        ├── LogStream.vue          ← WebSocket → lista de linhas de log
        ├── CandidateTable.vue     ← tabela filtrável/ordenável
        ├── ImageGallery.vue       ← grid de PNGs com lightbox
        ├── Viewer3D.vue           ← iframe viewer3d.html + postMessage
        └── ElisFontInput.vue      ← input com @font-face ELIS
```

---

### Fase 3 — Integração e Build

1. `vite build` → gera `frontend/dist/`
2. FastAPI serve `frontend/dist/` como `StaticFiles` em `/`
3. `uv run glifo-gui` sobe servidor em `http://localhost:8080`
4. Testar todas as abas ponta a ponta

---

### Fase 4 — Testes E2E com Playwright (opcional)

Cobrir os fluxos principais:
- Executar análise e verificar log em tempo real
- Selecionar candidato na tabela
- Gerar modelo 3D e baixar arquivo
- Gerar visualização e ver imagem na galeria

---

## Ordem de execução recomendada

```
/plan  → detalhar testes unitários para a Fase 1 (rotas FastAPI)
/test  → criar arquivos de teste para api/routes/*.py
impl   → Fase 1 (backend)
       → Fase 2 (frontend)
       → Fase 3 (integração)
       → Fase 4 (E2E, opcional)
```
