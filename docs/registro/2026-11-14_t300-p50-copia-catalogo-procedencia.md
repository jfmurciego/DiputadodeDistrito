## 2026-11-14 — T-300 — La P50 copia el catálogo de procedencia al sitio

Causa: la ficha «De dónde sale este mapa» del visor V3 (PR aparte) lee `datos/catalogo_procedencia.json` y la P50 no lo publicaba.
Cambio: `_reutilizable-publicar-sitio.yml` 3.17.0 (T-361: `herramientas/catalogo_procedencia_publico.py` 1.0.0 escribe `datos/catalogo_procedencia.json` del sitio filtrado por lista blanca —solo lo que lee `visor/v3/v3.js`; sin run_id, receipt_path, blob_sha, copias R2—, determinista; si el origen falta, no es JSON o no trae lo que el visor necesita, el sitio no se construye); copia en `legacy/`; `tests/test_hemiciclo_sitio.py` crea `datos/` antes de ese `cp` (el test omite el materializador).
Pruebas: `tests.test_t361_catalogo_procedencia_publico` (lista blanca real + control negativo, determinismo, fallo cerrado, paso tras `--materializar`, `node --test` del visor con el catálogo filtrado), `tests.test_hemiciclo_sitio`, t237, t301, t305, `test_workflow_safety`, GovernanceHeaders.
Riesgos: toca el workflow de producción (congelado hasta publicar los 71): no fusionar sin el Operador; sin 00 ni cambio de huellas.
