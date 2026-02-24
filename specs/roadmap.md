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
- ✅ **Fase 5 — Parâmetros Configuráveis de Análise** — **CONCLUÍDA**
  - `GET /api/analysis/params/defaults` expõe os 9 parâmetros do núcleo
  - `POST /api/analysis/run` aceita `AnalysisParams` opcional no body
  - Painel colapsável em `AnalysisView.vue` com 4 seções e botão "Restaurar padrões"
- ✅ **Fase 6 — Autoria, Citação e Licença** — **CONCLUÍDA**
  - `LICENSE` (MIT + cláusula de atribuição), `CITATION.bib` (BibLaTeX + ABNT), `CITATION.cff` (CFF v1.2)
  - `README.md` com seções "Autoria e Citação" e "Licença"
  - Rodapé permanente em `App.vue` com autor, copyright e badge de licença
- ✅ **Fase 7 — Mapa de Glifos ELIS (GlyphPickerModal)** — **CONCLUÍDA**
  - `GET /api/analysis/glyphs` retorna todos os glifos ELIS agrupados
  - `GlyphPickerModal.vue` — modal estilo Character Map com abas por grupo,
    painel de prévia, inserção imediata e remoção Unicode-safe
  - Integrado em `VisualizationView.vue` e `Model3DView.vue`
- ✅ **Fase 8 — Suporte a Docker** — **CONCLUÍDA**
  - `docker/Dockerfile` multi-stage: estágios `frontend-build` (node:22-slim),
    `python-deps` (python:3.12-slim + uv) e `final`
  - `docker/docker-compose.yml` com volume mapeado para `./output/`
  - `docker/manage.sh` com comandos `build / up / down / restart / logs / shell / status / clean`
  - `.dockerignore` na raiz do projeto
  - Build validado: **17.7 s** na primeira execução; re-build sem mudança de deps
    usa 100% de cache (< 2 s)
  - Testado: `GET /api/analysis/status` e `GET /api/analysis/glyphs` respondendo
    corretamente dentro do container

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

### Fase 5 — Parâmetros Configuráveis de Análise ✅

Expor os parâmetros do núcleo Python na GUI para que o usuário possa customizá-los
sem editar código ou reiniciar o servidor.

**Backend:**
- `AnalysisParams` (Pydantic) com os 9 parâmetros e seus padrões
- `GET /api/analysis/params/defaults` → retorna defaults de `config.py`
- `POST /api/analysis/run` aceita `params?: AnalysisParams` no body

**Frontend:**
- `AnalysisParams` interface + `fetchDefaults()` em `stores/analysis.ts`
- Painel colapsável em `AnalysisView.vue` com 4 seções:
  Resoluções, Espaçamento de Pinos, Parâmetros Físicos, Limiares
- Resumo dos valores ativos quando recolhido; botão "Restaurar padrões"

---

### Fase 6 — Autoria, Citação e Licença ✅

Formalizar propriedade intelectual e facilitar citação acadêmica.

**Arquivos criados:**
- `LICENSE` — MIT com cláusula de atribuição obrigatória ao autor original
- `CITATION.bib` — BibLaTeX `@software` + `@misc` ABNT
- `CITATION.cff` — Citation File Format v1.2 (GitHub exibe botão "Cite this repository")
- `README.md` — seções "Autoria e Citação" (APA, ABNT, BibLaTeX) e "Licença"
- `App.vue` — rodapé permanente com nome do autor, link e badge de licença

---

### Fase 7 — Mapa de Glifos ELIS (GlyphPickerModal) ✅

Modal estilo "Mapa de Caracteres" do Windows para seleção de glifos ELIS
nos campos "Sequência" das abas Visualização e Modelo 3D.

**Backend:**
- `GET /api/analysis/glyphs` → lista `[{codepoint, char, group}]` de todos os
  glifos não-brancos mapeados na fonte ELIS, agrupados por categoria

**Frontend — `GlyphPickerModal.vue`:**
- Abas de grupo: Todos / Maiúsculas / Minúsculas / Dígitos / Símbolos / Estendidos
- Grid `auto-fill 42 × 42px` com cada glifo renderizado em `font-family: 'ELIS'`
- Painel de prévia lateral: glifo em 5rem + codepoint U+XXXX + nome do grupo
- Inserção imediata ao clicar (emite `update:modelValue` sem precisar confirmar)
- Botões: ⌫ (remove último glifo, Unicode-safe via spread), ✕ (limpar), Confirmar
- Fecha via Escape ou clique na sobreposição; montado via `<Teleport to="body">`
- Integrado em `VisualizationView.vue` e `Model3DView.vue`

### Fase 8 — Suporte a Docker ✅

Permitir execução do sistema em container sem instalar Python, Node.js ou `uv`
no host. Uso opcional e totalmente compatível com o modo nativo (`uv run glifo-gui`).

**Arquivos criados em `docker/`:**
- `Dockerfile` — build multi-stage com foco em cache de camadas:
  1. `frontend-build` (node:22-slim): `npm ci` → `npm run build` → gera `dist/`
  2. `python-deps` (python:3.12-slim + uv): copia apenas `pyproject.toml` + `uv.lock`;
     `uv sync --frozen --no-dev --no-install-project` (cache quebrado só com `uv.lock`)
  3. `final`: copia `.venv/` + código-fonte, `uv sync --frozen --no-dev`, copia `dist/`
- `docker-compose.yml` — sobe o serviço na porta 8080; volume `./output:/app/output`
- `manage.sh` — wrapper com comandos: `build / up / down / restart / logs / shell / status / clean`
- `.dockerignore` — na raiz do projeto; exclui `.venv/`, `frontend/dist/`, `output/`, `tests/`, etc.

**Resultado dos testes:**
- Build: 17.7 s (primeiro build); rebuild sem mudança de deps < 2 s (cache 100%)
- `GET /api/analysis/status` → `{"status":"idle"}` ✔
- `GET /api/analysis/glyphs` → 145 glifos ELIS ✔

---

## Ordem de execução recomendada

```
/plan  → detalhar testes unitários para a Fase 1 (rotas FastAPI)
/test  → criar arquivos de teste para api/routes/*.py
impl   → Fase 1 (backend)          ✅ concluída
       → Fase 2 (frontend)         ✅ concluída
       → Fase 3 (integração)       ✅ concluída
       → Fase 4 (E2E, opcional)
       → Fase 5 (params análise)   ✅ concluída
       → Fase 6 (autoria/citação)  ✅ concluída
       → Fase 7 (GlyphPickerModal) ✅ concluída
       → Fase 8 (Docker)           ✅ concluída
```
