# Shows the project on your own computer to one outside person through ngrok (no domain, no server).
# Starts: the dev database (Docker), the backend, the built frontend and the ngrok tunnel, then prints the address.
# Run from the project folder:  powershell -ExecutionPolicy Bypass -File scripts\demo-tunnel.ps1
# Stop with:                    powershell -ExecutionPolicy Bypass -File scripts\demo-tunnel.ps1 -Stop
# Needs once: Docker Desktop, backend\venv (pip install -r backend\requirements-dev.txt), npm ci in frontend,
# backend\.env (copy of backend\.env.dev.example), ngrok installed and `ngrok config add-authtoken <token>` run.
param([switch]$Stop, [switch]$NoTunnel)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'
$envFile = Join-Path $backend '.env'
$python = Join-Path $backend 'venv\Scripts\python.exe'
$container = 'tickbron-dev-db'

function Stop-Port($port) {
    Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}

function Read-EnvValue($name) {
    $line = Get-Content $envFile | Where-Object { $_ -match "^$name=" } | Select-Object -First 1
    if (-not $line) { throw "$name is missing in backend\.env" }
    return ($line -replace "^$name=", '').Trim()
}

function Set-EnvValue($name, $value) {
    $lines = @(Get-Content $envFile | Where-Object { $_ -notmatch "^$name=" })
    Set-Content -Path $envFile -Value ($lines + "$name=$value")
}

if ($Stop) {
    Stop-Port 8000; Stop-Port 3000
    Get-Process ngrok -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host 'Backend, site and tunnel stopped (the database container keeps running).'
    return
}

foreach ($path in @($python, $envFile, (Join-Path $frontend 'node_modules'))) {
    if (-not (Test-Path $path)) { throw "Missing: $path (see the header of this script)" }
}
if (-not $NoTunnel -and -not (Get-Command ngrok -ErrorAction SilentlyContinue)) {
    throw 'ngrok is not installed or not on PATH. Install it and run: ngrok config add-authtoken <your token>'
}

# 1. Database
docker info *> $null
if ($LASTEXITCODE -ne 0) { throw 'Docker is not running: start Docker Desktop and run this script again.' }
if (docker ps -a --format '{{.Names}}' | Where-Object { $_ -eq $container }) {
    docker start $container | Out-Null
} else {
    docker run -d --name $container --restart unless-stopped -e "POSTGRES_DB=$(Read-EnvValue 'DB_NAME')" `
        -e "POSTGRES_USER=$(Read-EnvValue 'DB_USER')" -e "POSTGRES_PASSWORD=$(Read-EnvValue 'DB_PASSWORD')" `
        -p 127.0.0.1:5432:5432 -v tickbron-dev-pgdata:/var/lib/postgresql/data postgres:16 | Out-Null
}
for ($i = 0; $i -lt 30; $i++) {
    docker exec $container pg_isready -U (Read-EnvValue 'DB_USER') -d (Read-EnvValue 'DB_NAME') *> $null
    if ($LASTEXITCODE -eq 0) { break }
    Start-Sleep -Seconds 2
}

# 2. The built site (the dev server sends hundreds of small files, too slow through a tunnel); its /api goes to the backend
Push-Location $frontend
npm run build
Pop-Location
Stop-Port 3000
Start-Process -FilePath 'npm.cmd' -ArgumentList 'run', 'preview', '--', '--host', '127.0.0.1', '--port', '3000' -WorkingDirectory $frontend -WindowStyle Minimized

# 3. The tunnel, then its exact address into the backend's trusted origins (a free address changes at every start)
$address = $null
if (-not $NoTunnel) {
    Get-Process ngrok -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Process -FilePath 'ngrok' -ArgumentList 'http', '3000' -WindowStyle Minimized
    for ($i = 0; $i -lt 30 -and -not $address; $i++) {
        Start-Sleep -Seconds 1
        try {
            $address = (Invoke-RestMethod 'http://127.0.0.1:4040/api/tunnels').tunnels |
                Where-Object { $_.public_url -like 'https://*' } | Select-Object -First 1 -ExpandProperty public_url
        } catch { $address = $null }
    }
    if (-not $address) { throw 'ngrok did not give an address: check the ngrok window (token set? one tunnel at a time on the free plan).' }
    Set-EnvValue 'CSRF_TRUSTED_ORIGINS' "http://localhost:3000,http://127.0.0.1:3000,$address"
}

# 4. Backend
Stop-Port 8000
Push-Location $backend
& $python manage.py migrate --noinput
Pop-Location
Start-Process -FilePath $python -ArgumentList 'manage.py', 'runserver', '127.0.0.1:8000', '--noreload' -WorkingDirectory $backend -WindowStyle Minimized

Write-Host ''
Write-Host 'Site on this computer: http://localhost:3000'
if ($address) {
    Write-Host "Address for the tester: $address  (the first visit shows an ngrok notice: press Visit Site)"
}
Write-Host 'Stop everything: powershell -ExecutionPolicy Bypass -File scripts\demo-tunnel.ps1 -Stop'
