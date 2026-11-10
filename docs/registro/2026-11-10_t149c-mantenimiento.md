## 2026-11-10 — T-149 — Un solo auxiliar de mantenimiento programado

Causa: tres workflows de mantenimiento sueltos (archivo de artefactos en R2, métricas del proceso, extracción de la composición
por distrito) ocupaban tres entradas de la lista de Actions.
Cambio: nuevo `mantenimiento-programado.yml` 1.0.0, «Auxiliar — Mantenimiento programado», con un job por tarea
(`archivar_r2`, `metricas`, `extraer_m06`); cada job conserva su cuerpo, su concurrencia (mismos grupos, sin cancelar, cola máxima),
la credencial de registro tras el checkout y permisos mínimos propios. Cron diario 05:17 → archivo R2; cron del lunes 05:17 →
métricas; disparo manual con la entrada `tarea` (+ `caduca_antes` y `territorios`). Los tres antiguos dejan su última versión en
`legacy/workflows/`. «Auxiliar — Poda de R2» (borrado irreversible con entorno protegido) NO se funde: sigue separada y comparte el
grupo de concurrencia del archivista.
Pruebas: métricas, contrato de preparación, matriz y catálogo de diseño, credencial de registro, seguridad de workflows y gobernanza
en verde. La prueba real es el primer disparo programado/manual tras fusionar (sin lanzamientos productivos desde esta PR).
Riesgos: la concurrencia pasa a nivel de job (`queue: max` a nivel de job no se ha podido validar sin ejecutar en GitHub); los lunes
corren dos eventos de cron, cada uno activa solo su job. Ejecuciones antiguas conservan su nombre anterior en el historial.
