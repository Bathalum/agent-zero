#!/bin/bash
# Bash script to run Agent Zero Docker container
# Usage: ./docker-run.sh [-d|--detached] [-b|--build]

set -e

DETACHED=""
BUILD=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--detached)
            DETACHED="-d"
            shift
            ;;
        -b|--build)
            BUILD="--build"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [-d|--detached] [-b|--build]"
            exit 1
            ;;
    esac
done

echo "🚀 Starting Agent Zero Docker Container..."

# Load .env.docker if it exists
if [ -f .env.docker ]; then
    echo "Loading configuration from .env.docker..."
    export $(cat .env.docker | grep -v '^#' | xargs)
fi

# Set defaults if not in environment
export WEB_PORT=${WEB_PORT:-50080}
export SSH_PORT=${SSH_PORT:-55022}
export CACHE_DATE=${CACHE_DATE:-$(date +%Y-%m-%d)}

echo "Web UI Port: $WEB_PORT"
echo "SSH Port: $SSH_PORT"

if [ -n "$BUILD" ]; then
    echo ""
    echo "Building image first..."
    docker-compose -f docker-compose.local.yml build
fi

# Run command
echo ""
echo "Starting container..."
docker-compose -f docker-compose.local.yml up $DETACHED

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Container started successfully!"
    echo ""
    echo "📍 Access Agent Zero at: http://localhost:$WEB_PORT"
    echo "📍 SSH available at: localhost:$SSH_PORT"
    echo ""
    echo "Useful commands:"
    echo "  View logs:    docker logs -f agent-zero-local"
    echo "  Stop:         docker-compose -f docker-compose.local.yml down"
    echo "  Restart:      docker-compose -f docker-compose.local.yml restart"
else
    echo ""
    echo "❌ Failed to start container!"
    exit 1
fi



