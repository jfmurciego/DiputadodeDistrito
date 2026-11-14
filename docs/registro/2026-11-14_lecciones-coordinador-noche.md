## 2026-11-14 — Coordinador — Lecciones de la noche del 14-11 y cierre en el tablero

Causa: tanda larga de la noche (#765–#789): la campaña r3 dejó en `main` commits de robots con ids legacy que pusieron en rojo la CI de toda PR; hubo PR fusionadas antes del último push, tests que leen `legacy/` (excluido en la imagen de CI), una prueba Node sin ejecutar, borradores de releases invisibles con `contents: read` y artefactos que la nube no descarga.

Cambio: `.claude/rules/workflows.md` (+5 viñetas: revisor y concurrency, campañas y `main`, tests y `.dockerignore`, releases en borrador, sitio y PR), `.claude/rules/contratos.md` (+2: ids legacy en la preparación y linaje; visores y privacidad), línea de historial de `CLAUDE.md` (sigue en 100 líneas) y sección «Cierre 14-11 noche» en `docs/ESTADO.md`. Sin código ni workflows.

Pruebas: `comprobar_guardian_main.py todo` y `tests.test_r015_invariantes.GovernanceHeaders`; sin efectos externos.
