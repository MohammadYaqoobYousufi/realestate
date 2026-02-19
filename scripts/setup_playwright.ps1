# Install Playwright and download browser binaries in this venv
# Run from project root (PowerShell) while the virtualenv is activated

Write-Host "Installing Playwright Python package..." -ForegroundColor Yellow
pip install playwright

Write-Host "Installing Playwright browsers..." -ForegroundColor Yellow
playwright install

Write-Host "Playwright setup complete. You can now run: python scripts/playwright_fetch.py" -ForegroundColor Green
