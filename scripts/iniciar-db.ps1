# Enciende el servidor de PostgreSQL

$bin = "C:\Program Files\PostgreSQL\17\bin"
$data = "$env:USERPROFILE\PostgreSQL\17\data"
$log = "$env:USERPROFILE\PostgreSQL\17\postgres.log"

if (-not (Test-Path $data)) {
    Write-Host "No se encontro la base de datos en $data" -ForegroundColor Red
    Write-Host "Revisa la seccion de instalacion del README."
    exit 1
}

& "$bin\pg_isready.exe" -h localhost -p 5432 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "PostgreSQL ya estaba encendido." -ForegroundColor Green
    exit 0
}

& "$bin\pg_ctl.exe" -D $data -l $log -w start

if ($LASTEXITCODE -eq 0) {
    Write-Host "PostgreSQL encendido en localhost:5432" -ForegroundColor Green
} else {
    Write-Host "No se pudo encender. Revisa el archivo $log" -ForegroundColor Red
}
