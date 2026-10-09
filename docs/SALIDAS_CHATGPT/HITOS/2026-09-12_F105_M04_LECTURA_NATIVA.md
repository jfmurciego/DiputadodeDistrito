# Hito F1.5 — lectura nativa de propiedades M04

- Fecha: 2026-09-12
- Estado: lanzado
- Evidencia: el smoke confirmó que OGR omite `ddd_unit_id` cuando lo tipa como StringList.
- Cambio: postproceso v7.4.8 carga GeoJSON comprimido desde JSON nativo y normaliza listas unitarias.
- Alcance: deserialización; sin cambios en geometría, asignaciones ni restricciones.
- Verificación exigida: smoke M01–M06 y regresiones Aragón/Castilla y León.
