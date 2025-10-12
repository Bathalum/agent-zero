#!/bin/bash
# Bash script to stop Agent Zero Docker container
# Usage: ./docker-stop.sh [--remove]

set -e

REMOVE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --remove)
            REMOVE="true"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--remove]"
            exit 1
            ;;
    esac
done

echo "🛑 Stopping Agent Zero Docker Container..."

if [ -n "$REMOVE" ]; then
    echo "Stopping and removing container..."
    docker-compose -f docker-compose.local.yml down
else
    echo "Stopping container..."
    docker-compose -f docker-compose.local.yml stop
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Container stopped successfully!"
    if [ -n "$REMOVE" ]; then
        echo "Container and networks have been removed."
    fi
else
    echo ""
    echo "❌ Failed to stop container!"
    exit 1
fi



