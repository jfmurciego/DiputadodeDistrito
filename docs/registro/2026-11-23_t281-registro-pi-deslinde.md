## 2026-11-23 — T-281 — Paquete para el Registro de la Propiedad Intelectual de Deslinde 1.0

- **Causa:** D-196: el repositorio sigue público y Deslinde se protege con licencia propietaria y registro de la
  propiedad intelectual. El paquete 1.0.1 apuntaba a `ddd_motor2/` y a todo `docs/ESTUDIOS/`, sin PDF ni nota de autoría.
- **Cambio:** `herramientas/preparar_paquete_pi.py` 2.0.0: ZIP determinista con `paquetes/deslinde/`,
  `DESLINDE_1_0.md` y solo los estudios que cita (T64, T136, T179, T196, T211, T296); `COPIA_IDENTIFICATIVA.pdf`
  (portada, descripción, índice con sha256, código impreso; `--extremos N`), `NOTA_AUTORIA.pdf` y `MANIFIESTO.txt`.
  PDF sin dependencias. Autor por `--autor` (por defecto «[AUTOR]»). Nuevos `docs/registro_pi/DESCRIPCION.md` y
  `NOTA_AUTORIA.md` (D-32, D-44, D-48, D-50, D-57, D-62, D-63, D-66, D-68, D-79, D-84, D-86, D-90, D-97, D-98, D-196).
  `propiedad_intelectual/`: solo README versionado; se retiran MANIFEST.json y SHA256SUMS del 439af6a.
- **Pruebas:** `tests.test_preparar_paquete_pi` (8); ejecución real en local: 389 ficheros, 14,1 MB, PDF de 90 páginas
  (77 de código; con `--extremos 25`, 64); GovernanceHeaders y guardián.
- **PR/run:** sin run. Lo presenta el propietario.
