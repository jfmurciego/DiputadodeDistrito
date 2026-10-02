# Andalucía 2026 — adquisición SIEL manual reproducible

> **Operación normal:** usar `03 · Preparación de Resultados Electorales`. El workflow común resuelve la estrategia `official_api_snapshot` y el proveedor `siel` desde el contrato gobernado. Este documento queda como procedimiento diagnóstico/manual y como referencia de recuperación; no es la ruta ordinaria.


## Vía preferente: descarga oficial desde el portal definitivo

La Junta de Andalucía mantiene el portal oficial `https://resultadoseleccionesandalucia.es/` como acceso a datos definitivos de 2026. La documentación oficial indica que SIEL permite descargar tablas de resultados por **totales, municipios y mesas**.

Por tanto, la vía preferente para cerrar Andalucía es:

1. abrir `https://resultadoseleccionesandalucia.es/`;
2. seleccionar Elecciones Autonómicas Andalucía / convocatoria 2026-05;
3. usar **Centro de datos → CSV** y descargar la tabla de resultados por **mesas**;
4. conservar el fichero sin modificar y calcular su SHA-256;
5. adaptar ese CSV oficial al paquete DDD y reconciliarlo contra BOJA.

No asumir el formato del CSV antes de inspeccionarlo. La adquisición masiva por API descrita debajo queda como **fallback reproducible** si el portal no permite obtener de una vez la tabla granular necesaria.

Este procedimiento permite construir localmente el snapshot oficial de Andalucía 2026 sin ejecutar territorios, campañas ni registrar estado en producción.


## Windows PowerShell

Desde la raíz del repositorio:

```powershell
git checkout fix/electoral-input-19-territories
git pull

curl.exe -L `
  -o andalucia-section-locator.csv `
  "https://pub-36ce9aa148a348ae8d9b6686b7edf0c4.r2.dev/eleccionesdb-etl/data-raw/hechos/minsait/01-andalucia.csv"

$expected = "13FFB00BBBA4403B9E8D072E766E3979C29AC63CFB5CDCDB7B5E91348484AC21"
$actual = (Get-FileHash .\andalucia-section-locator.csv -Algorithm SHA256).Hash
if ($actual -ne $expected) { throw "SHA-256 incorrecto: $actual" }

Remove-Item -Recurse -Force .\.ddd-siel-andalucia-2026 -ErrorAction SilentlyContinue

py .\herramientas\adquirir_siel_andalucia_2026.py `
  --out .\.ddd-siel-andalucia-2026 `
  --workers 32 `
  --section-index .\andalucia-section-locator.csv `
  --section-index-sha256 13ffb00bbba4403b9e8d072e766e3979c29ac63cfb5cdcdb7b5e91348484ac21
```

El extractor muestra progreso cada 250 secciones. Si se interrumpe o falla después de haber descargado parte de las secciones, **no borres** `.ddd-siel-andalucia-2026`; reanuda así:

```powershell
py .\herramientas\adquirir_siel_andalucia_2026.py `
  --out .\.ddd-siel-andalucia-2026 `
  --workers 16 `
  --section-index .\andalucia-section-locator.csv `
  --section-index-sha256 13ffb00bbba4403b9e8d072e766e3979c29ac63cfb5cdcdb7b5e91348484ac21 `
  --resume
```

`--resume` sólo reutiliza secciones SIEL previamente guardadas cuyo identificador pertenece al mismo índice gobernado; cualquier checkpoint ajeno o inválido bloquea la ejecución. No modificar las validaciones.

Para comprimir el resultado:

```powershell
Compress-Archive -Path .\.ddd-siel-andalucia-2026 -DestinationPath .\siel-andalucia-2026.zip -Force
```

## 1. Preparar el índice de coordenadas

El fichero Minsait/EleccionesDB se usa exclusivamente como localizador de las 6.044 secciones. Sus votos no se consumen.

```bash
curl --fail --location --retry 1 --connect-timeout 10 --max-time 90 \
  -o andalucia-section-locator.csv \
  https://pub-36ce9aa148a348ae8d9b6686b7edf0c4.r2.dev/eleccionesdb-etl/data-raw/hechos/minsait/01-andalucia.csv

echo "13ffb00bbba4403b9e8d072e766e3979c29ac63cfb5cdcdb7b5e91348484ac21  andalucia-section-locator.csv" | sha256sum -c -
```

En macOS, si `sha256sum` no está instalado:

```bash
test "$(shasum -a 256 andalucia-section-locator.csv | awk '{print $1}')" = "13ffb00bbba4403b9e8d072e766e3979c29ac63cfb5cdcdb7b5e91348484ac21"
```

## 2. Consultar SIEL y construir el snapshot

```bash
rm -rf .ddd-siel-andalucia-2026

python herramientas/adquirir_siel_andalucia_2026.py \
  --out .ddd-siel-andalucia-2026 \
  --workers 32 \
  --section-index andalucia-section-locator.csv \
  --section-index-sha256 13ffb00bbba4403b9e8d072e766e3979c29ac63cfb5cdcdb7b5e91348484ac21
```

El extractor informa del progreso cada 250 secciones. Si la red local penaliza 32 workers, reducir a 16 u 8. Si la ejecución se interrumpe, conservar `.ddd-siel-andalucia-2026/.checkpoint-sections` y repetir el mismo comando añadiendo `--resume`. No modificar las validaciones.

## 3. Ficheros que deben existir

```text
.ddd-siel-andalucia-2026/
  manifest.json
  andalucia_2026_siel_secciones.csv
  andalucia_2026_siel_cera_provincias.csv
```

## 4. Criterios obligatorios de aceptación

El `manifest.json` debe acreditar simultáneamente:

- `territory_id = andalucia`
- `election_id = andalucia_parlamento_2026`
- `election_date = 2026-05-17`
- `siel_election_key = 202605`
- `sections = 6044`
- ocho controles provinciales
- todos los `province_controls[*].reconciles = true`
- `candidate_votes_official = 4157539`
- `candidate_votes_sections + candidate_votes_cera = 4157539`
- `sections_sha256` igual al SHA-256 real de `andalucia_2026_siel_secciones.csv`
- `cera_sha256` igual al SHA-256 real de `andalucia_2026_siel_cera_provincias.csv`

No aceptar un snapshot parcial ni sustituir votos SIEL por los votos del índice provisional.

## 5. Construir el paquete DDD sin registrar producción

```bash
rm -rf .ddd-electoral-package

python herramientas/adaptador_siel_andalucia_2026.py \
  --snapshot .ddd-siel-andalucia-2026 \
  --out .ddd-electoral-package \
  --sections-sha256 "$(jq -r .sections_sha256 .ddd-siel-andalucia-2026/manifest.json)" \
  --cera-sha256 "$(jq -r .cera_sha256 .ddd-siel-andalucia-2026/manifest.json)" \
  --edition 2025
```

El paquete debe quedar en decisión `ACQUIRE`, con `source_status = VERIFIED_OFFICIAL_FINAL`. Este procedimiento no registra el paquete en el catálogo de producción.
