# Script para configurar a timeline no VS Code
$settingsFile = ".vscode/settings.json"
$settings = @{
    "workbench.activityBar.visible" = $true
    "workbench.sideBar.location" = "left"
    "timeline.showView" = $true
    "workbench.views.timeline" = @{
        "visible" = $true
        "location" = "explorer"
    }
}

# Criar pasta .vscode se não existir
if (!(Test-Path ".vscode")) {
    New-Item -ItemType Directory -Path ".vscode"
}

# Atualizar ou criar settings.json
$settings | ConvertTo-Json -Depth 10 | Set-Content $settingsFile

Write-Host "Configurações da timeline atualizadas."
Write-Host "Por favor, reinicie o VS Code para aplicar as mudanças."