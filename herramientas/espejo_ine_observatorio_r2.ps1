<#
PROYECTO: Diputado de Distrito - T-356 - VERSION 1.0.0 - 2026-11-15 - ANTERIOR: ninguna (fichero nuevo)
Baja los 17 seccionados del INE (2010-2026), la tabla INE 30832 y el Censo 2011 por seccion (grupo padron, 2 piezas; D-126) y las 625 piezas del Observatorio Electoral de las Naciones, verifica el sha256 del
indice orchestracion/fuentes_r2.json (donde exista; donde no, lo mide y lo registra), las sube a R2 (ARC-E) en
arc-e/fuentes/ine/seccionado_<ano>_<sha12>.zip y arc-e/fuentes/nazioenbehatokia/<ruta>_<sha12>.json y escribe el JSON de resultado
(clave, sha256, bytes, origen_url, descargado_en, subido). Se ejecuta en el Windows del propietario (PowerShell 5.1+); no necesita checkout:
  irm https://raw.githubusercontent.com/jfmurciego/DiputadodeDistrito/main/herramientas/espejo_ine_observatorio_r2.ps1 -OutFile espejo.ps1
Sin checkout, el indice se baja de raw de main; con checkout (desde su raiz) se usa orchestracion/fuentes_r2.json local.
MIENTRAS LA PR #829 NO ESTE FUSIONADA hay que pasar -Indice con la raw de la rama, p. ej.
  -Indice https://raw.githubusercontent.com/jfmurciego/DiputadodeDistrito/t356-espejo-ine-observatorio-r2/orchestracion/fuentes_r2.json
Credenciales (solo para subir; nunca se imprimen ni se guardan): $env:AWS_ACCESS_KEY_ID, $env:AWS_SECRET_ACCESS_KEY, $env:R2_ACCOUNT_ID,
$env:R2_BUCKET, y AWS CLI (`aws`). AWS_DEFAULT_REGION=auto se pone aqui.
Uso:
  .\espejo_ine_observatorio_r2.ps1 -SoloBajar              # baja y mide, NO sube
  .\espejo_ine_observatorio_r2.ps1                         # baja, mide y sube (INE y Observatorio)
  .\espejo_ine_observatorio_r2.ps1 -Limite 1 -SoloBajar   # prueba con la primera pieza antes del lote
  .\espejo_ine_observatorio_r2.ps1 -Grupo ine              # solo los 17 seccionados (o -Grupo observatorio)
-Reanudar (comportamiento por defecto, explicito): la fuente de verdad es R2 + el .ok local, no el JSON de resultado anterior; al empezar imprime "Reanudando: N piezas ya en R2" (head-object; con -SoloBajar no hay head-object) y al final saltados / subidos / fallidos con la lista de fallidas y su motivo.
Reanudable: lo ya verificado (fichero + .ok) no se vuelve a bajar y lo ya subido (head-object con el mismo sha256) no se vuelve a subir.
Carpeta de trabajo corta (limite de ruta de Windows): C:\ddd. Sale con codigo 1 si falla alguna pieza y con 2 si no se confirma la sobrescritura del JSON. Despues, pega el JSON de resultado en el chat del Coordinador.
#>
[CmdletBinding()]
param(
    [string]$Indice = '',    # ruta local o URL del indice; vacio = orchestracion/fuentes_r2.json local si existe, si no raw de main
    [string]$Trabajo = 'C:\ddd',
    [string]$Salida = 'espejo_ine_observatorio_r2_resultado.json',
    [ValidateSet('todo', 'ine', 'observatorio', 'padron')][string]$Grupo = 'todo',
    [switch]$SoloBajar,
    [switch]$Reanudar,       # alias explicito del comportamiento por defecto (la fuente de verdad es R2 + el .ok local, no el JSON anterior)
    [switch]$Forzar,         # sobrescribe el JSON de resultado sin preguntar
    [int]$Reintentos = 5,
    [int]$PausaMs = 200,     # pausa entre peticiones al mismo servidor
    [int]$Limite = 0         # procesa solo las N primeras piezas (0 = todas); prueba: -Limite 1 -SoloBajar
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
    $r = Read-Host "$Salida ya existe y se sobrescribira. Escribe SI para continuar"
    if ($r -cne 'SI') { Write-Host 'Cancelado: no se ha hecho nada.'; exit 2 }
}

# --- indice -----------------------------------------------------------------------------------------------------------------
if (-not $Indice) { $Indice = if (Test-Path 'orchestracion/fuentes_r2.json') { 'orchestracion/fuentes_r2.json' } else { $RAW } }
$txt = if ($Indice -match '^https?://') { (Invoke-WebRequest -Uri $Indice -UseBasicParsing -UserAgent $ua).Content } else { Get-Content $Indice -Raw -Encoding UTF8 }
if ($txt -is [byte[]]) { $txt = [Text.Encoding]::UTF8.GetString($txt) }
$fuentes = ($txt | ConvertFrom-Json).fuentes
$piezas = @()
foreach ($p in $fuentes.PSObject.Properties) {
    $u = [string]$p.Value.origen_url
    $esIne = $u -match '^https://www\.ine\.es/prodyser/cartografia/seccionado_\d{4}\.zip$'
    $esObs = $u -match '^https://nazioenbehatokia\.eus/(data|geo)/.+\.json$'
    $esCsv = $u -eq 'https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/30832.csv'
    $esCen = $u -eq 'https://www.ine.es/censos2011_datos/indicadores_seccion_censal_csv.zip'
    $esPad = $esCsv -or $esCen
    if (($esIne -and $Grupo -in 'todo', 'ine') -or ($esPad -and $Grupo -in 'todo', 'padron') -or ($esObs -and $Grupo -in 'todo', 'observatorio')) {
        # tipo = carpeta de trabajo; valida = comprobacion del contenido (zip | csv | json)
        $piezas += [pscustomobject]@{ nombre = $p.Name; ficha = $p.Value; tipo = $(if ($esObs) { 'obs' } else { 'ine' }); valida = $(if ($esCsv) { 'csv' } elseif ($esObs) { 'json' } else { 'zip' }) }
    }
}
$esperadas = @{ todo = 644; ine = 17; observatorio = 625; padron = 2 }[$Grupo]
if ($piezas.Count -lt $esperadas) { throw "El indice trae solo $($piezas.Count) de $esperadas piezas: es el de main anterior a la PR #829? Pasa -Indice con la raw de la rama (ver cabecera)." }
if ($piezas.Count -ne $esperadas) { throw "Se esperaban $esperadas piezas y el indice trae $($piezas.Count): no se continua." }
if ($Limite -gt 0) { $piezas = @($piezas | Select-Object -First $Limite) }

# --- utilidades --------------------------------------------------------------------------------------------------------------
New-Item -ItemType Directory -Force -Path (Join-Path $Trabajo 'ine'), (Join-Path $Trabajo 'obs') | Out-Null
function Sha256Hex($ruta) { (Get-FileHash -Algorithm SHA256 -LiteralPath $ruta).Hash.ToLower() }
function Ruta-Completa($ruta) {
    # absolutas intactas; relativas contra la carpeta actual de PowerShell (no la del proceso .NET)
    if ([IO.Path]::IsPathRooted($ruta)) { return [IO.Path]::GetFullPath($ruta) }
    [IO.Path]::GetFullPath((Join-Path (Get-Location).ProviderPath $ruta))
}
function Escribir-Sin-Bom($ruta, $texto) { [IO.File]::WriteAllText((Ruta-Completa $ruta), $texto, (New-Object Text.UTF8Encoding($false))) }

function Detalle($e) {
    # error en UNA linea: tipo, mensaje (con internas), linea del script y pila (nunca vacio)
    $ex = $e.Exception
    $msgs = @()
    for ($x = $ex; $x; $x = $x.InnerException) { $msgs += ('{0}: {1}' -f $x.GetType().FullName, (([string]$x.Message) -replace '\s+', ' ').Trim()) }
    $lin = if ($e.InvocationInfo) { (('{0}: {1}' -f $e.InvocationInfo.ScriptLineNumber, ([string]$e.InvocationInfo.Line)) -replace '\s+', ' ').Trim() } else { '?' }
    $pila = (([string]$e.ScriptStackTrace) -replace '\s+', ' ').Trim()
    $id = [string]$e.FullyQualifiedErrorId
    ('{0} | id: {1} | linea {2} | pila: {3}' -f ($msgs -join ' <- '), $id, $lin, $pila)
}

function Validar($ruta, $valida) {
    # devuelve $null si es valido o el motivo
    $n = (Get-Item -LiteralPath $ruta).Length
    if ($n -eq 0) { return 'fichero vacio' }
    $fs = [IO.File]::OpenRead($ruta)
    try { $buf = New-Object byte[] ([Math]::Min(512, $n)); [void]$fs.Read($buf, 0, $buf.Length) } finally { $fs.Dispose() }
    $ini = [Text.Encoding]::UTF8.GetString($buf).TrimStart([char]0xFEFF, ' ', "`r", "`n", "`t")
    if ($ini -match '(?i)^<\s*(!doctype|html|head|body)') { return 'es HTML (pagina de error), no el fichero' }
    if ($valida -eq 'zip') {
        if (-not ($buf[0] -eq 0x50 -and $buf[1] -eq 0x4B -and $buf[2] -eq 3 -and $buf[3] -eq 4)) { return 'no es un ZIP (falta la firma PK)' }
        try {
            Add-Type -AssemblyName System.IO.Compression.FileSystem
            $z = [IO.Compression.ZipFile]::OpenRead($ruta)
            $entradas = $z.Entries.Count; $z.Dispose()
            if ($entradas -lt 1) { return 'ZIP sin entradas' }
        } catch { return "ZIP ilegible: $($_.Exception.Message)" }
    } elseif ($valida -eq 'csv') {
        if ($ini.Length -eq 0 -or $ini.Contains([string][char]0)) { return 'CSV vacio o binario' }
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
            if (-not $reintentable -or $i -eq $Reintentos) { throw (New-Object System.Exception(("HTTP {0} (intento {1}) {2}" -f $http, $i, (([string]$_.Exception.Message) -replace '\s+', ' ').Trim()), $_.Exception)) }
            $espera = 10 * [Math]::Pow(2, $i - 1)
            if ($http -eq 429 -and $resp.Headers['Retry-After']) { $ra = 0; if ([int]::TryParse($resp.Headers['Retry-After'], [ref]$ra)) { $espera = [Math]::Max($espera, $ra) } }
            Write-Warning "HTTP $http en $url; reintento $i de $Reintentos en $espera s"
            Start-Sleep -Seconds $espera
        }
    }
}

function Bajar-Reanudable($url, $destino) {
    # ficheros grandes (CSV de ~445 MB): a disco por bloques, con Range desde el .part si existe; sin cargar nada en memoria.
    # El .part se conserva entre reintentos y ejecuciones; 416 = el .part ya esta completo.
    for ($i = 1; $i -le $Reintentos; $i++) {
        $resp = $null; $fs = $null
        try {
            $ya = if (Test-Path -LiteralPath $destino) { (Get-Item -LiteralPath $destino).Length } else { 0 }
            $req = [Net.HttpWebRequest]::Create($url)
            $req.UserAgent = $ua; $req.Timeout = 600000; $req.ReadWriteTimeout = 120000; $req.AllowAutoRedirect = $true
            if ($ya -gt 0) { $req.AddRange([long]$ya) }
            try { $resp = $req.GetResponse() } catch [Net.WebException] {
                $rx = $_.Exception.Response
                if ($rx -and [int]$rx.StatusCode -eq 416 -and $ya -gt 0) { $rx.Close(); return 200 }   # ya completo
                throw
            }
            $http = [int]$resp.StatusCode
            $modo = if ($http -eq 206 -and $ya -gt 0) { [IO.FileMode]::Append } else { [IO.FileMode]::Create }
            $fs = New-Object IO.FileStream($destino, $modo, [IO.FileAccess]::Write)
            $in = $resp.GetResponseStream(); $buf = New-Object byte[] 1048576
            while (($k = $in.Read($buf, 0, $buf.Length)) -gt 0) { $fs.Write($buf, 0, $k) }
            return $http
        } catch {
            $rx = $_.Exception.Response
            $http = if ($rx) { [int]$rx.StatusCode } else { 0 }
            $reintentable = ($http -eq 0 -or $http -eq 429 -or $http -ge 500)
            if (-not $reintentable -or $i -eq $Reintentos) { throw (New-Object System.Exception(("HTTP {0} (intento {1}) {2}" -f $http, $i, (([string]$_.Exception.Message) -replace '\s+', ' ').Trim()), $_.Exception)) }
            $espera = 10 * [Math]::Pow(2, $i - 1)
            Write-Warning "HTTP $http en $url; reintento $i de $Reintentos en $espera s (se reanuda desde el .part)"
            Start-Sleep -Seconds $espera
        } finally { if ($fs) { $fs.Dispose() }; if ($resp) { $resp.Close() } }
    }
}

function Invocar-Aws([string[]]$Argumentos) {
    # unica puerta a aws: en PS 5.1 con ErrorActionPreference=Stop el stderr de un comando nativo es una excepcion
    # (NativeCommandError) aunque se redirija con 2>$null; aqui se baja a Continue, se captura todo y se devuelve codigo + salida
    $previo = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $salida = & aws @Argumentos 2>&1 | ForEach-Object { "$_" }
        $codigo = $LASTEXITCODE
    } finally { $ErrorActionPreference = $previo }
    [pscustomobject]@{ Codigo = $codigo; Salida = ((@($salida) -join "`n").Trim()) }
}

function Estado-R2($clave, $sha, $bytes) {
    # igual = existe con Metadata.sha256 y ContentLength iguales (se salta); falta = 404/NotFound; distinto = existe pero no coincide (se resube)
    # otro error (403, credenciales, red) se propaga con el texto de aws
    $r = Invocar-Aws @('s3api', 'head-object', '--bucket', $env:R2_BUCKET, '--key', $clave, '--endpoint-url', $endpoint)
    if ($r.Codigo -ne 0) {
        if ($r.Salida -match '(?i)\b404\b|not\s*found|NoSuchKey') { return 'falta' }
        throw "head-object fallo (codigo $($r.Codigo)): $($r.Salida)"
    }
    try { $j = $r.Salida | ConvertFrom-Json } catch { return 'distinto' }
    $shaR2 = if ($j.Metadata) { [string]$j.Metadata.sha256 } else { '' }
    if ($shaR2 -eq $sha -and [long]$j.ContentLength -eq [long]$bytes) { return 'igual' }
    return 'distinto'
}

# --- bucle -------------------------------------------------------------------------------------------------------------------
$resultado = [ordered]@{}
$fallos = 0
$saltados = 0
$subidos = 0
$soloBajados = 0
$fallidas = @()
if (-not $SoloBajar) {
    # cuenta rapida (head-object, nada se baja): cuantas piezas con huella conocida ya estan en R2 con sha256 y bytes iguales
    $yaEnR2 = 0
    $cacheR2 = @{}   # clave -> estado medido en la cuenta previa; el bucle lo reutiliza (nada cambia entre medias)
    foreach ($q in $piezas) {
        if ($q.ficha.clave -and $q.ficha.sha256 -and $q.ficha.bytes) {
            try { $e0 = Estado-R2 $q.ficha.clave $q.ficha.sha256 $q.ficha.bytes; $cacheR2[$q.ficha.clave] = $e0; if ($e0 -eq 'igual') { $yaEnR2++ } } catch { Write-Warning "cuenta previa: $($q.nombre): $((([string]$_.Exception.Message) -replace '\s+', ' ').Trim())" }
        }
    }
    Write-Host "Reanudando: $yaEnR2 piezas ya en R2 de $($piezas.Count) (las demas se bajan si falta el .ok y se suben)."
}
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
        $m = $null
        if ((Test-Path -LiteralPath $ruta) -and (Test-Path -LiteralPath $ok)) {
            try { $m = Get-Content -LiteralPath $ok -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $m = $null }
            if (-not $m -or -not $m.sha256 -or -not $m.bytes) {
                # .ok truncado o corrupto: se trata como "sin .ok" (se borra y la pieza se rebaja)
                Remove-Item -LiteralPath $ok -Force -ErrorAction SilentlyContinue
                Remove-Item -LiteralPath $ruta -Force -ErrorAction SilentlyContinue
                $m = $null
            }
        }
        if ($m) {
            # se recalcula el sha256 del fichero: debe casar con el .ok y, si el indice lo trae, con el indice
            if ((Get-Item -LiteralPath $ruta).Length -eq $m.bytes -and (Sha256Hex $ruta) -eq $m.sha256 -and (-not $f.sha256 -or $f.sha256 -eq $m.sha256)) { $meta = $m }
        }
        # 2. bajar y validar
        if (-not $meta) {
            $parte = "$ruta.part"
            $http = $(if ($p.valida -eq 'csv') { Bajar-Reanudable $f.origen_url $parte } else { Bajar $f.origen_url $parte })
            Start-Sleep -Milliseconds $PausaMs
            $motivo = Validar $parte $p.valida
            if ($motivo) { Remove-Item -LiteralPath $parte -Force; throw "contenido no valido: $motivo" }
            $sha = Sha256Hex $parte
            $bytes = (Get-Item -LiteralPath $parte).Length
            if ($f.sha256 -and $sha -ne $f.sha256) { Remove-Item -LiteralPath $parte -Force; throw "sha256 $sha distinto del indice $($f.sha256)" }
            if ($f.bytes -and $bytes -ne [long]$f.bytes) { Remove-Item -LiteralPath $parte -Force; throw "bytes $bytes distintos del indice $($f.bytes)" }
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
        # 4. subir (si no esta ya con el mismo sha256)
        $subido = $false
        $estadoPieza = 'solo_bajado'
        if (-not $SoloBajar) {
            $e1 = if ($cacheR2 -and $cacheR2.ContainsKey($clave)) { $cacheR2[$clave] } else { Estado-R2 $clave $meta.sha256 $meta.bytes }
            if ($e1 -eq 'igual') { $subido = $true; $estadoPieza = 'saltado'; $saltados++ }
            else {
                $cp = Invocar-Aws @('s3', 'cp', $ruta, "s3://$($env:R2_BUCKET)/$clave", '--endpoint-url', $endpoint, '--metadata', "sha256=$($meta.sha256)", '--only-show-errors')
                if ($cp.Codigo -ne 0) { throw "la subida a R2 fallo (codigo $($cp.Codigo)): $($cp.Salida)" }
                # un objeto parcial nunca cuenta: se comprueba sha256 y bytes en R2 tras subir
                if ((Estado-R2 $clave $meta.sha256 $meta.bytes) -ne 'igual') { throw "tras subir, R2 no tiene la clave con el mismo sha256 y bytes: $clave" }
                $subido = $true; $estadoPieza = 'subido'; $subidos++
            }
            $meta.subido = $true
            Escribir-Sin-Bom $ok ($meta | ConvertTo-Json)
        } else { $soloBajados++ }
        $resultado[$p.nombre] = [ordered]@{
            clave = $clave; sha256 = $meta.sha256; bytes = $meta.bytes; origen_url = $f.origen_url
            descargado_en = $meta.descargado_en; verificado = $meta.verificado; subido = $subido; estado_r2 = $estadoPieza
        }
        Write-Host ("[{0}/{1}] {2}: {3} bytes, sha256 {4}{5}" -f $n, $piezas.Count, $p.nombre, $meta.bytes, $meta.sha256, $(if ($subido) { ' (en R2)' } else { '' }))
    } catch {
        $detalle = Detalle $_
        Write-Warning "[$n/$($piezas.Count)] $($p.nombre): $detalle"
        $resultado[$p.nombre] = [ordered]@{ origen_url = $f.origen_url; subido = $false; estado_r2 = 'fallido'; error = $detalle }
        $fallidas += [ordered]@{ pieza = $p.nombre; clave = $f.clave; motivo = $detalle }
        $fallos++
    }
}
$resumen = [ordered]@{ saltados = $saltados; subidos = $subidos; solo_bajados = $soloBajados; fallidos = $fallos; total = $piezas.Count }
Escribir-Sin-Bom $Salida ([ordered]@{ resumen = $resumen; fallidas = @($fallidas); piezas = $resultado } | ConvertTo-Json -Depth 6)
Write-Host "Resultado en $Salida. Saltados (ya en R2): $saltados; subidos: $subidos; solo bajados: $soloBajados; fallidos: $fallos de $($piezas.Count)."
foreach ($q in $fallidas) { Write-Warning "FALLIDA $($q.pieza) ($($q.clave)): $($q.motivo)" }
if ($fallos -gt 0) { exit 1 }
