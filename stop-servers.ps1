# Stop all WanderAI frontend (port 3000) and backend (port 8000) processes on Windows

Write-Host "Stopping WanderAI servers..." -ForegroundColor Cyan

# Find and terminate processes on port 8000 (Backend)
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($port8000) {
    $port8000 | ForEach-Object {
        Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
        Write-Host "✓ Terminated backend process (PID $_) on port 8000" -ForegroundColor Green
    }
} else {
    Write-Host "• Port 8000 is already free" -ForegroundColor Gray
}

# Find and terminate processes on port 3000 (Frontend)
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($port3000) {
    $port3000 | ForEach-Object {
        Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
        Write-Host "✓ Terminated frontend process (PID $_) on port 3000" -ForegroundColor Green
    }
} else {
    Write-Host "• Port 3000 is already free" -ForegroundColor Gray
}

Write-Host "All ports (3000, 8000) are now completely free!" -ForegroundColor Cyan
