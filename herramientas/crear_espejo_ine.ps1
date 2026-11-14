# PROYECTO: Diputado de Distrito · VERSIÓN 1.0.0 · 2026-11-14 · T-298
# Crea los releases-espejo de las fuentes nacionales del INE (una sola descarga; la batería ya no vuelve a ine.es).
# Requisitos: gh autenticado con permiso de escritura en el repositorio; ejecutar desde la raíz del repo (git pull antes).
# Los sha256 son los de configuracion/fuentes_ine_espejo.yaml: si una descarga no cuadra, el script se detiene.
$ErrorActionPreference = 'Stop'
$repo = 'jfmurciego/diputadodedistrito'
$tmp = Join-Path $env:TEMP 'espejo_ine'
New-Item -ItemType Directory -Force $tmp | Out-Null
$fuentes = @(
  @{ tag='fuente-ine-seccionado-2023'; f='seccionado_2023.zip'; sha='7a15e700a4592d793230441cfcb4b72e40979998aef019ca644389271886bf1f'; url='https://www.ine.es/prodyser/cartografia/seccionado_2023.zip' },
  @{ tag='fuente-ine-seccionado-2024'; f='seccionado_2024.zip'; sha='df931fa0d372808eb81abb2f2645ed5ecccbd6ed397b85db656980748ddd6bf7'; url='https://www.ine.es/prodyser/cartografia/seccionado_2024.zip' },
  @{ tag='fuente-ine-seccionado-2025'; f='seccionado_2025.zip'; sha='55c9da7e34d3bb3cb725400c35b58e72f4db2ea8321ef91237a89e708d2dbcc4'; url='https://www.ine.es/prodyser/cartografia/seccionado_2025.zip' },
  # 65034: el zip del repositorio (la descarga en vivo del CSV pesa 1,6 GB); se reconstruye de inputs/partes y se verifica.
  @{ tag='fuente-ine-65034-2025'; f='65034.csv.zip'; sha='91d3ff9a90bac1c06e26df97179daa325b65fa77c9209879d6a40333b17057f3'; url=$null }
)
foreach ($s in $fuentes) {
  $dest = Join-Path $tmp $s.f
  if ($s.url) { Invoke-WebRequest -Uri $s.url -OutFile $dest }
  else {
    $out = [System.IO.File]::Create($dest)
    Get-ChildItem inputs/partes -Filter '65034.csv.zip.part*' | Sort-Object Name | ForEach-Object { $b = [System.IO.File]::ReadAllBytes($_.FullName); $out.Write($b, 0, $b.Length) }
    $out.Close()
  }
  $h = (Get-FileHash $dest -Algorithm SHA256).Hash.ToLower()
  if ($h -ne $s.sha) { throw "$($s.f): sha256 $h distinto del esperado $($s.sha)" }
  gh release create $s.tag $dest --repo $repo --title $s.tag --notes "Espejo de la fuente oficial del INE ($($s.f)). sha256 $($s.sha). T-298."
  Write-Host "OK $($s.tag)"
}
