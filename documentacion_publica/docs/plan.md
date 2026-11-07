# Plan de trabajo

## Hitos pequeños y verificables

| Orden | Entrega | Criterio de cierre |
|---|---|---|
| 1 · Ahora | Portal Zensical y auditoría base | Construcción estricta correcta, navegación revisada y PR disponible |
| 2 · Archivo piloto | Cuenta R2, bucket privado y escritura de prueba | Descarga independiente y SHA-256 coincidente; recibo durable |
| 3 · Conservación de ejecuciones | Archivador optativo conectado a salidas existentes | Idempotencia, fallo controlado y recuperación probados sin regenerar territorios |
| 4 · Documentación pública | Integración en publicador único | URL estable y visor preservado en despliegues sucesivos |
| 5 · Catálogo de consulta | Vista generada de fuentes, runs y escenarios | Linaje completo hasta ubicación descargable; no hay segundo catálogo manual |
| 6 · Versión académica | Paquete de investigación seleccionado | Licencias, entorno, parámetros, límites metodológicos y depósito citable |

## Primera prioridad de conservación

Cantabria M05 contiene 50 candidatos materialmente verificados. Sus bytes se pueden archivar sin recalcular el experimento. Antes de la caducidad indicada el 13 de noviembre, conservar una copia en el almacenamiento acordado y probar recuperación. La copia local de esta auditoría es evidencia de trabajo, no un archivo externo permanente ni una modificación del catálogo operacional.

## Decisiones pendientes

Confirmar cuenta Cloudflare, jurisdicción, presupuesto y responsables de credenciales; establecer retención y copia de respaldo; resolver licencia de cada recurso publicable; seleccionar ubicación definitiva del portal. La elección del proveedor no debe cambiar los identificadores científicos de las ejecuciones.

## Fuera del primer hito

API dinámica, PostGIS, CKAN, DVC, despliegue de Zenodo y nuevos barridos territoriales. STAC y Data Package se evaluarán cuando exista el catálogo mínimo; no se han implementado en esta PR.

*Versión 1.0.0 · 2026-11-03 · Archivo nuevo.*
