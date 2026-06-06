# Первый push трёх репозиториев (после создания пустых repo на GitHub)
param(
    [string]$GitHubUser = "shadow7971247",
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Repos = @("trello_api", "trello_ui", "trello_mobile")

foreach ($name in $Repos) {
    $dir = Join-Path $Root $name
    Write-Host "`n=== $name ===" -ForegroundColor Cyan
    Push-Location $dir
    try {
        if (-not (Test-Path .git)) {
            git init -b $Branch
        }
        git add -A
        git status --short
        $status = git status --porcelain
        if ($status) {
            git commit -m "Initial commit: Trello QA $name for diploma CI"
        } else {
            Write-Host "Nothing to commit"
        }
        $remote = "https://github.com/$GitHubUser/$name.git"
        $hasOrigin = git remote 2>$null | Select-String -Pattern "^origin$"
        if (-not $hasOrigin) {
            git remote add origin $remote
        } else {
            git remote set-url origin $remote
        }
        git push -u origin $Branch
    } finally {
        Pop-Location
    }
}

Write-Host "`nDone." -ForegroundColor Green
