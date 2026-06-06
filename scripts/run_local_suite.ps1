# Полный локальный прогон (без BrowserStack)
# Использование: .\scripts\run_local_suite.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

function Invoke-ProjectTests {
    param(
        [string]$Name,
        [string]$Dir,
        [string]$Marker,
        [string[]]$ExtraArgs = @()
    )
    Write-Host "`n========== $Name ==========" -ForegroundColor Cyan
    Push-Location (Join-Path $Root $Dir)
    try {
        & .\.venv\Scripts\python.exe -m pytest -m $Marker @ExtraArgs --alluredir=../allure-results-$Dir
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    } finally {
        Pop-Location
    }
}

Invoke-ProjectTests -Name "trello_api" -Dir "trello_api" -Marker "smoke"
Invoke-ProjectTests -Name "trello_ui" -Dir "trello_ui" -Marker "ui"
Invoke-ProjectTests -Name "trello_mobile" -Dir "trello_mobile" -Marker "mobile and not browserstack" -ExtraArgs @(
    "--run-context", "local"
)

Write-Host "`nAll projects passed (local suite)." -ForegroundColor Green
Write-Host "Allure: allure serve allure-results-trello_api (или объедините каталоги вручную)" -ForegroundColor Yellow
