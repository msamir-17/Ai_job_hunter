# AI Job Hunter Co-Pilot - Docker Deployment Helper Script (PowerShell)
param (
    [Parameter(Position=0)]
    [ValidateSet("up", "down", "build", "logs", "status", "test", "restart")]
    [string]$Action = "status"
)

$ErrorActionPreference = "Stop"

function Check-Docker {
    try {
        $dockerVersion = docker version --format '{{.Server.Version}}' 2>$null
        if (-not $dockerVersion) {
            Write-Error "Docker is not running. Please start Docker Desktop, then retry."
            exit 1
        }
    } catch {
        Write-Error "Docker is not running. Please start Docker Desktop, then retry."
        exit 1
    }
}

Check-Docker

switch ($Action) {
    "build" {
        Write-Host "Building all container images (db, migration, backend, worker, frontend)..." -ForegroundColor Cyan
        docker compose build
    }
    "up" {
        Write-Host "Starting AI Job Hunter complete stack..." -ForegroundColor Green
        docker compose up -d --build
        Write-Host "`nStack deployed successfully." -ForegroundColor Green
        Write-Host "Frontend: http://localhost:${env:FRONTEND_PORT:-3000}" -ForegroundColor White
        Write-Host "Backend API: http://localhost:${env:BACKEND_PORT:-8080}" -ForegroundColor White
        Write-Host "PostgreSQL (pgvector): localhost:${env:POSTGRES_PORT:-5435}" -ForegroundColor White
    }
    "down" {
        Write-Host "Stopping and removing containers..." -ForegroundColor Yellow
        docker compose down
    }
    "restart" {
        Write-Host "Restarting containers..." -ForegroundColor Yellow
        docker compose restart
    }
    "logs" {
        docker compose logs -f
    }
    "status" {
        docker compose ps
    }
    "test" {
        Write-Host "Running backend tests inside container..." -ForegroundColor Cyan
        docker compose run --rm backend pytest -v
    }
}
