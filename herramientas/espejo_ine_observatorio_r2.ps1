<#
PROYECTO: Diputado de Distrito · T-356 · VERSIÓN 1.0.0 · 2026-11-15 · ANTERIOR: ninguna (fichero nuevo)
Baja los 17 seccionados del INE (2010-2026) y las 625 piezas del Observatorio Electoral de las Naciones, verifica el sha256 del
índice orchestracion/fuentes_r2.json (donde exista; donde no, lo mide y lo registra), las sube a R2 (ARC-E) en
arc-e/fuentes/ine/seccionado_<año>_<sha12>.zip y arc-e/fuentes/nazioenbehatokia/<ruta>_<sha12>.json y escribe el JSON de resultado
(clave, sha256, bytes, origen_url, descargado_en, subido). Se ejecuta en el Windows del propietario (PowerShell 5.1+); no necesita checkout:
  irm https://raw.githubusercontent.com/jfmurciego/DiputadodeDistrito/main/herramientas/espejo_ine_observatorio_r2.ps1 -OutFile espejo.ps1
Sin checkout, el índice se baja de raw; con checkout (desde su raíz) se usa orchestracion/fuentes_r2.json local.
Credenciales (solo para subir; nunca se imprimen ni se guardan): $env:AWS_ACCESS_KEY_ID, $env:AWS_SECRET_ACCESS_KEY, $env:R2_ACCOUNT_ID,
$env:R2_BUCKET, y AWS CLI (`aws`). AWS_DEFAULT_REGION=auto se pone aquí.
Uso:
  .\espejo_ine_observatorio_r2.ps1 -SoloBajar              # baja y mide, NO sube
  .\espejo_ine_observatorio_r2.ps1                         # baja, mide y sube (INE y Observatorio)
  .\espejo_ine_observatorio_r2.ps1 -Grupo ine              # solo los 17 seccionados (o -Grupo observatorio)
Reanudable: lo ya verificado (fichero + .ok) no se vuelve a bajar y lo ya subido (head-object con el mismo sha256) no se vuelve a subir.
Carpeta de trabajo corta (límite de ruta de Windows): C:\ddd. Sale con código 1 si falla alguna pieza y con 2 si no se confirma la sobrescritura del JSON. Después, pega el JSON de resultado en el chat del Coordinador.
#>
[CmdletBinding()]
param(
    [string]$Indice = '',    # ruta local o URL del índice; vacío = orchestracion/fuentes_r2.json local si existe, si no raw de main
    [string]$Trabajo = 'C:\ddd',
    [string]$Salida = 'espejo_ine_observatorio_r2_resultado.json',
    [ValidateSet('todo', 'ine', 'observatorio')][string]$Grupo = 'todo',
    [switch]$SoloBajar,
    [switch]$Forzar,         # sobrescribe el JSON de resultado sin preguntar
    [int]$Reintentos = 5,
    [int]$PausaMs = 200      # pausa entre peticiones al mismo servidor
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'   # sin barra: acelera mucho Invoke-WebRequest en PS 5.1
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$RAW = 'https://raw.githubusercontent.com/jfmurciego/DiputadodeDistrito/main/orchestracion/fuentes_r2.json'
$ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'

if (-not $SoloBajar) {
    foreach ($v in 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'R2_ACCOUNT_ID', 'R2_BUCKET') {
        if (-not (Get-Item "Env:$v" -ErrorAction SilentlyContinue)) { throw "Falta la variable de entorno $v." }
    }
    if (-not (Get-Command aws -ErrorAction SilentlyContinue)) { throw 'Falta AWS CLI (aws).' }
    $env:AWS_DEFAULT_REGION = 'auto'
    $endpoint = "https://$($env:R2_ACCOUNT_ID).r2.cloudflarestorage.com"
}
if ((Test-Path $Salida) -and -not $Forzar) {
    $r = Read-Host "$Salida ya existe y se sobrescribirá. Escribe SI para continuar"
    if ($r -cne 'SI') { Write-Host 'Cancelado: no se ha hecho nada.'; exit 2 }
}

# --- índice -----------------------------------------------------------------------------------------------------------------
if (-not $Indice) { $Indice = if (Test-Path 'orchestracion/fuentes_r2.json') { 'orchestracion/fuentes_r2.json' } else { $RAW } }
$txt = if ($Indice -match '^https?://') { (Invoke-WebRequest -Uri $Indice -UseBasicParsing -UserAgent $ua).Content } else { Get-Content $Indice -Raw -Encoding UTF8 }
if ($txt -is [byte[]]) { $txt = [Text.Encoding]::UTF8.GetString($txt) }
$fuentes = ($txt | ConvertFrom-Json).fuentes
$piezas = @()
foreach ($p in $fuentes.PSObject.Properties) {
    $u = [string]$p.Value.origen_url
    $esIne = $u -match '^https://www\.ine\.es/prodyser/cartografia/seccionado_\d{4}\.zip$'
    $esObs = $u -match '^https://nazioenbehatokia\.eus/(data|geo)/.+\.json$'
    if (($esIne -and $Grupo -ne 'observatorio') -or ($esObs -and $Grupo -ne 'ine')) {
        $piezas += [pscustomobject]@{ nombre = $p.Name; ficha = $p.Value; tipo = $(if ($esIne) { 'ine' } else { 'obs' }) }
    }
}
$esperadas = @{ todo = 642; ine = 17; observatorio = 625 }[$Grupo]
if ($piezas.Count -ne $esperadas) { throw "Se esperaban $esperadas piezas y el índice trae $($piezas.Count): no se continúa." }

# --- utilidades --------------------------------------------------------------------------------------------------------------
New-Item -ItemType Directory -Force -Path (Join-Path $Trabajo 'ine'), (Join-Path $Trabajo 'obs') | Out-Null
function Sha256Hex($ruta) { (Get-FileHash -Algorithm SHA256 -LiteralPath $ruta).Hash.ToLower() }
function Ruta-Completa($ruta) {
    # absolutas intactas; relativas contra la carpeta actual de PowerShell (no la del proceso .NET)
    if ([IO.Path]::IsPathRooted($ruta)) { return [IO.Path]::GetFullPath($ruta) }
    [IO.Path]::GetFullPath((Join-Path (Get-Location).ProviderPath $ruta))
}
function Escribir-Sin-Bom($ruta, $texto) { [IO.File]::WriteAllText((Ruta-Completa $ruta), $texto, (New-Object Text.UTF8Encoding($false))) }

function Validar($ruta, $tipo) {
    # devuelve $null si es válido o el motivo
    $n = (Get-Item -LiteralPath $ruta).Length
    if ($n -eq 0) { return 'fichero vacío' }
    $fs = [IO.File]::OpenRead($ruta)
    try { $buf = New-Object byte[] ([Math]::Min(512, $n)); [void]$fs.Read($buf, 0, $buf.Length) } finally { $fs.Dispose() }
    $ini = [Text.Encoding]::UTF8.GetString($buf).TrimStart([char]0xFEFF, ' ', "`r", "`n", "`t")
    if ($ini -match '(?i)^<\s*(!doctype|html|head|body)') { return 'es HTML (página de error), no el fichero' }
    if ($tipo -eq 'ine') {
        if (-not ($buf[0] -eq 0x50 -and $buf[1] -eq 0x4B -and $buf[2] -eq 3 -and $buf[3] -eq 4)) { return 'no es un ZIP (falta la firma PK)' }
        try {
            Add-Type -AssemblyName System.IO.Compression.FileSystem
            $z = [IO.Compression.ZipFile]::OpenRead($ruta)
            $entradas = $z.Entries.Count; $z.Dispose()
            if ($entradas -lt 1) { return 'ZIP sin entradas' }
        } catch { return "ZIP ilegible: $($_.Exception.Message)" }
    } elseif ($ini.Length -eq 0 -or ($ini[0] -ne '{' -and $ini[0] -ne '[')) { return 'no empieza como JSON' }
    return $null
}

function Bajar($url, $destino) {
    # reintentos con espera ante 429, 5xx y resets; respeta Retry-After
    for ($i = 1; $i -le $Reintentos; $i++) {
        try {
            $r = Invoke-WebRequest -Uri $url -OutFile $destino -UserAgent $ua -TimeoutSec 600 -PassThru -UseBasicParsing
            return [int]$r.StatusCode
        } catch {
            $resp = $_.Exception.Response
            $http = if ($resp) { [int]$resp.StatusCode } else { 0 }
            Remove-Item -LiteralPath $destino -Force -ErrorAction SilentlyContinue
            $reintentable = ($http -eq 0 -or $http -eq 429 -or $http -ge 500)
            if (-not $reintentable -or $i -eq $Reintentos) { throw "HTTP $http $($_.Exception.Message)" }
            $espera = 10 * [Math]::Pow(2, $i - 1)
            if ($http -eq 429 -and $resp.Headers['Retry-After']) { $ra = 0; if ([int]::TryParse($resp.Headers['Retry-After'], [ref]$ra)) { $espera = [Math]::Max($espera, $ra) } }
            Write-Warning "HTTP $http en $url; reintento $i de $Reintentos en $espera s"
            Start-Sleep -Seconds $espera
        }
    }
}

function Subido($clave, $sha) {
    # ¿ya está en R2 con ese sha256? (head-object; sin imprimir credenciales)
    $out = & aws s3api head-object --bucket $env:R2_BUCKET --key $clave --endpoint-url $endpoint 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $out) { return $false }
    try { return (($out -join "`n") | ConvertFrom-Json).Metadata.sha256 -eq $sha } catch { return $false }
}

# --- bucle -------------------------------------------------------------------------------------------------------------------
$resultado = [ordered]@{}
$fallos = 0
$n = 0
foreach ($p in $piezas) {
    $n++
    $f = $p.ficha
    $plano = ($p.nombre -replace '^nazioenbehatokia/', '' -replace '[\\/]', '_')
    $ruta = Join-Path (Join-Path $Trabajo $p.tipo) $plano
    $ok = "$ruta.ok"
    $meta = $null
    try {
        # 1. reanudar: fichero ya verificado (sidecar .ok con sha256/bytes medidos) y que sigue cuadrando
        if ((Test-Path -LiteralPath $ruta) -and (Test-Path -LiteralPath $ok)) {
            $m = Get-Content -LiteralPath $ok -Raw -Encoding UTF8 | ConvertFrom-Json
            # se recalcula el sha256 del fichero: debe casar con el .ok y, si el índice lo trae, con el índice
            if ((Get-Item -LiteralPath $ruta).Length -eq $m.bytes -and (Sha256Hex $ruta) -eq $m.sha256 -and (-not $f.sha256 -or $f.sha256 -eq $m.sha256)) { $meta = $m }
        }
        # 2. bajar y validar
        if (-not $meta) {
            $parte = "$ruta.part"
            $http = Bajar $f.origen_url $parte
            Start-Sleep -Milliseconds $PausaMs
            $motivo = Validar $parte $p.tipo
            if ($motivo) { Remove-Item -LiteralPath $parte -Force; throw "contenido no válido: $motivo" }
            $sha = Sha256Hex $parte
            $bytes = (Get-Item -LiteralPath $parte).Length
            if ($f.sha256 -and $sha -ne $f.sha256) { Remove-Item -LiteralPath $parte -Force; throw "sha256 $sha distinto del índice $($f.sha256)" }
            if ($f.bytes -and $bytes -ne [long]$f.bytes) { Remove-Item -LiteralPath $parte -Force; throw "bytes $bytes distintos del índice $($f.bytes)" }
            Move-Item -LiteralPath $parte -Destination $ruta -Force
            $meta = [pscustomobject]@{ sha256 = $sha; bytes = $bytes; http = $http; descargado_en = (Get-Date -Format 'yyyy-MM-dd'); verificado = $(if ($f.sha256) { 'indice' } else { 'registrado' }); subido = $false }
            Escribir-Sin-Bom $ok ($meta | ConvertTo-Json)
        }
        # 3. clave con sha12 en el nombre
        $clave = $f.clave
        if (-not $clave) {
            if ($p.tipo -eq 'ine') { $clave = "arc-e/fuentes/ine/$($p.nombre -replace '\.zip$', '')_$($meta.sha256.Substring(0, 12)).zip" }
            else { $r0 = $p.nombre -replace '^nazioenbehatokia/', ''; $clave = "arc-e/fuentes/nazioenbehatokia/$($r0 -replace '\.json$', '')_$($meta.sha256.Substring(0, 12)).json" }
        }
        # 4. subir (si no está ya con el mismo sha256)
        $subido = [bool]$meta.subido
        if (-not $SoloBajar -and -not $subido) {
            if (Subido $clave $meta.sha256) { $subido = $true }
            else {
                & aws s3 cp $ruta "s3://$($env:R2_BUCKET)/$clave" --endpoint-url $endpoint --metadata "sha256=$($meta.sha256)" --only-show-errors
                if ($LASTEXITCODE -ne 0) { throw "la subida a R2 falló (código $LASTEXITCODE)" }
                $subido = $true
            }
            $meta.subido = $true
            Escribir-Sin-Bom $ok ($meta | ConvertTo-Json)
        }
        $resultado[$p.nombre] = [ordered]@{
            clave = $clave; sha256 = $meta.sha256; bytes = $meta.bytes; origen_url = $f.origen_url
            descargado_en = $meta.descargado_en; verificado = $meta.verificado; subido = $subido
        }
        Write-Host ("[{0}/{1}] {2}: {3} bytes, sha256 {4}{5}" -f $n, $piezas.Count, $p.nombre, $meta.bytes, $meta.sha256, $(if ($subido) { ' (en R2)' } else { '' }))
    } catch {
        Write-Warning "[$n/$($piezas.Count)] $($p.nombre): $($_.Exception.Message)"
        $fallos++
    }
}
Escribir-Sin-Bom $Salida ($resultado | ConvertTo-Json -Depth 4)
Write-Host "Resultado en $Salida ($($resultado.Count) de $($piezas.Count); fallos: $fallos)."
if ($fallos -gt 0) { exit 1 }
