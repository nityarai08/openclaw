#!/bin/bash
set -e

cd "$(dirname "$0")"

usage() {
    echo "Usage: ./dev.sh <command>"
    echo ""
    echo "Commands:"
    echo "  restart   Kill and restart gateway"
    echo "  update    Pull, install, build, and restart"
    echo "  watch     Start gateway with auto-reload on changes"
    echo ""
}

restart_gateway() {
    pkill -f "openclaw-gateway" 2>/dev/null && echo "==> Stopped old gateway" || true
    sleep 1
    echo "==> Starting gateway..."
    pnpm openclaw gateway
}

case "${1:-}" in
    restart)
        restart_gateway
        ;;
    update)
        echo "==> Pulling latest changes..."
        git pull
        echo "==> Installing dependencies..."
        pnpm install
        echo "==> Building..."
        pnpm build
        restart_gateway
        ;;
    watch)
        pkill -f "openclaw-gateway" 2>/dev/null && echo "==> Stopped old gateway" || true
        sleep 1
        echo "==> Starting watch mode..."
        pnpm gateway:watch
        ;;
    *)
        usage
        exit 1
        ;;
esac
