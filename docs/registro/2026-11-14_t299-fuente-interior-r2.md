## 2026-11-14 — T-299 — ZIP de Infoelectoral en R2 (ARC-E) y inventario de releases

**Causa.** El ZIP por mesa de Interior (que rechaza a los runners) vivía solo en el release `fuente-infoelectoral-02202307`; el Planificador lo quiere en ARC-E con su sha256 en el índice de fuentes.

**Cambio.** `orchestracion/fuentes_r2.json`: entrada `02202307_MESA.zip` (`arc-e/fuentes/interior/02202307_MESA_<sha12>.zip`, sha256 y bytes del contrato `contratos_infoelectoral.yaml`). `herramientas/fuente_r2.py` 1.0.0 (bajar/subir con verificación de sha256). `preparacion-resultados-electorales.yml` 1.0.13: el paso de Infoelectoral lee primero de R2, después la URL oficial y, como respaldo, el release; el ZIP verificado se sube a R2 si faltaba (se puebla solo en la primera 03 con credenciales). La huella del contrato se exige igual. Inventario de solo lectura de `almacen-m06-*` y `viewer-*` con BORRAR/CONSERVAR en `docs/ESTUDIOS/T299_INVENTARIO_RELEASES.md`; no se borra nada.

**Pruebas.** `tests.test_t299_fuente_r2` (R2 simulado: baja y verifica, sha distinto = 53 sin fichero, sin objeto/credenciales/índice = 3, subida exige sha del índice, orden R2 → oficial → release); workflow_safety, design_a y codauto.

**Riesgos.** `generar_hemiciclo.py` sigue leyendo el release (no se toca). El objeto aún no está en R2: la primera 03 de Congreso con credenciales lo sube.
