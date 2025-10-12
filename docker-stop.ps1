# PowerShell script to stop Agent Zero Docker container
# Usage: .\docker-stop.ps1 [-Remove]

param(
    [switch]$Remove
)

Write-Host "🛑 Stopping Agent Zero Docker Container..." -ForegroundColor Cyan

$composeArgs = @(
    "-f", "docker-compose.local.yml"
)

if ($Remove) {
    Write-Host "Stopping and removing container..." -ForegroundColor Yellow
    & docker-compose @composeArgs down
} else {
    Write-Host "Stopping container..." -ForegroundColor Yellow
    & docker-compose @composeArgs stop
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Container stopped successfully!" -ForegroundColor Green
    if ($Remove) {
        Write-Host "Container and networks have been removed." -ForegroundColor Gray
    }
} else {
    Write-Host "`n❌ Failed to stop container!" -ForegroundColor Red
    exit $LASTEXITCODE
}



