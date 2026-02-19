# Start the Postgres container (docker-compose must be installed)
# Usage: run from repo root in PowerShell

Set-StrictMode -Version Latest

Write-Host "Starting Postgres (docker-compose up -d db) ..."
docker-compose up -d db

Write-Host "Waiting for Postgres on localhost:5432 to accept connections..."
$max = 60
$i = 0
while ($i -lt $max) {
    $conn = Test-NetConnection -ComputerName 'localhost' -Port 5432
    if ($conn.TcpTestSucceeded) {
        Write-Host "Postgres is listening on port 5432"
        break
    }
    Start-Sleep -Seconds 1
    $i++
}

if ($i -ge $max) {
    Write-Host "Timed out waiting for Postgres to start. Check 'docker-compose logs db' for details." -ForegroundColor Red
    exit 1
}

# Run local checks from scripts/check_local_stack.py if python is available in venv
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "Running scripts/check_local_stack.py to validate setup..."
    python scripts/check_local_stack.py
} else {
    Write-Host "Python not found in PATH. Activate the venv and run 'python scripts/check_local_stack.py' manually." -ForegroundColor Yellow
}
