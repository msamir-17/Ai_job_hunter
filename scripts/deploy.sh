#!/usr/bin/env bash
# AI Job Hunter Co-Pilot - Docker Deployment Helper Script (Bash)

set -euo pipefail

ACTION="${1:-status}"

check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "Error: Docker is not running. Please start Docker, then retry." >&2
        exit 1
    fi
}

check_docker

case "$ACTION" in
    build)
        echo "Building all container images..."
        docker compose build
        ;;
    up)
        echo "Starting AI Job Hunter complete stack..."
        docker compose up -d --build
        echo ""
        echo "Stack deployed successfully."
        echo "Frontend: http://localhost:${FRONTEND_PORT:-3000}"
        echo "Backend API: http://localhost:${BACKEND_PORT:-8080}"
        echo "PostgreSQL (pgvector): localhost:${POSTGRES_PORT:-5435}"
        ;;
    down)
        echo "Stopping containers..."
        docker compose down
        ;;
    restart)
        echo "Restarting containers..."
        docker compose restart
        ;;
    logs)
        docker compose logs -f
        ;;
    status)
        docker compose ps
        ;;
    test)
        echo "Running backend tests inside container..."
        docker compose run --rm backend pytest -v
        ;;
    *)
        echo "Usage: $0 {up|down|build|logs|status|test|restart}"
        exit 1
        ;;
esac
