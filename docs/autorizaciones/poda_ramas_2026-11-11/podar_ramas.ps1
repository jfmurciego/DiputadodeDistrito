# Poda de ramas autorizada por el propietario el 2026-11-11 (criterio del Planificador). Versión Windows (PowerShell).
# Requisitos: git y gh (GitHub CLI) instalados y con sesión iniciada (gh auth status).
# Uso, desde la carpeta del repositorio:
#   powershell -ExecutionPolicy Bypass -File docs\autorizaciones\poda_ramas_2026-11-11\podar_ramas.ps1
# Solo borra si la rama sigue apuntando al mismo sha que en ramas_borradas.tsv.
# Restaurar una rama: gh api -X POST repos/jfmurciego/DiputadodeDistrito/git/refs -f ref=refs/heads/<rama> -f sha=<sha>
$R = "jfmurciego/DiputadodeDistrito"
$F = Join-Path $PSScriptRoot "ramas_borradas.tsv"
$res = @()
Get-Content $F | Select-Object -Skip 1 | ForEach-Object {
  $p = $_ -split "`t"; $rama = $p[0]; $sha = $p[1]
  if (-not $rama) { return }
  $actual = (gh api "repos/$R/git/ref/heads/$rama" --jq .object.sha 2>$null)
  if ($actual -ne $sha) { $l = "SALTADA (cambió o no existe): $rama" }
  else {
    gh api -X DELETE "repos/$R/git/refs/heads/$rama" *> $null
    if ($LASTEXITCODE -eq 0) { $l = "BORRADA $rama" } else { $l = "FALLO $rama" }
  }
  Write-Output $l; $res += $l
}
$res | Set-Content poda_ramas_resultado.txt -Encoding UTF8
"Borradas: " + ($res | Where-Object { $_ -like 'BORRADA*' }).Count + "  Saltadas: " + ($res | Where-Object { $_ -like 'SALTADA*' }).Count + "  Fallos: " + ($res | Where-Object { $_ -like 'FALLO*' }).Count
