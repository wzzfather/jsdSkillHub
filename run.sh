#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_DIR="$ROOT_DIR/backend"

FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"

# Ensure local service calls are never hijacked by global VPN proxy.
LOCAL_NO_PROXY="localhost,127.0.0.1,::1"
if [[ -n "${no_proxy:-}" ]]; then
  export no_proxy="$LOCAL_NO_PROXY,${no_proxy}"
else
  export no_proxy="$LOCAL_NO_PROXY"
fi
if [[ -n "${NO_PROXY:-}" ]]; then
  export NO_PROXY="$LOCAL_NO_PROXY,${NO_PROXY}"
else
  export NO_PROXY="$LOCAL_NO_PROXY"
fi

log() {
  printf '[run.sh] %s\n' "$1"
}

ensure_frontend_deps() {
  if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
    log "前端依赖缺失，执行 npm install"
    (cd "$FRONTEND_DIR" && npm install)
  fi
}

ensure_backend_deps() {
  if ! python3 -c "import fastapi, uvicorn" >/dev/null 2>&1; then
    log "后端依赖缺失，执行 pip install -r requirements.txt"
    (cd "$BACKEND_DIR" && python3 -m pip install -r requirements.txt)
  fi
}

cleanup() {
  log "收到退出信号，停止前后端进程"
  [[ -n "${BACKEND_PID:-}" ]] && kill "$BACKEND_PID" >/dev/null 2>&1 || true
  [[ -n "${FRONTEND_PID:-}" ]] && kill "$FRONTEND_PID" >/dev/null 2>&1 || true
  wait >/dev/null 2>&1 || true
}

trap cleanup INT TERM EXIT

ensure_frontend_deps
ensure_backend_deps

log "启动后端 FastAPI: http://$BACKEND_HOST:$BACKEND_PORT"
(cd "$BACKEND_DIR" && env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u all_proxy python3 -m uvicorn app.main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT") &
BACKEND_PID=$!

log "启动前端 Vite: http://$FRONTEND_HOST:$FRONTEND_PORT"
(cd "$FRONTEND_DIR" && env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u all_proxy npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT") &
FRONTEND_PID=$!

log "系统已启动"
log "前端地址: http://$FRONTEND_HOST:$FRONTEND_PORT"
log "后端地址: http://$BACKEND_HOST:$BACKEND_PORT"
log "Swagger: http://$BACKEND_HOST:$BACKEND_PORT/docs"

wait
