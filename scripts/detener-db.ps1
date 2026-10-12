# Apaga el servidor de PostgreSQL

$bin = "C:\Program Files\PostgreSQL\17\bin"
$data = "$env:USERPROFILE\PostgreSQL\17\data"

& "$bin\pg_ctl.exe" -D $data -w stop

if ($LASTEXITCODE -eq 0) {
    Write-Host "PostgreSQL apagado." -ForegroundColor Green
}
