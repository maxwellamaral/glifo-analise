#!/usr/bin/env bash
# start.sh — Modo produção: FastAPI serve o frontend pré-compilado em frontend/dist/
#
# Uso:
#   chmod +x start.sh
#   ./start.sh
#
# Acesse a aplicação em: http://localhost:8080
#
# Para recompilar o frontend antes de subir:
#   cd frontend && npm install && npm run build && cd ..

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIST="$ROOT_DIR/frontend/dist"

# ── Verificações de pré-requisitos ─────────────────────────────────────────────
if ! command -v uv &>/dev/null; then
  echo "[ERRO] 'uv' não encontrado. Instale em: https://docs.astral.sh/uv/"
  exit 1
fi

if [[ ! -d "$FRONTEND_DIST" ]]; then
  echo "[AVISO] frontend/dist/ não encontrado. Compilando o frontend..."

  if ! command -v npm &>/dev/null; then
    echo "[ERRO] 'npm' não encontrado. Instale Node.js em: https://nodejs.org/"
    exit 1
  fi

  FRONTEND_DIR="$ROOT_DIR/frontend"
  [[ ! -d "$FRONTEND_DIR/node_modules" ]] && npm --prefix "$FRONTEND_DIR" install
  npm --prefix "$FRONTEND_DIR" run build

  echo "[INFO] Build concluído."
fi

# ── Servidor ────────────────────────────────────────────────────────────────────
echo ""
echo "┌─────────────────────────────────────────────────────────┐"
echo "│  ELIS Glifo Analyser — modo produção                   │"
echo "│                                                          │"
echo "│  http://localhost:8080                                  │"
echo "│                                                          │"
echo "│  Ctrl+C para encerrar                                   │"
echo "└─────────────────────────────────────────────────────────┘"
echo ""

cd "$ROOT_DIR"
uv run glifo-gui
