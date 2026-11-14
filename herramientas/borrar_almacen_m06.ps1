<#
PROYECTO: Diputado de Distrito · T-302 · VERSIÓN 1.0.0 · 2026-11-14 · ANTERIOR: ninguna (fichero nuevo)
Borra SOLO las releases almacen-m06-* cuyos assets están TODOS en el índice de R2 (orchestracion/almacen_m06_r2.json) con la clave
arc-p/m06/<asset>_<sha12>.<ext> y el mismo sha256 que registra la release. Las demás se CONSERVAN (se avisa). No toca viewer-* ni otras releases.
Uso (desde la raíz del repositorio, con `gh auth login` hecho y el índice ya fusionado en main):
  .\herramientas\borrar_almacen_m06.ps1 -WhatIf     # solo muestra qué haría
  .\herramientas\borrar_almacen_m06.ps1             # pide escribir BORRAR y borra una a una (irreversible)
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$Repo = 'jfmurciego/DiputadodeDistrito',
    [string]$Indice = 'orchestracion/almacen_m06_r2.json'
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path $Indice)) { throw "No existe el índice $Indice: nada que comprobar, no se borra nada." }
$objetos = (Get-Content $Indice -Raw | ConvertFrom-Json).objetos
$claves = @{}
if ($objetos) { foreach ($p in $objetos.PSObject.Properties) { $claves[$p.Name] = "$($p.Value.sha256)".ToLower() } }

$crudo = gh api --paginate "repos/$Repo/releases?per_page=100"
if ($LASTEXITCODE -ne 0) { throw "gh api falló al listar las releases (código $LASTEXITCODE): no se borra nada." }
$releases = $crudo | ConvertFrom-Json | Where-Object { $_.tag_name -like 'almacen-m06-*' }
if (-not $releases) { Write-Warning 'No hay releases almacen-m06-*.'; return }

$borrar = @()
foreach ($r in $releases) {
    $faltan = @()
    foreach ($a in $r.assets) {
        $sha = "$($a.digest)" -replace '^sha256:', ''
        $dot = $a.name.LastIndexOf('.')
        $clave = "arc-p/m06/$($a.name.Substring(0, $dot))_$($sha.Substring(0, [Math]::Min(12, $sha.Length)))$($a.name.Substring($dot))"
        if ($sha.Length -ne 64 -or -not $claves.ContainsKey($clave) -or $claves[$clave] -ne $sha.ToLower()) { $faltan += $a.name }
    }
    if ($r.assets.Count -eq 0) { $faltan += '(sin assets)' }
    if ($faltan.Count -gt 0) {
        Write-Warning "CONSERVAR $($r.tag_name): NO VERIFICADO EN R2 ($($faltan.Count) de $($r.assets.Count) assets: $($faltan[0..2] -join ', ')...)"
    } else {
        Write-Host "BORRAR $($r.tag_name): $($r.assets.Count) assets, todos en R2 con el mismo sha256"
        $borrar += $r
    }
}
if ($borrar.Count -eq 0) { Write-Host 'Nada que borrar.'; return }
if (-not $WhatIfPreference) {
    $resp = Read-Host "Se borrarán $($borrar.Count) release(s), de forma irreversible. Escribe BORRAR para confirmar"
    if ($resp -cne 'BORRAR') { Write-Host 'Cancelado.'; return }
}
foreach ($r in $borrar) {
    if ($PSCmdlet.ShouldProcess($r.tag_name, 'Borrar release')) {
        gh api -X DELETE "repos/$Repo/releases/$($r.id)"
        if ($LASTEXITCODE -ne 0) { throw "No se pudo borrar $($r.tag_name) (código $LASTEXITCODE); se detiene." }
        Write-Host "Borrada $($r.tag_name)"
    }
}
