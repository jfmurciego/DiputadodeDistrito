<#
PROYECTO: Diputado de Distrito · T-354 · VERSIÓN 1.1.0 · 2026-11-23 · ANTERIOR: legacy/herramientas/espejo_galicia_r2_v1.0.0_20261123.ps1
CAMBIOS 1.1.0 (T-443, D-188/D-198): sube al árbol nuevo de R2, fuentes/xunta/2024/<nombre>.csv (sin sha12; el sha256 va en el índice), y anota
la clave vieja (arc-e/fuentes/xunta/<nombre>_<sha12>.csv, donde ya está) en clave_anterior para la transición. Fuentes inmutables: si la clave ya
existe con el mismo sha256 no se resube; con otro sha256, falla esa fuente y no se sube. Con las 4 bien, sube fuentes/xunta/2024/manifiesto.json
(nombre, sha256, bytes, origen y clave anterior de cada fichero), también inmutable.
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

function Estado-Clave($clave, $sha) {
    # igual = existe con Metadata.sha256 igual; falta = 404; distinto = existe con otro sha256 (fuentes inmutables, D-198); otro error: se propaga
    $ep = "https://" + $env:R2_ACCOUNT_ID + ".r2.cloudflarestorage.com"
    $h = (aws s3api head-object --bucket $env:R2_BUCKET --key $clave --endpoint-url $ep 2>&1 | Out-String)
    if ($LASTEXITCODE -ne 0) { if ($h -match '(?i)\(404\)|NoSuchKey|Not Found') { return 'falta' }; throw "head-object fallo para $clave" }
    $j = $h | ConvertFrom-Json
    if ($j.Metadata -and [string]$j.Metadata.sha256 -eq $sha) { return 'igual' }
    return 'distinto'
}
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
    $clave = "fuentes/xunta/2024/galicia_parlamento_2024_$($f.id).csv"
    $claveAnterior = "arc-e/fuentes/xunta/galicia_parlamento_2024_$($f.id)_$($sha.Substring(0, 12)).csv"
    Write-Host "$($f.id): HTTP $http, $bytes bytes, sha256 $sha"
    if (-not $SoloBajar) {
        $estado = Estado-Clave $clave $sha
        if ($estado -eq 'distinto') { Write-Warning "$($f.id): $clave ya existe en R2 con otro sha256 (fuentes inmutables): no se sube"; $fallos++; continue }
        if ($estado -eq 'falta') {
            aws s3 cp $ruta "s3://$($env:R2_BUCKET)/$clave" --endpoint-url "https://$($env:R2_ACCOUNT_ID).r2.cloudflarestorage.com" `
                --metadata "sha256=$sha" --only-show-errors
            if ($LASTEXITCODE -ne 0) { Write-Warning "$($f.id): la subida a R2 falló (código $LASTEXITCODE)"; $fallos++; continue }
        }
    }
    $resultado[$nombre] = [ordered]@{
        clave = $clave; clave_anterior = $claveAnterior; sha256 = $sha; bytes = $bytes; origen_url = $f.url
        descargado_en = (Get-Date -Format 'yyyy-MM-dd'); http = $http; subido = (-not $SoloBajar)
    }
}
if (-not $SoloBajar -and $fallos -eq 0 -and $resultado.Count -eq 4) {
    # manifiesto de la carpeta (D-188): sin fechas, para que el mismo contenido dé el mismo sha256
    $man = [ordered]@{ schema = 'ddd.r2-manifiesto/1.0'; carpeta = 'fuentes/xunta/2024'; ficheros = [ordered]@{} }
    foreach ($k in ($resultado.Keys | Sort-Object)) {
        $r = $resultado[$k]
        $man.ficheros[($r.clave -split '/')[-1]] = [ordered]@{ sha256 = $r.sha256; bytes = $r.bytes; origen_url = $r.origen_url; clave_anterior = $r.clave_anterior }
    }
    $mruta = Join-Path ([System.IO.Path]::GetTempPath()) 'manifiesto_xunta_2024.json'
    [System.IO.File]::WriteAllText($mruta, ($man | ConvertTo-Json -Depth 4), (New-Object System.Text.UTF8Encoding($false)))
    $msha = (Get-FileHash -Algorithm SHA256 $mruta).Hash.ToLower()
    $mclave = 'fuentes/xunta/2024/manifiesto.json'
    $me = Estado-Clave $mclave $msha
    if ($me -eq 'distinto') { Write-Warning "$mclave ya existe con otro contenido (inmutable): no se sobrescribe"; $fallos++ }
    elseif ($me -eq 'falta') {
        aws s3 cp $mruta "s3://$($env:R2_BUCKET)/$mclave" --endpoint-url "https://$($env:R2_ACCOUNT_ID).r2.cloudflarestorage.com" `
            --metadata "sha256=$msha" --only-show-errors
        if ($LASTEXITCODE -ne 0) { Write-Warning "$mclave`: la subida a R2 falló (código $LASTEXITCODE)"; $fallos++ }
    }
}
$resultado | ConvertTo-Json -Depth 4 | Set-Content -Path $Salida -Encoding UTF8
Write-Host "Resultado en $Salida ($($resultado.Count) de 4; fallos: $fallos)."
if ($fallos -gt 0) { exit 1 }
