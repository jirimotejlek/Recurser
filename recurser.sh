#!/bin/bash
# Docker Compose management script

BASE_FILES="-f docker-compose.base.yml"
LOCAL_FILES="$BASE_FILES -f docker-compose.local.yml"
EXTERNAL_FILES="$BASE_FILES -f docker-compose.external.yml"

show_help() {
    echo "Usage: ./docker.sh [command]"
    echo ""
    echo "Commands:"
    echo "  run-local      Start services with local LLM"
    echo "  run-external   Start services with external LLM provider"
    echo "  build-local    Build containers for local LLM"
    echo "  build-external Build containers for external LLM"
    echo "  stop           Stop services (containers remain)"
    echo "  restart        Restart stopped services"
    echo "  status         Show status of project containers"
    echo "  logs           Show logs from running services"
    echo "  remove         Remove all project containers and volumes"
    echo "  help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./docker.sh run-local"
    echo "  ./docker.sh run-local -d     # Run in detached mode"
    echo "  ./docker.sh stop             # Stop but keep containers"
    echo "  ./docker.sh restart          # Restart stopped containers"
    echo "  ./docker.sh logs llm-dispatcher"
}

check_env_file() {
    if [ ! -f .env ]; then
        echo "Error: .env file not found!"
        echo ""
        echo "To use an external LLM provider:"
        echo "1. Copy a template: cp env-templates/openai .env"
        echo "2. Edit .env and add your API key"
        echo "3. Run this script again"
        exit 1
    fi
}

case "$1" in
    run-local)
        echo "Starting services with local LLM..."
        shift
        docker compose $LOCAL_FILES up "$@"
        ;;
    run-external)
        check_env_file
        echo "Starting services with external LLM provider..."
        shift
        docker compose $EXTERNAL_FILES up "$@"
        ;;
    build-local)
        echo "Building services with local LLM..."
        shift
        docker compose $LOCAL_FILES build "$@"
        ;;
    build-external)
        echo "Building services for external LLM provider..."
        shift
        docker compose $EXTERNAL_FILES build "$@"
        ;;
    stop)
        echo "Stopping services..."
        shift
        # Just stop containers, don't remove them
        docker compose $LOCAL_FILES stop "$@" 2>/dev/null || docker compose $EXTERNAL_FILES stop "$@" 2>/dev/null
        ;;
    restart)
        echo "Restarting services..."
        shift
        # Restart whichever configuration is currently stopped
        docker compose $LOCAL_FILES restart "$@" 2>/dev/null || docker compose $EXTERNAL_FILES restart "$@" 2>/dev/null
        ;;
    status)
        echo "Project containers status:"
        # Try both configurations to show all project containers
        docker compose $LOCAL_FILES ps 2>/dev/null || docker compose $EXTERNAL_FILES ps 2>/dev/null || echo "No active compose configuration found"
        ;;
    logs)
        shift
        # Check which compose files have running containers
        if docker compose $LOCAL_FILES ps -q 2>/dev/null | grep -q .; then
            docker compose $LOCAL_FILES logs -f "$@"
        elif docker compose $EXTERNAL_FILES ps -q 2>/dev/null | grep -q .; then
            docker compose $EXTERNAL_FILES logs -f "$@"
        else
            echo "No running services found"
        fi
        ;;
    remove)
        echo "WARNING: This will remove all containers and volumes for this project!"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            shift
            echo "Detecting project containers..."
            
            # Get the compose project name (defaults to directory name)
            PROJECT_NAME=${COMPOSE_PROJECT_NAME:-$(basename "$PWD" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g')}
            
            # First try graceful shutdown with compose
            echo "Stopping services..."
            docker compose $LOCAL_FILES down --remove-orphans 2>/dev/null || true
            LLM_API_KEY=dummy LLM_API_ENDPOINT=dummy LLM_PROVIDER=dummy docker compose $EXTERNAL_FILES down --remove-orphans 2>/dev/null || true
            
            # List and remove only containers from this project
            echo "Removing project containers..."
            docker ps -a --filter "label=com.docker.compose.project=${PROJECT_NAME}" --format "{{.ID}}" | xargs -r docker rm -f 2>/dev/null || true
            
            # Remove only volumes from this project
            echo "Removing project volumes..."
            docker volume ls --filter "label=com.docker.compose.project=${PROJECT_NAME}" -q | xargs -r docker volume rm -f 2>/dev/null || true
            
            # Also try with explicit volume names from this project
            docker volume rm -f "${PROJECT_NAME}_chroma_data" "${PROJECT_NAME}_ollama_data" 2>/dev/null || true
            
            echo "Project containers and volumes removed"
        else
            echo "Cancelled"
        fi
        ;;
    help|"")
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac