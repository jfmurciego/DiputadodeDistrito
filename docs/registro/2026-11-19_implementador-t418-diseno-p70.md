## 2026-11-19 — T-418 — Diseño corto de la doble vuelta desde R2 (opción de P70)

Causa: orden del propietario (D-178/D-179): V4 en producción sin regenerar. Cambio: `docs/ESTUDIOS/T418_P70_DOBLE_VUELTA/DISENO.md` (1.1.0): acción «P75 Doble vuelta desde R2» en P70
(sin entradas nuevas), pasos por territorio, salidas en R2 y 4 decisiones aprobadas por el Planificador. Revisión de #923 incorporada: objetos nuevos por ejecución
(`<carpeta>/<run>/ddd-doble-vuelta-<run>-p75-<run_p75>.zip` y `doble_vuelta/<AAAA-MM>/<run_p75>/INFORME.json`, nada se sobrescribe ni se borra), run vigente de la elección con
`resultados_ligeros.vigente_por_eleccion` (ámbito NAC por el resolutor), ids nuevos frente a legacy y carpeta del archivista, `aut` rechazado, puerta del workflow y regeneración
inmediata (00 «Generar desde fuente») de los territorios sin el CSV de M07. Implementado y fusionado en #925 (P70 1.1.0). Solo documento; sin código ni workflows. `no-automerge`.
