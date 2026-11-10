## 2026-11-10 — T-148 — Tabla maestra de notación AUT01-19 / NAC01-52

Causa: orden del propietario (10-11): sustituir el CODAUTO suelto por una notación única con nombres en español.
Cambio: `configuracion/notacion_territorial.csv` 1.0.0 (71 filas: AUTnn = CODAUTO y NACnn = CPRO del INE, nombre en español, literal INE, id interno actual); fuente INE descargada el 10-11 en `fuentes/ine_codigos_territoriales_2026-11-10/` con `SHA256SUMS`.
Pruebas: `tests.test_notacion_territorial` (sha256 de la fuente, 19+52 filas con códigos y literales del INE, sin nombres en otras lenguas, correspondencia con el catálogo y `territorios/`).
Efectos: ninguno en motor, huellas, workflows, visor ni datos; sin cambio de modo de 00.
