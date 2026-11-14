# T-285 · Borra las 34 releases de lista.tsv (33 borradores ensemble-* y cyl-m06-checkpoint-temp) y sus etiquetas.
# Requisito: gh autenticado (gh auth status). Ejecutar en PowerShell desde la raíz del repositorio:
#   powershell -ExecutionPolicy Bypass -File docs\autorizaciones\poda_releases_2026-11-14\borrar_releases.ps1
$repo = 'jfmurciego/DiputadodeDistrito'
$lista = Import-Csv -Delimiter "`t" -Path "$PSScriptRoot\lista.tsv"
$ok = 0; $fallos = @()
foreach ($r in $lista) {
    gh api -X DELETE "repos/$repo/releases/$($r.release_id)" 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $ok++; Write-Host "release OK  $($r.tag)" } else { $fallos += $r.tag; Write-Host "release FALLO $($r.tag)" }
    gh api -X DELETE "repos/$repo/git/refs/tags/$($r.tag)" 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-Host "  etiqueta OK" } else { Write-Host "  etiqueta no existe o FALLO" }
}
Write-Host "Borradas $ok de $($lista.Count). Fallos: $($fallos -join ', ')"
