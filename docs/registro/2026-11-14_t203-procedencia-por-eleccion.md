## 2026-11-14 — T-203 — Catálogo de procedencia: elección por producto y fuentes con ids nuevos

- **Causa:** tras T-220 `catalogo_preparacion.yaml` usa `aut01…nac52` y el generador buscaba la fuente con el id viejo: las 71 fuentes territoriales/electorales salían vacías (SIN_FUENTE_*). Además los productos no declaraban su elección.
- **Cambio:** `catalogo_procedencia.py` 1.4.0: campo `eleccion` (election_date; por defecto 2023-07-23) en cada producto y búsqueda de la fuente por id nuevo o viejo (`resolver_id`). Ids de salida sin cambio (lecturas viejas intactas). Catálogo regenerado (avisos 300 → 158).
- **Pruebas:** `tests.test_catalogo_procedencia` (nuevo caso por elección y por id nuevo).
- **Riesgos:** ninguno en el motor ni huellas; no toca workflows ni contratos. T-206 queda aparte.
