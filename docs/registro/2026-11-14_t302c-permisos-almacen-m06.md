## 2026-11-14 — T-302 — El archivado del almacén M06 ve los borradores (contents: write)

Causa: el run 43632394790 de `archivar_almacen_m06` falló con ALMACEN_SIN_ASSETS: las 6 releases `almacen-m06-*` son borradores y la API de releases solo los lista con `contents: write`; el job corría con `read`.
Cambio: `bateria-motor.yml` 1.3.1 (solo el job `archivar_almacen_m06` pasa a `contents: write`; workflow y demás jobs, read; copia en `legacy/`). El job solo lee releases (GET y descarga de assets) y sube a R2: sin push ni edición ni borrado. Comprobado antes de relanzar: con acceso de escritura la API lista las 6 releases (45 zips, 1112 MB, el mayor 93 MB, todos con digest sha256, 45 claves distintas); no hay otro fallo detrás en `inventario`.
Pruebas: `tests/test_t302_permisos_almacen.py` (solo ese job escribe; el job no usa git push, release edit/delete/create ni verbos de escritura).
Riesgos: sin 00 ni huellas; el job sigue siendo solo `workflow_dispatch` del Operador. Los MANIFIESTO-*.tsv entran con #779.
