# Expose local OCR API publicly via ngrok
# Usage:
#   .\run_public_api.ps1
# Prérequis : ngrok installé et accessible dans le PATH.

$defaultPort = 8000

function Test-PortFree {
    param([int]$Port)
    $result = Test-NetConnection -ComputerName 127.0.0.1 -Port $Port -WarningAction SilentlyContinue
    return -not $result.TcpTestSucceeded
}

function Get-FreePort {
    $listener = New-Object System.Net.Sockets.TcpListener ([System.Net.IPAddress]::Loopback, 0)
    $listener.Start()
    $port = ($listener.LocalEndpoint).Port
    $listener.Stop()
    return $port
}

# Vérifier si ngrok est disponible
$ngrokCommand = Get-Command ngrok -ErrorAction SilentlyContinue
if (-not $ngrokCommand) {
    Write-Host "Erreur : ngrok n'a pas été trouvé dans le PATH." -ForegroundColor Red
    Write-Host "Installez ngrok et relancez le script." -ForegroundColor Yellow
    Write-Host "Téléchargement : https://ngrok.com/download" -ForegroundColor Cyan
    exit 1
}

$port = $defaultPort
if (-not (Test-PortFree -Port $port)) {
    Write-Host "Le port $port est déjà utilisé. Recherche d'un port libre..." -ForegroundColor Yellow
    $port = Get-FreePort
    Write-Host "Utilisation du port libre $port plutôt que $defaultPort." -ForegroundColor Green
}

Write-Host "Démarrage de l'API FastAPI en local sur http://127.0.0.1:$port ..." -ForegroundColor Cyan
$uvicornArgs = "-m uvicorn api.main:app --host 127.0.0.1 --port $port"
Start-Process -FilePath ".\venv\Scripts\python.exe" -ArgumentList $uvicornArgs -WindowStyle Hidden

Write-Host "Lancement de ngrok pour exposer l'API publiquement..." -ForegroundColor Cyan
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "& '$($ngrokCommand.Source)' http $port"

Write-Host "Attente de l'URL ngrok publique..." -ForegroundColor Cyan
$ngrokApi = 'http://127.0.0.1:4040/api/tunnels'
$publicUrl = $null
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 1
    try {
        $tunnels = Invoke-RestMethod -Uri $ngrokApi -TimeoutSec 2
        if ($tunnels.tunnels.Count -gt 0) {
            $publicUrl = $tunnels.tunnels[0].public_url
            break
        }
    } catch {
        # ngrok n'est pas encore prêt
    }
}

if ($publicUrl) {
    Write-Host "API publique disponible : $publicUrl" -ForegroundColor Green
    Write-Host "Swagger public : $publicUrl/docs" -ForegroundColor Green
    Write-Host "Utilisez cette URL pour appeler /extract-all ou /translate." -ForegroundColor Yellow
} else {
    Write-Host "ngrok est lancé, mais l'URL publique n'a pas pu être récupérée automatiquement." -ForegroundColor Yellow
    Write-Host "Ouvrez la fenêtre ngrok visible pour copier l'URL manuellement." -ForegroundColor Yellow
    Write-Host "Vous pouvez aussi visiter http://127.0.0.1:4040 pour voir les tunnels ngrok." -ForegroundColor Cyan
}
