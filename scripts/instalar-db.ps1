# Crea la base de datos desde cero en un equipo nuevo
# Usar solo la primera vez, despues basta con iniciar-db.ps1

$bin = "C:\Program Files\PostgreSQL\17\bin"
$base = "$env:USERPROFILE\PostgreSQL\17"
$data = "$base\data"

if (-not (Test-Path "$bin\initdb.exe")) {
    Write-Host "No se encontro PostgreSQL 17 en $bin" -ForegroundColor Red
    Write-Host "Instalalo con: winget install PostgreSQL.PostgreSQL.17"
    exit 1
}

if (Test-Path $data) {
    Write-Host "La base de datos ya existe en $data" -ForegroundColor Yellow
    Write-Host "Si quieres empezar de cero, borra esa carpeta y vuelve a ejecutar este script."
    exit 0
}

# Crear el cluster
New-Item -ItemType Directory -Force -Path $base | Out-Null
$pwfile = "$base\.initpw"
Set-Content -Path $pwfile -Value "postgres" -NoNewline -Encoding ascii

& "$bin\initdb.exe" -D $data -U postgres -E UTF8 --locale=C `
    --auth-local=trust --auth-host=scram-sha-256 --pwfile=$pwfile

Remove-Item $pwfile -Force

if ($LASTEXITCODE -ne 0) {
    Write-Host "Fallo la creacion de la base de datos." -ForegroundColor Red
    exit 1
}

# Encender el servidor
& "$bin\pg_ctl.exe" -D $data -l "$base\postgres.log" -w start

# Crear la base de datos del proyecto
$env:PGPASSWORD = "postgres"
& "$bin\psql.exe" -h localhost -U postgres `
    -c "CREATE DATABASE gestion_cultivos ENCODING 'UTF8' TEMPLATE template0;"

Write-Host ""
Write-Host "Listo. Base de datos 'gestion_cultivos' creada." -ForegroundColor Green
Write-Host "Usuario: postgres   Contrasena: postgres   Puerto: 5432"
