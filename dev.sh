#!/usr/bin/env bash
# dev.sh — Modo desenvolvimento: FastAPI (porta 8080) + Vite dev server (porta 5173)
#
# Uso:
#   chmod +x dev.sh
#   ./dev.sh
#
# Acesse a aplicação em: http://localhost:5173  (Vite com hot-reload)
# A API é acessível em:  http://localhost:8080/api
#
# Ctrl+C encerra ambos os processos.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"

# ── Verificações de pré-requisitos ─────────────────────────────────────────────
if ! command -v uv &>/dev/null; then
  echo "[ERRO] 'uv' não encontrado. Instale em: https://docs.astral.sh/uv/"
  exit 1
fi

if ! command -v npm &>/dev/null; then
  echo "[ERRO] 'npm' não encontrado. Instale Node.js em: https://nodejs.org/"
  exit 1
fi

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "[INFO] node_modules não encontrado. Executando 'npm install'..."
  npm --prefix "$FRONTEND_DIR" install
fi

# ── Encerramento gracioso ───────────────────────────────────────────────────────
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo ""
  echo "[INFO] Encerrando processos..."
  [[ -n "$BACKEND_PID" ]]  && kill "$BACKEND_PID"  2>/dev/null || true
  [[ -n "$FRONTEND_PID" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
  wait 2>/dev/null || true
  echo "[INFO] Encerrado."
  exit 0
}

trap cleanup INT TERM

# ── Backend FastAPI ─────────────────────────────────────────────────────────────
echo "[INFO] Iniciando backend FastAPI em http://localhost:8080 ..."
cd "$ROOT_DIR"
uv run glifo-gui &
BACKEND_PID=$!

# Aguarda o backend responder antes de iniciar o frontend
echo -n "[INFO] Aguardando backend ficar disponível"
for i in $(seq 1 20); do
  if curl -sf http://localhost:8080/api/analysis/status &>/dev/null; then
    echo " OK"
    break
  fi
  echo -n "."
  sleep 0.5
done

# ── Frontend Vite dev server ────────────────────────────────────────────────────
echo "[INFO] Iniciando frontend Vite em http://localhost:5173 ..."
npm --prefix "$FRONTEND_DIR" run dev &
FRONTEND_PID=$!

echo ""
echo "┌─────────────────────────────────────────────────────────┐"
echo "│  ELIS Glifo Analyser — modo desenvolvimento             │"
echo "│                                                          │"
echo "│  Frontend (hot-reload) : http://localhost:5173          │"
echo "│  Backend  (API)        : http://localhost:8080/api      │"
echo "│                                                          │"
echo "│  Ctrl+C para encerrar                                   │"
echo "└─────────────────────────────────────────────────────────┘"
echo ""

# Aguarda qualquer processo terminar
wait -n 2>/dev/null || wait
cleanup
