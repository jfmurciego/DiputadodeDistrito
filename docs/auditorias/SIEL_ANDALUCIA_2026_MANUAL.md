# Andalucía 2026 — adquisición SIEL manual reproducible

Este procedimiento permite construir localmente el snapshot oficial de Andalucía 2026 sin ejecutar territorios, campañas ni registrar estado en producción.

## 1. Preparar el índice de coordenadas

El fichero Minsait/EleccionesDB se usa exclusivamente como localizador de las 6.044 secciones. Sus votos no se consumen.

```bash
curl --fail --location --retry 1 --connect-timeout 10 --max-time 90 \
  -o andalucia-section-locator.csv \
  https://pub-36ce9aa148a348ae8d9b6686b7edf0c4.r2.dev/eleccionesdb-etl/data-raw/hechos/minsait/01-andalucia.csv

echo "13ffb00bbba4403b9e8d072e766e3979c29ac63cfb5cdcdb7b5e91348484ac21  andalucia-section-locator.csv" | sha256sum -c -
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

Si la red local penaliza 32 workers, reducir a 16 u 8. No modificar las validaciones.

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
