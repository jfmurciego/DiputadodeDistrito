## 2026-11-14 — T-300 — La P50 copia el catálogo de procedencia al sitio

Causa: la ficha «De dónde sale este mapa» del visor V3 (PR aparte) lee `datos/catalogo_procedencia.json` y la P50 no lo publicaba.
Cambio: `_reutilizable-publicar-sitio.yml` 3.17.0 (`cp orchestracion/catalogo_procedencia.json` a `datos/catalogo_procedencia.json` del sitio; si falta, el sitio no se construye); copia en `legacy/`; `tests/test_hemiciclo_sitio.py` crea `datos/` antes de ese `cp` (el test omite el materializador).
Pruebas: `tests.test_hemiciclo_sitio`, t237, t301, t305, `test_workflow_safety`, GovernanceHeaders.
Riesgos: toca el workflow de producción (congelado hasta publicar los 71): no fusionar sin el Operador; sin 00 ni cambio de huellas.
