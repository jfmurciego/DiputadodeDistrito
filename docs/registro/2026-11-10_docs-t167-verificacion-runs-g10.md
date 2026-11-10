## 2026-11-10 — T-167 — Verificación de los 844 runs retirados por T-149 y decisión propuesta

Causa: los 647 runs de `orquestacion-control` figuraban «sin decidir» por sus 3 artefactos `g10-*` sin archivar.
Cambio (solo docs, sin borrar ni lanzar nada): consulta REST de los 647 (1941 artefactos, todos vivos, 4,4 MB; selftest, validación de Aragón y resumen; ninguno en `archivo_r2.json` ni en git, reproducibles desde el SHA). Propuesta: borrar los 844. Nuevos `HISTORIAL_WORKFLOWS_BORRADO_RUNS_T149_DECISION.csv` (con `verificada`, `decision_propuesta`, `motivo_decision`) y `HISTORIAL_WORKFLOWS_ARTEFACTOS_G10_T167.csv` (ficha de los artefactos); sección de simulación en `HISTORIAL_WORKFLOWS.md`. Los CSV de 222 y de 844 originales, intactos (sha256 sin cambio).
Pruebas: recuentos y sha256 comprobados con script; contenido no leído (host de descarga bloqueado en cloud).
Riesgos: borrar es irreversible; el Operador debe repetir el inventario antes de ejecutar.
