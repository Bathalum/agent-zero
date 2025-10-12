# PowerShell script to view Agent Zero Docker container logs
# Usage: .\docker-logs.ps1 [-Follow] [-Lines <number>]

param(
    [switch]$Follow,
    [int]$Lines = 100
)

Write-Host "📋 Viewing Agent Zero Container Logs..." -ForegroundColor Cyan

$logArgs = @("logs")

if ($Follow) {
    $logArgs += "-f"
}

$logArgs += "--tail", $Lines.ToString(), "agent-zero-local"

Write-Host "Press Ctrl+C to exit" -ForegroundColor Gray
Write-Host ""

& docker @logArgs



