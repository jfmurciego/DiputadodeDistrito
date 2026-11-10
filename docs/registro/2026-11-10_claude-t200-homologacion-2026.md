## 2026-11-10 — T-200 — Cargadores de homologación y equivalencia de secciones para las generales 2026

**Causa.** El ensayo T-197 (#664) dejó dos huecos: las siglas de Interior no cubiertas por las reglas pasaban como identidad ALTA sin aviso, y no había forma de cargar una tabla de equivalencia de secciones por fecha.

**Cambio.**
- `herramientas/homologacion_candidaturas_2026.py` 1.1.0 (copia en `legacy/`): `resolver_zip`, `siglas_sin_regla`, `exigir_siglas_zip`. Orden: regla 2026 → tabla `interior` de `reglas_generales.json` → candidatura BOE de la provincia (BOE-A-2026-23103 + 23383, sha256 en `candidaturas_congreso_2026.json`) → `SIN_REGLA` (falla con `SIGLAS_SIN_REGLA`). Ninguna sigla de Interior 2026 se inventa.
- `herramientas/equivalencia_congreso.py` 1.0.0: `cargar(fecha)`; 2023-07-23 usa la tabla vigente (sha256 contra su JSON); 2026-11-29 falla con `EQUIVALENCIA_NO_ACREDITADA` y la causa.
- Tests: `test_homologacion_candidaturas_2026` (+4) y `test_equivalencia_congreso` (3). Valores esperados literales de los ficheros de reglas y de la tabla 2023. No se tocan `resultados_partidos.py`, el registro del visor ni workflows.

**Qué queda para después del 29-11-2026** (el ZIP de Interior sale tras la jornada; fecha exacta sin publicar):
1. Con el ZIP real: ejecutar `exigir_siglas_zip` por provincia, decidir y añadir las reglas `interior["202611"]` (familia SUMAR, JUNTS, PSE-EE, UPN: decisión de contenido) y las 10 reglas BAJA.
2. Construir `equivalencia_secciones_congreso_20261129.csv/.json` (seccionado electoral 2026 + callejero; hoy bloqueado, F10) y enlazar `resultados_partidos` (T-199).
3. 52 contratos Infoelectoral 2026 y decisión del registro 2023/2026 (T-199).

**Riesgos.** Sin cambios en M04/M05/política: no invalida checkpoints ni huellas; no requiere 00. Los cargadores aún no están conectados al flujo (ver T-199).
