# Клонирование экосистемы Trello QA в одну папку (4 репозитория)
# Использование: .\scripts\clone_workspace.ps1 -Target C:\Projects\trello

param(
    [string]$GitHubUser = "shadow7971247",
    [string]$Target = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
)

$ErrorActionPreference = "Stop"
$Repos = @(
    @{ Name = "trello"; Url = "https://github.com/$GitHubUser/trello.git" },
    @{ Name = "trello_api"; Url = "https://github.com/$GitHubUser/trello_api.git" },
    @{ Name = "trello_ui"; Url = "https://github.com/$GitHubUser/trello_ui.git" },
    @{ Name = "trello_mobile"; Url = "https://github.com/$GitHubUser/trello_mobile.git" }
)

New-Item -ItemType Directory -Force -Path $Target | Out-Null

foreach ($repo in $Repos) {
    $dest = Join-Path $Target $repo.Name
    if (Test-Path (Join-Path $dest ".git")) {
        Write-Host "Skip (exists): $($repo.Name)" -ForegroundColor Yellow
        continue
    }
    Write-Host "Clone: $($repo.Name)" -ForegroundColor Cyan
    git clone $repo.Url $dest
}

Write-Host "`nWorkspace ready: $Target" -ForegroundColor Green
Write-Host "  trello/          — README, docs, media, CI"
Write-Host "  trello_api/      — REST API tests"
Write-Host "  trello_ui/       — Web UI tests"
Write-Host "  trello_mobile/   — Appium tests"
