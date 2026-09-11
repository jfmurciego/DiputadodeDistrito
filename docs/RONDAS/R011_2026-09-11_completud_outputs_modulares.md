# R011 — Completud de outputs y contrato auditable por módulo

**Fecha:** 2026-09-11

## Problema detectado
La primera publicación R010 daba visibilidad nominal pero no completud: M01-M03 mostraban principalmente informes/resúmenes; M04-M05 ocultaban la asignación real tras GeoJSON no navegables desde la carpeta; M06 reducía el distrito a `district_id,district_pop`. Esto incumplía el objetivo de procedimiento demostrable.

## Decisión
Cada módulo debe materializar el **estado completo que produce**. Los informes son metadatos del producto, nunca sustitutos del producto.

## Implementación
Se añade `herramientas/generar_outputs_auditables.py` v1.0.0 y workflow 2.7.0. Cada ejecución genera `auditoria/M01..M08`; las tablas/JSON/JSONL se publican en `resultados/ejecuciones/<run_id>/`; las geometrías se publican en ocho artefactos de Actions separados. `PRODUCTOS.json` registra ruta, tamaño y SHA-256 de cada producto pesado.

## Contrato especial M06
Se introduce catálogo distrital rico: población y desviaciones; cumplimiento; secciones; municipios; provincias; superficie; perímetro; compacidad; centroide; bounding box. Se añade composición completa sección→distrito con CUSEC y contexto administrativo.

## Documentación
Se crean ocho documentos en `docs/MODULOS/`, uno por módulo, con explicación funcional y arquitectónica, entradas, transformaciones, productos y validaciones.

## Criterio de aceptación
La siguiente ejecución iterativa solo valida R011 si reproduce el PASS territorial de Run #4 y deja accesibles los productos completos de M01-M08 tanto en la carpeta Git de resultados como en los artefactos pesados por módulo.
