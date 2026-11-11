## 2026-11-11 — T-267 (regresión de T-251) — La puerta de validación vuelve a funcionar bajo `bash -eo pipefail`

- `_reutilizable-puerta-validacion.yml` 1.3.1 (legacy 1.3.0): `descargar()` ya no aborta el paso. `shell: bash` ejecuta con
  `-eo pipefail`; en 1.3.0 un rc≠0 del helper cortaba antes de clasificar (75/44/42) y, con descarga correcta, el `grep` sin
  coincidencias + pipefail mataba el paso con exit 1 sin mensaje (todas las puertas; Andalucía, run 43113205292). Ahora
  `dl_rc=0; … || dl_rc=$?` y `{ grep … || true; }`.
- Test `DescargarBajoErrexit` (tests/test_descargar_artefacto.py): extrae la función y los dos bloques de la puerta y los ejecuta
  con `bash -eo pipefail` y un `python` falso para rc 0/75/44/42 (artefacto) y 0/75/44 (certificación). Falla con 1.3.0.
