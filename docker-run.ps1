# PowerShell script to run Agent Zero Docker container
# Usage: .\docker-run.ps1 [-Detached] [-Build]

param(
    [switch]$Detached,
    [switch]$Build
)

Write-Host "🚀 Starting Agent Zero Docker Container..." -ForegroundColor Cyan

# Load .env.docker if it exists
$envFile = ".env.docker"
if (Test-Path $envFile) {
    Write-Host "Loading configuration from $envFile..." -ForegroundColor Yellow
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+?)\s*=\s*(.+?)\s*$') {
            $name = $matches[1]
            $value = $matches[2]
            Set-Item -Path "env:$name" -Value $value
        }
    }
}

# Set defaults if not in environment
if (-not $env:WEB_PORT) { $env:WEB_PORT = "50080" }
if (-not $env:SSH_PORT) { $env:SSH_PORT = "55022" }
if (-not $env:CACHE_DATE) { $env:CACHE_DATE = (Get-Date -Format "yyyy-MM-dd") }

Write-Host "Web UI Port: $env:WEB_PORT" -ForegroundColor Gray
Write-Host "SSH Port: $env:SSH_PORT" -ForegroundColor Gray

# Build arguments
$composeArgs = @(
    "-f", "docker-compose.local.yml"
)

if ($Build) {
    Write-Host "`nBuilding image first..." -ForegroundColor Yellow
    & docker-compose @composeArgs build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Build failed!" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

# Run command
$upArgs = @("up")
if ($Detached) {
    $upArgs += "-d"
}

Write-Host "`nStarting container..." -ForegroundColor Yellow
& docker-compose @composeArgs @upArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Container started successfully!" -ForegroundColor Green
    Write-Host "`n📍 Access Agent Zero at: http://localhost:$env:WEB_PORT" -ForegroundColor Cyan
    Write-Host "📍 SSH available at: localhost:$env:SSH_PORT" -ForegroundColor Cyan
    Write-Host "`nUseful commands:" -ForegroundColor Yellow
    Write-Host "  View logs:    docker logs -f agent-zero-local" -ForegroundColor White
    Write-Host "  Stop:         docker-compose -f docker-compose.local.yml down" -ForegroundColor White
    Write-Host "  Restart:      docker-compose -f docker-compose.local.yml restart" -ForegroundColor White
} else {
    Write-Host "`n❌ Failed to start container!" -ForegroundColor Red
    exit $LASTEXITCODE
}



