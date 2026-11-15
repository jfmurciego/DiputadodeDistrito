<#
PROYECTO: Diputado de Distrito · T-354 · VERSIÓN 1.0.0 · 2026-11-15 · ANTERIOR: ninguna (fichero nuevo)
Baja las 4 fuentes oficiales de mesas de Galicia 2024 (abertos.xunta.gal; las de territorios/aut12/config/elecciones/galicia_parlamento_vigente.yaml),
calcula sha256 y bytes, las sube a R2 (ARC-E) en arc-e/fuentes/xunta/<nombre>_<sha12>.csv con metadato sha256 y escribe
espejo_galicia_r2_resultado.json (entradas listas para orchestracion/fuentes_r2.json). La nube no llega a la Xunta (proxy 403): se ejecuta en Windows.
Requisitos: PowerShell 5.1+, AWS CLI (`aws`) y estas variables de entorno (las mismas de los secretos del repositorio):
  $env:AWS_ACCESS_KEY_ID, $env:AWS_SECRET_ACCESS_KEY, $env:R2_ACCOUNT_ID, $env:R2_BUCKET   (AWS_DEFAULT_REGION=auto se pone aquí)
Uso (desde la raíz del repositorio):
  .\herramientas\espejo_galicia_r2.ps1 -SoloBajar     # baja y mide, NO sube (comprobación)
  .\herramientas\espejo_galicia_r2.ps1                # baja, mide y sube
Después, pega el contenido de espejo_galicia_r2_resultado.json en el chat del Coordinador (con los códigos HTTP si falla alguna).
#>
[CmdletBinding()]
param(
    [string]$Declaracion = 'territorios/aut12/config/elecciones/galicia_parlamento_vigente.yaml',
    [string]$Salida = 'espejo_galicia_r2_resultado.json',
    [switch]$SoloBajar,
    [switch]$Forzar    # sobrescribe el JSON de resultado sin preguntar
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path $Declaracion)) { throw "No existe $Declaracion (ejecuta desde la raíz del repositorio)." }
if (-not $SoloBajar) {
    foreach ($v in 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'R2_ACCOUNT_ID', 'R2_BUCKET') {
        if (-not (Get-Item "Env:$v" -ErrorAction SilentlyContinue)) { throw "Falta la variable de entorno $v." }
    }
    if (-not (Get-Command aws -ErrorAction SilentlyContinue)) { throw 'Falta AWS CLI (aws).' }
    $env:AWS_DEFAULT_REGION = 'auto'
}
# Fuentes: pares id/url de la declaración (sin dependencias de YAML).
$fuentes = @()
$id = $null
foreach ($l in Get-Content $Declaracion -Encoding UTF8) {
    if ($l -match '^\s*-\s*id:\s*(\S+)\s*$') { $id = $Matches[1] }
    elseif ($id -and $l -match '^\s*url:\s*(\S+)\s*$') { $fuentes += [pscustomobject]@{ id = $id; url = $Matches[1] }; $id = $null }
}
if ($fuentes.Count -ne 4) { throw "Se esperaban 4 fuentes y hay $($fuentes.Count): no se continúa." }
if ((Test-Path $Salida) -and -not $Forzar) {
    $r = Read-Host "$Salida ya existe y se sobrescribirá. Escribe SI para continuar"
    if ($r -cne 'SI') { Write-Host 'Cancelado.'; return }
}
$tmp = Join-Path ([IO.Path]::GetTempPath()) 'espejo_galicia_r2'
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
$ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
$resultado = [ordered]@{}
$fallos = 0
foreach ($f in $fuentes) {
    $nombre = "galicia_parlamento_2024_$($f.id).csv"
    $ruta = Join-Path $tmp $nombre
    try {
        $r = Invoke-WebRequest -Uri $f.url -OutFile $ruta -UserAgent $ua -TimeoutSec 120 -PassThru -UseBasicParsing
        $http = [int]$r.StatusCode
    } catch {
        $http = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
        Write-Warning "$($f.id): HTTP $http $($_.Exception.Message)"
        $fallos++
        continue
    }
    $sha = (Get-FileHash -Algorithm SHA256 $ruta).Hash.ToLower()
    $bytes = (Get-Item $ruta).Length
    $inicio = (Get-Content $ruta -TotalCount 20 -Encoding UTF8) -join "`n"
    if ($bytes -eq 0 -or $inicio -match '(?i)<\s*(html|head|body)\b|<!DOCTYPE' -or $inicio -notmatch '(?i)mesa|censo') { Write-Warning "$($f.id): contenido vacío, HTML o sin cabecera mesa/censo"; $fallos++; continue }
    $clave = "arc-e/fuentes/xunta/galicia_parlamento_2024_$($f.id)_$($sha.Substring(0, 12)).csv"
    Write-Host "$($f.id): HTTP $http, $bytes bytes, sha256 $sha"
    if (-not $SoloBajar) {
        aws s3 cp $ruta "s3://$($env:R2_BUCKET)/$clave" --endpoint-url "https://$($env:R2_ACCOUNT_ID).r2.cloudflarestorage.com" `
            --metadata "sha256=$sha" --only-show-errors
        if ($LASTEXITCODE -ne 0) { Write-Warning "$($f.id): la subida a R2 falló (código $LASTEXITCODE)"; $fallos++; continue }
    }
    $resultado[$nombre] = [ordered]@{
        clave = $clave; sha256 = $sha; bytes = $bytes; origen_url = $f.url
        descargado_en = (Get-Date -Format 'yyyy-MM-dd'); http = $http; subido = (-not $SoloBajar)
    }
}
$resultado | ConvertTo-Json -Depth 4 | Set-Content -Path $Salida -Encoding UTF8
Write-Host "Resultado en $Salida ($($resultado.Count) de 4; fallos: $fallos)."
if ($fallos -gt 0) { exit 1 }
