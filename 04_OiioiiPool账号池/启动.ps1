$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $root

Write-Host "============================================"
Write-Host "  OiioiiPool Launcher"
Write-Host "============================================"
Write-Host ""

# Prepare dirs
@("data", "data\output", "data\backups", "logs") | % { if (!(Test-Path $_)) { New-Item -ItemType Directory $_ | Out-Null } }

# Check if already running
try {
    Invoke-WebRequest "http://localhost:7861/" -UseBasicParsing -TimeoutSec 2 | Out-Null
    Write-Host "[OK] Already running at http://localhost:7861"
    Start-Process "http://localhost:7861"
    pause
    exit
} catch {}

# Find Python
$python = "python"
try { & $python --version | Out-Null } catch {
    $python = "C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe"
    if (!(Test-Path $python)) {
        Write-Host "[ERROR] Python not found!"
        pause
        exit 1
    }
}

Write-Host "[OK] Using $python"
Write-Host ""
Write-Host "Starting OiioiiPool..."
Write-Host "Open http://localhost:7861 in your browser"
Write-Host "Close this window to stop the server"
Write-Host ""

& $python main.py

Read-Host "[INFO] Server stopped. Press Enter to exit"