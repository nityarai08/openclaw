#!/bin/bash
set -e

cd "$(dirname "$0")/.."

REQUIRED_NODE_MAJOR=22

usage() {
    echo "Usage: ./scripts/dev.sh <command>"
    echo ""
    echo "Commands:"
    echo "  install   First-time install from source (deps, UI, build, onboard)"
    echo "  update    Pull, install, build, and restart"
    echo "  restart   Restart the gateway"
    echo "  watch     Start gateway with auto-reload on changes"
    echo ""
}

check_node() {
    if ! command -v node &>/dev/null; then
        echo "ERROR: Node.js is not installed. Install Node >= ${REQUIRED_NODE_MAJOR} and try again."
        exit 1
    fi
    local node_major
    node_major=$(node -p 'process.versions.node.split(".")[0]')
    if (( node_major < REQUIRED_NODE_MAJOR )); then
        echo "ERROR: Node >= ${REQUIRED_NODE_MAJOR} required (found v$(node -v)). Please upgrade."
        exit 1
    fi
}

check_pnpm() {
    if ! command -v pnpm &>/dev/null; then
        echo "ERROR: pnpm is not installed."
        echo "  Install it with: corepack enable && corepack prepare pnpm@latest --activate"
        echo "  Or: npm install -g pnpm"
        exit 1
    fi
}

preflight() {
    check_node
    check_pnpm
}

restart_gateway() {
    if systemctl --user is-active openclaw-gateway.service &>/dev/null; then
        echo "==> Restarting gateway service..."
        systemctl --user restart openclaw-gateway.service
        echo "==> Gateway service restarted."
    else
        pkill -f "openclaw-gateway" 2>/dev/null && echo "==> Stopped old gateway" || true
        sleep 1
        echo "==> Starting gateway..."
        pnpm openclaw gateway
    fi
}

stop_gateway() {
    if systemctl --user is-active openclaw-gateway.service &>/dev/null; then
        echo "==> Stopping gateway service..."
        systemctl --user stop openclaw-gateway.service
    else
        pkill -f "openclaw-gateway" 2>/dev/null && echo "==> Stopped old gateway" || true
    fi
    sleep 1
}

reload_service() {
    if systemctl --user list-unit-files openclaw-gateway.service &>/dev/null 2>&1; then
        echo "==> Reloading systemd unit..."
        systemctl --user daemon-reload
    fi
}

case "${1:-}" in
    install)
        preflight
        echo "==> Installing dependencies..."
        pnpm install
        echo "==> Building UI..."
        pnpm ui:build
        echo "==> Building..."
        pnpm build
        echo "==> Running onboard wizard..."
        pnpm openclaw onboard --install-daemon
        echo "==> Install complete."
        ;;
    update)
        preflight
        echo "==> Pulling latest changes..."
        git pull
        echo "==> Installing dependencies..."
        pnpm install
        echo "==> Building UI..."
        pnpm ui:build
        echo "==> Building..."
        pnpm build
        reload_service
        restart_gateway
        ;;
    restart)
        restart_gateway
        ;;
    watch)
        preflight
        stop_gateway
        echo "==> Starting watch mode..."
        pnpm gateway:watch
        ;;
    *)
        usage
        exit 1
        ;;
esac
