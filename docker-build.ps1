# PowerShell script to build Agent Zero Docker image
# Usage: .\docker-build.ps1 [-NoCache] [-Tag <tag-name>]

param(
    [switch]$NoCache,
    [string]$Tag = "agent-zero-local"
)

Write-Host "🐳 Building Agent Zero Docker Image..." -ForegroundColor Cyan
Write-Host "Image tag: $Tag" -ForegroundColor Yellow

# Generate cache date for smart caching
$cacheDate = Get-Date -Format "yyyy-MM-dd:HH:mm:ss"

# Build command
$buildArgs = @(
    "build",
    "-f", "DockerfileLocal",
    "-t", $Tag,
    "--build-arg", "CACHE_DATE=$cacheDate"
)

if ($NoCache) {
    Write-Host "Building without cache..." -ForegroundColor Yellow
    $buildArgs += "--no-cache"
}

$buildArgs += "."

Write-Host "`nRunning: docker $($buildArgs -join ' ')" -ForegroundColor Gray
Write-Host ""

# Execute build
& docker @buildArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Build completed successfully!" -ForegroundColor Green
    Write-Host "`nTo run the container, use:" -ForegroundColor Cyan
    Write-Host "  docker-compose -f docker-compose.local.yml up -d" -ForegroundColor White
    Write-Host "or:" -ForegroundColor Cyan
    Write-Host "  .\docker-run.ps1" -ForegroundColor White
} else {
    Write-Host "`n❌ Build failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}



