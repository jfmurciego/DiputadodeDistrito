# Propuesta de borrado de artefactos de Actions (2026-11-14, solo lectura)

Causa: «Artifact storage quota has been hit». Vivos: 30.382 artefactos, 244,8 GB; de ellos `ddd-state` 197,7 GB y `ddd-source` 40,2 GB (el resto, ~7 GB, no entra en la propuesta).

Criterio (solo `ddd-state*` y `ddd-source*`; `propuesta.tsv`: id, nombre, run, bytes, fecha, conclusión del run, decisión, motivo):
- CONSERVAR: `ddd-source-package` vigentes en `configuracion/catalogo_preparacion.yaml` (74, 5,86 GB); `ddd-state` de los runs de las 71 publicadas (territorial, electoral y Reutilizar) sin copia en R2 (477, 39,62 GB); `ddd-state` de runs del registro del visor sin copia en R2 (200, 16,23 GB).
- BORRAR: archivados en R2 por nombre exacto (`artefacto` o `artefacto_origen` en `orchestracion/archivo_r2.json`) (315, 27,28 GB); paquetes fuente fuera del catálogo (241, 18,57 GB); de runs fallidos (688, 55,38 GB) o cancelados (242, 18,30 GB); de runs sustituidos, ni publicados ni vigentes (716, 56,71 GB).

**Recuperable: 176,24 GB** (2.202 artefactos). Se conservan 61,71 GB.

Prueba del proxy: `DELETE repos/<r>/actions/artifacts/1` (id inexistente) devuelve 404 de GitHub, no 403 del proxy: el borrado de artefactos por REST pasa por el proxy. Sin borrar nada.
