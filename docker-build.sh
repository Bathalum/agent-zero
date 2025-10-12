#!/bin/bash
# Bash script to build Agent Zero Docker image
# Usage: ./docker-build.sh [--no-cache] [--tag <tag-name>]

set -e

TAG="agent-zero-local"
NO_CACHE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-cache)
            NO_CACHE="--no-cache"
            shift
            ;;
        --tag)
            TAG="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--no-cache] [--tag <tag-name>]"
            exit 1
            ;;
    esac
done

echo "🐳 Building Agent Zero Docker Image..."
echo "Image tag: $TAG"

# Generate cache date for smart caching
CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S)

# Build command
echo ""
echo "Running: docker build -f DockerfileLocal -t $TAG --build-arg CACHE_DATE=$CACHE_DATE $NO_CACHE ."
echo ""

docker build -f DockerfileLocal -t "$TAG" --build-arg CACHE_DATE="$CACHE_DATE" $NO_CACHE .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build completed successfully!"
    echo ""
    echo "To run the container, use:"
    echo "  docker-compose -f docker-compose.local.yml up -d"
    echo "or:"
    echo "  ./docker-run.sh"
else
    echo ""
    echo "❌ Build failed!"
    exit 1
fi



