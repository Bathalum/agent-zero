#!/bin/bash
# Bash script to view Agent Zero Docker container logs
# Usage: ./docker-logs.sh [-f|--follow] [-n|--lines <number>]

FOLLOW=""
LINES="100"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--follow)
            FOLLOW="-f"
            shift
            ;;
        -n|--lines)
            LINES="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [-f|--follow] [-n|--lines <number>]"
            exit 1
            ;;
    esac
done

echo "📋 Viewing Agent Zero Container Logs..."
echo "Press Ctrl+C to exit"
echo ""

docker logs $FOLLOW --tail "$LINES" agent-zero-local



