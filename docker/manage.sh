#!/usr/bin/env bash
# =============================================================================
# Glifo Análise — Script de gerenciamento Docker
# =============================================================================
# Uso: ./docker/manage.sh <comando>
#
# Comandos disponíveis:
#   build    Constrói (ou reconstrói) a imagem Docker
#   up       Sobe o container em background
#   down     Para e remove o container
#   restart  Para e re-sobe o container
#   logs     Acompanha os logs em tempo real (Ctrl+C para sair)
#   shell    Abre um shell bash dentro do container em execução
#   status   Exibe o status do container
#   clean    Remove container, imagem e volumes anônimos
#   help     Exibe esta ajuda
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
IMAGE_NAME="glifo-analise:latest"
CONTAINER_NAME="glifo-analise"

# ── Utilitários ────────────────────────────────────────────────────────────────
_info()  { echo -e "\033[1;34m[INFO]\033[0m  $*"; }
_ok()    { echo -e "\033[1;32m[ OK ]\033[0m  $*"; }
_warn()  { echo -e "\033[1;33m[WARN]\033[0m  $*"; }
_error() { echo -e "\033[1;31m[ERR ]\033[0m  $*" >&2; }

_dc() {
  docker compose -f "$COMPOSE_FILE" "$@"
}

_require_docker() {
  if ! command -v docker &>/dev/null; then
    _error "Docker não encontrado. Instale em: https://docs.docker.com/get-docker/"
    exit 1
  fi
}

# ── Comandos ───────────────────────────────────────────────────────────────────
cmd_build() {
  _info "Construindo imagem '$IMAGE_NAME'..."
  cd "$PROJECT_ROOT"
  _dc build --pull
  _ok "Imagem construída com sucesso."
}

cmd_up() {
  _info "Subindo container '$CONTAINER_NAME'..."
  _dc up -d
  _ok "Container iniciado. Acesse: http://localhost:8080"
}

cmd_down() {
  _info "Parando container '$CONTAINER_NAME'..."
  _dc down
  _ok "Container parado."
}

cmd_restart() {
  cmd_down
  cmd_up
}

cmd_logs() {
  _info "Acompanhando logs de '$CONTAINER_NAME' (Ctrl+C para sair)..."
  _dc logs -f
}

cmd_shell() {
  if ! docker ps --filter "name=^${CONTAINER_NAME}$" --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    _warn "Container não está em execução. Iniciando com shell interativo..."
    _dc run --rm -it glifo-gui bash
  else
    _info "Abrindo shell no container '$CONTAINER_NAME'..."
    docker exec -it "$CONTAINER_NAME" bash
  fi
}

cmd_status() {
  _info "Status do container:"
  docker ps -a --filter "name=^${CONTAINER_NAME}$" \
    --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

  echo ""
  _info "Saúde do serviço:"
  if docker ps --filter "name=^${CONTAINER_NAME}$" --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    HEALTH=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "n/a")
    echo "  health: $HEALTH"
  else
    echo "  container não está em execução"
  fi
}

cmd_clean() {
  _warn "Isso vai remover o container e a imagem '${IMAGE_NAME}'."
  read -r -p "Confirmar? [s/N] " resp
  if [[ "$resp" =~ ^[Ss]$ ]]; then
    _dc down --volumes --remove-orphans 2>/dev/null || true
    docker rmi "$IMAGE_NAME" 2>/dev/null && _ok "Imagem removida." || _warn "Imagem não encontrada (já removida)."
    _ok "Limpeza concluída."
  else
    _info "Operação cancelada."
  fi
}

cmd_help() {
  sed -n '/^# Comandos/,/^# ====/p' "$0" | grep -E '^\s+\w' | sed 's/#//'
  echo ""
  echo "Exemplo:"
  echo "  ./docker/manage.sh build && ./docker/manage.sh up"
}

# ── Dispatcher ────────────────────────────────────────────────────────────────
_require_docker

case "${1:-help}" in
  build)   cmd_build   ;;
  up)      cmd_up      ;;
  down)    cmd_down    ;;
  restart) cmd_restart ;;
  logs)    cmd_logs    ;;
  shell)   cmd_shell   ;;
  status)  cmd_status  ;;
  clean)   cmd_clean   ;;
  help|--help|-h) cmd_help ;;
  *)
    _error "Comando desconhecido: '$1'"
    echo "Execute './docker/manage.sh help' para ver os comandos disponíveis."
    exit 1
    ;;
esac
