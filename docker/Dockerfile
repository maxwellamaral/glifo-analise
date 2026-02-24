# =============================================================================
# Glifo Análise — Multi-stage Dockerfile
# -----------------------------------------------------------------------------
# Estágio 1: Build do frontend Vue 3 / Vite          (node:22-slim)
# Estágio 2: Instalação de deps Python com uv         (python:3.12-slim)
# Estágio 3: Imagem final mínima                      (python:3.12-slim + uv)
#
# Cache: deps do Node e do Python são re-instaladas SOMENTE quando os arquivos
# de lockfile (package-lock.json / uv.lock) mudam.
# =============================================================================


# ── Estágio 1: build do frontend ──────────────────────────────────────────────
FROM node:22-slim AS frontend-build

WORKDIR /app/frontend

# Instalar deps primeiro (cache quebrado só quando package-lock.json mudar)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copiar código-fonte e buildar
COPY frontend/ .
RUN npm run build


# ── Estágio 2: dependências Python via uv ─────────────────────────────────────
FROM python:3.12-slim AS python-deps

# Copiar o binário do uv da imagem oficial Astral
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copiar apenas manifesto e lockfile — cache quebrado só quando uv.lock mudar
COPY pyproject.toml uv.lock ./

# Instalar dependências de produção no venv local (.venv)
# --no-install-project: pula a instalação do pacote em si (código-fonte ainda não copiado)
RUN uv sync --frozen --no-dev --no-install-project


# ── Estágio 3: imagem final ───────────────────────────────────────────────────
FROM python:3.12-slim AS final

LABEL org.opencontainers.image.title="Glifo Análise" \
      org.opencontainers.image.description="Viabilidade tátil para dispositivo matricial ELIS" \
      org.opencontainers.image.authors="Maxwell Anderson Ielpo do Amaral" \
      org.opencontainers.image.source="https://github.com/maxwellamaral/glifo-analise" \
      org.opencontainers.image.licenses="MIT"

# Copiar uv para a imagem final (necessário para `uv run`)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copiar venv com deps já instaladas do estágio anterior
COPY --from=python-deps /app/.venv /app/.venv

# Copiar manifesto e lockfile
COPY pyproject.toml uv.lock ./

# Copiar código-fonte Python e asset da fonte ELIS
COPY glifo_analise/ glifo_analise/
COPY elis.ttf ./

# Instalar o projeto em si no venv (deps já presentes — apenas registra scripts)
RUN uv sync --frozen --no-dev

# Copiar frontend compilado do estágio 1
COPY --from=frontend-build /app/frontend/dist frontend/dist/

# Criar diretório de saída (persistido via volume em produção)
RUN mkdir -p output

# Colocar o venv no PATH
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8080

# Health-check simples via endpoint de status da análise
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/analysis/status')" || exit 1

CMD ["glifo-gui"]
