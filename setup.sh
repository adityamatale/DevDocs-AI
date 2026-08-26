#!/usr/bin/env bash

set -e

# ============================================
# DevDocs AI - Setup Script
# ============================================

COMPOSE_LOCAL="docker-compose.yml"
COMPOSE_PROD="docker-compose.prod.yml"
COMPOSE_FILE="$COMPOSE_LOCAL"

# --------------------------------------------
# Colors / formatting
# --------------------------------------------

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# --------------------------------------------
# Help
# --------------------------------------------

show_help() {
    cat << EOF

DevDocs AI Setup

Usage:
    ./setup.sh [OPTION]

Options:
    --local     Build and start Docker services locally
    --prod      Pull and start Docker services from DockerHub
    --ingest    Run document ingestion
    --all       Start Docker services and run ingestion
    --status    Show running Docker services
    --stop      Stop Docker services
    --clean     Stop services and remove Docker volumes
    --help      Show this help message

If no option is provided, interactive setup is started.

EOF
}

# --------------------------------------------
# Check prerequisites
# --------------------------------------------

check_prerequisites() {

    info "Checking prerequisites..."

    if ! command -v docker &> /dev/null; then
        error "Docker is not installed."
        exit 1
    fi

    if ! docker compose version &> /dev/null; then
        error "Docker Compose is not available."
        exit 1
    fi

    info "Docker: OK"
    info "Docker Compose: OK"
}

# --------------------------------------------
# Environment setup
# --------------------------------------------

setup_env() {

    if [ -f ".env" ]; then
        info ".env already exists."
        return
    fi

    if [ -f ".env.example" ]; then
        info "Creating .env from .env.example..."
        cp .env.example .env
        warn "Review .env and add your API keys/configuration."
    else
        warn ".env.example not found."
        warn "You will need to create .env manually."
    fi
}

# --------------------------------------------
# Select environment
# --------------------------------------------

select_environment() {

    echo
    echo "Select environment:"
    echo "1) Local (build images)"
    echo "2) Production (DockerHub)"
    echo

    read -r -p "Select option [1]: " env_choice

    case "$env_choice" in
        2)
            COMPOSE_FILE="$COMPOSE_PROD"
            ;;
        *)
            COMPOSE_FILE="$COMPOSE_LOCAL"
            ;;
    esac

    info "Using $COMPOSE_FILE"
}

# --------------------------------------------
# Check compose file
# --------------------------------------------

check_compose_file() {

    if [ ! -f "$COMPOSE_FILE" ]; then
        error "$COMPOSE_FILE not found."
        error "Run this script from the repository root."
        exit 1
    fi
}

# --------------------------------------------
# Start Docker services
# --------------------------------------------

start_docker() {

    check_compose_file
    setup_env

    info "Starting Docker services using $COMPOSE_FILE..."

    if [ "$COMPOSE_FILE" = "$COMPOSE_LOCAL" ]; then
        docker compose -f "$COMPOSE_FILE" up --build -d
    else
        docker compose -f "$COMPOSE_FILE" up --pull always -d
    fi

    info "Waiting for RAG API to become healthy..."

    local retries=60

    while [ $retries -gt 0 ]; do

        status=$(docker compose -f "$COMPOSE_FILE" ps --format '{{.Service}} {{.Health}}' 2>/dev/null || true)

        if echo "$status" | grep -q "rag-api healthy"; then
            info "RAG API is healthy."
            return 0
        fi

        sleep 5
        retries=$((retries - 1))

    done

    error "RAG API did not become healthy."
    warn "Check logs with:"
    echo "    docker compose -f $COMPOSE_FILE logs rag-api"

    exit 1
}

# --------------------------------------------
# Ingestion
# --------------------------------------------

run_ingestion() {

    check_compose_file

    info "Starting document ingestion..."

    docker compose -f "$COMPOSE_FILE" exec rag-api python -m app.rag.ingestion

    info "Ingestion completed."
}

# --------------------------------------------
# Stop services
# --------------------------------------------

stop_services() {

    check_compose_file

    info "Stopping Docker services..."

    docker compose -f "$COMPOSE_FILE" down

    info "Services stopped."
}

# --------------------------------------------
# Clean environment
# --------------------------------------------

clean_environment() {

    check_compose_file

    warn "This will remove Docker volumes, including Qdrant data."
    read -r -p "Are you sure? [y/N] " answer

    case "$answer" in
        y|Y|yes|YES)
            info "Removing containers and volumes..."
            docker compose -f "$COMPOSE_FILE" down -v
            info "Docker environment cleaned."
            ;;
        *)
            info "Cancelled."
            ;;
    esac
}

# --------------------------------------------
# Show service status
# --------------------------------------------

show_status() {

    check_compose_file

    docker compose -f "$COMPOSE_FILE" ps
}

# --------------------------------------------
# Interactive mode
# --------------------------------------------

interactive_menu() {

    echo
    echo "============================================"
    echo "        DevDocs AI Setup"
    echo "============================================"

    select_environment

    echo
    echo "1) Start Docker services"
    echo "2) Run document ingestion"
    echo "3) Start services + ingest"
    echo "4) Show service status"
    echo "5) Stop services"
    echo "6) Clean Docker environment"
    echo "7) Exit"
    echo

    read -r -p "Select an option: " choice

    case "$choice" in

        1)
            check_prerequisites
            start_docker
            ;;

        2)
            check_prerequisites
            run_ingestion
            ;;

        3)
            check_prerequisites
            start_docker
            run_ingestion
            ;;

        4)
            show_status
            ;;

        5)
            stop_services
            ;;

        6)
            clean_environment
            ;;

        7)
            info "Goodbye."
            exit 0
            ;;

        *)
            error "Invalid option."
            exit 1
            ;;

    esac
}

# --------------------------------------------
# Main
# --------------------------------------------

case "${1:-}" in

    --local)
        COMPOSE_FILE="$COMPOSE_LOCAL"
        check_prerequisites
        start_docker
        ;;

    --prod)
        COMPOSE_FILE="$COMPOSE_PROD"
        check_prerequisites
        start_docker
        ;;

    --ingest)
        check_prerequisites
        run_ingestion
        ;;

    --all)
        COMPOSE_FILE="$COMPOSE_LOCAL"
        check_prerequisites
        start_docker
        run_ingestion
        ;;

    --status)
        check_prerequisites
        show_status
        ;;

    --stop)
        check_prerequisites
        stop_services
        ;;

    --clean)
        check_prerequisites
        clean_environment
        ;;

    --help|-h)
        show_help
        ;;

    "")
        check_prerequisites
        interactive_menu
        ;;

    *)
        error "Unknown option: $1"
        show_help
        exit 1
        ;;

esac
