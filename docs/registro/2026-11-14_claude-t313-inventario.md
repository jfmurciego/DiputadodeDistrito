## 2026-11-14 — T-313 — inventario de rutas para migrar M01-M08 a P21-P26 y P40

Causa: el propietario aprobó migrar la notación interna a la de fases del framework §2; antes de hacerlo hace falta saber qué se toca.
Cambio: solo documental, `docs/ESTUDIOS/T313_MIGRACION_FASES/INVENTARIO.md` (equivalencias y ambigüedades, recuentos por categoría, riesgos, modelo T-220, orden en una PR). Sin código ni workflows.
Pruebas: recuentos con `git grep`/`git ls-files` sobre `origin/main` (c4e4206); sin tests que ejecutar.
Riesgos: ninguno (docs-only); la migración invalidará checkpoints M04/M05 y exigirá 00 «Ejecutar desde el principio» para las 71.
