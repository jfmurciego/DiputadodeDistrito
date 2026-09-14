# Bitácora de progreso

**Versión:** 2.7.0  
**Fecha:** 2026-09-11  
**Anterior:** `legacy/bitacora/BITACORA_v2.6.0.md`

## R001–R008 — Base profesional y ejecución reproducible
Se recupera el procedimiento, se formalizan M01-M08, configuración única, caché territorial, fuentes congeladas para desarrollo y adquisición INE para certificación.

## GitHub Run #3 — 34580841510
Infraestructura completa PASS; algoritmo antiguo deja 29 distritos bajo suelo.

## R009 — Restricciones poblacionales y concurrencia
M05 v7.1.0 prioriza restricciones duras; workflow serializa únicamente preparación M01-M03.

## GitHub Run #4 — 34581760340
**Nueva referencia algorítmica:** 67 distritos, contigüidad PASS, 0 bajo suelo, 0 sobre techo, `best_max_rel_dev≈0,3382`. M01-M03 se reutilizan correctamente desde caché.

## R010 — Primera visibilidad de resultados
Se publica `resultados/ejecuciones/<run_id>/`, pero la revisión del usuario detecta una carencia de calidad: M01-M05 estaban representados en Git principalmente por informes/logs y M06 por un resumen poblacional demasiado pobre.

## R011 — Completud y auditabilidad de cada módulo
Se establece la regla: **todo módulo debe exponer el estado que produce, no solo métricas sobre ese estado**. Se crea `herramientas/generar_outputs_auditables.py` y workflow 2.7.0. Desde la siguiente ejecución:
- M01 publica las 1.463 secciones completas en tabla y su GeoJSON;
- M02 publica las 4.293 adyacencias reales;
- M03 publica el grafo completo;
- M04 publica asignación inicial sección→distrito completa;
- M05 publica asignación optimizada completa;
- M06 publica catálogo rico de 67 distritos y composición sección a sección;
- M07 publica detalle por partido y resumen electoral;
- M08 publica tabla final y GeoJSON final.
Las tablas/JSON/JSONL auditables quedan en Git por ejecución; las geometrías pesadas se guardan en artefactos separados M01-M08, con ruta/tamaño/SHA-256 registrados en `PRODUCTOS.json`. Se crean ocho documentos en `docs/MODULOS/` explicando propósito, contrato, entradas, salidas, validaciones y razón arquitectónica.

## Regla permanente de auditoría
Un contador, log o informe nunca sustituye al producto de un módulo. Cada ejecución debe permitir inspeccionar las entidades producidas y rastrear los productos pesados por hash.

## Regla permanente de progreso
Una versión nueva solo sustituye a la referencia si mantiene todos los criterios duros ya satisfechos y mejora una capacidad o métrica explícita.
