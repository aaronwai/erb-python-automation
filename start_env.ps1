<#
PowerShell launcher for automation_env venv
Run with: .\start_env.ps1
#>
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Activating virtual environment [automation_env]" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
.\automation_env\Scripts\Activate.ps1
Write-Host ""
Write-Host "✅ Venv activated, (automation_env) prompt ready." -ForegroundColor Green
Write-Host "Run your python scripts in this PowerShell session." -ForegroundColor Green
