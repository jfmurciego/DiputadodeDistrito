# Continuación de Fuentes Oficiales — transferencia auténtica F10

Checkpoint técnico del 11-10-2026 sobre el Plan Maestro existente. La transferencia llegó en `DDD_F10_5_ARTEFACTOS_AUTENTICOS_20261011.zip`; los bytes originales se conservan bajo `/private/tmp/ddd-f10-transfer-20261011` y los ZIP exteriores originales permanecen en `Downloads`. No se copiaron los paquetes fuente voluminosos a Git.

El ZIP de transferencia mide 69.747.289 bytes y su SHA-256 es `d44f79be353f6c5df469189d47cce9667d451da21a1b60c0eef28f2b34afd66c`. Pasó CRC. `SHA256SUMS` verifica los cinco artefactos exteriores. Para cada uno se comprobaron el ID de run y artefacto declarados, commit, nombre, tamaño, SHA-256 exterior, manifiesto interior, SHA-256 de `prepared_sources.zip`, CRC, identidad territorial y el informe congelado de compatibilidad. `validate_prepared_package` y `validate_compatibility_package(require_ready=True)` pasan en los cinco paquetes. Los hashes e identidades completas están en `validacion.json`.

Se generaron cinco documentos de receipt `ddd.territorial-source-receipt/1.0` desde esos mismos bytes, todos para edición/población/seccionado 2025/2025. Están en `receipts-pendientes/` y fuera de `configuracion/catalogo_preparacion.yaml` y de las rutas territoriales consumibles. Ningún receipt fue registrado y no se ejecutó promoción.

La función canónica `validate_territorial_receipt` aceptó el receipt auténtico de Extremadura edición 2025 en un scratch aislado, tras validar el paquete y el informe de compatibilidad. Esa prueba confirma la puerta territorial #179. El catálogo productivo no cambió. Su fuente electoral permanece `BLOCKED_PROVISIONAL`, separada de la identidad territorial.

La matriz vigente exige Andalucía, Aragón y Castilla y León con población 2025/seccionado 2026; Comunidad Valenciana con 2023/2023; Extremadura con 2025/2025. El inventario local no contiene receipts existentes para las cinco identidades requeridas. Los paquetes F10 auténticos de Andalucía, Aragón, Castilla y León y Comunidad Valenciana son 2025/2025, así que sus receipts acreditan esa identidad histórica pero no resuelven la temporalidad vigente. Los paquetes históricos/candidatos locales tampoco constituyen una fuente con la identidad temporal vigente. La entrada `inputs/cyl_2026_secciones_partidos.csv` es electoral y no acredita geometría territorial.

No se adquirieron datos del INE ni se descargó nada de GitHub, no se ejecutaron workflows, generación, `00`, promoción, push, PR ni merge. El inventario de 19 consumidores conserva 14 PASS históricos y 5 BLOCKED: la verificación de Extremadura en scratch no cambia ese estado productivo.

## Estado de gobierno

F04 queda como propuesta técnica de cierre pendiente de Work; su estado formal no se modifica. F09 continúa PASS. No se escribe en el Plan Maestro fuera del worktree autorizado. Tampoco se hace respaldo externo: el traslado queda pendiente de autorización/herramienta de almacenamiento accesible. La carpeta temporal actual es el checkpoint local verificable.

## Próximos pasos reservados

- Work decide si autoriza registrar los cinco receipts y promover fuentes.
- Para la elegibilidad territorial vigente, Work debe autorizar primero cualquier adquisición oficial requerida: población 2025/seccionado 2026 para Andalucía, Aragón y Castilla y León, y población/seccionado 2023 para Comunidad Valenciana. No hay evidencia local durable ya acreditada para esas identidades.
- Extremadura solo necesita el registro/promoción territorial del receipt tras autorización; la elegibilidad del par sigue bloqueada por la fuente electoral provisional.
- Work determina el respaldo durable fuera del área temporal y resuelve formalmente la propuesta F04.

## Dictamen técnico actualizado

La selección de regresión #179/consumo/temporalidad dio **58 PASS** al excluir la prueba `test_00_executes_real_territorial_reuse_route_without_preparing_source`. La invocación inicial de esa suite detectó que la prueba intenta abrir la ruta `00` en un subprocess con Python 2 del sistema; falló inmediatamente con `No module named herramientas`, antes de cargar o ejecutar el proyecto. Por la restricción de Work no se repitió ese caso. No se lanzaron workflows ni generación.

El verificador nacional previo confirma **14 consumidores PASS y cinco BLOCKED** y F04 técnicamente satisfecho, con transición formal pendiente de Work. No se repitió esa matriz; el catálogo productivo no se alteró. F09 queda PASS y F10 permanece PENDING en el Plan Maestro. En el consumidor activo, los cinco receipts nuevos aún no están registrados; por ello la validación aislada de Extremadura no cambia el bloqueo canónico ni el bloqueo electoral provisional.

La salida está separada por dominio: receipt territorial Extremadura #179 = `PASS` en scratch; fuente electoral = `BLOCKED_PROVISIONAL`; readiness temporal vigente de cuatro paquetes = `BLOCKED_WRONG_YEAR`; catálogo canónico = sin cambios. Las tres identidades 2025/2026 y la identidad CV 2023/2023 carecen de paquete/receipt reusable local verificado. El inventario reutilizable detallado está en `inventario-reutilizacion.json`.

Pruebas reproducibles, desde checkout limpio con dependencias geoespaciales instaladas:

```sh
python3 docs/AUDITORIAS/CIERRE_FUENTES_20261011/transferencia-autentica-20261011/verificar_transferencia.py \
  --transfer /ruta/DDD_F10_5_ARTEFACTOS_AUTENTICOS_20261011.zip \
  --output /private/tmp/ddd-f10-transfer-verify-20261011
python3 docs/AUDITORIAS/CIERRE_FUENTES_20261011/transferencia-autentica-20261011/validar_extremadura_aislada.py \
  --validated-root /private/tmp/ddd-f10-transfer-verify-20261011 \
  --scratch /private/tmp/ddd-f10-extremadura-scratch-20261011
```

Además, la selección unittest indicada arriba terminó con 58 tests OK, sin skips, excluyendo explícitamente el test que intenta invocar `00`.
